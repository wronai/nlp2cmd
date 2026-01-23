"""
Schema Registry for file format validation and repair.

Supports Docker, Kubernetes, SQL, Terraform, and other configuration formats.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml


@dataclass
class FileFormatSchema:
    """Definition of a file format schema."""

    name: str
    extensions: list[str]
    mime_types: list[str]
    validator: Callable[[str], dict[str, Any]]
    parser: Callable[[str], dict[str, Any]]
    generator: Callable[[dict[str, Any]], str]
    repair_rules: list[dict[str, Any]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    description: str = ""
    
    def validate(self, content: str) -> dict[str, Any]:
        """Validate content using this schema."""
        return self.validator(content)
    
    def parse(self, content: str) -> dict[str, Any]:
        """Parse content using this schema."""
        return self.parser(content)
    
    def generate(self, data: dict[str, Any]) -> str:
        """Generate content from data using this schema."""
        return self.generator(data)
    
    def self_validate(self) -> dict[str, Any]:
        """Validate the schema itself."""
        errors = []
        warnings = []
        
        if not self.name:
            errors.append("Schema name cannot be empty")
        
        if not self.extensions:
            errors.append("Schema must have at least one extension")
        
        if not self.mime_types:
            errors.append("Schema must have at least one MIME type")
        
        if not self.validator:
            errors.append("Schema must have a validator function")
        
        if not self.parser:
            errors.append("Schema must have a parser function")
        
        if not self.generator:
            errors.append("Schema must have a generator function")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


class SchemaRegistry:
    """Registry for file format schemas with validation and repair capabilities."""

    def __init__(self):
        self.schemas: dict[str, FileFormatSchema] = {}
        self._register_builtin_schemas()

    def _register_builtin_schemas(self):
        """Register built-in schemas."""
        # Dockerfile schema
        self.schemas["dockerfile"] = FileFormatSchema(
            name="Dockerfile",
            extensions=["Dockerfile", "Dockerfile.*", "*.dockerfile"],
            mime_types=["text/x-dockerfile"],
            validator=self._validate_dockerfile,
            parser=self._parse_dockerfile,
            generator=self._generate_dockerfile,
            repair_rules=[
                {
                    "pattern": r"^RUN apt-get install(?! -y)",
                    "fix": r"RUN apt-get install -y",
                    "reason": "Add -y flag for non-interactive install",
                },
                {
                    "pattern": r"^FROM (\w+)$",
                    "fix": r"FROM \1:latest",
                    "reason": "Add explicit tag to base image",
                },
                {
                    "pattern": r"^RUN apt-get install",
                    "check": lambda m, c: "apt-get update" in c[:m.start()],
                    "reason": "Run apt-get update before install",
                },
            ],
        )

        # Docker Compose schema
        self.schemas["docker-compose"] = FileFormatSchema(
            name="Docker Compose",
            extensions=["docker-compose.yml", "docker-compose.yaml", "compose.yml"],
            mime_types=["application/x-yaml"],
            validator=self._validate_docker_compose,
            parser=lambda c: yaml.safe_load(c),
            generator=lambda d: yaml.dump(d, default_flow_style=False),
            repair_rules=[
                {
                    "path": "version",
                    "check": lambda v: v in ["3", "3.8", "3.9"],
                    "fix": "3.8",
                    "reason": "Update to compose version 3.8",
                },
                {
                    "path": "services.*.restart",
                    "check": lambda v: v is not None,
                    "fix": "unless-stopped",
                    "reason": "Add restart policy",
                },
            ],
        )

        # Kubernetes Deployment schema
        self.schemas["kubernetes-deployment"] = FileFormatSchema(
            name="Kubernetes Deployment",
            extensions=["*.yaml", "*.yml"],
            mime_types=["application/x-yaml"],
            validator=self._validate_k8s_deployment,
            parser=lambda c: yaml.safe_load(c),
            generator=lambda d: yaml.dump(d, default_flow_style=False),
            repair_rules=[
                {
                    "path": "apiVersion",
                    "check": lambda v: v == "apps/v1",
                    "fix": "apps/v1",
                    "reason": "Use apps/v1 API version",
                },
                {
                    "path": "spec.template.spec.containers.*.resources",
                    "check": lambda v: v is not None,
                    "fix": {"requests": {"memory": "128Mi", "cpu": "100m"}},
                    "reason": "Add resource requests",
                },
            ],
        )

        # GitHub Actions workflow schema
        self.schemas["github-workflow"] = FileFormatSchema(
            name="GitHub Actions Workflow",
            extensions=[".github/workflows/*.yml", ".github/workflows/*.yaml"],
            mime_types=["application/x-yaml"],
            validator=self._validate_github_workflow,
            parser=lambda c: yaml.safe_load(c),
            generator=lambda d: yaml.dump(d, default_flow_style=False),
            repair_rules=[
                {
                    "path": "jobs.*.runs-on",
                    "check": lambda v: v is not None,
                    "fix": "ubuntu-latest",
                    "reason": "Specify runs-on runner",
                },
            ],
        )

        # Environment file schema
        self.schemas["env-file"] = FileFormatSchema(
            name="Environment File",
            extensions=[".env", ".env.*", "*.env"],
            mime_types=["text/plain"],
            validator=self._validate_env_file,
            parser=self._parse_env_file,
            generator=self._generate_env_file,
            repair_rules=[
                {
                    "pattern": r"^([a-z][a-z0-9_]*)=",
                    "fix_fn": lambda m: f"{m.group(1).upper()}=",
                    "reason": "Environment variables should be UPPERCASE",
                },
            ],
        )

    def register(self, name: str, schema: FileFormatSchema) -> None:
        """Register a new schema."""
        self.schemas[name.lower()] = schema

    def get(self, name: str) -> Optional[FileFormatSchema]:
        """Get schema by name."""
        return self.schemas.get(name.lower())

    def has_schema(self, name: str) -> bool:
        """Check if schema exists."""
        return name.lower() in self.schemas

    def list_schemas(self) -> list[str]:
        """List all registered schema names."""
        return list(self.schemas.keys())

    def unregister(self, name: str) -> bool:
        """Unregister a schema by name."""
        name_lower = name.lower()
        if name_lower in self.schemas:
            # Prevent unregistering built-in schemas
            if name_lower in ['dockerfile', 'docker-compose', 'kubernetes-deployment', 'github-workflow', 'env-file']:
                raise ValueError(f"Cannot unregister built-in schema: {name}")
            del self.schemas[name_lower]
            return True
        return False

    def find_schema_for_file(self, filename: str) -> Optional[FileFormatSchema]:
        """Find schema for a given filename."""
        file_path = Path(filename)
        return self.detect_format(file_path)

    def find_schema_by_mime_type(self, mime_type: str) -> Optional[FileFormatSchema]:
        """Find schema by MIME type."""
        for schema in self.schemas.values():
            if mime_type in schema.mime_types:
                return schema
        return None

    def find_extension_conflicts(self) -> dict[str, list[str]]:
        """Find extension conflicts between schemas."""
        conflicts = {}
        extension_map = {}
        
        for name, schema in self.schemas.items():
            for ext in schema.extensions:
                if ext not in extension_map:
                    extension_map[ext] = []
                extension_map[ext].append(name)
        
        for ext, schemas in extension_map.items():
            if len(schemas) > 1:
                conflicts[ext] = schemas
        
        return conflicts

    def validate_integrity(self) -> bool:
        """Validate registry integrity."""
        # Check for extension conflicts
        conflicts = self.find_extension_conflicts()
        if conflicts:
            return False
        
        # Check that all schemas have required methods
        for name, schema in self.schemas.items():
            if not hasattr(schema, 'validator') or not hasattr(schema, 'parser') or not hasattr(schema, 'generator'):
                return False
        
        return True

    def load_from_file(self, file_path: str) -> bool:
        """Load schema from file."""
        try:
            path = Path(file_path)
            if path.suffix == '.json':
                import json
                with open(path) as f:
                    data = json.load(f)
            elif path.suffix in ['.yml', '.yaml']:
                with open(path) as f:
                    data = yaml.safe_load(f)
            else:
                return False
            
            # Create FileFormatSchema from data
            schema = FileFormatSchema(
                name=data['name'],
                extensions=data['extensions'],
                mime_types=data['mime_types'],
                validator=lambda c: {'valid': True, 'errors': [], 'warnings': []},
                parser=lambda c: {'parsed': c},
                generator=lambda d: d.get('content', ''),
                repair_rules=data.get('repair_rules', []),
                examples=data.get('examples', [])
            )
            
            self.register(data['name'], schema)
            return True
        except Exception:
            return False

    def load_from_directory(self, directory: str) -> int:
        """Load all schemas from directory."""
        path = Path(directory)
        loaded_count = 0
        
        for file_path in path.glob('*.json'):
            if self.load_from_file(str(file_path)):
                loaded_count += 1
        
        for file_path in path.glob('*.yaml'):
            if self.load_from_file(str(file_path)):
                loaded_count += 1
        
        for file_path in path.glob('*.yml'):
            if self.load_from_file(str(file_path)):
                loaded_count += 1
        
        return loaded_count

    def detect_format(self, file_path: Path) -> Optional[FileFormatSchema]:
        """Detect file format from path."""
        filename = file_path.name
        full_path = str(file_path)

        for schema in self.schemas.values():
            for pattern in schema.extensions:
                if self._match_pattern(filename, pattern):
                    return schema
                if self._match_pattern(full_path, pattern):
                    return schema

        # Try content-based detection
        return self._detect_by_content(file_path)

        # Try content-based detection
        return self._detect_by_content(file_path)

    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match filename against pattern."""
        import fnmatch

        return fnmatch.fnmatch(text, pattern) or text == pattern

    def _detect_by_content(self, file_path: Path) -> Optional[FileFormatSchema]:
        """Detect format by content analysis."""
        try:
            content = file_path.read_text()[:1000]

            if content.strip().startswith("FROM "):
                return self.schemas.get("dockerfile")
            if "apiVersion:" in content and "kind:" in content:
                if "Deployment" in content:
                    return self.schemas.get("kubernetes-deployment")
            if "version:" in content and "services:" in content:
                return self.schemas.get("docker-compose")
            if content.strip().startswith("on:") or "jobs:" in content:
                return self.schemas.get("github-workflow")

        except Exception:
            pass

        return None

    def validate(self, content: str, schema_name: str) -> dict[str, Any]:
        """Validate content against schema."""
        schema = self.get(schema_name)
        if not schema:
            return {"valid": False, "errors": [f"Unknown schema: {schema_name}"]}

        return schema.validator(content)

    def repair(
        self,
        content: str,
        schema_name: str,
        auto_fix: bool = False,
    ) -> dict[str, Any]:
        """Repair content according to schema rules."""
        schema = self.get(schema_name)
        if not schema:
            return {"repaired": False, "content": content, "changes": []}

        changes = []
        repaired_content = content

        for rule in schema.repair_rules:
            if "pattern" in rule:
                repaired_content, rule_changes = self._apply_pattern_rule(
                    repaired_content, rule, auto_fix
                )
                changes.extend(rule_changes)
            elif "path" in rule:
                repaired_content, rule_changes = self._apply_path_rule(
                    repaired_content, rule, schema, auto_fix
                )
                changes.extend(rule_changes)

        return {
            "repaired": any(c.get("type") == "fixed" for c in changes),
            "content": repaired_content,
            "changes": changes,
        }

    def _apply_pattern_rule(
        self,
        content: str,
        rule: dict[str, Any],
        auto_fix: bool,
    ) -> tuple[str, list[dict]]:
        """Apply regex-based repair rule."""
        changes = []
        pattern = rule["pattern"]
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for match in reversed(matches):
            check_fn = rule.get("check")
            if check_fn and check_fn(match, content):
                continue  # Check passed, no fix needed

            if auto_fix and ("fix" in rule or "fix_fn" in rule):
                if "fix_fn" in rule:
                    fix = rule["fix_fn"](match)
                else:
                    fix = re.sub(pattern, rule["fix"], match.group(0))

                content = content[: match.start()] + fix + content[match.end() :]
                changes.append({
                    "type": "fixed",
                    "original": match.group(0),
                    "fixed": fix,
                    "reason": rule.get("reason", ""),
                })
            else:
                changes.append({
                    "type": "warning",
                    "location": match.start(),
                    "text": match.group(0),
                    "reason": rule.get("reason", ""),
                })

        return content, changes

    def _apply_path_rule(
        self,
        content: str,
        rule: dict[str, Any],
        schema: FileFormatSchema,
        auto_fix: bool,
    ) -> tuple[str, list[dict]]:
        """Apply path-based repair rule for YAML/JSON."""
        changes = []
        try:
            data = schema.parser(content)
            path = rule["path"]
            issues = self._check_path(data, path.split("."), rule)

            if issues and auto_fix and "fix" in rule:
                data = self._apply_path_fix(data, path.split("."), rule["fix"])
                content = schema.generator(data)
                for issue in issues:
                    issue["type"] = "fixed"
                changes.extend(issues)
            else:
                changes.extend(issues)

        except Exception as e:
            changes.append({"type": "parse_error", "reason": str(e)})

        return content, changes

    def _check_path(
        self,
        data: Any,
        path_parts: list[str],
        rule: dict[str, Any],
        current_path: str = "",
    ) -> list[dict]:
        """Recursively check path in data structure."""
        issues = []

        if not path_parts:
            return issues

        part = path_parts[0]
        remaining = path_parts[1:]

        if part == "*":
            # Wildcard - iterate all
            if isinstance(data, dict):
                for key, value in data.items():
                    issues.extend(
                        self._check_path(value, remaining, rule, f"{current_path}.{key}")
                    )
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    issues.extend(
                        self._check_path(item, remaining, rule, f"{current_path}[{i}]")
                    )
        else:
            if isinstance(data, dict) and part in data:
                if not remaining:
                    # Final element - check
                    value = data[part]
                    check_fn = rule.get("check", lambda v: True)
                    if not check_fn(value):
                        issues.append({
                            "type": "warning",
                            "path": f"{current_path}.{part}",
                            "value": value,
                            "reason": rule.get("reason", ""),
                        })
                else:
                    issues.extend(
                        self._check_path(
                            data[part], remaining, rule, f"{current_path}.{part}"
                        )
                    )
            elif not remaining:
                # Missing key
                issues.append({
                    "type": "missing",
                    "path": f"{current_path}.{part}",
                    "reason": rule.get("reason", ""),
                })

        return issues

    def _apply_path_fix(
        self,
        data: Any,
        path_parts: list[str],
        fix_value: Any,
    ) -> Any:
        """Apply fix at specified path."""
        if not path_parts:
            return fix_value

        part = path_parts[0]
        remaining = path_parts[1:]

        if part == "*":
            if isinstance(data, dict):
                for key in data:
                    data[key] = self._apply_path_fix(data[key], remaining, fix_value)
            elif isinstance(data, list):
                for i in range(len(data)):
                    data[i] = self._apply_path_fix(data[i], remaining, fix_value)
        else:
            if isinstance(data, dict):
                if not remaining:
                    data[part] = fix_value
                else:
                    if part not in data:
                        data[part] = {}
                    data[part] = self._apply_path_fix(data[part], remaining, fix_value)

        return data

    # Validators
    def _validate_dockerfile(self, content: str) -> dict[str, Any]:
        """Validate Dockerfile."""
        errors = []
        warnings = []

        lines = content.strip().split("\n")
        has_from = False

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("FROM"):
                has_from = True
                if ":" not in line and "@" not in line:
                    warnings.append(f"Line {i}: Image has no tag")

            if line.startswith("RUN") and "apt-get install" in line:
                if "-y" not in line and "--yes" not in line:
                    warnings.append(f"Line {i}: apt-get install should use -y")

        if not has_from:
            errors.append("Dockerfile must start with FROM")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_docker_compose(self, content: str) -> dict[str, Any]:
        """Validate docker-compose.yml."""
        errors = []
        warnings = []

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return {"valid": False, "errors": [f"YAML error: {e}"], "warnings": []}

        if not isinstance(data, dict):
            return {"valid": False, "errors": ["Root must be a mapping"], "warnings": []}

        if "services" not in data:
            errors.append("Missing 'services' key")

        services = data.get("services", {})
        for name, config in services.items():
            if not config:
                errors.append(f"Service '{name}' is empty")
                continue

            if "image" not in config and "build" not in config:
                errors.append(f"Service '{name}' needs 'image' or 'build'")

            if "healthcheck" not in config:
                warnings.append(f"Service '{name}': consider adding healthcheck")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_k8s_deployment(self, content: str) -> dict[str, Any]:
        """Validate Kubernetes Deployment manifest."""
        errors = []
        warnings = []

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return {"valid": False, "errors": [f"YAML error: {e}"], "warnings": []}

        if data.get("kind") != "Deployment":
            return {"valid": True, "errors": [], "warnings": []}

        if data.get("apiVersion") != "apps/v1":
            warnings.append("Consider using apiVersion: apps/v1")

        spec = data.get("spec", {})
        if "selector" not in spec:
            errors.append("spec.selector is required")

        template = spec.get("template", {}).get("spec", {})
        containers = template.get("containers", [])

        for i, container in enumerate(containers):
            if "name" not in container:
                errors.append(f"containers[{i}].name is required")
            if "image" not in container:
                errors.append(f"containers[{i}].image is required")
            if "resources" not in container:
                warnings.append(f"containers[{i}]: consider adding resources")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_github_workflow(self, content: str) -> dict[str, Any]:
        """Validate GitHub Actions workflow."""
        errors = []
        warnings = []

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return {"valid": False, "errors": [f"YAML error: {e}"], "warnings": []}

        # YAML parses 'on' as True, so check for both
        has_on = "on" in data or True in data
        if not has_on:
            errors.append("Missing 'on' trigger")

        if "jobs" not in data:
            errors.append("Missing 'jobs'")
            return {"valid": False, "errors": errors, "warnings": warnings}

        for job_name, job_config in data.get("jobs", {}).items():
            if "runs-on" not in job_config:
                errors.append(f"Job '{job_name}' missing 'runs-on'")
            if "steps" not in job_config:
                errors.append(f"Job '{job_name}' missing 'steps'")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_env_file(self, content: str) -> dict[str, Any]:
        """Validate .env file."""
        errors = []
        warnings = []

        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                errors.append(f"Line {i}: Invalid format (missing =)")
                continue

            key, _, value = line.partition("=")

            if not key.isupper():
                warnings.append(f"Line {i}: '{key}' should be UPPERCASE")

            # Check unclosed quotes
            if value.startswith('"') and not value.endswith('"'):
                errors.append(f"Line {i}: Unclosed double quote")
            if value.startswith("'") and not value.endswith("'"):
                errors.append(f"Line {i}: Unclosed single quote")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # Parsers and generators
    def _parse_dockerfile(self, content: str) -> dict[str, Any]:
        """Parse Dockerfile into structure."""
        instructions = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if parts:
                instructions.append({
                    "instruction": parts[0],
                    "arguments": parts[1] if len(parts) > 1 else "",
                })
        return {"instructions": instructions}

    def _generate_dockerfile(self, data: dict[str, Any]) -> str:
        """Generate Dockerfile from structure."""
        lines = []
        for inst in data.get("instructions", []):
            lines.append(f"{inst['instruction']} {inst.get('arguments', '')}")
        return "\n".join(lines)

    def _parse_env_file(self, content: str) -> dict[str, str]:
        """Parse .env file."""
        result = {}
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                # Remove quotes
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                result[key.strip()] = value
        return result

    def _generate_env_file(self, data: dict[str, str]) -> str:
        """Generate .env file."""
        lines = []
        for key, value in data.items():
            if " " in value or "=" in value:
                value = f'"{value}"'
            lines.append(f"{key}={value}")
        return "\n".join(lines)


# Convenience exports
__all__ = ["FileFormatSchema", "SchemaRegistry"]
