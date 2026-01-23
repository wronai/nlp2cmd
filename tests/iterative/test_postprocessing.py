"""
Test post-processing of extracted entities.

This module tests the structure, normalization, and metadata handling
of extracted entities after the initial regex extraction.
"""

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult


class TestExtractionPostProcessing:
    """Test post-processing of extracted entities."""
    
    @pytest.fixture
    def extractor(self) -> RegexEntityExtractor:
        return RegexEntityExtractor()
    
    def test_sql_filters_structure(self, extractor):
        """Test SQL filters are properly structured."""
        result = extractor.extract("gdzie status = active i age > 18", domain='sql')
        
        filters = result.entities.get('filters', [])
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
