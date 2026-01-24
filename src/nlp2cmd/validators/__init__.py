"""
Validators for NLP2CMD.

This module provides validation capabilities for generated commands
and configuration files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import re


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            suggestions=self.suggestions + other.suggestions,
            metadata={**self.metadata, **other.metadata},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationResult":
        """Create validation result from dictionary."""
        return cls(
            is_valid=data.get("is_valid", True),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            suggestions=data.get("suggestions", []),
            metadata=data.get("metadata", {}),
        )

    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Check if validation result has errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if validation result has warnings."""
        return len(self.warnings) > 0

    def copy(self) -> "ValidationResult":
        """Create a copy of the validation result."""
        return ValidationResult(
            is_valid=self.is_valid,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            suggestions=self.suggestions.copy(),
            metadata=self.metadata.copy(),
        )

    def __str__(self) -> str:
        """String representation of validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        details = []
        if self.errors:
            details.append(f" - {', '.join(self.errors[:2])}")
            if len(self.errors) > 2:
                details[-1] += f" (and {len(self.errors) - 2} more)"
        if self.warnings:
            details.append(f" - {', '.join(self.warnings[:2])}")
            if len(self.warnings) > 2:
                details[-1] += f" (and {len(self.warnings) - 2} more)"
        return f"{status} ValidationResult(errors={len(self.errors)}, warnings={len(self.warnings)}){''.join(details)}"


class BaseValidator(ABC):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, content: str) -> ValidationResult:
        """
        Validate content.

        Args:
            content: Content to validate

        Returns:
            ValidationResult with validation outcome
        """
        raise NotImplementedError

    def validate_with_context(
        self,
        content: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate content with additional context.

        Args:
            content: Content to validate
            context: Additional context for validation

        Returns:
            ValidationResult with validation outcome
        """
        return self.validate(content)


