"""
Iteration 7: Validation & Self-Correction.

Validate generated DSL and retry with error context for self-correction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from nlp2cmd.generation.llm_simple import LLMGenerationResult
from nlp2cmd.generation.llm_multi import MultiDomainGenerator, MultiDomainResult


class DSLValidator(Protocol):
    """Protocol for DSL validators."""
    
    def validate(self, command: str) -> "ValidationResult":
        """Validate a DSL command."""
        ...


@dataclass
class ValidationResult:
    """Result of DSL validation."""
    
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ValidatingGeneratorResult:
    """Result of validated generation."""
    
    command: str
    domain: str
    is_valid: bool
    attempts: int
    errors_history: list[str] = field(default_factory=list)
    final_validation: Optional[ValidationResult] = None
    generation_result: Optional[MultiDomainResult] = None


class ValidatingGenerator:
    """
    Generate DSL with validation and self-correction.
    
    Validates generated output and retries with error context
    if validation fails, allowing LLM to self-correct.
    
    Example:
        generator = ValidatingGenerator(
            generator=MultiDomainGenerator(llm),
            validators={'sql': SQLValidator()},
            max_retries=3
        )
        result = await generator.generate("Pokaż użytkowników")
        # result.is_valid == True (after potential self-correction)
    """
    
    def __init__(
        self,
        generator: MultiDomainGenerator,
        validators: Optional[dict[str, DSLValidator]] = None,
        max_retries: int = 3,
    ):
        self.generator = generator
        self.validators = validators or {}
        self.max_retries = max_retries
    
    async def generate(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ValidatingGeneratorResult:
        """
        Generate DSL with validation and retry.
        
        Args:
            text: Natural language input
            context: Additional context
            
        Returns:
            ValidatingGeneratorResult with validated command
        """
        errors_history: list[str] = []
        last_result: Optional[MultiDomainResult] = None
        last_validation: Optional[ValidationResult] = None
        
        for attempt in range(self.max_retries):
            # Generate (with error context for retries)
            gen_context = context.copy() if context else {}
            if errors_history:
                gen_context["previous_errors"] = errors_history
            
            result = await self.generator.generate(text, gen_context)
            last_result = result
            
            if not result.success:
                errors_history.append(f"Generation failed: {result.error}")
                continue
            
            # Get validator for domain
            validator = self.validators.get(result.domain)
            
            if validator is None:
                # No validator - assume valid
                return ValidatingGeneratorResult(
                    command=result.command,
                    domain=result.domain,
                    is_valid=True,
                    attempts=attempt + 1,
                    errors_history=errors_history,
                    generation_result=result,
                )
            
            # Validate
            validation = validator.validate(result.command)
            last_validation = validation
            
            if validation.is_valid:
                return ValidatingGeneratorResult(
                    command=result.command,
                    domain=result.domain,
                    is_valid=True,
                    attempts=attempt + 1,
                    errors_history=errors_history,
                    final_validation=validation,
                    generation_result=result,
                )
            
            # Collect errors for retry
            errors_history.extend(validation.errors)
        
        # Return last attempt even if invalid
        return ValidatingGeneratorResult(
            command=last_result.command if last_result else "",
            domain=last_result.domain if last_result else "unknown",
            is_valid=False,
            attempts=self.max_retries,
            errors_history=errors_history,
            final_validation=last_validation,
            generation_result=last_result,
        )
    
    def add_validator(self, domain: str, validator: DSLValidator) -> None:
        """Add validator for a domain."""
        self.validators[domain] = validator


# Built-in validators
class SimpleSQLValidator:
    """Simple SQL syntax validator."""
    
    REQUIRED_KEYWORDS = {
        "select": ["SELECT", "FROM"],
        "insert": ["INSERT", "INTO"],
        "update": ["UPDATE", "SET"],
        "delete": ["DELETE", "FROM"],
    }
    
    def validate(self, command: str) -> ValidationResult:
        """Validate SQL command."""
        errors = []
        warnings = []
        
        command_upper = command.upper()
        
        # Check parentheses balance
        if command.count("(") != command.count(")"):
            errors.append("Unbalanced parentheses")
        
        # Check quotes balance
        single_quotes = command.count("'") - command.count("\\'") * 2
        if single_quotes % 2 != 0:
            errors.append("Unclosed string literal")
        
        # Check for dangerous patterns
        if "DELETE FROM" in command_upper and "WHERE" not in command_upper:
            warnings.append("DELETE without WHERE - will affect all rows")
        
        if "UPDATE" in command_upper and "WHERE" not in command_upper:
            warnings.append("UPDATE without WHERE - will affect all rows")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class SimpleShellValidator:
    """Simple shell command validator."""
    
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        ":(){:|:&};:",
        "mkfs",
        "dd if=/dev/zero",
    ]
    
    def validate(self, command: str) -> ValidationResult:
        """Validate shell command."""
        errors = []
        warnings = []
        
        # Check for dangerous patterns
        command_lower = command.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                errors.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for unclosed quotes
        if command.count("'") % 2 != 0:
            errors.append("Unclosed single quote")
        if command.count('"') % 2 != 0:
            errors.append("Unclosed double quote")
        
        # Check sudo usage
        if command.strip().startswith("sudo"):
            warnings.append("Command uses sudo - requires elevated privileges")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class SimpleDockerValidator:
    """Simple Docker command validator."""
    
    def validate(self, command: str) -> ValidationResult:
        """Validate Docker command."""
        errors = []
        warnings = []
        
        # Check if it starts with docker
        if not command.strip().startswith("docker"):
            errors.append("Command should start with 'docker'")
        
        # Check for privileged mode
        if "--privileged" in command:
            warnings.append("Running in privileged mode - security risk")
        
        # Check for host network
        if "--network=host" in command or "--net=host" in command:
            warnings.append("Using host network - may expose ports")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class SimpleKubernetesValidator:
    """Simple Kubernetes command validator."""
    
    PROTECTED_NAMESPACES = ["kube-system", "kube-public", "kube-node-lease"]
    
    def validate(self, command: str) -> ValidationResult:
        """Validate kubectl command."""
        errors = []
        warnings = []
        
        # Check if it starts with kubectl
        if not command.strip().startswith("kubectl"):
            errors.append("Command should start with 'kubectl'")
        
        # Check for operations on protected namespaces
        for ns in self.PROTECTED_NAMESPACES:
            if f"-n {ns}" in command or f"--namespace={ns}" in command:
                if "delete" in command.lower():
                    errors.append(f"Cannot delete in protected namespace: {ns}")
                else:
                    warnings.append(f"Operating on system namespace: {ns}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_default_validators() -> dict[str, DSLValidator]:
    """Create default validators for all domains."""
    return {
        "sql": SimpleSQLValidator(),
        "shell": SimpleShellValidator(),
        "docker": SimpleDockerValidator(),
        "kubernetes": SimpleKubernetesValidator(),
    }
