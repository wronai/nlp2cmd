from __future__ import annotations

import os
import random
from typing import Any, Optional

from nlp2cmd.generation.regex import ExtractionResult, RegexEntityExtractor


_ALLOWED_MODES = {"regex", "semantic", "shadow", "ab"}


def _normalize_mode(value: Optional[str]) -> str:
    if not value:
        return "regex"
    mode = value.strip().lower()
    return mode if mode in _ALLOWED_MODES else "regex"


def _parse_ab_ratio(value: Optional[str]) -> float:
    if not value:
        return 0.1
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        return 0.1
    if ratio < 0.0:
        return 0.0
    if ratio > 1.0:
        return 1.0
    return ratio


class SemanticEntityExtractor:
    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        regex_extractor: Optional[RegexEntityExtractor] = None,
    ):
        self.config = config or {}
        self._regex_extractor = regex_extractor or RegexEntityExtractor()
        self._mode = _normalize_mode(os.environ.get("NLP2CMD_ENTITY_EXTRACTOR_MODE"))
        self._ab_ratio = _parse_ab_ratio(os.environ.get("NLP2CMD_ENTITY_AB_RATIO"))
        self.last_mode = self._mode
        self.last_semantic_entities: Optional[dict[str, Any]] = None

    @property
    def mode(self) -> str:
        return self._mode

    def extract(self, text: str, domain: str) -> ExtractionResult:
        regex_result = self._regex_extractor.extract(text, domain)
        active_mode = self._select_mode()
        self.last_mode = active_mode

        if active_mode == "regex":
            self.last_semantic_entities = None
            return regex_result

        semantic_entities = self._extract_semantic(text, domain)
        self.last_semantic_entities = semantic_entities

        if active_mode == "shadow":
            return regex_result

        if semantic_entities:
            merged = self._merge_entities(regex_result.entities, semantic_entities)
            return ExtractionResult(
                entities=merged,
                extracted=regex_result.extracted,
                raw_text=regex_result.raw_text,
            )

        return regex_result

    def _select_mode(self) -> str:
        if self._mode == "ab":
            return "semantic" if random.random() < self._ab_ratio else "regex"
        return self._mode

    def _extract_semantic(self, text: str, domain: str) -> dict[str, Any]:
        _ = text
        _ = domain
        return {}

    @staticmethod
    def _merge_entities(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in extra.items():
            if key == "filters" and isinstance(value, list):
                existing = merged.get("filters")
                if isinstance(existing, list):
                    merged["filters"] = existing + [item for item in value if item not in existing]
                    continue
            if key not in merged or merged[key] in {None, "", [], {}}:
                merged[key] = value
        return merged
