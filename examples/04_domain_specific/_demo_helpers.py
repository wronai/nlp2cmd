from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional

from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


def print_demo_header(title: str, *, leading_newline: bool = False) -> None:
    prefix = "\n" if leading_newline else ""
    print(f"{prefix}{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


async def run_thermo_demo(
    title: str,
    prompt: str,
    *,
    leading_newline: bool = False,
    **generate_kwargs,
):
    print_demo_header(title, leading_newline=leading_newline)
    thermo = ThermodynamicGenerator()
    return await thermo.generate(prompt, **generate_kwargs)


def print_metrics(
    result,
    *,
    energy: bool = False,
    converged: bool = False,
    solution_quality: bool = False,
    solution_feasible: bool = False,
    latency: bool = False,
    sampler_steps: bool = False,
    energy_estimate: bool = False,
    energy_estimate_label: str = "Energy savings",
) -> None:
    if energy:
        print(f"   Energy: {result.energy:.4f}")
    if converged:
        print(f"   Converged: {result.converged}")
    if solution_quality:
        print(f"   Solution quality: {result.solution_quality.explanation}")
    if solution_feasible:
        print(f"   Solution feasible: {result.solution_quality.is_feasible}")
    if latency:
        print(f"   Latency: {result.latency_ms:.1f}ms")
    if sampler_steps:
        print(f"   Sampler steps: {result.sampler_steps}")
    if energy_estimate:
        estimate = getattr(result, "energy_estimate", None)
        if estimate:
            savings = estimate.get("savings_digital_percent", 0)
            print(f"   {energy_estimate_label}: {savings:.1f}%")
        else:
            print(f"   {energy_estimate_label}: N/A")


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def project_sample(problem, raw_sample: List[float]) -> Dict[str, float]:
    if not raw_sample:
        return {}

    constraint_map = {
        c.get("var"): c
        for c in problem.constraints
        if c.get("type") == "range" and c.get("var")
    }

    projected: Dict[str, float] = {}
    for idx, var in enumerate(problem.variables):
        raw_value = raw_sample[idx] if idx < len(raw_sample) else 0.0
        constraint = constraint_map.get(var)
        if constraint and "min" in constraint and "max" in constraint:
            min_val = float(constraint["min"])
            max_val = float(constraint["max"])
            projected[var] = min_val + (max_val - min_val) * sigmoid(raw_value)
        else:
            projected[var] = raw_value

    return projected


def print_projected(
    title: str,
    projected: Dict[str, float],
    *,
    precision: int = 4,
    empty_message: Optional[str] = "(no projected values)",
) -> None:
    print(title)
    if not projected:
        if empty_message:
            print(f"  {empty_message}")
        return
    for key, value in projected.items():
        print(f"  {key}: {value:.{precision}f}")


def print_fallback_note(problem_name: str) -> None:
    print(
        f"\n⚠️  Uwaga: brak dedykowanego modelu energii dla '{problem_name}'. "
        "Wyniki bazują na surowej próbce (raw_sample) rzutowanej na zakresy."
    )
