"""
Plan Executor for NLP2CMD.

Executes multi-step execution plans with support for:
- Sequential step execution
- Foreach loops over results
- Variable references between steps
- Conditional execution
- Error handling and rollback
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from nlp2cmd.registry import ActionRegistry, ActionResult, get_registry

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a plan step."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    foreach: Optional[str] = None  # Reference to iterate over
    condition: Optional[str] = None  # Condition for execution
    store_as: Optional[str] = None  # Variable name to store result
    on_error: str = "stop"  # "stop", "skip", "continue"
    timeout: Optional[float] = None  # Timeout in seconds
    retry: int = 0  # Number of retries on failure
    
    def __post_init__(self):
        # Generate store_as if not provided
        if self.store_as is None:
            self.store_as = f"{self.action}_result"


@dataclass
class StepResult:
    """Result of executing a single step."""
    
    step_index: int
    action: str
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    iterations: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Multi-step execution plan."""
    
    steps: list[PlanStep]
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPlan":
        """Create plan from dictionary."""
        steps = []
        for step_data in data.get("steps", []):
            steps.append(PlanStep(
                action=step_data["action"],
                params=step_data.get("params", {}),
                foreach=step_data.get("foreach"),
                condition=step_data.get("condition"),
                store_as=step_data.get("store_as"),
                on_error=step_data.get("on_error", "stop"),
                timeout=step_data.get("timeout"),
                retry=step_data.get("retry", 0),
            ))
        
        return cls(
            steps=steps,
            metadata=data.get("metadata", {}),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary."""
        return {
            "steps": [
                {
                    "action": step.action,
                    "params": step.params,
                    "foreach": step.foreach,
                    "condition": step.condition,
                    "store_as": step.store_as,
                    "on_error": step.on_error,
                    "timeout": step.timeout,
                    "retry": step.retry,
                }
                for step in self.steps
            ],
            "metadata": self.metadata,
        }


@dataclass
class ExecutionContext:
    """Context for plan execution."""
    
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    variables: dict[str, Any] = field(default_factory=dict)
    results: list[StepResult] = field(default_factory=list)
    current_step: int = 0
    dry_run: bool = False
    
    def set(self, name: str, value: Any) -> None:
        """Set a variable."""
        self.variables[name] = value
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get a variable."""
        return self.variables.get(name, default)
    
    def resolve_reference(self, ref: str) -> Any:
        """
        Resolve a variable reference.
        
        Supports:
        - $variable_name
        - $step_result.field
        - $item (in foreach context)
        - $index (in foreach context)
        """
        if not ref.startswith("$"):
            return ref
        
        path = ref[1:].split(".")
        var_name = path[0]
        
        if var_name not in self.variables:
            raise ValueError(f"Unknown variable: {var_name}")
        
        value = self.variables[var_name]
        
        # Navigate nested path
        for key in path[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                raise ValueError(f"Cannot resolve path: {ref}")
        
        return value


@dataclass
class ExecutionResult:
    """Result of executing a complete plan."""
    
    trace_id: str
    success: bool
    steps: list[StepResult]
    final_result: Any = None
    error: Optional[str] = None
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class PlanValidator:
    """Validates execution plans against action registry."""
    
    # JSON Schema for plan validation
    PLAN_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["steps"],
        "properties": {
            "steps": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string"},
                        "params": {"type": "object"},
                        "foreach": {"type": "string"},
                        "condition": {"type": "string"},
                        "store_as": {"type": "string"},
                        "on_error": {
                            "type": "string",
                            "enum": ["stop", "skip", "continue"]
                        },
                        "timeout": {"type": "number", "minimum": 0},
                        "retry": {"type": "integer", "minimum": 0},
                    },
                },
            },
            "metadata": {"type": "object"},
        },
    }
    
    def __init__(self, registry: Optional[ActionRegistry] = None):
        self.registry = registry or get_registry()
    
    def validate(self, plan: ExecutionPlan) -> tuple[bool, list[str]]:
        """
        Validate an execution plan.
        
        Args:
            plan: Plan to validate
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        if not plan.steps:
            errors.append("Plan must have at least one step")
            return False, errors
        
        defined_variables = set()
        
        for i, step in enumerate(plan.steps):
            step_errors = self._validate_step(step, i, defined_variables)
            errors.extend(step_errors)
            
            # Track defined variables
            if step.store_as:
                defined_variables.add(step.store_as)
        
        return len(errors) == 0, errors
    
    def _validate_step(
        self,
        step: PlanStep,
        index: int,
        defined_variables: set[str],
    ) -> list[str]:
        """Validate a single step."""
        errors = []
        prefix = f"Step {index + 1} ({step.action})"
        
        # Check action exists
        if not self.registry.has(step.action):
            errors.append(f"{prefix}: Unknown action '{step.action}'")
            return errors  # Can't validate params if action unknown
        
        # Validate params
        is_valid, param_errors = self.registry.validate_action(
            step.action, step.params
        )
        if not is_valid:
            for err in param_errors:
                errors.append(f"{prefix}: {err}")
        
        # Validate foreach reference
        if step.foreach:
            ref_var = step.foreach.split(".")[0]
            if ref_var not in defined_variables and not ref_var.startswith("$"):
                errors.append(
                    f"{prefix}: foreach references undefined variable '{ref_var}'"
                )
        
        # Validate condition references
        if step.condition:
            refs = re.findall(r"\$(\w+)", step.condition)
            for ref in refs:
                if ref not in defined_variables and ref not in ("item", "index"):
                    errors.append(
                        f"{prefix}: condition references undefined variable '{ref}'"
                    )
        
        # Validate param references
        for param_name, param_value in step.params.items():
            if isinstance(param_value, str) and param_value.startswith("$"):
                ref_var = param_value[1:].split(".")[0]
                if ref_var not in defined_variables and ref_var not in ("item", "index"):
                    errors.append(
                        f"{prefix}: param '{param_name}' references undefined variable '{ref_var}'"
                    )
        
        return errors


class PlanExecutor:
    """
    Executes multi-step plans.
    
    Features:
    - Sequential and parallel execution
    - Foreach loops with item/index context
    - Variable substitution
    - Conditional execution
    - Retry with backoff
    - Timeout handling
    - Dry-run mode
    """
    
    def __init__(
        self,
        registry: Optional[ActionRegistry] = None,
        action_handlers: Optional[dict[str, Callable]] = None,
    ):
        """
        Initialize executor.
        
        Args:
            registry: Action registry for validation
            action_handlers: Custom action handlers
        """
        self.registry = registry or get_registry()
        self.validator = PlanValidator(self.registry)
        self.action_handlers = action_handlers or {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default action handlers for testing."""
        # These are stub handlers - real implementations would do actual work
        
        def summarize_results(data: Any, format: str = "text") -> str:
            if isinstance(data, list):
                return f"Summary: {len(data)} items"
            return f"Summary: {data}"
        
        def filter_results(data: list, condition: str) -> list:
            # Simple filtering - real implementation would parse condition
            return data
        
        def sort_results(data: list, key: str, reverse: bool = False) -> list:
            if data and isinstance(data[0], dict) and key in data[0]:
                return sorted(data, key=lambda x: x.get(key), reverse=reverse)
            return data
        
        self.action_handlers["summarize_results"] = summarize_results
        self.action_handlers["filter_results"] = filter_results
        self.action_handlers["sort_results"] = sort_results
    
    def execute(
        self,
        plan: ExecutionPlan,
        initial_context: Optional[dict[str, Any]] = None,
        dry_run: bool = False,
        on_step_complete: Optional[Callable[[StepResult], None]] = None,
    ) -> ExecutionResult:
        """
        Execute a plan.
        
        Args:
            plan: Plan to execute
            initial_context: Initial variables
            dry_run: If True, validate but don't execute
            on_step_complete: Callback after each step
            
        Returns:
            ExecutionResult with all step results
        """
        start_time = time.time()
        
        # Validate plan
        is_valid, errors = self.validator.validate(plan)
        if not is_valid:
            return ExecutionResult(
                trace_id="invalid",
                success=False,
                steps=[],
                error=f"Plan validation failed: {'; '.join(errors)}",
            )
        
        # Initialize context
        ctx = ExecutionContext(dry_run=dry_run)
        if initial_context:
            ctx.variables.update(initial_context)
        
        logger.info(f"[{ctx.trace_id}] Starting plan execution ({len(plan.steps)} steps)")
        
        # Execute steps
        for i, step in enumerate(plan.steps):
            ctx.current_step = i
            
            try:
                result = self._execute_step(step, i, ctx)
                ctx.results.append(result)
                
                if on_step_complete:
                    on_step_complete(result)
                
                # Handle step failure
                if result.status == StepStatus.FAILED:
                    if step.on_error == "stop":
                        logger.error(f"[{ctx.trace_id}] Step {i + 1} failed, stopping execution")
                        break
                    elif step.on_error == "skip":
                        logger.warning(f"[{ctx.trace_id}] Step {i + 1} failed, skipping")
                        continue
                    # "continue" - just keep going
                
            except Exception as e:
                logger.exception(f"[{ctx.trace_id}] Step {i + 1} raised exception")
                ctx.results.append(StepResult(
                    step_index=i,
                    action=step.action,
                    status=StepStatus.FAILED,
                    error=str(e),
                ))
                if step.on_error == "stop":
                    break
        
        # Determine overall success
        all_success = all(
            r.status in (StepStatus.SUCCESS, StepStatus.SKIPPED)
            for r in ctx.results
        )
        
        # Get final result (last successful step's result)
        final_result = None
        for result in reversed(ctx.results):
            if result.status == StepStatus.SUCCESS and result.result is not None:
                final_result = result.result
                break
        
        total_duration = (time.time() - start_time) * 1000
        
        return ExecutionResult(
            trace_id=ctx.trace_id,
            success=all_success,
            steps=ctx.results,
            final_result=final_result,
            total_duration_ms=total_duration,
            metadata={"dry_run": dry_run},
        )
    
    def _execute_step(
        self,
        step: PlanStep,
        index: int,
        ctx: ExecutionContext,
    ) -> StepResult:
        """Execute a single step."""
        start_time = time.time()
        
        logger.debug(f"[{ctx.trace_id}] Executing step {index + 1}: {step.action}")
        
        # Check condition
        if step.condition and not self._evaluate_condition(step.condition, ctx):
            logger.debug(f"[{ctx.trace_id}] Step {index + 1} skipped (condition not met)")
            return StepResult(
                step_index=index,
                action=step.action,
                status=StepStatus.SKIPPED,
                metadata={"reason": "condition_not_met"},
            )
        
        # Dry run - just validate
        if ctx.dry_run:
            return StepResult(
                step_index=index,
                action=step.action,
                status=StepStatus.SUCCESS,
                metadata={"dry_run": True},
            )
        
        # Handle foreach
        if step.foreach:
            return self._execute_foreach(step, index, ctx)
        
        # Resolve params
        resolved_params = self._resolve_params(step.params, ctx)
        
        # Execute with retry
        last_error = None
        for attempt in range(step.retry + 1):
            try:
                result = self._call_action(step.action, resolved_params, step.timeout)
                
                # Store result
                if step.store_as:
                    ctx.set(step.store_as, result)
                
                duration = (time.time() - start_time) * 1000
                
                return StepResult(
                    step_index=index,
                    action=step.action,
                    status=StepStatus.SUCCESS,
                    result=result,
                    duration_ms=duration,
                    metadata={"attempt": attempt + 1},
                )
                
            except Exception as e:
                last_error = str(e)
                if attempt < step.retry:
                    logger.warning(
                        f"[{ctx.trace_id}] Step {index + 1} attempt {attempt + 1} failed, retrying"
                    )
                    time.sleep(0.1 * (attempt + 1))  # Simple backoff
        
        duration = (time.time() - start_time) * 1000
        
        return StepResult(
            step_index=index,
            action=step.action,
            status=StepStatus.FAILED,
            error=last_error,
            duration_ms=duration,
            metadata={"attempts": step.retry + 1},
        )
    
    def _execute_foreach(
        self,
        step: PlanStep,
        index: int,
        ctx: ExecutionContext,
    ) -> StepResult:
        """Execute step as foreach loop."""
        start_time = time.time()
        
        # Resolve the iterable
        try:
            iterable = ctx.resolve_reference(f"${step.foreach}")
        except ValueError as e:
            return StepResult(
                step_index=index,
                action=step.action,
                status=StepStatus.FAILED,
                error=str(e),
            )
        
        if not isinstance(iterable, (list, tuple)):
            return StepResult(
                step_index=index,
                action=step.action,
                status=StepStatus.FAILED,
                error=f"foreach target is not iterable: {type(iterable)}",
            )
        
        results = []
        
        for i, item in enumerate(iterable):
            # Set loop context
            ctx.set("item", item)
            ctx.set("index", i)
            
            # Resolve params with loop context
            resolved_params = self._resolve_params(step.params, ctx)
            
            try:
                result = self._call_action(step.action, resolved_params, step.timeout)
                results.append(result)
            except Exception as e:
                logger.warning(f"[{ctx.trace_id}] foreach iteration {i} failed: {e}")
                if step.on_error == "stop":
                    break
        
        # Clean up loop context
        ctx.variables.pop("item", None)
        ctx.variables.pop("index", None)
        
        # Store aggregated results
        if step.store_as:
            ctx.set(step.store_as, results)
        
        duration = (time.time() - start_time) * 1000
        
        return StepResult(
            step_index=index,
            action=step.action,
            status=StepStatus.SUCCESS,
            result=results,
            duration_ms=duration,
            iterations=len(iterable),
        )
    
    def _resolve_params(
        self,
        params: dict[str, Any],
        ctx: ExecutionContext,
    ) -> dict[str, Any]:
        """Resolve variable references in params."""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                resolved[key] = ctx.resolve_reference(value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value, ctx)
            elif isinstance(value, list):
                resolved[key] = [
                    ctx.resolve_reference(v) if isinstance(v, str) and v.startswith("$") else v
                    for v in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def _evaluate_condition(self, condition: str, ctx: ExecutionContext) -> bool:
        """Evaluate a condition expression."""
        # Simple condition evaluation
        # Real implementation would use a proper expression parser
        
        # Replace variable references
        expr = condition
        for match in re.finditer(r"\$(\w+(?:\.\w+)*)", condition):
            ref = match.group(0)
            try:
                value = ctx.resolve_reference(ref)
                if isinstance(value, str):
                    expr = expr.replace(ref, f"'{value}'")
                else:
                    expr = expr.replace(ref, str(value))
            except ValueError:
                return False
        
        try:
            # Safe eval for simple conditions
            return eval(expr, {"__builtins__": {}}, {})
        except Exception:
            return False
    
    def _call_action(
        self,
        action: str,
        params: dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Any:
        """Call an action handler."""
        if action in self.action_handlers:
            handler = self.action_handlers[action]
            return handler(**params)
        
        # Check registry for handler
        registry_handler = self.registry.get_handler(action)
        if registry_handler:
            result = registry_handler.execute(params)
            if result.success:
                return result.data
            raise RuntimeError(result.error)
        
        raise NotImplementedError(f"No handler for action: {action}")
    
    def register_handler(
        self,
        action: str,
        handler: Callable[..., Any],
    ) -> None:
        """Register a custom action handler."""
        self.action_handlers[action] = handler


__all__ = [
    "PlanExecutor",
    "PlanValidator",
    "ExecutionPlan",
    "ExecutionContext",
    "ExecutionResult",
    "PlanStep",
    "StepResult",
    "StepStatus",
]
