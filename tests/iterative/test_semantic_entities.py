"""
Tests for the SemanticEntityExtractor scaffolding and feature flags.
"""

from __future__ import annotations

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor
from nlp2cmd.generation.semantic_entities import SemanticEntityExtractor

SAMPLE_TEXT = "Find *.py files in /home/user"
SAMPLE_DOMAIN = "shell"


def _regex_entities(text: str = SAMPLE_TEXT, domain: str = SAMPLE_DOMAIN) -> dict[str, object]:
    return RegexEntityExtractor().extract(text, domain).entities


def test_semantic_extractor_defaults_to_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", raising=False)
    monkeypatch.delenv("NLP2CMD_ENTITY_AB_RATIO", raising=False)

    extractor = SemanticEntityExtractor()
    result = extractor.extract(SAMPLE_TEXT, SAMPLE_DOMAIN)

    assert result.entities == _regex_entities()
    assert extractor.last_mode == "regex"
    assert extractor.last_semantic_entities is None


def test_semantic_extractor_shadow_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", "shadow")
    monkeypatch.delenv("NLP2CMD_ENTITY_AB_RATIO", raising=False)

    extractor = SemanticEntityExtractor()
    result = extractor.extract(SAMPLE_TEXT, SAMPLE_DOMAIN)

    assert result.entities == _regex_entities()
    assert extractor.last_mode == "shadow"
    assert extractor.last_semantic_entities == {}


@pytest.mark.parametrize(
    ("ratio", "expected_mode"),
    [
        ("1", "semantic"),
        ("0", "regex"),
    ],
)
def test_semantic_extractor_ab_mode(
    monkeypatch: pytest.MonkeyPatch,
    ratio: str,
    expected_mode: str,
) -> None:
    monkeypatch.setenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", "ab")
    monkeypatch.setenv("NLP2CMD_ENTITY_AB_RATIO", ratio)

    extractor = SemanticEntityExtractor()
    result = extractor.extract(SAMPLE_TEXT, SAMPLE_DOMAIN)

    assert result.entities == _regex_entities()
    assert extractor.last_mode == expected_mode
    if expected_mode == "regex":
        assert extractor.last_semantic_entities is None
    else:
        assert extractor.last_semantic_entities == {}
