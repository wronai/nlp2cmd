#!/usr/bin/env python3
"""
Benchmark script for NLP2CMD Thermodynamic Computing.

Measures:
1. Performance improvements from adaptive steps
2. Parallel vs sequential sampling speedup
3. Energy savings estimation
4. Problem type comparison (schedule, allocate, route)

Usage:
    PYTHONPATH=src python3 benchmarks/thermodynamic_benchmark.py
"""

import asyncio
import time
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from nlp2cmd.generation.thermodynamic import (
    create_thermodynamic_generator,
    ThermodynamicGenerator,
    OptimizationProblem,
    SchedulingEnergy,
    AllocationEnergy,
    RoutingEnergy,
)
from nlp2cmd.thermodynamic import (
    LangevinConfig,
    LangevinSampler,
    QuadraticEnergy,
    EnergyEstimator,
)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_time_ms: float
    avg_energy: float
    convergence_rate: float
    extra: Dict[str, Any] = None


def benchmark_langevin_sampler(
    n_iterations: int = 10,
    n_steps: int = 200,
    dim: int = 20,
) -> BenchmarkResult:
    """Benchmark raw Langevin sampler performance."""
    config = LangevinConfig(n_steps=n_steps, dim=dim, kT=0.5)
    energy = QuadraticEnergy(target=np.zeros(dim))
    sampler = LangevinSampler(energy, config)
    
    times = []
    energies = []
    converged_count = 0
    
    for _ in range(n_iterations):
        start = time.perf_counter()
        result = sampler.sample({}, n_samples=1)
        elapsed = (time.perf_counter() - start) * 1000
        
        times.append(elapsed)
        energies.append(result.energy)
        if result.converged:
            converged_count += 1
    
    return BenchmarkResult(
        name=f"LangevinSampler (steps={n_steps}, dim={dim})",
        iterations=n_iterations,
        total_time_ms=sum(times),
        avg_time_ms=np.mean(times),
        min_time_ms=np.min(times),
        max_time_ms=np.max(times),
        std_time_ms=np.std(times),
        avg_energy=np.mean(energies),
        convergence_rate=converged_count / n_iterations,
    )


def benchmark_parallel_vs_sequential(
    n_samples: int = 5,
    n_steps: int = 100,
    dim: int = 10,
) -> tuple[BenchmarkResult, BenchmarkResult]:
    """Compare parallel vs sequential sampling."""
    config = LangevinConfig(n_steps=n_steps, dim=dim, kT=0.5)
    energy = QuadraticEnergy(target=np.zeros(dim))
    sampler = LangevinSampler(energy, config)
    
    # Sequential
    seq_times = []
    for _ in range(5):
        start = time.perf_counter()
        results = sampler.sample({}, n_samples=n_samples)
        elapsed = (time.perf_counter() - start) * 1000
        seq_times.append(elapsed)
    
    seq_result = BenchmarkResult(
        name=f"Sequential ({n_samples} samples)",
        iterations=5,
        total_time_ms=sum(seq_times),
        avg_time_ms=np.mean(seq_times),
        min_time_ms=np.min(seq_times),
        max_time_ms=np.max(seq_times),
        std_time_ms=np.std(seq_times),
        avg_energy=np.mean([r.energy for r in results]),
        convergence_rate=sum(1 for r in results if r.converged) / n_samples,
    )
    
    # Parallel
    par_times = []
    for _ in range(5):
        start = time.perf_counter()
        results = sampler.sample_parallel({}, n_samples=n_samples, max_workers=4)
        elapsed = (time.perf_counter() - start) * 1000
        par_times.append(elapsed)
    
    par_result = BenchmarkResult(
        name=f"Parallel ({n_samples} samples, 4 workers)",
        iterations=5,
        total_time_ms=sum(par_times),
        avg_time_ms=np.mean(par_times),
        min_time_ms=np.min(par_times),
        max_time_ms=np.max(par_times),
        std_time_ms=np.std(par_times),
        avg_energy=np.mean([r.energy for r in results]),
        convergence_rate=sum(1 for r in results if r.converged) / n_samples,
        extra={"speedup": seq_result.avg_time_ms / np.mean(par_times)},
    )
    
    return seq_result, par_result


