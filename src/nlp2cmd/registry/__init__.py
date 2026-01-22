"""
Action Registry for NLP2CMD.

Central registry of all allowed actions with their schemas,
validators, and execution handlers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ParamType(Enum):
    """Parameter types for action validation."""
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"
    FILE_PATH = "file_path"
    GLOB_PATTERN = "glob_pattern"
    REGEX_PATTERN = "regex_pattern"
    SQL_IDENTIFIER = "sql_identifier"
    K8S_RESOURCE = "k8s_resource"


@dataclass
class ParamSchema:
    """Schema for an action parameter."""
    
    name: str
    type: ParamType
    required: bool = True
    default: Any = None
    description: str = ""
    validators: list[Callable[[Any], bool]] = field(default_factory=list)
    allowed_values: Optional[list[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for strings


@dataclass
class ActionSchema:
    """Schema definition for an action."""
    
    name: str
    description: str
    domain: str  # e.g., "sql", "shell", "docker", "kubernetes"
    params: list[ParamSchema] = field(default_factory=list)
    returns: ParamType = ParamType.ANY
    returns_description: str = ""
    requires_confirmation: bool = False
    is_destructive: bool = False
    tags: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
    
    def get_required_params(self) -> list[str]:
        """Get list of required parameter names."""
        return [p.name for p in self.params if p.required]
    
    def get_optional_params(self) -> list[str]:
        """Get list of optional parameter names."""
        return [p.name for p in self.params if not p.required]
    
    def get_param(self, name: str) -> Optional[ParamSchema]:
        """Get parameter schema by name."""
        for param in self.params:
            if param.name == name:
                return param
        return None


@dataclass
class ActionResult:
    """Result of action execution."""
    
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, data: Any, **metadata) -> "ActionResult":
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def fail(cls, error: str, **metadata) -> "ActionResult":
        """Create failed result."""
        return cls(success=False, error=error, metadata=metadata)


class ActionHandler:
    """Base class for action handlers."""
    
    def __init__(self, schema: ActionSchema):
        self.schema = schema
    
    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate parameters against schema.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required params
        for param_name in self.schema.get_required_params():
            if param_name not in params:
                errors.append(f"Missing required parameter: {param_name}")
        
        # Validate each provided param
        for name, value in params.items():
            param_schema = self.schema.get_param(name)
            
            if param_schema is None:
                errors.append(f"Unknown parameter: {name}")
                continue
            
            # Type validation
            if not self._validate_type(value, param_schema.type):
                errors.append(
                    f"Parameter '{name}' has invalid type. "
                    f"Expected {param_schema.type.value}, got {type(value).__name__}"
                )
                continue
            
            # Allowed values
            if param_schema.allowed_values is not None:
                if value not in param_schema.allowed_values:
                    errors.append(
                        f"Parameter '{name}' must be one of: {param_schema.allowed_values}"
                    )
            
            # Range validation
            if param_schema.min_value is not None and value < param_schema.min_value:
                errors.append(
                    f"Parameter '{name}' must be >= {param_schema.min_value}"
                )
            
            if param_schema.max_value is not None and value > param_schema.max_value:
                errors.append(
                    f"Parameter '{name}' must be <= {param_schema.max_value}"
                )
            
            # Custom validators
            for validator in param_schema.validators:
                try:
                    if not validator(value):
                        errors.append(f"Parameter '{name}' failed custom validation")
                except Exception as e:
                    errors.append(f"Parameter '{name}' validation error: {e}")
        
        return len(errors) == 0, errors
    
    def _validate_type(self, value: Any, expected: ParamType) -> bool:
        """Validate value type."""
        if expected == ParamType.ANY:
            return True
        
        type_map = {
            ParamType.STRING: str,
            ParamType.INTEGER: int,
            ParamType.FLOAT: (int, float),
            ParamType.BOOLEAN: bool,
            ParamType.LIST: list,
            ParamType.DICT: dict,
            ParamType.FILE_PATH: str,
            ParamType.GLOB_PATTERN: str,
            ParamType.REGEX_PATTERN: str,
            ParamType.SQL_IDENTIFIER: str,
            ParamType.K8S_RESOURCE: str,
        }
        
        expected_type = type_map.get(expected, object)
        return isinstance(value, expected_type)
    
    def execute(self, params: dict[str, Any]) -> ActionResult:
        """
        Execute the action.
        
        Must be overridden by concrete handlers.
        """
        raise NotImplementedError("Subclasses must implement execute()")


class ActionRegistry:
    """
    Central registry for all system actions.
    
    Provides:
    - Action registration and lookup
    - Schema validation
    - Allowlist enforcement
    - Domain-based filtering
    """
    
    def __init__(self):
        self._actions: dict[str, ActionSchema] = {}
        self._handlers: dict[str, ActionHandler] = {}
        self._domains: dict[str, list[str]] = {}
        self._register_builtin_actions()
    
    def _register_builtin_actions(self) -> None:
        """Register built-in actions."""
        # SQL Actions
        self.register(ActionSchema(
            name="sql_select",
            description="Execute SELECT query",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.SQL_IDENTIFIER, description="Table name"),
                ParamSchema(name="columns", type=ParamType.LIST, required=False, default=["*"], description="Columns to select"),
                ParamSchema(name="filters", type=ParamType.LIST, required=False, default=[], description="WHERE conditions"),
                ParamSchema(name="ordering", type=ParamType.LIST, required=False, description="ORDER BY clauses"),
                ParamSchema(name="limit", type=ParamType.INTEGER, required=False, min_value=1, description="LIMIT value"),
            ],
            returns=ParamType.LIST,
            returns_description="List of matching rows",
            tags=["read", "query"],
        ))
        
        self.register(ActionSchema(
            name="sql_insert",
            description="Execute INSERT statement",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.SQL_IDENTIFIER),
                ParamSchema(name="values", type=ParamType.DICT, description="Column-value pairs"),
            ],
            returns=ParamType.INTEGER,
            returns_description="Number of inserted rows",
            is_destructive=True,
            tags=["write", "insert"],
        ))
        
        self.register(ActionSchema(
            name="sql_update",
            description="Execute UPDATE statement",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.SQL_IDENTIFIER),
                ParamSchema(name="values", type=ParamType.DICT, description="Column-value pairs to update"),
                ParamSchema(name="filters", type=ParamType.LIST, description="WHERE conditions"),
            ],
            returns=ParamType.INTEGER,
            returns_description="Number of updated rows",
            requires_confirmation=True,
            is_destructive=True,
            tags=["write", "update"],
        ))
        
        self.register(ActionSchema(
            name="sql_delete",
            description="Execute DELETE statement",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.SQL_IDENTIFIER),
                ParamSchema(name="filters", type=ParamType.LIST, description="WHERE conditions"),
            ],
            returns=ParamType.INTEGER,
            returns_description="Number of deleted rows",
            requires_confirmation=True,
            is_destructive=True,
            tags=["write", "delete"],
        ))
        
        self.register(ActionSchema(
            name="sql_aggregate",
            description="Execute aggregation query",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.SQL_IDENTIFIER),
                ParamSchema(name="aggregations", type=ParamType.LIST, description="Aggregation functions"),
                ParamSchema(name="grouping", type=ParamType.LIST, required=False, description="GROUP BY columns"),
                ParamSchema(name="having", type=ParamType.LIST, required=False, description="HAVING conditions"),
            ],
            returns=ParamType.LIST,
            returns_description="Aggregated results",
            tags=["read", "aggregate"],
        ))
        
        # Shell Actions
        self.register(ActionSchema(
            name="shell_find",
            description="Find files matching criteria",
            domain="shell",
            params=[
                ParamSchema(name="path", type=ParamType.FILE_PATH, required=False, default="."),
                ParamSchema(name="glob", type=ParamType.GLOB_PATTERN, required=False),
                ParamSchema(name="type", type=ParamType.STRING, required=False, allowed_values=["f", "d", "l"]),
                ParamSchema(name="size", type=ParamType.STRING, required=False, description="Size filter (e.g., +100M)"),
                ParamSchema(name="mtime", type=ParamType.INTEGER, required=False, description="Modified time in days"),
            ],
            returns=ParamType.LIST,
            returns_description="List of matching file paths",
            tags=["read", "filesystem"],
        ))
        
        self.register(ActionSchema(
            name="shell_read_file",
            description="Read file contents",
            domain="shell",
            params=[
                ParamSchema(name="path", type=ParamType.FILE_PATH),
                ParamSchema(name="encoding", type=ParamType.STRING, required=False, default="utf-8"),
            ],
            returns=ParamType.STRING,
            returns_description="File contents",
            tags=["read", "filesystem"],
        ))
        
        self.register(ActionSchema(
            name="shell_count_pattern",
            description="Count pattern occurrences in file",
            domain="shell",
            params=[
                ParamSchema(name="file", type=ParamType.FILE_PATH),
                ParamSchema(name="pattern", type=ParamType.REGEX_PATTERN),
                ParamSchema(name="case_sensitive", type=ParamType.BOOLEAN, required=False, default=True),
            ],
            returns=ParamType.INTEGER,
            returns_description="Number of matches",
            tags=["read", "search"],
        ))
        
        self.register(ActionSchema(
            name="shell_process_list",
            description="List running processes",
            domain="shell",
            params=[
                ParamSchema(name="filter", type=ParamType.STRING, required=False),
                ParamSchema(name="sort_by", type=ParamType.STRING, required=False, 
                           allowed_values=["cpu", "memory", "pid", "name"]),
                ParamSchema(name="limit", type=ParamType.INTEGER, required=False, default=10),
            ],
            returns=ParamType.LIST,
            returns_description="List of process info",
            tags=["read", "system"],
        ))
        
        # Docker Actions
        self.register(ActionSchema(
            name="docker_ps",
            description="List containers",
            domain="docker",
            params=[
                ParamSchema(name="all", type=ParamType.BOOLEAN, required=False, default=False),
                ParamSchema(name="filter", type=ParamType.STRING, required=False),
            ],
            returns=ParamType.LIST,
            returns_description="List of containers",
            tags=["read", "containers"],
        ))
        
        self.register(ActionSchema(
            name="docker_run",
            description="Run a container",
            domain="docker",
            params=[
                ParamSchema(name="image", type=ParamType.STRING),
                ParamSchema(name="name", type=ParamType.STRING, required=False),
                ParamSchema(name="ports", type=ParamType.LIST, required=False),
                ParamSchema(name="volumes", type=ParamType.LIST, required=False),
                ParamSchema(name="environment", type=ParamType.DICT, required=False),
                ParamSchema(name="detach", type=ParamType.BOOLEAN, required=False, default=True),
            ],
            returns=ParamType.STRING,
            returns_description="Container ID",
            is_destructive=True,
            tags=["write", "containers"],
        ))
        
        self.register(ActionSchema(
            name="docker_stop",
            description="Stop a container",
            domain="docker",
            params=[
                ParamSchema(name="container", type=ParamType.STRING),
                ParamSchema(name="timeout", type=ParamType.INTEGER, required=False, default=10),
            ],
            returns=ParamType.BOOLEAN,
            returns_description="Success status",
            is_destructive=True,
            tags=["write", "containers"],
        ))
        
        self.register(ActionSchema(
            name="docker_logs",
            description="Get container logs",
            domain="docker",
            params=[
                ParamSchema(name="container", type=ParamType.STRING),
                ParamSchema(name="tail", type=ParamType.INTEGER, required=False, default=100),
                ParamSchema(name="follow", type=ParamType.BOOLEAN, required=False, default=False),
            ],
            returns=ParamType.STRING,
            returns_description="Container logs",
            tags=["read", "containers"],
        ))
        
        # Kubernetes Actions
        self.register(ActionSchema(
            name="k8s_get",
            description="Get Kubernetes resources",
            domain="kubernetes",
            params=[
                ParamSchema(name="resource", type=ParamType.K8S_RESOURCE),
                ParamSchema(name="name", type=ParamType.STRING, required=False),
                ParamSchema(name="namespace", type=ParamType.STRING, required=False, default="default"),
                ParamSchema(name="labels", type=ParamType.DICT, required=False),
                ParamSchema(name="output", type=ParamType.STRING, required=False, 
                           allowed_values=["wide", "yaml", "json"]),
            ],
            returns=ParamType.LIST,
            returns_description="List of resources",
            tags=["read", "k8s"],
        ))
        
        self.register(ActionSchema(
            name="k8s_scale",
            description="Scale a deployment",
            domain="kubernetes",
            params=[
                ParamSchema(name="deployment", type=ParamType.STRING),
                ParamSchema(name="replicas", type=ParamType.INTEGER, min_value=0, max_value=100),
                ParamSchema(name="namespace", type=ParamType.STRING, required=False, default="default"),
            ],
            returns=ParamType.BOOLEAN,
            returns_description="Success status",
            is_destructive=True,
            tags=["write", "k8s", "scaling"],
        ))
        
        self.register(ActionSchema(
            name="k8s_logs",
            description="Get pod logs",
            domain="kubernetes",
            params=[
                ParamSchema(name="pod", type=ParamType.STRING),
                ParamSchema(name="container", type=ParamType.STRING, required=False),
                ParamSchema(name="namespace", type=ParamType.STRING, required=False, default="default"),
                ParamSchema(name="tail", type=ParamType.INTEGER, required=False, default=100),
                ParamSchema(name="follow", type=ParamType.BOOLEAN, required=False, default=False),
            ],
            returns=ParamType.STRING,
            returns_description="Pod logs",
            tags=["read", "k8s"],
        ))
        
        # Utility Actions
        self.register(ActionSchema(
            name="summarize_results",
            description="Summarize results from previous steps",
            domain="utility",
            params=[
                ParamSchema(name="data", type=ParamType.ANY, description="Data to summarize"),
                ParamSchema(name="format", type=ParamType.STRING, required=False, 
                           allowed_values=["text", "table", "json"], default="text"),
            ],
            returns=ParamType.STRING,
            returns_description="Formatted summary",
            tags=["utility", "formatting"],
        ))
        
        self.register(ActionSchema(
            name="filter_results",
            description="Filter results based on criteria",
            domain="utility",
            params=[
                ParamSchema(name="data", type=ParamType.LIST),
                ParamSchema(name="condition", type=ParamType.STRING, description="Filter expression"),
            ],
            returns=ParamType.LIST,
            returns_description="Filtered results",
            tags=["utility", "filtering"],
        ))
        
        self.register(ActionSchema(
            name="sort_results",
            description="Sort results",
            domain="utility",
            params=[
                ParamSchema(name="data", type=ParamType.LIST),
                ParamSchema(name="key", type=ParamType.STRING),
                ParamSchema(name="reverse", type=ParamType.BOOLEAN, required=False, default=False),
            ],
            returns=ParamType.LIST,
            returns_description="Sorted results",
            tags=["utility", "sorting"],
        ))
    
    def register(
        self,
        schema: ActionSchema,
        handler: Optional[ActionHandler] = None,
    ) -> None:
        """
        Register an action schema.
        
        Args:
            schema: Action schema definition
            handler: Optional handler for execution
        """
        self._actions[schema.name] = schema
        
        if handler:
            self._handlers[schema.name] = handler
        
        # Update domain index
        if schema.domain not in self._domains:
            self._domains[schema.domain] = []
        if schema.name not in self._domains[schema.domain]:
            self._domains[schema.domain].append(schema.name)
        
        logger.debug(f"Registered action: {schema.name} (domain: {schema.domain})")
    
    def get(self, name: str) -> Optional[ActionSchema]:
        """Get action schema by name."""
        return self._actions.get(name)
    
    def get_handler(self, name: str) -> Optional[ActionHandler]:
        """Get action handler by name."""
        return self._handlers.get(name)
    
    def has(self, name: str) -> bool:
        """Check if action exists."""
        return name in self._actions
    
    def list_actions(self, domain: Optional[str] = None) -> list[str]:
        """List all registered action names."""
        if domain:
            return self._domains.get(domain, [])
        return list(self._actions.keys())
    
    def list_domains(self) -> list[str]:
        """List all domains."""
        return list(self._domains.keys())
    
    def get_by_tag(self, tag: str) -> list[ActionSchema]:
        """Get all actions with a specific tag."""
        return [a for a in self._actions.values() if tag in a.tags]
    
    def get_destructive_actions(self) -> list[str]:
        """Get all destructive action names."""
        return [name for name, schema in self._actions.items() if schema.is_destructive]
    
    def validate_action(
        self,
        name: str,
        params: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Validate an action call.
        
        Args:
            name: Action name
            params: Action parameters
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if not self.has(name):
            return False, [f"Unknown action: {name}"]
        
        schema = self._actions[name]
        
        # Create temporary handler for validation
        handler = ActionHandler(schema)
        return handler.validate_params(params)
    
    def to_llm_prompt(self, domain: Optional[str] = None) -> str:
        """
        Generate action catalog for LLM prompt.
        
        Args:
            domain: Optional domain filter
            
        Returns:
            Formatted action catalog string
        """
        lines = ["Available actions:"]
        
        actions = self.list_actions(domain)
        
        for name in sorted(actions):
            schema = self._actions[name]
            
            # Action signature
            required = schema.get_required_params()
            optional = schema.get_optional_params()
            
            params_str = ", ".join(required)
            if optional:
                params_str += f" [, {', '.join(optional)}]"
            
            lines.append(f"\n- {name}({params_str})")
            lines.append(f"  Description: {schema.description}")
            lines.append(f"  Returns: {schema.returns.value} - {schema.returns_description}")
            
            if schema.requires_confirmation:
                lines.append("  ⚠️ Requires confirmation")
            
            if schema.is_destructive:
                lines.append("  🔴 Destructive action")
        
        return "\n".join(lines)


# Global registry instance
_registry: Optional[ActionRegistry] = None


def get_registry() -> ActionRegistry:
    """Get the global action registry instance."""
    global _registry
    if _registry is None:
        _registry = ActionRegistry()
    return _registry


__all__ = [
    "ActionRegistry",
    "ActionSchema",
    "ActionResult",
    "ActionHandler",
    "ParamSchema",
    "ParamType",
    "get_registry",
]
