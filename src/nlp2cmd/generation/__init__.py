"""
Text → Multi-DSL Generation Module.

This module provides iterative text-to-DSL generation capabilities:
- Rule-based intent detection (no LLM)
- Regex entity extraction
- Template-based generation
- LLM integration (optional)
- Hybrid rule+LLM approach
"""

from nlp2cmd.generation.keywords import KeywordIntentDetector
from nlp2cmd.generation.regex import RegexEntityExtractor
from nlp2cmd.generation.templates import TemplateGenerator
from nlp2cmd.generation.pipeline import RuleBasedPipeline

__all__ = [
    "KeywordIntentDetector",
    "RegexEntityExtractor",
    "TemplateGenerator",
    "RuleBasedPipeline",
]
