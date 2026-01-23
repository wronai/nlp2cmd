"""
Dynamic adapter that uses extracted schemas instead of hardcoded keywords.

This adapter dynamically generates commands based on extracted schemas
from OpenAPI specs, shell help, Python code, etc.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

from nlp2cmd.adapters.base import BaseDSLAdapter, AdapterConfig, SafetyPolicy
from nlp2cmd.schema_extraction import (
    DynamicSchemaRegistry,
    CommandSchema,
    CommandParameter,
    ExtractedSchema,
)


class DynamicSafetyPolicy(SafetyPolicy):
    """Enhanced safety policy that adapts based on extracted schemas."""
    
    def __init__(self):
        super().__init__()
        self.blocked_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+/\*',
            r'mkfs',
            r'dd\s+if=/dev/zero',
            r':\(\)\{\:\|:&\}\;',  # fork bomb
            r'chmod\s+-R\s+777\s+/',
            r'chown\s+-R',
            r'sudo\s+rm',
            r'sudo\s+chmod',
            r'sudo\s+chown',
        ]
        self.require_confirmation_patterns = [
            r'rm\s+',
            r'rmdir\s+',
            r'kill\s+',
            r'killall\s+',
            r'shutdown\s+',
            r'reboot\s+',
            r'systemctl\s+stop\s+',
            r'docker\s+rm\s+',
            r'docker\s+rmi\s+',
        ]
    
    def check_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check if command is safe based on dynamic patterns."""
        command_lower = command.lower()
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, command_lower):
                return {
                    "allowed": False,
                    "reason": f"Command matches blocked pattern: {pattern}",
                    "risk_level": "high",
                }
        
        # Check confirmation patterns
        for pattern in self.require_confirmation_patterns:
            if re.search(pattern, command_lower):
                return {
                    "allowed": True,
                    "requires_confirmation": True,
                    "reason": f"Command requires confirmation: {pattern}",
                    "risk_level": "medium",
                }
        
        return {
            "allowed": True,
            "requires_confirmation": False,
            "risk_level": "low",
        }


