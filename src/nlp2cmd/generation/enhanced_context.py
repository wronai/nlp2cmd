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

try:
    from nlp2cmd.generation.enhanced_context import get_enhanced_detector
    ENHANCED_CONTEXT_AVAILABLE = True
except ImportError:
    ENHANCED_CONTEXT_AVAILABLE = False

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


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
        """Build semantic index for all domain/intent combinations."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return
        
        self.semantic_index = {}
        
        # Load patterns for semantic indexing
        patterns_file = Path("/home/tom/github/wronai/nlp2cmd/data/patterns.json")
        if patterns_file.exists():
            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            
            # Skip schema field and iterate domains
            for domain, intents in patterns.items():
                if domain.startswith('$'):  # Skip schema field
                    continue
                if isinstance(intents, dict):
                    for intent, pattern_list in intents.items():
                        if isinstance(pattern_list, list):
                            # Add patterns to semantic index
                            for pattern in pattern_list:
                                if pattern not in self.semantic_index:
                                    self.semantic_index[pattern] = {}
                                self.semantic_index[pattern][domain] = intent
        
        # Add web schema actions to semantic index
        if 'browser' in self.schemas:
            for site_name, schema in self.schemas['browser'].items():
                if 'actions' in schema:
                    for action in schema['actions']:
                        action_name = action.get('name', '')
                        description = action.get('description', '')
                        examples = action.get('examples', [])
                        
                        # Add action name
                        if action_name:
                            if action_name not in self.semantic_index:
                                self.semantic_index[action_name] = {}
                            self.semantic_index[action_name]['browser'] = 'web_action'
                        
                        # Add description
                        if description:
                            if description not in self.semantic_index:
                                self.semantic_index[description] = {}
                            self.semantic_index[description]['browser'] = 'web_action'
                        
                        # Add examples
                        for example in examples:
                            if example not in self.semantic_index:
                                self.semantic_index[example] = {}
                            self.semantic_index[example]['browser'] = 'web_action'
        
        # Encode all semantic keys
        self.semantic_embeddings = {}
        for semantic_key in self.semantic_index.keys():
            try:
                embedding = self.sentence_model.encode(semantic_key, convert_to_tensor=True)
                self.semantic_embeddings[semantic_key] = embedding
            except Exception as e:
                print(f"Failed to encode semantic key '{semantic_key}': {e}")
                continue
    
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
                
                # Extract user-related entities
                user_keywords = ['user', 'użytkownik', 'użytkownika', 'usera', 'userów', 'użytkowników']
                user_found = any(keyword.lower() in user_keywords for keyword in keywords)
                if user_found:
                    entities['user'] = 'current'  # Default to current user
                    # Check for specific user names
                    for token, pos in pos_tags:
                        if pos == 'NNP' and token.lower() not in user_keywords:
                            entities['user'] = token
                            break
                
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
        
        # Add regex entities (NEW)
        try:
            from ..generation.regex import RegexEntityExtractor
            regex_extractor = RegexEntityExtractor()
            regex_entities = regex_extractor.extract(text, 'shell')
            
            # Merge regex entities with existing entities
            for key, value in regex_entities.entities.items():
                if key not in entities:
                    entities[key] = value
                elif key == 'path' and entities.get('path') == '.':
                    # Prefer regex path over NLTK path
                    entities[key] = value
        except Exception as e:
            print(f"Regex entity extraction failed: {e}")
        
        return entities
    
    def _calculate_keyword_similarity(self, query: str, pattern: str) -> float:
        """Calculate keyword similarity with fuzzy matching."""
        if not pattern:
            return 0.0
        
        query_words = set(query.lower().split())
        pattern_words = set(pattern.lower().split())
        
        # Exact match
        if query_words == pattern_words:
            return 1.0
        
        # Jaccard similarity
        intersection = query_words.intersection(pattern_words)
        union = query_words.union(pattern_words)
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Fuzzy matching for typo tolerance
        fuzzy_score = 0.0
        if FUZZY_AVAILABLE and len(query) > 3 and len(pattern) > 3:
            # Use rapidfuzz for fuzzy string matching
            fuzzy_score = fuzz.ratio(query.lower(), pattern.lower()) / 100.0
        
        # Combine scores (70% Jaccard, 30% fuzzy)
        combined_score = 0.7 * jaccard + 0.3 * fuzzy_score
        
        return combined_score
    
    def _calculate_semantic_similarity(self, query: str, domain: str, intent: str) -> float:
        """Calculate semantic similarity using sentence transformers."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return 0.0
        
        # Try to find patterns for this domain/intent combination
        patterns_file = Path("/home/tom/github/wronai/nlp2cmd/data/patterns.json")
        if patterns_file.exists():
            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            
            # Get patterns for this domain/intent
            domain_patterns = patterns.get(domain, {})
            intent_patterns = domain_patterns.get(intent, [])
            
            if intent_patterns:
                try:
                    # Encode query and patterns using sentence_model
                    query_embedding = self.sentence_model.encode([query])
                    pattern_embeddings = self.sentence_model.encode(intent_patterns)
                    
                    # Calculate cosine similarity
                    similarities = cosine_similarity(query_embedding, pattern_embeddings)[0]
                    
                    # Return maximum similarity
                    return float(max(similarities)) if len(similarities) > 0 else 0.0
                    
                except Exception as e:
                    print(f"Semantic similarity calculation failed: {e}")
                    return 0.0
        
        # Fallback: use semantic index if available
        semantic_key = f"{domain}/{intent}"
        if semantic_key in self.semantic_index:
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
        
        return 0.0
    
    def _calculate_context_score(self, query: str, domain: str, intent: str, entities: Dict[str, Any]) -> float:
        """Calculate context-based score using schema information."""
        score = 0.0
        
        # Domain schema availability
        if domain in self.schemas:
            score += 0.3
        
        # Template availability
        if domain in self.templates and intent in self.templates[domain]:
            score += 0.3
        
        # Entity matching bonus
        if 'keywords' in entities:
            keywords = entities['keywords']
            if any(keyword in domain or keyword in intent for keyword in keywords):
                score += 0.2
        
        # Language detection bonus
        if entities.get('language') in ['pl', 'en']:
            score += 0.2
        
        # Shell domain boost for file/user operations
        if domain == 'shell':
            shell_keywords = ['plik', 'folder', 'użytkownik', 'uzytkownik', 'pokaż', 'pokaz', 'lista', 'list']
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in shell_keywords):
                score += 0.3
        
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
