"""
Test SQL keyword intent detection.

This module tests keyword-based intent detection for SQL domain
including SELECT, INSERT, UPDATE, DELETE operations.
"""

import pytest

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult


class TestSQLKeywords:
    """Test SQL keyword intent detection."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
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
        result = detector.detect("Policz liczbę rekordów")
        assert result.domain == 'sql'
        assert result.intent in ['count', 'aggregate']
    
    def test_sql_join(self, detector):
        """Test SQL join detection."""
        result = detector.detect("Połącz tabele users i orders")
        assert result.domain == 'sql'
        assert result.intent == 'join'
    
    def test_sql_create_table(self, detector):
        """Test SQL create table detection."""
        result = detector.detect("Stwórz tabelę products")
        assert result.domain == 'sql'
        assert result.intent == 'create_table'
    
    def test_sql_drop_table(self, detector):
        """Test SQL drop table detection."""
        result = detector.detect("Usuń tabelę temp_data")
        assert result.domain == 'sql'
        assert result.intent == 'drop_table'
