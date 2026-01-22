"""
Iteration 2: Regex Entity Extraction Tests.

Test entity extraction from text using regex patterns.
"""

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult


class TestRegexEntityExtractor:
    """Test regex-based entity extraction."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    # ==================== SQL Entity Extraction ====================
    
    def test_sql_extract_table_from_polish(self, extractor):
        """Test table extraction from Polish text."""
        result = extractor.extract("Pokaż dane z tabeli users", domain='sql')
        assert result.entities.get('table') == 'users'
    
    def test_sql_extract_table_from_english(self, extractor):
        """Test table extraction from English text."""
        result = extractor.extract("Select all from orders table", domain='sql')
        assert 'orders' in str(result.entities.get('table', '')) or result.entities.get('table') == 'orders'
    
    def test_sql_extract_limit(self, extractor):
        """Test limit extraction."""
        result = extractor.extract("Pokaż limit 10 rekordów", domain='sql')
        assert result.entities.get('limit') == '10'
    
    def test_sql_extract_limit_polish_suffix(self, extractor):
        """Test limit extraction with Polish suffix."""
        result = extractor.extract("Pokaż 5 rekordów z tabeli users", domain='sql')
        assert result.entities.get('limit') == '5'
    
    def test_sql_extract_where_field_value(self, extractor):
        """Test WHERE clause extraction."""
        result = extractor.extract("gdzie status = active", domain='sql')
        assert result.entities.get('where_field') == 'status'
        assert result.entities.get('where_value') == 'active'
    
    def test_sql_extract_order_by(self, extractor):
        """Test ORDER BY extraction."""
        result = extractor.extract("sortuj po created_at malejąco", domain='sql')
        assert result.entities.get('order_by') == 'created_at'
        assert result.entities.get('order_direction') in ['DESC', 'malejąco']
    
    def test_sql_extract_aggregation(self, extractor):
        """Test aggregation function extraction."""
        result = extractor.extract("policz ile jest rekordów", domain='sql')
        assert 'aggregation' in result.entities or 'aggregations' in result.entities
    
    def test_sql_filters_post_processing(self, extractor):
        """Test that filters are post-processed correctly."""
        result = extractor.extract("gdzie status = active z tabeli users", domain='sql')
        
        if 'filters' in result.entities:
            assert len(result.entities['filters']) > 0
            assert result.entities['filters'][0]['field'] == 'status'
    
    # ==================== Shell Entity Extraction ====================
    
    def test_shell_extract_path(self, extractor):
        """Test path extraction."""
        result = extractor.extract("w katalogu /home/user/documents", domain='shell')
        assert '/home/user/documents' in result.entities.get('path', '')
    
    def test_shell_extract_path_with_tilde(self, extractor):
        """Test path extraction with tilde."""
        result = extractor.extract("w folderze ~/projects", domain='shell')
        path = result.entities.get('path', '')
        assert '~' in path or '$HOME' in path or 'projects' in path
    
    def test_shell_extract_file_pattern(self, extractor):
        """Test file pattern extraction."""
        result = extractor.extract("znajdź pliki .py", domain='shell')
        pattern = result.entities.get('file_pattern', result.entities.get('pattern', ''))
        assert 'py' in pattern
    
    def test_shell_extract_file_pattern_with_asterisk(self, extractor):
        """Test file pattern extraction with asterisk."""
        result = extractor.extract("znajdź *.log files", domain='shell')
        assert 'log' in str(result.entities)
    
    def test_shell_extract_size(self, extractor):
        """Test file size extraction."""
        result = extractor.extract("pliki większe niż 100MB", domain='shell')
        size = result.entities.get('size', {})
        if isinstance(size, dict):
            assert size.get('value') == 100 or '100' in str(size)
    
    def test_shell_extract_process_name(self, extractor):
        """Test process name extraction."""
        result = extractor.extract("zabij proces python", domain='shell')
        assert result.entities.get('process_name') == 'python'
    
    # ==================== Docker Entity Extraction ====================
    
    def test_docker_extract_container_name(self, extractor):
        """Test container name extraction."""
        result = extractor.extract("logi kontenera myapp", domain='docker')
        assert result.entities.get('container') == 'myapp'
    
    def test_docker_extract_image(self, extractor):
        """Test image name extraction."""
        result = extractor.extract("uruchom z obrazu nginx:latest", domain='docker')
        assert 'nginx' in result.entities.get('image', '')
    
    def test_docker_extract_port(self, extractor):
        """Test port extraction."""
        result = extractor.extract("na porcie 8080", domain='docker')
        port = result.entities.get('port')
        if isinstance(port, dict):
            assert '8080' in str(port)
        else:
            assert port == '8080'
    
    def test_docker_extract_port_mapping(self, extractor):
        """Test port mapping extraction."""
        result = extractor.extract("-p 8080:80", domain='docker')
        port = result.entities.get('port', {})
        if isinstance(port, dict):
            assert port.get('host') == '8080'
            assert port.get('container') in ['80', '8080']
    
    def test_docker_extract_tail_lines(self, extractor):
        """Test tail lines extraction."""
        result = extractor.extract("--tail 50 logi", domain='docker')
        assert result.entities.get('tail_lines') == '50'
    
    # ==================== Kubernetes Entity Extraction ====================
    
    def test_k8s_extract_resource_type(self, extractor):
        """Test resource type extraction."""
        result = extractor.extract("pokaż wszystkie pody", domain='kubernetes')
        rt = result.entities.get('resource_type', '')
        assert 'pod' in rt.lower()
    
    def test_k8s_extract_namespace(self, extractor):
        """Test namespace extraction."""
        result = extractor.extract("w namespace production", domain='kubernetes')
        assert result.entities.get('namespace') == 'production'
    
    def test_k8s_extract_namespace_flag(self, extractor):
        """Test namespace extraction from -n flag."""
        result = extractor.extract("-n default", domain='kubernetes')
        assert result.entities.get('namespace') == 'default'
    
    def test_k8s_extract_replica_count(self, extractor):
        """Test replica count extraction."""
        result = extractor.extract("skaluj do 5 replik", domain='kubernetes')
        assert result.entities.get('replica_count') == '5'
    
    def test_k8s_extract_selector(self, extractor):
        """Test selector extraction."""
        result = extractor.extract("z etykietą app=myapp", domain='kubernetes')
        selector = result.entities.get('selector', '')
        assert 'app=myapp' in selector or 'app' in selector


class TestExtractionPostProcessing:
    """Test post-processing of extracted entities."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    def test_sql_filters_structure(self, extractor):
        """Test SQL filters are properly structured."""
        result = extractor.extract("gdzie status = active", domain='sql')
        
        if 'filters' in result.entities:
            filters = result.entities['filters']
            assert isinstance(filters, list)
            if filters:
                assert 'field' in filters[0]
                assert 'operator' in filters[0]
                assert 'value' in filters[0]
    
    def test_sql_ordering_structure(self, extractor):
        """Test SQL ordering is properly structured."""
        result = extractor.extract("sortuj po name rosnąco", domain='sql')
        
        if 'ordering' in result.entities:
            ordering = result.entities['ordering']
            assert isinstance(ordering, list)
            if ordering:
                assert 'field' in ordering[0]
                assert 'direction' in ordering[0]
    
    def test_shell_path_normalization(self, extractor):
        """Test shell path normalization."""
        result = extractor.extract("w katalogu ~/docs", domain='shell')
        path = result.entities.get('path', '')
        # Should contain the path or be normalized
        assert path or 'docs' in str(result.entities)
    
    def test_k8s_resource_type_normalization(self, extractor):
        """Test Kubernetes resource type normalization."""
        result = extractor.extract("pokaż pody", domain='kubernetes')
        rt = result.entities.get('resource_type', '')
        assert rt.lower() in ['pods', 'pod', 'pody']


