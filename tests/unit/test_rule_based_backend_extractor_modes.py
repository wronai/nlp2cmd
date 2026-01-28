from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass
class _FakeExtractionResult:
    entities: dict


def test_rule_based_backend_defaults_to_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", raising=False)

    from nlp2cmd.core import RuleBasedBackend

    backend = RuleBasedBackend(rules={}, config={"dsl": "shell"})
    entities = backend.extract_entities("Znajdź pliki *.py")

    assert isinstance(entities, list)
    assert all(hasattr(e, "name") and hasattr(e, "value") for e in entities)


def test_rule_based_backend_uses_semantic_extractor_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", "semantic")

    from nlp2cmd import core as core_mod
    from nlp2cmd.generation import semantic_entities as sem_mod

    called = {"used": False}

    class FakeSemanticEntityExtractor:
        def __init__(self):
            self.last_mode = "semantic"
            self.last_semantic_entities = {"semantic_only": "x"}

        def extract(self, text: str, domain: str):
            called["used"] = True
            return _FakeExtractionResult(entities={"semantic_only": "x"})

    monkeypatch.setattr(sem_mod, "SemanticEntityExtractor", FakeSemanticEntityExtractor)

    backend = core_mod.RuleBasedBackend(rules={}, config={"dsl": "shell"})
    entities = backend.extract_entities("Znajdź pliki *.py")

    assert called["used"] is True
    assert any(e.name == "semantic_only" and e.value == "x" for e in entities)
