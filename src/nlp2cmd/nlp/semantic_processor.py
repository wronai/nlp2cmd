"""Semantic processing pipeline built from modular NLP components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from nlp2cmd.nlp.entity_recognizer import EntityRecognizer, RecognizedEntity
from nlp2cmd.nlp.intent_classifier import IntentClassifier, IntentResult


@dataclass
class SemanticResult:
    """Combined result of intent classification and entity recognition."""

    intent: IntentResult
    entities: list[RecognizedEntity]
    entity_map: dict[str, object]


class SemanticProcessor:
    """Pipeline that combines intent classification and entity recognition."""

    def __init__(
        self,
        classifier: Optional[IntentClassifier] = None,
        recognizer: Optional[EntityRecognizer] = None,
    ) -> None:
        self.classifier = classifier or IntentClassifier()
        self.recognizer = recognizer or EntityRecognizer()

    def process(self, text: str, domain: Optional[str] = None) -> SemanticResult:
        """Process text into intent + entities."""
        intent = self.classifier.classify(text)
        target_domain = domain or intent.domain
        entities = self.recognizer.recognize(text, target_domain)
        entity_map = {entity.name: entity.value for entity in entities}
        return SemanticResult(intent=intent, entities=entities, entity_map=entity_map)
