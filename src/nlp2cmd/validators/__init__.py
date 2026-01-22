"""
Validators for NLP2CMD.

This module provides validation capabilities for generated commands
and configuration files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


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
            errors.append("Unclosed single quote")

        # Check double quotes
        double_quotes = content.count('"') - content.count('\\"')
        if double_quotes % 2 != 0:
            errors.append("Unclosed double quote")

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
        for pattern, message in self.DANGEROUS_PATTERNS:
            if pattern in content_upper:
                if self.strict:
                    errors.append(message)
                else:
                    warnings.append(message)

        # Check DELETE without WHERE
        if "DELETE FROM" in content_upper and "WHERE" not in content_upper:
            warnings.append("DELETE without WHERE will affect all rows")
            suggestions.append("Add WHERE clause to limit affected rows")

        # Check UPDATE without WHERE
        if "UPDATE" in content_upper and "SET" in content_upper:
            if "WHERE" not in content_upper:
                warnings.append("UPDATE without WHERE will affect all rows")
                suggestions.append("Add WHERE clause to limit affected rows")

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

        # Check for dangerous commands
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in content_lower:
                errors.append(f"Dangerous command detected: {dangerous}")

        # Check sudo usage
        if content.strip().startswith("sudo") and not self.allow_sudo:
            warnings.append("sudo usage detected - requires elevated privileges")
            suggestions.append("Consider if root privileges are necessary")

        # Check for rm with wildcards
        if "rm " in content and "*" in content:
            warnings.append("rm with wildcard - verify target carefully")

        # Check pipe to shell
        if "| sh" in content or "| bash" in content:
            warnings.append("Piping to shell is potentially dangerous")

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

    def validate(self, content: str) -> ValidationResult:
        """Validate Docker command or Dockerfile."""
        errors = []
        warnings = []
        suggestions = []

        # Check for privileged mode
        if "--privileged" in content:
            warnings.append("Privileged mode grants full host access")
            suggestions.append("Consider using specific capabilities instead")

        # Check for host network
        if "--network host" in content or "--net=host" in content:
            warnings.append("Host network mode bypasses network isolation")

        # Check for dangerous volume mounts
        dangerous_mounts = ["-v /:/", "-v /etc:", "-v /var/run/docker.sock"]
        for mount in dangerous_mounts:
            if mount in content:
                warnings.append(f"Potentially dangerous volume mount: {mount}")

        # Check for missing image tag
        if "docker run" in content or "docker pull" in content:
            # Simple heuristic: look for image without tag
            parts = content.split()
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

        # Check for operations in system namespaces
        for ns in self.BLOCKED_NAMESPACES:
            if f"-n {ns}" in content or f"--namespace={ns}" in content:
                warnings.append(f"Operating in system namespace: {ns}")
                suggestions.append("Avoid modifying system namespaces")

        # Check delete without confirmation
        if "kubectl delete" in content:
            if "--force" in content:
                warnings.append("Force delete bypasses graceful termination")
            if "-A" in content or "--all-namespaces" in content:
                errors.append("Delete across all namespaces is very dangerous")

        # Check missing namespace
        if "kubectl" in content:
            if "-n" not in content and "--namespace" not in content:
                if "-A" not in content and "--all-namespaces" not in content:
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
