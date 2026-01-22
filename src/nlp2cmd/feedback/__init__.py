"""
Feedback Loop module for NLP2CMD.

Provides intelligent feedback analysis, error correction suggestions,
and iterative improvement capabilities.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback from the system."""

    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    RUNTIME_ERROR = "runtime_error"
    AMBIGUOUS_INPUT = "ambiguous_input"
    PARTIAL_SUCCESS = "partial_success"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class FeedbackResult:
    """Result of feedback analysis."""

    type: FeedbackType
    original_input: str
    generated_output: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    auto_corrections: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    requires_user_input: bool = False
    clarification_questions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if feedback indicates success."""
        return self.type == FeedbackType.SUCCESS

    @property
    def can_auto_fix(self) -> bool:
        """Check if automatic fixes are available."""
        return len(self.auto_corrections) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "original_input": self.original_input,
            "generated_output": self.generated_output,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "auto_corrections": self.auto_corrections,
            "confidence": self.confidence,
            "requires_user_input": self.requires_user_input,
            "clarification_questions": self.clarification_questions,
            "metadata": self.metadata,
        }


@dataclass
class CorrectionRule:
    """Rule for automatic correction."""

    pattern: str
    replacement: str | Callable[[re.Match], str]
    description: str
    confidence: float = 0.9
    applies_to: list[str] = field(default_factory=list)  # DSL types


class FeedbackAnalyzer:
    """
    Analyzes transformation results and provides feedback.

    This class examines errors, warnings, and the generated output
    to provide actionable feedback and correction suggestions.
    """

    def __init__(self, correction_rules: Optional[list[CorrectionRule]] = None):
        """
        Initialize the analyzer.

        Args:
            correction_rules: Custom correction rules
        """
        self.correction_rules = correction_rules or []
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default correction rules."""
        default_rules = [
            # SQL rules
            CorrectionRule(
                pattern=r"DELETE FROM (\w+)\s*;",
                replacement=r"DELETE FROM \1 WHERE /* add condition */;",
                description="Add WHERE clause to DELETE",
                confidence=0.85,
                applies_to=["sql"],
            ),
            CorrectionRule(
                pattern=r"UPDATE (\w+) SET (.+);$",
                replacement=r"UPDATE \1 SET \2 WHERE /* add condition */;",
                description="Add WHERE clause to UPDATE",
                confidence=0.85,
                applies_to=["sql"],
            ),
            # Shell rules
            CorrectionRule(
                pattern=r"rm -rf (\S+)",
                replacement=r"rm -ri \1",
                description="Use interactive mode for rm",
                confidence=0.7,
                applies_to=["shell"],
            ),
            # Docker rules
            CorrectionRule(
                pattern=r"docker run (.+) (\w+)$",
                replacement=r"docker run \1 \2:latest",
                description="Add :latest tag to image",
                confidence=0.8,
                applies_to=["docker"],
            ),
        ]
        self.correction_rules.extend(default_rules)

    def analyze(
        self,
        original_input: str,
        generated_output: str,
        validation_errors: Optional[list[str]] = None,
        validation_warnings: Optional[list[str]] = None,
        dsl_type: str = "unknown",
        context: Optional[dict[str, Any]] = None,
    ) -> FeedbackResult:
        """
        Analyze transformation result and generate feedback.

        Args:
            original_input: Original natural language input
            generated_output: Generated command/output
            validation_errors: Errors from validation
            validation_warnings: Warnings from validation
            dsl_type: Type of DSL (sql, shell, docker, etc.)
            context: Additional context

        Returns:
            FeedbackResult with analysis
        """
        errors = validation_errors or []
        warnings = validation_warnings or []
        suggestions = []
        auto_corrections = {}
        clarification_questions = []

        # Determine feedback type
        if errors:
            feedback_type = FeedbackType.SYNTAX_ERROR
        elif warnings:
            feedback_type = FeedbackType.PARTIAL_SUCCESS
        else:
            feedback_type = FeedbackType.SUCCESS

        # Analyze errors and generate suggestions
        for error in errors:
            error_analysis = self._analyze_error(error, generated_output, dsl_type)
            suggestions.extend(error_analysis.get("suggestions", []))
            auto_corrections.update(error_analysis.get("auto_corrections", {}))
            clarification_questions.extend(error_analysis.get("questions", []))

        # Try to apply correction rules
        for rule in self.correction_rules:
            if rule.applies_to and dsl_type not in rule.applies_to:
                continue

            match = re.search(rule.pattern, generated_output)
            if match:
                if callable(rule.replacement):
                    fixed = rule.replacement(match)
                else:
                    fixed = re.sub(rule.pattern, rule.replacement, generated_output)

                if rule.confidence >= 0.9:
                    auto_corrections[generated_output] = fixed
                else:
                    suggestions.append(f"💡 {rule.description}: {fixed}")

        # Check for ambiguous input
        if self._is_ambiguous(original_input, context):
            feedback_type = FeedbackType.AMBIGUOUS_INPUT
            clarification_questions.extend(
                self._generate_clarification_questions(original_input, dsl_type)
            )

        # Calculate confidence
        confidence = self._calculate_confidence(
            errors, warnings, len(auto_corrections), generated_output
        )

        return FeedbackResult(
            type=feedback_type,
            original_input=original_input,
            generated_output=generated_output,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            auto_corrections=auto_corrections,
            confidence=confidence,
            requires_user_input=len(clarification_questions) > 0,
            clarification_questions=clarification_questions,
        )

    def _analyze_error(
        self,
        error: str,
        output: str,
        dsl_type: str,
    ) -> dict[str, Any]:
        """Analyze a specific error and generate suggestions."""
        suggestions = []
        auto_corrections = {}
        questions = []

        error_lower = error.lower()

        # Common error patterns
        if "unbalanced" in error_lower or "unclosed" in error_lower:
            if "parenthes" in error_lower:
                suggestions.append("Check for missing opening or closing parenthesis")
            elif "quote" in error_lower:
                suggestions.append("Check for missing quotation marks")
            elif "brace" in error_lower:
                suggestions.append("Check for missing curly braces")

        if "not found" in error_lower or "unknown" in error_lower:
            if "table" in error_lower:
                questions.append("Which table did you mean to query?")
            elif "command" in error_lower:
                questions.append("Is the required tool installed?")
            elif "column" in error_lower:
                questions.append("Which column did you intend to use?")

        if "permission" in error_lower or "access denied" in error_lower:
            suggestions.append("You may need elevated privileges (sudo) for this operation")

        return {
            "suggestions": suggestions,
            "auto_corrections": auto_corrections,
            "questions": questions,
        }

    def _is_ambiguous(
        self,
        input_text: str,
        context: Optional[dict[str, Any]],
    ) -> bool:
        """Check if input is ambiguous."""
        ambiguous_indicators = [
            "to", "that thing", "the file", "my project",
            "it", "them", "those", "these",
        ]

        input_lower = input_text.lower()

        # Check for pronouns without clear referent
        for indicator in ambiguous_indicators:
            if indicator in input_lower:
                # If no context provided, it's ambiguous
                if not context:
                    return True
                # If context doesn't have previous references, it's ambiguous
                if "previous_commands" not in context and "previous_topics" not in context:
                    return True

        return False

    def _generate_clarification_questions(
        self,
        input_text: str,
        dsl_type: str,
    ) -> list[str]:
        """Generate clarification questions for ambiguous input."""
        questions = []

        input_lower = input_text.lower()

        if "the file" in input_lower or "that file" in input_lower:
            questions.append("Which file are you referring to?")

        if "the table" in input_lower or "that table" in input_lower:
            questions.append("Which database table did you mean?")

        if "delete" in input_lower or "remove" in input_lower:
            questions.append("Can you confirm what you want to delete?")

        if "all" in input_lower:
            questions.append("When you say 'all', which specific items do you mean?")

        return questions

    def _calculate_confidence(
        self,
        errors: list[str],
        warnings: list[str],
        auto_fix_count: int,
        output: str,
    ) -> float:
        """Calculate confidence score."""
        confidence = 1.0

        # Reduce confidence for errors
        confidence -= len(errors) * 0.2

        # Slightly reduce for warnings
        confidence -= len(warnings) * 0.05

        # Increase slightly for auto-fixes available
        if auto_fix_count > 0:
            confidence += 0.05

        # Reduce for very short or very long output
        if len(output) < 10:
            confidence -= 0.1
        elif len(output) > 1000:
            confidence -= 0.05

        return max(0.0, min(1.0, confidence))

    def check_syntax(self, content: str, dsl_type: str) -> dict[str, Any]:
        """Quick syntax check for content."""
        errors = []

        # Basic checks
        if content.count("(") != content.count(")"):
            errors.append("Unbalanced parentheses")
        if content.count("[") != content.count("]"):
            errors.append("Unbalanced brackets")
        if content.count("{") != content.count("}"):
            errors.append("Unbalanced braces")

        # Quote checks
        single_quotes = content.count("'") - content.count("\\'")
        double_quotes = content.count('"') - content.count('\\"')

        if single_quotes % 2 != 0:
            errors.append("Unclosed single quote")
        if double_quotes % 2 != 0:
            errors.append("Unclosed double quote")

        return {"valid": len(errors) == 0, "errors": errors}

    def analyze_exception(self, exception: Exception) -> dict[str, Any]:
        """Analyze an exception and provide suggestions."""
        error_msg = str(exception)
        error_type = type(exception).__name__

        suggestions = []
        questions = []

        # Common exception patterns
        if "FileNotFoundError" in error_type or "No such file" in error_msg:
            suggestions.append("Check if the file path is correct")
            suggestions.append("Verify the file exists")
            questions.append("What is the correct file path?")

        elif "PermissionError" in error_type:
            suggestions.append("Try running with elevated privileges")
            suggestions.append("Check file/directory permissions")

        elif "ConnectionError" in error_type or "timeout" in error_msg.lower():
            suggestions.append("Check network connectivity")
            suggestions.append("Verify the service is running")

        elif "SyntaxError" in error_type:
            suggestions.append("Review command syntax")
            suggestions.append("Check for typos or missing elements")

        return {
            "suggestions": suggestions,
            "questions": questions,
            "error_type": error_type,
            "error_message": error_msg,
        }


