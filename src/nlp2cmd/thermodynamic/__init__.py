"""
Thermodynamic Computing Module for NLP2CMD.

Implements Whitelam's generative thermodynamic computing framework:
- Langevin dynamics sampling
- Energy-based models for constraints
- Entropy production regularization

Reference: Whitelam (2025) "Generative thermodynamic computing" arXiv:2506.15121
"""

from __future__ import annotations

import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class LangevinConfig:
    """Configuration for Langevin dynamics sampler."""
    
    mu: float = 1.0           # Mobility coefficient
    kT: float = 1.0           # Thermal energy (k_B * T)
    dt: float = 0.01          # Time step
    n_steps: int = 1000       # Number of integration steps
    dim: int = 64             # Latent dimension
    record_trajectory: bool = False  # Whether to record full trajectory
    seed: Optional[int] = None
    
    # Early stopping parameters
    early_stopping: bool = True    # Enable early stopping
    convergence_threshold: float = 0.01  # Energy threshold for convergence
    check_interval: int = 100      # Check convergence every N steps


@dataclass
class SamplerResult:
    """Result from Langevin sampling."""
    
    sample: np.ndarray                    # Final sample z
    energy: float                         # Final energy V(z)
    trajectory: Optional[np.ndarray]      # Full trajectory (if recorded)
    entropy_production: float             # Estimated entropy production
    n_steps: int                          # Actual steps taken
    converged: bool                       # Whether converged
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Energy Models (Abstract)
# =============================================================================

class EnergyModel(ABC):
    """
    Abstract base class for energy models.
    
    Energy function V(z; c) defines the probability distribution:
    p(z | c) ∝ exp(-V(z; c) / kT)
    """
    
    @abstractmethod
    def energy(self, z: np.ndarray, condition: Dict[str, Any]) -> float:
        """Compute energy V(z; c)."""
        raise NotImplementedError
    
    @abstractmethod
    def gradient(self, z: np.ndarray, condition: Dict[str, Any]) -> np.ndarray:
        """Compute energy gradient ∇V(z; c)."""
        raise NotImplementedError
    
    def __call__(self, z: np.ndarray, condition: Dict[str, Any]) -> float:
        return self.energy(z, condition)


class QuadraticEnergy(EnergyModel):
    """
    Simple quadratic energy for testing: V(z) = 0.5 * ||z - target||²
    """
    
    def __init__(self, target: Optional[np.ndarray] = None):
        self.target = target
    
    def energy(self, z: np.ndarray, condition: Dict[str, Any]) -> float:
        target = condition.get('target', self.target)
        if target is None:
            target = np.zeros_like(z)
        return 0.5 * np.sum((z - target) ** 2)
    
    def gradient(self, z: np.ndarray, condition: Dict[str, Any]) -> np.ndarray:
        target = condition.get('target', self.target)
        if target is None:
            target = np.zeros_like(z)
        return z - target


class ConstraintEnergy(EnergyModel):
    """
    Energy model for constraint satisfaction problems.
    
    V(z; c) = Σ_a λ_a φ_a(z; c)
    
    Where:
    - φ_a: penalty functions for constraint violations
    - λ_a: weights
    """
    
    def __init__(self):
        self.penalties: Dict[str, Callable] = {}
        self.lambdas: Dict[str, float] = {}
    
    def add_penalty(
        self, 
        name: str, 
        penalty_fn: Callable[[np.ndarray, Any], float],
        gradient_fn: Callable[[np.ndarray, Any], np.ndarray],
        weight: float = 1.0
    ):
        """Add a penalty function."""
        self.penalties[name] = (penalty_fn, gradient_fn)
        self.lambdas[name] = weight
    
    def energy(self, z: np.ndarray, condition: Dict[str, Any]) -> float:
        total = 0.0
        constraints = condition.get('constraints', {})
        for name, (penalty_fn, _) in self.penalties.items():
            if name in constraints:
                violation = penalty_fn(z, constraints[name])
                total += self.lambdas[name] * violation
        return total
    
    def gradient(self, z: np.ndarray, condition: Dict[str, Any]) -> np.ndarray:
        grad = np.zeros_like(z)
        constraints = condition.get('constraints', {})
        for name, (_, gradient_fn) in self.penalties.items():
            if name in constraints:
                g = gradient_fn(z, constraints[name])
                grad += self.lambdas[name] * g
        return grad


