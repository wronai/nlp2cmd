"""Integration tests for Polish language queries."""

from __future__ import annotations

from nlp2cmd.generation.pipeline import RuleBasedPipeline


def test_polish_file_content_query() -> None:
    """Ensure Polish file content queries map to cat commands."""
    pipeline = RuleBasedPipeline()
    result = pipeline.process("pokaż zawartość pliku config.txt")

    assert "cat" in result.command
    assert "config.txt" in result.command


def test_polish_json_query() -> None:
    """Ensure Polish JSON parsing queries map to jq commands."""
    pipeline = RuleBasedPipeline()
    result = pipeline.process("parsuj json z pliku data.json")

    assert "jq" in result.command
    assert "data.json" in result.command