def benchmark_adaptive_steps(
    problem_sizes: List[int] = [2, 5, 10, 20],
) -> List[BenchmarkResult]:
    """Benchmark adaptive steps for different problem sizes."""
    results = []
    
    for size in problem_sizes:
        # With adaptive steps
        gen_adaptive = create_thermodynamic_generator(
            n_samples=3,
            n_steps=500,
            adaptive_steps=True,
        )
        
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=[f"task_{i}" for i in range(size)],
            constraints=[],
            n_tasks=size,
            n_slots=size * 2,
        )
        
        config_adaptive, _ = gen_adaptive._get_sampling_config(problem)
        
        # Without adaptive steps
        gen_fixed = create_thermodynamic_generator(
            n_samples=3,
            n_steps=500,
            adaptive_steps=False,
        )
        
        config_fixed, _ = gen_fixed._get_sampling_config(problem)
        
        step_reduction = (config_fixed.n_steps - config_adaptive.n_steps) / config_fixed.n_steps * 100
        
        results.append(BenchmarkResult(
            name=f"Problem size {size}",
            iterations=1,
            total_time_ms=0,
            avg_time_ms=0,
            min_time_ms=0,
            max_time_ms=0,
            std_time_ms=0,
            avg_energy=0,
            convergence_rate=0,
            extra={
                "adaptive_steps": config_adaptive.n_steps,
                "fixed_steps": config_fixed.n_steps,
                "step_reduction_percent": step_reduction,
            },
        ))
    
    return results


async def benchmark_generator_problems(
    n_iterations: int = 5,
) -> List[BenchmarkResult]:
    """Benchmark different problem types with ThermodynamicGenerator."""
    problems = [
        ("Scheduling (5 tasks)", "Zaplanuj 5 zadań w 10 slotach"),
        ("Allocation (3x4)", "Przydziel 3 zasoby do 4 konsumentów"),
        ("Routing (5 cities)", "Znajdź trasę przez 5 miast"),
    ]
    
    results = []
    
    for name, query in problems:
        generator = create_thermodynamic_generator(
            n_samples=3,
            n_steps=200,
            adaptive_steps=True,
        )
        
        times = []
        energies = []
        
        for _ in range(n_iterations):
            start = time.perf_counter()
            result = await generator.generate(query)
            elapsed = (time.perf_counter() - start) * 1000
            
            times.append(elapsed)
            energies.append(result.energy)
        
        results.append(BenchmarkResult(
            name=name,
            iterations=n_iterations,
            total_time_ms=sum(times),
            avg_time_ms=np.mean(times),
            min_time_ms=np.min(times),
            max_time_ms=np.max(times),
            std_time_ms=np.std(times),
            avg_energy=np.mean(energies),
            convergence_rate=1.0,  # Generator always returns
        ))
    
    return results


def benchmark_energy_savings() -> Dict[str, Any]:
    """Calculate energy savings for different scenarios."""
    estimator = EnergyEstimator()
    
    scenarios = [
        {
            "name": "Simple query (5 vars)",
            "llm_input": 30,
            "llm_output_classic": 50,
            "llm_output_hybrid": 20,
            "langevin_steps": 100,
        },
        {
            "name": "Medium query (20 vars)",
            "llm_input": 50,
            "llm_output_classic": 150,
            "llm_output_hybrid": 40,
            "langevin_steps": 300,
        },
        {
            "name": "Complex query (50+ vars)",
            "llm_input": 100,
            "llm_output_classic": 300,
            "llm_output_hybrid": 60,
            "langevin_steps": 500,
        },
    ]
    
    results = []
    for scenario in scenarios:
        estimate = estimator.estimate(
            llm_input_tokens=scenario["llm_input"],
            llm_output_tokens_classic=scenario["llm_output_classic"],
            llm_output_tokens_hybrid=scenario["llm_output_hybrid"],
            langevin_steps=scenario["langevin_steps"],
        )
        
        results.append({
            "name": scenario["name"],
            "llm_only_mJ": estimate["llm_only_joules"] * 1000,
            "hybrid_digital_mJ": estimate["hybrid_digital_joules"] * 1000,
            "hybrid_analog_mJ": estimate["hybrid_analog_joules"] * 1000,
            "savings_digital_%": estimate["savings_digital_percent"],
            "savings_analog_%": estimate["savings_analog_percent"],
        })
    
    return results


