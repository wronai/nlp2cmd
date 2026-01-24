from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Optional

from nlp2cmd.core import NLPBackend, ExecutionPlan


@dataclass
class _ParsedSize:
    value: float
    unit: str


class SemanticShellBackend(NLPBackend):
    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        self.model = os.environ.get("NLP2CMD_SPACY_MODEL") or "blank:pl"
        self._nlp = None

    def _maybe_warm_spacy(self) -> None:
        if self._nlp is not None:
            return

        try:
            import spacy

            if self.model.startswith("blank:"):
                lang = self.model.split(":", 1)[1] or "pl"
                nlp = spacy.blank(lang)
            else:
                nlp = spacy.load(self.model)

            if "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")

            self._nlp = nlp
        except Exception:
            self._nlp = None

    def extract_intent(self, text: str) -> tuple[str, float]:
        text_lower = (text or "").lower()
        if any(x in text_lower for x in ("znajd", "find", "szuk")):
            return "file_search", 0.75
        if any(x in text_lower for x in ("pokaż", "pokaz", "list", "wyświetl", "wyswietl")):
            return "file_search", 0.55
        return "unknown", 0.0

    def extract_entities(self, text: str) -> list[Any]:
        raise NotImplementedError

    def generate_plan(self, text: str, context: Optional[dict] = None) -> ExecutionPlan:
        # Optional warmup: does not affect logic if spaCy isn't installed.
        self._maybe_warm_spacy()
        text_lower = (text or "").lower()

        entities: dict[str, Any] = {}
        entities["scope"] = self._extract_scope(text)
        entities["target"] = self._infer_target(text_lower)

        filters: list[dict[str, Any]] = []

        ext = self._extract_extension(text)
        if ext:
            filters.append({"attribute": "extension", "operator": "=", "value": ext})

        size_filter = self._extract_size_filter(text_lower)
        if size_filter is not None:
            filters.append(size_filter)

        age_filter = self._extract_age_filter(text_lower)
        if age_filter is not None:
            filters.append(age_filter)

        entities["filters"] = filters

        confidence = 0.45
        if size_filter is not None or age_filter is not None:
            confidence = 0.8
        if ext:
            confidence = max(confidence, 0.7)

        return ExecutionPlan(
            intent="file_search",
            entities=entities,
            confidence=confidence,
            text=text or "",
            metadata={"backend": "semantic_shell_light", "spacy_model": self.model},
        )

    @staticmethod
    def _infer_target(text_lower: str) -> str:
        if any(x in text_lower for x in ("katalog", "folder", "directory", "directories")):
            return "directories"
        return "files"

    @staticmethod
    def _extract_scope(text: str) -> str:
        if not text:
            return "."

        m = re.search(r"\b(?:w|in|from)\s+([/~][\w\./\-]+|\./[\w\./\-]*|\.\./[\w\./\-]*|\.{1,2})\b", text)
        if m:
            return m.group(1)

        return "."

    @staticmethod
    def _extract_extension(text: str) -> Optional[str]:
        if not text:
            return None

        m = re.search(r"\*\.(\w{1,16})\b", text)
        if m:
            return m.group(1).lower()

        m = re.search(r"\.(\w{1,16})\b", text)
        if m:
            return m.group(1).lower()

        text_lower = text.lower()
        if "logi" in text_lower or "logs" in text_lower:
            return "log"

        return None

    @classmethod
    def _extract_size_filter(cls, text_lower: str) -> Optional[dict[str, Any]]:
        parsed = cls._extract_first_size(text_lower)
        if parsed is None:
            return None

        op = cls._infer_size_operator(text_lower)
        value = cls._format_size_for_find(parsed)

        return {"attribute": "size", "operator": op, "value": value}

    @staticmethod
    def _infer_size_operator(text_lower: str) -> str:
        if re.search(r"\bnie\s+mniejsz\w*\b", text_lower):
            return ">="
        if re.search(r"\bnie\s+większ\w*\b", text_lower) or re.search(r"\bnie\s+duż\w*\b", text_lower):
            return "<="
        if any(x in text_lower for x in ("mniejsz", "poniżej", "ponizej")):
            return "<"
        if re.search(r"\bdo\b", text_lower) and re.search(r"\d", text_lower):
            return "<="
        if any(x in text_lower for x in ("większ", "wieksz", "powyżej", "powyzej", "ponad", "duż", "duz")):
            return ">"
        return ">"

    @classmethod
    def _extract_age_filter(cls, text_lower: str) -> Optional[dict[str, Any]]:
        m = re.search(
            r"\b(starsz\w*|nowsz\w*|ostatnio\s+zmienion\w*)\b.*?(\d+)\s*(dni|dnia|dzie[nń]|days?)\b",
            text_lower,
        )
        if not m:
            return None

        kind = m.group(1)
        days = int(m.group(2))

        if kind.startswith("nowsz"):
            op = "<="
        elif kind.startswith("ostatnio"):
            op = "<="
        else:
            op = ">="

        return {"attribute": "mtime", "operator": op, "value": f"{days}_days"}

    @staticmethod
    def _extract_first_size(text_lower: str) -> Optional[_ParsedSize]:
        m = re.search(r"(\d+(?:[\.,]\d+)?)\s*([kmgt]?b)\b", text_lower)
        if not m:
            return None

        val_raw = m.group(1).replace(",", ".")
        try:
            value = float(val_raw)
        except ValueError:
            return None

        unit = m.group(2).upper()
        return _ParsedSize(value=value, unit=unit)

    @staticmethod
    def _format_size_for_find(size: _ParsedSize) -> str:
        # GNU find expects: c (bytes), k (KiB), M/G/T (MiB/GiB/TiB)
        unit_upper = (size.unit or "").upper()
        if unit_upper in {"KB", "K"}:
            unit_letter = "k"
        elif unit_upper in {"MB", "M"}:
            unit_letter = "M"
        elif unit_upper in {"GB", "G"}:
            unit_letter = "G"
        elif unit_upper in {"TB", "T"}:
            unit_letter = "T"
        elif unit_upper in {"B", "BYTE", "BYTES"}:
            unit_letter = "c"
        else:
            unit_letter = "M"

        value_int = int(size.value) if float(size.value).is_integer() else int(round(size.value))
        return f"{value_int}{unit_letter}"
