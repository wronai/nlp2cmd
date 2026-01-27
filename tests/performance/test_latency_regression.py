"""Latency regression tests for core NLP2CMD flows."""

from __future__ import annotations

import time

import pytest

from nlp2cmd import NLP2CMD, ShellAdapter
from nlp2cmd.core import RuleBasedBackend


@pytest.mark.slow
def test_shell_transform_latency_regression() -> None:
    """Ensure shell transforms remain within reasonable latency bounds."""
    adapter = ShellAdapter()
    rules = {name: list(config.get("patterns", [])) for name, config in adapter.INTENTS.items()}
    backend = RuleBasedBackend(rules=rules, config={"dsl": adapter.DSL_NAME})
    nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

    queries = [
        "Znajdź pliki *.log",
        "Pokaż procesy",
        "Policz linie w pliku app.log",
        "Pokaż zawartość pliku config.txt",
        "Wyświetl katalogi w bieżącym katalogu",
        "Pokaż użycie dysku",
    ]

    # Warm-up to avoid cold-start skew.
    nlp.transform(queries[0])

    start = time.perf_counter()
    for query in queries:
        result = nlp.transform(query)
        assert result.command
    elapsed = time.perf_counter() - start

    avg_ms = (elapsed / len(queries)) * 1000
    assert avg_ms < 500, f"Shell transform latency regression: {avg_ms:.1f}ms average"
