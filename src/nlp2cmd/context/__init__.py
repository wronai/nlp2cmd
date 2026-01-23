"""
Context-aware command disambiguation.

Uses history to suggest and disambiguate commands when queries are unclear.
"""

from nlp2cmd.context.disambiguator import CommandDisambiguator, DisambiguationResult

__all__ = [
    "CommandDisambiguator",
    "DisambiguationResult",
]
