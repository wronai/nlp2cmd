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
    Intent,
    Entity,
    NLPBackend,
    RuleBasedBackend,
    SpaCyBackend,
    LLMBackend,
)
from nlp2cmd.adapters import SQLAdapter, ShellAdapter


class TestIntent:
    """Test Intent dataclass."""

    def test_intent_creation(self):
        """Test intent creation."""
        intent = Intent(
            name="select",
            confidence=0.85,
            domain="sql",
        )

        assert intent.name == "select"
        assert intent.confidence == 0.85
        assert intent.domain == "sql"

    def test_intent_defaults(self):
        """Test intent default values."""
        intent = Intent(name="list")

        assert intent.name == "list"
        assert intent.confidence == 0.0
        assert intent.domain is None

    def test_intent_validation(self):
        """Test intent validation."""
        # Valid intent
        valid_intent = Intent(name="find", confidence=0.7)
        assert valid_intent.is_valid()

        # Invalid intent - empty name
        invalid_intent = Intent(name="", confidence=0.7)
        assert not invalid_intent.is_valid()

        # Invalid intent - confidence out of range
        invalid_confidence = Intent(name="test", confidence=1.5)
        assert not invalid_confidence.is_valid()

    def test_intent_str_representation(self):
        """Test intent string representation."""
        intent = Intent(
            name="create",
            confidence=0.92,
            domain="kubernetes",
        )

        intent_str = str(intent)
        assert "create" in intent_str
        assert "0.92" in intent_str
        assert "kubernetes" in intent_str


class TestEntity:
    """Test Entity dataclass."""

    def test_entity_creation(self):
        """Test entity creation."""
        entity = Entity(
            name="table",
            value="users",
            confidence=0.9,
            source="regex",
        )

        assert entity.name == "table"
        assert entity.value == "users"
        assert entity.confidence == 0.9
        assert entity.source == "regex"

    def test_entity_defaults(self):
        """Test entity default values."""
        entity = Entity(name="test", value="data")

        assert entity.name == "test"
        assert entity.value == "data"
        assert entity.confidence == 0.0
        assert entity.source is None

    def test_entity_with_metadata(self):
        """Test entity with metadata."""
        metadata = {
            "position": {"start": 10, "end": 15},
            "pattern": r"\b(\w+)\b",
            "context": "table name"
        }

        entity = Entity(
            name="table",
            value="users",
            metadata=metadata
        )

        assert entity.metadata["position"]["start"] == 10
        assert entity.metadata["pattern"] == r"\b(\w+)\b"

    def test_entity_validation(self):
        """Test entity validation."""
        # Valid entity
        valid_entity = Entity(name="port", value="8080", confidence=0.8)
        assert valid_entity.is_valid()

        # Invalid entity - empty name
        invalid_entity = Entity(name="", value="8080")
        assert not invalid_entity.is_valid()

        # Invalid entity - empty value
        invalid_entity = Entity(name="port", value="")
        assert not invalid_entity.is_valid()


class TestNLPBackend:
    """Test NLP backend abstract class."""

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        backend = NLPBackend()

        with pytest.raises(NotImplementedError):
            backend.extract_intent("test text")

        with pytest.raises(NotImplementedError):
            backend.extract_entities("test text")

        with pytest.raises(NotImplementedError):
            backend.generate_plan("test text")


