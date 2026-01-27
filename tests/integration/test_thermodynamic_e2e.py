"""End-to-end tests for thermodynamic optimization pipeline."""

from __future__ import annotations

import pytest

from nlp2cmd.generation.thermodynamic import create_thermodynamic_generator


@pytest.mark.asyncio
async def test_thermodynamic_schedule_end_to_end() -> None:
    """Ensure thermodynamic generator solves a basic scheduling problem."""
    pytest.importorskip("numpy")

    generator = create_thermodynamic_generator(n_samples=2, n_steps=80, adaptive_steps=True)
    result = await generator.generate("Zaplanuj 3 zadania w 5 slotach")

    assert result.problem.problem_type == "schedule"
    assert result.solution
    assert result.decoded_output is not None
    assert result.latency_ms >= 0
