"""
Test accuracy measurement for regex entity extraction.

This module contains evaluation datasets and accuracy measurement
tests to ensure the regex patterns perform adequately.
"""

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult


# Evaluation dataset for accuracy measurement
REGEX_EVAL_DATASET = [
    # SQL
    {
        "text": "Pokaż dane z tabeli users",
        "domain": "sql",
        "expected": {"table": "users"},
    },
    {
        "text": "Select from orders where status = active",
        "domain": "sql",
        "expected": {"table": "orders"},
    },
    {
        "text": "Pokaż 10 rekordów z tabeli products",
        "domain": "sql",
        "expected": {"table": "products", "limit": "10"},
    },
    # Shell
    {
        "text": "Znajdź pliki .py w katalogu /home/user",
        "domain": "shell",
        "expected_contains": {"path": "/home/user"},
    },
    {
        "text": "pliki większe niż 100MB",
        "domain": "shell",
        "expected_contains": {"size": "100"},
    },
    # Docker
    {
        "text": "logi kontenera webapp na porcie 8080",
        "domain": "docker",
        "expected": {"container": "webapp"},
    },
    # Kubernetes
    {
        "text": "pody w namespace production",
        "domain": "kubernetes",
        "expected": {"namespace": "production"},
    },
    {
        "text": "skaluj do 3 replik",
        "domain": "kubernetes",
        "expected": {"replica_count": "3"},
    },
]


class TestRegexAccuracy:
    """Measure accuracy on evaluation dataset."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    @pytest.mark.parametrize("test_case", REGEX_EVAL_DATASET)
    def test_eval_case(self, extractor, test_case):
        """Test individual evaluation case."""
        result = extractor.extract(test_case["text"], test_case["domain"])
        
        if "expected" in test_case:
            for key, value in test_case["expected"].items():
                actual = result.entities.get(key)
                assert actual == value or value in str(actual), \
                    f"Entity '{key}' mismatch for '{test_case['text']}': expected {value}, got {actual}"
        
        if "expected_contains" in test_case:
            for key, value in test_case["expected_contains"].items():
                actual = str(result.entities.get(key, ''))
                assert value in actual, \
                    f"Entity '{key}' should contain '{value}' for '{test_case['text']}': got {actual}"
    
    def test_overall_extraction_rate(self, extractor):
        """Calculate overall entity extraction rate."""
        total_expected = 0
        total_extracted = 0
        
        for test_case in REGEX_EVAL_DATASET:
            result = extractor.extract(test_case["text"], test_case["domain"])
            
            expected = test_case.get("expected", test_case.get("expected_contains", {}))
            for key, value in expected.items():
                total_expected += 1
                actual = str(result.entities.get(key, ''))
                if value in actual or actual == value:
                    total_extracted += 1
        
        extraction_rate = total_extracted / total_expected if total_expected > 0 else 0
        
        print(f"\n=== Regex Extraction Accuracy ===")
        print(f"  Extraction rate: {extraction_rate:.1%} ({total_extracted}/{total_expected})")
        
        # Target: >60% extraction rate
        assert extraction_rate >= 0.60, f"Extraction rate too low: {extraction_rate:.1%}"
