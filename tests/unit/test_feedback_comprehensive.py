"""
Comprehensive unit tests for NLP2CMD feedback module.
"""

import pytest

from nlp2cmd.feedback import (
    FeedbackType,
    FeedbackResult,
    FeedbackAnalyzer,
    CorrectionEngine,
    CorrectionRule,
)


class TestFeedbackType:
    """Tests for FeedbackType enum."""

    def test_all_types_exist(self):
        """Test all feedback types exist."""
        assert FeedbackType.SUCCESS
        assert FeedbackType.SYNTAX_ERROR
        assert FeedbackType.SCHEMA_MISMATCH
        assert FeedbackType.RUNTIME_ERROR
        assert FeedbackType.AMBIGUOUS_INPUT
        assert FeedbackType.PARTIAL_SUCCESS
        assert FeedbackType.SECURITY_VIOLATION

    def test_type_values(self):
        """Test feedback type values."""
        assert FeedbackType.SUCCESS.value == "success"
        assert FeedbackType.SYNTAX_ERROR.value == "syntax_error"


class TestFeedbackResult:
    """Tests for FeedbackResult dataclass."""

    def test_success_result(self):
        """Test successful feedback result."""
        result = FeedbackResult(
            type=FeedbackType.SUCCESS,
            original_input="Show users",
            generated_output="SELECT * FROM users;",
            confidence=0.95,
        )

        assert result.is_success
        assert not result.can_auto_fix
        assert result.confidence == 0.95

    def test_result_with_errors(self):
        """Test feedback result with errors."""
        result = FeedbackResult(
            type=FeedbackType.SYNTAX_ERROR,
            original_input="Show",
            generated_output="SELECT",
            errors=["Incomplete query", "Missing table"],
            confidence=0.0,
        )

        assert not result.is_success
        assert len(result.errors) == 2

    def test_result_with_auto_corrections(self):
        """Test feedback result with auto-corrections."""
        result = FeedbackResult(
            type=FeedbackType.PARTIAL_SUCCESS,
            original_input="Delet users",
            generated_output="DELETE FROM users;",
            auto_corrections={
                "Delet": "DELETE"
            },
            confidence=0.8,
        )

        assert result.can_auto_fix
        assert "Delet" in result.auto_corrections

    def test_result_to_dict(self):
        """Test conversion to dictionary."""
        result = FeedbackResult(
            type=FeedbackType.SUCCESS,
            original_input="test",
            generated_output="output",
            confidence=1.0,
            warnings=["warning1"],
            suggestions=["suggestion1"],
        )

        data = result.to_dict()

        assert data["type"] == "success"
        assert data["original_input"] == "test"
        assert "warning1" in data["warnings"]

    def test_result_requires_user_input(self):
        """Test result requiring user input."""
        result = FeedbackResult(
            type=FeedbackType.AMBIGUOUS_INPUT,
            original_input="Delete that",
            generated_output="",
            requires_user_input=True,
            clarification_questions=["Which table do you want to delete from?"],
            confidence=0.3,
        )

        assert result.requires_user_input
        assert len(result.clarification_questions) == 1


class TestCorrectionRule:
    """Tests for CorrectionRule dataclass."""

    def test_basic_rule(self):
        """Test basic correction rule."""
        rule = CorrectionRule(
            pattern=r"DELET\b",
            replacement="DELETE",
            description="Fix typo: DELET -> DELETE",
            confidence=0.95,
        )

        assert rule.pattern == r"DELET\b"
        assert rule.confidence == 0.95

    def test_rule_with_dsl_filter(self):
        """Test rule with DSL filter."""
        rule = CorrectionRule(
            pattern=r"rm -rf /",
            replacement="# Blocked",
            description="Block dangerous command",
            confidence=1.0,
            applies_to=["shell"],
        )

        assert "shell" in rule.applies_to
        assert "sql" not in rule.applies_to


