"""
Dynamic schema extraction and analysis for NLP2CMD.

This module provides dynamic schema parsing capabilities for:
- OpenAPI/Swagger specifications
- Shell command help output
- Python source code with decorators
- Click applications
- And other command sources

Instead of hardcoded keywords, this module dynamically extracts
command patterns, parameters, and metadata from various sources.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
import yaml
from pydantic import BaseModel, Field


def _ast_unparse(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def _python_annotation_to_param_type(annotation: Optional[ast.AST]) -> str:
    if annotation is None:
        return "string"

    txt = _ast_unparse(annotation)
    txt_lower = txt.lower()

    if txt_lower in {"int", "integer"}:
        return "integer"
    if txt_lower in {"float", "double", "number"}:
        return "number"
    if txt_lower in {"bool", "boolean"}:
        return "boolean"
    if "path" in txt_lower:
        return "path"
    if txt_lower.startswith("list[") or txt_lower.startswith("set[") or txt_lower.startswith("tuple["):
        return "array"
    if txt_lower.startswith("dict["):
        return "object"

    return "string"


def _shell_opt_to_param_name(opt: str) -> str:
    return opt.lstrip("-").replace("-", "_")


def _dedupe_params(params: list["CommandParameter"]) -> list["CommandParameter"]:
    seen: set[str] = set()
    out: list[CommandParameter] = []
    for p in params:
        if p.name in seen:
            continue
        seen.add(p.name)
        out.append(p)
    return out


@dataclass
class CommandParameter:
    """Represents a command parameter extracted from schema."""
    
    name: str
    type: str
    description: str = ""
    required: bool = False
    default: Any = None
    choices: List[str] = field(default_factory=list)
    pattern: Optional[str] = None
    example: Optional[str] = None
    location: str = "unknown"


@dataclass
class CommandSchema:
    """Dynamic command schema extracted from various sources."""
    
    name: str
    description: str
    category: str = "general"
    parameters: List[CommandParameter] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    source_type: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedSchema:
    """Container for extracted schemas from a source."""
    
    source: str
    source_type: str
    commands: List[CommandSchema] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OpenAPISchemaExtractor:
    """Extract command schemas from OpenAPI/Swagger specifications."""
    
    def __init__(self, http_client: Optional[httpx.Client] = None):
        self.client = http_client or httpx.Client()
    
    def extract_from_url(self, url: str) -> ExtractedSchema:
        """Extract schema from OpenAPI spec URL."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            
            if url.endswith('.yaml') or url.endswith('.yml'):
                spec = yaml.safe_load(response.text)
            else:
                spec = response.json()
            
            return self._parse_openapi_spec(spec, url)
        except Exception as e:
            raise ValueError(f"Failed to fetch OpenAPI spec from {url}: {e}")
    
    def extract_from_file(self, file_path: Union[str, Path]) -> ExtractedSchema:
        """Extract schema from OpenAPI spec file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
            
            return self._parse_openapi_spec(spec, str(file_path))
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI spec from {file_path}: {e}")
    
    def _parse_openapi_spec(self, spec: Dict[str, Any], source: str) -> ExtractedSchema:
        """Parse OpenAPI specification and extract command schemas."""
        commands = []
        
        # Extract basic info
        info = spec.get('info', {})
        title = info.get('title', 'API')
        version = info.get('version', '1.0.0')

        base_url = ""
        servers = spec.get('servers')
        if isinstance(servers, list) and servers:
            first_server = servers[0]
            if isinstance(first_server, dict):
                base_url = str(first_server.get('url', '') or '')
        
        # Extract paths as commands
        paths = spec.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                command = self._extract_operation_command(
                    path, method, operation, f"{title} v{version}"
                )
                if command:
                    command.metadata["base_url"] = base_url
                    commands.append(command)
        
        return ExtractedSchema(
            source=source,
            source_type="openapi",
            commands=commands,
            metadata={
                "title": title,
                "version": version,
                "base_url": base_url,
                "total_paths": len(paths),
            }
        )
    
    def _extract_operation_command(self, path: str, method: str, operation: Dict[str, Any], api_name: str) -> Optional[CommandSchema]:
        """Extract a single command from OpenAPI operation."""
        operation_id = operation.get('operationId') or f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
        summary = operation.get('summary', '')
        description = operation.get('description', summary)
        
        # Extract parameters
        parameters = []
        
        # Path parameters
        for param in operation.get('parameters', []):
            if param.get('in') == 'path':
                param_schema = param.get('schema', {})
                command_param = CommandParameter(
                    name=param['name'],
                    type=param_schema.get('type', 'string'),
                    description=param.get('description', ''),
                    required=param.get('required', False),
                    example=param.get('example'),
                    location='path',
                )
                parameters.append(command_param)
        
        # Query parameters
        for param in operation.get('parameters', []):
            if param.get('in') == 'query':
                param_schema = param.get('schema', {})
                command_param = CommandParameter(
                    name=param['name'],
                    type=param_schema.get('type', 'string'),
                    description=param.get('description', ''),
                    required=param.get('required', False),
                    default=param_schema.get('default'),
                    choices=param_schema.get('enum', []),
                    example=param.get('example'),
                    location='query',
                )
                parameters.append(command_param)
        
        # Request body parameters
        request_body = operation.get('requestBody')
        if request_body:
            content = request_body.get('content', {})
            for media_type, media_obj in content.items():
                schema = media_obj.get('schema', {})
                if schema.get('type') == 'object':
                    properties = schema.get('properties', {})
                    required_fields = schema.get('required', [])
                    
                    for prop_name, prop_schema in properties.items():
                        command_param = CommandParameter(
                            name=prop_name,
                            type=prop_schema.get('type', 'string'),
                            description=prop_schema.get('description', ''),
                            required=prop_name in required_fields,
                            default=prop_schema.get('default'),
                            choices=prop_schema.get('enum', []),
                            example=prop_schema.get('example'),
                            location='body',
                        )
                        parameters.append(command_param)
        
        # Generate patterns from operation
        patterns = [
            f"{method.lower()} {path}",
            f"{operation_id}",
        ]
        
        if summary:
            patterns.append(summary.lower())
        
        # Generate examples
        examples = []
        for example_key, example_obj in operation.get('examples', {}).items():
            if isinstance(example_obj, dict) and 'value' in example_obj:
                examples.append(str(example_obj['value']))
        
        return CommandSchema(
            name=operation_id,
            description=description,
            category=api_name,
            parameters=parameters,
            examples=examples,
            patterns=patterns,
            source_type="openapi",
            metadata={
                "method": method,
                "path": path,
                "tags": operation.get('tags', []),
            }
        )


class ShellHelpExtractor:
    """Extract command schemas from shell help output."""
    
    def __init__(self):
        self.common_commands = {
            'find', 'grep', 'sed', 'awk', 'ls', 'cd', 'mkdir', 'rm', 'cp', 'mv',
            'ps', 'top', 'htop', 'kill', 'killall', 'systemctl', 'service',
            'docker', 'kubectl', 'git', 'curl', 'wget', 'ping', 'netstat',
            'tar', 'zip', 'unzip', 'chmod', 'chown', 'ssh', 'scp', 'rsync'
        }
    
    def extract_from_command(self, command: str) -> ExtractedSchema:
        """Extract schema from command help output."""
        try:
            # Try different help flags
            help_flags = ['--help', '-h', '-help', 'help']
            help_output = None
            
            for flag in help_flags:
                try:
                    result = subprocess.run(
                        [command, flag],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        help_output = result.stdout
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            if not help_output:
                # Try man page
                try:
                    result = subprocess.run(
                        ['man', command],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        help_output = result.stdout
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            if not help_output:
                raise ValueError(f"Could not get help for command: {command}")
            
            return self._parse_help_output(help_output, command)
        
        except Exception as e:
            raise ValueError(f"Failed to extract help for {command}: {e}")
    
    def extract_from_multiple_commands(self, commands: List[str]) -> List[ExtractedSchema]:
        """Extract schemas from multiple commands."""
        schemas = []
        for command in commands:
            try:
                schema = self.extract_from_command(command)
                schemas.append(schema)
            except ValueError:
                # Skip commands that don't have help available
                continue
        return schemas
    
    def _parse_help_output(self, help_text: str, command_name: str) -> ExtractedSchema:
        """Parse help output and extract command schema."""
        lines = help_text.split('\n')
        
        # Extract description (first non-empty lines)
        description = ""
        description_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                description_lines.append(line)
            elif description_lines:
                break
        
        description = ' '.join(description_lines[:3])  # First 3 lines as description
        
        # Extract usage patterns
        usage_patterns = []
        in_usage = False
        for line in lines:
            line = line.strip()
            if line.startswith('Usage:') or line.startswith('usage:'):
                in_usage = True
                usage_part = line.split(':', 1)[1].strip()
                usage_patterns.append(usage_part)
            elif in_usage and line:
                if line.startswith(' ') or line.startswith('\t'):
                    usage_patterns.append(line.strip())
                else:
                    in_usage = False
        
        # Extract options/parameters
        parameters = []
        current_param = None
        
        for line in lines:
            line = line.strip()
            
            # Match option patterns like -h, --help, -f FILE, --file=FILE
            option_match = re.match(r'^(-[a-zA-Z]|--[a-zA-Z0-9-]+)(?:\s+|=)(.+)?$', line)
            if option_match:
                option = option_match.group(1)
                rest = option_match.group(2) or ''
                
                # Extract parameter name and description
                param_name = option.lstrip('-').replace('-', '_')
                param_desc = rest
                
                # Check if it's a flag (boolean) or takes a value
                param_type = 'boolean'
                if '=' in rest or '<' in rest or '[' in rest:
                    param_type = 'string'
                    # Try to extract type from description
                    if 'file' in rest.lower():
                        param_type = 'file'
                    elif 'number' in rest.lower() or 'int' in rest.lower():
                        param_type = 'integer'
                
                parameters.append(CommandParameter(
                    name=param_name,
                    type=param_type,
                    description=param_desc,
                    required=False,  # Most options are optional
                    location="option",
                ))
        
        # Generate patterns from usage and description
        patterns = usage_patterns.copy()
        if description:
            patterns.append(description.lower())
        
        return ExtractedSchema(
            source=command_name,
            source_type="shell_help",
            commands=[CommandSchema(
                name=command_name,
                description=description,
                category="shell",
                parameters=parameters,
                examples=usage_patterns,
                patterns=patterns,
                source_type="shell_help",
                metadata={
                    "command": command_name,
                    "help_lines": len(lines),
                }
            )]
        )


class PythonCodeExtractor:
    """Extract command schemas from Python source code with decorators."""
    
    def extract_from_file(self, file_path: Union[str, Path]) -> ExtractedSchema:
        """Extract schemas from Python file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Python file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        return self.extract_from_source(source_code, str(file_path))
    
    def extract_from_source(self, source_code: str, source_name: str = "string") -> ExtractedSchema:
        """Extract schemas from Python source code string."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in {source_name}: {e}")
        
        commands: list[CommandSchema] = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for Click decorators
                click_command = self._extract_click_command(node)
                if click_command:
                    commands.append(click_command)
                    continue

                # Check for Typer CLI commands
                typer_command = self._extract_typer_command(node, tree)
                if typer_command:
                    commands.append(typer_command)
                    continue
                
                # Check for other command decorators
                generic_command = self._extract_generic_command(node)
                if generic_command:
                    commands.append(generic_command)
                    continue

                plain_command = self._extract_plain_function(node)
                if plain_command:
                    commands.append(plain_command)

        # Detect argparse-based scripts (single-command CLI)
        argparse_command = self._extract_argparse_cli(tree, source_name)
        if argparse_command:
            commands.append(argparse_command)
        
        return ExtractedSchema(
            source=source_name,
            source_type="python_code",
            commands=commands,
            metadata={
                "functions_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "classes_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            }
        )

    def _extract_typer_command(self, node: ast.AST, tree: ast.AST) -> Optional[CommandSchema]:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None

        typer_apps: set[str] = set()
        for n in getattr(tree, "body", []) or []:
            if not isinstance(n, ast.Assign):
                continue
            if not n.targets:
                continue
            t0 = n.targets[0]
            if not isinstance(t0, ast.Name):
                continue
            if not isinstance(n.value, ast.Call):
                continue
            fn = n.value.func
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                if fn.value.id == "typer" and fn.attr == "Typer":
                    typer_apps.add(t0.id)
            elif isinstance(fn, ast.Name) and fn.id == "Typer":
                typer_apps.add(t0.id)

        if not typer_apps:
            return None

        decorator_call: Optional[ast.Call] = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if isinstance(dec.func.value, ast.Name) and dec.func.value.id in typer_apps:
                    if dec.func.attr == "command":
                        decorator_call = dec
                        break

        if decorator_call is None:
            return None

        cmd_name = node.name
        for kw in decorator_call.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                cmd_name = kw.value.value

        description = ast.get_docstring(node) or ""
        parameters: list[CommandParameter] = []

        defaults = list(node.args.defaults or [])
        default_by_arg: dict[str, ast.AST] = {}
        if defaults:
            for a, d in zip(node.args.args[-len(defaults):], defaults):
                default_by_arg[a.arg] = d

        for a in node.args.args:
            if a.arg in {"self", "cls", "ctx"}:
                continue

            default_node = default_by_arg.get(a.arg)
            required = default_node is None
            param_type = _python_annotation_to_param_type(a.annotation)
            location = "option"
            default_val: Any = None

            if isinstance(default_node, ast.Call) and isinstance(default_node.func, ast.Attribute):
                if isinstance(default_node.func.value, ast.Name) and default_node.func.value.id == "typer":
                    if default_node.func.attr in {"Option", "Argument"}:
                        location = "argument" if default_node.func.attr == "Argument" else "option"
                        if default_node.args:
                            first = default_node.args[0]
                            if isinstance(first, ast.Constant) and first.value is Ellipsis:
                                required = True
                            else:
                                required = False
                                try:
                                    default_val = ast.literal_eval(first)
                                except Exception:
                                    default_val = _ast_unparse(first)
                        for kw in default_node.keywords:
                            if kw.arg == "default":
                                required = False
                                try:
                                    default_val = ast.literal_eval(kw.value)
                                except Exception:
                                    default_val = _ast_unparse(kw.value)

            parameters.append(
                CommandParameter(
                    name=a.arg,
                    type=param_type,
                    description="",
                    required=required,
                    default=default_val,
                    location=location,
                )
            )

        patterns = [cmd_name]
        if description:
            patterns.extend([word.lower() for word in description.split()[:3]])

        return CommandSchema(
            name=cmd_name,
            description=description,
            category="typer",
            parameters=_dedupe_params(parameters),
            examples=[f"{cmd_name} --help"],
            patterns=patterns,
            source_type="python_typer",
            metadata={"line_number": node.lineno},
        )

    def _extract_argparse_cli(self, tree: ast.AST, source_name: str) -> Optional[CommandSchema]:
        arg_calls: list[ast.Call] = []

        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument":
                arg_calls.append(n)

        if not arg_calls:
            return None

        params: list[CommandParameter] = []
        for call in arg_calls:
            opt_strings: list[str] = []
            for a in call.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    opt_strings.append(a.value)

            dest: Optional[str] = None
            required = False
            default_val: Any = None
            choices: list[str] = []
            param_type = "string"
            action = None
            nargs = None

            for kw in call.keywords:
                if kw.arg == "dest" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    dest = kw.value.value
                elif kw.arg == "required" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, bool):
                    required = kw.value.value
                elif kw.arg == "default":
                    try:
                        default_val = ast.literal_eval(kw.value)
                    except Exception:
                        default_val = _ast_unparse(kw.value)
                elif kw.arg == "choices":
                    if isinstance(kw.value, (ast.List, ast.Tuple)):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                choices.append(elt.value)
                elif kw.arg == "action" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    action = kw.value.value
                elif kw.arg == "nargs":
                    nargs = _ast_unparse(kw.value)
                elif kw.arg == "type":
                    txt = _ast_unparse(kw.value).lower()
                    if "int" in txt:
                        param_type = "integer"
                    elif "float" in txt:
                        param_type = "number"

            if action in {"store_true", "store_false"}:
                param_type = "boolean"

            is_positional = not any(s.startswith("-") for s in opt_strings)
            location = "argument" if is_positional else "option"

            name = dest
            if not name:
                long_opts = [s for s in opt_strings if s.startswith("--")]
                if long_opts:
                    name = _shell_opt_to_param_name(long_opts[0])
                elif opt_strings:
                    name = _shell_opt_to_param_name(opt_strings[0])
                else:
                    continue

            if default_val is not None and not required:
                required = False
            if location == "argument" and default_val is None and not required:
                if nargs in {"?", "*"}:
                    required = False
                else:
                    required = True

            params.append(
                CommandParameter(
                    name=name,
                    type=param_type,
                    description="",
                    required=required,
                    default=default_val,
                    choices=choices,
                    location=location,
                )
            )

        cmd_name = Path(str(source_name)).stem
        patterns = [cmd_name, "argparse"]
        return CommandSchema(
            name=cmd_name,
            description="",
            category="argparse",
            parameters=_dedupe_params(params),
            examples=[f"python {Path(str(source_name)).name} --help"],
            patterns=patterns,
            source_type="python_argparse",
            metadata={},
        )
    
    def _extract_plain_function(self, node: ast.AST) -> Optional[CommandSchema]:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None

        if node.name.startswith("_"):
            return None

        description = ast.get_docstring(node) or ""

        args = node.args
        parameters: list[CommandParameter] = []

        pos_args = list(args.args)
        defaults = list(args.defaults)
        default_by_arg: dict[str, Any] = {}
        if defaults:
            for a, d in zip(pos_args[-len(defaults):], defaults):
                try:
                    default_by_arg[a.arg] = ast.literal_eval(d)
                except Exception:
                    default_by_arg[a.arg] = _ast_unparse(d)

        for a in pos_args:
            if a.arg in {"self", "cls", "ctx"}:
                continue
            parameters.append(
                CommandParameter(
                    name=a.arg,
                    type=_python_annotation_to_param_type(a.annotation),
                    description="",
                    required=a.arg not in default_by_arg,
                    default=default_by_arg.get(a.arg),
                )
            )

        for a, d in zip(args.kwonlyargs, args.kw_defaults):
            if a.arg in {"self", "cls", "ctx"}:
                continue

            required = d is None
            default_val = None
            if d is not None:
                try:
                    default_val = ast.literal_eval(d)
                except Exception:
                    default_val = _ast_unparse(d)

            parameters.append(
                CommandParameter(
                    name=a.arg,
                    type=_python_annotation_to_param_type(a.annotation),
                    description="",
                    required=required,
                    default=default_val,
                )
            )

        if args.vararg:
            parameters.append(
                CommandParameter(
                    name=args.vararg.arg,
                    type="array",
                    description="",
                    required=False,
                )
            )

        if args.kwarg:
            parameters.append(
                CommandParameter(
                    name=args.kwarg.arg,
                    type="object",
                    description="",
                    required=False,
                )
            )

        patterns = [node.name]
        if description:
            patterns.extend([word.lower() for word in description.split()[:3]])

        return CommandSchema(
            name=node.name,
            description=description,
            category="python",
            parameters=_dedupe_params(parameters),
            examples=[],
            patterns=patterns,
            source_type="python_ast",
            metadata={
                "line_number": node.lineno,
            },
        )

    def _extract_click_command(self, node: ast.AST) -> Optional[CommandSchema]:
        """Extract Click command schema from function with Click decorators."""
        click_decorators = []

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'command':
                click_decorators.append('command')
            elif isinstance(decorator, ast.Attribute):
                if (isinstance(decorator.value, ast.Name) and 
                    decorator.value.id == 'click' and 
                    decorator.attr in ['command', 'option', 'argument']):
                    click_decorators.append(decorator.attr)
        
        if not click_decorators:
            return None
        
        # Extract docstring
        description = ""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            description = node.body[0].value.value.strip()
        
        # Extract parameters from function arguments and Click decorators
        parameters = []
        
        # Extract from function signature
        args = node.args
        for arg in args.args:
            if arg.arg in ('ctx',):  # Skip Click context
                continue
            
            param_type = 'string'
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    param_type = str(arg.annotation.value)
            
            parameters.append(CommandParameter(
                name=arg.arg,
                type=param_type,
                description=f"Parameter {arg.arg}",
                required=arg.arg not in (args.defaults or []),
            ))
        
        # Extract from Click option decorators
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call) and
                isinstance(decorator.func, ast.Attribute) and
                decorator.func.attr == 'option'):
                
                # Extract option name(s)
                option_names = []
                if isinstance(decorator.args[0], ast.Constant):
                    option_names = [decorator.args[0].value]
                elif isinstance(decorator.args[0], (ast.List, ast.Tuple)):
                    for elt in decorator.args[0].elts:
                        if isinstance(elt, ast.Constant):
                            option_names.append(elt.value)
                
                # Extract other properties
                param_name = option_names[0].lstrip('-').replace('-', '_') if option_names else "option"
                param_type = 'string'
                param_help = ""
                required = False
                
                for keyword in decorator.keywords:
                    if keyword.arg == 'type':
                        param_type = 'string'  # Could be enhanced to parse Click types
                    elif keyword.arg == 'help':
                        param_help = keyword.value.value if isinstance(keyword.value, ast.Constant) else ""
                    elif keyword.arg == 'required':
                        required = keyword.value.value if isinstance(keyword.value, ast.Constant) else False
                
                parameters.append(CommandParameter(
                    name=param_name,
                    type=param_type,
                    description=param_help,
                    required=required,
                ))
        
        # Generate patterns
        patterns = [node.name, f"run {node.name}"]
        if description:
            patterns.extend([word.lower() for word in description.split()[:3]])
        
        return CommandSchema(
            name=node.name,
            description=description,
            category="click",
            parameters=parameters,
            examples=[f"{node.name} --help"],
            patterns=patterns,
            source_type="python_click",
            metadata={
                "decorators": click_decorators,
                "line_number": node.lineno,
            }
        )
    
    def _extract_generic_command(self, node: ast.AST) -> Optional[CommandSchema]:
        """Extract generic command schema from function with command-like decorators."""
        command_decorators = []

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id.lower() in ['command', 'cmd', 'task']:
                    command_decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr.lower() in ['command', 'cmd', 'task']:
                    command_decorators.append(decorator.attr)
        
        if not command_decorators:
            return None
        
        # Extract docstring
        description = ""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            description = node.body[0].value.value.strip()

        # Extract parameters from function signature
        parameters = []
        args = node.args

        for arg in args.args:
            param_type = 'string'
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    param_type = str(arg.annotation.value)

            parameters.append(CommandParameter(
                name=arg.arg,
                type=param_type,
                description=f"Parameter {arg.arg}",
                required=arg.arg not in (args.defaults or []),
            ))

        # Generate patterns
        patterns = [node.name, f"execute {node.name}"]
        if description:
            patterns.extend([word.lower() for word in description.split()[:3]])

        return CommandSchema(
            name=node.name,
            description=description,
            category="python",
            parameters=parameters,
            examples=[f"python -c \"import {node.__module__}; {node.name}()\""],
            patterns=patterns,
            source_type="python_generic",
            metadata={
                "decorators": command_decorators,
                "line_number": node.lineno,
            }
        )


class ShellScriptExtractor:
    """Extract schema from a shell script file using shlex/regex heuristics."""

    _re_getopts = re.compile(r"\bgetopts\s+['\"]([^'\"]+)['\"]")
    _re_long_opt = re.compile(r"--[A-Za-z0-9][A-Za-z0-9_-]*")
    _re_long_opt_value = re.compile(
        r"(--[A-Za-z0-9][A-Za-z0-9_-]*)(?:=|\s+)(?P<value><[^>]+>|\[[^\]]+\]|[A-Za-z0-9_]+)"
    )
    _re_short_opt = re.compile(r"(?:^|\s)-(?P<flag>[A-Za-z0-9])\b")
    _re_usage = re.compile(r"\b(usage:|Usage:)\s*(.*)")

    def extract_from_file(self, file_path: Union[str, Path]) -> ExtractedSchema:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Shell script not found: {file_path}")

        source_code = file_path.read_text(encoding="utf-8", errors="replace")
        return self.extract_from_source(source_code, str(file_path))

    def extract_from_source(self, source_code: str, source_name: str) -> ExtractedSchema:
        lines = source_code.splitlines()
        shebang = lines[0].strip() if lines and lines[0].startswith("#!") else ""

        description_lines: list[str] = []
        for line in lines[:30]:
            s = line.strip()
            if s.startswith("#"):
                txt = s.lstrip("#").strip()
                if txt:
                    description_lines.append(txt)
            elif s:
                break

        description = " ".join(description_lines[:3])

        usage_lines: list[str] = []
        for line in lines:
            m = self._re_usage.search(line)
            if m:
                usage_lines.append(m.group(2).strip())

        params: list[CommandParameter] = []

        # getopts: "ab:c" => -a, -b <val>, -c
        for m in self._re_getopts.finditer(source_code):
            spec = m.group(1)
            i = 0
            while i < len(spec):
                ch = spec[i]
                if ch in {":", "?"}:
                    i += 1
                    continue
                takes_value = i + 1 < len(spec) and spec[i + 1] == ":"
                params.append(
                    CommandParameter(
                        name=ch,
                        type="string" if takes_value else "boolean",
                        description="",
                        required=False,
                        location="option",
                    )
                )
                i += 2 if takes_value else 1

        long_opts_with_value: set[str] = set()
        for m in self._re_long_opt_value.finditer(source_code):
            long_opts_with_value.add(m.group(1))

        for opt in sorted(set(self._re_long_opt.findall(source_code))):
            params.append(
                CommandParameter(
                    name=_shell_opt_to_param_name(opt),
                    type="string" if opt in long_opts_with_value else "boolean",
                    description="",
                    required=False,
                    location="option",
                )
            )

        for m in self._re_short_opt.finditer(source_code):
            params.append(
                CommandParameter(
                    name=m.group("flag"),
                    type="boolean",
                    description="",
                    required=False,
                    location="option",
                )
            )

        # Heuristic: parse usage tokens for positional args
        for u in usage_lines[:3]:
            try:
                toks = shlex.split(u)
            except Exception:
                toks = u.split()

            for t in toks:
                if t.startswith("--") or t.startswith("-"):
                    continue
                cleaned = t.strip("[]<>")
                if cleaned and cleaned.isidentifier():
                    params.append(
                        CommandParameter(
                            name=cleaned,
                            type="string",
                            description="",
                            required=False,
                            location="argument",
                        )
                    )

        script_name = Path(source_name).stem
        command = CommandSchema(
            name=script_name,
            description=description,
            category="shell_script",
            parameters=_dedupe_params(params),
            examples=[f"./{Path(source_name).name}"],
            patterns=[script_name] + ([description.lower()] if description else []),
            source_type="shell_script",
            metadata={"shebang": shebang, "usages": usage_lines},
        )

        return ExtractedSchema(
            source=source_name,
            source_type="shell_script",
            commands=[command],
            metadata={"shebang": shebang},
        )


class MakefileExtractor:
    """Extract schema from Makefile targets and variables."""

    _re_var = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op>[:+?]?=)\s*(?P<value>.*)$")
    _re_target = re.compile(r"^(?P<target>[A-Za-z0-9][A-Za-z0-9_.\-/]*)\s*:(?P<deps>.*)$")
    _re_var_ref = re.compile(r"\$\((?P<name>[A-Za-z_][A-Za-z0-9_]*)\)")

    def extract_from_file(self, file_path: Union[str, Path]) -> ExtractedSchema:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Makefile not found: {file_path}")

        parsed = self._try_parse_with_library(file_path)
        if parsed is not None:
            return parsed

        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self._parse_fallback(content, str(file_path))

    def _try_parse_with_library(self, file_path: Path) -> Optional[ExtractedSchema]:
        # Optional dependency.
        try:
            import makefile_parser  # type: ignore
        except Exception:
            return None

        parser_cls = getattr(makefile_parser, "MakefileParser", None)
        if parser_cls is None:
            return None

        try:
            parser = parser_cls()
            data = parser.parse(str(file_path))
        except Exception:
            return None

        if not isinstance(data, dict):
            return None

        targets = data.get("targets") if isinstance(data.get("targets"), dict) else {}
        variables = data.get("variables") if isinstance(data.get("variables"), dict) else {}

        commands: list[CommandSchema] = []
        for tname, tinfo in targets.items():
            deps: list[str] = []
            if isinstance(tinfo, dict):
                deps = list(tinfo.get("deps", tinfo.get("prereqs", [])) or [])

            commands.append(
                CommandSchema(
                    name=str(tname),
                    description="",
                    category="make",
                    parameters=[],
                    examples=[f"make {tname}"],
                    patterns=[str(tname), f"make {tname}"],
                    source_type="makefile",
                    metadata={"deps": deps},
                )
            )

        return ExtractedSchema(
            source=str(file_path),
            source_type="makefile",
            commands=commands,
            metadata={"variables": list(variables.keys())},
        )

    def _parse_fallback(self, content: str, source: str) -> ExtractedSchema:
        lines = content.splitlines()
        variables: dict[str, str] = {}
        targets: dict[str, dict[str, Any]] = {}
        target_comments: dict[str, str] = {}

        last_comment: Optional[str] = None
        current_target: Optional[str] = None
        current_recipe: list[str] = []

        def flush_recipe() -> None:
            nonlocal current_target, current_recipe
            if current_target is not None:
                targets[current_target]["recipe"] = list(current_recipe)
            current_recipe = []
            current_target = None

        for raw in lines:
            line = raw.rstrip("\n")
            if not line.strip():
                last_comment = None
                continue
            if line.lstrip().startswith("#"):
                txt = line.lstrip()[1:].strip()
                if txt:
                    last_comment = txt
                continue

            # Recipe lines begin with a tab
            if line.startswith("\t") and current_target is not None:
                current_recipe.append(line.strip())
                continue

            mv = self._re_var.match(line)
            if mv:
                variables[mv.group("name")] = mv.group("value").strip()
                continue

            mt = self._re_target.match(line)
            if mt:
                flush_recipe()
                tname = mt.group("target").strip()
                deps = [d for d in mt.group("deps").strip().split() if d]
                targets[tname] = {"deps": deps, "recipe": []}
                if last_comment:
                    target_comments[tname] = last_comment
                current_target = tname
                last_comment = None
                continue

            flush_recipe()

        flush_recipe()

        commands: list[CommandSchema] = []
        for tname, tinfo in targets.items():
            used_vars: set[str] = set()
            for r in tinfo.get("recipe", []):
                for m in self._re_var_ref.finditer(r):
                    used_vars.add(m.group("name"))

            params = [
                CommandParameter(name=v, type="string", description="", required=False)
                for v in sorted(used_vars)
            ]

            commands.append(
                CommandSchema(
                    name=tname,
                    description=target_comments.get(tname, ""),
                    category="make",
                    parameters=params,
                    examples=[f"make {tname}"],
                    patterns=[tname, f"make {tname}"],
                    source_type="makefile",
                    metadata={"deps": tinfo.get("deps", [])},
                )
            )

        return ExtractedSchema(
            source=source,
            source_type="makefile",
            commands=commands,
            metadata={"variables": variables, "targets": list(targets.keys())},
        )


class DynamicSchemaRegistry:
    """Registry for managing dynamically extracted schemas."""
    
    def __init__(self):
        self.schemas: Dict[str, ExtractedSchema] = {}
        self.openapi_extractor = OpenAPISchemaExtractor()
        self.shell_extractor = ShellHelpExtractor()
        self.python_extractor = PythonCodeExtractor()
        self.shell_script_extractor = ShellScriptExtractor()
        self.makefile_extractor = MakefileExtractor()
    
    def register_openapi_schema(self, source: Union[str, Path]) -> ExtractedSchema:
        """Register OpenAPI schema from URL or file."""
        if isinstance(source, str) and source.startswith(('http://', 'https://')):
            schema = self.openapi_extractor.extract_from_url(source)
        else:
            schema = self.openapi_extractor.extract_from_file(source)
        
        self.schemas[schema.source] = schema
        return schema
    
    def register_shell_help(self, command: str) -> ExtractedSchema:
        """Register shell command help schema."""
        schema = self.shell_extractor.extract_from_command(command)
        self.schemas[schema.source] = schema
        return schema
    
    def register_python_code(self, source: Union[str, Path]) -> ExtractedSchema:
        """Register Python code schema."""
        if isinstance(source, str) and '\n' in source:
            schema = self.python_extractor.extract_from_source(source)
        else:
            schema = self.python_extractor.extract_from_file(source)
        
        self.schemas[schema.source] = schema
        return schema

    def register_shell_script(self, source: Union[str, Path]) -> ExtractedSchema:
        """Register schema from a shell script file (.sh)."""
        schema = self.shell_script_extractor.extract_from_file(source)
        self.schemas[schema.source] = schema
        return schema

    def register_makefile(self, source: Union[str, Path]) -> ExtractedSchema:
        """Register schema from a Makefile."""
        schema = self.makefile_extractor.extract_from_file(source)
        self.schemas[schema.source] = schema
        return schema

    def register_dynamic_export(self, file_path: Union[str, Path]) -> list[ExtractedSchema]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dynamic schema export file not found: {file_path}")

        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse dynamic schema export from {file_path}: {e}")

        exported = payload
        if isinstance(payload, dict) and payload.get("format") == "nlp2cmd.dynamic_schema_export":
            exported = payload.get("sources", {})

        if not isinstance(exported, dict):
            raise ValueError(f"Dynamic schema export has invalid structure: {file_path}")

        imported: list[ExtractedSchema] = []
        for source, schema_obj in exported.items():
            if not isinstance(schema_obj, dict):
                continue

            commands: list[CommandSchema] = []
            for cmd_obj in schema_obj.get("commands", []) or []:
                if not isinstance(cmd_obj, dict):
                    continue

                params: list[CommandParameter] = []
                for p_obj in cmd_obj.get("parameters", []) or []:
                    if not isinstance(p_obj, dict):
                        continue
                    params.append(
                        CommandParameter(
                            name=str(p_obj.get("name", "")),
                            type=str(p_obj.get("type", "string")),
                            description=str(p_obj.get("description") or ""),
                            required=bool(p_obj.get("required", False)),
                            default=p_obj.get("default"),
                            choices=list(p_obj.get("choices", []) or []),
                            pattern=p_obj.get("pattern"),
                            example=p_obj.get("example"),
                            location=str(p_obj.get("location", "unknown")),
                        )
                    )

                commands.append(
                    CommandSchema(
                        name=str(cmd_obj.get("name", "")),
                        description=str(cmd_obj.get("description") or ""),
                        category=str(cmd_obj.get("category") or "general"),
                        parameters=params,
                        examples=list(cmd_obj.get("examples", []) or []),
                        patterns=list(cmd_obj.get("patterns", []) or []),
                        source_type=str(cmd_obj.get("source_type") or schema_obj.get("source_type") or "unknown"),
                        metadata=dict(cmd_obj.get("metadata", {}) or {}),
                    )
                )

            extracted_schema = ExtractedSchema(
                source=str(source),
                source_type=str(schema_obj.get("source_type") or "dynamic_export"),
                commands=commands,
                metadata=dict(schema_obj.get("metadata", {}) or {}),
            )
            self.schemas[extracted_schema.source] = extracted_schema
            imported.append(extracted_schema)

        return imported
    
    def get_all_commands(self) -> List[CommandSchema]:
        """Get all registered commands."""
        all_commands = []
        for schema in self.schemas.values():
            all_commands.extend(schema.commands)
        return all_commands
    
    def search_commands(self, query: str, limit: int = 10) -> List[CommandSchema]:
        """Search commands by name, description, or patterns."""
        query_lower = query.lower()
        matches = []
        
        for command in self.get_all_commands():
            score = 0
            
            # Name match
            if query_lower in command.name.lower():
                score += 10
            
            # Description match
            if query_lower in command.description.lower():
                score += 5
            
            # Pattern match
            for pattern in command.patterns:
                if query_lower in pattern.lower():
                    score += 3
                    break
            
            # Parameter name match
            for param in command.parameters:
                if query_lower in param.name.lower():
                    score += 2
            
            if score > 0:
                matches.append((command, score))
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return [cmd for cmd, _ in matches[:limit]]
    
    def get_command_by_name(self, name: str) -> Optional[CommandSchema]:
        """Get command by exact name."""
        for command in self.get_all_commands():
            if command.name == name:
                return command
        return None
    
    def get_commands_by_category(self, category: str) -> List[CommandSchema]:
        """Get all commands in a category."""
        return [cmd for cmd in self.get_all_commands() if cmd.category == category]
    
    def export_schemas(self, format: str = "json") -> str:
        """Export all schemas in specified format."""
        sources_payload = {
            source: {
                "source_type": schema.source_type,
                "commands": [
                    {
                        "name": cmd.name,
                        "description": cmd.description,
                        "category": cmd.category,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                                "default": p.default,
                                "choices": p.choices,
                                "location": p.location,
                            }
                            for p in cmd.parameters
                        ],
                        "examples": cmd.examples,
                        "patterns": cmd.patterns,
                        "source_type": cmd.source_type,
                        "metadata": cmd.metadata,
                    }
                    for cmd in schema.commands
                ],
                "metadata": schema.metadata,
            }
            for source, schema in self.schemas.items()
        }

        export_obj = {
            "format": "nlp2cmd.dynamic_schema_export",
            "sources": sources_payload,
        }

        fmt = format.lower()
        if fmt == "json":
            return json.dumps(export_obj, indent=2)
        if fmt in {"yaml", "yml"}:
            return yaml.safe_dump(export_obj, sort_keys=False)
        if fmt in {"jsonschema", "json_schema", "schema"}:
            return json.dumps(self._export_registry_json_schema(), indent=2)

        raise ValueError(f"Unsupported export format: {format}")

    def _export_registry_json_schema(self) -> dict[str, Any]:
        commands = self.get_all_commands()
        command_defs: dict[str, Any] = {}

        type_map = {
            "string": "string",
            "path": "string",
            "file": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
        }

        for cmd in commands:
            props: dict[str, Any] = {}
            required: list[str] = []
            for p in cmd.parameters:
                props[p.name] = {
                    "type": type_map.get(p.type, "string"),
                    "description": p.description or "",
                }
                if p.default is not None:
                    props[p.name]["default"] = p.default
                if p.choices:
                    props[p.name]["enum"] = list(p.choices)
                if p.required:
                    required.append(p.name)

            command_defs[cmd.name] = {
                "type": "object",
                "description": cmd.description or "",
                "properties": props,
                "required": required,
                "additionalProperties": False,
            }

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "NLP2CMD Dynamic Registry",
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": sorted(list(command_defs.keys()))},
                "entities": {"type": "object"},
                "commands": {"type": "object", "additionalProperties": False, "properties": command_defs},
            },
            "required": ["intent"],
            "additionalProperties": True,
        }
