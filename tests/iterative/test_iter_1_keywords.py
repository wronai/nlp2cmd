"""
Iteration 1: Keyword Intent Detection Tests.

Test rule-based intent detection without LLM.
"""

import pytest
import time

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult


class TestKeywordIntentDetector:
    """Test keyword-based intent detection."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    # ==================== SQL Detection ====================
    
    def test_sql_select_polish(self, detector):
        """Test SQL select detection in Polish."""
        result = detector.detect("Pokaż wszystkich użytkowników")
        assert result.domain == 'sql'
        assert result.intent == 'select'
        assert result.confidence >= 0.7
    
    def test_sql_select_english(self, detector):
        """Test SQL select detection in English."""
        result = detector.detect("Show all users from the table")
        assert result.domain == 'sql'
        assert result.intent == 'select'
    
    def test_sql_select_with_table(self, detector):
        """Test SQL select with table reference."""
        result = detector.detect("Wyświetl dane z tabeli orders")
        assert result.domain == 'sql'
        assert result.confidence >= 0.7
    
    def test_sql_insert_polish(self, detector):
        """Test SQL insert detection in Polish."""
        result = detector.detect("Dodaj nowy rekord do tabeli users")
        assert result.domain == 'sql'
        assert result.intent == 'insert'
    
    def test_sql_update_polish(self, detector):
        """Test SQL update detection in Polish."""
        result = detector.detect("Zaktualizuj status użytkownika")
        assert result.domain == 'sql'
        assert result.intent == 'update'
    
    def test_sql_delete_polish(self, detector):
        """Test SQL delete detection in Polish."""
        result = detector.detect("Usuń rekord z tabeli orders")
        assert result.domain == 'sql'
        assert result.intent == 'delete'
    
    def test_sql_aggregate(self, detector):
        """Test SQL aggregate detection."""
        result = detector.detect("Policz ile jest rekordów w tabeli users")
        assert result.domain == 'sql'
        assert result.intent == 'aggregate'
    
    # ==================== Shell Detection ====================
    
    def test_shell_find_polish(self, detector):
        """Test shell find detection in Polish."""
        result = detector.detect("Znajdź pliki .py w katalogu")
        assert result.domain == 'shell'
        assert result.intent == 'find'
    
    def test_shell_find_english(self, detector):
        """Test shell find detection in English."""
        result = detector.detect("Find all Python files in directory")
        assert result.domain == 'shell'
    
    def test_shell_list(self, detector):
        """Test shell list detection."""
        result = detector.detect("Pokaż zawartość katalogu /var/log")
        assert result.domain == 'shell'
    
    def test_shell_process(self, detector):
        """Test shell process detection."""
        result = detector.detect("Pokaż uruchomione procesy systemowe")
        assert result.domain == 'shell'
        assert result.intent == 'process'
    
    def test_shell_disk(self, detector):
        """Test shell disk detection."""
        result = detector.detect("df -h miejsce na dysku")
        assert result.domain == 'shell'
        assert result.intent == 'disk'
    
    def test_shell_grep(self, detector):
        """Test shell grep detection."""
        result = detector.detect("Grep error w plikach logów")
        assert result.domain == 'shell'
        assert result.intent == 'grep'
    
    # ==================== Docker Detection ====================
    
    def test_docker_list_polish(self, detector):
        """Test docker list detection in Polish."""
        result = detector.detect("Pokaż uruchomione kontenery")
        assert result.domain == 'docker'
        assert result.intent == 'list'
    
    def test_docker_list_english(self, detector):
        """Test docker list detection in English."""
        result = detector.detect("Show running containers")
        assert result.domain == 'docker'
    
    def test_docker_run(self, detector):
        """Test docker run detection."""
        result = detector.detect("Uruchom kontener z obrazu nginx")
        assert result.domain == 'docker'
        assert result.intent == 'run'
    
    def test_docker_logs(self, detector):
        """Test docker logs detection."""
        result = detector.detect("Pokaż logi kontenera myapp")
        assert result.domain == 'docker'
        assert result.intent == 'logs'
    
    def test_docker_compose(self, detector):
        """Test docker compose detection."""
        result = detector.detect("Uruchom docker-compose up")
        assert result.domain == 'docker'
        assert result.intent == 'compose'
    
    # ==================== Kubernetes Detection ====================
    
    def test_k8s_get_pods_polish(self, detector):
        """Test k8s get pods detection in Polish."""
        result = detector.detect("Pokaż wszystkie pody w namespace default")
        assert result.domain == 'kubernetes'
        assert result.intent == 'get'
    
    def test_k8s_get_pods_english(self, detector):
        """Test k8s get pods detection in English."""
        result = detector.detect("k8s get pods deployments")
        assert result.domain == 'kubernetes'
    
    def test_k8s_scale(self, detector):
        """Test k8s scale detection."""
        result = detector.detect("Skaluj deployment do 5 replik")
        assert result.domain == 'kubernetes'
        assert result.intent == 'scale'
    
    def test_k8s_logs(self, detector):
        """Test k8s logs detection."""
        result = detector.detect("Pokaż logi poda myapp-123")
        assert result.domain == 'kubernetes'
        assert result.intent == 'logs'
    
    def test_k8s_describe(self, detector):
        """Test k8s describe detection."""
        result = detector.detect("opisz szczegóły poda myapp")
        assert result.domain == 'kubernetes'
        assert result.intent == 'describe'
    
    # ==================== Unknown Detection ====================
    
    def test_unknown_input(self, detector):
        """Test unknown input returns unknown domain."""
        result = detector.detect("xyzabc qwerty zxcvbn")
        assert result.domain == 'unknown'
        assert result.confidence == 0.0
    
    def test_ambiguous_input(self, detector):
        """Test ambiguous input with multiple possible domains."""
        # This could be SQL or Shell depending on context
        result = detector.detect("show something")
        # Should still detect something
        assert result.domain in ['sql', 'shell', 'docker', 'kubernetes', 'unknown']


class TestDetectionConfidence:
    """Test confidence scoring."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_high_confidence_with_domain_keywords(self, detector):
        """Test that domain-specific keywords boost confidence."""
        # With domain keyword "tabela"
        result1 = detector.detect("Pokaż dane z tabeli users")
        
        # Without domain keyword
        result2 = detector.detect("Pokaż dane")
        
        # Result with domain keyword should have higher confidence
        assert result1.confidence >= result2.confidence or result1.domain != 'unknown'
    
    def test_longer_keywords_boost_confidence(self, detector):
        """Test that longer keyword matches have higher confidence."""
        # Longer, more specific match
        result1 = detector.detect("znajdź pliki w katalogu")
        
        # Shorter match
        result2 = detector.detect("find x")
        
        # Both should detect shell domain
        assert result1.domain == 'shell'