def print_benchmark_result(result: BenchmarkResult):
    """Pretty print a benchmark result."""
    print(f"\n  📊 {result.name}")
    print(f"     Iterations: {result.iterations}")
    print(f"     Avg time:   {result.avg_time_ms:.2f}ms (±{result.std_time_ms:.2f})")
    print(f"     Min/Max:    {result.min_time_ms:.2f}ms / {result.max_time_ms:.2f}ms")
    print(f"     Avg energy: {result.avg_energy:.4f}")
    print(f"     Convergence: {result.convergence_rate*100:.1f}%")
    if result.extra:
        for k, v in result.extra.items():
            if isinstance(v, float):
                print(f"     {k}: {v:.2f}")
            else:
                print(f"     {k}: {v}")


async def main():
    """Run all benchmarks."""
    print("\n" + "=" * 70)
    print("🌡️  NLP2CMD Thermodynamic Computing Benchmarks")
    print("=" * 70)
    print("\nBased on Whitelam 2025 'Generative Thermodynamic Computing'")
    
    # 1. Raw Langevin sampler
    print("\n" + "-" * 70)
    print("1️⃣  Langevin Sampler Performance")
    print("-" * 70)
    
    for dim in [10, 20, 50]:
        result = benchmark_langevin_sampler(n_iterations=10, n_steps=200, dim=dim)
        print_benchmark_result(result)
    
    # 2. Parallel vs Sequential
    print("\n" + "-" * 70)
    print("2️⃣  Parallel vs Sequential Sampling")
    print("-" * 70)
    
    seq, par = benchmark_parallel_vs_sequential(n_samples=5, n_steps=100, dim=20)
    print_benchmark_result(seq)
    print_benchmark_result(par)
    print(f"\n  ⚡ Speedup: {par.extra['speedup']:.2f}x")
    
    # 3. Adaptive steps
    print("\n" + "-" * 70)
    print("3️⃣  Adaptive Steps Efficiency")
    print("-" * 70)
    
    adaptive_results = benchmark_adaptive_steps([2, 5, 10, 20, 50])
    print("\n  Problem Size → Step Reduction:")
    for r in adaptive_results:
        extra = r.extra
        reduction = extra["step_reduction_percent"]
        print(f"    {r.name}: {extra['fixed_steps']} → {extra['adaptive_steps']} steps ({reduction:.1f}% reduction)")
    
    # 4. Generator problems
    print("\n" + "-" * 70)
    print("4️⃣  ThermodynamicGenerator Problem Types")
    print("-" * 70)
    
    gen_results = await benchmark_generator_problems(n_iterations=5)
    for r in gen_results:
        print_benchmark_result(r)
    
    # 5. Energy savings
    print("\n" + "-" * 70)
    print("5️⃣  Energy Savings Estimation")
    print("-" * 70)
    
    energy_results = benchmark_energy_savings()
    print("\n  Scenario                   LLM Only    Hybrid(Digital)  Hybrid(Analog)   Savings")
    print("  " + "-" * 85)
    for r in energy_results:
        print(f"  {r['name']:<25} {r['llm_only_mJ']:>8.1f}mJ   {r['hybrid_digital_mJ']:>8.1f}mJ       {r['hybrid_analog_mJ']:>8.1f}mJ      {r['savings_digital_%']:.1f}%/{r['savings_analog_%']:.1f}%")
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 EFFICIENCY SUMMARY")
    print("=" * 70)
    
    avg_speedup = par.extra['speedup']
    avg_step_reduction = np.mean([r.extra['step_reduction_percent'] for r in adaptive_results])
    avg_energy_saving = np.mean([r['savings_digital_%'] for r in energy_results])
    
    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  Improvement                              Value                 │
  ├─────────────────────────────────────────────────────────────────┤
  │  Parallel sampling speedup:               {avg_speedup:.2f}x                  │
  │  Avg step reduction (adaptive):           {avg_step_reduction:.1f}%                 │
  │  Avg energy savings (digital):            {avg_energy_saving:.1f}%                 │
  │  Avg energy savings (analog, future):     {np.mean([r['savings_analog_%'] for r in energy_results]):.1f}%                 │
  └─────────────────────────────────────────────────────────────────┘
    """)
    
    print("✅ Benchmarks completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
