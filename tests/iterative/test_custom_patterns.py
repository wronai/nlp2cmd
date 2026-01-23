"""
Test custom regex patterns functionality.

This module tests the ability to add custom patterns
and initialize the extractor with custom pattern dictionaries.
"""

import pytest

from nlp2cmd.generation.regex import RegexEntityExtractor


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
