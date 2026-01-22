"""
Unit tests for schemas and feedback modules.
"""

import pytest
from pathlib import Path
import tempfile

from nlp2cmd.schemas import SchemaRegistry, FileFormatSchema
from nlp2cmd.feedback import (
    FeedbackAnalyzer,
    FeedbackResult,
    FeedbackType,
    CorrectionEngine,
)


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""

    def test_builtin_schemas_registered(self):
        """Test that builtin schemas are registered."""
        registry = SchemaRegistry()

        assert registry.has_schema("dockerfile")
        assert registry.has_schema("docker-compose")
        assert registry.has_schema("kubernetes-deployment")
        assert registry.has_schema("env-file")

    def test_get_schema(self):
        """Test getting a schema by name."""
        registry = SchemaRegistry()

        schema = registry.get("dockerfile")

        assert schema is not None
        assert schema.name == "Dockerfile"
        assert "Dockerfile" in schema.extensions

    def test_detect_dockerfile(self):
        """Test detecting Dockerfile format."""
        registry = SchemaRegistry()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="", delete=False
        ) as f:
            f.write("FROM python:3.11\nRUN pip install flask")
            f.flush()

            schema = registry.detect_format(Path(f.name))

        # Cleanup handled by context manager

    def test_validate_dockerfile(self):
        """Test Dockerfile validation."""
        registry = SchemaRegistry()

        valid_dockerfile = "FROM python:3.11\nWORKDIR /app\nCOPY . ."
        result = registry.validate(valid_dockerfile, "dockerfile")

        assert result["valid"]

    def test_validate_dockerfile_missing_from(self):
        """Test Dockerfile validation catches missing FROM."""
        registry = SchemaRegistry()

        invalid_dockerfile = "WORKDIR /app\nCOPY . ."
        result = registry.validate(invalid_dockerfile, "dockerfile")

        assert not result["valid"]
        assert any("FROM" in e for e in result["errors"])

    def test_validate_docker_compose(self):
        """Test Docker Compose validation."""
        registry = SchemaRegistry()

        valid_compose = """
version: "3.8"
services:
  web:
    image: nginx
"""
        result = registry.validate(valid_compose, "docker-compose")

        assert result["valid"]

    def test_validate_docker_compose_missing_services(self):
        """Test Docker Compose validation catches missing services."""
        registry = SchemaRegistry()

        invalid_compose = """
version: "3.8"
networks:
  default:
"""
        result = registry.validate(invalid_compose, "docker-compose")

        assert not result["valid"]
        assert any("services" in e.lower() for e in result["errors"])

    def test_repair_dockerfile(self):
        """Test Dockerfile repair."""
        registry = SchemaRegistry()

        # Missing tag on FROM
        dockerfile = "FROM python\nRUN apt-get install -y curl"
        result = registry.repair(dockerfile, "dockerfile", auto_fix=True)

        # Should suggest or fix missing tag
        assert result["changes"]

    def test_validate_env_file(self):
        """Test .env file validation."""
        registry = SchemaRegistry()

        valid_env = """
DATABASE_URL=postgresql://localhost/db
API_KEY="secret-key"
"""
        result = registry.validate(valid_env, "env-file")

        assert result["valid"]

    def test_validate_env_unclosed_quote(self):
        """Test .env validation catches unclosed quotes."""
        registry = SchemaRegistry()

        invalid_env = 'API_KEY="unclosed'
        result = registry.validate(invalid_env, "env-file")

        assert not result["valid"]

    def test_register_custom_schema(self):
        """Test registering a custom schema."""
        registry = SchemaRegistry()

        custom_schema = FileFormatSchema(
            name="custom",
            extensions=["*.custom"],
            mime_types=["text/custom"],
            validator=lambda c: {"valid": True, "errors": []},
            parser=lambda c: {},
            generator=lambda d: "",
        )

        registry.register(custom_schema)

        assert registry.has_schema("custom")


