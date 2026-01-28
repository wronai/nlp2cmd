#!/usr/bin/env python3
"""
NLP2CMD Thermodynamic Computing Example.

Demonstrates:
1. Basic scheduling optimization with Langevin dynamics
2. Resource allocation with thermodynamic sampling
3. Hybrid DSL + thermodynamic generation
4. Energy savings estimation

Based on Whitelam 2025 "Generative Thermodynamic Computing"

Usage:
    python examples/thermodynamic_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_separator

import numpy as np

from nlp2cmd.generation import (
    create_thermodynamic_generator,
    ThermodynamicGenerator,
    OptimizationProblem,
)
from nlp2cmd.thermodynamic import (
    LangevinConfig,
    LangevinSampler,
    EnergyEstimator,
    MajorityVoter,
)


async def example_scheduling():
    """Example 1: Scheduling tasks with Langevin dynamics."""
    print_separator("📅 Example 1: Scheduling Optimization", leading_newline=True, width=60)

    # Create generator with adaptive steps for faster convergence
    generator = create_thermodynamic_generator(
        n_samples=5,
        n_steps=300,
        adaptive_steps=True,
    )

    # Polish natural language query
    query = "Zaplanuj 5 zadań w 10 slotach, zadanie 3 musi być przed slotem 5"
    print(f"\n📝 Query: {query}")

    result = await generator.generate(query)

    print(f"\n✅ Result:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Samples: {result.n_samples}")
    print(f"   Latency: {result.latency_ms:.1f}ms")

    if result.decoded_output:
        print(f"\n📋 Schedule:")
        print(result.decoded_output)

    if result.solution_quality:
        print(f"\n🔍 Solution Quality:")
        print(f"   Feasible: {result.solution_quality.is_feasible}")
        print(f"   Violations: {result.solution_quality.constraint_violations}")

    return result


async def example_allocation():
    """Example 2: Resource allocation with thermodynamic sampling."""
    print_separator("📦 Example 2: Resource Allocation", leading_newline=True, width=60)

    generator = create_thermodynamic_generator(
        n_samples=5,
        adaptive_steps=True,
    )

    # Polish query for resource allocation
    query = "Przydziel 3 zasoby do 4 konsumentów z balansowaniem obciążenia"
    print(f"\n📝 Query: {query}")

    result = await generator.generate(query)

    print(f"\n✅ Result:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Entropy Production: {result.entropy_production:.4f}")
    print(f"   Latency: {result.latency_ms:.1f}ms")

    if result.decoded_output:
        print(f"\n📊 Allocation:")
        print(result.decoded_output)

    return result


async def example_energy_savings():
    """Example 3: Energy savings estimation."""
    print_separator("⚡ Example 3: Energy Savings Analysis", leading_newline=True, width=60)

    estimator = EnergyEstimator()

    # Compare approaches for a scheduling problem
    estimate = estimator.estimate(
        llm_input_tokens=50,       # Input tokens
        llm_output_tokens_classic=100,  # Pure LLM output
        llm_output_tokens_hybrid=30,    # Hybrid (formalization only)
        langevin_steps=300,        # Langevin steps
    )

    print(f"\n📊 Energy Comparison:")
    print(f"   Pure LLM:      {estimate['llm_only_joules']*1000:.1f} mJ")
    print(f"   Hybrid (GPU):  {estimate['hybrid_digital_joules']*1000:.1f} mJ")
    print(f"   Hybrid (Analog): {estimate['hybrid_analog_joules']*1000:.1f} mJ")
    print(f"\n💚 Savings:")
    print(f"   Digital Langevin: {estimate['savings_digital_percent']:.1f}%")
    print(f"   Analog (future):  {estimate['savings_analog_percent']:.1f}%")

    return estimate


async def example_majority_voting():
    """Example 4: Majority voting strategies."""
    print_separator("🗳️ Example 4: Majority Voting Strategies", leading_newline=True, width=60)

    from nlp2cmd.thermodynamic import QuadraticEnergy, SamplerResult

    # Create mock results with different energies
    results = [
        SamplerResult(
            sample=np.array([0.1, 0.2]),
            energy=0.5,
            trajectory=None,
            entropy_production=0.1,
            n_steps=100,
            converged=True,
        ),
        SamplerResult(
            sample=np.array([0.15, 0.18]),
            energy=0.3,  # Best energy
            trajectory=None,
            entropy_production=0.2,
            n_steps=100,
            converged=True,
        ),
        SamplerResult(
            sample=np.array([0.5, 0.5]),
            energy=1.0,
            trajectory=None,
            entropy_production=0.05,  # Best entropy
            n_steps=100,
            converged=True,
        ),
    ]

    # Test different voting strategies
    for strategy in ["energy", "entropy", "combined"]:
        voter = MajorityVoter(strategy=strategy)
        best = voter.vote(results)
        print(f"\n   Strategy '{strategy}':")
        print(f"   Selected: energy={best.energy:.2f}, entropy={best.entropy_production:.2f}")


async def example_routing():
    """Example 5: Routing/TSP optimization with Langevin dynamics."""
    print_separator("🗺️ Example 5: Routing (TSP) Optimization", leading_newline=True, width=60)

    generator = create_thermodynamic_generator(
        n_samples=5,
        adaptive_steps=True,
    )

    # Polish query for routing
    query = "Znajdź optymalną trasę przez 5 miast"
    print(f"\n📝 Query: {query}")

    result = await generator.generate(query)

    print(f"\n✅ Result:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Latency: {result.latency_ms:.1f}ms")

    if result.decoded_output:
        print(f"\n{result.decoded_output}")

    if result.solution_quality:
        print(f"\n🔍 Solution Quality:")
        print(f"   Feasible: {result.solution_quality.is_feasible}")
        if result.solution_quality.constraint_violations:
            print(f"   Violations: {result.solution_quality.constraint_violations}")

    return result


async def example_direct_problem():
    """Example 6: Direct problem definition (without NL parsing)."""
    print_separator("🎯 Example 6: Direct Problem Definition", leading_newline=True, width=60)

    # Define problem directly (bypasses NL parsing)
    problem = OptimizationProblem(
        problem_type="schedule",
        variables=["task_0", "task_1", "task_2", "task_3"],
        constraints=[
            {"type": "deadline", "task": 2, "slot": 3},
            {"type": "deadline", "task": 3, "slot": 5},
        ],
        n_tasks=4,
        n_slots=8,
    )

    generator = create_thermodynamic_generator(n_samples=3)
    result = await generator.generate("", problem=problem)

    print(f"\n📋 Direct Problem:")
    print(f"   Type: {problem.problem_type}")
    print(f"   Variables: {problem.variables}")
    print(f"   Constraints: {problem.constraints}")

    print(f"\n✅ Result:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Feasible: {result.solution_quality.is_feasible if result.solution_quality else 'N/A'}")

    if result.decoded_output:
        print(f"\n{result.decoded_output}")


async def main():
    """Run all examples."""
    print_separator(
        "🌡️ NLP2CMD Thermodynamic Computing Examples",
        leading_newline=True,
        width=60,
    )
    print("\nBased on Whitelam 2025 'Generative Thermodynamic Computing'")
    print("Framework: Langevin dynamics for optimization problems")

    try:
        await example_scheduling()
        await example_allocation()
        await example_energy_savings()
        await example_majority_voting()
        await example_routing()
        await example_direct_problem()

        print_separator("✅ All examples completed successfully!", leading_newline=True, width=60)

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure numpy is installed: pip install numpy")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
