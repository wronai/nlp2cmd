"""Entity recognition helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from nlp2cmd.generation.regex import ExtractedEntity, RegexEntityExtractor


@dataclass
class RecognizedEntity:
    """Normalized entity extraction result."""

    name: str
    value: Any
    confidence: float = 1.0
    source: str = "regex"


class EntityRecognizer:
    """Entity recognizer backed by regex extraction."""

    def __init__(self, extractor: Optional[RegexEntityExtractor] = None) -> None:
        self.extractor = extractor or RegexEntityExtractor()

    def recognize(self, text: str, domain: str) -> list[RecognizedEntity]:
        """Extract entities for a given domain."""
        result = self.extractor.extract(text, domain)
        extracted = result.extracted or []
        return self._normalize(extracted, result.entities)

    def _normalize(
        self,
        extracted: Iterable[ExtractedEntity],
        entity_map: dict[str, Any],
    ) -> list[RecognizedEntity]:
        seen = set()
        normalized: list[RecognizedEntity] = []
        for entity in extracted:
            seen.add(entity.name)
            normalized.append(
                RecognizedEntity(
                    name=entity.name,
                    value=entity.value,
                    confidence=entity.confidence,
                    source="regex",
                )
            )

        for name, value in entity_map.items():
            if name in seen:
                continue
            normalized.append(RecognizedEntity(name=name, value=value, confidence=1.0))

        return normalized
