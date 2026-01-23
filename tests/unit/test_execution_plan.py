"""
Test ExecutionPlan functionality.

This module tests execution plan creation, validation,
serialization, and plan management operations.
"""

import pytest
from dataclasses import asdict
import json

from nlp2cmd.core import (
    ExecutionPlan,
    Intent,
    Entity,
)


class TestExecutionPlan:
    """Test execution plan functionality."""

    def test_create_plan(self):
        """Test creating an execution plan."""
        plan = ExecutionPlan(
            intent="select",
            entities={"table": "users", "columns": ["id", "name"]},
            confidence=0.9,
        )

        assert plan.intent == "select"
        assert plan.entities["table"] == "users"
        assert plan.entities["columns"] == ["id", "name"]
        assert plan.confidence == 0.9
        assert not plan.requires_confirmation
        assert plan.metadata == {}

    def test_plan_defaults(self):
        """Test plan default values."""
        plan = ExecutionPlan(
            intent="list",
            entities={"path": "/home"},
        )

        assert plan.confidence == 0.0  # Default confidence
        assert not plan.requires_confirmation
        assert plan.metadata == {}

    def test_plan_with_confirmation(self):
        """Test plan requiring confirmation."""
        plan = ExecutionPlan(
            intent="delete",
            entities={"table": "users"},
            requires_confirmation=True,
            metadata={"reason": "destructive operation"},
        )

        assert plan.requires_confirmation
        assert plan.metadata["reason"] == "destructive operation"

    def test_plan_serialization(self):
        """Test plan model_dump."""
        plan = ExecutionPlan(
            intent="update",
            entities={"table": "users", "field": "status", "value": "active"},
            confidence=0.85,
            requires_confirmation=False,
            metadata={"source": "user_input"},
        )

        # Test model serialization
        plan_dict = plan.model_dump()
        
        assert plan_dict["intent"] == "update"
        assert plan_dict["entities"]["table"] == "users"
        assert plan_dict["confidence"] == 0.85
        assert plan_dict["requires_confirmation"] is False
        assert plan_dict["metadata"]["source"] == "user_input"

    def test_plan_json_serialization(self):
        """Test plan JSON serialization."""
        plan = ExecutionPlan(
            intent="create",
            entities={"resource": "deployment", "name": "webapp"},
            confidence=0.92,
        )

        # Test JSON serialization
        plan_json = json.dumps(plan.model_dump())
        parsed_plan = json.loads(plan_json)

        assert parsed_plan["intent"] == "create"
        assert parsed_plan["entities"]["resource"] == "deployment"
        assert parsed_plan["confidence"] == 0.92

    def test_plan_copy(self):
        """Test plan copying."""
        original = ExecutionPlan(
            intent="scale",
            entities={"deployment": "webapp", "replicas": "3"},
            metadata={"namespace": "default"},
        )

        copied = original.model_copy(deep=True)
        
        assert copied == original
        assert copied is not original  # Different objects
        assert copied.entities is not original.entities  # Different dict (deep copy)

    def test_plan_merge_entities(self):
        """Test merging entities into plan."""
        plan = ExecutionPlan(
            intent="select",
            entities={"table": "users"},
        )

        additional_entities = {"columns": ["id", "name"], "limit": "10"}
        merged_plan = plan.with_entities(additional_entities)

        assert merged_plan.intent == "select"
        assert merged_plan.entities["table"] == "users"
        assert merged_plan.entities["columns"] == ["id", "name"]
        assert merged_plan.entities["limit"] == "10"

    def test_plan_update_confidence(self):
        """Test updating plan confidence."""
        plan = ExecutionPlan(
            intent="find",
            entities={"pattern": "*.log"},
            confidence=0.7,
        )

        updated_plan = plan.with_confidence(0.95)
        
        assert updated_plan.confidence == 0.95
        assert updated_plan.intent == "find"
        assert updated_plan.entities == plan.entities

    def test_plan_add_metadata(self):
        """Test adding metadata to plan."""
        plan = ExecutionPlan(
            intent="run",
            entities={"image": "nginx"},
        )

        plan_with_metadata = plan.with_metadata({"port": "8080", "env": "prod"})
        
        assert plan_with_metadata.metadata["port"] == "8080"
        assert plan_with_metadata.metadata["env"] == "prod"

    def test_plan_validation(self):
        """Test plan validation."""
        # Valid plan
        valid_plan = ExecutionPlan(
            intent="select",
            entities={"table": "users"},
            confidence=0.8,
        )
        assert valid_plan.is_valid()

        # Invalid plan - missing intent
        invalid_plan = ExecutionPlan(
            intent="",
            entities={"table": "users"},
            confidence=0.8,
        )
        assert not invalid_plan.is_valid()

        # Invalid plan - confidence out of range
        invalid_confidence = ExecutionPlan(
            intent="select",
            entities={"table": "users"},
            confidence=1.5,  # > 1.0
        )
        assert not invalid_confidence.is_valid()

    def test_plan_equality(self):
        """Test plan equality."""
        plan1 = ExecutionPlan(
            intent="delete",
            entities={"table": "temp"},
            confidence=0.9,
        )

        plan2 = ExecutionPlan(
            intent="delete",
            entities={"table": "temp"},
            confidence=0.9,
        )

        plan3 = ExecutionPlan(
            intent="delete",
            entities={"table": "temp"},
            confidence=0.8,  # Different confidence
        )

        assert plan1 == plan2
        assert plan1 != plan3

    def test_plan_str_representation(self):
        """Test plan string representation."""
        plan = ExecutionPlan(
            intent="create",
            entities={"resource": "pod", "name": "webapp"},
            confidence=0.95,
        )

        plan_str = str(plan)
        
        assert "create" in plan_str
        assert "webapp" in plan_str
        assert "0.95" in plan_str

    def test_plan_with_complex_entities(self):
        """Test plan with complex nested entities."""
        complex_entities = {
            "filters": [
                {"field": "status", "operator": "=", "value": "active"},
                {"field": "created_at", "operator": ">", "value": "2023-01-01"}
            ],
            "ordering": [
                {"field": "created_at", "direction": "desc"},
                {"field": "name", "direction": "asc"}
            ],
            "pagination": {"offset": 0, "limit": 50}
        }

        plan = ExecutionPlan(
            intent="select",
            entities=complex_entities,
            confidence=0.88,
        )

        assert plan.entities["filters"][0]["field"] == "status"
        assert plan.entities["ordering"][1]["direction"] == "asc"
        assert plan.entities["pagination"]["limit"] == 50

    def test_plan_context_management(self):
        """Test plan context management."""
        base_plan = ExecutionPlan(
            intent="list",
            entities={"path": "/var/log"},
        )

        # Add context
        contextual_plan = base_plan.with_context({
            "user": "admin",
            "working_directory": "/home/user",
            "previous_command": "ls -la"
        })

        assert "context" in contextual_plan.metadata
        assert contextual_plan.metadata["context"]["user"] == "admin"

    def test_plan_error_handling(self):
        """Test plan error handling."""
        plan = ExecutionPlan(
            intent="invalid_operation",
            entities={},
            confidence=0.0,
        )

        # Add errors
        plan_with_errors = plan.with_errors([
            "Invalid operation specified",
            "Missing required parameters"
        ])

        assert "errors" in plan_with_errors.metadata
        assert len(plan_with_errors.metadata["errors"]) == 2

    def test_plan_performance_tracking(self):
        """Test plan performance tracking."""
        plan = ExecutionPlan(
            intent="search",
            entities={"pattern": "*.log"},
        )

        # Add performance metadata
        performance_plan = plan.with_performance({
            "generation_time_ms": 15.2,
            "confidence_calculation_ms": 2.1,
            "total_processing_ms": 17.3
        })

        assert "performance" in performance_plan.metadata
        assert performance_plan.metadata["performance"]["generation_time_ms"] == 15.2

    def test_plan_security_context(self):
        """Test plan security context."""
        plan = ExecutionPlan(
            intent="delete",
            entities={"table": "users"},
            requires_confirmation=True,
        )

        security_plan = plan.with_security({
            "risk_level": "high",
            "requires_approval": True,
            "audit_required": True
        })

        assert "security" in security_plan.metadata
        assert security_plan.metadata["security"]["risk_level"] == "high"
