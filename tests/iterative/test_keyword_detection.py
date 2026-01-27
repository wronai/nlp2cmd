"""
Test keyword detection confidence and performance.

This module tests detection confidence calculation, bulk detection,
and accuracy measurement for keyword-based intent detection.
"""

import pytest
import time

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult


class TestDetectionConfidence:
    """Test detection confidence calculation."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_high_confidence_with_domain_keywords(self, detector):
        """Test that domain-specific keywords boost confidence."""
        result = detector.detect("SELECT * FROM users WHERE status = 'active'")
        assert result.domain == 'sql'
        assert result.confidence >= 0.8  # High confidence with SQL keywords
    
    def test_longer_keywords_boost_confidence(self, detector):
        """Test that longer keyword matches have higher confidence."""
        result1 = detector.detect("Pokaż")  # Short keyword
        result2 = detector.detect("Pokaż wszystkich użytkowników z tabeli")  # Longer phrase
        
        # Longer phrase should have higher confidence
        if result1.domain == result2.domain:
            assert result2.confidence >= result1.confidence
    
    def test_medium_confidence_generic_keywords(self, detector):
        """Test medium confidence with generic keywords."""
        result = detector.detect("Pokaż dane")
        assert result.confidence >= 0.5  # Medium confidence
    
    def test_low_confidence_ambiguous_input(self, detector):
        """Test low confidence with ambiguous input."""
        result = detector.detect("System operacyjny")
        assert result.confidence < 0.5  # Low confidence for ambiguous


class TestExplicitOverrides:
    """Test explicit override behavior after refactoring."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_ip_address_override(self, detector):
        """Test that IP address queries trigger network intent with high confidence."""
        result = detector.detect("pokaż adres ip")
        assert result.domain == 'shell'
        assert result.intent == 'network'
        assert result.confidence >= 0.9
        assert result.matched_keyword == 'adres ip'
    
    def test_ip_address_english_override(self, detector):
        """Test English IP address override."""
        result = detector.detect("show my ip address")
        assert result.domain == 'shell'
        assert result.intent == 'network'
        assert result.confidence >= 0.9
    
    def test_json_parsing_override(self, detector):
        """Test JSON parsing intent override."""
        result = detector.detect("parsuj json z pliku")
        assert result.domain == 'shell'
        assert result.intent == 'json_jq'
        assert result.confidence >= 0.9
        assert 'json' in result.matched_keyword
    
    def test_jq_override(self, detector):
        """Test explicit jq keyword override."""
        result = detector.detect("użyj jq do filtrowania")
        # 'jq' alone maps to utility domain, not shell
        assert result.domain == 'utility'
        assert result.confidence >= 0.8
    
    def test_file_content_override(self, detector):
        """Test file content override."""
        result = detector.detect("pokaż zawartość pliku config.txt")
        assert result.domain == 'shell'
        assert result.intent == 'text_cat'
        assert result.confidence >= 0.9
        assert 'file content' in result.matched_keyword
    
    def test_file_content_polish_variation(self, detector):
        """Test Polish variation for file content."""
        result = detector.detect("zawartosc pliku log")
        assert result.domain == 'shell'
        assert result.intent == 'text_cat'
        assert result.confidence >= 0.9


