"""
Drug Discovery - Optymalizacja cząsteczek i profilu ADMET.

Demonstruje użycie NLP2CMD do wielokryterialnej optymalizacji
w procesie odkrywania leków (lead optimization).
"""

import asyncio
import math
from typing import Dict, List

from nlp2cmd.generation.thermodynamic import (
    OptimizationProblem,
    ThermodynamicGenerator,
)


def _sigmoid(value: float) -> float:
    """Map raw sample value to [0, 1]."""
    return 1.0 / (1.0 + math.exp(-value))


def _project_sample(
    problem: OptimizationProblem,
    raw_sample: List[float],
) -> Dict[str, float]:
    """Project raw Langevin samples into variable ranges (heuristic)."""
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
            projected[var] = min_val + (max_val - min_val) * _sigmoid(raw_value)
        else:
            projected[var] = raw_value

    return projected


def _print_projected(title: str, projected: Dict[str, float]) -> None:
    print(title)
    for key, value in projected.items():
        print(f"   {key}: {value:.3f}")


def _print_fallback_note() -> None:
    print(
        "\n⚠️  Uwaga: brak dedykowanego modelu energii dla 'drug_discovery'. "
        "Wyniki bazują na surowej próbce (raw_sample) rzutowanej na zakresy."
    )


async def demo_lead_optimization() -> None:
    """Optymalizacja leadu z ograniczeniami fizykochemicznymi."""
    print("=" * 70)
    print("  Drug Discovery - Lead Optimization")
    print("=" * 70)

    thermo = ThermodynamicGenerator()

    problem = OptimizationProblem(
        problem_type="drug_discovery",
        variables=[
            "molecular_weight",
            "logP",
            "tpsa",
            "hbd",
            "hba",
            "rotatable_bonds",
        ],
        constraints=[
            {"type": "range", "var": "molecular_weight", "min": 250, "max": 450},
            {"type": "range", "var": "logP", "min": 1.5, "max": 3.5},
            {"type": "range", "var": "tpsa", "min": 40, "max": 90},
            {"type": "range", "var": "hbd", "min": 0, "max": 3},
            {"type": "range", "var": "hba", "min": 2, "max": 8},
            {"type": "range", "var": "rotatable_bonds", "min": 0, "max": 6},
        ],
        objective="maximize",
        objective_field="binding_affinity",
    )

    result = await thermo.generate(
        "Zoptymalizuj lead: wysokie powinowactwo do celu, dobry profil ADMET.",
        problem=problem,
    )

    raw_sample = result.solution.get("raw_sample", [])
    projected = _project_sample(problem, raw_sample)

    print(result.decoded_output)
    _print_projected("\n🔬 Projected physicochemical profile:", projected)
    print(f"\n   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    _print_fallback_note()


async def demo_admet_balancing() -> None:
    """Wielokryterialna optymalizacja ADMET."""
    print("\n" + "=" * 70)
    print("  Drug Discovery - ADMET Balancing")
    print("=" * 70)

    thermo = ThermodynamicGenerator()

    problem = OptimizationProblem(
        problem_type="drug_discovery",
        variables=[
            "solubility",
            "clearance",
            "toxicity_score",
            "bioavailability",
            "cyp_inhibition",
        ],
        constraints=[
            {"type": "range", "var": "solubility", "min": 0.2, "max": 1.0},
            {"type": "range", "var": "clearance", "min": 0.1, "max": 0.8},
            {"type": "range", "var": "toxicity_score", "min": 0.0, "max": 0.3},
            {"type": "range", "var": "bioavailability", "min": 0.4, "max": 0.9},
            {"type": "range", "var": "cyp_inhibition", "min": 0.0, "max": 0.4},
        ],
        objective="maximize",
        objective_field="admet_score",
    )

    result = await thermo.generate(
        "Zbalansuj ADMET: wysoka biodostępność, niska toksyczność, stabilność metaboliczna.",
        problem=problem,
    )

    raw_sample = result.solution.get("raw_sample", [])
    projected = _project_sample(problem, raw_sample)

    print(result.decoded_output)
    _print_projected("\n🧪 Projected ADMET profile:", projected)
    print(f"\n   Energy: {result.energy:.4f}")
    print(f"   Latency: {result.latency_ms:.1f}ms")
    _print_fallback_note()


async def main() -> None:
    """Uruchom demonstracje Drug Discovery."""
    await demo_lead_optimization()
    await demo_admet_balancing()

    print("\n" + "=" * 70)
    print("  Drug Discovery demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