class TestFeedbackAnalyzer:
    """Tests for FeedbackAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return FeedbackAnalyzer()

    def test_analyze_success(self, analyzer):
        """Test analyzing successful transformation."""
        result = analyzer.analyze(
            original_input="Show all users",
            generated_output="SELECT * FROM users;",
            validation_errors=[],
            validation_warnings=[],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.SUCCESS
        assert result.confidence > 0

    def test_analyze_with_errors(self, analyzer):
        """Test analyzing transformation with errors."""
        result = analyzer.analyze(
            original_input="Show users",
            generated_output="SELECT * FROM users",
            validation_errors=["Missing semicolon"],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.SYNTAX_ERROR
        assert "Missing semicolon" in result.errors

    def test_analyze_with_warnings(self, analyzer):
        """Test analyzing transformation with warnings."""
        result = analyzer.analyze(
            original_input="Delete users",
            generated_output="DELETE FROM users;",
            validation_warnings=["DELETE without WHERE"],
            dsl_type="sql",
        )

        assert result.type == FeedbackType.PARTIAL_SUCCESS
        assert len(result.warnings) > 0

    def test_analyze_ambiguous_input(self, analyzer):
        """Test analyzing ambiguous input."""
        result = analyzer.analyze(
            original_input="Delete that thing",
            generated_output="",
            dsl_type="sql",
            context=None,  # No context makes it ambiguous
        )

        # Should detect ambiguity
        assert result.type in [FeedbackType.AMBIGUOUS_INPUT, FeedbackType.SUCCESS]

    def test_schema_mismatch_no_matching_command(self, analyzer):
        result = analyzer.analyze(
            original_input="Do something with containers",
            generated_output="# No matching command found for: containers",
            dsl_type="dynamic",
            context={},
        )

        assert result.type == FeedbackType.SCHEMA_MISMATCH
        assert result.requires_user_input
        assert any("tool/domain" in q.lower() for q in result.clarification_questions)

    def test_missing_tool_detection(self, analyzer):
        result = analyzer.analyze(
            original_input="Run kubectl get pods",
            generated_output="kubectl get pods",
            dsl_type="shell",
            context={},
        )

        if result.type == FeedbackType.RUNTIME_ERROR:
            assert result.metadata.get("missing_tool") == "kubectl"
            assert result.requires_user_input

    def test_placeholder_detection(self, analyzer):
        result = analyzer.analyze(
            original_input="Run nginx",
            generated_output="docker run -p {port}:80 nginx",
            dsl_type="docker",
            context={},
        )

        assert result.type == FeedbackType.AMBIGUOUS_INPUT
        assert result.requires_user_input
        assert any("port" in q.lower() for q in result.clarification_questions)

    def test_check_syntax_valid(self, analyzer):
        """Test syntax check for valid content."""
        result = analyzer.check_syntax(
            "SELECT * FROM users WHERE id = 1;",
            "sql"
        )

        assert result["valid"]
        assert len(result["errors"]) == 0

    def test_check_syntax_unbalanced_parens(self, analyzer):
        """Test syntax check catches unbalanced parentheses."""
        result = analyzer.check_syntax(
            "SELECT * FROM users WHERE (id = 1",
            "sql"
        )

        assert not result["valid"]
        assert any("parenthes" in e.lower() for e in result["errors"])

    def test_check_syntax_unclosed_quote(self, analyzer):
        """Test syntax check catches unclosed quotes."""
        result = analyzer.check_syntax(
            "SELECT * FROM users WHERE name = 'John",
            "sql"
        )

        assert not result["valid"]
        assert any("quote" in e.lower() for e in result["errors"])

    def test_analyze_exception(self, analyzer):
        """Test analyzing an exception."""
        error = FileNotFoundError("File 'test.sql' not found")

        result = analyzer.analyze_exception(error)

        assert "FileNotFoundError" in result["error_type"]
        assert len(result["suggestions"]) > 0

    def test_analyze_permission_error(self, analyzer):
        """Test analyzing permission error."""
        error = PermissionError("Access denied to /etc/passwd")

        result = analyzer.analyze_exception(error)

        assert any("permission" in s.lower() for s in result["suggestions"])

    def test_analyze_connection_error(self, analyzer):
        """Test analyzing connection error."""
        error = ConnectionError("Failed to connect to database")

        result = analyzer.analyze_exception(error)

        assert any("connection" in s.lower() or "network" in s.lower() 
                   for s in result["suggestions"])

    def test_error_analysis_with_table_not_found(self, analyzer):
        """Test error analysis for table not found."""
        result = analyzer._analyze_error(
            "Table 'users' not found",
            "SELECT * FROM users;",
            "sql"
        )

        assert len(result["questions"]) > 0 or len(result["suggestions"]) > 0

    def test_error_analysis_with_command_not_found(self, analyzer):
        """Test error analysis for command not found."""
        result = analyzer._analyze_error(
            "command not found: kubectl",
            "kubectl get pods",
            "shell"
        )

        assert len(result["questions"]) > 0 or len(result["suggestions"]) > 0


class TestCorrectionEngine:
    """Tests for CorrectionEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return CorrectionEngine()

    def test_suggest_balance_fix_parentheses(self, engine):
        """Test suggesting fix for unbalanced parentheses."""
        suggestion = engine._suggest_balance_fix(
            "SELECT * FROM users WHERE (id = 1",
            "Unbalanced parentheses"
        )

        assert suggestion["confidence"] > 0
        assert "fix" in suggestion

    def test_suggest_quote_fix(self, engine):
        """Test suggesting fix for unclosed quotes."""
        suggestion = engine._suggest_quote_fix(
            "SELECT * FROM users WHERE name = 'John",
            "Unclosed single quote"
        )

        assert suggestion["confidence"] > 0
        assert suggestion["fix"].endswith("'")

    def test_suggest_double_quote_fix(self, engine):
        """Test suggesting fix for unclosed double quotes."""
        suggestion = engine._suggest_quote_fix(
            'SELECT * FROM users WHERE name = "John',
            "Unclosed double quote"
        )

        assert suggestion["fix"].endswith('"')

    def test_suggest_missing_element(self, engine):
        """Test suggesting fix for missing element."""
        suggestion = engine._suggest_missing_element(
            "SELECT * FROM",
            "Table not found",
            None
        )

        assert "question" in suggestion

    def test_apply_correction(self, engine):
        """Test applying a correction."""
        original = "SELCT * FROM users"
        correction = {"fix": "SELECT * FROM users"}

        result = engine.apply_correction(original, correction)

        assert result == "SELECT * FROM users"

    def test_register_correction(self, engine):
        """Test registering custom correction."""
        rule = CorrectionRule(
            pattern=r"SELCT",
            replacement="SELECT",
            description="Fix SELCT typo",
            confidence=0.95,
        )

        engine.register_correction("sql", rule)

        assert "sql" in engine.corrections
        assert len(engine.corrections["sql"]) > 0


