"""Energy model interface for thermodynamic optimization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class EnergyModel(ABC):
    """Interface for energy models used by thermodynamic samplers."""

    @abstractmethod
    def energy(self, z: Any, condition: Dict[str, Any]) -> float:
        """Compute energy V(z; c)."""

    @abstractmethod
    def gradient(self, z: Any, condition: Dict[str, Any]) -> Any:
        """Compute gradient ∇V(z; c)."""

    def __call__(self, z: Any, condition: Dict[str, Any]) -> float:
        return self.energy(z, condition)
