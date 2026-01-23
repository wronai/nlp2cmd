"""
Base solver class for thermodynamic optimization.

This module provides a common base class for all thermodynamic
optimization solvers, implementing shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
import time


class BaseSolver(ABC):
    """Base class for thermodynamic optimization solvers."""
    
    def __init__(self):
        self.solution_history = []
        self.best_solution = None
        self.best_energy = float('inf')
        self.start_time = None
        self.end_time = None
    
    @abstractmethod
    def solve(self, *args, **kwargs) -> Any:
        """Solve the optimization problem."""
        pass
    
    def _should_accept_solution(self, current_energy: float, new_energy: float, temperature: float) -> bool:
        """Metropolis acceptance criterion."""
        if new_energy < current_energy:
            return True
        
        # Accept with some probability even if worse
        acceptance_prob = np.exp(-(new_energy - current_energy) / temperature)
        return np.random.random() < acceptance_prob
    
    def _calculate_solution_energy(self, solution: Any) -> float:
        """Calculate energy of solution (lower is better)."""
        # Default implementation - should be overridden
        return 0.0
    
    def _record_iteration(self, iteration: int, energy: float, temperature: float, solution: Any):
        """Record iteration data for analysis."""
        self.solution_history.append({
            'iteration': iteration,
            'energy': energy,
            'temperature': temperature,
            'solution': solution,
            'timestamp': time.time()
        })
        
        # Update best solution
        if energy < self.best_energy:
            self.best_energy = energy
            self.best_solution = solution
    
    def get_solution_stats(self) -> Dict[str, Any]:
        """Get statistics about the solution process."""
        if not self.solution_history:
            return {}
        
        energies = [entry['energy'] for entry in self.solution_history]
        temperatures = [entry['temperature'] for entry in self.solution_history]
        
        return {
            'iterations': len(self.solution_history),
            'best_energy': self.best_energy,
            'initial_energy': energies[0] if energies else None,
            'final_energy': energies[-1] if energies else None,
            'energy_improvement': energies[0] - self.best_energy if energies else 0,
            'initial_temperature': temperatures[0] if temperatures else None,
            'final_temperature': temperatures[-1] if temperatures else None,
            'convergence_iteration': self._find_convergence_iteration(energies),
            'execution_time': self.end_time - self.start_time if self.start_time and self.end_time else None
        }
    
    def _find_convergence_iteration(self, energies: List[float], window_size: int = 10) -> Optional[int]:
        """Find the iteration where the solution converged."""
        if len(energies) < window_size * 2:
            return None
        
        # Look for the point where improvement becomes minimal
        for i in range(window_size, len(energies) - window_size):
            window_before = energies[i - window_size:i]
            window_after = energies[i:i + window_size]
            
            improvement_before = window_before[0] - window_before[-1]
            improvement_after = window_after[0] - window_after[-1]
            
            # If improvement drops significantly, consider it converged
            if improvement_after < improvement_before * 0.1:
                return i
        
        return None
    
    def reset(self):
        """Reset solver state."""
        self.solution_history = []
        self.best_solution = None
        self.best_energy = float('inf')
        self.start_time = None
        self.end_time = None
    
    def _start_timing(self):
        """Start timing the solution process."""
        self.start_time = time.time()
    
    def _end_timing(self):
        """End timing the solution process."""
        self.end_time = time.time()
    
    def get_energy_history(self) -> List[float]:
        """Get the energy history."""
        return [entry['energy'] for entry in self.solution_history]
    
    def get_temperature_history(self) -> List[float]:
        """Get the temperature history."""
        return [entry['temperature'] for entry in self.solution_history]
