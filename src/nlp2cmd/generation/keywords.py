"""
Iteration 1: Rule-Based Intent Detection.

Keyword matching for intent and domain detection without LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import re


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
                'dane z', 'data from', 'wszystkie rekordy', 'all records', 'wiersze', 'rows',
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
                'kasuj', 'drop record', 'usuń rekord', 'skasuj rekord', 'z tabeli',
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
                'find python', 'find log', 'znajdź pliki z rozszerzeniem',
                'znajdź pliki większe niż', 'znajdź pliki zmodyfikowane',
                'pokaż zawartość pliku', 'wyświetl plik', 'cat plik', 'odczytaj plik',
                'pokaż ostatnie linii pliku', 'tail plik', 'koniec pliku'
            ],
            'list': [
                'lista plików', 'pokaż katalog', 'ls', 'dir', 'wylistuj',
                'zawartość katalogu', 'directory contents', 'folder contents',
                'pokaż pliki', 'listuj pliki', 'wypisz pliki'
            ],
            'process': [
                'procesy', 'ps', 'uruchomione procesy', 'running processes',
                'działające procesy', 'top procesy', 'cpu', 'memory usage', 
                'użycie pamięci', 'show processes', 'pokaż procesy',
                'sprawdź procesy', 'procesy zużywające pamięć', 'procesy zużywające cpu',
                'znajdź procesy', 'procesy użytkownika', 'zombie procesy', 'drzewo procesów',
                'pokaż użycie cpu i pamięci', 'monitor systemowy', 'htop'
            ],
            'file_operation': [
                'kopiuj', 'przenieś', 'usuń plik', 'copy', 'move', 'rm',
                'skopiuj', 'mv', 'rename', 'zmień nazwę',
                'skopiuj plik', 'przenieś plik', 'usuń plik', 'usuń wszystkie pliki',
                'utwórz katalog', 'zmień nazwę pliku', 'zmień nazwę pliku na',
                'sprawdź rozmiar pliku', 'rozmiar pliku', 'du plik', 'wielkość pliku'
            ],
            'disk': [
                'miejsce na dysku', 'disk space', 'df', 'du', 'rozmiar',
                'ile miejsca', 'how much space', 'wolne miejsce', 'free space',
                'pokaż dysk', 'użycie dysku', 'miejsce na dysku', 'sprawdź miejsce na dysku',
                'sprawdź dysk twardy', 'dysk twardy', 'zdrowie dysku', 'defragmentacja'
            ],
            'network': [
                'ping', 'curl', 'wget', 'sieć', 'network', 'port',
                'połączenie', 'connection', 'netstat',
                'sprawdź połączenie', 'testuj łączność', 'pinguj', 'sprawdź ping',
                'pokaż adres ip', 'adres ip', 'ip address', 'konfiguracja sieciowa',
                'znajdź porty', 'otwarte porty', 'porty nasłuchujące', 'aktywne połączenia',
                'znajdź urządzenia', 'skanuj sieć', 'nmap', 'prędkość internetu'
            ],
            'archive': [
                'spakuj', 'rozpakuj', 'zip', 'tar', 'compress', 'extract',
                'archiwum', 'archive', 'unzip', 'untar',
                'utwórz backup', 'skompresuj', 'backup', 'kopia zapasowa',
                'skopiuj backup', 'odtwórz z backupu', 'integralność backupu', 'status backupu',
                'usuń stare backupi', 'rozmiar backupu', 'harmonogram backup'
            ],
            'grep': [
                'grep', 'wyszukaj tekst', 'find text', 'szukaj w pliku',
                'pattern', 'wzorzec', 'filtruj', 'filter',
                'znajdź błędy', 'wyszukaj błędy', 'grep error', 'filtruj logi', 'przeglądaj logi'
            ],
            'system_maintenance': [
                'aktualizacja', 'upgrade', 'czyszczenie', 'maintenance', 'update', 'clean',
                'czyść cache', 'aktualizuj system', 'uruchom aktualizację', 'czyszczenie systemowe',
                'sprawdź logi', 'logi systemowe', 'oczyszczanie plików tymczasowych', 'usuń stare pliki',
                'sprawdź cron', 'status cron', 'uruchom defragmentację'
            ],
            'development': [
                'test', 'build', 'compile', 'run', 'debug', 'lint', 'version', 'install',
                'uruchom testy', 'testy jednostkowe', 'zbuduj projekt', 'maven', 'npm install',
                'serwer deweloperski', 'uruchom serwer', 'debugger', 'linter', 'analiza kodu',
                'logi aplikacji', 'czyszczenie cache', 'generuj dokumentację', 'wersja node'
            ],
            'security': [
                'bezpieczeństwo', 'security', 'who', 'last', 'ssh', 'permissions', 'firewall',
                'kto jest zalogowany', 'historia logowań', 'sesje ssh', 'uprawnienia pliku',
                'pliki suid', 'firewall rules', 'logi bezpieczeństwa', 'podejrzane procesy',
                'zainstalowane pakiety', 'użytkownicy systemu'
            ],
            'process_management': [
                'zabij proces', 'uruchom proces', 'zatrzymaj proces', 'restartuj proces', 'uruchom ponownie',
                'uruchom w tle', 'uruchom skrypt', 'zatrzymaj usługę', 'uruchom usługę', 'status usługi',
                'sprawdź status', 'monitor systemowy', 'htop', 'top'
            ],
            'open_url': [
                'otwórz przeglądarkę', 'open browser', 'otwórz stronę', 'open url', 'open website',
                'otwórz link', 'browse to', 'navigate to', 'go to url', 'idź do strony',
                'wejdź na stronę', 'przeglądarka', 'browser', 'xdg-open', 'open link',
                'otwórz google', 'otwórz youtube', 'otwórz github', 'open google', 'open youtube',
                'go to youtube', 'go to github', 'go to google', 'go to facebook',
                'youtube.com', 'github.com', 'google.com', 'facebook.com',
            ],
            'search_web': [
                'wyszukaj w google', 'google search', 'szukaj w internecie', 'search web',
                'wyszukaj online', 'znajdź w internecie', 'look up online',
                'wyszukaj w', 'szukaj w google', 'google python', 'google tutorial',
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
            'start': [
                'uruchom kontener', 'docker start', 'start container',
                'odpal kontener', 'wystartuj', 'zatrzymany kontener',
            ],
            'stop': [
                'zatrzymaj kontener', 'docker stop', 'stop container',
                'zatrzymaj', 'kill container',
            ],
            'remove': [
                'usuń kontener', 'docker remove', 'remove container',
                'usuń', 'docker rm',
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
        'sql': ['tabela', 'table', 'kolumna', 'column', 'baza', 'database', 'sql', 'where', 'join', 'tabeli', 'z tabeli'],
        'shell': ['plik', 'file', 'katalog', 'directory', 'folder', 'ścieżka', 'path', 'bash', 'terminal',
                  'znajdź', 'skopiuj', 'usuń', 'utwórz', 'zmień', 'sprawdź', 'pokaż', 'uruchom', 'zatrzymaj',
                  'proces', 'dysk', 'sieć', 'port', 'backup', 'logi', 'test', 'build', 'debug'],
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
        'shell': ['open_url', 'search_web', 'file_operation', 'archive', 'process', 'disk', 'system_maintenance', 'development', 'security', 'process_management'],
        'docker': ['stop', 'prune', 'build', 'run', 'list', 'logs', 'exec', 'start', 'remove'],
        'kubernetes': ['delete', 'scale', 'describe', 'logs'],
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

        # Fast-path: browser/URL opening queries.
        # Detect URLs or common website names in the query.
        url_pattern = re.search(r'\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|dev|pl|de|uk|eu|gov|edu|tv|co))\b', text_lower)
        browser_keywords = ['przeglądark', 'browser', 'otwórz stronę', 'open url', 'open website', 'go to', 'navigate to']
        has_browser_keyword = any(kw in text_lower for kw in browser_keywords)
        
        # Check if it's a search query (can be with or without URL)
        search_keywords = ['wyszukaj', 'szukaj', 'search for', 'google search', 'znajdź w', 'look up']
        if any(kw in text_lower for kw in search_keywords):
            return DetectionResult(
                domain="shell",
                intent="search_web",
                confidence=0.9,
                matched_keyword="search+web",
            )
        
        # URL opening (needs URL pattern or browser keyword)
        if url_pattern or has_browser_keyword:
            return DetectionResult(
                domain="shell",
                intent="open_url",
                confidence=0.9,
                matched_keyword=url_pattern.group(1) if url_pattern else "browser",
            )

        # Fast-path: docker-like queries without explicit 'docker' keyword.
        # Example: "run nginx on port 8080".
        # Without this, generic shell 'development' keywords (e.g. 'run') can dominate.
        common_images = {
            "nginx",
            "redis",
            "postgres",
            "postgresql",
            "mysql",
            "mongo",
            "mongodb",
            "rabbitmq",
        }
        has_run_word = bool(re.search(r"\b(run|start|launch)\b", text_lower))
        has_port = bool(re.search(r"\bport\b\s*\d+|\bon\s+port\s+\d+|\bporcie\s+\d+", text_lower))
        has_common_image = any(img in text_lower for img in common_images)
        if has_run_word and has_port and has_common_image:
            return DetectionResult(
                domain="docker",
                intent="run_detached",
                confidence=0.9,
                matched_keyword="run+port+image",
            )

        # Fast-path: if the user explicitly uses the docker CLI, prefer docker intents
        # (prevents shell/process keywords like 'ps' from dominating).
        if 'docker' in text_lower:
            docker_intents = self.patterns.get('docker', {})
            for intent, keywords in docker_intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.9
                        keyword_length_bonus = min(len(kw) / 25, 0.05)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        return DetectionResult(
                            domain='docker',
                            intent=intent,
                            confidence=confidence,
                            matched_keyword=kw,
                        )
        
        # Fast-path: if the user explicitly uses kubernetes terms, prefer k8s intents
        # (prevents shell keywords like 'pokaż' from dominating).
        k8s_boosters = self.DOMAIN_BOOSTERS.get('kubernetes', [])
        if any(booster.lower() in text_lower for booster in k8s_boosters):
            k8s_intents = self.patterns.get('kubernetes', {})
            for intent, keywords in k8s_intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.9
                        keyword_length_bonus = min(len(kw) / 25, 0.05)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        return DetectionResult(
                            domain='kubernetes',
                            intent=intent,
                            confidence=confidence,
                            matched_keyword=kw,
                        )
        
        best_match: Optional[DetectionResult] = None
        best_score = 0.0
        
        # First pass: check priority intents (destructive operations)
        for domain, priority_intents in self.PRIORITY_INTENTS.items():
            if domain not in self.patterns:
                continue

            # Guard: docker intents should only win when docker-specific boosters are present.
            # This prevents generic phrases like "pokaż logi" from overriding kubernetes.
            if domain == 'docker':
                docker_boosters = self.DOMAIN_BOOSTERS.get('docker', [])
                if not any(b.lower() in text_lower for b in docker_boosters):
                    continue

            for intent in priority_intents:
                if intent not in self.patterns[domain]:
                    continue
                
                # Special handling: prefer shell for file operations when shell context is present
                if domain == 'sql' and intent == 'delete':
                    shell_boosters = self.DOMAIN_BOOSTERS.get('shell', [])
                    shell_context = any(b.lower() in text_lower for b in shell_boosters)
                    sql_boosters = self.DOMAIN_BOOSTERS.get('sql', [])
                    sql_context = any(b.lower() in text_lower for b in sql_boosters)
                    
                    # Only skip SQL delete if shell context is strong AND no SQL context
                    if shell_context and not sql_context:
                        # Skip SQL delete intent when shell context is detected but no SQL context
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
                        
                        # Special rule: SQL delete should always beat SQL select
                        if domain == 'sql' and intent == 'delete' and best_match and best_match.domain == 'sql' and best_match.intent == 'select':
                            score += 0.2  # Boost delete over select
                        
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
                        # Special handling: prefer shell for file operations when shell context is present
                        if domain == 'sql' and intent == 'delete':
                            shell_boosters = self.DOMAIN_BOOSTERS.get('shell', [])
                            shell_context = any(b.lower() in text_lower for b in shell_boosters)
                            if shell_context:
                                # Skip SQL delete intent when shell context is detected
                                continue
                        
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
