"""
Test SQL validation functionality.

This module tests SQL syntax validation, safety checks,
and comprehensive validation rules for SQL queries.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
    SQLValidator,
)


class TestSQLValidator:
    """Test SQL validator functionality."""
    
    @pytest.fixture
    def validator(self) -> SQLValidator:
        return SQLValidator()
    
    def test_valid_select(self, validator):
        """Test valid SELECT is accepted."""
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid
        assert not result.errors
    
    def test_unbalanced_parentheses(self, validator):
        """Test unbalanced parentheses detected."""
        result = validator.validate("SELECT * FROM users WHERE (id = 1")
        assert not result.is_valid
        assert any("parentheses" in error.lower() for error in result.errors)
    
    def test_unclosed_string(self, validator):
        """Test unclosed string detected."""
        result = validator.validate("SELECT * FROM users WHERE name = 'test")
        assert not result.is_valid
        assert any("string" in error.lower() for error in result.errors)
    
    def test_delete_without_where_warning(self, validator):
        """Test DELETE without WHERE generates warning."""
        result = validator.validate("DELETE FROM users")
        assert result.is_valid  # Still valid but with warning
        assert any("without where" in warning.lower() for warning in result.warnings)
    
    def test_update_without_where_warning(self, validator):
        """Test UPDATE without WHERE generates warning."""
        result = validator.validate("UPDATE users SET name = 'test'")
        assert result.is_valid  # Still valid but with warning
        assert any("without where" in warning.lower() for warning in result.warnings)
    
    def test_drop_table_warning(self, validator):
        """Test DROP TABLE generates warning."""
        result = validator.validate("DROP TABLE users")
        assert result.is_valid  # Still valid but with warning
        assert any("DROP" in warning.upper() for warning in result.warnings)
    
    def test_sql_injection_attempt(self, validator):
        """Test SQL injection attempt detection."""
        result = validator.validate("SELECT * FROM users WHERE id = 1; DROP TABLE users; --")
        assert not result.is_valid
        assert any("injection" in error.lower() or "multiple statements" in error.lower() 
                   for error in result.errors)
    
    def test_reserved_keywords_in_identifiers(self, validator):
        """Test reserved keywords in identifiers."""
        result = validator.validate("SELECT * FROM order WHERE select = 'test'")
        assert result.is_valid  # Valid but with warning
        assert any("reserved keyword" in warning.lower() for warning in result.warnings)
    
    def test_aggregate_without_group_by(self, validator):
        """Test aggregate without GROUP BY warning."""
        result = validator.validate("SELECT COUNT(*) FROM users")
        assert result.is_valid  # Valid but with warning
        assert any("GROUP BY" in warning for warning in result.warnings)
    
    def test_limit_clause_validation(self, validator):
        """Test LIMIT clause validation."""
        result = validator.validate("SELECT * FROM users LIMIT -1")
        assert not result.is_valid
        assert any("negative" in error.lower() or "invalid limit" in error.lower() 
                   for error in result.errors)
    
    def test_join_syntax_validation(self, validator):
        """Test JOIN syntax validation."""
        result = validator.validate("SELECT * FROM users JOIN orders")
        assert not result.is_valid
        assert any("join" in error.lower() and "condition" in error.lower() 
                   for error in result.errors)
    
    def test_subquery_validation(self, validator):
        """Test subquery validation."""
        result = validator.validate("SELECT * FROM users WHERE id IN (SELECT id FROM orders)")
        assert result.is_valid
    
    def test_union_validation(self, validator):
        """Test UNION validation."""
        result = validator.validate("SELECT name FROM users UNION SELECT title FROM products")
        assert result.is_valid
    
    def test_union_all_validation(self, validator):
        """Test UNION ALL validation."""
        result = validator.validate("SELECT name FROM users UNION ALL SELECT title FROM products")
        assert result.is_valid
