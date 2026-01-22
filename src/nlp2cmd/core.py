"""
Core module for NLP2CMD framework.

This module contains the main NLP2CMD class and related components
for transforming natural language into domain-specific commands.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nlp2cmd.adapters.base import BaseDSLAdapter
    from nlp2cmd.feedback import FeedbackAnalyzer
    from nlp2cmd.validators.base import BaseValidator

logger = logging.getLogger(__name__)


class TransformStatus(str, Enum):
    """Status of a transformation operation."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    NEEDS_CLARIFICATION = "needs_clarification"


class Intent(BaseModel):
    """Represents a detected intent from natural language input."""

    name: str = Field(..., description="Intent name")
    patterns: list[str] = Field(default_factory=list, description="Matching patterns")
    required_entities: list[str] = Field(
        default_factory=list, description="Required entities for this intent"
    )
    optional_entities: list[str] = Field(
        default_factory=list, description="Optional entities"
    )
    confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence for this intent"
    )


class Entity(BaseModel):
    """Represents an extracted entity from natural language input."""

    name: str = Field(..., description="Entity name")
    value: Any = Field(..., description="Entity value")
    type: str = Field(..., description="Entity type")
    start: int = Field(default=0, description="Start position in text")
    end: int = Field(default=0, description="End position in text")
    confidence: float = Field(default=1.0, description="Extraction confidence")