# =============================================================================
# Langevin Sampler
# =============================================================================

class LangevinSampler:
    """
    Thermodynamic sampler using overdamped Langevin dynamics.
    
    Implements: dz = -μ∇V(z;c)dt + √(2μkT) dW
    
    Discretized (Euler-Maruyama):
    z_{k+1} = z_k - μ∇V(z_k;c)Δt + √(2μkTΔt) η_k
    
    Where:
    - z: latent state
    - c: condition from LLM
    - V: energy function
    - η: standard normal noise
    """
    
    def __init__(self, energy_model: EnergyModel, config: Optional[LangevinConfig] = None):
        self.energy = energy_model
        self.config = config or LangevinConfig()
    
    def sample(
        self,
        condition: Dict[str, Any],
        n_samples: int = 1,
        initial_state: Optional[np.ndarray] = None,
    ) -> Union[SamplerResult, List[SamplerResult]]:
        """
        Generate samples via Langevin dynamics.
        
        Args:
            condition: Conditioning information (constraints, targets, etc.)
            n_samples: Number of independent samples
            initial_state: Starting point (default: random noise)
        
        Returns:
            SamplerResult or list of SamplerResult if n_samples > 1
        """
        if n_samples == 1:
            return self._sample_single(condition, initial_state)
        else:
            return [self._sample_single(condition, initial_state) for _ in range(n_samples)]
    
    def _sample_single(
        self,
        condition: Dict[str, Any],
        initial_state: Optional[np.ndarray] = None,
    ) -> SamplerResult:
        """Generate a single sample."""
        cfg = self.config
        
        # Set random seed if specified
        if cfg.seed is not None:
            np.random.seed(cfg.seed)
        
        # Initialize from noise or given state
        if initial_state is not None:
            z = initial_state.copy()
        else:
            z = np.random.randn(cfg.dim)
        
        # Precompute noise scaling
        noise_scale = math.sqrt(2 * cfg.mu * cfg.kT * cfg.dt)
        
        # Track trajectory if requested
        trajectory = [z.copy()] if cfg.record_trajectory else None
        
        # Track entropy production
        entropy_prod = 0.0
        
        # Langevin integration
        converged = False
        actual_steps = cfg.n_steps

        for step in range(cfg.n_steps):
            # Compute energy gradient
            grad_V = self.energy.gradient(z, condition)
            
            # Generate noise
            eta = np.random.randn(cfg.dim)
            
            # Langevin update: z_{k+1} = z_k - μ∇V·dt + √(2μkT·dt)·η
            dz = -cfg.mu * grad_V * cfg.dt + noise_scale * eta
            z = z + dz
            
            # Accumulate entropy production: σ ≈ Σ (∇V · Δz) / kT
            entropy_prod += np.dot(grad_V, dz) / cfg.kT
            
            if cfg.record_trajectory:
                trajectory.append(z.copy())

            # Convergence / early stopping
            if cfg.early_stopping and (step + 1) % cfg.check_interval == 0:
                current_energy = self.energy.energy(z, condition)
                if current_energy <= cfg.convergence_threshold:
                    converged = True
                    actual_steps = step + 1
                    break
        
        # Final energy
        final_energy = self.energy.energy(z, condition)

        if cfg.early_stopping and not converged:
            converged = final_energy <= cfg.convergence_threshold

        return SamplerResult(
            sample=z,
            energy=final_energy,
            trajectory=np.array(trajectory) if trajectory else None,
            entropy_production=entropy_prod,
            n_steps=actual_steps,
            converged=converged,
            metadata={'condition': condition}
        )
    
    def sample_parallel(
        self,
        condition: Dict[str, Any],
        n_samples: int,
        max_workers: int = 4,
    ) -> List[SamplerResult]:
        """Sample in parallel using thread pool."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._sample_single, condition, None)
                for _ in range(n_samples)
            ]
            results = [f.result() for f in as_completed(futures)]
        return results


# =============================================================================
# Entropy Production Regularizer
# =============================================================================

class EntropyProductionRegularizer:
    """
    Regularizer based on Whitelam's principle:
    
    L = -E[log P(ω̃)] + λ E[Q(ω̃)]
    
    Where Q is heat (entropy production) along trajectory.
    Lower entropy production = more reversible = better generative quality.
    """
    
    def __init__(self, lambda_entropy: float = 0.1, kT: float = 1.0):
        self.lambda_entropy = lambda_entropy
        self.kT = kT
    
    def compute_regularization(self, result: SamplerResult) -> float:
        """
        Compute entropy production regularization term.
        
        Lower values indicate more reversible (thermodynamically efficient) sampling.
        """
        return self.lambda_entropy * result.entropy_production
    
    def estimate_heat_dissipation(self, result: SamplerResult) -> float:
        """
        Estimate heat dissipation Q during sampling.
        
        Q = kT * σ where σ is entropy production
        """
        return self.kT * result.entropy_production


# =============================================================================
# Majority Voting
# =============================================================================

class MajorityVoter:
    """
    Select best sample from multiple candidates.
    
    Strategies:
    - 'energy': Select lowest energy sample
    - 'entropy': Select lowest entropy production
    - 'cluster': Cluster similar solutions, select from largest cluster
    """
    
    def __init__(self, strategy: str = 'energy'):
        self.strategy = strategy
    
    def vote(self, results: List[SamplerResult]) -> SamplerResult:
        """Select best result based on voting strategy."""
        if not results:
            raise ValueError("No results to vote on")
        
        if len(results) == 1:
            return results[0]
        
        if self.strategy == 'energy':
            return min(results, key=lambda r: r.energy)
        
        elif self.strategy == 'entropy':
            return min(results, key=lambda r: r.entropy_production)
        
        elif self.strategy == 'combined':
            # Weighted combination of energy and entropy
            def score(r):
                return r.energy + 0.1 * r.entropy_production
            return min(results, key=score)
        
        elif self.strategy == 'cluster':
            return self._cluster_vote(results)
        
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _cluster_vote(self, results: List[SamplerResult], threshold: float = 0.1) -> SamplerResult:
        """Cluster similar samples and select from largest cluster."""
        # Simple clustering by sample similarity
        clusters = []
        
        for result in results:
            added = False
            for cluster in clusters:
                # Check similarity to cluster centroid
                centroid = np.mean([r.sample for r in cluster], axis=0)
                dist = np.linalg.norm(result.sample - centroid)
                if dist < threshold:
                    cluster.append(result)
                    added = True
                    break
            
            if not added:
                clusters.append([result])
        
        # Select from largest cluster
        largest_cluster = max(clusters, key=len)
        
        # Return lowest energy from largest cluster
        return min(largest_cluster, key=lambda r: r.energy)


# =============================================================================
# Thermodynamic Router
# =============================================================================

class ThermodynamicRouter:
    """
    Routes problems to appropriate solver:
    - Classic DSL agents for simple queries
    - Langevin/EBM for constraint satisfaction
    """
    
    THERMODYNAMIC_INTENTS = {
        'schedule',         # Scheduling problems
        'allocate',         # Resource allocation
        'optimize',         # General optimization
        'sample',           # Bayesian sampling
        'plan',             # Planning with constraints
        'route',            # Routing/TSP problems
        'assign',           # Assignment problems
        'balance',          # Load balancing
    }
    
    CLASSIC_INTENTS = {
        'query',            # SQL queries
        'execute',          # Shell commands
        'deploy',           # Docker/K8s
        'transform',        # Data transformation
        'list',             # Listing resources
        'get',              # Getting information
        'create',           # Creating resources
        'delete',           # Deleting resources
    }
    
    def __init__(self, complexity_threshold: float = 0.5):
        self.complexity_threshold = complexity_threshold
    
    def route(self, intent: str, complexity: float = 0.5) -> str:
        """
        Decide solver type based on intent and complexity.
        
        Args:
            intent: Detected intent
            complexity: Estimated problem complexity (0-1)
        
        Returns:
            'classic' | 'langevin' | 'hybrid'
        """
        # Normalize intent
        intent_lower = intent.lower().strip()
        
        if intent_lower in self.THERMODYNAMIC_INTENTS:
            if complexity > self.complexity_threshold:
                return 'langevin'
            else:
                return 'hybrid'  # LLM formalization + Langevin sampling
        
        elif intent_lower in self.CLASSIC_INTENTS:
            return 'classic'
        
        else:
            # Unknown intent - default to hybrid for safety
            return 'hybrid' if complexity > self.complexity_threshold else 'classic'
    
    def estimate_complexity(self, problem_description: str, entities: Dict[str, Any]) -> float:
        """
        Estimate problem complexity based on description and entities.
        
        Heuristics:
        - Number of constraints
        - Number of variables
        - Problem size indicators
        """
        complexity = 0.3  # Base complexity
        
        # Count constraints
        n_constraints = len(entities.get('constraints', []))
        complexity += min(0.3, n_constraints * 0.05)
        
        # Check for optimization keywords
        opt_keywords = ['minimize', 'maximize', 'optimal', 'best', 'efficient']
        if any(kw in problem_description.lower() for kw in opt_keywords):
            complexity += 0.2
        
        # Check for combinatorial keywords
        comb_keywords = ['schedule', 'assign', 'allocate', 'route', 'plan']
        if any(kw in problem_description.lower() for kw in comb_keywords):
            complexity += 0.15
        
        return min(1.0, complexity)


# =============================================================================
# Energy Estimation
# =============================================================================

class EnergyEstimator:
    """
    Estimate computational energy consumption.
    
    Compares:
    - Pure LLM approach (all tokens through transformer)
    - Hybrid approach (LLM formalization + Langevin sampling)
    - Future analog approach (LLM + analog Langevin)
    """
    
    # Approximate energy per operation (Joules)
    LLM_ENERGY_PER_TOKEN = 0.003        # ~3mJ per token (GPU inference)
    LANGEVIN_DIGITAL_PER_STEP = 0.0003  # ~0.3mJ per step (CPU/GPU)
    LANGEVIN_ANALOG_PER_STEP = 0.00001  # ~0.01mJ per step (theoretical)
    
    def estimate(
        self,
        llm_input_tokens: int,
        llm_output_tokens_classic: int,
        llm_output_tokens_hybrid: int,
        langevin_steps: int,
    ) -> Dict[str, float]:
        """
        Estimate energy for different approaches.
        
        Args:
            llm_input_tokens: Input tokens (same for all approaches)
            llm_output_tokens_classic: Output tokens for pure LLM approach
            llm_output_tokens_hybrid: Output tokens for hybrid (formalization only)
            langevin_steps: Number of Langevin steps
        
        Returns:
            Dictionary with energy estimates and savings
        """
        # Pure LLM
        llm_only = (llm_input_tokens + llm_output_tokens_classic) * self.LLM_ENERGY_PER_TOKEN
        
        # Hybrid (digital Langevin)
        llm_formalization = (llm_input_tokens + llm_output_tokens_hybrid) * self.LLM_ENERGY_PER_TOKEN
        langevin_digital = langevin_steps * self.LANGEVIN_DIGITAL_PER_STEP
        hybrid_digital = llm_formalization + langevin_digital
        
        # Hybrid (analog Langevin - future)
        langevin_analog = langevin_steps * self.LANGEVIN_ANALOG_PER_STEP
        hybrid_analog = llm_formalization + langevin_analog
        
        return {
            'llm_only_joules': llm_only,
            'hybrid_digital_joules': hybrid_digital,
            'hybrid_analog_joules': hybrid_analog,
            'savings_digital_percent': (llm_only - hybrid_digital) / llm_only * 100,
            'savings_analog_percent': (llm_only - hybrid_analog) / llm_only * 100,
            'breakdown': {
                'llm_formalization': llm_formalization,
                'langevin_digital': langevin_digital,
                'langevin_analog': langevin_analog,
            }
        }


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    # Config
    'LangevinConfig',
    'SamplerResult',
    
    # Energy models
    'EnergyModel',
    'QuadraticEnergy',
    'ConstraintEnergy',
    
    # Samplers
    'LangevinSampler',
    
    # Utilities
    'EntropyProductionRegularizer',
    'MajorityVoter',
    'ThermodynamicRouter',
    'EnergyEstimator',
]