class SyntaxValidator(BaseValidator):
    """Generic syntax validator for balanced brackets, quotes, etc."""

    def validate(self, content: str) -> ValidationResult:
        """Validate basic syntax."""
        errors = []
        warnings = []

        # Check balanced parentheses
        if content.count("(") != content.count(")"):
            errors.append("Unbalanced parentheses")

        # Check balanced brackets
        if content.count("[") != content.count("]"):
            errors.append("Unbalanced square brackets")

        # Check balanced braces
        if content.count("{") != content.count("}"):
            errors.append("Unbalanced curly braces")

        # Check single quotes
        single_quotes = content.count("'") - content.count("\\'")
        if single_quotes % 2 != 0:
            errors.append("Unclosed single quote string")

        # Check double quotes
        double_quotes = content.count('"') - content.count('\\"')
        if double_quotes % 2 != 0:
            errors.append("Unclosed double quote string")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class SQLValidator(BaseValidator):
    """SQL-specific validator."""

    DANGEROUS_PATTERNS = [
        ("DROP DATABASE", "DROP DATABASE is extremely dangerous"),
        ("TRUNCATE TABLE", "TRUNCATE removes all data permanently"),
        ("; DROP", "Possible SQL injection pattern detected"),
        ("--", "SQL comment detected - review for injection"),
    ]

    def __init__(self, strict: bool = False):
        self.strict = strict

    def validate(self, content: str) -> ValidationResult:
        """Validate SQL statement."""
        errors = []
        warnings = []
        suggestions = []

        content_upper = content.upper()

        # Check for dangerous patterns
        injection_detected = False
        for pattern, message in self.DANGEROUS_PATTERNS:
            if pattern in content_upper:
                if self.strict or pattern in ["; DROP", "DROP DATABASE"]:
                    errors.append(message)
                    injection_detected = True
                else:
                    warnings.append(message)

        # If injection detected and not strict, still mark as invalid
        if injection_detected and not self.strict:
            # Still mark as invalid for security, but allow warnings
            pass

        # Check DELETE without WHERE
        if "DELETE FROM" in content_upper and "WHERE" not in content_upper:
            warnings.append("DELETE without WHERE will affect all rows")
            suggestions.append("Add WHERE clause to limit affected rows")

        # Check UPDATE without WHERE
        if "UPDATE" in content_upper and "SET" in content_upper:
            if "WHERE" not in content_upper:
                warnings.append("UPDATE without WHERE will affect all rows")
                suggestions.append("Add WHERE clause to limit affected rows")

        # Check DROP TABLE warning
        if "DROP TABLE" in content_upper:
            warnings.append("DROP TABLE operation detected - ensure you have a backup")

        # Check reserved keywords in identifiers (basic check)
        reserved_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'ORDER', 'GROUP', 'HAVING']
        # Simple check for keywords used as column/table names without backticks
        words = re.findall(r'\b\w+\b', content)
        for word in words:
            if word.upper() in reserved_keywords and word.upper() not in ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
                # Check if it's likely used as an identifier (not a keyword)
                context = content_upper
                if f' {word.upper()} ' in context or f'{word.upper()} ' in context or f' {word.upper()}' in context:
                    if not any(f'{word.upper()}(' in context for word in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']):
                        warnings.append(f"Reserved keyword '{word}' used as identifier - consider using backticks")
                        break

        # Check aggregate without GROUP BY
        aggregate_functions = ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(']
        has_aggregate = any(func in content_upper for func in aggregate_functions)
        has_group_by = 'GROUP BY' in content_upper
        
        if has_aggregate and not has_group_by and 'WHERE' in content_upper:
            warnings.append("Aggregate function without GROUP BY may return unexpected results")

        # Check LIMIT clause
        if 'LIMIT' in content_upper:
            limit_match = re.search(r'LIMIT\s+(-?\d+)', content_upper)
            if limit_match and int(limit_match.group(1)) < 0:
                errors.append("LIMIT value cannot be negative")

        # Check JOIN syntax
        join_types = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN']
        for join_type in join_types:
            if join_type in content_upper:
                # Basic check for JOIN condition
                if ' ON ' not in content_upper and ' USING ' not in content_upper:
                    errors.append(f"JOIN without ON or USING clause")
                break

        # Basic syntax check
        syntax_result = SyntaxValidator().validate(content)
        errors.extend(syntax_result.errors)
        warnings.extend(syntax_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


class ShellValidator(BaseValidator):
    """Shell command validator."""

    DANGEROUS_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        ":(){:|:&};:",
        "dd if=/dev/zero",
        "chmod -R 777 /",
        "> /dev/sda",
    ]

    def __init__(self, allow_sudo: bool = False):
        self.allow_sudo = allow_sudo

    def validate(self, content: str) -> ValidationResult:
        """Validate shell command."""
        errors = []
        warnings = []
        suggestions = []

        content_lower = content.lower()

        # Check for dangerous commands - mark as errors
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in content_lower:
                errors.append(f"Dangerous command detected: {dangerous}")

        # Check sudo usage
        if content.strip().startswith("sudo") and not self.allow_sudo:
            warnings.append("sudo usage detected - requires elevated privileges")
            suggestions.append("Consider if root privileges are necessary")

        # Check for rm with wildcards - mark as error for safety
        if "rm " in content and "*" in content:
            errors.append("rm with wildcard - verify target carefully")

        # Check pipe to shell - warning only
        if "| sh" in content or "| bash" in content:
            warnings.append("Piping to shell is potentially dangerous")

        # Check for eval command - error for security
        if "eval " in content_lower:
            errors.append("eval command detected - potential code injection risk")

        # Check for command injection patterns
        injection_patterns = ["&&", "||", ";", "$(", "`"]
        for pattern in injection_patterns:
            if pattern in content and not pattern in ["&&", "||"]:  # Allow logical operators in safe contexts
                if pattern == ";":
                    errors.append("Command separator detected - potential injection risk")
                elif pattern == "$(":
                    warnings.append("Command substitution detected - review for safety")
                elif pattern == "`":
                    warnings.append("Backtick command substitution detected - review for safety")

        # Check for dangerous permission changes
        if "chmod" in content_lower and ("777" in content or "a+rwx" in content):
            warnings.append("Dangerous permission change detected")
            suggestions.append("Consider more restrictive permissions")

        # Check for process killing
        if "kill" in content_lower and ("-9" in content or "SIGKILL" in content_upper):
            warnings.append("Force kill signal detected - consider graceful termination")
            suggestions.append("Try SIGTERM (kill -15) first")

        # Check for system file modification
        system_paths = ["/etc/", "/boot/", "/sys/", "/proc/", "/dev/", "/root/", "/usr/bin/"]
        for path in system_paths:
            if path in content and (">>" in content or ">" in content):
                errors.append(f"System file modification detected: {path}")

        # Check for background job patterns
        if "nohup" in content_lower or (content.endswith("&") and not content.endswith(" &")):
            errors.append("Background job detected - verify job management")

        # Check for path traversal
        if "../" in content or "..\\" in content:
            errors.append("Path traversal pattern detected")

        # Syntax check
        syntax_result = SyntaxValidator().validate(content)
        errors.extend(syntax_result.errors)
        warnings.extend(syntax_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


class DockerValidator(BaseValidator):
    """Docker command and Dockerfile validator."""

    _IMAGE_RE = re.compile(
        r"^(?:(?:[a-z0-9]+(?:[._-][a-z0-9]+)*)/)*[a-z0-9]+(?:[._-][a-z0-9]+)*(?::[A-Za-z0-9][A-Za-z0-9._-]{0,127})?$"
    )

    @staticmethod
    def _iter_publish_ports(tokens: list[str]) -> list[int]:
        ports: list[int] = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in {"-p", "--publish"}:
                if i + 1 < len(tokens):
                    spec = tokens[i + 1]
                    ports.extend(DockerValidator._parse_ports_from_spec(spec))
                    i += 2
                    continue
            if t.startswith("--publish="):
                spec = t.split("=", 1)[1]
                ports.extend(DockerValidator._parse_ports_from_spec(spec))
            i += 1
        return ports

    @staticmethod
    def _parse_ports_from_spec(spec: str) -> list[int]:
        # handle forms:
        # - 8080:80
        # - 127.0.0.1:8080:80
        # - 8080:80/tcp
        if not isinstance(spec, str) or not spec:
            return []
        cleaned = spec.split("/", 1)[0]
        parts = cleaned.split(":")
        numeric: list[int] = []
        for p in parts:
            if p.isdigit():
                try:
                    numeric.append(int(p))
                except Exception:
                    continue
        return numeric

    @classmethod
    def _is_valid_image_name(cls, image: str) -> bool:
        if not isinstance(image, str) or not image:
            return False
        if "@" in image:
            return False
        return cls._IMAGE_RE.match(image) is not None

    @staticmethod
    def _find_docker_image(tokens: list[str], *, subcommand: str) -> Optional[str]:
        if not tokens:
            return None
        tokens_lower = [t.lower() for t in tokens]
        if subcommand not in tokens_lower:
            return None
        idx = tokens_lower.index(subcommand)

        if subcommand == "pull":
            for t in tokens[idx + 1 :]:
                if t.startswith("-"):
                    continue
                return t
            return None

        if subcommand != "run":
            return None

        opts_with_arg = {
            "-p",
            "--publish",
            "-e",
            "--env",
            "-v",
            "--volume",
            "--entrypoint",
            "--user",
            "-u",
            "--network",
            "--name",
            "--label",
            "--memory",
            "--cpus",
            "--security-opt",
        }
        inline_prefixes = ("-p", "-e", "-v", "-u")
        inline_equals_prefixes = (
            "--publish=",
            "--env=",
            "--volume=",
            "--entrypoint=",
            "--user=",
            "--network=",
            "--name=",
            "--label=",
            "--memory=",
            "--cpus=",
            "--security-opt=",
        )

        i = idx + 1
        while i < len(tokens):
            t = tokens[i]
            tl = tokens_lower[i]

            if tl == "--":
                i += 1
                continue

            if tl.startswith("-"):
                if tl.startswith(inline_equals_prefixes):
                    i += 1
                    continue
                if any(tl.startswith(p) and tl != p for p in inline_prefixes):
                    i += 1
                    continue
                if tl in opts_with_arg:
                    i += 2
                    continue
                i += 1
                continue

            return t
        return None

    def validate(self, content: str) -> ValidationResult:
        """Validate Docker command or Dockerfile."""
        errors = []
        warnings = []
        suggestions = []

        content_stripped = (content or "").strip()
        content_lower = content_stripped.lower()

        is_docker_cmd = (
            content_lower.startswith("docker ")
            or content_lower.startswith("docker-compose")
            or content_lower.startswith("docker compose")
        )
        is_dockerfile = (
            "\n" in content_stripped
            and ("from " in content_lower or "cmd " in content_lower or "entrypoint " in content_lower)
            and any(line.strip().lower().startswith("from ") for line in content_stripped.splitlines() if line.strip())
        )
        if not is_docker_cmd and not is_dockerfile:
            return ValidationResult(
                is_valid=False,
                errors=["Not a docker command"],
                warnings=[],
                suggestions=["Prefix the command with 'docker' or provide a Dockerfile"],
            )

        tokens = content_stripped.split()
        tokens_lower = [t.lower() for t in tokens]

        # Root user warning
        is_root_user = False
        for i, t in enumerate(tokens_lower):
            if t in {"--user", "-u"} and i + 1 < len(tokens_lower):
                if tokens_lower[i + 1] == "root":
                    is_root_user = True
                    break
            if t.startswith("--user=") and t.split("=", 1)[1] == "root":
                is_root_user = True
                break
        if is_root_user:
            warnings.append("Running container as root user")

        # docker rm force warning
        if content_lower.startswith("docker rm") and (" -f" in content_lower or " --force" in content_lower or "-f" in tokens_lower):
            warnings.append("Force removal detected (-f/--force)")

        # docker kill warning
        if content_lower.startswith("docker kill"):
            warnings.append("docker kill sends SIGKILL immediately")

        # docker build context warning
        if content_lower.startswith("docker build"):
            # find last token that isn't a flag
            context = None
            for t in reversed(tokens[2:]):
                if not t.startswith("-"):
                    context = t
                    break
            if context == "/":
                warnings.append("Build context is root directory")
                suggestions.append("Use a narrower build context than '/'")

        # Validate published ports
        for port in self._iter_publish_ports(tokens):
            if port < 1 or port > 65535:
                errors.append(f"Invalid port: {port}")

        # Validate image name for docker run / pull
        if content_lower.startswith("docker run"):
            image = self._find_docker_image(tokens, subcommand="run")
            if image and not self._is_valid_image_name(image):
                errors.append(f"Invalid image name: {image}")
        elif content_lower.startswith("docker pull"):
            image = self._find_docker_image(tokens, subcommand="pull")
            if image and not self._is_valid_image_name(image):
                errors.append(f"Invalid image name: {image}")

        # Check for privileged mode
        if "--privileged" in content:
            warnings.append("Privileged mode grants full host access")
            suggestions.append("Consider using specific capabilities instead")

        # Check for host network
        if "--network host" in content or "--net=host" in content:
            warnings.append("Host network bypasses network isolation")

        # Check for dangerous volume mounts
        dangerous_mounts = ["-v /:/", "-v /etc:", "-v /var/run/docker.sock"]
        for mount in dangerous_mounts:
            if mount in content:
                if "docker.sock" in mount:
                    warnings.append("Docker socket mount detected")
                else:
                    warnings.append(f"Dangerous volume mount: {mount}")

        # docker socket mount warning (more general check)
        if "docker.sock" in content_lower:
            warnings.append("Docker socket mount detected")

        # Check for image tag
        parts = content_lower.split()
        for i, part in enumerate(parts):
            if part in ["run", "pull"] and i + 1 < len(parts):
                image = parts[i + 1]
                if not image.startswith("-") and ":" not in image:
                    warnings.append(f"Image '{image}' has no tag, using :latest")
                    suggestions.append("Specify explicit image tag for reproducibility")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


class KubernetesValidator(BaseValidator):
    """Kubernetes command and manifest validator."""

    BLOCKED_NAMESPACES = ["kube-system", "kube-public", "kube-node-lease"]

    def __init__(self, allowed_namespaces: Optional[list[str]] = None):
        self.allowed_namespaces = allowed_namespaces

    def validate(self, content: str) -> ValidationResult:
        """Validate kubectl command."""
        errors = []
        warnings = []
        suggestions = []

        content_stripped = (content or "").strip()
        content_lower = content_stripped.lower()

        is_kubectl_cmd = content_lower.startswith("kubectl ")
        is_manifest = (
            "\n" in content_stripped
            and re.search(r"^\s*apiVersion\s*:", content_stripped, flags=re.IGNORECASE | re.MULTILINE) is not None
            and re.search(r"^\s*kind\s*:", content_stripped, flags=re.IGNORECASE | re.MULTILINE) is not None
        )
        if not is_kubectl_cmd and not is_manifest:
            return ValidationResult(
                is_valid=False,
                errors=["Not a kubectl command"],
                warnings=[],
                suggestions=["Prefix the command with 'kubectl' or provide a Kubernetes YAML manifest"],
            )

        tokens = content_stripped.split()
        tokens_lower = [t.lower() for t in tokens]

        is_delete = len(tokens_lower) >= 2 and tokens_lower[1] == "delete"
        is_get = len(tokens_lower) >= 2 and tokens_lower[1] == "get"
        is_logs = len(tokens_lower) >= 2 and tokens_lower[1] == "logs"
        is_scale = len(tokens_lower) >= 2 and tokens_lower[1] == "scale"
        is_port_forward = len(tokens_lower) >= 2 and tokens_lower[1] in {"port-forward", "portforward"}

        # Extract namespace if present
        namespace: Optional[str] = None
        for i, t in enumerate(tokens_lower):
            if t in {"-n", "--namespace"} and i + 1 < len(tokens_lower):
                namespace = tokens_lower[i + 1]
                break
            if t.startswith("--namespace="):
                namespace = t.split("=", 1)[1]
                break

        # Block delete in system namespaces
        if is_delete and namespace in self.BLOCKED_NAMESPACES:
            errors.append(f"Delete in system namespace is blocked: {namespace}")

        # Warn about delete without explicit namespace (defaults to 'default')
        if is_delete and not namespace and "--all-namespaces" not in tokens_lower and "-a" not in tokens_lower:
            warnings.append("Deleting in default namespace; consider specifying -n")

        # Force delete warning
        if is_delete and ("--force" in tokens_lower or "--grace-period=0" in tokens_lower):
            warnings.append("Force delete / grace period override detected")

        # Cluster-admin operations warning
        if "clusterrolebinding" in tokens_lower or "clusterrole" in tokens_lower:
            warnings.append("Cluster-admin level operation detected")

        # Validate kubectl get resource type
        if is_get and len(tokens_lower) >= 3:
            resource = tokens_lower[2]
            allowed_resources = {
                "pods", "pod", "deployments", "deployment", "services", "service", "svc",
                "namespaces", "namespace", "ns", "nodes", "node", "ingress", "ingresses",
                "configmap", "configmaps", "secret", "secrets", "crd", "crds", "crds.v1",
                "pv", "pvs", "pvc", "pvcs", "events", "event", "jobs", "job",
                "replicasets", "replicaset", "statefulsets", "statefulset", "daemonsets", "daemonset",
            }
            if resource not in allowed_resources and "/" not in resource:
                errors.append(f"Invalid resource type: {resource}")

        # apply -f file existence warning
        if len(tokens_lower) >= 2 and tokens_lower[1] == "apply":
            if "-f" in tokens_lower:
                idx = tokens_lower.index("-f")
                if idx + 1 < len(tokens):
                    path = tokens[idx + 1]
                    try:
                        from pathlib import Path

                        if path.endswith((".yml", ".yaml")) and not Path(path).expanduser().exists():
                            warnings.append(f"File not found: {path}")
                    except Exception:
                        pass

        if is_port_forward:
            warnings.append("Port forward operation detected")

        if is_logs and ("--all-namespaces" in tokens_lower or "-a" in tokens_lower):
            warnings.append("Logs across all namespaces requested")

        if "--watch" in tokens_lower:
            warnings.append("Watch operation requested")

        # Validate replicas for scale
        if is_scale:
            replicas_val: Optional[str] = None
            for t in tokens_lower:
                if t.startswith("--replicas="):
                    replicas_val = t.split("=", 1)[1]
                    break
            if replicas_val is not None:
                try:
                    replicas_int = int(replicas_val)
                    if replicas_int < 0:
                        errors.append("Replica count cannot be negative")
                except Exception:
                    errors.append("Invalid replica count")

        # Delete across all namespaces is dangerous
        if is_delete and ("-a" in tokens_lower or "--all-namespaces" in tokens_lower or "-A" in tokens):
            errors.append("Delete across all namespaces is very dangerous")

        # General suggestion: specify namespace if missing
        if is_kubectl_cmd and not namespace and "--all-namespaces" not in tokens_lower and "-a" not in tokens_lower and "-A" not in tokens:
            suggestions.append("Consider specifying namespace with -n")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


class CompositeValidator(BaseValidator):
    """Combines multiple validators."""

    def __init__(self, validators: list[BaseValidator]):
        self.validators = validators

    def validate(self, content: str) -> ValidationResult:
        """Run all validators and merge results."""
        result = ValidationResult(is_valid=True)

        for validator in self.validators:
            validator_result = validator.validate(content)
            result = result.merge(validator_result)

        return result


__all__ = [
    "BaseValidator",
    "ValidationResult",
    "SyntaxValidator",
    "SQLValidator",
    "ShellValidator",
    "DockerValidator",
    "KubernetesValidator",
    "CompositeValidator",
]
