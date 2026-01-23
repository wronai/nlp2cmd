"""
Test NLP integration functionality.

This module tests NLP backend integration, intent detection,
entity extraction, and end-to-end transformation flows.
"""

import pytest
from unittest.mock import Mock, patch

from nlp2cmd.core import (
    NLP2CMD,
    TransformResult,
    TransformStatus,
    ExecutionPlan,
    NLPBackend,
    RuleBasedBackend,
    SpaCyBackend,
    LLMBackend,
)
from nlp2cmd.adapters import SQLAdapter, ShellAdapter


class TestNLPIntegration:
    """Test NLP integration functionality."""

    def test_nlp2cmd_initialization(self):
        """Test NLP2CMD initialization."""
        from nlp2cmd.adapters import SQLAdapter
        adapter = SQLAdapter()
        nlp2cmd = NLP2CMD(adapter=adapter)
        
        assert nlp2cmd is not None
        assert hasattr(nlp2cmd, 'transform')
        assert hasattr(nlp2cmd, 'adapter')

    def test_transform_result_creation(self):
        """Test transform result creation."""
        plan = ExecutionPlan(intent="select", entities={"table": "users"})
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT * FROM users",
            plan=plan,
            confidence=0.9,
            dsl_type="sql",
        )
        
        assert result.status == TransformStatus.SUCCESS
        assert result.command == "SELECT * FROM users"
        assert result.is_success
        assert result.is_valid

    def test_execution_plan_creation(self):
        """Test execution plan creation."""
        plan = ExecutionPlan(
            intent="create",
            entities={"resource": "pod", "name": "webapp"},
            confidence=0.92,
        )
        
        assert plan.intent == "create"
        assert plan.entities["resource"] == "pod"
        assert plan.confidence == 0.92
        assert plan.is_valid

    def test_nlp_backend_base_class(self):
        """Test NLP backend base class."""
        backend = NLPBackend()
        
        assert backend is not None
        assert hasattr(backend, 'extract_intent')
        assert hasattr(backend, 'extract_entities')
        assert hasattr(backend, 'config')

    def test_adapter_integration(self):
        """Test adapter integration with core components."""
        sql_adapter = SQLAdapter()
        shell_adapter = ShellAdapter()
        
        assert sql_adapter is not None
        assert shell_adapter is not None
        assert hasattr(sql_adapter, 'generate')
        assert hasattr(shell_adapter, 'generate')

    def test_transform_status_values(self):
        """Test transform status enum values."""
        assert TransformStatus.SUCCESS.value == "success"
        assert TransformStatus.FAILED.value == "failed"
        assert TransformStatus.BLOCKED.value == "blocked"
        assert TransformStatus.PARTIAL.value == "partial"
        assert TransformStatus.ERROR.value == "error"

    def test_execution_plan_methods(self):
        """Test execution plan helper methods."""
        plan = ExecutionPlan(intent="list", entities={"path": "/home"})
        
        # Test with_confidence
        updated_plan = plan.with_confidence(0.95)
        assert updated_plan.confidence == 0.95
        assert updated_plan.intent == "list"
        
        # Test with_entities
        merged_plan = plan.with_entities({"recursive": True})
        assert merged_plan.entities["path"] == "/home"
        assert merged_plan.entities["recursive"] is True

    def test_nlp_backend_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        backend = NLPBackend()

        with pytest.raises(NotImplementedError):
            backend.extract_intent("test text")

        with pytest.raises(NotImplementedError):
            backend.extract_entities("test text")

        with pytest.raises(NotImplementedError):
            backend.generate_plan("test text")

    def test_basic_integration_flow(self):
        """Test basic integration flow between components."""
        # Create execution plan
        plan = ExecutionPlan(
            intent="select",
            entities={"table": "users", "columns": ["id", "name"]},
            confidence=0.9
        )
        
        # Create transform result
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT id, name FROM users",
            plan=plan,
            confidence=0.9,
            dsl_type="sql"
        )
        
        # Verify integration
        assert result.is_success
        assert result.is_valid
        assert plan.is_valid
        assert result.plan.intent == plan.intent
