"""Sampler interface for thermodynamic optimization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Sampler(ABC):
    """Interface for Langevin-style samplers."""

    @abstractmethod
    def sample(self, condition: Dict[str, Any], n_samples: int = 1) -> Any:
        """Sample one or more solutions for a given condition."""

    def sample_parallel(
        self,
        condition: Dict[str, Any],
        n_samples: int = 1,
        max_workers: Optional[int] = None,
    ) -> Any:
        """Optional parallel sampling helper (override if supported)."""
        raise NotImplementedError
