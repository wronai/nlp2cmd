"""
Test TransformResult functionality.

This module tests transformation result creation, status handling,
error management, and result serialization.
"""

import pytest
from dataclasses import asdict
import json

from nlp2cmd.core import (
    TransformResult,
    TransformStatus,
    ExecutionPlan,
)


class TestTransformResult:
    """Tests for TransformResult dataclass."""

    def test_success_status(self):
        """Test successful transformation result."""
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT * FROM users;",
            plan=ExecutionPlan(intent="select", entities={"table": "users"}),
            confidence=0.95,
            dsl_type="sql",
        )

        assert result.is_success
        assert not result.is_blocked
        assert result.confidence == 0.95
        assert result.command == "SELECT * FROM users;"
        assert result.dsl_type == "sql"

    def test_blocked_status(self):
        """Test blocked transformation result."""
        result = TransformResult(
            status=TransformStatus.BLOCKED,
            command="DELETE FROM users;",
            plan=ExecutionPlan(intent="delete", entities={}),
            confidence=0.0,
            dsl_type="sql",
            errors=["DELETE operations are disabled"],
        )

        assert not result.is_success
        assert result.is_blocked
        assert len(result.errors) == 1
        assert "DELETE operations are disabled" in result.errors[0]

    def test_partial_status_with_warnings(self):
        """Test partial success with warnings."""
        result = TransformResult(
            status=TransformStatus.PARTIAL,
            command="UPDATE users SET status = 'active' WHERE id = 1;",
            plan=ExecutionPlan(intent="update", entities={"table": "users"}),
            confidence=0.7,
            dsl_type="sql",
            warnings=["No WHERE clause specified for safety"],
        )

        assert result.is_success  # Partial still counts as success
        assert not result.is_blocked
        assert result.confidence == 0.7
        assert len(result.warnings) == 1
        assert "WHERE clause" in result.warnings[0]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT 1;",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.8,
            dsl_type="sql",
        )

        result_dict = asdict(result)
        
        assert result_dict["status"] == TransformStatus.SUCCESS
        assert result_dict["command"] == "SELECT 1;"
        assert result_dict["confidence"] == 0.8
        assert result_dict["dsl_type"] == "sql"
        assert "plan" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict

    def test_json_serialization(self):
        """Test JSON serialization."""
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="docker run nginx",
            plan=ExecutionPlan(intent="run", entities={"image": "nginx"}),
            confidence=0.9,
            dsl_type="docker",
        )

        # Convert to JSON
        result_json = json.dumps(asdict(result), default=str)
        parsed_result = json.loads(result_json)

        assert parsed_result["status"] == "success"
        assert parsed_result["command"] == "docker run nginx"
        assert parsed_result["confidence"] == 0.9

    def test_error_handling(self):
        """Test error handling in results."""
        errors = [
            "Invalid syntax in query",
            "Table not found: users",
            "Permission denied"
        ]

        result = TransformResult(
            status=TransformStatus.ERROR,
            command="",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.0,
            dsl_type="sql",
            errors=errors,
        )

        assert not result.is_success
        assert len(result.errors) == 3
        assert "Invalid syntax" in result.errors[0]
        assert "Permission denied" in result.errors[2]

    def test_warning_accumulation(self):
        """Test warning accumulation."""
        warnings = [
            "Query may be slow without index",
            "Consider adding LIMIT clause",
            "Using deprecated syntax"
        ]

        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT * FROM large_table",
            plan=ExecutionPlan(intent="select", entities={"table": "large_table"}),
            confidence=0.6,
            dsl_type="sql",
            warnings=warnings,
        )

        assert result.is_success
        assert len(result.warnings) == 3
        assert "slow without index" in result.warnings[0]

    def test_result_with_metadata(self):
        """Test result with additional metadata."""
        metadata = {
            "processing_time_ms": 25.5,
            "model_used": "gpt-4",
            "tokens_consumed": 150,
            "cache_hit": False
        }

        plan = ExecutionPlan(
            intent="list",
            entities={"path": "/home"},
            metadata=metadata
        )

        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="ls /home",
            plan=plan,
            confidence=0.85,
            dsl_type="shell",
        )

        assert "processing_time_ms" in result.plan.metadata
        assert result.plan.metadata["model_used"] == "gpt-4"

    def test_result_copy(self):
        """Test result copying."""
        original = TransformResult(
            status=TransformStatus.SUCCESS,
            command="kubectl get pods",
            plan=ExecutionPlan(intent="get", entities={"resource": "pods"}),
            confidence=0.92,
            dsl_type="kubernetes",
            warnings=["Using default namespace"],
        )

        copied = original.copy()
        
        assert copied == original
        assert copied is not original  # Different objects
        assert copied.plan is not original.plan  # Different plan objects

    def test_result_status_transitions(self):
        """Test various status transitions."""
        statuses = [
            TransformStatus.SUCCESS,
            TransformStatus.PARTIAL,
            TransformStatus.BLOCKED,
            TransformStatus.ERROR,
        ]

        for status in statuses:
            result = TransformResult(
                status=status,
                command="test command",
                plan=ExecutionPlan(intent="test", entities={}),
                confidence=0.5,
                dsl_type="test",
            )

            assert result.status == status
            assert result.command == "test command"

    def test_result_validation(self):
        """Test result validation."""
        # Valid result
        valid_result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT * FROM users",
            plan=ExecutionPlan(intent="select", entities={"table": "users"}),
            confidence=0.8,
            dsl_type="sql",
        )
        assert valid_result.is_valid()

        # Invalid result - empty command with success status
        invalid_result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.8,
            dsl_type="sql",
        )
        assert not invalid_result.is_valid()

        # Invalid result - confidence out of range
        invalid_confidence = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT 1",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=1.5,  # > 1.0
            dsl_type="sql",
        )
        assert not invalid_confidence.is_valid()
        
        # Invalid result - SUCCESS status but with errors
        result_with_errors = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT 1",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.8,
            dsl_type="sql",
            errors=["syntax error"]
        )
        assert not result_with_errors.is_valid()
        
        # Invalid result - ERROR status
        error_result = TransformResult(
            status=TransformStatus.ERROR,
            command="SELECT 1",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.8,
            dsl_type="sql",
        )
        assert not error_result.is_valid()

    def test_result_equality(self):
        """Test result equality."""
        result1 = TransformResult(
            status=TransformStatus.SUCCESS,
            command="docker ps",
            plan=ExecutionPlan(intent="list", entities={}),
            confidence=0.9,
            dsl_type="docker",
        )

        result2 = TransformResult(
            status=TransformStatus.SUCCESS,
            command="docker ps",
            plan=ExecutionPlan(intent="list", entities={}),
            confidence=0.9,
            dsl_type="docker",
        )

        result3 = TransformResult(
            status=TransformStatus.SUCCESS,
            command="docker ps",
            plan=ExecutionPlan(intent="list", entities={}),
            confidence=0.8,  # Different confidence
            dsl_type="docker",
        )

        assert result1 == result2
        assert result1 != result3

    def test_result_str_representation(self):
        """Test result string representation."""
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="find /home -name '*.log'",
            plan=ExecutionPlan(intent="find", entities={"path": "/home", "pattern": "*.log"}),
            confidence=0.88,
            dsl_type="shell",
        )

        result_str = str(result)
        
        assert "SUCCESS" in result_str
        assert "find /home" in result_str
        assert "0.88" in result_str

    def test_result_with_complex_errors(self):
        """Test result with complex error structure."""
        complex_errors = [
            {
                "type": "syntax_error",
                "message": "Unexpected token at line 5",
                "line": 5,
                "column": 12,
                "suggestion": "Check for missing comma"
            },
            {
                "type": "validation_error",
                "message": "Invalid table reference",
                "table": "nonexistent_table",
                "suggestion": "Use valid table name"
            }
        ]

        result = TransformResult(
            status=TransformStatus.ERROR,
            command="",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=0.0,
            dsl_type="sql",
            errors=[str(error) for error in complex_errors],
        )

        assert not result.is_success
        assert len(result.errors) == 2
        assert "syntax_error" in result.errors[0]
        assert "validation_error" in result.errors[1]

    def test_result_aggregation(self):
        """Test result aggregation from multiple sources."""
        results = [
            TransformResult(
                status=TransformStatus.SUCCESS,
                command="SELECT id FROM users",
                plan=ExecutionPlan(intent="select", entities={"table": "users", "columns": ["id"]}),
                confidence=0.9,
                dsl_type="sql",
            ),
            TransformResult(
                status=TransformStatus.SUCCESS,
                command="SELECT name FROM users",
                plan=ExecutionPlan(intent="select", entities={"table": "users", "columns": ["name"]}),
                confidence=0.85,
                dsl_type="sql",
            ),
        ]

        # Aggregate results (simplified example)
        best_result = max(results, key=lambda r: r.confidence)
        
        assert best_result.confidence == 0.9
        assert "SELECT id FROM users" in best_result.command

    def test_result_with_timing_info(self):
        """Test result with timing information."""
        timing_metadata = {
            "nlp_processing_ms": 12.5,
            "plan_generation_ms": 3.2,
            "command_generation_ms": 8.7,
            "total_ms": 24.4
        }

        plan = ExecutionPlan(
            intent="list",
            entities={"path": "/tmp"},
            metadata=timing_metadata
        )

        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="ls /tmp",
            plan=plan,
            confidence=0.95,
            dsl_type="shell",
        )

        assert "nlp_processing_ms" in result.plan.metadata
        assert result.plan.metadata["total_ms"] == 24.4
