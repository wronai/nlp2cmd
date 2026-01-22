"""
Iteration 10: Thermodynamic Optimization Integration.

Integrate Langevin sampling for complex optimization problems:
- Scheduling, allocation, routing, planning
- Energy-based constraint satisfaction
- Hybrid LLM formalization + thermodynamic sampling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import numpy as np

from nlp2cmd.thermodynamic import (
    LangevinConfig,
    LangevinSampler,
    SamplerResult,
    EnergyModel,
    ConstraintEnergy,
    MajorityVoter,
    ThermodynamicRouter,
    EnergyEstimator,
    EntropyProductionRegularizer,
)
from nlp2cmd.generation.structured import StructuredPlan, StructuredLLMPlanner
from nlp2cmd.generation.llm_simple import LLMClient, LLMConfig


@dataclass
class OptimizationProblem:
    """Structured optimization problem definition."""
    
    problem_type: str  # schedule, allocate, route, assign, balance
    variables: list[str]
    constraints: list[dict[str, Any]]
    objective: Optional[str] = None  # minimize, maximize
    objective_field: Optional[str] = None
    bounds: Optional[dict[str, tuple[float, float]]] = None
    
    def to_condition(self) -> dict[str, Any]:
        """Convert to condition dict for Langevin sampler."""
        return {
            "problem_type": self.problem_type,
            "constraints": self.constraints,
            "objective": self.objective,
            "bounds": self.bounds,
        }


@dataclass
class ThermodynamicResult:
    """Result of thermodynamic optimization."""
    
    problem: OptimizationProblem
    solution: dict[str, Any]
    energy: float
    entropy_production: float
    n_samples: int
    converged: bool
    latency_ms: float
    
    # Decoded solution
    decoded_output: Optional[str] = None
    
    # Energy estimation
    energy_estimate: Optional[dict[str, float]] = None
    
    errors: list[str] = field(default_factory=list)


class SchedulingEnergy(EnergyModel):
    """
    Energy model for scheduling problems.
    
    Penalizes:
    - Task overlaps
    - Deadline violations
    - Resource overallocation
    """
    
    OVERLAP_PENALTY = 100.0
    DEADLINE_PENALTY = 50.0
    PREFERENCE_PENALTY = 10.0
    
    def __init__(self, n_tasks: int, n_slots: int):
        self.n_tasks = n_tasks
        self.n_slots = n_slots
    
    def energy(self, z: np.ndarray, condition: dict[str, Any]) -> float:
        """Compute scheduling energy."""
        # Decode z into task-slot assignments
        assignments = self._decode_assignments(z)
        
        total_energy = 0.0
        constraints = condition.get("constraints", [])
        
        # Overlap penalty
        for slot in range(self.n_slots):
            tasks_in_slot = sum(1 for a in assignments if a == slot)
            if tasks_in_slot > 1:
                total_energy += self.OVERLAP_PENALTY * (tasks_in_slot - 1)
        
        # Deadline constraints
        for c in constraints:
            if c.get("type") == "deadline":
                task_idx = c.get("task", 0)
                deadline_slot = c.get("slot", self.n_slots)
                if task_idx < len(assignments):
                    if assignments[task_idx] > deadline_slot:
                        violation = assignments[task_idx] - deadline_slot
                        total_energy += self.DEADLINE_PENALTY * violation
        
        return total_energy
    
    def gradient(self, z: np.ndarray, condition: dict[str, Any]) -> np.ndarray:
        """Compute gradient numerically."""
        eps = 1e-5
        grad = np.zeros_like(z)
        e0 = self.energy(z, condition)
        
        for i in range(len(z)):
            z_plus = z.copy()
            z_plus[i] += eps
            grad[i] = (self.energy(z_plus, condition) - e0) / eps
        
        return grad
    
    def _decode_assignments(self, z: np.ndarray) -> list[int]:
        """Decode continuous z to discrete slot assignments."""
        # Each task gets n_slots values, softmax to get assignment
        assignments = []
        chunk_size = self.n_slots
        
        for i in range(self.n_tasks):
            start = i * chunk_size
            end = start + chunk_size
            if end <= len(z):
                probs = self._softmax(z[start:end])
                assignments.append(int(np.argmax(probs)))
            else:
                assignments.append(0)
        
        return assignments
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Stable softmax."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()


class AllocationEnergy(EnergyModel):
    """
    Energy model for resource allocation problems.
    
    Penalizes:
    - Capacity violations
    - Unmet demands
    - Imbalanced allocation
    """
    
    CAPACITY_PENALTY = 100.0
    DEMAND_PENALTY = 50.0
    BALANCE_PENALTY = 5.0
    
    def __init__(self, n_resources: int, n_consumers: int):
        self.n_resources = n_resources
        self.n_consumers = n_consumers
    
    def energy(self, z: np.ndarray, condition: dict[str, Any]) -> float:
        """Compute allocation energy."""
        # Decode z into allocation matrix
        allocation = self._decode_allocation(z)
        
        total_energy = 0.0
        constraints = condition.get("constraints", [])
        
        # Capacity constraints
        for c in constraints:
            if c.get("type") == "capacity":
                resource_idx = c.get("resource", 0)
                capacity = c.get("value", float("inf"))
                if resource_idx < self.n_resources:
                    usage = allocation[:, resource_idx].sum()
                    if usage > capacity:
                        total_energy += self.CAPACITY_PENALTY * (usage - capacity)
        
        # Demand constraints
        for c in constraints:
            if c.get("type") == "demand":
                consumer_idx = c.get("consumer", 0)
                demand = c.get("value", 0)
                if consumer_idx < self.n_consumers:
                    allocated = allocation[consumer_idx, :].sum()
                    if allocated < demand:
                        total_energy += self.DEMAND_PENALTY * (demand - allocated)
        
        # Balance penalty (variance in allocation)
        resource_usage = allocation.sum(axis=0)
        if len(resource_usage) > 1:
            total_energy += self.BALANCE_PENALTY * np.var(resource_usage)
        
        return total_energy
    
    def gradient(self, z: np.ndarray, condition: dict[str, Any]) -> np.ndarray:
        """Compute gradient numerically."""
        eps = 1e-5
        grad = np.zeros_like(z)
        e0 = self.energy(z, condition)
        
        for i in range(len(z)):
            z_plus = z.copy()
            z_plus[i] += eps
            grad[i] = (self.energy(z_plus, condition) - e0) / eps
        
        return grad
    
    def _decode_allocation(self, z: np.ndarray) -> np.ndarray:
        """Decode continuous z to allocation matrix."""
        # Reshape and apply softmax per consumer
        size = self.n_consumers * self.n_resources
        z_resized = z[:size] if len(z) >= size else np.pad(z, (0, size - len(z)))
        
        matrix = z_resized.reshape(self.n_consumers, self.n_resources)
        
        # Apply sigmoid to get [0, 1] allocation values
        return 1 / (1 + np.exp(-matrix))


class ThermodynamicGenerator:
    """
    Generate solutions for optimization problems using Langevin sampling.
    
    Workflow:
    1. Parse NL problem description (via LLM or rules)
    2. Build energy model for problem type
    3. Run Langevin sampling
    4. Decode solution and format output
    
    Example:
        generator = ThermodynamicGenerator()
        result = await generator.generate(
            "Zaplanuj 5 zadań w 10 slotach, zadanie 3 musi być przed slotem 5"
        )
    """
    
    # Problem type to energy model mapping
    ENERGY_MODELS: dict[str, type[EnergyModel]] = {
        "schedule": SchedulingEnergy,
        "allocate": AllocationEnergy,
    }
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        langevin_config: Optional[LangevinConfig] = None,
        n_samples: int = 5,
        voting_strategy: str = "energy",
    ):
        self.llm = llm_client
        self.langevin_config = langevin_config or LangevinConfig(
            n_steps=500,
            kT=0.5,
            mu=1.0,
        )
        self.n_samples = n_samples
        self.voter = MajorityVoter(strategy=voting_strategy)
        self.router = ThermodynamicRouter()
        self.energy_estimator = EnergyEstimator()
        self.regularizer = EntropyProductionRegularizer()
        
        if llm_client:
            self.planner = StructuredLLMPlanner(llm_client)
        else:
            self.planner = None
    
    async def generate(
        self,
        text: str,
        problem: Optional[OptimizationProblem] = None,
    ) -> ThermodynamicResult:
        """
        Generate solution for optimization problem.
        
        Args:
            text: Natural language problem description
            problem: Pre-parsed problem (optional)
            
        Returns:
            ThermodynamicResult with solution
        """
        import time
        start = time.time()
        
        try:
            # Parse problem if not provided
            if problem is None:
                problem = await self._parse_problem(text)
            
            # Get or create energy model
            energy_model = self._create_energy_model(problem)
            
            # Configure sampler
            sampler = LangevinSampler(energy_model, self.langevin_config)
            
            # Sample multiple solutions
            condition = problem.to_condition()
            results = sampler.sample(condition, n_samples=self.n_samples)
            
            if not isinstance(results, list):
                results = [results]
            
            # Vote for best solution
            best = self.voter.vote(results)
            
            # Decode solution
            solution = self._decode_solution(best, problem, energy_model)
            
            # Format output
            decoded_output = self._format_output(solution, problem)
            
            # Estimate energy savings
            energy_estimate = self.energy_estimator.estimate(
                llm_input_tokens=len(text.split()),
                llm_output_tokens_classic=100,
                llm_output_tokens_hybrid=30,
                langevin_steps=self.langevin_config.n_steps,
            )
            
            latency = (time.time() - start) * 1000
            
            return ThermodynamicResult(
                problem=problem,
                solution=solution,
                energy=best.energy,
                entropy_production=best.entropy_production,
                n_samples=len(results),
                converged=best.converged,
                latency_ms=latency,
                decoded_output=decoded_output,
                energy_estimate=energy_estimate,
            )
            
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ThermodynamicResult(
                problem=problem or OptimizationProblem("unknown", [], []),
                solution={},
                energy=float("inf"),
                entropy_production=0.0,
                n_samples=0,
                converged=False,
                latency_ms=latency,
                errors=[str(e)],
            )
    
    async def _parse_problem(self, text: str) -> OptimizationProblem:
        """Parse problem from natural language."""
        # Try LLM if available
        if self.planner:
            result = await self.planner.plan(text)
            if result.success and result.plan:
                return self._plan_to_problem(result.plan)
        
        # Fallback: rule-based parsing
        return self._rule_based_parse(text)
    
    def _plan_to_problem(self, plan: StructuredPlan) -> OptimizationProblem:
        """Convert structured plan to optimization problem."""
        entities = plan.entities
        
        return OptimizationProblem(
            problem_type=plan.intent,
            variables=entities.get("variables", []),
            constraints=entities.get("constraints", []),
            objective=entities.get("objective"),
            objective_field=entities.get("objective_field"),
            bounds=entities.get("bounds"),
        )
    
    def _rule_based_parse(self, text: str) -> OptimizationProblem:
        """Simple rule-based problem parsing."""
        text_lower = text.lower()
        
        # Detect problem type
        if "zaplanuj" in text_lower or "schedule" in text_lower or "zadań" in text_lower:
            problem_type = "schedule"
        elif "przydziel" in text_lower or "allocate" in text_lower or "zasobów" in text_lower:
            problem_type = "allocate"
        else:
            problem_type = "schedule"  # default
        
        # Extract numbers
        import re
        numbers = [int(n) for n in re.findall(r'\d+', text)]
        
        # Build constraints from text
        constraints = []
        
        if "przed" in text_lower or "before" in text_lower:
            # Deadline constraint
            if len(numbers) >= 2:
                constraints.append({
                    "type": "deadline",
                    "task": numbers[0] if len(numbers) > 0 else 0,
                    "slot": numbers[1] if len(numbers) > 1 else 5,
                })
        
        return OptimizationProblem(
            problem_type=problem_type,
            variables=[f"task_{i}" for i in range(numbers[0] if numbers else 5)],
            constraints=constraints,
        )
    
    def _create_energy_model(self, problem: OptimizationProblem) -> EnergyModel:
        """Create appropriate energy model for problem."""
        n_vars = len(problem.variables) or 5
        
        if problem.problem_type == "schedule":
            # Default: 10 time slots
            n_slots = 10
            return SchedulingEnergy(n_tasks=n_vars, n_slots=n_slots)
        
        elif problem.problem_type == "allocate":
            # Default: 5 resources
            n_resources = 5
            return AllocationEnergy(n_resources=n_resources, n_consumers=n_vars)
        
        else:
            # Generic constraint energy
            return ConstraintEnergy()
    
    def _decode_solution(
        self,
        result: SamplerResult,
        problem: OptimizationProblem,
        energy_model: EnergyModel,
    ) -> dict[str, Any]:
        """Decode sampler result to solution dict."""
        z = result.sample
        
        if isinstance(energy_model, SchedulingEnergy):
            assignments = energy_model._decode_assignments(z)
            return {
                "assignments": {
                    var: slot
                    for var, slot in zip(problem.variables, assignments)
                },
                "raw_sample": z.tolist(),
            }
        
        elif isinstance(energy_model, AllocationEnergy):
            allocation = energy_model._decode_allocation(z)
            return {
                "allocation": allocation.tolist(),
                "raw_sample": z.tolist(),
            }
        
        return {"raw_sample": z.tolist()}
    
    def _format_output(
        self,
        solution: dict[str, Any],
        problem: OptimizationProblem,
    ) -> str:
        """Format solution as readable output."""
        if problem.problem_type == "schedule":
            assignments = solution.get("assignments", {})
            lines = ["# Schedule:"]
            for task, slot in sorted(assignments.items(), key=lambda x: x[1]):
                lines.append(f"  Slot {slot}: {task}")
            return "\n".join(lines)
        
        elif problem.problem_type == "allocate":
            allocation = solution.get("allocation", [])
            lines = ["# Allocation:"]
            for i, row in enumerate(allocation):
                resources = ", ".join(f"R{j}={v:.2f}" for j, v in enumerate(row))
                lines.append(f"  Consumer {i}: {resources}")
            return "\n".join(lines)
        
        return f"# Solution:\n{solution}"


class HybridThermodynamicGenerator:
    """
    Hybrid generator combining rule/LLM-based DSL with thermodynamic optimization.
    
    Routes:
    - Simple queries → Rule-based or LLM generation
    - Optimization problems → Thermodynamic sampling
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        langevin_config: Optional[LangevinConfig] = None,
    ):
        from nlp2cmd.generation.hybrid import HybridGenerator, create_hybrid_generator
        
        self.dsl_generator = create_hybrid_generator(llm_client)
        self.thermo_generator = ThermodynamicGenerator(
            llm_client=llm_client,
            langevin_config=langevin_config,
        )
        self.router = ThermodynamicRouter()
    
    async def generate(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Route and generate based on problem type.
        
        Returns dict with:
        - source: 'dsl' or 'thermodynamic'
        - result: Generation result
        """
        # Estimate complexity and route
        entities = context.get("entities", {}) if context else {}
        complexity = self.router.estimate_complexity(text, entities)
        
        # Detect intent for routing
        text_lower = text.lower()
        
        # Check for optimization keywords
        opt_keywords = ["zaplanuj", "schedule", "przydziel", "allocate", 
                       "optymalizuj", "optimize", "rozłóż", "balance"]
        
        is_optimization = any(kw in text_lower for kw in opt_keywords)
        
        if is_optimization and complexity > 0.4:
            # Use thermodynamic generator
            result = await self.thermo_generator.generate(text)
            return {
                "source": "thermodynamic",
                "result": result,
                "complexity": complexity,
            }
        else:
            # Use DSL generator
            result = await self.dsl_generator.generate(text, context)
            return {
                "source": "dsl",
                "result": result,
                "complexity": complexity,
            }


def create_thermodynamic_generator(
    llm_client: Optional[LLMClient] = None,
    n_samples: int = 5,
    n_steps: int = 500,
) -> ThermodynamicGenerator:
    """Factory function for thermodynamic generator."""
    config = LangevinConfig(
        n_steps=n_steps,
        kT=0.5,
        mu=1.0,
        dim=64,
    )
    
    return ThermodynamicGenerator(
        llm_client=llm_client,
        langevin_config=config,
        n_samples=n_samples,
    )
