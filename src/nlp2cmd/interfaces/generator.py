"""Generator interface for NLP2CMD pipelines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class Generator(ABC):
    """Interface for command generators.

    Implementations may be synchronous or async, but should expose a generate
    method with the same signature.
    """

    @abstractmethod
    def generate(self, text: str, context: Optional[dict[str, Any]] = None) -> Any:
        """Generate a command or plan from natural language text."""
