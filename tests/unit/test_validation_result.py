"""
Test ValidationResult functionality.

This module tests the ValidationResult dataclass and its methods
for managing validation outcomes, errors, and warnings.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test creating valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
    
    def test_invalid_result_with_errors(self):
        """Test creating invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(
            is_valid=True,
            warnings=["Warning 1"],
        )
        result2 = ValidationResult(
            is_valid=False,
            errors=["Error 1"],
        )
        
        merged = result1.merge(result2)
        
        assert not merged.is_valid  # Should be invalid due to error
        assert "Error 1" in merged.errors
        assert "Warning 1" in merged.warnings
    
    def test_merge_multiple_results(self):
        """Test merging multiple validation results."""
        result1 = ValidationResult(
            is_valid=True,
            warnings=["Warning 1"],
        )
        result2 = ValidationResult(
            is_valid=True,
            warnings=["Warning 2"],
        )
        result3 = ValidationResult(
            is_valid=False,
            errors=["Error 1"],
            warnings=["Warning 3"],
        )
        
        merged = result1.merge(result2).merge(result3)
        
        assert not merged.is_valid
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 3
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["is_valid"] is False
        assert result_dict["errors"] == ["Error 1", "Error 2"]
        assert result_dict["warnings"] == ["Warning 1"]
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "is_valid": True,
            "errors": [],
            "warnings": ["Warning 1"],
        }
        
        result = ValidationResult.from_dict(data)
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["Warning 1"]
    
    def test_add_error(self):
        """Test adding error to result."""
        result = ValidationResult(is_valid=True)
        
        result.add_error("New error")
        
        assert not result.is_valid
        assert "New error" in result.errors
    
    def test_add_warning(self):
        """Test adding warning to result."""
        result = ValidationResult(is_valid=True)
        
        result.add_warning("New warning")
        
        assert result.is_valid  # Still valid with warning
        assert "New warning" in result.warnings
    
    def test_has_errors(self):
        """Test has_errors method."""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=False, errors=["Error"])
        
        assert not result1.has_errors()
        assert result2.has_errors()
    
    def test_has_warnings(self):
        """Test has_warnings method."""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=True, warnings=["Warning"])
        
        assert not result1.has_warnings()
        assert result2.has_warnings()
    
    def test_str_representation(self):
        """Test string representation."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        
        str_repr = str(result)
        
        assert "INVALID" in str_repr
        assert "Error 1" in str_repr
        assert "Error 2" in str_repr
        assert "Warning 1" in str_repr
    
    def test_equality(self):
        """Test result equality."""
        result1 = ValidationResult(
            is_valid=False,
            errors=["Error"],
            warnings=["Warning"],
        )
        result2 = ValidationResult(
            is_valid=False,
            errors=["Error"],
            warnings=["Warning"],
        )
        result3 = ValidationResult(is_valid=True)
        
        assert result1 == result2
        assert result1 != result3
    
    def test_copy(self):
        """Test result copying."""
        original = ValidationResult(
            is_valid=False,
            errors=["Error"],
            warnings=["Warning"],
        )
        
        copied = original.copy()
        
        assert copied == original
        assert copied is not original  # Different objects
        assert copied.errors is not original.errors  # Different lists
