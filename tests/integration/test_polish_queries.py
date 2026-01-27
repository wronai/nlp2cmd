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


def test_polish_multi_sentence_shell_steps() -> None:
    """Ensure multi-sentence shell queries return multiple steps."""
    pipeline = RuleBasedPipeline()
    results = pipeline.process_steps("Pokaż pliki. Pokaż procesy.")

    assert len(results) >= 2
    commands = [res.command for res in results]
    assert any("ls" in cmd or "dir" in cmd for cmd in commands)
    assert any("ps" in cmd for cmd in commands)


def test_polish_multi_sentence_mixed_domains() -> None:
    """Ensure mixed-domain multi-sentence inputs are handled stepwise."""
    pipeline = RuleBasedPipeline()
    results = pipeline.process_steps("Pokaż kontenery. Pokaż pliki.")

    assert len(results) >= 2
    commands = [res.command for res in results]
    assert any("docker ps" in cmd for cmd in commands)
    assert any("ls" in cmd or "dir" in cmd for cmd in commands)


def test_polish_multi_sentence_user_list() -> None:
    """Ensure user list and process queries split into multiple steps."""
    pipeline = RuleBasedPipeline()
    results = pipeline.process_steps("Pokaż userów systemu. Pokaż procesy.")

    assert len(results) >= 2
    commands = [res.command for res in results]
    assert any("/etc/passwd" in cmd for cmd in commands)
    assert any("ps" in cmd for cmd in commands)