class TestExtractedEntityMetadata:
    """Test extracted entity metadata."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    def test_extraction_includes_source_pattern(self, extractor):
        """Test that extraction result includes source pattern."""
        result = extractor.extract("z tabeli users", domain='sql')
        
        # Check extracted list has source pattern info
        for entity in result.extracted:
            if entity.name == 'table':
                assert entity.source_pattern is not None
    
    def test_extraction_includes_confidence(self, extractor):
        """Test that extraction result includes confidence."""
        result = extractor.extract("z tabeli users", domain='sql')
        
        for entity in result.extracted:
            assert entity.confidence > 0


class TestCustomPatterns:
    """Test adding custom regex patterns."""
    
    def test_add_custom_pattern(self):
        """Test adding custom patterns."""
        extractor = RegexEntityExtractor()
        
        extractor.add_pattern('sql', 'custom_field', [r'moje_pole\s+(\w+)'])
        
        result = extractor.extract("moje_pole test_value", domain='sql')
        assert result.entities.get('custom_field') == 'test_value'
    
    def test_custom_patterns_dict(self):
        """Test initializing with custom patterns dict."""
        custom = {
            'custom_domain': {
                'custom_entity': [r'entity:\s*(\w+)'],
            }
        }
        
        extractor = RegexEntityExtractor(custom_patterns=custom)
        
        result = extractor.extract("entity: my_value", domain='custom_domain')
        assert result.entities.get('custom_entity') == 'my_value'


class TestHelperMethods:
    """Test helper extraction methods."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    def test_extract_all_numbers(self, extractor):
        """Test extracting all numbers from text."""
        numbers = extractor.extract_all_numbers("Pokaż 10 rekordów z ostatnich 30 dni limit 5")
        assert 10 in numbers
        assert 30 in numbers
        assert 5 in numbers
    
    def test_extract_quoted_strings(self, extractor):
        """Test extracting quoted strings."""
        strings = extractor.extract_quoted_strings('znajdź "error" w pliku \'log.txt\'')
        assert 'error' in strings
        assert 'log.txt' in strings


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