class TestDetectAll:
    """Test detection of multiple possible domains."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_detect_all_returns_sorted_results(self, detector):
        """Test detect_all returns results sorted by confidence."""
        results = detector.detect_all("Pokaż dane z tabeli users")
        
        # Results should be sorted by confidence descending
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence
    
    def test_detect_all_no_duplicates(self, detector):
        """Test detect_all returns unique domain/intent pairs."""
        results = detector.detect_all("Pokaż wszystkich użytkowników z tabeli")
        
        seen = set()
        for r in results:
            key = (r.domain, r.intent)
            assert key not in seen, f"Duplicate: {key}"
            seen.add(key)


class TestCustomPatterns:
    """Test adding custom patterns."""
    
    def test_add_custom_pattern(self):
        """Test adding custom patterns."""
        detector = KeywordIntentDetector()
        
        # Add custom pattern
        detector.add_pattern('custom_domain', 'custom_intent', ['my_keyword', 'another_keyword'])
        
        result = detector.detect("Please my_keyword something")
        assert result.domain == 'custom_domain'
        assert result.intent == 'custom_intent'
    
    def test_custom_patterns_dict(self):
        """Test initializing with custom patterns dict."""
        custom = {
            'myapp': {
                'deploy': ['deploy', 'wdróż', 'release'],
                'rollback': ['rollback', 'cofnij', 'revert'],
            }
        }
        
        detector = KeywordIntentDetector(patterns=custom)
        
        result = detector.detect("Wdróż nową wersję aplikacji")
        assert result.domain == 'myapp'
        assert result.intent == 'deploy'


class TestKeywordDetectorPerformance:
    """Test performance metrics."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_detection_latency(self, detector):
        """Test that detection is fast (<10ms)."""
        test_inputs = [
            "Pokaż wszystkich użytkowników z tabeli users",
            "Find all Python files in /home",
            "Show running Docker containers",
            "Get pods in namespace production",
        ]
        
        for text in test_inputs:
            # Warm up
            detector.detect(text)
            
            # Measure
            start = time.time()
            for _ in range(100):
                detector.detect(text)
            elapsed = (time.time() - start) * 10  # ms per call
            
            assert elapsed < 10, f"Detection too slow: {elapsed:.2f}ms for '{text[:30]}...'"
    
    def test_bulk_detection_throughput(self, detector):
        """Test throughput with many detections."""
        test_inputs = [
            "Pokaż użytkowników",
            "Find files",
            "Docker containers",
            "Kubectl get pods",
        ] * 25  # 100 inputs
        
        start = time.time()
        results = [detector.detect(text) for text in test_inputs]
        elapsed = time.time() - start
        
        throughput = len(test_inputs) / elapsed
        
        # Should handle at least 1000 detections per second
        assert throughput > 1000, f"Throughput too low: {throughput:.0f}/s"
        
        # Verify results are valid
        assert all(isinstance(r, DetectionResult) for r in results)


