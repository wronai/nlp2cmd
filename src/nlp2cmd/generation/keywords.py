"""
Iteration 1: Rule-Based Intent Detection.

Keyword matching for intent and domain detection without LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import json
import os
from pathlib import Path
import re

from nlp2cmd.utils.data_files import find_data_files

# Lazy import for polish support to avoid circular imports
_polish_support = None

def _get_polish_support():
    """Lazy load Polish support to avoid circular imports."""
    global _polish_support
    if _polish_support is None:
        try:
            from nlp2cmd.polish_support import polish_support
            _polish_support = polish_support
        except ImportError:
            _polish_support = False  # Mark as unavailable
    return _polish_support if _polish_support else None

# Lazy import for multilingual fuzzy schema matcher
_fuzzy_schema_matcher = None

def _get_fuzzy_schema_matcher():
    """Lazy load FuzzySchemaMatcher with multilingual phrases."""
    global _fuzzy_schema_matcher
    if _fuzzy_schema_matcher is None:
        try:
            from nlp2cmd.generation.fuzzy_schema_matcher import FuzzySchemaMatcher
            from pathlib import Path
            
            # Try to load multilingual phrases schema
            schema_paths = [
                Path(__file__).parent.parent.parent.parent / "data" / "multilingual_phrases.json",
                Path("data/multilingual_phrases.json"),
                Path("multilingual_phrases.json"),
            ]
            
            matcher = FuzzySchemaMatcher()
            for path in schema_paths:
                if path.exists():
                    matcher.load_schema(path)
                    break
            
            # If no schema loaded, use default phrases
            if not matcher.phrases:
                from nlp2cmd.generation.fuzzy_schema_matcher import create_multilingual_matcher
                matcher = create_multilingual_matcher()
            
            _fuzzy_schema_matcher = matcher
        except ImportError:
            _fuzzy_schema_matcher = False
    return _fuzzy_schema_matcher if _fuzzy_schema_matcher else None

# Lazy import for ML intent classifier (TF-IDF + SVM)
_ml_classifier = None

def _get_ml_classifier():
    """Lazy load ML intent classifier for high-accuracy predictions."""
    global _ml_classifier
    if _ml_classifier is None:
        try:
            from nlp2cmd.generation.ml_intent_classifier import get_ml_classifier
            _ml_classifier = get_ml_classifier()
            if _ml_classifier is None:
                _ml_classifier = False  # Mark as unavailable
        except ImportError:
            _ml_classifier = False
    return _ml_classifier if _ml_classifier else None

# Lazy import for semantic matcher (sentence embeddings) - use optimized version
_semantic_matcher = None

def _get_semantic_matcher():
    """Lazy load optimized semantic matcher for embedding-based similarity."""
    global _semantic_matcher
    if _semantic_matcher is None:
        try:
            # Try optimized version first
            from nlp2cmd.generation.semantic_matcher_optimized import get_optimized_semantic_matcher
            _semantic_matcher = get_optimized_semantic_matcher(preload=False)
            if _semantic_matcher is None:
                _semantic_matcher = False
        except ImportError:
            try:
                # Fallback to original
                from nlp2cmd.generation.semantic_matcher import get_semantic_matcher
                _semantic_matcher = get_semantic_matcher()
                if _semantic_matcher is None:
                    _semantic_matcher = False
            except ImportError:
                _semantic_matcher = False
    return _semantic_matcher if _semantic_matcher else None

@staticmethod
def _normalize_polish_text(text: str) -> str:
    """Normalize Polish diacritics to handle typos."""
    text = text.replace('ł', 'l').replace('Ł', 'L')
    text = text.replace('ą', 'a').replace('Ą', 'A')
    text = text.replace('ę', 'e').replace('Ę', 'E')
    text = text.replace('ś', 's').replace('Ś', 'S')
    text = text.replace('ć', 'c').replace('Ć', 'C')
    text = text.replace('ń', 'n').replace('Ń', 'N')
    text = text.replace('ó', 'o').replace('Ó', 'O')
    text = text.replace('ź', 'z').replace('Ź', 'Z')
    text = text.replace('ż', 'z').replace('Ż', 'Z')
    return text

try:
    from rapidfuzz import fuzz, process
except ImportError:
    # rapidfuzz not installed - fuzzy matching disabled
    fuzz = None
    process = None

# spaCy is intentionally imported lazily to keep CLI cold-start fast.
_SPACY = None
_NLP_MODEL = None
_NLP_MODEL_LOAD_ATTEMPTED = False

_ENABLE_SPACY_LEMMATIZATION = str(
    os.environ.get("NLP2CMD_ENABLE_SPACY_LEMMATIZATION")
    or os.environ.get("NLP2CMD_ENABLE_HEAVY_NLP")
    or ""
).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_spacy_model():
    global _SPACY, _NLP_MODEL, _NLP_MODEL_LOAD_ATTEMPTED

    if not _ENABLE_SPACY_LEMMATIZATION:
        return None

    if _NLP_MODEL_LOAD_ATTEMPTED:
        return _NLP_MODEL

    _NLP_MODEL_LOAD_ATTEMPTED = True
    try:
        import spacy as _spacy  # noqa: WPS433
        _SPACY = _spacy
    except Exception:
        _SPACY = None
        _NLP_MODEL = None
        return None

    try:
        _NLP_MODEL = _SPACY.load("pl_core_news_sm")
    except Exception:
        try:
            _NLP_MODEL = _SPACY.load("spacy_pl_model")
        except Exception:
            _NLP_MODEL = None

    return _NLP_MODEL


@dataclass
class DetectionResult:
    """Result of intent detection."""
    
    domain: str
    intent: str
    confidence: float
    matched_keyword: Optional[str] = None
    entities: dict = field(default_factory=dict)


class KeywordIntentDetector:
    """
    Rule-based intent detection using keyword matching.
    
    No LLM needed - uses predefined keyword patterns to detect
    domain (sql, shell, docker, kubernetes) and intent.
    
    Example:
        detector = KeywordIntentDetector()
        result = detector.detect("Pokaż wszystkich użytkowników z tabeli users")
        # result.domain == 'sql', result.intent == 'select'
    """
    
    PATTERNS: dict[str, dict[str, list[str]]] = {}
    
    # Domain-specific boost keywords (increase confidence)
    DOMAIN_BOOSTERS: dict[str, list[str]] = {}
    
    def __init__(
        self,
        patterns: Optional[dict[str, dict[str, list[str]]]] = None,
        custom_patterns: Optional[dict[str, dict[str, list[str]]]] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize keyword detector.
        
        Args:
            patterns: Custom patterns to use (or default PATTERNS)
            confidence_threshold: Minimum confidence to return a match
        """
        self._custom_patterns_provided = patterns is not None or custom_patterns is not None
        self.patterns = patterns or custom_patterns or {}
        self.confidence_threshold = confidence_threshold
        # Initialize with empty defaults - will be loaded from JSON
        self.domain_boosters: dict[str, list[str]] = {}
        self.priority_intents: dict[str, list[str]] = {}
        self.fast_path_browser_keywords: list[str] = []
        self.fast_path_search_keywords: list[str] = []
        self.fast_path_common_images: set[str] = set()

        # Load configuration from JSON files.
        self._load_detector_config_from_json()
        self._load_patterns_from_json()

        if not self.domain_boosters or not self.priority_intents:
            raise FileNotFoundError(
                "Keyword detector config not loaded. Expected keyword_intent_detector_config.json "
                "to be available in the package data dir or user config dir, or set "
                "NLP2CMD_KEYWORD_DETECTOR_CONFIG."
            )
        if not self.patterns:
            raise FileNotFoundError(
                "Keyword patterns not loaded. Expected patterns.json to be available in the package "
                "data dir or user config dir, or set NLP2CMD_PATTERNS_FILE."
            )

    def _load_detector_config_from_json(self) -> None:
        for p in find_data_files(
            explicit_path=os.environ.get("NLP2CMD_KEYWORD_DETECTOR_CONFIG"),
            default_filename="keyword_intent_detector_config.json",
        ):
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue

            boosters = payload.get("domain_boosters")
            if isinstance(boosters, dict):
                for d, items in boosters.items():
                    if not isinstance(d, str) or not d.strip() or not isinstance(items, list):
                        continue
                    clean = [_normalize_polish_text(x.strip()) for x in items if isinstance(x, str) and x.strip()]
                    if not clean:
                        continue
                    key = d.strip()
                    prev = self.domain_boosters.get(key, [])
                    merged: list[str] = []
                    seen: set[str] = set()
                    for s in [*prev, *clean]:
                        k = s.strip().lower()
                        if not k or k in seen:
                            continue
                        seen.add(k)
                        merged.append(s.strip())
                    self.domain_boosters[key] = merged

            priority = payload.get("priority_intents")
            if isinstance(priority, dict):
                for d, items in priority.items():
                    if not isinstance(d, str) or not d.strip() or not isinstance(items, list):
                        continue
                    clean = [_normalize_polish_text(x.strip()) for x in items if isinstance(x, str) and x.strip()]
                    if not clean:
                        continue
                    key = d.strip()
                    prev = self.priority_intents.get(key, [])
                    merged: list[str] = []
                    seen: set[str] = set()
                    for s in [*prev, *clean]:
                        k = s.strip().lower()
                        if not k or k in seen:
                            continue
                        seen.add(k)
                        merged.append(s.strip())
                    self.priority_intents[key] = merged

            fast_path = payload.get("fast_path")
            if isinstance(fast_path, dict):
                b = fast_path.get("browser_keywords")
                if isinstance(b, list):
                    prev = list(self.fast_path_browser_keywords)
                    clean = [_normalize_polish_text(x.strip()) for x in b if isinstance(x, str) and x.strip()]
                    merged: list[str] = []
                    seen: set[str] = set()
                    for s in [*prev, *clean]:
                        k = s.strip().lower()
                        if not k or k in seen:
                            continue
                        seen.add(k)
                        merged.append(s.strip())
                    self.fast_path_browser_keywords = merged

                s = fast_path.get("search_keywords")
                if isinstance(s, list):
                    prev = list(self.fast_path_search_keywords)
                    clean = [_normalize_polish_text(x.strip()) for x in s if isinstance(x, str) and x.strip()]
                    merged: list[str] = []
                    seen: set[str] = set()
                    for ss in [*prev, *clean]:
                        k = ss.strip().lower()
                        if not k or k in seen:
                            continue
                        seen.add(k)
                        merged.append(ss.strip())
                    self.fast_path_search_keywords = merged

                imgs = fast_path.get("common_images")
                if isinstance(imgs, list):
                    for x in imgs:
                        if isinstance(x, str) and x.strip():
                            self.fast_path_common_images.add(x.strip().lower())

    def _load_patterns_from_json(self) -> None:
        """Load patterns from external JSON file with fallback to embedded PATTERNS."""
        if self._custom_patterns_provided:
            return

        base: dict[str, dict[str, list[str]]] = {
            d: {i: [_normalize_polish_text(kw.strip()) for kw in kws if isinstance(kw, str) and kw.strip()] 
                for i, kws in intents.items()}
            for d, intents in self.PATTERNS.items()
        }

        def _dedupe_case_insensitive(items: list[str]) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            for s in items:
                if not isinstance(s, str):
                    continue
                key = s.strip()
                if not key:
                    continue
                k = key.lower()
                if k in seen:
                    continue
                seen.add(k)
                out.append(key)
            return out

        for p in find_data_files(
            explicit_path=os.environ.get("NLP2CMD_PATTERNS_FILE"),
            default_filename="patterns.json",
        ):
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue

            if isinstance(payload, dict):
                for domain, intents in payload.items():
                    if not isinstance(domain, str) or not domain.strip() or not isinstance(intents, dict):
                        continue
                    d = domain.strip()
                    bucket = base.setdefault(d, {})
                    if not isinstance(bucket, dict):
                        continue
                    for intent, keywords in intents.items():
                        if not isinstance(intent, str) or not intent.strip() or not isinstance(keywords, list):
                            continue
                        i = intent.strip()
                        clean = [_normalize_polish_text(kw.strip()) for kw in keywords if isinstance(kw, str) and kw.strip()]
                        if not clean:
                            continue
                        prev = bucket.get(i)
                        prev_list = prev if isinstance(prev, list) else []
                        bucket[i] = _dedupe_case_insensitive([*clean, *prev_list])

        self.patterns = base
    
    # Priority intents - check these first as they are more specific/destructive
    PRIORITY_INTENTS: dict[str, list[str]] = {}

    @staticmethod
    def _match_keyword(text_lower: str, kw: str) -> bool:
        k = (kw or "").strip().lower()
        if not k:
            return False
        if k in {"fold"}:
            return re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", text_lower) is not None
        if k == "deploy":
            return re.search(r"(?<![a-z0-9])deploy(?![a-z0-9])", text_lower) is not None
        if len(k) <= 3 and re.fullmatch(r"[a-z0-9]+", k):
            return re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", text_lower) is not None
        # Use regex with flexible spacing for multi-word keywords to handle extra spaces
        if ' ' in k:
            pattern = r'\s+'.join(map(re.escape, k.split()))
            return re.search(pattern, text_lower) is not None
        return k in text_lower

    @staticmethod
    def _normalize_text_lower(text_lower: str) -> str:
        if not isinstance(text_lower, str) or not text_lower:
            return text_lower
        
        # Apply existing regex-based normalizations
        # Normalize Polish diacritics to handle typos
        text_lower = _normalize_polish_text(text_lower)
        text_lower = text_lower.replace('ł', 'l').replace('Ł', 'L')
        text_lower = text_lower.replace('ą', 'a').replace('Ą', 'A')
        text_lower = text_lower.replace('ę', 'e').replace('Ę', 'E')
        text_lower = text_lower.replace('ś', 's').replace('Ś', 'S')
        text_lower = text_lower.replace('ć', 'c').replace('Ć', 'C')
        text_lower = text_lower.replace('ń', 'n').replace('Ń', 'N')
        text_lower = text_lower.replace('ó', 'o').replace('Ó', 'O')
        text_lower = text_lower.replace('ź', 'z').replace('Ź', 'Z')
        text_lower = text_lower.replace('ż', 'z').replace('Ż', 'Z')

        text_lower = re.sub(r"\blist\s+aplik", "lista plik", text_lower)
        text_lower = re.sub(r"\blist\s+a\s+plik", "lista plik", text_lower)
        text_lower = re.sub(r"\blisty\s+plik", "lista plik", text_lower)
        text_lower = re.sub(r"\bliste\s+plik", "lista plik", text_lower)
        
        text_lower = re.sub(r"(?<![a-z0-9])doker(?![a-z0-9])", "docker", text_lower)
        text_lower = re.sub(r"(?<![a-z0-9])dokcer(?![a-z0-9])", "docker", text_lower)
        text_lower = re.sub(r"\bstartuj(?:cie|my|)?\b", "uruchom", text_lower)
        text_lower = re.sub(r"\bwystartuj(?:cie|my|)?\b", "uruchom", text_lower)
        
        return text_lower

    @staticmethod
    def _maybe_lemmatize_text_lower(text_lower: str) -> str:
        if not _ENABLE_SPACY_LEMMATIZATION:
            return text_lower
        model = _get_spacy_model()
        if model is None:
            return text_lower

        try:
            doc = model(text_lower)
            lemmatized_tokens = []
            for token in doc:
                if token.is_punct or token.like_num or token.is_space:
                    lemmatized_tokens.append(token.text)
                else:
                    original_text = token.text.lower()
                    lemma = (token.lemma_ or "").lower()
                    important_keywords = {
                        'restartuj', 'uruchom', 'zrestartuj', 'startuj', 'wystartuj',
                        'zatrzymaj', 'stopuj', 'usuń', 'skopiuj', 'przenieś', 'znajdź',
                        'pokaż', 'sprawdź', 'utwórz', 'zmień', 'restart', 'docker', 'ps',
                        'systemctl', 'nginx', 'kontener', 'kontenery', 'plik', 'foldery',
                        'katalog', 'katalogi', 'usługa', 'usługi', 'usługę', 'serwis',
                        'komputer', 'system', 'proces', 'procesy'
                    }
                    if original_text in important_keywords or not lemma or len(lemma) <= 1:
                        lemmatized_tokens.append(original_text)
                    else:
                        lemmatized_tokens.append(lemma)
            return " ".join(lemmatized_tokens)
        except Exception:
            return text_lower

    @staticmethod
    def _normalize_intent(domain: str, intent: str, text_lower: str) -> str:
        if domain == 'sql':
            if intent in {'inner_join', 'left_join', 'right_join', 'full_join'}:
                return 'join'
            return intent

        if domain == 'docker':
            if intent.startswith('docker_'):
                intent = intent[len('docker_'):]
            if intent == 'compose':
                if re.search(r"\b(run|start|launch|uruchom|odpal|wystartuj)\b", text_lower):
                    return 'compose_up'
            return intent

        if domain != 'shell':
            return intent

        # Process-related heuristics: avoid misclassifying "find process" style queries
        # as file searching just because they contain "znajdź".
        if any(k in text_lower for k in ("proces", "procesy", "process", "pid")):
            wants_most = any(k in text_lower for k in ("najwięcej", "najwiecej", "najbardziej", "most", "top"))
            wants_mem = any(k in text_lower for k in ("ram", "pamięc", "pamiec", "%mem", "mem"))
            wants_cpu = any(k in text_lower for k in ("cpu", "procesor", "%cpu"))

            if wants_mem and (wants_most or wants_cpu or True):
                # Prefer memory sort when user mentions RAM/memory.
                return 'process_memory'
            if wants_cpu:
                return 'process_cpu'

        if intent in {'process', 'process_list', 'process_management'}:
            return 'list_processes'
        if intent == 'disk':
            return 'disk_usage'
        if intent == 'archive':
            return 'compress'
        if intent.startswith('perm_chmod') or intent == 'perm_chmod':
            return 'chmod'
        if intent == 'grep':
            return 'search'

        if intent == 'file_operation':
            if any(k in text_lower for k in ['skopiuj', 'kopiuj', 'copy', 'cp '] ):
                return 'copy'
            if any(k in text_lower for k in ['przenieś', 'przenies', 'move', 'mv '] ):
                return 'move'
            if any(k in text_lower for k in ['usuń', 'usun', 'delete', 'remove', 'rm '] ):
                return 'delete'

        return intent

    @staticmethod
    def _has_shell_file_context(text_lower: str) -> bool:
        if not isinstance(text_lower, str):
            return False
        if any(x in text_lower for x in ['/', './', '../']):
            return True
        if re.search(r"\.[a-z0-9]{1,5}\b", text_lower):
            return True
        if re.search(r"\bplik\w*\b", text_lower):
            return True
        if re.search(r"\bfile\w*\b", text_lower):
            return True
        if re.search(r"\bkatalog\w*\b", text_lower):
            return True
        if re.search(r"\bfolder\w*\b", text_lower):
            return True
        if re.search(r"\bdirectory\w*\b", text_lower):
            return True
        if re.search(r"\bpath\w*\b", text_lower):
            return True
        if 'ścieżk' in text_lower or 'sciezk' in text_lower:
            return True
        return False

    def _detect_fast_path(self, text_lower: str) -> Optional[DetectionResult]:
        url_pattern = re.search(
            r'\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|dev|pl|de|uk|eu|gov|edu|tv|co))\b',
            text_lower,
        )
        browser_keywords = self.fast_path_browser_keywords
        has_browser_keyword = any(kw in text_lower for kw in browser_keywords)

        search_keywords = self.fast_path_search_keywords
        if any(kw in text_lower for kw in search_keywords):
            return DetectionResult(
                domain="shell",
                intent="search_web",
                confidence=0.9,
                matched_keyword="search+web",
            )

        if url_pattern or has_browser_keyword:
            return DetectionResult(
                domain="shell",
                intent="open_url",
                confidence=0.9,
                matched_keyword=url_pattern.group(1) if url_pattern else "browser",
            )

        if (
            re.search(r"\b(użytkownik\w*|uzytkownik\w*|users?)\b", text_lower)
            and re.search(r"\b(systemu|system)\b", text_lower)
            and not re.search(r"\b(tabel\w*|table|sql)\b", text_lower)
        ):
            return DetectionResult(
                domain="shell",
                intent="user_list",
                confidence=0.9,
                matched_keyword="system users",
            )

        if (
            re.search(r"\b(lista|list)\b", text_lower)
            and re.search(
                r"\b(foldery|folderow|folders|katalogi|katalogow|directories)\b",
                text_lower,
            )
            and not re.search(r"\b(tabel\w*|table|sql)\b", text_lower)
        ):
            return DetectionResult(
                domain="shell",
                intent="list_dirs",
                confidence=0.85,
                matched_keyword="list folders",
            )

        if re.search(r"\bfind\b", text_lower) and re.search(r"\bfiles?\b", text_lower):
            return DetectionResult(
                domain='shell',
                intent='find',
                confidence=0.9,
                matched_keyword='find files',
            )

        if 'uprawnien' in text_lower or re.search(r"\bchmod\b", text_lower):
            return DetectionResult(
                domain='shell',
                intent='chmod',
                confidence=0.9,
                matched_keyword='uprawnienia',
            )

        if self._has_shell_file_context(text_lower) and re.search(
            r"\b(usuń|usun|usuw\w*|skasuj|delete|remove|rm)\b",
            text_lower,
        ):
            return DetectionResult(
                domain='shell',
                intent='delete',
                confidence=0.9,
                matched_keyword='delete file',
            )

        if (
            ('logach' in text_lower or 'logi' in text_lower or re.search(r"\blogs?\b", text_lower))
            and ('error' in text_lower)
            and ('znajd' in text_lower or re.search(r"\b(find|search|grep)\b", text_lower))
        ):
            return DetectionResult(
                domain='shell',
                intent='search',
                confidence=0.9,
                matched_keyword='error',
            )

        if (
            'logi aplikacji' in text_lower
            and not self._has_shell_file_context(text_lower)
            and 'systemowe' not in text_lower
            and 'kubectl' not in text_lower
        ):
            return DetectionResult(
                domain='docker',
                intent='logs',
                confidence=0.85,
                matched_keyword='logi aplikacji',
            )

        run_detached = self._detect_fast_path_docker_run_detached(text_lower)
        if run_detached is not None:
            return run_detached

        return None

    def _detect_fast_path_docker_run_detached(self, text_lower: str) -> Optional[DetectionResult]:
        common_images = self.fast_path_common_images
        has_run_word = bool(re.search(r"\b(run|start|launch|uruchom|odpal|wystartuj)\b", text_lower))
        has_port = bool(re.search(r"\bport\b\s*\d+|\bon\s+port\s+\d+|\bporcie\s+\d+", text_lower))
        has_common_image = any(img in text_lower for img in common_images)
        
        # Exclude shell service management context
        has_service_context = bool(re.search(r"\b(usług|uslug|usluge|serwis|service|systemctl)\b", text_lower))
        
        if has_run_word and has_port and has_common_image and not has_service_context:
            return DetectionResult(
                domain="docker",
                intent="run_detached",
                confidence=0.9,
                matched_keyword="run+port+image",
            )
        return None

    def _compute_sql_context(self, text_lower: str) -> tuple[bool, bool]:
        sql_boosters = self.domain_boosters.get('sql', [])
        shell_boosters = self.domain_boosters.get('shell', [])
        
        # Check if this is clearly a file operation - if so, don't treat as SQL
        file_context_keywords = ['plik', 'pliki', 'folder', 'foldery', 'katalog', 'katalogi', 'file', 'files']
        has_file_context = any(keyword in text_lower for keyword in file_context_keywords)
        
        # If we have "pokaż" with file context, it's shell, not SQL
        if 'pokaż' in text_lower or 'pokaz' in text_lower:
            if has_file_context:
                return False, False
        
        sql_soft_context = bool(
            re.search(
                r"\b(użytkown\w*|uzytkown\w*|rekord\w*|record\w*|tabel\w*|table\w*|dane\w*)\b",
                text_lower,
            )
        ) and not has_file_context
        
        sql_context = any(b.lower() in text_lower for b in sql_boosters) or sql_soft_context
        sql_explicit = bool(re.search(r"\b(select|update|delete|insert|where|join|sql|table|tabela)\b", text_lower))
        return sql_context, sql_explicit

    def _detect_sql_drop_table(self, text_lower: str, *, sql_context: bool, sql_explicit: bool) -> Optional[DetectionResult]:
        if not (sql_context or sql_explicit):
            return None

        sql_intents = self.patterns.get('sql', {})
        drop_keywords = sql_intents.get('drop_table', [])
        for kw in drop_keywords:
            if self._match_keyword(text_lower, kw):
                confidence = 0.9
                keyword_length_bonus = min(len(kw) / 25, 0.05)
                confidence = min(confidence + keyword_length_bonus, 0.95)
                return DetectionResult(
                    domain='sql',
                    intent='drop_table',
                    confidence=confidence,
                    matched_keyword=kw,
                )

        # Guard against priority SQL delete winning for "usuń tabelę ..."
        if re.search(r"\b(usuń|usun|skasuj|delete|drop)\b\s+tabel\w*\b", text_lower):
            return DetectionResult(
                domain='sql',
                intent='drop_table',
                confidence=0.9,
                matched_keyword='drop table',
            )

        return None

    def _detect_explicit_docker(self, text_lower: str) -> Optional[DetectionResult]:
        docker_boosters = self.domain_boosters.get('docker', [])
        has_docker_context = (
            'docker' in text_lower
            or any(b.lower() in text_lower for b in docker_boosters)
            or any(
                x in text_lower
                for x in (
                    'kontener', 'container', 'obraz', 'image'
                )
            )
        )
        if not has_docker_context:
            return None

        if (
            re.search(r"\bzatrzyman\w*\b", text_lower)
            and re.search(r"\b(uruchom|odpal|start)\b", text_lower)
            and ("kontener" in text_lower or "container" in text_lower)
        ):
            return DetectionResult(
                domain='docker',
                intent='start',
                confidence=0.85,
                matched_keyword='start stopped container',
            )

        if (
            ("obraz" in text_lower or "image" in text_lower)
            and ("repozytor" in text_lower or "registry" in text_lower)
            and re.search(r"\b(wypchnij|push|wyślij|wyslij|opublikuj|publish)\b", text_lower)
        ):
            return DetectionResult(
                domain='docker',
                intent='push',
                confidence=0.85,
                matched_keyword='push image',
            )

        if (
            ("kontener" in text_lower or "container" in text_lower)
            and re.search(r"\b(komend\w*|polecen\w*)\b", text_lower)
            and re.search(r"\b(wykonaj|exec|uruchom)\b", text_lower)
        ):
            return DetectionResult(
                domain='docker',
                intent='exec',
                confidence=0.85,
                matched_keyword='exec in container',
            )

        run_detached = self._detect_fast_path_docker_run_detached(text_lower)
        if run_detached is not None:
            return run_detached

        docker_intents = self.patterns.get('docker', {})
        priority = list(self.priority_intents.get('docker', []))
        ordered_intents = priority + [i for i in docker_intents.keys() if i not in priority]
        for intent in ordered_intents:
            keywords = docker_intents.get(intent, [])
            for kw in keywords:
                if self._match_keyword(text_lower, kw):
                    confidence = 0.9
                    keyword_length_bonus = min(len(kw) / 25, 0.05)
                    confidence = min(confidence + keyword_length_bonus, 0.95)
                    out_intent = self._normalize_intent('docker', intent, text_lower)
                    return DetectionResult(
                        domain='docker',
                        intent=out_intent,
                        confidence=confidence,
                        matched_keyword=kw,
                    )

        if re.search(r"\b(uruchom|odpal|start|wystartuj|run|launch)\b", text_lower):
            return DetectionResult(
                domain='docker',
                intent='list',
                confidence=0.6,
                matched_keyword='docker',
            )

        return None

    def _detect_explicit_kubernetes(self, text_lower: str) -> Optional[DetectionResult]:
        k8s_boosters = self.domain_boosters.get('kubernetes', [])
        has_k8s_context = (
            any(
                x in text_lower
                for x in (
                    'pod', 'pods', 'pody',
                    'deployment',
                    'namespace',
                    'service', 'serwis',
                    'configmap',
                    'secret',
                    'ingress',
                    'cluster',
                )
            )
            or re.search(r"\b(zastosuj|apply)\b", text_lower) is not None
            or re.search(r"\bskaluj\w*\b", text_lower) is not None
            or re.search(r"\breplik\w*\b", text_lower) is not None
        )
        if not has_k8s_context:
            return None

        if re.search(r"\b(zastosuj|apply)\b", text_lower) and re.search(
            r"\b(konfiguracj\w*|yaml|yml|manifest)\b",
            text_lower,
        ):
            return DetectionResult(
                domain='kubernetes',
                intent='apply',
                confidence=0.85,
                matched_keyword='apply',
            )

        if re.search(r"\b(utw[oó]rz|stw[oó]rz|create)\b", text_lower):
            if re.search(r"\b(serwis|service)\b", text_lower):
                return DetectionResult(
                    domain='kubernetes',
                    intent='create_service',
                    confidence=0.85,
                    matched_keyword='service',
                )
            if 'configmap' in text_lower:
                return DetectionResult(
                    domain='kubernetes',
                    intent='create_configmap',
                    confidence=0.85,
                    matched_keyword='configmap',
                )
            if 'secret' in text_lower:
                return DetectionResult(
                    domain='kubernetes',
                    intent='create_secret',
                    confidence=0.85,
                    matched_keyword='secret',
                )
            if 'ingress' in text_lower:
                return DetectionResult(
                    domain='kubernetes',
                    intent='create_ingress',
                    confidence=0.85,
                    matched_keyword='ingress',
                )
            if 'deployment' in text_lower:
                return DetectionResult(
                    domain='kubernetes',
                    intent='create',
                    confidence=0.85,
                    matched_keyword='deployment',
                )

        if re.search(r"\bget\b", text_lower) and ("pods" in text_lower or re.search(r"\bpody\b", text_lower)):
            return DetectionResult(
                domain='kubernetes',
                intent='get',
                confidence=0.8,
                matched_keyword='get pods',
            )

        k8s_intents = self.patterns.get('kubernetes', {})
        priority = list(self.priority_intents.get('kubernetes', []))
        ordered_intents = priority + [i for i in k8s_intents.keys() if i not in priority]
        for intent in ordered_intents:
            keywords = k8s_intents.get(intent, [])
            for kw in keywords:
                if self._match_keyword(text_lower, kw):
                    confidence = 0.9
                    keyword_length_bonus = min(len(kw) / 25, 0.05)
                    confidence = min(confidence + keyword_length_bonus, 0.95)
                    out = DetectionResult(
                        domain='kubernetes',
                        intent=intent,
                        confidence=confidence,
                        matched_keyword=kw,
                    )

                    m = re.search(r"\bnamespace\b\s+([a-z0-9][a-z0-9\-]*)", text_lower)
                    if m:
                        out.entities = {"namespace": m.group(1)}
                    return out

        m = re.search(r"\bnamespace\b\s+([a-z0-9][a-z0-9\-]*)", text_lower)
        if m:
            return DetectionResult(
                domain="kubernetes",
                intent="unknown",
                confidence=0.55,
                matched_keyword="namespace",
                entities={"namespace": m.group(1)},
            )

        return None

    def _domain_scan_allowed(
        self,
        text_lower: str,
        domain: str,
        *,
        sql_context: bool,
        sql_explicit: bool,
    ) -> bool:
        if domain == 'sql' and not (sql_context or sql_explicit):
            return False
        if domain == 'kubernetes':
            if any(
                x in text_lower
                for x in (
                    'kubectl', 'kubernetes', 'k8s',
                    'pod', 'pods', 'pody',
                    'deployment', 'namespace',
                    'service', 'serwis',
                    'configmap', 'secret', 'ingress',
                    'cluster',
                )
            ):
                return True
            if re.search(r"\bskaluj\w*\b", text_lower) or re.search(r"\breplik\w*\b", text_lower):
                return True
            if re.search(r"\b(zastosuj|apply)\b", text_lower) and re.search(
                r"\b(konfiguracj\w*|yaml|yml|manifest)\b",
                text_lower,
            ):
                return True
            return False
        if domain in {'docker', 'kubernetes'}:
            boosters = self.domain_boosters.get(domain, [])
            text_clean = text_lower.strip()
            if not any(b.lower() in text_clean for b in boosters):
                return False
        return True

    def _detect_best_from_priority_intents(
        self,
        text_lower: str,
        *,
        sql_context: bool,
        sql_explicit: bool,
    ) -> Optional[DetectionResult]:
        best_match: Optional[DetectionResult] = None
        best_score = 0.0

        for domain, priority_intents in self.priority_intents.items():
            if domain not in self.patterns:
                continue

            if not self._domain_scan_allowed(
                text_lower,
                domain,
                sql_context=sql_context,
                sql_explicit=sql_explicit,
            ):
                continue

            for intent in priority_intents:
                if intent not in self.patterns[domain]:
                    continue

                if domain == 'sql' and intent == 'delete':
                    if self._has_shell_file_context(text_lower):
                        continue

                keywords = self.patterns[domain][intent]
                for kw in keywords:
                    if self._match_keyword(text_lower, kw):
                        confidence = 0.85
                        keyword_length_bonus = min(len(kw) / 20, 0.10)
                        confidence = min(confidence + keyword_length_bonus, 0.95)

                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 15 else 0.0
                        score = confidence + position_bonus

                        if (
                            domain == 'sql'
                            and intent == 'delete'
                            and best_match
                            and best_match.domain == 'sql'
                            and best_match.intent == 'select'
                        ):
                            score += 0.2

                        if score > best_score:
                            best_score = score
                            out_intent = self._normalize_intent(domain, intent, text_lower)
                            best_match = DetectionResult(
                                domain=domain,
                                intent=out_intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )

        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        return None

    def _detect_explicit_system_reboot(self, text_lower: str) -> Optional[DetectionResult]:
        """
        Explicit detection for system reboot commands.
        This should be checked before general pattern matching to avoid conflicts.
        """
        reboot_patterns = [
            r'\bstartuj\s+(?:system|systemu|komputer|sistem)\b',
            r'\buruchom\s+(?:system|systemu|komputer|sistem)\b',
            r'\brestartuj\s+(?:system|systemu|komputer|sistem)\b',
            r'\bzrestartuj\s+(?:system|systemu|komputer|sistem)\b',
            r'\bsystem\s+(?:uruchom|startuj|restartuj|zrestartuj)\b',
            r'\bkomputer\s+(?:uruchom|startuj|restartuj|zrestartuj)\b',
            r'\bsistem\s+(?:uruchom|startuj|restartuj|zrestartuj)\b',
        ]
        
        for pattern in reboot_patterns:
            if re.search(pattern, text_lower):
                return DetectionResult(
                    domain='shell',
                    intent='reboot',
                    confidence=0.95,
                    matched_keyword='system reboot',
                )
        
        return None

    def _detect_explicit_service_restart(self, text_lower: str) -> Optional[DetectionResult]:
        """
        Explicit detection for service restart commands.
        This should be checked before general pattern matching to avoid conflicts.
        """
        restart_patterns = [
            r'\brestartuj\s+(?:usługę|usluge|serwis|service)\b',
            r'\bzrestartuj\s+(?:usługę|usluge|serwis|service)\b',
            r'\bprzerestartuj\s+(?:usługę|usluge|serwis|service)\b',
            r'\bsystemctl\s+restart\b',
        ]
        
        for pattern in restart_patterns:
            if re.search(pattern, text_lower):
                return DetectionResult(
                    domain='shell',
                    intent='service_restart',
                    confidence=0.95,
                    matched_keyword='restartuj usługę',
                )
        
        return None

    def _detect_best_from_patterns(
        self,
        text_lower: str,
        *,
        sql_context: bool,
        sql_explicit: bool,
    ) -> Optional[DetectionResult]:
        best_match: Optional[DetectionResult] = None
        best_score = 0.0

        for domain, intents in self.patterns.items():
            if not self._domain_scan_allowed(
                text_lower,
                domain,
                sql_context=sql_context,
                sql_explicit=sql_explicit,
            ):
                continue

            for intent, keywords in intents.items():
                for kw in keywords:
                    if self._match_keyword(text_lower, kw):
                        if domain == 'sql' and intent == 'delete':
                            if self._has_shell_file_context(text_lower):
                                continue

                        confidence = 0.7
                        keyword_length_bonus = min(len(kw) / 15, 0.2)  # Increased bonus for longer keywords
                        # Extra bonus for service-related patterns to prioritize them over generic ones
                        if domain == 'shell' and intent.startswith('service_'):
                            keyword_length_bonus += 0.05
                        confidence += keyword_length_bonus
                        domain_boost = self._calculate_domain_boost(text_lower, domain)
                        confidence += domain_boost
                        confidence = min(confidence, 0.95)

                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 20 else 0.0
                        score = confidence + position_bonus

                        if score > best_score:
                            best_score = score
                            out_intent = self._normalize_intent(domain, intent, text_lower)
                            best_match = DetectionResult(
                                domain=domain,
                                intent=out_intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )

        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        return None
    
    def detect(self, text: str) -> DetectionResult:
        """
        Detect domain and intent from text.
        
        Args:
            text: Natural language input
            
        Returns:
            DetectionResult with domain, intent, confidence
        """
        raw_lower = text.lower()
        
        # Apply STT error normalization for Polish text
        polish = _get_polish_support()
        if polish:
            raw_lower = polish.normalize_stt_errors(raw_lower)
        
        text_lower = self._normalize_text_lower(raw_lower)

        result = self._detect_normalized(text_lower)
        if result.domain != 'unknown' or result.confidence > 0.0:
            return result

        # Lazy lemmatization fallback (loads spaCy only if needed)
        lemmatized = self._maybe_lemmatize_text_lower(raw_lower)
        if lemmatized != raw_lower:
            lemmatized_norm = self._normalize_text_lower(lemmatized)
            fallback = self._detect_normalized(lemmatized_norm)
            if fallback.domain != 'unknown' and fallback.confidence >= result.confidence:
                return fallback

        return result

    def _detect_normalized(self, text_lower: str) -> DetectionResult:
        # Try ML classifier first for high-confidence matches (fastest, <1ms)
        ml_classifier = _get_ml_classifier()
        if ml_classifier:
            ml_result = ml_classifier.predict(text_lower)
            if ml_result and ml_result.confidence >= 0.9:
                return DetectionResult(
                    domain=ml_result.domain,
                    intent=ml_result.intent,
                    confidence=ml_result.confidence,
                    matched_keyword=f"ml:{ml_result.method}",
                )
        
        # Try multilingual schema matching for high-confidence matches
        schema_matcher = _get_fuzzy_schema_matcher()
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
        
        # ML classifier fallback for medium confidence (still useful)
        if ml_classifier and ml_result and ml_result.confidence >= 0.7:
            return DetectionResult(
                domain=ml_result.domain,
                intent=ml_result.intent,
                confidence=ml_result.confidence,
                matched_keyword=f"ml:{ml_result.method}",
            )
        
        # Semantic matching fallback for typos and paraphrases (slower but more accurate)
        semantic_matcher = _get_semantic_matcher()
        if semantic_matcher:
            semantic_result = semantic_matcher.match(text_lower)
            if semantic_result and semantic_result.confidence >= 0.75:
                return DetectionResult(
                    domain=semantic_result.domain,
                    intent=semantic_result.intent,
                    confidence=semantic_result.confidence,
                    matched_keyword=f"semantic:{semantic_result.matched_phrase}",
                )
        
        fast_path = self._detect_fast_path(text_lower)
        if fast_path is not None:
            return fast_path

        sql_context, sql_explicit = self._compute_sql_context(text_lower)

        sql_drop = self._detect_sql_drop_table(text_lower, sql_context=sql_context, sql_explicit=sql_explicit)
        if sql_drop is not None:
            return sql_drop

        docker_explicit = self._detect_explicit_docker(text_lower)
        if docker_explicit is not None:
            return docker_explicit

        k8s_explicit = self._detect_explicit_kubernetes(text_lower)
        if k8s_explicit is not None:
            return k8s_explicit

        system_reboot = self._detect_explicit_system_reboot(text_lower)
        if system_reboot is not None:
            return system_reboot

        service_restart = self._detect_explicit_service_restart(text_lower)
        if service_restart is not None:
            return service_restart

        priority_match = self._detect_best_from_priority_intents(
            text_lower,
            sql_context=sql_context,
            sql_explicit=sql_explicit,
        )
        if priority_match is not None:
            return priority_match

        best_match = self._detect_best_from_patterns(
            text_lower,
            sql_context=sql_context,
            sql_explicit=sql_explicit,
        )
        if best_match is not None:
            return best_match

        if fuzz is not None and process is not None:
            fuzzy_match = self._detect_best_from_fuzzy(text_lower)
            if fuzzy_match is not None:
                return fuzzy_match

        # Fallback: Try multilingual fuzzy schema matching
        schema_matcher = _get_fuzzy_schema_matcher()
        if schema_matcher:
            schema_result = schema_matcher.match(text_lower)
            if schema_result and schema_result.matched:
                return DetectionResult(
                    domain=schema_result.domain,
                    intent=schema_result.intent,
                    confidence=schema_result.confidence,
                    matched_keyword=schema_result.phrase,
                )

        return DetectionResult(
            domain='unknown',
            intent='unknown',
            confidence=0.0,
            matched_keyword=None,
        )
    
    def _calculate_domain_boost(self, text: str, domain: str) -> float:
        """Calculate confidence boost based on domain-specific keywords."""
        boosters = self.domain_boosters.get(domain, [])
        text_clean = text.strip().lower()
        matches = sum(1 for b in boosters if b.lower() in text_clean)
        return min(matches * 0.05, 0.15)
    
    def detect_all(self, text: str) -> list[DetectionResult]:
        """
        Detect all matching domains and intents.
        
        Args:
            text: Natural language input
            
        Returns:
            List of DetectionResult, sorted by confidence descending
        """
        text_lower = text.lower()
        results: list[DetectionResult] = []
        seen: set[tuple[str, str]] = set()
        
        for domain, intents in self.patterns.items():
            # Keep behavior consistent with `detect`: avoid returning docker/kubernetes
            # results when the query contains no domain-specific boosters.
            if domain in {'docker', 'kubernetes'}:
                boosters = self.domain_boosters.get(domain, [])
                if not any(b.lower() in text_lower for b in boosters):
                    continue
            for intent, keywords in intents.items():
                for kw in keywords:
                    if self._match_keyword(text_lower, kw):
                        out_intent = self._normalize_intent(domain, intent, text_lower)
                        key = (domain, out_intent)
                        if key not in seen:
                            seen.add(key)
                            confidence = 0.7 + self._calculate_domain_boost(text_lower, domain)
                            results.append(DetectionResult(
                                domain=domain,
                                intent=out_intent,
                                confidence=min(confidence, 0.95),
                                matched_keyword=kw,
                            ))
        
        return sorted(results, key=lambda r: r.confidence, reverse=True)
    
    def add_pattern(self, domain: str, intent: str, keywords: list[str]) -> None:
        """
        Add custom patterns.
        
        Args:
            domain: Domain name
            intent: Intent name
            keywords: Keywords to match
        """
        if domain not in self.patterns:
            self.patterns[domain] = {}
        if intent not in self.patterns[domain]:
            self.patterns[domain][intent] = []
        self.patterns[domain][intent].extend(keywords)
    
    def get_supported_domains(self) -> list[str]:
        """Get list of supported domains."""
        return list(self.patterns.keys())
    
    def get_supported_intents(self, domain: str) -> list[str]:
        """Get list of supported intents for a domain."""
        return list(self.patterns.get(domain, {}).keys())

    def _detect_best_from_fuzzy(self, text_lower: str) -> Optional[DetectionResult]:
        """
        Fuzzy matching fallback using rapidfuzz.
        Tries to match text against domain boosters and intent keywords with similarity threshold.
        """
        if fuzz is None or process is None:
            return None

        # Collect all possible keywords with their domain/intent mapping
        all_keywords = []
        
        # Add domain boosters
        for domain, boosters in self.domain_boosters.items():
            for booster in boosters:
                all_keywords.append((booster.lower(), domain, 'domain_booster', domain))
        
        # Add intent keywords from patterns
        for domain, intents in self.patterns.items():
            for intent, keywords in intents.items():
                for keyword in keywords:
                    # Avoid false positives for very short keywords (e.g. "fg") when
                    # matching arbitrary strings like "abcdefg".
                    if isinstance(keyword, str) and len(keyword.strip()) < 3:
                        continue
                    all_keywords.append((keyword.lower(), domain, intent, intent))
        
        if not all_keywords:
            return None

        # Extract just the keyword strings for rapidfuzz
        keyword_strings = [kw for kw, _, _, _ in all_keywords]
        
        # Use rapidfuzz to find best matches
        try:
            # Find best match with score
            result = process.extractOne(
                text_lower,
                keyword_strings,
                scorer=fuzz.WRatio,
                score_cutoff=85  # Threshold for fuzzy matching
            )
            
            if result is None:
                return None
            
            matched_keyword, score, _ = result
            
            # Find the corresponding domain/intent
            for kw, domain, intent_type, mapped_intent in all_keywords:
                if kw == matched_keyword:
                    # Calculate confidence based on similarity score
                    confidence = score / 100.0
                    
                    # Apply domain boost if it's a domain booster
                    if intent_type == 'domain_booster':
                        # For domain boosters, we need to find the best intent within that domain
                        domain_intents = self.patterns.get(domain, {})
                        best_intent = None
                        best_intent_score = 0.0
                        
                        for intent, keywords in domain_intents.items():
                            for kw in keywords:
                                kw_score = fuzz.WRatio(text_lower, kw.lower())
                                if kw_score > best_intent_score:
                                    best_intent_score = kw_score
                                    best_intent = intent
                        
                        if best_intent and best_intent_score >= 85:
                            return DetectionResult(
                                domain=domain,
                                intent=self._normalize_intent(domain, best_intent, text_lower),
                                confidence=min(best_intent_score / 100.0, 0.85),  # Cap fuzzy confidence
                                matched_keyword=matched_keyword,
                            )
                    else:
                        # Direct intent match
                        return DetectionResult(
                            domain=domain,
                            intent=self._normalize_intent(domain, mapped_intent, text_lower),
                            confidence=min(confidence, 0.85),  # Cap fuzzy confidence
                            matched_keyword=matched_keyword,
                        )
                    break
            
        except Exception:
            # If rapidfuzz fails for any reason, silently fall back
            pass
        
        return None
