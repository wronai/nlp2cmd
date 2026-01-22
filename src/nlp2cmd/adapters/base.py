"""
Base adapter for DSL transformations.

All DSL-specific adapters should inherit from BaseDSLAdapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SafetyPolicy:
    """Base safety policy configuration."""

    enabled: bool = True
    blocked_patterns: list[str] = field(default_factory=list)
    require_confirmation_for: list[str] = field(default_factory=list)
    max_complexity: int = 100
    custom_rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterConfig:
    """Configuration for DSL adapters."""

    safety_policy: SafetyPolicy = field(default_factory=SafetyPolicy)
    strict_mode: bool = False
    debug: bool = False
    custom_options: dict[str, Any] = field(default_factory=dict)


class BaseDSLAdapter(ABC):
    """
    Abstract base class for Domain-Specific Language adapters.

    Each DSL (SQL, Shell, Docker, etc.) should have its own adapter
    that implements the abstract methods defined here.
    """

    DSL_NAME: str = "base"
    DSL_VERSION: str = "1.0"

    # Intent patterns for this DSL
    INTENTS: dict[str, dict[str, Any]] = {}

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        safety_policy: Optional[SafetyPolicy] = None,
    ):
        """
        Initialize the adapter.

        Args:
            config: Adapter configuration
            safety_policy: Safety policy for command generation
        """
        self.config = config or AdapterConfig()
        if safety_policy:
            self.config.safety_policy = safety_policy

    @abstractmethod
    def generate(self, plan: dict[str, Any]) -> str:
        """
        Generate a DSL command from an execution plan.

        Args:
            plan: Execution plan dictionary with intent and entities

        Returns:
            Generated command string
        """
        raise NotImplementedError

    @abstractmethod
    def validate_syntax(self, command: str) -> dict[str, Any]:
        """
        Validate the syntax of a generated command.

        Args:
            command: Command string to validate

        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        raise NotImplementedError

    def check_safety(self, command: str) -> dict[str, Any]:
        """
        Check if a command passes safety policy.

        Args:
            command: Command string to check

        Returns:
            Dictionary with 'allowed' boolean and optional 'reason', 'alternatives'
        """
        policy = self.config.safety_policy

        if not policy.enabled:
            return {"allowed": True}

        # Check blocked patterns
        command_lower = command.lower()
        for pattern in policy.blocked_patterns:
            if pattern.lower() in command_lower:
                return {
                    "allowed": False,
                    "reason": f"Command contains blocked pattern: {pattern}",
                    "alternatives": [],
                }

        # Check confirmation requirements
        requires_confirmation = False
        for pattern in policy.require_confirmation_for:
            if pattern.lower() in command_lower:
                requires_confirmation = True
                break

        return {
            "allowed": True,
            "requires_confirmation": requires_confirmation,
        }

    def get_intents(self) -> dict[str, dict[str, Any]]:
        """Get available intents for this DSL."""
        return self.INTENTS.copy()

    def suggest_intent(self, text: str) -> Optional[str]:
        """
        Suggest an intent based on input text.

        Args:
            text: Natural language input

        Returns:
            Suggested intent name or None
        """
        text_lower = text.lower()

        for intent_name, intent_data in self.INTENTS.items():
            patterns = intent_data.get("patterns", [])
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    return intent_name

        return None

    def format_output(self, command: str, pretty: bool = False) -> str:
        """
        Format the output command.

        Args:
            command: Generated command
            pretty: Whether to apply pretty formatting

        Returns:
            Formatted command string
        """
        if pretty:
            return self._pretty_format(command)
        return command

    def _pretty_format(self, command: str) -> str:
        """Apply pretty formatting to command. Override in subclasses."""
        return command

    def get_schema_context(self) -> dict[str, Any]:
        """Get schema context for validation. Override in subclasses."""
        return {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} dsl={self.DSL_NAME}>"
