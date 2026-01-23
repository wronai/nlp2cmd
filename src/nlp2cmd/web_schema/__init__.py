"""
Web schema extraction and learning module.

Provides:
- Schema extraction from web pages (Opcja B)
- Interaction history tracking (Opcja C)
- Schema learning from user behavior
"""

from nlp2cmd.web_schema.extractor import WebSchemaExtractor, extract_web_schema
from nlp2cmd.web_schema.history import InteractionHistory, InteractionRecord

__all__ = [
    "WebSchemaExtractor",
    "extract_web_schema",
    "InteractionHistory",
    "InteractionRecord",
]
