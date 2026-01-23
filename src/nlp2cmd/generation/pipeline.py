"""
Iteration 3: Rule-Based Pipeline.

Combines KeywordIntentDetector, RegexEntityExtractor, and TemplateGenerator
into a complete NL → DSL pipeline without LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import time

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult
from nlp2cmd.generation.regex import RegexEntityExtractor, ExtractionResult
from nlp2cmd.generation.templates import TemplateGenerator, TemplateResult


@dataclass
class PipelineResult:
    """Result of the complete pipeline."""
    
    # Input
    input_text: str
    
    # Detection
    domain: str
    intent: str
    detection_confidence: float
    
    # Extraction
    entities: dict[str, Any]
    
    # Generation
    command: str
    template_used: str
    
    # Metadata
    success: bool
    source: str = "rules"  # "rules" or "llm"
    latency_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def to_plan(self) -> dict[str, Any]:
        """Convert to execution plan format for adapters."""
        return {
            "intent": self.intent,
            "entities": self.entities,
            "confidence": self.detection_confidence,
        }


class RuleBasedPipeline:
    """
    Complete rule-based NL → DSL pipeline.
    
    Combines:
    - KeywordIntentDetector for domain/intent detection
    - RegexEntityExtractor for entity extraction  
    - TemplateGenerator for DSL generation
    
    No LLM required - fast, free, deterministic.
    
    Example:
        pipeline = RuleBasedPipeline()
        result = pipeline.process("Pokaż wszystkich użytkowników z tabeli users")
        print(result.command)  # SELECT * FROM users;
    """
    
    def __init__(
        self,
        detector: Optional[KeywordIntentDetector] = None,
        extractor: Optional[RegexEntityExtractor] = None,
        generator: Optional[TemplateGenerator] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize pipeline.
        
        Args:
            detector: Intent detector (default: KeywordIntentDetector)
            extractor: Entity extractor (default: RegexEntityExtractor)
            generator: Template generator (default: TemplateGenerator)
            confidence_threshold: Minimum confidence to proceed
        """
        self.detector = detector or KeywordIntentDetector()
        self.extractor = extractor or RegexEntityExtractor()
        self.generator = generator or TemplateGenerator()
        self.confidence_threshold = confidence_threshold
    
    def process(self, text: str) -> PipelineResult:
        """
        Process natural language text through the pipeline.
        
        Args:
            text: Natural language input
            
        Returns:
            PipelineResult with generated command
        """
        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []
        
        # Step 1: Detect domain and intent
        detection = self.detector.detect(text)
        
        if detection.domain == 'unknown':
            latency = (time.time() - start_time) * 1000
            return PipelineResult(
                input_text=text,
                domain='unknown',
                intent='unknown',
                detection_confidence=0.0,
                entities={},
                command=f"# Could not detect domain for: {text}",
                template_used="",
                success=False,
                latency_ms=latency,
                errors=["Could not detect domain from input text"],
            )
        
        if detection.confidence < self.confidence_threshold:
            warnings.append(f"Low confidence detection: {detection.confidence:.2f}")
        
        # Step 2: Extract entities
        extraction = self.extractor.extract(text, detection.domain)
        
        if not extraction.entities:
            warnings.append("No entities extracted from text")
        
        # Step 3: Generate command from template
        # Add original text to entities for context-aware template selection
        entities_with_text = extraction.entities.copy()
        entities_with_text['text'] = text

        template_result = self.generator.generate(
            domain=detection.domain,
            intent=detection.intent,
            entities=entities_with_text,
        )

        if not template_result.success:
            fallback_results: list[tuple[DetectionResult, ExtractionResult, TemplateResult]] = []
            for cand in self.detector.detect_all(text)[:8]:
                if cand.domain == detection.domain and cand.intent == detection.intent:
                    continue

                cand_extraction = self.extractor.extract(text, cand.domain)
                cand_entities = cand_extraction.entities.copy()
                cand_entities["text"] = text
                cand_template = self.generator.generate(
                    domain=cand.domain,
                    intent=cand.intent,
                    entities=cand_entities,
                )
                if cand_template.success:
                    fallback_results.append((cand, cand_extraction, cand_template))
                    break

            if fallback_results:
                chosen_detection, chosen_extraction, chosen_template = fallback_results[0]
                detection = chosen_detection
                extraction = chosen_extraction
                template_result = chosen_template
        
        if not template_result.success:
            errors.append(f"Template generation failed: {template_result.command}")
        
        if template_result.missing_entities:
            warnings.append(f"Missing entities: {template_result.missing_entities}")
        
        latency = (time.time() - start_time) * 1000
        
        return PipelineResult(
            input_text=text,
            domain=detection.domain,
            intent=detection.intent,
            detection_confidence=detection.confidence,
            entities=extraction.entities,
            command=template_result.command,
            template_used=template_result.template_used,
            success=template_result.success and len(errors) == 0,
            source="rules",
            latency_ms=latency,
            errors=errors,
            warnings=warnings,
        )
    
    def process_batch(self, texts: list[str]) -> list[PipelineResult]:
        """
        Process multiple texts.
        
        Args:
            texts: List of natural language inputs
            
        Returns:
            List of PipelineResult
        """
        return [self.process(text) for text in texts]
    
    def detect_only(self, text: str) -> DetectionResult:
        """
        Only detect domain and intent (skip extraction and generation).
        
        Args:
            text: Natural language input
            
        Returns:
            DetectionResult
        """
        return self.detector.detect(text)
    
    def extract_only(self, text: str, domain: str) -> ExtractionResult:
        """
        Only extract entities (skip detection and generation).
        
        Args:
            text: Natural language input
            domain: Target domain
            
        Returns:
            ExtractionResult
        """
        return self.extractor.extract(text, domain)
    
    def generate_only(
        self,
        domain: str,
        intent: str,
        entities: dict[str, Any],
    ) -> TemplateResult:
        """
        Only generate command (skip detection and extraction).
        
        Args:
            domain: Target domain
            intent: Intent
            entities: Entities dict
            
        Returns:
            TemplateResult
        """
        return self.generator.generate(domain, intent, entities)
    
    def get_supported_domains(self) -> list[str]:
        """Get list of supported domains."""
        return self.detector.get_supported_domains()
    
    def get_supported_intents(self, domain: str) -> list[str]:
        """Get list of supported intents for a domain."""
        return self.detector.get_supported_intents(domain)


