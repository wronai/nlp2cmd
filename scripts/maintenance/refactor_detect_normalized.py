#!/usr/bin/env python3
"""Refactor _detect_normalized in KeywordIntentDetector to reduce cyclomatic complexity."""

from __future__ import annotations

import re
from typing import Optional

from nlp2cmd.generation.keywords import DetectionResult


# Import required helper functions from keywords module
def _get_helper_functions():
    """Import required helper functions from keywords module."""
    from nlp2cmd.generation.keywords import _get_ml_classifier, _get_fuzzy_schema_matcher, _get_semantic_matcher, fuzz, process
    return {
        '_get_ml_classifier': _get_ml_classifier,
        '_get_fuzzy_schema_matcher': _get_fuzzy_schema_matcher,
        '_get_semantic_matcher': _get_semantic_matcher,
        'fuzz': fuzz,
        'process': process
    }


def _detect_ml_classifier(self, text_lower: str) -> Optional[DetectionResult]:
    """Try ML classifier for high-confidence matches (fastest, <1ms)."""
    helpers = _get_helper_functions()
    ml_classifier = helpers['_get_ml_classifier']()
    if ml_classifier:
        ml_result = ml_classifier.predict(text_lower)
        if ml_result and ml_result.confidence >= 0.9:
            return DetectionResult(
                domain=ml_result.domain,
                intent=ml_result.intent,
                confidence=ml_result.confidence,
                matched_keyword=f"ml:{ml_result.method}",
            )
        # Store for medium confidence fallback
        self._last_ml_result = ml_result
    return None


def _detect_ml_medium_confidence(self) -> Optional[DetectionResult]:
    """ML classifier fallback for medium confidence (still useful)."""
    ml_result = getattr(self, '_last_ml_result', None)
    if ml_result and ml_result.confidence >= 0.7:
        return DetectionResult(
            domain=ml_result.domain,
            intent=ml_result.intent,
            confidence=ml_result.confidence,
            matched_keyword=f"ml:{ml_result.method}",
        )
    return None


def _detect_schema_matcher(self, text_lower: str) -> Optional[DetectionResult]:
    """Try multilingual schema matching for high-confidence matches."""
    helpers = _get_helper_functions()
    schema_matcher = helpers['_get_fuzzy_schema_matcher']()
    if schema_matcher:
        schema_result = schema_matcher.match(text_lower)
        if schema_result and schema_result.matched:
            # Accept if confidence is high OR if phrase is contained within input
            if (schema_result.confidence >= 0.85 or 
                (schema_result.confidence >= 0.7 and 
                 schema_matcher._normalize(schema_result.phrase) in text_lower)):
                return DetectionResult(
                    domain=schema_result.domain,
                    intent=schema_result.intent,
                    confidence=schema_result.confidence,
                    matched_keyword=schema_result.phrase,
                )
    return None


def _detect_schema_fallback(self, text_lower: str) -> Optional[DetectionResult]:
    """Fallback: Try multilingual fuzzy schema matching."""
    helpers = _get_helper_functions()
    schema_matcher = helpers['_get_fuzzy_schema_matcher']()
    if schema_matcher:
        schema_result = schema_matcher.match(text_lower)
        if schema_result and schema_result.matched:
            return DetectionResult(
                domain=schema_result.domain,
                intent=schema_result.intent,
                confidence=schema_result.confidence,
                matched_keyword=schema_result.phrase,
            )
    return None


def _detect_semantic_fallback(self, text_lower: str) -> Optional[DetectionResult]:
    """Semantic matching fallback for typos and paraphrases (slower)."""
    helpers = _get_helper_functions()
    semantic_matcher = helpers['_get_semantic_matcher']()
    if semantic_matcher:
        try:
            semantic_result = semantic_matcher.match(text_lower)
        except Exception:
            semantic_result = None
        if semantic_result and semantic_result.confidence >= 0.9:
            return DetectionResult(
                domain=semantic_result.domain,
                intent=semantic_result.intent,
                confidence=semantic_result.confidence,
                matched_keyword=f"semantic:{semantic_result.matched_phrase}",
            )
    return None