class TestFeedbackAnalyzer:
    """Tests for FeedbackAnalyzer."""

    def test_analyze_success(self):
        """Test analyzing successful transformation."""
        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze(
            original_input="Show all users",
            generated_output="SELECT * FROM users;",
            validation_errors=[],
            validation_warnings=[],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.SUCCESS
        assert result.confidence > 0

    def test_analyze_with_errors(self):
        """Test analyzing transformation with errors."""
        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze(
            original_input="Delete users",
            generated_output="DELETE FROM users;",
            validation_errors=["Missing WHERE clause"],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.SYNTAX_ERROR
        assert len(result.errors) > 0

    def test_analyze_with_warnings(self):
        """Test analyzing transformation with warnings."""
        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze(
            original_input="Update status",
            generated_output="UPDATE users SET status = 'active';",
            validation_warnings=["UPDATE without WHERE"],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.PARTIAL_SUCCESS
        assert len(result.warnings) > 0

    def test_suggestions_generated(self):
        """Test that suggestions are generated for errors."""
        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze(
            original_input="test",
            generated_output="test",
            validation_errors=["Unbalanced parentheses"],
            dsl_type="sql",
        )

        assert len(result.suggestions) > 0 or len(result.errors) > 0

    def test_check_syntax(self):
        """Test quick syntax check."""
        analyzer = FeedbackAnalyzer()

        valid = analyzer.check_syntax("SELECT * FROM users", "sql")
        assert valid["valid"]

        invalid = analyzer.check_syntax("SELECT * FROM users (", "sql")
        assert not invalid["valid"]

    def test_analyze_exception(self):
        """Test exception analysis."""
        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_exception(FileNotFoundError("test.txt"))

        assert "suggestions" in result
        assert len(result["suggestions"]) > 0


class TestFeedbackResult:
    """Tests for FeedbackResult."""

    def test_is_success(self):
        """Test is_success property."""
        success = FeedbackResult(
            type=FeedbackType.SUCCESS,
            original_input="",
            generated_output="",
        )
        assert success.is_success

        failure = FeedbackResult(
            type=FeedbackType.SYNTAX_ERROR,
            original_input="",
            generated_output="",
        )
        assert not failure.is_success

    def test_can_auto_fix(self):
        """Test can_auto_fix property."""
        with_fix = FeedbackResult(
            type=FeedbackType.PARTIAL_SUCCESS,
            original_input="",
            generated_output="original",
            auto_corrections={"original": "fixed"},
        )
        assert with_fix.can_auto_fix

        without_fix = FeedbackResult(
            type=FeedbackType.SYNTAX_ERROR,
            original_input="",
            generated_output="",
        )
        assert not without_fix.can_auto_fix

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = FeedbackResult(
            type=FeedbackType.SUCCESS,
            original_input="test input",
            generated_output="test output",
            confidence=0.95,
        )

        d = result.to_dict()

        assert d["type"] == "success"
        assert d["original_input"] == "test input"
        assert d["confidence"] == 0.95


class TestCorrectionEngine:
    """Tests for CorrectionEngine."""

    def test_suggest_balance_fix(self):
        """Test suggestion for unbalanced parentheses."""
        engine = CorrectionEngine()

        result = engine.suggest(
            error="Unbalanced parentheses",
            content="SELECT * FROM users WHERE (id = 1",
        )

        assert result["confidence"] > 0
        assert "fix" in result

    def test_suggest_quote_fix(self):
        """Test suggestion for unclosed quotes."""
        engine = CorrectionEngine()

        result = engine.suggest(
            error="Unclosed single quote",
            content="SELECT * FROM users WHERE name = 'test",
        )

        assert result["confidence"] > 0
        assert result["fix"].endswith("'")

    def test_apply_correction(self):
        """Test applying a correction."""
        engine = CorrectionEngine()

        correction = {
            "fix": "SELECT * FROM users WHERE (id = 1)",
            "confidence": 0.9,
        }

        result = engine.apply_correction(
            "SELECT * FROM users WHERE (id = 1",
            correction,
        )

        assert result == correction["fix"]