class TestFeedbackIntegration:
    """Integration tests for feedback module."""

    def test_full_feedback_flow(self):
        """Test complete feedback flow."""
        analyzer = FeedbackAnalyzer()

        # Simulate a transformation with errors
        result = analyzer.analyze(
            original_input="Delet all usrs",
            generated_output="DELETE FROM users;",
            validation_errors=[],
            validation_warnings=["DELETE without WHERE clause"],
            dsl_type="sql",
        )

        assert result.type in [FeedbackType.PARTIAL_SUCCESS, FeedbackType.SUCCESS]

        # Check for suggestions
        if result.warnings:
            assert any("WHERE" in w for w in result.warnings)

    def test_feedback_with_correction_engine(self):
        """Test feedback with correction engine."""
        analyzer = FeedbackAnalyzer()
        engine = CorrectionEngine()

        # Analyze error
        feedback = analyzer.analyze(
            original_input="Show users",
            generated_output="SELECT * FROM users WHERE (id = 1",
            validation_errors=["Unbalanced parentheses"],
            dsl_type="sql",
        )

        # Get correction suggestion
        for error in feedback.errors:
            suggestion = engine.suggest(
                error,
                feedback.generated_output,
                {"dsl_type": "sql"}
            )

            if suggestion.get("fix"):
                corrected = engine.apply_correction(
                    feedback.generated_output,
                    suggestion
                )
                assert corrected is not None

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        analyzer = FeedbackAnalyzer()

        # No errors - high confidence
        result1 = analyzer.analyze(
            original_input="test",
            generated_output="SELECT * FROM test;",
            validation_errors=[],
            validation_warnings=[],
            dsl_type="sql",
        )

        # With errors - lower confidence
        result2 = analyzer.analyze(
            original_input="test",
            generated_output="SELECT * FROM test",
            validation_errors=["Error 1", "Error 2"],
            validation_warnings=[],
            dsl_type="sql",
        )

        assert result1.confidence > result2.confidence


class TestEdgeCases:
    """Tests for edge cases in feedback module."""

    @pytest.fixture
    def analyzer(self):
        return FeedbackAnalyzer()

    def test_empty_input(self, analyzer):
        """Test with empty input."""
        result = analyzer.analyze(
            original_input="",
            generated_output="",
            dsl_type="sql",
        )

        assert result is not None

    def test_very_long_error_message(self, analyzer):
        """Test with very long error message."""
        long_error = "Error: " + "x" * 10000

        result = analyzer.analyze(
            original_input="test",
            generated_output="test",
            validation_errors=[long_error],
            dsl_type="sql",
        )

        assert result is not None

    def test_special_characters_in_content(self, analyzer):
        """Test with special characters."""
        result = analyzer.analyze(
            original_input="Show users with name = 'O\\'Brien'",
            generated_output="SELECT * FROM users WHERE name = 'O\\'Brien';",
            dsl_type="sql",
        )

        assert result is not None

    def test_unicode_content(self, analyzer):
        """Test with Unicode content."""
        result = analyzer.analyze(
            original_input="Pokaż użytkowników",
            generated_output="SELECT * FROM użytkownicy;",
            dsl_type="sql",
        )

        assert result is not None

    def test_null_context(self, analyzer):
        """Test with null context."""
        result = analyzer.analyze(
            original_input="test",
            generated_output="test",
            dsl_type="sql",
            context=None,
        )

        assert result is not None
