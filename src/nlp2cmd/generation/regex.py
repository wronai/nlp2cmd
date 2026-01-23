"""
Iteration 2: Regex Entity Extraction.

Extract entities from text using regex patterns without LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ExtractedEntity:
    """A single extracted entity."""
    
    name: str
    value: Any
    confidence: float
    source_pattern: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    
    entities: dict[str, Any]
    extracted: list[ExtractedEntity]
    raw_text: str


class RegexEntityExtractor:
    """
    Extract entities from text using regex patterns.
    
    No LLM needed - uses predefined regex patterns to extract
    entities like table names, columns, paths, etc.
    
    Example:
        extractor = RegexEntityExtractor()
        result = extractor.extract("Pokaż kolumny id, name z tabeli users", domain='sql')
        # result.entities == {'table': 'users', 'columns': ['id', 'name']}
    """
    
    # Common patterns across domains
    COMMON_PATTERNS: dict[str, list[str]] = {
        'number': [
            r'\b(\d+)\b',
        ],
        'quoted_string': [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'`([^`]+)`',
        ],
    }
    
    # Domain-specific patterns
    SQL_PATTERNS: dict[str, list[str]] = {
        'table': [
            r'(?:from|into|update|table|tabeli?|tabelę|z tabeli)\s+[`"\']?(\w+)[`"\']?',
            r'(?:do tabeli|do|from|into)\s+[`"\']?(\w+)[`"\']?',
        ],
        'columns': [
            r'(?:columns?|kolumny?|pola?|select)\s*[:\s]+([a-zA-Z_][\w,\s]*)',
            r'(?:pokaż|wyświetl)\s+([a-zA-Z_][\w,\s]*)\s+(?:z|from)',
        ],
        'limit': [
            r'(?:limit|pierwsz[ye]|top|ostatni[che]?)\s+(\d+)',
            r'(\d+)\s+(?:rekordów|wierszy|rows?|pierwszych|ostatnich)',
        ],
        'where_field': [
            r'(?:where|gdzie|gdy|dla|for)\s+(\w+)\s*[=<>!]',
            r'(\w+)\s*=\s*[\'"]?[\w]+[\'"]?',
        ],
        'where_value': [
            r'(?:where|gdzie|gdy)\s+\w+\s*=\s*[\'"]?(\w+)[\'"]?',
            r'=\s*[\'"]?(\w+)[\'"]?',
        ],
        'order_by': [
            r'(?:order\s+by|sortuj\s+(?:po|wg)|posortuj)\s+(\w+)',
            r'(?:rosnąco|malejąco|asc|desc)\s+(?:po|by)\s+(\w+)',
        ],
        'order_direction': [
            r'\b(asc|desc|rosnąco|malejąco)\b',
        ],
        'aggregation': [
            r'\b(count|sum|avg|min|max|policz|zsumuj|średnia)\b',
        ],
        'group_by': [
            r'(?:group\s+by|grupuj\s+(?:po|wg))\s+(\w+)',
            r'(?:pogrupuj|grupowanie)\s+(?:po|wg)\s+(\w+)',
        ],
    }
    
    SHELL_PATTERNS: dict[str, list[str]] = {
        'path': [
            r'(?:w\s+)?(?:katalogu|folderze|ścieżce|directory|folder|path)?\s*[`"\']?([/~][\w\.\-/]+)[`"\']?',
            r'(?:do|from|to|z|in)\s+[`"\']?([/~][\w\.\-/]+)[`"\']?',
            r'\s([/~][\w\.\-/]+)\s',
        ],
        'file_pattern': [
            r'\*\.(\w+)',
            r'\.(\w+)\s+files?',
            r'(?:pliki?|files?)\s+\.?(\w+)',
            r'(?:rozszerzenie|extension)\s+\.?(\w+)',
        ],
        'filename': [
            r'(?:plik|file)\s+[`"\']?([\w\.\-]+)[`"\']?',
            r'[`"\']?([\w]+\.\w+)[`"\']?',
        ],
        'size': [
            r'(\d+)\s*([KMGT]?B)',
            r'(?:większ[ey]|larger|bigger)\s+(?:niż|than)?\s*(\d+)\s*([KMGT]?B)?',
            r'(?:mniejsz[ey]|smaller)\s+(?:niż|than)?\s*(\d+)\s*([KMGT]?B)?',
        ],
        'age': [
            r'(?:starsze|older)\s+(?:niż|than)?\s*(\d+)\s*(dni|days?|godzin|hours?|minut|minutes?)',
            r'(?:młodsze|newer)\s+(?:niż|than)?\s*(\d+)\s*(dni|days?|godzin|hours?|minut|minutes?)',
            r'(\d+)\s*(dni|days?|godzin|hours?)\s+(?:temu|ago)',
        ],
        'process_name': [
            r'(?:proces|process)\s+[`"\']?(\w+)[`"\']?',
            r'(?:kill|zabij)\s+[`"\']?(\w+)[`"\']?',
        ],
        'grep_pattern': [
            r'(?:szukaj|grep|find|wyszukaj)\s+[`"\']?(.+?)[`"\']?\s+(?:w|in)',
            r'(?:pattern|wzorzec)\s+[`"\']?(.+?)[`"\']?',
        ],
    }
    
    DOCKER_PATTERNS: dict[str, list[str]] = {
        'flags': [
            r'\b(-a|--all)\b',
            r'\b(--no-trunc)\b',
        ],
        'container': [
            r'(?:kontener[a]?|container)\s+[`"\']?(\w[\w\-]*)[`"\']?',
            r'(?:w|in)\s+[`"\']?(\w[\w\-]*)[`"\']?\s+(?:kontener|container)',
        ],
        'image': [
            r'(?:obraz[u]?|image)\s+[`"\']?([\w\-/:\.]+)[`"\']?',
            r'(?:z|from)\s+[`"\']?([\w]+(?:/[\w\-]+)?(?::[\w\.\-]+)?)[`"\']?',
            r'\b(?:run|start|launch)\s+([a-zA-Z0-9][\w\-./:]+)\b',
        ],
        'port': [
            r'(?:port[u]?|porcie)\s+(\d+)',
            r'(\d+):(\d+)',
            r'-p\s+(\d+):?(\d+)?',
        ],
        'volume': [
            r'(?:wolumen|volume)\s+[`"\']?([/\w\.\-:]+)[`"\']?',
            r'-v\s+[`"\']?([/\w\.\-]+):([/\w\.\-]+)[`"\']?',
        ],
        'network': [
            r'(?:sieć|network)\s+[`"\']?(\w[\w\-]*)[`"\']?',
        ],
        'env_var': [
            r'(?:zmienna|env|environment)\s+(\w+)=([^\s]+)',
            r'-e\s+(\w+)=([^\s]+)',
        ],
        'tail_lines': [
            r'(?:ostatni[che]?|tail|last)\s+(\d+)\s+(?:lini[ie]|lines?|wierszy)',
            r'--tail\s+(\d+)',
        ],
    }
    
    KUBERNETES_PATTERNS: dict[str, list[str]] = {
        'resource_type': [
            r'\b(pod[sy]?|deployment[sy]?|service[sy]?|serwis[y]?|configmap[sy]?|secret[sy]?|ingress|namespace[sy]?|node[sy]?|pv|pvc)\b',
        ],
        'resource_name': [
            r'(?:pod[a]?|deployment[u]?|serwis[u]?)\s+[`"\']?(\w[\w\-]*)[`"\']?',
            r'(?:o\s+nazwie|named|name)\s+[`"\']?(\w[\w\-]*)[`"\']?',
        ],
        'namespace': [
            r'(?:namespace|ns|przestrzeni)\s+[`"\']?(\w[\w\-]*)[`"\']?',
            r'-n\s+(\w[\w\-]*)',
        ],
        'replica_count': [
            r'(?:do|to)\s+(\d+)\s+(?:replik|replicas?|instancji|instances?)',
            r'(\d+)\s+(?:replik|replicas?|instancji|instances?)',
            r'--replicas[=\s]+(\d+)',
        ],
        'selector': [
            r'(?:label|etykiet[aą]|selector)\s+(\w+=\w+)',
            r'-l\s+(\w+=\w+)',
        ],
        'container_name': [
            r'(?:kontener|container)\s+[`"\']?(\w[\w\-]*)[`"\']?\s+w\s+(?:podzie|pod)',
            r'-c\s+(\w[\w\-]*)',
        ],
    }
    
    def __init__(
        self,
        custom_patterns: Optional[dict[str, dict[str, list[str]]]] = None,
    ):
        """
        Initialize entity extractor.
        
        Args:
            custom_patterns: Additional patterns per domain
        """
        self.patterns: dict[str, dict[str, list[str]]] = {
            'sql': self.SQL_PATTERNS.copy(),
            'shell': self.SHELL_PATTERNS.copy(),
            'docker': self.DOCKER_PATTERNS.copy(),
            'kubernetes': self.KUBERNETES_PATTERNS.copy(),
        }
        
        if custom_patterns:
            for domain, domain_patterns in custom_patterns.items():
                if domain not in self.patterns:
                    self.patterns[domain] = {}
                self.patterns[domain].update(domain_patterns)
    
    def extract(self, text: str, domain: str) -> ExtractionResult:
        """
        Extract entities from text.
        
        Args:
            text: Natural language input
            domain: Target domain (sql, shell, docker, kubernetes)
            
        Returns:
            ExtractionResult with extracted entities
        """
        entities: dict[str, Any] = {}
        extracted: list[ExtractedEntity] = []
        
        # Get patterns for domain
        domain_patterns = self.patterns.get(domain, {})
        
        for entity_type, patterns in domain_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = self._process_match(entity_type, match)
                    if value is not None:
                        # Handle special cases
                        if entity_type == 'columns':
                            value = self._parse_columns(value)
                        elif entity_type == 'order_direction':
                            value = self._normalize_direction(value)
                        
                        entities[entity_type] = value
                        extracted.append(ExtractedEntity(
                            name=entity_type,
                            value=value,
                            confidence=0.8,
                            source_pattern=pattern,
                        ))
                        break  # Use first match for each entity type
        
        # Post-processing: build structured entities
        entities = self._post_process(entities, domain)
        
        return ExtractionResult(
            entities=entities,
            extracted=extracted,
            raw_text=text,
        )
    
    def _process_match(self, entity_type: str, match: re.Match) -> Any:
        """Process regex match and return value."""
        groups = match.groups()
        
        if not groups:
            return match.group(0)
        
        # For patterns with multiple groups, handle specially
        if entity_type == 'port' and len(groups) >= 2:
            host_port = groups[0]
            container_port = groups[1] if groups[1] else groups[0]
            return {'host': host_port, 'container': container_port}
        
        if entity_type == 'size' and len(groups) >= 2:
            size = groups[0]
            unit = groups[1] if len(groups) > 1 and groups[1] else 'B'
            return {'value': int(size), 'unit': unit}
        
        if entity_type == 'age' and len(groups) >= 2:
            value = groups[0]
            unit = groups[1]
            return {'value': int(value), 'unit': self._normalize_time_unit(unit)}
        
        if entity_type == 'volume' and len(groups) >= 2:
            return {'host': groups[0], 'container': groups[1] if groups[1] else groups[0]}
        
        if entity_type == 'env_var' and len(groups) >= 2:
            return {'name': groups[0], 'value': groups[1]}
        
        return groups[0]
    
    def _parse_columns(self, value: str) -> list[str]:
        """Parse column list from string."""
        if not value:
            return ['*']
        
        # Split by comma and clean up
        columns = [col.strip() for col in value.split(',')]
        blocked = {
            'z', 'from', 'tabeli', 'table',
            # Generic words that often appear in NL queries but are not real columns
            'dane', 'data', 'rekordy', 'wiersze', 'wszystko', 'wszystkie',
            'all', 'everything',
        }
        columns = [col for col in columns if col and col.lower() not in blocked]
        
        return columns if columns else ['*']
    
    def _normalize_direction(self, value: str) -> str:
        """Normalize sort direction."""
        if value.lower() in ('asc', 'rosnąco'):
            return 'ASC'
        if value.lower() in ('desc', 'malejąco'):
            return 'DESC'
        return 'ASC'
    
    def _normalize_time_unit(self, unit: str) -> str:
        """Normalize time unit."""
        unit_map = {
            'dni': 'days',
            'day': 'days',
            'days': 'days',
            'godzin': 'hours',
            'hour': 'hours',
            'hours': 'hours',
            'minut': 'minutes',
            'minute': 'minutes',
            'minutes': 'minutes',
        }
        return unit_map.get(unit.lower(), unit)
    
    def _post_process(self, entities: dict[str, Any], domain: str) -> dict[str, Any]:
        """Post-process entities for adapter compatibility."""
        result = entities.copy()
        
        if domain == 'sql':
            # Convert to adapter format
            if 'where_field' in entities and 'where_value' in entities:
                result['filters'] = [{
                    'field': entities['where_field'],
                    'operator': '=',
                    'value': entities['where_value'],
                }]
            
            if 'order_by' in entities:
                direction = entities.get('order_direction', 'ASC')
                result['ordering'] = [{
                    'field': entities['order_by'],
                    'direction': direction,
                }]
            
            if 'aggregation' in entities:
                agg_map = {
                    'count': 'COUNT',
                    'policz': 'COUNT',
                    'sum': 'SUM',
                    'zsumuj': 'SUM',
                    'avg': 'AVG',
                    'średnia': 'AVG',
                    'min': 'MIN',
                    'max': 'MAX',
                }
                result['aggregations'] = [{
                    'function': agg_map.get(entities['aggregation'].lower(), 'COUNT'),
                    'field': '*',
                }]
            
            if 'group_by' in entities:
                result['grouping'] = [entities['group_by']]
        
        elif domain == 'shell':
            # Normalize path
            if 'path' in entities and entities['path']:
                path = entities['path']
                if path.startswith('~'):
                    path = path.replace('~', '$HOME', 1)
                result['path'] = path
            
            # Build find pattern
            if 'file_pattern' in entities:
                result['pattern'] = f"*.{entities['file_pattern']}"
        
        elif domain == 'docker':
            # Ensure container/image names are clean
            if 'container' in entities:
                result['container'] = entities['container'].strip('`"\'')
            if 'image' in entities:
                result['image'] = entities['image'].strip('`"\'')
        
        elif domain == 'kubernetes':
            # Normalize resource types
            if 'resource_type' in entities:
                resource_map = {
                    'pody': 'pods',
                    'pod': 'pods',
                    'deploymenty': 'deployments',
                    'serwisy': 'services',
                    'serwis': 'services',
                }
                rt = entities['resource_type'].lower()
                result['resource_type'] = resource_map.get(rt, rt)
        
        return result
    
    def extract_all_numbers(self, text: str) -> list[int]:
        """Extract all numbers from text."""
        return [int(m) for m in re.findall(r'\b(\d+)\b', text)]
    
    def extract_quoted_strings(self, text: str) -> list[str]:
        """Extract all quoted strings from text."""
        results = []
        for pattern in self.COMMON_PATTERNS['quoted_string']:
            results.extend(re.findall(pattern, text))
        return results
    
    def add_pattern(self, domain: str, entity_type: str, patterns: list[str]) -> None:
        """
        Add custom patterns.
        
        Args:
            domain: Domain name
            entity_type: Entity type name
            patterns: Regex patterns to add
        """
        if domain not in self.patterns:
            self.patterns[domain] = {}
        if entity_type not in self.patterns[domain]:
            self.patterns[domain][entity_type] = []
        self.patterns[domain][entity_type].extend(patterns)