class DynamicAdapter(BaseDSLAdapter):
    """
    Dynamic adapter that uses extracted schemas instead of hardcoded patterns.
    
    This adapter can work with:
    - OpenAPI specifications
    - Shell command help
    - Python Click applications
    - Generic Python functions with decorators
    """
    
    DSL_NAME = "dynamic"
    DSL_VERSION = "2.0"
    
    def __init__(
        self,
        schema_registry: Optional[DynamicSchemaRegistry] = None,
        config: Optional[AdapterConfig] = None,
        safety_policy: Optional[SafetyPolicy] = None,
    ):
        """Initialize dynamic adapter."""
        if isinstance(config, dict):
            config = AdapterConfig(**config)
        super().__init__(config, safety_policy or DynamicSafetyPolicy())
        
        # Use auto_save_path from config if provided
        auto_save_path = config.custom_options.get("auto_save_path")
        self.registry = schema_registry or DynamicSchemaRegistry(auto_save_path=auto_save_path)
        self._command_cache: Dict[str, CommandSchema] = {}
        
        # Initialize with some common shell commands
        if bool(self.config.custom_options.get("load_common_commands", True)):
            self._load_common_commands()

    def check_safety(self, command: str) -> dict[str, Any]:
        policy = self.config.safety_policy
        check_fn = getattr(policy, "check_command", None)
        if callable(check_fn):
            return check_fn(command)
        return super().check_safety(command)
    
    def _load_common_commands(self):
        """Load schemas for common shell commands."""
        common_commands = [
            'find', 'grep', 'sed', 'awk', 'ls', 'mkdir', 'rm', 'cp', 'mv',
            'ps', 'top', 'kill', 'systemctl', 'docker', 'git', 'curl', 'ping',
            'df', 'du', 'tar'
        ]
        
        for cmd in common_commands:
            try:
                # Register with shell help - templates will be generated automatically
                self.registry.register_shell_help(cmd)
            except Exception:
                # If shell help fails, create minimal schema without template
                from nlp2cmd.schema_extraction import CommandSchema
                schema = CommandSchema(
                    name=cmd,
                    description=f"{cmd} command",
                    category="shell",
                    parameters=[],
                    examples=[f"{cmd} --help"],
                    patterns=[cmd],
                    source_type="shell_common",
                )
                self.registry.register_command(schema)
    
    def register_schema_source(self, source: str, source_type: str = "auto") -> ExtractedSchema:
        """Register a new schema source."""
        if source_type == "auto":
            # Auto-detect source type
            if source.startswith(('http://', 'https://')):
                if any(ext in source for ext in ['.json', '.yaml', '.yml']):
                    return self.registry.register_openapi_schema(source)
            elif source.endswith(('.py', '.pyx')):
                return self.registry.register_python_code(source)
            elif source.endswith('.sh'):
                return self.registry.register_shell_script(source)
            elif source.endswith('.mk') or source.endswith('/Makefile') or source.endswith('Makefile'):
                return self.registry.register_makefile(source)
            elif source.endswith(('.json', '.yaml', '.yml')):
                # Try to detect AppSpec
                if source.endswith('.json'):
                    try:
                        p = Path(source)
                        if p.exists():
                            data = json.loads(p.read_text(encoding="utf-8"))
                            fmt = data.get("format")
                            if fmt == "app2schema.appspec":
                                return self.registry.register_appspec_export(source)
                            if fmt == "nlp2cmd.dynamic_schema_export":
                                return self.registry.register_dynamic_export(source)
                    except Exception:
                        pass  # Fall back to OpenAPI
                return self.registry.register_openapi_schema(source)
            else:
                # Assume it's a shell command
                return self.registry.register_shell_help(source)
        
        elif source_type == "openapi":
            return self.registry.register_openapi_schema(source)
        elif source_type == "shell":
            return self.registry.register_shell_help(source)
        elif source_type == "python":
            return self.registry.register_python_code(source)
        elif source_type in {"shell_script", "sh"}:
            return self.registry.register_shell_script(source)
        elif source_type in {"makefile", "make"}:
            return self.registry.register_makefile(source)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def generate(self, plan: Dict[str, Any]) -> str:
        """Generate command from execution plan using dynamic schemas."""
        intent = plan.get("intent", "")
        entities = plan.get("entities", {})
        text = plan.get("text", "") or plan.get("query", "") or ""

        # If the NLP backend produced a full shell-like command (e.g. "git status"),
        # prefer returning it directly when the base command exists in the registry.
        try:
            tokens = shlex.split(str(intent)) if intent else []
        except Exception:
            tokens = str(intent).split() if intent else []

        if len(tokens) >= 2:
            base = tokens[0]
            if self.registry.get_command_by_name(base) is not None:
                return str(intent)
        
        # Search for matching commands
        matching_commands = self._find_matching_commands(intent, entities, text)
        
        if not matching_commands:
            # Try to find commands by searching the text
            matching_commands = self.registry.search_commands(text, limit=5)
        
        if not matching_commands:
            return f"# No matching command found for: {text}"
        
        # Use the best match
        best_command = matching_commands[0]
        
        # Generate command based on the schema
        generated_command = self._generate_from_schema(best_command, entities, text)
        
        return generated_command
    
    def _find_matching_commands(self, intent: str, entities: Dict[str, Any], text: str) -> List[CommandSchema]:
        """Find commands that match the intent and entities."""
        matches = []
        
        for command in self.registry.get_all_commands():
            score = 0
            
            # Check intent/command name match
            if intent.lower() in command.name.lower():
                score += 10
            elif command.name.lower() in intent.lower():
                score += 8
            
            # Check pattern matches
            for pattern in command.patterns:
                if intent.lower() in pattern.lower():
                    score += 5
                elif pattern.lower() in intent.lower():
                    score += 3
            
            # Check entity matches with parameters
            for param in command.parameters:
                if param.name in entities:
                    score += 2
            
            # Check text matches
            text_lower = text.lower()
            if any(word in text_lower for word in command.name.lower().split()):
                score += 3
            
            if score > 0:
                matches.append((command, score))
        
        # Sort by score and return matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return [cmd for cmd, _ in matches]
    
    def _generate_from_schema(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate a command based on the schema and entities."""
        if schema.source_type in {"shell_help", "shell_script"}:
            return self._generate_shell_command(schema, entities, text)
        elif schema.source_type == "openapi":
            return self._generate_api_command(schema, entities, text)
        elif schema.source_type in ["python_click", "python_generic"]:
            return self._generate_python_command(schema, entities, text)
        elif schema.source_type == "makefile":
            return self._generate_make_command(schema, entities)
        elif schema.source_type == "web_dom":
            return self._generate_web_dql(schema, entities)
        else:
            return self._generate_generic_command(schema, entities, text)

    def _generate_make_command(self, schema: CommandSchema, entities: Dict[str, Any]) -> str:
        parts = ["make", schema.name]

        # Treat schema.parameters as Makefile variables (VAR=value)
        for param in schema.parameters:
            if param.name in entities and entities.get(param.name) is not None:
                parts.append(f"{param.name}={entities[param.name]}")

        return " ".join(parts)

    def _generate_web_dql(self, schema: CommandSchema, entities: Dict[str, Any]) -> str:
        action = str(schema.metadata.get("action") or "")
        selector = str(schema.metadata.get("selector") or "")

        params: dict[str, Any] = {}
        if action in {"type", "select"}:
            value = None
            if "value" in entities and entities.get("value") is not None:
                value = entities.get("value")
            elif "quoted_string" in entities and entities.get("quoted_string") is not None:
                value = entities.get("quoted_string")
            elif "text" in entities and entities.get("text") is not None:
                value = entities.get("text")
            elif "input" in entities and entities.get("input") is not None:
                value = entities.get("input")

            if value is not None:
                params["value"] = value

        payload = {
            "dsl": "dom_dql.v1",
            "action": action,
            "target": {
                "by": "css" if selector.startswith(("#", ".")) or selector.startswith("input") else "auto",
                "value": selector,
            },
            "params": params,
        }
        return json.dumps(payload, ensure_ascii=False)
    
    def _generate_from_template(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate command using template if available."""
        template = schema.template or schema.metadata.get('template')
        if not template:
            return None
        
        text_lower = text.lower()
        
        # Extract values from text for template variables
        template_vars = {}
        
        # Size extraction (e.g., "100MB", "1GB")
        import re
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|GB|KB|M|G|K)', text, re.IGNORECASE)
        if size_match:
            size = size_match.group(1)
            unit = size_match.group(2)
            if unit.upper() in ['MB', 'M']:
                template_vars['size'] = f"+{size}M"
            elif unit.upper() in ['GB', 'G']:
                template_vars['size'] = f"+{size}G"
            elif unit.upper() in ['KB', 'K']:
                template_vars['size'] = f"+{size}k"
        
        # Time extraction (e.g., "last week", "recent")
        if any(k in text_lower for k in ['last week', 'week', 'recent']):
            template_vars['days'] = '7'
        elif any(k in text_lower for k in ['today', 'yesterday']):
            template_vars['days'] = '1'
        elif any(k in text_lower for k in ['last month', 'month']):
            template_vars['days'] = '30'
        
        # Pattern extraction
        if 'todo' in text_lower:
            template_vars['pattern'] = 'TODO'
        elif 'python' in text_lower:
            template_vars['pattern'] = '--include=*.py'
        
        # Path extraction
        if any(k in text_lower for k in ['current directory', 'this directory', 'here']):
            template_vars['path'] = '.'
        elif 'logs' in text_lower:
            template_vars['path'] = 'logs/'
            template_vars['source'] = 'logs'
            template_vars['archive'] = 'logs'
        
        # Subcommand extraction
        subcommand_map = {
            'docker': {
                'list': 'ps -a',
                'images': 'images',
                'logs': 'logs',
                'run': 'run',
            },
            'git': {
                'status': 'status',
                'log': 'log',
                'diff': 'diff',
                'branch': 'branch',
                'add': 'add',
                'commit': 'commit',
                'push': 'push',
                'pull': 'pull',
            }
        }
        
        if schema.name in subcommand_map:
            for keyword, subcmd in subcommand_map[schema.name].items():
                if keyword in text_lower:
                    template_vars['subcommand'] = subcmd
                    break
        
        # Special cases
        if 'top 10' in text_lower or 'top processes' in text_lower:
            template_vars['limit'] = '10'
        
        # Fill template
        try:
            cmd = template.format(**template_vars)
            # Clean up double spaces and trailing spaces
            cmd = ' '.join(cmd.split())
            return cmd
        except KeyError:
            # Missing template variable, try to fill with defaults
            default_vars = {
                'size': '+100M',
                'days': '7',
                'path': '.',
                'pattern': 'TODO',
                'subcommand': 'help',
                'options': '',
                'limit': '10',
                'archive': 'archive',
                'source': 'directory',
            }
            
            # Merge with extracted vars
            final_vars = {**default_vars, **template_vars}
            
            try:
                cmd = template.format(**final_vars)
                # Clean up double spaces and trailing spaces
                cmd = ' '.join(cmd.split())
                return cmd
            except KeyError as e:
                # Still missing variables, return template with placeholders
                return template
    
    def _generate_shell_command(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate shell command from schema."""
        # First try template-based generation
        template_cmd = self._generate_from_template(schema, entities, text)
        if template_cmd:
            return template_cmd
        
        # Fallback to heuristics if no template
        command_parts = [schema.name]
        text_lower = (text or "").lower()

        # Minimal heuristics for fallback
        if schema.name == "ps" and "processes" in text_lower:
            command_parts.extend(["aux", "|", "head", "-10"])
            return " ".join(command_parts)
        
        if schema.name == "find" and "files" in text_lower:
            command_parts.append(".")
            return " ".join(command_parts)
        
        # Add parameters based on entities
        for param in schema.parameters:
            if param.name in entities:
                value = entities[param.name]
                
                # Format parameter based on type
                if param.type == "boolean":
                    if value:
                        command_parts.append(f"--{param.name.replace('_', '-')}")
                elif param.type == "file":
                    command_parts.extend([f"--{param.name.replace('_', '-')}", str(value)])
                else:
                    command_parts.extend([f"--{param.name.replace('_', '-')}", str(value)])
        
        # Add any remaining entities as positional arguments
        for key, value in entities.items():
            if key not in [p.name for p in schema.parameters] and value:
                command_parts.append(str(value))
        
        return " ".join(command_parts)
    
    def _generate_api_command(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate API command (curl) from OpenAPI schema."""
        metadata = schema.metadata
        method = metadata.get("method", "GET").upper()
        path = metadata.get("path", "/")
        base_url = str(metadata.get("base_url") or "")
        
        # Replace path parameters
        for param in schema.parameters:
            if param.location == "path" and param.name in entities and f"{{{param.name}}}" in path:
                path = path.replace(f"{{{param.name}}}", str(entities[param.name]))

        url = path
        if base_url and not url.startswith(("http://", "https://")):
            if url.startswith("/"):
                url = base_url.rstrip("/") + url
            else:
                url = base_url.rstrip("/") + "/" + url
        
        # Build curl command
        curl_parts = ["curl", "-X", method]
        
        # Add query parameters
        query_params = []
        for param in schema.parameters:
            if param.location == "query" and param.name in entities:
                query_params.append(f"{param.name}={entities[param.name]}")
        
        if query_params:
            url += "?" + "&".join(query_params)
        
        curl_parts.append(url)
        
        # Add headers
        curl_parts.extend(["-H", "Content-Type: application/json"])
        
        # Add request body if it's a POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"]:
            body_params = {}
            for param in schema.parameters:
                if param.location == "body" and param.name in entities:
                    body_params[param.name] = entities[param.name]
            
            if body_params:
                curl_parts.extend(["-d", json.dumps(body_params)])
        
        return " ".join(curl_parts)
    
    def _generate_python_command(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate Python command from schema."""
        if schema.source_type == "python_click":
            # Click command
            command_parts = ["python", "-c", f"import {schema.metadata.get('module', 'main')}; {schema.name}()"]
            
            # Add parameters
            for param in schema.parameters:
                if param.name in entities:
                    value = entities[param.name]
                    if param.type == "boolean":
                        if value:
                            command_parts.append(f"--{param.name.replace('_', '-')}")
                    else:
                        command_parts.extend([f"--{param.name.replace('_', '-')}", str(value)])
            
            return " ".join(command_parts)
        else:
            # Generic Python function
            args = []
            for param in schema.parameters:
                if param.name in entities:
                    args.append(f"{param.name}={repr(entities[param.name])}")
            
            if args:
                return f"python -c \"import {schema.metadata.get('module', 'main')}; {schema.name}({', '.join(args)})\""
            else:
                return f"python -c \"import {schema.metadata.get('module', 'main')}; {schema.name}()\""
    
    def _generate_generic_command(self, schema: CommandSchema, entities: Dict[str, Any], text: str) -> str:
        """Generate generic command from schema."""
        # Fallback: use examples or patterns
        if schema.examples:
            example = schema.examples[0]
            
            # Try to substitute entities in the example
            for key, value in entities.items():
                if f"{{{key}}}" in example:
                    example = example.replace(f"{{{key}}}", str(value))
            
            return example
        
        # Fallback to command name with parameters
        command_parts = [schema.name]
        for param in schema.parameters:
            if param.name in entities:
                command_parts.extend([f"--{param.name.replace('_', '-')}", str(entities[param.name])])
        
        return " ".join(command_parts)
    
    def get_available_commands(self) -> List[str]:
        """Get list of all available command names."""
        return [cmd.name for cmd in self.registry.get_all_commands()]
    
    def get_command_categories(self) -> List[str]:
        """Get list of all command categories."""
        categories = set()
        for cmd in self.registry.get_all_commands():
            categories.add(cmd.category)
        return sorted(list(categories))
    
    def search_commands(self, query: str, limit: int = 10) -> List[CommandSchema]:
        """Search for commands matching the query."""
        return self.registry.search_commands(query, limit)
    
    def validate_syntax(self, command: str) -> Dict[str, Any]:
        """Validate command syntax."""
        # Basic syntax validation
        if not command or not command.strip():
            return {
                "valid": False,
                "errors": ["Command is empty"],
                "warnings": []
            }
        
        # Check for basic shell command patterns
        if any(char in command for char in ['|', '&', ';', '>', '<']):
            return {
                "valid": True,
                "errors": [],
                "warnings": ["Command contains shell operators - please verify"]
            }
        
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }
    
    def get_command_help(self, command_name: str) -> Optional[str]:
        """Get help text for a specific command."""
        command = self.registry.get_command_by_name(command_name)
        if command:
            help_text = f"Command: {command.name}\n"
            help_text += f"Description: {command.description}\n"
            help_text += f"Category: {command.category}\n"
            
            if command.parameters:
                help_text += "\nParameters:\n"
                for param in command.parameters:
                    help_text += f"  --{param.name.replace('_', '-')} ({param.type})"
                    if param.required:
                        help_text += " [required]"
                    if param.description:
                        help_text += f": {param.description}"
                    help_text += "\n"
            
            if command.examples:
                help_text += "\nExamples:\n"
                for example in command.examples:
                    help_text += f"  {example}\n"
            
            return help_text
        
        return None
