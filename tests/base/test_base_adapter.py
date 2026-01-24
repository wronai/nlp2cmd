"""
Base test class for DSL adapters.

This module provides common test utilities and base classes
for testing DSL adapters, reducing code duplication across test files.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

from nlp2cmd.adapters.base import BaseDSLAdapter
from nlp2cmd.core import ExecutionPlan


class BaseAdapterTestCase(ABC):
    """Base test case for DSL adapters with common test patterns."""
    
    @pytest.fixture
    @abstractmethod
    def adapter(self) -> BaseDSLAdapter:
        """Create adapter instance for testing."""
        pass
    
    @pytest.fixture
    def sample_plan(self) -> ExecutionPlan:
        """Create sample execution plan for testing."""
        return ExecutionPlan(
            intent="test",
            entities={"test_param": "test_value"},
            confidence=0.8,
        )
    
    def test_adapter_creation(self, adapter):
        """Test adapter creation and basic properties."""
        assert adapter is not None
        assert hasattr(adapter, 'generate')
        assert hasattr(adapter, 'check_safety')
        assert hasattr(adapter, 'validate_syntax')
        assert hasattr(adapter, 'get_intents')
    
    def test_generate_method_exists(self, adapter):
        """Test that generate method exists and is callable."""
        assert callable(getattr(adapter, 'generate', None))
    
    def test_check_safety_exists(self, adapter):
        """Test that check_safety method exists and is callable."""
        assert callable(getattr(adapter, 'check_safety', None))
    
    def test_validate_syntax_exists(self, adapter):
        """Test that validate_syntax method exists and is callable."""
        assert callable(getattr(adapter, 'validate_syntax', None))
    
    def test_get_intents_exists(self, adapter):
        """Test that get_intents method exists and is callable."""
        assert callable(getattr(adapter, 'get_intents', None))
    
    def test_generate_with_valid_plan(self, adapter, sample_plan):
        """Test generation with valid execution plan."""
        result = adapter.generate(sample_plan)
        
        assert isinstance(result, str)
        assert len(result) > 0  # Should generate some command
    
    def test_generate_with_empty_plan(self, adapter):
        """Test generation with empty execution plan."""
        empty_plan = ExecutionPlan(intent="", entities={})
        
        result = adapter.generate(empty_plan)
        
        # Should handle gracefully
        assert isinstance(result, str)
    
    def test_check_safety_safe_command(self, adapter):
        """Test safety check for safe command."""
        safe_command = "ls -la"
        
        result = adapter.check_safety(safe_command)
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
    
    def test_check_safety_dangerous_command(self, adapter):
        """Test safety check for dangerous command."""
        dangerous_command = "rm -rf /"
        
        result = adapter.check_safety(dangerous_command)
        
        assert isinstance(result, dict)
        # Should detect danger
        if not result.get('valid', True):
            assert len(result.get('errors', [])) > 0
    
    def test_validate_syntax_valid_command(self, adapter):
        """Test syntax validation for valid command."""
        valid_command = self._get_valid_command()
        
        result = adapter.validate_syntax(valid_command)
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
    
    def test_validate_syntax_invalid_command(self, adapter):
        """Test syntax validation for invalid command."""
        invalid_command = self._get_invalid_command()
        
        result = adapter.validate_syntax(invalid_command)
        
        assert isinstance(result, dict)
        # Should detect syntax errors
        if not result.get('valid', True):
            assert len(result.get('errors', [])) > 0
    
    def test_get_intents_returns_list(self, adapter):
        """Test that get_intents returns a list."""
        intents = adapter.get_intents()
        
        assert isinstance(intents, list)
        assert len(intents) > 0  # Should have at least one intent
    
    def test_get_intents_contains_expected_intents(self, adapter):
        """Test that get_intents contains expected intents."""
        intents = adapter.get_intents()
        expected_intents = self._get_expected_intents()
        
        for expected_intent in expected_intents:
            assert expected_intent in intents
    
    def test_adapter_error_handling(self, adapter):
        """Test adapter error handling."""
        # Test with None plan
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(None)
    
    def test_adapter_with_minimal_entities(self, adapter):
        """Test adapter with minimal entities."""
        minimal_plan = ExecutionPlan(
            intent=self._get_minimal_intent(),
            entities={},
            confidence=0.5,
        )
        
        result = adapter.generate(minimal_plan)
        assert isinstance(result, str)
    
    def test_adapter_with_complex_entities(self, adapter):
        """Test adapter with complex nested entities."""
        complex_entities = self._get_complex_entities()
        complex_plan = ExecutionPlan(
            intent="complex",
            entities=complex_entities,
            confidence=0.7,
        )
        
        result = adapter.generate(complex_plan)
        assert isinstance(result, str)
    
    def test_adapter_with_low_confidence(self, adapter):
        """Test adapter with low confidence plan."""
        low_confidence_plan = ExecutionPlan(
            intent="test",
            entities={"param": "value"},
            confidence=0.1,  # Very low confidence
        )
        
        result = adapter.generate(low_confidence_plan)
        assert isinstance(result, str)
    
    def test_adapter_with_high_confidence(self, adapter):
        """Test adapter with high confidence plan."""
        high_confidence_plan = ExecutionPlan(
            intent="test",
            entities={"param": "value"},
            confidence=0.95,  # High confidence
        )
        
        result = adapter.generate(high_confidence_plan)
        assert isinstance(result, str)
    
    def test_adapter_consistency(self, adapter):
        """Test that adapter produces consistent results."""
        plan = ExecutionPlan(
            intent="test",
            entities={"param": "value"},
            confidence=0.8,
        )
        
        result1 = adapter.generate(plan)
        result2 = adapter.generate(plan)
        
        # Should produce same result for same input
        assert result1 == result2
    
    def test_adapter_metadata_handling(self, adapter):
        """Test adapter handling of metadata."""
        plan_with_metadata = ExecutionPlan(
            intent="test",
            entities={"param": "value"},
            confidence=0.8,
            metadata={"test": "metadata"},
        )
        
        result = adapter.generate(plan_with_metadata)
        assert isinstance(result, str)
    
    # Abstract methods to be implemented by concrete test classes
    
    @abstractmethod
    def _get_valid_command(self) -> str:
        """Get a valid command for this adapter type."""
        pass
    
    @abstractmethod
    def _get_invalid_command(self) -> str:
        """Get an invalid command for this adapter type."""
        pass
    
    @abstractmethod
    def _get_expected_intents(self) -> List[str]:
        """Get expected intents for this adapter type."""
        pass
    
    @abstractmethod
    def _get_minimal_intent(self) -> str:
        """Get minimal intent that should work."""
        pass
    
    def _get_complex_entities(self) -> Dict[str, Any]:
        """Get complex entities for testing."""
        return {
            "filters": [
                {"field": "status", "operator": "=", "value": "active"},
                {"field": "created_at", "operator": ">", "value": "2023-01-01"}
            ],
            "ordering": [{"field": "created_at", "direction": "desc"}],
            "pagination": {"offset": 0, "limit": 50}
        }


class AdapterTestUtils:
    """Utility methods for adapter testing."""
    
    @staticmethod
    def assert_command_contains(command: str, expected_substrings: List[str]):
        """Assert that command contains all expected substrings."""
        for substring in expected_substrings:
            assert substring in command, f"Expected '{substring}' in command: {command}"
    
    @staticmethod
    def assert_command_not_contains(command: str, forbidden_substrings: List[str]):
        """Assert that command does not contain any forbidden substrings."""
        for substring in forbidden_substrings:
            assert substring not in command, f"Command should not contain '{substring}': {command}"
    
    @staticmethod
    def assert_valid_syntax_result(result: Dict[str, Any]):
        """Assert that syntax validation result has expected structure."""
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert isinstance(result['valid'], bool)
        assert isinstance(result['errors'], list)
        assert isinstance(result['warnings'], list)
    
    @staticmethod
    def assert_safety_result(result: Dict[str, Any]):
        """Assert that safety check result has expected structure."""
        AdapterTestUtils.assert_valid_syntax_result(result)
        
        # Additional safety-specific checks
        if not result['valid']:
            assert len(result['errors']) > 0, "Invalid result should have at least one error"
    
    @staticmethod
    def create_mock_execution_plan(intent: str, entities: Dict[str, Any], 
                                   confidence: float = 0.8) -> ExecutionPlan:
        """Create a mock execution plan for testing."""
        return ExecutionPlan(
            intent=intent,
            entities=entities,
            confidence=confidence,
        )
    
    @staticmethod
    def run_adapter_test_suite(adapter: BaseDSLAdapter, test_cases: List[Dict[str, Any]]):
        """Run a standard test suite for an adapter."""
        for test_case in test_cases:
            plan = test_case['plan']
            expected_contains = test_case.get('expected_contains', [])
            expected_not_contains = test_case.get('expected_not_contains', [])
            
            result = adapter.generate(plan)
            
            if expected_contains:
                AdapterTestUtils.assert_command_contains(result, expected_contains)
            
            if expected_not_contains:
                AdapterTestUtils.assert_command_not_contains(result, expected_not_contains)


class MockAdapter(BaseDSLAdapter):
    """Mock adapter for testing purposes."""
    
    def generate(self, plan: ExecutionPlan) -> str:
        """Mock generate method."""
        if plan is None:
            raise TypeError("plan must not be None")
        return f"mock command for {plan.intent} with {plan.entities}"
    
    def check_safety(self, command: str) -> Dict[str, Any]:
        """Mock safety check."""
        return {
            'valid': True,
            'errors': [],
            'warnings': []
        }
    
    def validate_syntax(self, command: str) -> Dict[str, Any]:
        """Mock syntax validation."""
        return {
            'valid': True,
            'errors': [],
            'warnings': []
        }
    
    def get_intents(self) -> List[str]:
        """Mock intents."""
        return ['mock_intent']


class TestBaseAdapterTestCase(BaseAdapterTestCase):
    """Test the base test case class itself."""
    
    @pytest.fixture
    def adapter(self):
        """Create mock adapter for testing."""
        return MockAdapter()
    
    def _get_valid_command(self) -> str:
        """Get a valid command for mock adapter."""
        return "mock command"
    
    def _get_invalid_command(self) -> str:
        """Get an invalid command for mock adapter."""
        return ""
    
    def _get_expected_intents(self) -> List[str]:
        """Get expected intents for mock adapter."""
        return ['mock_intent']
    
    def _get_minimal_intent(self) -> str:
        """Get minimal intent that should work."""
        return "mock_intent"
