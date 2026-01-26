"""
Semantic Similarity Matcher using Sentence Embeddings.

Uses sentence-transformers for high-accuracy semantic matching.
Handles typos, synonyms, and paraphrases effectively.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import numpy as np

# Lazy imports for optional dependencies
_sentence_transformers_available = None
_model_instance = None


def _check_sentence_transformers():
    global _sentence_transformers_available
    if _sentence_transformers_available is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformers_available = True
        except ImportError:
            _sentence_transformers_available = False
    return _sentence_transformers_available


@dataclass
class SemanticMatch:
    """Result of semantic matching."""
    intent: str
    domain: str
    confidence: float
    matched_phrase: str
    similarity_score: float
    method: str = "semantic_embedding"


@dataclass
class IntentEmbedding:
    """Stored embedding for an intent phrase."""
    phrase: str
    intent: str
    domain: str
    embedding: np.ndarray
    language: str = "multi"


class SemanticMatcher:
    """
    Semantic similarity matcher using sentence embeddings.
    
    Features:
    - Handles typos and paraphrases
    - Multilingual support (Polish, English, German, etc.)
    - Cosine similarity for matching
    - Configurable threshold
    
    Example:
        matcher = SemanticMatcher()
        matcher.add_intent("list files", "shell", "list")
        result = matcher.match("show me all files")
        # result.intent = "list", result.confidence = 0.87
    """
    
    # Multilingual model that works well for Polish and English
    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        threshold: float = 0.7,
        cache_path: Optional[Path] = None
    ):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.threshold = threshold
        self.cache_path = cache_path
        self.model = None
        self.intent_embeddings: list[IntentEmbedding] = []
        self._embedding_matrix = None
        self._is_loaded = False
    
    def _get_model(self):
        """Lazy load the sentence transformer model."""
        global _model_instance
        
        if self.model is not None:
            return self.model
        
        if not _check_sentence_transformers():
            return None
        
        # Use singleton for the default model
        if self.model_name == self.DEFAULT_MODEL and _model_instance is not None:
            self.model = _model_instance
            return self.model
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            
            if self.model_name == self.DEFAULT_MODEL:
                _model_instance = self.model
            
            return self.model
        except Exception:
            return None
    
    def add_intent(self, phrase: str, domain: str, intent: str, language: str = "multi"):
        """Add an intent phrase for matching."""
        model = self._get_model()
        if model is None:
            return
        
        embedding = model.encode(phrase, convert_to_numpy=True)
        
        self.intent_embeddings.append(IntentEmbedding(
            phrase=phrase,
            intent=intent,
            domain=domain,
            embedding=embedding,
            language=language
        ))
        
        # Invalidate cached matrix
        self._embedding_matrix = None
    
    def add_intents_batch(self, intents: list[tuple[str, str, str, str]]):
        """
        Add multiple intent phrases efficiently.
        
        Args:
            intents: List of (phrase, domain, intent, language) tuples
        """
        model = self._get_model()
        if model is None:
            return
        
        phrases = [p[0] for p in intents]
        embeddings = model.encode(phrases, convert_to_numpy=True, show_progress_bar=False)
        
        for (phrase, domain, intent, language), embedding in zip(intents, embeddings):
            self.intent_embeddings.append(IntentEmbedding(
                phrase=phrase,
                intent=intent,
                domain=domain,
                embedding=embedding,
                language=language
            ))
        
        self._embedding_matrix = None
    
    def _get_embedding_matrix(self) -> Optional[np.ndarray]:
        """Get or build the embedding matrix for fast similarity computation."""
        if self._embedding_matrix is not None:
            return self._embedding_matrix
        
        if not self.intent_embeddings:
            return None
        
        self._embedding_matrix = np.vstack([ie.embedding for ie in self.intent_embeddings])
        return self._embedding_matrix
    
    def match(self, text: str, top_k: int = 3) -> Optional[SemanticMatch]:
        """
        Find the best matching intent for the given text.
        
        Args:
            text: Input text to match
            top_k: Number of candidates to consider
            
        Returns:
            SemanticMatch if confidence >= threshold, else None
        """
        model = self._get_model()
        if model is None or not self.intent_embeddings:
            return None
        
        # Encode query
        query_embedding = model.encode(text, convert_to_numpy=True)
        
        # Get embedding matrix
        matrix = self._get_embedding_matrix()
        if matrix is None:
            return None
        
        # Compute cosine similarities
        similarities = self._cosine_similarity(query_embedding, matrix)
        
        # Get top match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score < self.threshold:
            return None
        
        best_intent = self.intent_embeddings[best_idx]
        
        return SemanticMatch(
            intent=best_intent.intent,
            domain=best_intent.domain,
            confidence=float(best_score),
            matched_phrase=best_intent.phrase,
            similarity_score=float(best_score),
            method="semantic_embedding"
        )
    
    def match_all(self, text: str, top_k: int = 5) -> list[SemanticMatch]:
        """Get top-k matches with scores."""
        model = self._get_model()
        if model is None or not self.intent_embeddings:
            return []
        
        query_embedding = model.encode(text, convert_to_numpy=True)
        matrix = self._get_embedding_matrix()
        if matrix is None:
            return []
        
        similarities = self._cosine_similarity(query_embedding, matrix)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score < self.threshold * 0.5:  # Allow lower threshold for alternatives
                continue
            
            intent = self.intent_embeddings[idx]
            results.append(SemanticMatch(
                intent=intent.intent,
                domain=intent.domain,
                confidence=float(score),
                matched_phrase=intent.phrase,
                similarity_score=float(score),
                method="semantic_embedding"
            ))
        
        return results
    
    @staticmethod
    def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all embeddings."""
        query_norm = query / (np.linalg.norm(query) + 1e-8)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
        return np.dot(matrix_norm, query_norm)
    
    def save(self, path: Path):
        """Save embeddings to disk (excludes model)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings as numpy arrays
        data = {
            'model_name': self.model_name,
            'threshold': self.threshold,
            'intents': [
                {
                    'phrase': ie.phrase,
                    'intent': ie.intent,
                    'domain': ie.domain,
                    'embedding': ie.embedding.tolist(),
                    'language': ie.language,
                }
                for ie in self.intent_embeddings
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def load(self, path: Path) -> bool:
        """Load embeddings from disk."""
        path = Path(path)
        if not path.exists():
            return False
        
        try:
            with open(path) as f:
                data = json.load(f)
            
            self.model_name = data.get('model_name', self.DEFAULT_MODEL)
            self.threshold = data.get('threshold', 0.7)
            
            self.intent_embeddings = [
                IntentEmbedding(
                    phrase=ie['phrase'],
                    intent=ie['intent'],
                    domain=ie['domain'],
                    embedding=np.array(ie['embedding']),
                    language=ie.get('language', 'multi'),
                )
                for ie in data.get('intents', [])
            ]
            
            self._embedding_matrix = None
            self._is_loaded = True
            return True
        except Exception:
            return False
    
    @property
    def is_ready(self) -> bool:
        return len(self.intent_embeddings) > 0


def create_semantic_matcher_from_phrases(phrases_path: Path) -> SemanticMatcher:
    """Create a SemanticMatcher from multilingual_phrases.json."""
    matcher = SemanticMatcher()
    
    if not phrases_path.exists():
        return matcher
    
    with open(phrases_path) as f:
        data = json.load(f)
    
    intents = []
    for phrase_entry in data.get('phrases', []):
        phrase = phrase_entry.get('phrase', '')
        domain = phrase_entry.get('domain', 'unknown')
        intent = phrase_entry.get('intent', 'unknown')
        language = phrase_entry.get('language', 'multi')
        aliases = phrase_entry.get('aliases', [])
        
        # Add main phrase
        intents.append((phrase, domain, intent, language))
        
        # Add aliases
        for alias in aliases:
            intents.append((alias, domain, intent, language))
    
    if intents:
        matcher.add_intents_batch(intents)
    
    return matcher


# Singleton instance
_semantic_matcher_instance: Optional[SemanticMatcher] = None


def get_semantic_matcher() -> Optional[SemanticMatcher]:
    """
    Get or create semantic matcher singleton.
    
    Loads from cache if available, otherwise builds from phrases.
    """
    global _semantic_matcher_instance
    
    if not _check_sentence_transformers():
        return None
    
    if _semantic_matcher_instance is not None and _semantic_matcher_instance.is_ready:
        return _semantic_matcher_instance
    
    # Try to load from cache
    cache_path = Path(__file__).parent.parent.parent.parent / "data" / "semantic_embeddings.json"
    
    _semantic_matcher_instance = SemanticMatcher(cache_path=cache_path)
    
    if cache_path.exists():
        if _semantic_matcher_instance.load(cache_path):
            return _semantic_matcher_instance
    
    # Build from phrases
    phrases_path = Path(__file__).parent.parent.parent.parent / "data" / "multilingual_phrases.json"
    if phrases_path.exists():
        try:
            _semantic_matcher_instance = create_semantic_matcher_from_phrases(phrases_path)
            # Cache for faster loading next time
            _semantic_matcher_instance.save(cache_path)
        except Exception:
            pass
    
    return _semantic_matcher_instance if _semantic_matcher_instance.is_ready else None