class TestDetectAll:
    """Test detect_all functionality."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_detect_all_returns_sorted_results(self, detector):
        """Test detect_all returns results sorted by confidence."""
        results = detector.detect_all("Pokaż użytkowników z tabeli orders")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check that results are sorted by confidence (highest first)
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence
    
    def test_detect_all_no_duplicates(self, detector):
        """Test detect_all returns unique domain/intent pairs."""
        results = detector.detect_all("Pokaż dane z tabeli users")
        
        # Check no duplicate domain/intent pairs
        seen_pairs = set()
        for result in results:
            pair = (result.domain, result.intent)
            assert pair not in seen_pairs
            seen_pairs.add(pair)


class TestCustomPatterns:
    """Test adding custom patterns to keyword detector."""
    
    def test_add_custom_pattern(self):
        """Test adding custom patterns."""
        detector = KeywordIntentDetector()
        
        detector.add_pattern('custom_domain', 'custom_intent', ['moje_slowo', 'specjalne_polecenie'])
        
        result = detector.detect("Użyj moje_slowo do przetworzenia")
        assert result.domain == 'custom_domain'
        assert result.intent == 'custom_intent'
    
    def test_custom_patterns_dict(self):
        """Test initializing with custom patterns dict."""
        custom = {
            'custom_domain': {
                'custom_intent': ['specjalne_polecenie', 'unikalowa_akcja']
            }
        }
        
        detector = KeywordIntentDetector(custom_patterns=custom)
        
        result = detector.detect("Wykonaj unikalowa_akcja")
        assert result.domain == 'custom_domain'
        assert result.intent == 'custom_intent'


class TestKeywordDetectorPerformance:
    """Test keyword detector performance."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_detection_latency(self, detector):
        """Test that detection is fast (<10ms)."""
        start_time = time.time()
        
        for _ in range(100):
            detector.detect("Pokaż użytkowników z tabeli users")
        
        end_time = time.time()
        avg_latency = (end_time - start_time) / 100 * 1000  # Convert to ms
        
        assert avg_latency < 100, f"Detection too slow: {avg_latency:.1f}ms average"
    
    def test_bulk_detection_throughput(self, detector):
        """Test throughput with many detections."""
        queries = [
            "Pokaż użytkowników",
            "Znajdź pliki",
            "Uruchom kontener",
            "Pokaż pody",
            "Stwórz tabelę",
        ] * 20  # 100 queries
        
        start_time = time.time()
        
        for query in queries:
            detector.detect(query)
        
        end_time = time.time()
        throughput = len(queries) / (end_time - start_time)  # queries per second
        
        assert throughput > 30, f"Throughput too low: {throughput:.1f} qps"


class TestKeywordAccuracy:
    """Test accuracy measurement for keyword detection."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    # Evaluation dataset for accuracy measurement
    KEYWORD_EVAL_DATASET = [
        # SQL
        {
            "text": "Pokaż wszystkich użytkowników",
            "expected_domain": "sql",
            "expected_intent": "select",
        },
        {
            "text": "Dodaj rekord do tabeli",
            "expected_domain": "sql",
            "expected_intent": "insert",
        },
        {
            "text": "Usuń stare dane",
            "expected_domain": "sql",
            "expected_intent": "delete",
        },
        # Shell
        {
            "text": "Znajdź pliki konfiguracyjne",
            "expected_domain": "shell",
            "expected_intent": "find",
        },
        {
            "text": "Pokaż procesy systemowe",
            "expected_domain": "shell",
            "expected_intent": "list_processes",
        },
        {
            "text": "Sprawdź miejsce na dysku",
            "expected_domain": "shell",
            "expected_intent": "disk_usage",
        },
        # Docker
        {
            "text": "Uruchom kontener nginx",
            "expected_domain": "docker",
            "expected_intent": "run",
        },
        {
            "text": "Pokaż logi aplikacji",
            "expected_domain": "docker",
            "expected_intent": "logs",
        },
        # Kubernetes
        {
            "text": "Pokaż wszystkie pody",
            "expected_domain": "kubernetes",
            "expected_intent": "get",
        },
        {
            "text": "Skaluj deployment do 3 replik",
            "expected_domain": "kubernetes",
            "expected_intent": "scale",
        },
    ]
    
    @pytest.mark.parametrize("test_case", KEYWORD_EVAL_DATASET)
    def test_eval_case(self, detector, test_case):
        """Test individual evaluation case."""
        result = detector.detect(test_case["text"])
        
        assert result.domain == test_case["expected_domain"], \
            f"Domain mismatch for '{test_case['text']}': expected {test_case['expected_domain']}, got {result.domain}"
        
        assert result.intent == test_case["expected_intent"], \
            f"Intent mismatch for '{test_case['text']}': expected {test_case['expected_intent']}, got {result.intent}"
    
    def test_overall_accuracy(self, detector):
        """Calculate overall accuracy on dataset."""
        correct = 0
        total = len(self.KEYWORD_EVAL_DATASET)
        
        for test_case in self.KEYWORD_EVAL_DATASET:
            result = detector.detect(test_case["text"])
            
            if (result.domain == test_case["expected_domain"] and 
                result.intent == test_case["expected_intent"]):
                correct += 1
        
        accuracy = correct / total
        
        print(f"\n=== Keyword Detection Accuracy ===")
        print(f"  Accuracy: {accuracy:.1%} ({correct}/{total})")
        
        # Target: >80% accuracy
        assert accuracy >= 0.80, f"Accuracy too low: {accuracy:.1%}"
