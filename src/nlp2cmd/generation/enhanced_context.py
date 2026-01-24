"""
Enhanced Context Understanding with NLP Libraries.

Uses multiple NLP libraries to better understand context from schemas,
templates, and user queries for improved intent detection.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Try to import advanced NLP libraries
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    from nltk.chunk import ne_chunk
    from nltk.tag import pos_tag
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


@dataclass
class ContextualMatch:
    """Enhanced match with semantic similarity."""
    query: str
    pattern: str
    keyword_score: float
    semantic_score: float
    context_score: float
    combined_score: float
    domain: str
    intent: str
    entities: Dict[str, Any]


class EnhancedContextDetector:
    """Enhanced context detection using multiple NLP approaches."""
    
    def __init__(self):
        self.schemas: Dict[str, Any] = {}
        self.templates: Dict[str, Any] = {}
        self.semantic_index: Dict[str, np.ndarray] = {}
        self.stop_words: set = set()
        
        # Initialize NLP components
        self._initialize_nlp()
        
        # Load schemas and templates
        self._load_schemas_and_templates()
        
        # Build semantic index
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._build_semantic_index()
    
    def _initialize_nlp(self):
        """Initialize NLP libraries."""
        global NLTK_AVAILABLE
        if NLTK_AVAILABLE:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
                
                # Get Polish and English stop words
                self.stop_words = set(stopwords.words('english'))
                try:
                    self.stop_words.update(stopwords.words('polish'))
                except:
                    pass  # Polish stopwords not available
                    
                self.lemmatizer = WordNetLemmatizer()
            except Exception as e:
                print(f"NLTK initialization failed: {e}")
                NLTK_AVAILABLE = False
        
        global SENTENCE_TRANSFORMERS_AVAILABLE
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use multilingual model for Polish/English
                self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                print(f"Sentence transformers initialization failed: {e}")
                SENTENCE_TRANSFORMERS_AVAILABLE = False
        
        global TRANSFORMERS_AVAILABLE
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use lightweight multilingual model
                self.tokenizer = AutoTokenizer.from_pretrained('bert-base-multilingual-cased')
                self.model = AutoModel.from_pretrained('bert-base-multilingual-cased')
            except Exception as e:
                print(f"Transformers initialization failed: {e}")
                TRANSFORMERS_AVAILABLE = False
    
    def _load_schemas_and_templates(self):
        """Load command schemas and templates for context."""
        # Load command schemas
        schemas_path = Path("/home/tom/github/wronai/nlp2cmd/command_schemas")
        if schemas_path.exists():
            for domain_dir in schemas_path.iterdir():
                if domain_dir.is_dir():
                    domain = domain_dir.name
                    self.schemas[domain] = {}
                    for schema_file in domain_dir.glob("*.json"):
                        try:
                            with open(schema_file, 'r') as f:
                                schema = json.load(f)
                                self.schemas[domain][schema_file.stem] = schema
                        except Exception as e:
                            print(f"Failed to load schema {schema_file}: {e}")
        
        # Load web schemas from sites subdirectory
        sites_path = schemas_path / "sites"
        if sites_path.exists():
            for site_file in sites_path.glob("*.json"):
                try:
                    with open(site_file, 'r') as f:
                        schema = json.load(f)
                        site_name = site_file.stem
                        if 'actions' in schema:
                            # Extract web actions for browser domain
                            if 'browser' not in self.schemas:
                                self.schemas['browser'] = {}
                            self.schemas['browser'][site_name] = schema
                except Exception as e:
                    print(f"Failed to load web schema {site_file}: {e}")
        
        # Load templates
        templates_path = Path("/home/tom/github/wronai/nlp2cmd/data/templates.json")
        if templates_path.exists():
            try:
                with open(templates_path, 'r') as f:
                    self.templates = json.load(f)
            except Exception as e:
                print(f"Failed to load templates: {e}")
    
    def _build_semantic_index(self):
        """Build semantic index for patterns and templates."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return
        
        all_patterns = []
        pattern_keys = []
        
        # Extract patterns from templates
        for domain, intents in self.templates.items():
            if isinstance(intents, dict):
                for intent, template in intents.items():
                    # Create description from template
                    description = f"{domain} {intent} {template}"
                    all_patterns.append(description)
                    pattern_keys.append((domain, intent, template))
        
        # Extract patterns from web schemas
        for domain, schemas in self.schemas.items():
            if domain == 'browser':
                for site_name, schema in schemas.items():
                    if 'actions' in schema:
                        for action in schema['actions']:
                            # Create description from web action
                            action_desc = action.get('description', '')
                            action_name = action.get('name', '')
                            description = f"browser {action_name} {action_desc}"
                            all_patterns.append(description)
                            pattern_keys.append(('browser', 'web_action', action))
        
        # Encode all patterns
        if all_patterns:
            embeddings = self.sentence_model.encode(all_patterns)
            for i, key in enumerate(pattern_keys):
                domain, intent, template_or_action = key
                semantic_key = f"{domain}/{intent}"
                if semantic_key not in self.semantic_index:
                    self.semantic_index[semantic_key] = []
                self.semantic_index[semantic_key].append({
                    'embedding': embeddings[i],
                    'template': template_or_action,
                    'domain': domain,
                    'intent': intent
                })
    
    def _preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing."""
        if not isinstance(text, str):
            return ""
        
        # Normalize Polish characters
        text = text.lower()
        polish_map = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        for pl, en in polish_map.items():
            text = text.replace(pl, en)
        
        # Remove extra whitespace and punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities using multiple NLP approaches."""
        entities = {}
        
        # Language detection
        if LANGDETECT_AVAILABLE:
            try:
                entities['language'] = detect(text)
            except:
                entities['language'] = 'unknown'
        
        # NLTK entity extraction
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text)
                pos_tags = pos_tag(tokens)
                
                # Extract named entities
                tree = ne_chunk(pos_tags)
                named_entities = []
                for subtree in tree:
                    if hasattr(subtree, 'label'):
                        entity_name = ' '.join([token for token, pos in subtree.leaves()])
                        named_entities.append({'type': subtree.label(), 'name': entity_name})
                
                entities['named_entities'] = named_entities
                
                # Extract keywords (nouns and verbs)
                keywords = [token for token, pos in pos_tags if pos.startswith(('NN', 'VB'))]
                entities['keywords'] = keywords
                
            except Exception as e:
                print(f"NLTK entity extraction failed: {e}")
        
        # TextBlob sentiment and noun phrases
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                entities['sentiment'] = {
                    'polarity': blob.sentiment.polarity,
                    'subjectivity': blob.sentiment.subjectivity
                }
                entities['noun_phrases'] = blob.noun_phrases
            except Exception as e:
                print(f"TextBlob analysis failed: {e}")
        
        return entities
    
    def _calculate_keyword_similarity(self, query: str, pattern: str) -> float:
        """Calculate keyword-based similarity."""
        query_words = set(self._preprocess_text(query).split())
        pattern_words = set(self._preprocess_text(pattern).split())
        
        # Remove stop words
        query_words -= self.stop_words
        pattern_words -= self.stop_words
        
        if not query_words or not pattern_words:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words.intersection(pattern_words)
        union = query_words.union(pattern_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_semantic_similarity(self, query: str, domain: str, intent: str) -> float:
        """Calculate semantic similarity using sentence transformers."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return 0.0
        
        semantic_key = f"{domain}/{intent}"
        if semantic_key not in self.semantic_index:
            return 0.0
        
        try:
            query_embedding = self.sentence_model.encode([query])
            
            # Calculate similarity with all embeddings for this semantic key
            similarities = []
            for item in self.semantic_index[semantic_key]:
                pattern_embedding = item['embedding'].reshape(1, -1)
                similarity = cosine_similarity(query_embedding, pattern_embedding)[0][0]
                similarities.append(similarity)
            
            # Return the maximum similarity
            return float(max(similarities)) if similarities else 0.0
        except Exception as e:
            print(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_context_score(self, query: str, domain: str, intent: str, entities: Dict[str, Any]) -> float:
        """Calculate context-based score using schema information."""
        score = 0.0
        
        # Check if domain has relevant schemas
        if domain in self.schemas:
            score += 0.3
        
        # Check if intent exists in templates
        if domain in self.templates and intent in self.templates[domain]:
            score += 0.3
        
        # Bonus for entity matches
        if 'keywords' in entities:
            keywords = entities['keywords']
            if any(keyword in domain or keyword in intent for keyword in keywords):
                score += 0.2
        
        # Language bonus
        if entities.get('language') in ['pl', 'en']:
            score += 0.2
        
        return min(score, 1.0)
    
    def detect_intent_with_context(self, query: str) -> List[ContextualMatch]:
        """Enhanced intent detection with context understanding."""
        entities = self._extract_entities(query)
        processed_query = self._preprocess_text(query)
        
        matches = []
        
        # Check all domain/intent combinations
        for domain, intents in self.templates.items():
            if not isinstance(intents, dict):
                continue
            
            for intent, template in intents.items():
                # Calculate different similarity scores
                keyword_score = self._calculate_keyword_similarity(processed_query, f"{domain} {intent}")
                semantic_score = self._calculate_semantic_similarity(query, domain, intent)
                context_score = self._calculate_context_score(query, domain, intent, entities)
                
                # Combined score with weights
                combined_score = (
                    0.4 * keyword_score +
                    0.4 * semantic_score +
                    0.2 * context_score
                )
                
                if combined_score > 0.1:  # Threshold for relevance
                    match = ContextualMatch(
                        query=query,
                        pattern=f"{domain}/{intent}",
                        keyword_score=keyword_score,
                        semantic_score=semantic_score,
                        context_score=context_score,
                        combined_score=combined_score,
                        domain=domain,
                        intent=intent,
                        entities=entities
                    )
                    matches.append(match)
        
        # Sort by combined score
        matches.sort(key=lambda x: x.combined_score, reverse=True)
        
        return matches
    
    def get_best_match(self, query: str) -> Optional[ContextualMatch]:
        """Get the best match for a query."""
        matches = self.detect_intent_with_context(query)
        return matches[0] if matches else None
    
    def explain_detection(self, query: str) -> Dict[str, Any]:
        """Explain the detection process with scores."""
        matches = self.detect_intent_with_context(query)
        entities = self._extract_entities(query)
        
        explanation = {
            'query': query,
            'entities': entities,
            'matches': []
        }
        
        for match in matches[:5]:  # Top 5 matches
            explanation['matches'].append({
                'domain': match.domain,
                'intent': match.intent,
                'combined_score': match.combined_score,
                'keyword_score': match.keyword_score,
                'semantic_score': match.semantic_score,
                'context_score': match.context_score,
                'reasoning': self._generate_reasoning(match)
            })
        
        return explanation
    
    def _generate_reasoning(self, match: ContextualMatch) -> str:
        """Generate human-readable reasoning for the match."""
        reasons = []
        
        if match.keyword_score > 0.5:
            reasons.append(f"Strong keyword overlap ({match.keyword_score:.2f})")
        
        if match.semantic_score > 0.5:
            reasons.append(f"High semantic similarity ({match.semantic_score:.2f})")
        
        if match.context_score > 0.5:
            reasons.append(f"Good context match ({match.context_score:.2f})")
        
        if match.entities.get('language') in ['pl', 'en']:
            reasons.append(f"Language detected: {match.entities['language']}")
        
        return "; ".join(reasons) if reasons else "Low confidence match"


# Global instance for easy access
enhanced_detector = None

def get_enhanced_detector() -> EnhancedContextDetector:
    """Get or create enhanced detector instance."""
    global enhanced_detector
    if enhanced_detector is None:
        enhanced_detector = EnhancedContextDetector()
    return enhanced_detector
