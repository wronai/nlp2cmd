from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass
class _FakeExtractionResult:
    entities: dict


def test_semantic_shell_shadow_mode_sets_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    from nlp2cmd.generation import semantic_entities as sem_mod
    from nlp2cmd.nlp_light.semantic_shell import SemanticShellBackend

    class FakeSemanticEntityExtractor:
        def __init__(self):
            self.last_mode = "regex"
            self.last_semantic_entities = None

        def extract(self, text: str, domain: str):
            self.last_mode = "shadow"
            self.last_semantic_entities = {"semantic_only": "x"}
            return _FakeExtractionResult(entities={"semantic_only": "x"})

    monkeypatch.setattr(sem_mod, "SemanticEntityExtractor", FakeSemanticEntityExtractor)

    backend = SemanticShellBackend(config={"dsl": "shell"})
    plan = backend.generate_plan("Znajdź pliki *.py")

    assert plan.metadata.get("entity_extractor_mode") == "shadow"
    assert plan.metadata.get("shadow_entities") == {"semantic_only": "x"}
    assert "semantic_only" not in plan.entities


def test_semantic_shell_semantic_mode_merges_entities(monkeypatch: pytest.MonkeyPatch) -> None:
    from nlp2cmd.generation import semantic_entities as sem_mod
    from nlp2cmd.nlp_light.semantic_shell import SemanticShellBackend

    class FakeSemanticEntityExtractor:
        def __init__(self):
            self.last_mode = "regex"
            self.last_semantic_entities = None

        def extract(self, text: str, domain: str):
            self.last_mode = "semantic"
            self.last_semantic_entities = {"semantic_only": "x"}
            return _FakeExtractionResult(entities={"semantic_only": "x"})

    monkeypatch.setattr(sem_mod, "SemanticEntityExtractor", FakeSemanticEntityExtractor)

    backend = SemanticShellBackend(config={"dsl": "shell"})
    plan = backend.generate_plan("Znajdź pliki *.py")

    assert plan.metadata.get("entity_extractor_mode") == "semantic"
    assert "shadow_entities" not in plan.metadata
    assert plan.entities.get("semantic_only") == "x"