class CorrectionEngine:
    """
    Engine for applying corrections to generated content.

    Provides intelligent correction capabilities based on
    error analysis and predefined rules.
    """

    def __init__(self):
        self.corrections: dict[str, list[CorrectionRule]] = {}

    def register_correction(self, dsl_type: str, rule: CorrectionRule):
        """Register a correction rule for a DSL type."""
        if dsl_type not in self.corrections:
            self.corrections[dsl_type] = []
        self.corrections[dsl_type].append(rule)

    def suggest(
        self,
        error: str,
        content: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Suggest a correction for an error.

        Args:
            error: Error message
            content: Content with error
            context: Additional context

        Returns:
            Dictionary with correction suggestion
        """
        # Analyze error type
        error_lower = error.lower()

        # Pattern-based suggestions
        if "unbalanced" in error_lower:
            return self._suggest_balance_fix(content, error)

        if "unclosed" in error_lower:
            return self._suggest_quote_fix(content, error)

        if "not found" in error_lower:
            return self._suggest_missing_element(content, error, context)

        # Default: ask for clarification
        return {
            "confidence": 0.3,
            "description": "Could not determine automatic fix",
            "fix": content,
            "question": "Can you provide more details about the error?",
        }

    def _suggest_balance_fix(self, content: str, error: str) -> dict[str, Any]:
        """Suggest fix for unbalanced brackets/parentheses."""
        if "parenthes" in error.lower():
            open_count = content.count("(")
            close_count = content.count(")")

            if open_count > close_count:
                return {
                    "confidence": 0.8,
                    "description": f"Add {open_count - close_count} closing parenthesis",
                    "fix": content + ")" * (open_count - close_count),
                }
            else:
                return {
                    "confidence": 0.5,
                    "description": "Extra closing parenthesis - review needed",
                    "fix": content,
                    "question": "Where should the opening parenthesis be added?",
                }

        return {"confidence": 0.3, "fix": content, "description": "Balance issue detected"}

    def _suggest_quote_fix(self, content: str, error: str) -> dict[str, Any]:
        """Suggest fix for unclosed quotes."""
        if "single quote" in error.lower():
            return {
                "confidence": 0.7,
                "description": "Add closing single quote",
                "fix": content + "'",
            }
        elif "double quote" in error.lower():
            return {
                "confidence": 0.7,
                "description": "Add closing double quote",
                "fix": content + '"',
            }

        return {"confidence": 0.3, "fix": content, "description": "Quote issue detected"}

    def _suggest_missing_element(
        self,
        content: str,
        error: str,
        context: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """Suggest fix for missing elements."""
        return {
            "confidence": 0.4,
            "description": "Missing element detected",
            "fix": content,
            "question": "What is the correct name or value?",
        }

    def apply_correction(
        self,
        content: str,
        correction: dict[str, Any],
    ) -> str:
        """Apply a correction to content."""
        return correction.get("fix", content)


__all__ = [
    "FeedbackType",
    "FeedbackResult",
    "FeedbackAnalyzer",
    "CorrectionEngine",
    "CorrectionRule",
]
