"""
Iteration 1: Rule-Based Intent Detection.

Keyword matching for intent and domain detection without LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DetectionResult:
    """Result of intent detection."""
    
    domain: str
    intent: str
    confidence: float
    matched_keyword: Optional[str] = None


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
    
    PATTERNS: dict[str, dict[str, list[str]]] = {
        'sql': {
            'select': [
                'pokaż', 'wyświetl', 'znajdź', 'pobierz', 'select', 'get', 
                'show', 'list', 'fetch', 'query', 'retrieve',
                'z tabeli', 'from table', 'wszystkich', 'all records',
                'dane z', 'data from', 'rekordy', 'records', 'wiersze', 'rows',
            ],
            'insert': [
                'dodaj', 'wstaw', 'insert', 'create record', 'add record',
                'nowy rekord', 'new record', 'wprowadź', 'enter',
            ],
            'update': [
                'zmień', 'zaktualizuj', 'update', 'modify', 'ustaw',
                'set', 'edit', 'zmiana', 'aktualizacja',
            ],
            'delete': [
                'usuń', 'skasuj', 'delete', 'remove', 'wymaż',
                'kasuj', 'drop record',
            ],
            'aggregate': [
                'policz', 'zsumuj', 'średnia', 'count', 'sum', 'avg',
                'ile jest', 'how many', 'total', 'suma', 'średnio',
                'grupuj', 'group by', 'pogrupuj',
            ],
        },
        'shell': {
            'find': [
                'znajdź plik', 'szukaj plik', 'find files', 'search files',
                'locate', 'wyszukaj', 'gdzie jest', 'where is',
                'find python', 'find log',
            ],
            'list': [
                'lista plików', 'pokaż katalog', 'ls', 'dir', 'wylistuj',
                'zawartość katalogu', 'directory contents', 'folder contents',
            ],
            'process': [
                'procesy', 'ps', 'uruchomione procesy', 'running processes',
                'działające procesy', 'top procesy', 'cpu', 'memory usage', 
                'użycie pamięci', 'show processes', 'pokaż procesy',
            ],
            'file_operation': [
                'kopiuj', 'przenieś', 'usuń plik', 'copy', 'move', 'rm',
                'skopiuj', 'mv', 'rename', 'zmień nazwę',
            ],
            'disk': [
                'miejsce na dysku', 'disk space', 'df', 'du', 'rozmiar',
                'ile miejsca', 'how much space', 'wolne miejsce', 'free space',
            ],
            'network': [
                'ping', 'curl', 'wget', 'sieć', 'network', 'port',
                'połączenie', 'connection', 'netstat',
            ],
            'archive': [
                'spakuj', 'rozpakuj', 'zip', 'tar', 'compress', 'extract',
                'archiwum', 'archive', 'unzip', 'untar',
            ],
            'grep': [
                'grep', 'wyszukaj tekst', 'find text', 'szukaj w pliku',
                'pattern', 'wzorzec', 'filtruj', 'filter',
            ],
        },
        'docker': {
            'list': [
                'kontenery', 'containers', 'docker ps', 'pokaż kontenery',
                'lista kontenerów', 'running containers', 'obrazy', 'images',
            ],
            'run': [
                'uruchom kontener', 'docker run', 'start container',
                'odpal kontener', 'wystartuj',
            ],
            'stop': [
                'zatrzymaj kontener', 'docker stop', 'stop container',
                'zatrzymaj', 'kill container',
            ],
            'logs': [
                'logi kontenera', 'docker logs', 'container logs',
                'pokaż logi', 'show logs', 'dziennik',
            ],
            'build': [
                'zbuduj obraz', 'docker build', 'build image',
                'stwórz obraz', 'create image',
            ],
            'exec': [
                'wejdź do kontenera', 'docker exec', 'execute in container',
                'bash w kontenerze', 'shell in container',
            ],
            'compose': [
                'docker-compose', 'compose up', 'compose down',
                'stack', 'docker compose',
            ],
            'prune': [
                'wyczyść docker', 'docker prune', 'clean docker',
                'usuń nieużywane', 'remove unused',
            ],
        },
        'kubernetes': {
            'get': [
                'kubectl get', 'kubectl', 'pody', 'pods', 'deployments', 'pokaż pody',
                'services', 'serwisy', 'namespace', 'nodes', 'nody',
                'configmap', 'secret', 'ingress', 'k8s get',
            ],
            'scale': [
                'skaluj', 'scale', 'replicas', 'replik', 'zwiększ',
                'zmniejsz', 'autoscale',
            ],
            'apply': [
                'zastosuj', 'apply', 'kubectl apply', 'wdróż',
                'deploy', 'deployment',
            ],
            'delete': [
                'usuń pod', 'delete pod', 'kubectl delete',
                'usuń deployment', 'remove',
            ],
            'logs': [
                'logi poda', 'kubectl logs', 'pod logs',
                'pokaż logi k8s', 'kubernetes logs',
            ],
            'describe': [
                'opisz', 'describe', 'szczegóły', 'details',
                'kubectl describe', 'info',
            ],
            'exec': [
                'wejdź do poda', 'kubectl exec', 'exec pod',
                'shell w podzie', 'bash pod',
            ],
        },
        'dql': {
            'query': [
                'znajdź entity', 'entity query', 'dql', 'graph query',
                'relacje', 'relations', 'powiązania', 'connections',
            ],
        },
    }
    
    # Domain-specific boost keywords (increase confidence)
    DOMAIN_BOOSTERS: dict[str, list[str]] = {
        'sql': ['tabela', 'table', 'kolumna', 'column', 'baza', 'database', 'sql', 'where', 'join'],
        'shell': ['plik', 'file', 'katalog', 'directory', 'folder', 'ścieżka', 'path', 'bash', 'terminal'],
        'docker': ['docker', 'kontener', 'container', 'obraz', 'image', 'compose', 'dockerfile'],
        'kubernetes': ['kubernetes', 'k8s', 'kubectl', 'pod', 'deployment', 'namespace', 'helm'],
        'dql': ['entity', 'graph', 'node', 'edge', 'relation'],
    }
    
    def __init__(
        self,
        patterns: Optional[dict[str, dict[str, list[str]]]] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize keyword detector.
        
        Args:
            patterns: Custom patterns to use (or default PATTERNS)
            confidence_threshold: Minimum confidence to return a match
        """
        self.patterns = patterns or self.PATTERNS
        self.confidence_threshold = confidence_threshold
    
    # Priority intents - check these first as they are more specific/destructive
    PRIORITY_INTENTS: dict[str, list[str]] = {
        'sql': ['delete', 'update', 'insert', 'aggregate'],
        'shell': ['file_operation', 'archive', 'process', 'disk'],
        'docker': ['stop', 'prune', 'build', 'run'],
        'kubernetes': ['delete', 'scale', 'describe'],
    }
    
    def detect(self, text: str) -> DetectionResult:
        """
        Detect domain and intent from text.
        
        Args:
            text: Natural language input
            
        Returns:
            DetectionResult with domain, intent, confidence
        """
        text_lower = text.lower()
        
        best_match: Optional[DetectionResult] = None
        best_score = 0.0
        
        # First pass: check priority intents (destructive operations)
        for domain, priority_intents in self.PRIORITY_INTENTS.items():
            if domain not in self.patterns:
                continue
            for intent in priority_intents:
                if intent not in self.patterns[domain]:
                    continue
                keywords = self.patterns[domain][intent]
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.85  # Higher base confidence for priority
                        keyword_length_bonus = min(len(kw) / 20, 0.10)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        
                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 15 else 0.0
                        score = confidence + position_bonus
                        
                        if score > best_score:
                            best_score = score
                            best_match = DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )
        
        # If we found a priority match, return it
        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        
        # Second pass: check all patterns
        for domain, intents in self.patterns.items():
            for intent, keywords in intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        # Base confidence
                        confidence = 0.7
                        
                        # Boost for longer keyword matches (more specific)
                        keyword_length_bonus = min(len(kw) / 20, 0.15)
                        confidence += keyword_length_bonus
                        
                        # Boost for domain-specific keywords
                        domain_boost = self._calculate_domain_boost(text_lower, domain)
                        confidence += domain_boost
                        
                        # Cap at 0.95
                        confidence = min(confidence, 0.95)
                        
                        # Calculate score (confidence + match position penalty)
                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 20 else 0.0
                        score = confidence + position_bonus
                        
                        if score > best_score:
                            best_score = score
                            best_match = DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )
        
        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        
        return DetectionResult(
            domain='unknown',
            intent='unknown',
            confidence=0.0,
            matched_keyword=None,
        )
    
    def _calculate_domain_boost(self, text: str, domain: str) -> float:
        """Calculate confidence boost based on domain-specific keywords."""
        boosters = self.DOMAIN_BOOSTERS.get(domain, [])
        matches = sum(1 for b in boosters if b.lower() in text)
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
            for intent, keywords in intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        key = (domain, intent)
                        if key not in seen:
                            seen.add(key)
                            confidence = 0.7 + self._calculate_domain_boost(text_lower, domain)
                            results.append(DetectionResult(
                                domain=domain,
                                intent=intent,
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