class PipelineMetrics:
    """Track pipeline metrics for evaluation."""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.domain_counts: dict[str, int] = {}
        self.intent_counts: dict[str, int] = {}
        self.total_latency_ms = 0.0
        self.confidence_sum = 0.0
        self.errors: list[str] = []
    
    def record(self, result: PipelineResult) -> None:
        """Record a pipeline result."""
        self.total_requests += 1
        
        if result.success:
            self.successful_requests += 1
        
        self.domain_counts[result.domain] = self.domain_counts.get(result.domain, 0) + 1
        
        intent_key = f"{result.domain}.{result.intent}"
        self.intent_counts[intent_key] = self.intent_counts.get(intent_key, 0) + 1
        
        self.total_latency_ms += result.latency_ms
        self.confidence_sum += result.detection_confidence
        
        if result.errors:
            self.errors.extend(result.errors)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests
    
    @property
    def avg_confidence(self) -> float:
        """Calculate average confidence."""
        if self.total_requests == 0:
            return 0.0
        return self.confidence_sum / self.total_requests
    
    def report(self) -> dict[str, Any]:
        """Generate metrics report."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "success_rate": f"{self.success_rate:.2%}",
            "avg_latency_ms": f"{self.avg_latency_ms:.2f}",
            "avg_confidence": f"{self.avg_confidence:.2f}",
            "domain_distribution": self.domain_counts,
            "intent_distribution": self.intent_counts,
            "error_count": len(self.errors),
        }


def create_pipeline(
    confidence_threshold: float = 0.5,
    custom_patterns: Optional[dict[str, dict[str, list[str]]]] = None,
    custom_templates: Optional[dict[str, dict[str, str]]] = None,
) -> RuleBasedPipeline:
    """
    Factory function to create a configured pipeline.
    
    Args:
        confidence_threshold: Minimum confidence threshold
        custom_patterns: Additional keyword patterns
        custom_templates: Additional templates
        
    Returns:
        Configured RuleBasedPipeline
    """
    detector = KeywordIntentDetector(confidence_threshold=confidence_threshold)
    extractor = RegexEntityExtractor()
    generator = TemplateGenerator(custom_templates=custom_templates)
    
    # Add custom patterns if provided
    if custom_patterns:
        for domain, intents in custom_patterns.items():
            for intent, keywords in intents.items():
                detector.add_pattern(domain, intent, keywords)
    
    return RuleBasedPipeline(
        detector=detector,
        extractor=extractor,
        generator=generator,
        confidence_threshold=confidence_threshold,
    )