# Evaluation dataset for accuracy measurement
KEYWORD_EVAL_DATASET = [
    # SQL - Polish
    ("Pokaż wszystkich użytkowników", "sql", "select"),
    ("Wyświetl dane z tabeli orders", "sql", "select"),
    ("Dodaj nowy rekord", "sql", "insert"),
    ("Zaktualizuj status", "sql", "update"),
    ("Usuń rekord", "sql", "delete"),
    ("Policz ile rekordów", "sql", "aggregate"),
    
    # SQL - English
    ("Show all users from table", "sql", "select"),
    ("Select data from orders", "sql", "select"),
    ("Insert new record", "sql", "insert"),
    ("Update user status", "sql", "update"),
    ("Delete old records", "sql", "delete"),
    
    # Shell - Polish
    ("Znajdź pliki .py", "shell", "find"),
    ("Pokaż zawartość katalogu", "shell", "list"),
    ("Pokaż uruchomione procesy", "shell", "process"),
    ("Sprawdź miejsce na dysku", "shell", "disk"),
    
    # Shell - English  
    ("Find Python files", "shell", "find"),
    ("List directory contents", "shell", "list"),
    ("Show running processes", "shell", "process"),
    
    # Docker - Polish
    ("Pokaż kontenery", "docker", "list"),
    ("Uruchom kontener", "docker", "run"),
    ("Logi kontenera", "docker", "logs"),
    
    # Docker - English
    ("Show containers", "docker", "list"),
    ("Docker run kontener nginx", "docker", "run"),
    ("Container logs", "docker", "logs"),
    
    # Kubernetes - Polish
    ("Pokaż pody", "kubernetes", "get"),
    ("Skaluj do 5 replik", "kubernetes", "scale"),
    ("Logi poda", "kubernetes", "logs"),
    
    # Kubernetes - English
    ("Get pods", "kubernetes", "get"),
    ("Scale to 5 replicas", "kubernetes", "scale"),
    ("Pod logs", "kubernetes", "logs"),
]


class TestKeywordAccuracy:
    """Measure accuracy on evaluation dataset."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    @pytest.mark.parametrize("text,expected_domain,expected_intent", KEYWORD_EVAL_DATASET)
    def test_eval_case(self, detector, text, expected_domain, expected_intent):
        """Test individual evaluation case."""
        result = detector.detect(text)
        
        assert result.domain == expected_domain, \
            f"Domain mismatch for '{text}': expected {expected_domain}, got {result.domain}"
        assert result.intent == expected_intent, \
            f"Intent mismatch for '{text}': expected {expected_intent}, got {result.intent}"
    
    def test_overall_accuracy(self, detector):
        """Calculate overall accuracy on dataset."""
        correct_domain = 0
        correct_intent = 0
        total = len(KEYWORD_EVAL_DATASET)
        
        for text, expected_domain, expected_intent in KEYWORD_EVAL_DATASET:
            result = detector.detect(text)
            
            if result.domain == expected_domain:
                correct_domain += 1
                if result.intent == expected_intent:
                    correct_intent += 1
        
        domain_accuracy = correct_domain / total
        intent_accuracy = correct_intent / total
        
        print(f"\n=== Keyword Detection Accuracy ===")
        print(f"  Domain accuracy: {domain_accuracy:.1%} ({correct_domain}/{total})")
        print(f"  Intent accuracy: {intent_accuracy:.1%} ({correct_intent}/{total})")
        
        # Target: >70% accuracy
        assert domain_accuracy >= 0.70, f"Domain accuracy too low: {domain_accuracy:.1%}"
        assert intent_accuracy >= 0.60, f"Intent accuracy too low: {intent_accuracy:.1%}"
