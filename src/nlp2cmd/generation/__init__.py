"""
Text → Multi-DSL Generation Module.

This module provides iterative text-to-DSL generation capabilities:
- Rule-based intent detection (no LLM) - Iteration 1
- Regex entity extraction - Iteration 2
- Template-based generation - Iteration 3
- LLM integration (single/multi domain) - Iterations 4-5
- Structured JSON output - Iteration 6
- Validation & self-correction - Iteration 7
- Hybrid rule+LLM approach - Iteration 9
"""

# Iteration 1-3: Rule-based components
from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult
from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult
from nlp2cmd.generation.templates import TemplateGenerator, TemplateResult
from nlp2cmd.generation.pipeline import (
    RuleBasedPipeline,
    PipelineResult,
    PipelineMetrics,
    create_pipeline,
)

# Iteration 4-5: LLM generators
from nlp2cmd.generation.llm_simple import (
    LLMClient,
    LLMConfig,
    LLMGenerationResult,
    BaseLLMGenerator,
    SimpleLLMSQLGenerator,
    SimpleLLMShellGenerator,
    SimpleLLMDockerGenerator,
    SimpleLLMKubernetesGenerator,
    MockLLMClient,
)
from nlp2cmd.generation.llm_multi import (
    LLMDomainRouter,
    MultiDomainGenerator,
    MultiDomainResult,
    RoutingResult,
    CachedMultiDomainGenerator,
)

# Iteration 6: Structured output
from nlp2cmd.generation.structured import (
    StructuredLLMPlanner,
    StructuredPlan,
    StructuredPlanResult,
    MultiStepPlanner,
    MultiStepPlan,
    PLAN_SCHEMA,
)

# Iteration 7: Validation
from nlp2cmd.generation.validating import (
    ValidatingGenerator,
    ValidatingGeneratorResult,
    ValidationResult,
    SimpleSQLValidator,
    SimpleShellValidator,
    SimpleDockerValidator,
    SimpleKubernetesValidator,
    create_default_validators,
)

# Iteration 9: Hybrid
from nlp2cmd.generation.hybrid import (
    HybridGenerator,
    HybridResult,
    HybridStats,
    AdaptiveHybridGenerator,
    create_hybrid_generator,
)

__all__ = [
    # Iteration 1-3: Rule-based
    "KeywordIntentDetector",
    "DetectionResult",
    "RegexEntityExtractor",
    "ExtractionResult",
    "TemplateGenerator",
    "TemplateResult",
    "RuleBasedPipeline",
    "PipelineResult",
    "PipelineMetrics",
    "create_pipeline",
    # Iteration 4-5: LLM
    "LLMClient",
    "LLMConfig",
    "LLMGenerationResult",
    "BaseLLMGenerator",
    "SimpleLLMSQLGenerator",
    "SimpleLLMShellGenerator",
    "SimpleLLMDockerGenerator",
    "SimpleLLMKubernetesGenerator",
    "MockLLMClient",
    "LLMDomainRouter",
    "MultiDomainGenerator",
    "MultiDomainResult",
    "RoutingResult",
    "CachedMultiDomainGenerator",
    # Iteration 6: Structured
    "StructuredLLMPlanner",
    "StructuredPlan",
    "StructuredPlanResult",
    "MultiStepPlanner",
    "MultiStepPlan",
    "PLAN_SCHEMA",
    # Iteration 7: Validation
    "ValidatingGenerator",
    "ValidatingGeneratorResult",
    "ValidationResult",
    "SimpleSQLValidator",
    "SimpleShellValidator",
    "SimpleDockerValidator",
    "SimpleKubernetesValidator",
    "create_default_validators",
    # Iteration 9: Hybrid
    "HybridGenerator",
    "HybridResult",
    "HybridStats",
    "AdaptiveHybridGenerator",
    "create_hybrid_generator",
]