class TestRuleBasedBackend:
    """Test rule-based NLP backend."""

    @pytest.fixture
    def backend(self):
        """Create rule-based backend instance."""
        return RuleBasedBackend()

    def test_extract_intent(self, backend):
        """Test intent extraction with rules."""
        # SQL intent
        intent = backend.extract_intent("Pokaż wszystkich użytkowników")
        assert intent.name == "select"
        assert intent.domain == "sql"
        assert intent.confidence > 0.5

        # Shell intent
        intent = backend.extract_intent("Znajdź pliki *.py")
        assert intent.name == "find"
        assert intent.domain == "shell"

    def test_extract_entities(self, backend):
        """Test entity extraction with rules."""
        entities = backend.extract_entities("Pokaż dane z tabeli users limit 10")
        
        # Should extract table and limit
        entity_names = [e.name for e in entities]
        assert "table" in entity_names
        assert "limit" in entity_names

    def test_generate_plan(self, backend):
        """Test plan generation."""
        plan = backend.generate_plan("Pokaż 10 użytkowników")
        
        assert plan.intent in ["select", "list"]
        assert plan.confidence > 0.0
        assert isinstance(plan.entities, dict)

    def test_unknown_input(self, backend):
        """Test handling of unknown input."""
        intent = backend.extract_intent("completely unrelated text")
        assert intent.name == "unknown"
        assert intent.confidence < 0.5

    def test_confidence_calculation(self, backend):
        """Test confidence calculation."""
        # High confidence for clear patterns
        intent1 = backend.extract_intent("SELECT * FROM users")
        assert intent1.confidence > 0.8

        # Lower confidence for ambiguous patterns
        intent2 = backend.extract_intent("show me something")
        assert intent2.confidence < 0.8


class TestNLP2CMD:
    """Test main NLP2CMD class."""

    @pytest.fixture
    def sql_nlp(self):
        """Create NLP2CMD instance with SQL adapter."""
        adapter = SQLAdapter()
        return NLP2CMD(adapter=adapter)

    @pytest.fixture
    def shell_nlp(self):
        """Create NLP2CMD instance with Shell adapter."""
        adapter = ShellAdapter()
        return NLP2CMD(adapter=adapter)

    def test_dsl_name(self, sql_nlp):
        """Test DSL name property."""
        assert sql_nlp.dsl_name == "sql"

    def test_transform_basic(self, sql_nlp):
        """Test basic transformation."""
        result = sql_nlp.transform("Pokaż użytkowników")
        
        assert isinstance(result, TransformResult)
        assert result.dsl_type == "sql"
        assert result.command is not None

    def test_context_management(self, sql_nlp):
        """Test context setting and clearing."""
        # Set context
        sql_nlp.set_context({"default_table": "users"})
        
        # Transform with context
        result = sql_nlp.transform("Pokaż wszystkie dane")
        assert result.is_success
        
        # Clear context
        sql_nlp.clear_context()
        
        # Transform without context
        result2 = sql_nlp.transform("Pokaż wszystkie dane")
        assert isinstance(result2, TransformResult)

    def test_history_tracking(self, sql_nlp):
        """Test transformation history."""
        # Perform multiple transformations
        sql_nlp.transform("SELECT * FROM users")
        sql_nlp.transform("SELECT * FROM orders")
        sql_nlp.transform("SELECT COUNT(*) FROM products")
        
        history = sql_nlp.get_history()
        assert len(history) == 3
        assert all(isinstance(h, TransformResult) for h in history)

    def test_transform_with_context(self, sql_nlp):
        """Test transformation with context."""
        context = {
            "previous_query": "SELECT * FROM users",
            "user_preferences": {"limit_default": 10}
        }
        
        result = sql_nlp.transform("Pokaż więcej", context=context)
        assert isinstance(result, TransformResult)

    def test_transform_blocked_by_safety(self, sql_nlp):
        """Test transformation blocked by safety policy."""
        result = sql_nlp.transform("DROP TABLE users")
        
        assert result.status == TransformStatus.BLOCKED
        assert result.is_blocked
        assert len(result.errors) > 0

    def test_transform_with_validator(self, sql_nlp):
        """Test transformation with validator."""
        # This would require a validator setup
        result = sql_nlp.transform("SELECT * FROM users")
        assert isinstance(result, TransformResult)

    def test_different_backends(self):
        """Test with different NLP backends."""
        # Test with rule-based backend
        rule_backend = RuleBasedBackend()
        adapter = SQLAdapter()
        nlp_rule = NLP2CMD(adapter=adapter, backend=rule_backend)
        
        result = nlp_rule.transform("Pokaż użytkowników")
        assert result.is_success

    def test_confidence_threshold(self, sql_nlp):
        """Test confidence threshold filtering."""
        # Set high confidence threshold
        sql_nlp.confidence_threshold = 0.9
        
        result = sql_nlp.transform("ambiguous query")
        # Should handle low confidence appropriately
        assert isinstance(result, TransformResult)

    def test_multiple_adapters(self):
        """Test with multiple adapters."""
        # This would require adapter registry or similar
        pass  # Implementation depends on adapter management system

    def test_error_handling(self, sql_nlp):
        """Test error handling in transformation."""
        # Test with malformed input
        result = sql_nlp.transform("")
        assert isinstance(result, TransformResult)
        
        # Test with None input
        with pytest.raises((TypeError, ValueError)):
            sql_nlp.transform(None)

    def test_performance_monitoring(self, sql_nlp):
        """Test performance monitoring."""
        import time
        
        start_time = time.time()
        result = sql_nlp.transform("SELECT * FROM users WHERE id = 1")
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert result.is_success
        assert processing_time < 1000  # Should complete within 1 second


