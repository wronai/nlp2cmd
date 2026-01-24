"""
Test entity extraction from text using regex patterns.

This module focuses on testing the core entity extraction functionality
for different domains (SQL, Shell, Docker, Kubernetes).
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
    
    def test_sql_extract_aggregation(self, extractor):
        """Test aggregation function extraction."""
        result = extractor.extract("policz rekordy", domain='sql')
        assert result.entities.get('aggregation') == 'count'
    
    # ==================== Shell Entity Extraction ====================
    
    def test_shell_extract_path(self, extractor):
        """Test path extraction."""
        result = extractor.extract("w katalogu /home/user", domain='shell')
        path = result.entities.get('path', '')
        assert '/home/user' in path or 'home' in path
    
    def test_shell_extract_path_with_tilde(self, extractor):
        """Test path extraction with tilde."""
        result = extractor.extract("w katalogu ~/docs", domain='shell')
        path = result.entities.get('path', '')
        assert path or 'docs' in str(result.entities)
    
    def test_shell_extract_file_pattern(self, extractor):
        """Test file pattern extraction."""
        result = extractor.extract("pliki *.py", domain='shell')
        pattern = result.entities.get('pattern', '')
        assert '.py' in pattern or 'py' in pattern
    
    def test_shell_extract_file_pattern_with_asterisk(self, extractor):
        """Test file pattern extraction with asterisk."""
        result = extractor.extract("wszystkie pliki *.log", domain='shell')
        pattern = result.entities.get('pattern', '')
        assert '.log' in pattern or 'log' in pattern
    
    def test_shell_extract_size(self, extractor):
        """Test file size extraction."""
        result = extractor.extract("pliki większe niż 100MB", domain='shell')
        size = result.entities.get('size', '')
        assert '100' in size

    def test_shell_extract_size_does_not_set_file_pattern(self, extractor):
        result = extractor.extract("Znajdź pliki większe niż 1MB", domain='shell')
        assert result.entities.get('file_pattern') in {None, ''}

    def test_shell_extract_process_name(self, extractor):
        """Test process name extraction."""
        result = extractor.extract("proces nginx", domain='shell')
        process = result.entities.get('process_name', '')
        assert 'nginx' in process
    
    # ==================== Docker Entity Extraction ====================
    
    def test_docker_extract_container_name(self, extractor):
        """Test container name extraction."""
        result = extractor.extract("kontener webapp", domain='docker')
        container = result.entities.get('container', '')
        assert 'webapp' in container
    
    def test_docker_extract_image(self, extractor):
        """Test image name extraction."""
        result = extractor.extract("obraz nginx:latest", domain='docker')
        image = result.entities.get('image', '')
        assert 'nginx' in image
    
    def test_docker_extract_port(self, extractor):
        """Test port extraction."""
        result = extractor.extract("na porcie 8080", domain='docker')
        port = result.entities.get('port', '')
        assert '8080' in port
    
    def test_docker_extract_port_mapping(self, extractor):
        """Test port mapping extraction."""
        result = extractor.extract("mapuj port 8080:80", domain='docker')
        port = result.entities.get('port', '')
        assert '8080' in port or '80' in port
    
    def test_docker_extract_tail_lines(self, extractor):
        """Test tail lines extraction."""
        result = extractor.extract("ostatnie 100 linii", domain='docker')
        tail = result.entities.get('tail_lines', '')
        assert '100' in tail
    
    # ==================== Kubernetes Entity Extraction ====================
    
    def test_k8s_extract_resource_type(self, extractor):
        """Test resource type extraction."""
        result = extractor.extract("poda", domain='kubernetes')
        resource = result.entities.get('resource_type', '')
        assert resource.lower() in ['pod', 'poda', 'pods']
    
    def test_k8s_extract_namespace(self, extractor):
        """Test namespace extraction."""
        result = extractor.extract("w namespace production", domain='kubernetes')
        namespace = result.entities.get('namespace', '')
        assert 'production' in namespace
    
    def test_k8s_extract_namespace_flag(self, extractor):
        """Test namespace extraction from -n flag."""
        result = extractor.extract("-n staging", domain='kubernetes')
        namespace = result.entities.get('namespace', '')
        assert 'staging' in namespace
    
    def test_k8s_extract_replica_count(self, extractor):
        """Test replica count extraction."""
        result = extractor.extract("3 repliki", domain='kubernetes')
        replicas = result.entities.get('replica_count', '')
        assert '3' in replicas
    
    def test_k8s_extract_selector(self, extractor):
        """Test selector extraction."""
        result = extractor.extract("z selektorem app=web", domain='kubernetes')
        selector = result.entities.get('selector', '')
        assert 'app=web' in selector