class ExecutionPlan(BaseModel):
    """Structured plan for command execution."""

    intent: str = Field(..., description="Detected intent")
    entities: dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    confidence: float = Field(default=0.0, description="Overall confidence")
    requires_confirmation: bool = Field(
        default=False, description="Whether user confirmation is needed"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@dataclass
class TransformResult:
    """Result of a natural language to command transformation."""

    status: TransformStatus
    command: str
    plan: ExecutionPlan
    confidence: float
    dsl_type: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if transformation was successful."""
        return self.status == TransformStatus.SUCCESS

    @property
    def is_blocked(self) -> bool:
        """Check if transformation was blocked by security policy."""
        return self.status == TransformStatus.BLOCKED

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "command": self.command,
            "plan": self.plan.model_dump(),
            "confidence": self.confidence,
            "dsl_type": self.dsl_type,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "alternatives": self.alternatives,
            "metadata": self.metadata,
        }


class NLPBackend:
    """Base class for NLP processing backends."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}

    def extract_intent(self, text: str) -> tuple[str, float]:
        """Extract intent from text."""
        raise NotImplementedError

    def extract_entities(self, text: str) -> list[Entity]:
        """Extract entities from text."""
        raise NotImplementedError

    def generate_plan(self, text: str, context: Optional[dict] = None) -> ExecutionPlan:
        """Generate execution plan from text."""
        raise NotImplementedError


class SpaCyBackend(NLPBackend):
    """spaCy-based NLP backend."""

    def __init__(self, model: str = "en_core_web_sm", config: Optional[dict] = None):
        super().__init__(config)
        self.model_name = model
        self._nlp = None

    @property
    def nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            try:
                import spacy

                self._nlp = spacy.load(self.model_name)
            except ImportError:
                raise ImportError("spaCy is required. Install with: pip install nlp2cmd[nlp]")
        return self._nlp

    def extract_entities(self, text: str) -> list[Entity]:
        """Extract named entities using spaCy."""
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append(
                Entity(
                    name=ent.label_,
                    value=ent.text,
                    type=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                )
            )
        return entities


class LLMBackend(NLPBackend):
    """LLM-based NLP backend (Claude, GPT, etc.)."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        config: Optional[dict] = None,
    ):
        super().__init__(config)
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._client = None

    def _default_system_prompt(self) -> str:
        return """You are an assistant that converts natural language to structured commands.
        
Analyze the user's request and respond with a JSON object containing:
- intent: the main action (e.g., "query", "create", "update", "delete", "find")
- entities: extracted parameters as key-value pairs
- confidence: your confidence score (0.0-1.0)

Respond ONLY with valid JSON, no additional text."""

    @property
    def client(self):
        """Lazy-load API client."""
        if self._client is None:
            if "claude" in self.model.lower():
                try:
                    from anthropic import Anthropic

                    self._client = Anthropic(api_key=self.api_key)
                except ImportError:
                    raise ImportError(
                        "anthropic is required. Install with: pip install nlp2cmd[llm]"
                    )
            else:
                try:
                    from openai import OpenAI

                    self._client = OpenAI(api_key=self.api_key)
                except ImportError:
                    raise ImportError(
                        "openai is required. Install with: pip install nlp2cmd[llm]"
                    )
        return self._client

    def generate_plan(self, text: str, context: Optional[dict] = None) -> ExecutionPlan:
        """Generate execution plan using LLM."""
        import json

        prompt = text
        if context:
            prompt = f"Context: {json.dumps(context)}\n\nRequest: {text}"

        if "claude" in self.model.lower():
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            result_text = response.choices[0].message.content

        try:
            data = json.loads(result_text)
            return ExecutionPlan(
                intent=data.get("intent", "unknown"),
                entities=data.get("entities", {}),
                confidence=data.get("confidence", 0.5),
            )
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM response: {result_text}")
            return ExecutionPlan(intent="unknown", entities={}, confidence=0.0)


class RuleBasedBackend(NLPBackend):
    """Simple rule-based NLP backend for basic pattern matching."""

    def __init__(self, rules: Optional[dict[str, list[str]]] = None, config: Optional[dict] = None):
        super().__init__(config)
        self.rules = rules or {}

    def extract_intent(self, text: str) -> tuple[str, float]:
        """Extract intent using pattern matching."""
        text_lower = text.lower()

        for intent, patterns in self.rules.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    return intent, 0.8

        return "unknown", 0.0


class NLP2CMD:
    """
    Main class for Natural Language to Command transformation.

    This class orchestrates the transformation of natural language input
    into domain-specific commands using adapters, validators, and NLP backends.
    """

    def __init__(
        self,
        adapter: BaseDSLAdapter,
        nlp_backend: Optional[NLPBackend] = None,
        validator: Optional[BaseValidator] = None,
        feedback_analyzer: Optional[FeedbackAnalyzer] = None,
        validation_mode: str = "normal",
        auto_fix: bool = False,
    ):
        """
        Initialize NLP2CMD instance.

        Args:
            adapter: DSL adapter for command generation
            nlp_backend: NLP processing backend (spaCy, LLM, or rule-based)
            validator: Command validator
            feedback_analyzer: Analyzer for feedback loop
            validation_mode: Validation strictness ("strict", "normal", "permissive")
            auto_fix: Whether to automatically fix detected issues
        """
        self.adapter = adapter
        self.nlp_backend = nlp_backend or RuleBasedBackend()
        self.validator = validator
        self.feedback_analyzer = feedback_analyzer
        self.validation_mode = validation_mode
        self.auto_fix = auto_fix

        # Context for multi-turn conversations
        self._context: dict[str, Any] = {}
        self._history: list[TransformResult] = []

    @property
    def dsl_name(self) -> str:
        """Get the name of the current DSL adapter."""
        return self.adapter.DSL_NAME

    def transform(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> TransformResult:
        """
        Transform natural language text into a DSL command.

        Args:
            text: Natural language input
            context: Additional context for transformation
            dry_run: If True, don't execute, just generate

        Returns:
            TransformResult with generated command and metadata
        """
        # Merge context
        full_context = {**self._context, **(context or {})}

        # Step 1: NLP Processing - Generate execution plan
        try:
            if isinstance(self.nlp_backend, LLMBackend):
                plan = self.nlp_backend.generate_plan(text, full_context)
            else:
                intent, confidence = self.nlp_backend.extract_intent(text)
                entities = self.nlp_backend.extract_entities(text)
                plan = ExecutionPlan(
                    intent=intent,
                    entities={e.name: e.value for e in entities},
                    confidence=confidence,
                )
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return TransformResult(
                status=TransformStatus.FAILED,
                command="",
                plan=ExecutionPlan(intent="error", entities={}),
                confidence=0.0,
                dsl_type=self.dsl_name,
                errors=[str(e)],
            )

        # Step 2: Generate command using adapter
        try:
            command = self.adapter.generate(plan.model_dump())
        except Exception as e:
            logger.error(f"Command generation failed: {e}")
            return TransformResult(
                status=TransformStatus.FAILED,
                command="",
                plan=plan,
                confidence=0.0,
                dsl_type=self.dsl_name,
                errors=[f"Generation error: {e}"],
            )

        # Step 3: Validate command
        errors = []
        warnings = []
        suggestions = []

        if self.validator:
            validation_result = self.validator.validate(command)
            if not validation_result.is_valid:
                errors.extend(validation_result.errors)
            warnings.extend(validation_result.warnings)
            suggestions.extend(validation_result.suggestions)

        # Step 4: Check safety policy
        safety_result = self.adapter.check_safety(command)
        if not safety_result["allowed"]:
            return TransformResult(
                status=TransformStatus.BLOCKED,
                command=command,
                plan=plan,
                confidence=plan.confidence,
                dsl_type=self.dsl_name,
                errors=[safety_result.get("reason", "Blocked by safety policy")],
                suggestions=safety_result.get("alternatives", []),
            )

        # Determine status
        if errors:
            status = TransformStatus.FAILED
        elif warnings:
            status = TransformStatus.PARTIAL
        else:
            status = TransformStatus.SUCCESS

        result = TransformResult(
            status=status,
            command=command,
            plan=plan,
            confidence=plan.confidence,
            dsl_type=self.dsl_name,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

        # Store in history
        self._history.append(result)

        return result

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value for subsequent transformations."""
        self._context[key] = value

    def clear_context(self) -> None:
        """Clear all context."""
        self._context.clear()

    def get_history(self) -> list[TransformResult]:
        """Get transformation history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear transformation history."""
        self._history.clear()