class TestIntegrationFlows:
    """Test end-to-end integration flows."""

    @pytest.fixture
    def nlp_instance(self):
        """Create NLP2CMD instance for integration tests."""
        adapter = SQLAdapter()
        backend = RuleBasedBackend()
        return NLP2CMD(adapter=adapter, backend=backend)

    def test_sql_select_flow(self, nlp_instance):
        """Test complete SELECT flow."""
        result = nlp_instance.transform("Pokaż wszystkich użytkowników z tabeli users")
        
        assert result.is_success
        assert "SELECT" in result.command.upper()
        assert "users" in result.command.upper()

    def test_shell_find_flow(self, nlp_instance):
        """Test complete find command flow."""
        # Would need shell adapter for this test
        pass  # Implementation depends on adapter setup

    def test_docker_run_flow(self, nlp_instance):
        """Test complete docker run flow."""
        # Would need docker adapter for this test
        pass  # Implementation depends on adapter setup

    def test_kubernetes_get_flow(self, nlp_instance):
        """Test complete kubectl get flow."""
        # Would need kubernetes adapter for this test
        pass  # Implementation depends on adapter setup

    def test_error_recovery_flow(self, nlp_instance):
        """Test error recovery and fallback mechanisms."""
        # Test with problematic input
        result = nlp_instance.transform("invalid sql syntax")
        
        # Should handle gracefully
        assert isinstance(result, TransformResult)
        if not result.is_success:
            assert len(result.errors) > 0

    def test_context_preservation_flow(self, nlp_instance):
        """Test context preservation across transformations."""
        # Set initial context
        nlp_instance.set_context({"user_role": "admin"})
        
        # Transform with context
        result1 = nlp_instance.transform("Pokaż dane")
        
        # Transform again, context should be preserved
        result2 = nlp_instance.transform("Pokaż więcej")
        
        assert result1.is_success
        assert result2.is_success

    def test_batch_processing_flow(self, nlp_instance):
        """Test batch processing of multiple queries."""
        queries = [
            "SELECT * FROM users",
            "SELECT * FROM orders",
            "SELECT COUNT(*) FROM products"
        ]
        
        results = []
        for query in queries:
            result = nlp_instance.transform(query)
            results.append(result)
        
        assert len(results) == 3
        assert all(r.is_success for r in results)

    def test_concurrent_processing(self, nlp_instance):
        """Test concurrent processing capabilities."""
        import threading
        import time
        
        results = []
        errors = []
        
        def transform_query(query):
            try:
                result = nlp_instance.transform(query)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        queries = ["SELECT 1", "SELECT 2", "SELECT 3"] * 5
        threads = []
        
        for query in queries:
            thread = threading.Thread(target=transform_query, args=(query,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == len(queries)
