"""
Test accuracy measurement for regex entity extraction.

This module contains evaluation datasets and accuracy measurement
tests to ensure the regex patterns perform adequately.
"""

import json
from pathlib import Path

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult
from nlp2cmd.generation.semantic_entities import SemanticEntityExtractor


_EVAL_DATASET_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "entity_extraction_eval.json"
EVAL_DATASET = json.loads(_EVAL_DATASET_PATH.read_text(encoding="utf-8"))


def _assert_expected_entities(result: ExtractionResult, test_case: dict) -> None:
    if "expected" in test_case:
        for key, value in test_case["expected"].items():
            actual = result.entities.get(key)
            assert actual == value or value in str(actual), (
                f"Entity '{key}' mismatch for '{test_case['text']}': expected {value}, got {actual}"
            )

    if "expected_contains" in test_case:
        for key, value in test_case["expected_contains"].items():
            actual = str(result.entities.get(key, ""))
            assert value in actual, (
                f"Entity '{key}' should contain '{value}' for '{test_case['text']}': got {actual}"
            )


def _calculate_extraction_rate(extractor, dataset: list[dict]) -> tuple[int, int]:
    total_expected = 0
    total_extracted = 0

    for test_case in dataset:
        result = extractor.extract(test_case["text"], test_case["domain"])

        expected = test_case.get("expected", test_case.get("expected_contains", {}))
        for key, value in expected.items():
            total_expected += 1
            actual = str(result.entities.get(key, ""))
            if value in actual or actual == value:
                total_extracted += 1

    return total_extracted, total_expected


class TestRegexAccuracy:
    """Measure accuracy on evaluation dataset."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    @pytest.mark.parametrize("test_case", EVAL_DATASET)
    def test_eval_case(self, extractor, test_case):
        """Test individual evaluation case."""
        result = extractor.extract(test_case["text"], test_case["domain"])

        _assert_expected_entities(result, test_case)
    
    def test_overall_extraction_rate(self, extractor):
        """Calculate overall entity extraction rate."""
        total_extracted, total_expected = _calculate_extraction_rate(extractor, EVAL_DATASET)
        extraction_rate = total_extracted / total_expected if total_expected > 0 else 0
        
        print(f"\n=== Regex Extraction Accuracy ===")
        print(f"  Extraction rate: {extraction_rate:.1%} ({total_extracted}/{total_expected})")
        
        # Target: >60% extraction rate
        assert extraction_rate >= 0.60, f"Extraction rate too low: {extraction_rate:.1%}"


class TestSemanticAccuracy:
    """Measure accuracy for semantic entity extraction."""

    @pytest.fixture
    def extractor(self, monkeypatch: pytest.MonkeyPatch) -> SemanticEntityExtractor:
        monkeypatch.setenv("NLP2CMD_ENTITY_EXTRACTOR_MODE", "semantic")
        monkeypatch.delenv("NLP2CMD_ENTITY_AB_RATIO", raising=False)
        return SemanticEntityExtractor()

    @pytest.mark.parametrize("test_case", EVAL_DATASET)
    def test_eval_case(self, extractor, test_case):
        """Test individual evaluation case."""
        result = extractor.extract(test_case["text"], test_case["domain"])

        _assert_expected_entities(result, test_case)

    def test_overall_extraction_rate(self, extractor):
        """Calculate overall entity extraction rate."""
        total_extracted, total_expected = _calculate_extraction_rate(extractor, EVAL_DATASET)
        extraction_rate = total_extracted / total_expected if total_expected > 0 else 0

        print(f"\n=== Semantic Extraction Accuracy ===")
        print(f"  Extraction rate: {extraction_rate:.1%} ({total_extracted}/{total_expected})")

        # Target: parity with regex baseline
        assert extraction_rate >= 0.60, f"Extraction rate too low: {extraction_rate:.1%}"
