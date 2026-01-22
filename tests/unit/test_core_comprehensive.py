"""
Comprehensive unit tests for NLP2CMD core module.
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

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = TransformResult(
            status=TransformStatus.SUCCESS,
            command="SELECT 1;",
            plan=ExecutionPlan(intent="select", entities={}),
            confidence=1.0,
            dsl_type="sql",
            warnings=["Test warning"],
        )

        data = result.to_dict()

        assert data["status"] == "success"
        assert data["command"] == "SELECT 1;"
        assert data["confidence"] == 1.0
        assert "Test warning" in data["warnings"]

    def test_partial_status_with_warnings(self):
        """Test partial success with warnings."""
        result = TransformResult(
            status=TransformStatus.PARTIAL,
            command="UPDATE users SET status = 'active';",
            plan=ExecutionPlan(intent="update", entities={}),
            confidence=0.7,
            dsl_type="sql",
            warnings=["UPDATE without WHERE affects all rows"],
        )

        assert not result.is_success
        assert not result.is_blocked
        assert len(result.warnings) == 1


class TestExecutionPlan:
    """Tests for ExecutionPlan model."""

    def test_basic_plan(self):
        """Test basic execution plan."""
        plan = ExecutionPlan(
            intent="select",
            entities={"table": "users", "columns": ["id", "name"]},
            confidence=0.9,
        )

        assert plan.intent == "select"
        assert plan.entities["table"] == "users"
        assert plan.confidence == 0.9
        assert not plan.requires_confirmation

    def test_plan_with_confirmation(self):
        """Test plan requiring confirmation."""
        plan = ExecutionPlan(
            intent="delete",
            entities={"table": "users"},
            confidence=0.85,
            requires_confirmation=True,
        )

        assert plan.requires_confirmation

    def test_plan_serialization(self):
        """Test plan model_dump."""
        plan = ExecutionPlan(
            intent="insert",
            entities={"table": "users", "values": {"name": "John"}},
            confidence=0.95,
            metadata={"source": "test"},
        )

        data = plan.model_dump()

        assert data["intent"] == "insert"
        assert data["entities"]["values"]["name"] == "John"
        assert data["metadata"]["source"] == "test"


class TestIntent:
    """Tests for Intent model."""

    def test_intent_creation(self):
        """Test intent creation."""
        intent = Intent(
            name="select",
            patterns=["show", "display", "get"],
            required_entities=["table"],
            optional_entities=["columns", "filters"],
        )

        assert intent.name == "select"
        assert "show" in intent.patterns
        assert "table" in intent.required_entities

    def test_intent_confidence_threshold(self):
        """Test intent confidence threshold."""
        intent = Intent(
            name="delete",
            patterns=["remove", "delete"],
            confidence_threshold=0.9,
        )

        assert intent.confidence_threshold == 0.9


class TestEntity:
    """Tests for Entity model."""

    def test_entity_creation(self):
        """Test entity creation."""
        entity = Entity(
            name="table",
            value="users",
            type="identifier",
            start=10,
            end=15,
            confidence=0.95,
        )

        assert entity.name == "table"
        assert entity.value == "users"
        assert entity.confidence == 0.95


class TestRuleBasedBackend:
    """Tests for RuleBasedBackend."""

    def test_extract_intent_match(self):
        """Test intent extraction with matching pattern."""
        backend = RuleBasedBackend(
            rules={
                "select": ["show", "display", "get", "find"],
                "delete": ["remove", "delete"],
            }
        )

        intent, confidence = backend.extract_intent("Show all users")

        assert intent == "select"
        assert confidence > 0

    def test_extract_intent_no_match(self):
        """Test intent extraction with no matching pattern."""
        backend = RuleBasedBackend(rules={"select": ["show"]})

        intent, confidence = backend.extract_intent("Something random")

        assert intent == "unknown"
        assert confidence == 0.0

    def test_empty_rules(self):
        """Test with empty rules."""
        backend = RuleBasedBackend()

        intent, confidence = backend.extract_intent("Any text")

        assert intent == "unknown"


class TestNLP2CMD:
    """Tests for main NLP2CMD class."""

    @pytest.fixture
    def sql_nlp(self):
        """Create NLP2CMD with SQL adapter."""
        adapter = SQLAdapter(dialect="postgresql")
        return NLP2CMD(adapter=adapter)

    @pytest.fixture
    def shell_nlp(self):
        """Create NLP2CMD with Shell adapter."""
        adapter = ShellAdapter(shell_type="bash")
        return NLP2CMD(adapter=adapter)

    def test_dsl_name(self, sql_nlp):
        """Test DSL name property."""
        assert sql_nlp.dsl_name == "sql"

    def test_transform_basic(self, sql_nlp):
        """Test basic transformation."""
        # Mock the NLP backend to return a known plan
        sql_nlp.nlp_backend = Mock()
        sql_nlp.nlp_backend.extract_intent.return_value = ("select", 0.9)
        sql_nlp.nlp_backend.extract_entities.return_value = [
            Entity(name="table", value="users", type="identifier")
        ]

        result = sql_nlp.transform("Show all users")

        assert result.dsl_type == "sql"
        assert result.command  # Some command was generated

    def test_context_management(self, sql_nlp):
        """Test context setting and clearing."""
        sql_nlp.set_context("database", "test_db")
        sql_nlp.set_context("schema", "public")

        assert sql_nlp._context["database"] == "test_db"
        assert sql_nlp._context["schema"] == "public"

        sql_nlp.clear_context()

        assert len(sql_nlp._context) == 0

    def test_history_tracking(self, sql_nlp):
        """Test transformation history."""
        # Perform some transformations
        sql_nlp.nlp_backend = Mock()
        sql_nlp.nlp_backend.extract_intent.return_value = ("select", 0.9)
        sql_nlp.nlp_backend.extract_entities.return_value = []

        sql_nlp.transform("Query 1")
        sql_nlp.transform("Query 2")

        history = sql_nlp.get_history()

        assert len(history) == 2

        sql_nlp.clear_history()

        assert len(sql_nlp.get_history()) == 0

    def test_transform_with_context(self, sql_nlp):
        """Test transformation with context."""
        sql_nlp.nlp_backend = Mock()
        sql_nlp.nlp_backend.extract_intent.return_value = ("select", 0.9)
        sql_nlp.nlp_backend.extract_entities.return_value = []

        sql_nlp.set_context("default_table", "users")

        result = sql_nlp.transform(
            "Show records",
            context={"limit": 10}
        )

        assert result is not None

    def test_transform_blocked_by_safety(self):
        """Test transformation blocked by safety policy."""
        from nlp2cmd.adapters import SQLSafetyPolicy

        adapter = SQLAdapter(
            dialect="postgresql",
            safety_policy=SQLSafetyPolicy(allow_delete=False)
        )
        nlp = NLP2CMD(adapter=adapter)

        # Mock to generate a DELETE command
        nlp.nlp_backend = Mock()
        nlp.nlp_backend.extract_intent.return_value = ("delete", 0.9)
        nlp.nlp_backend.extract_entities.return_value = []

        # Force the adapter to generate DELETE
        with patch.object(adapter, 'generate', return_value="DELETE FROM users;"):
            result = nlp.transform("Delete all users")

        assert result.is_blocked

    def test_transform_with_validator(self, sql_nlp):
        """Test transformation with validator."""
        from nlp2cmd.validators import SQLValidator

        sql_nlp.validator = SQLValidator()
        sql_nlp.nlp_backend = Mock()
        sql_nlp.nlp_backend.extract_intent.return_value = ("select", 0.9)
        sql_nlp.nlp_backend.extract_entities.return_value = []

        result = sql_nlp.transform("Show users")

        # Validator should have been called
        assert result is not None


class TestNLP2CMDWithDifferentBackends:
    """Tests for NLP2CMD with different NLP backends."""

    def test_with_rule_based_backend(self):
        """Test with rule-based backend."""
        backend = RuleBasedBackend(
            rules={
                "select": ["show", "get", "find"],
                "insert": ["add", "create"],
            }
        )

        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

        result = nlp.transform("Show all users")

        assert result is not None
        assert result.dsl_type == "sql"

    @pytest.mark.skipif(True, reason="Requires spaCy model")
    def test_with_spacy_backend(self):
        """Test with spaCy backend."""
        backend = SpaCyBackend(model="en_core_web_sm")
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

        result = nlp.transform("Show users from New York")

        assert result is not None

    @pytest.mark.skipif(True, reason="Requires API key")
    def test_with_llm_backend(self):
        """Test with LLM backend."""
        backend = LLMBackend(
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

        # Would require actual API call
        pass


class TestNLP2CMDIntegration:
    """Integration tests for NLP2CMD."""

    def test_sql_select_flow(self):
        """Test complete SELECT flow."""
        adapter = SQLAdapter(
            dialect="postgresql",
            schema_context={
                "tables": ["users", "orders"],
                "columns": {
                    "users": ["id", "name", "email"],
                    "orders": ["id", "user_id", "total"],
                }
            }
        )

        nlp = NLP2CMD(adapter=adapter)

        # Use direct plan for predictable output
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*",
                "filters": [
                    {"field": "name", "operator": "LIKE", "value": "%John%"}
                ]
            }
        }

        command = adapter.generate(plan)

        assert "SELECT" in command
        assert "FROM users" in command
        assert "LIKE" in command

    def test_shell_find_flow(self):
        """Test complete find command flow."""
        adapter = ShellAdapter(shell_type="bash")
        nlp = NLP2CMD(adapter=adapter)

        plan = {
            "intent": "file_search",
            "entities": {
                "target": "files",
                "filters": [
                    {"attribute": "size", "operator": ">", "value": "100M"}
                ]
            }
        }

        command = adapter.generate(plan)

        assert "find" in command
        assert "-size" in command
        assert "100M" in command

    def test_docker_run_flow(self):
        """Test complete docker run flow."""
        from nlp2cmd.adapters import DockerAdapter

        adapter = DockerAdapter()
        nlp = NLP2CMD(adapter=adapter)

        plan = {
            "intent": "container_run",
            "entities": {
                "image": "nginx",
                "name": "web",
                "ports": ["8080:80"],
                "detach": True
            }
        }

        command = adapter.generate(plan)

        assert "docker run" in command
        assert "-d" in command
        assert "nginx" in command

    def test_kubernetes_get_flow(self):
        """Test complete kubectl get flow."""
        from nlp2cmd.adapters import KubernetesAdapter

        adapter = KubernetesAdapter()
        nlp = NLP2CMD(adapter=adapter)

        plan = {
            "intent": "get",
            "entities": {
                "resource_type": "pods",
                "namespace": "default"
            }
        }

        command = adapter.generate(plan)

        assert "kubectl get pods" in command
        assert "-n default" in command


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_input(self):
        """Test with empty input."""
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter)

        result = nlp.transform("")

        assert result is not None

    def test_very_long_input(self):
        """Test with very long input."""
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter)

        long_input = "Show " + "users " * 1000

        result = nlp.transform(long_input)

        assert result is not None

    def test_special_characters_in_input(self):
        """Test with special characters."""
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter)

        result = nlp.transform("Show users with name = 'O'Brien'")

        assert result is not None

    def test_unicode_input(self):
        """Test with Unicode characters."""
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter)

        result = nlp.transform("Pokaż użytkowników z Warszawy")

        assert result is not None

    def test_nlp_backend_error_handling(self):
        """Test error handling when NLP backend fails."""
        adapter = SQLAdapter(dialect="postgresql")
        nlp = NLP2CMD(adapter=adapter)

        # Mock backend to raise exception
        nlp.nlp_backend = Mock()
        nlp.nlp_backend.extract_intent.side_effect = Exception("NLP Error")

        result = nlp.transform("Test query")

        assert result.status == TransformStatus.FAILED
        assert len(result.errors) > 0