def _detect_fuzzy_match(self, text_lower: str) -> Optional[DetectionResult]:
    """Try fuzzy matching if available."""
    helpers = _get_helper_functions()
    if helpers['fuzz'] is not None and helpers['process'] is not None:
        return self._detect_best_from_fuzzy(text_lower)
    return None


def _detect_explicit_matches(self, text_lower: str) -> Optional[DetectionResult]:
    """Detect explicit domain-specific matches."""
    # SQL DROP
    sql_context, sql_explicit = self._compute_sql_context(text_lower)
    sql_drop = self._detect_sql_drop_table(text_lower, sql_context=sql_context, sql_explicit=sql_explicit)
    if sql_drop is not None:
        return sql_drop

    # Docker
    docker_explicit = self._detect_explicit_docker(text_lower)
    if docker_explicit is not None:
        return docker_explicit

    # Kubernetes
    k8s_explicit = self._detect_explicit_kubernetes(text_lower)
    if k8s_explicit is not None:
        return k8s_explicit

    # System reboot
    system_reboot = self._detect_explicit_system_reboot(text_lower)
    if system_reboot is not None:
        return system_reboot

    # Service restart
    service_restart = self._detect_explicit_service_restart(text_lower)
    if service_restart is not None:
        return service_restart

    return None


def _detect_pattern_matches(self, text_lower: str) -> Optional[DetectionResult]:
    """Detect matches from priority intents and general patterns."""
    sql_context, sql_explicit = self._compute_sql_context(text_lower)

    # Try priority intents first
    priority_match = self._detect_best_from_priority_intents(
        text_lower,
        sql_context=sql_context,
        sql_explicit=sql_explicit,
    )
    if priority_match is not None:
        return priority_match

    # Then try general patterns
    best_match = self._detect_best_from_patterns(
        text_lower,
        sql_context=sql_context,
        sql_explicit=sql_explicit,
    )
    if best_match is not None:
        return best_match

    return None


# Apply the refactored methods to KeywordIntentDetector
def apply_refactor_to_keyword_detector():
    """Apply the refactored _detect_normalized method to KeywordIntentDetector."""
    from nlp2cmd.generation.keywords import KeywordIntentDetector
    
    # Store original method
    original_detect_normalized = KeywordIntentDetector._detect_normalized
    
    def _detect_normalized(self, text_lower: str) -> DetectionResult:
        """Refactored detect method with reduced complexity."""
        # Try ML classifier first
        result = _detect_ml_classifier(self, text_lower)
        if result is not None:
            return result
        
        # Try schema matching
        result = _detect_schema_matcher(self, text_lower)
        if result is not None:
            return result
        
        # ML classifier fallback for medium confidence
        result = _detect_ml_medium_confidence(self)
        if result is not None:
            return result
        
        # Fast path
        fast_path = self._detect_fast_path(text_lower)
        if fast_path is not None:
            return fast_path
        
        # Explicit matches
        result = _detect_explicit_matches(self, text_lower)
        if result is not None:
            return result
        
        # Pattern matches
        result = _detect_pattern_matches(self, text_lower)
        if result is not None:
            return result
        
        # Fuzzy matching
        result = _detect_fuzzy_match(self, text_lower)
        if result is not None:
            return result
        
        # Schema fallback
        result = _detect_schema_fallback(self, text_lower)
        if result is not None:
            return result
        
        # Semantic fallback
        result = _detect_semantic_fallback(self, text_lower)
        if result is not None:
            return result
        
        # No match found
        return DetectionResult(
            domain='unknown',
            intent='unknown',
            confidence=0.0,
            matched_keyword=None,
        )
    
    # Replace the method
    KeywordIntentDetector._detect_normalized = _detect_normalized
    KeywordIntentDetector._last_ml_result = None  # Instance variable for fallback
    
    return original_detect_normalized


if __name__ == "__main__":
    # Apply the refactor
    original = apply_refactor_to_keyword_detector()
    print("✅ Refactored _detect_normalized to reduce cyclomatic complexity")
    print(f"Original method: {original.__name__ if hasattr(original, '__name__') else 'method'}")
