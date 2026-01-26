# Refactoring Plan for nlp2cmd Command Generation

## Overview
This document outlines the refactoring plan to address the architectural issues discovered during the shell command generation bug fix.

## Phase 1: Template Selection Refactoring (High Priority)

### 1.1 Create Template Selection Strategy Interface
**File**: `src/nlp2cmd/generation/template_strategy.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class TemplateSelectionStrategy(ABC):
    """Interface for template selection strategies"""
    
    @abstractmethod
    def select_template(self, domain: str, intent: str, entities: Dict[str, Any]) -> str:
        """Select the appropriate template based on context"""
        pass
    
    @abstractmethod
    def should_use_alternative(self, domain: str, intent: str, entities: Dict[str, Any]) -> bool:
        """Determine if an alternative template should be used"""
        pass

class ContextAwareTemplateStrategy(TemplateSelectionStrategy):
    """Context-aware template selection strategy"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('template_mappings', {})
    
    def select_template(self, domain: str, intent: str, entities: Dict[str, Any]) -> str:
        # Implementation based on configuration rules
        pass
```

### 1.2 Refactor TemplateGenerator
**File**: `src/nlp2cmd/generation/templates.py`

```python
class TemplateGenerator:
    def __init__(self, 
                 custom_templates: Optional[dict[str, dict[str, str]]] = None,
                 strategy: Optional[TemplateSelectionStrategy] = None):
        # ... existing initialization ...
        self.strategy = strategy or ContextAwareTemplateStrategy(self._load_config())
    
    def generate(self, domain: str, intent: str, entities: dict[str, Any]) -> TemplateResult:
        # Use strategy for template selection
        template = self.strategy.select_template(domain, intent, entities)
        # ... rest of implementation ...
```

### 1.3 Create Configuration Schema
**File**: `config/template_mappings.json`

```json
{
  "template_mappings": {
    "shell": {
      "list": {
        "conditions": [
          {
            "field": "target",
            "value": "directories",
            "template": "list_dirs"
          },
          {
            "field": "text",
            "pattern": "folders",
            "template": "list_dirs"
          },
          {
            "field": "text",
            "pattern": "directories",
            "template": "list_dirs"
          }
        ]
      }
    }
  }
}
```

## Phase 2: Entity Extraction Standardization (High Priority)

### 2.1 Create Entity Extraction Registry
**File**: `src/nlp2cmd/generation/entity_registry.py`

```python
from typing import Dict, List, Tuple, Any
import re

class EntityExtractionRegistry:
    """Registry for domain-specific entity extraction patterns"""
    
    def __init__(self):
        self.patterns: Dict[str, Dict[str, List[Tuple[str, int]]]] = {}
        self.post_processors: Dict[str, List[callable]] = {}
    
    def register_pattern(self, domain: str, entity_type: str, pattern: str, priority: int = 0):
        """Register a pattern with priority (higher = more specific)"""
        if domain not in self.patterns:
            self.patterns[domain] = {}
        if entity_type not in self.patterns[domain]:
            self.patterns[domain][entity_type] = []
        self.patterns[domain][entity_type].append((pattern, priority))
    
    def register_post_processor(self, domain: str, processor: callable):
        """Register a post-processing function for a domain"""
        if domain not in self.post_processors:
            self.post_processors[domain] = []
        self.post_processors[domain].append(processor)
    
    def extract_entities(self, text: str, domain: str) -> Dict[str, Any]:
        """Extract entities using registered patterns"""
        entities = {}
        domain_patterns = self.patterns.get(domain, {})
        
        # Sort patterns by priority (highest first)
        for entity_type, patterns in domain_patterns.items():
            sorted_patterns = sorted(patterns, key=lambda x: x[1], reverse=True)
            for pattern, _ in sorted_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities[entity_type] = match.group(1) if match.groups() else match.group(0)
                    break
        
        # Apply post-processors
        for processor in self.post_processors.get(domain, []):
            entities = processor(entities, text)
        
        return entities
```

### 2.2 Migrate Existing Patterns
**File**: `src/nlp2cmd/generation/pattern_definitions.py`

```python
from .entity_registry import EntityExtractionRegistry

def register_shell_patterns(registry: EntityExtractionRegistry):
    """Register all shell domain patterns"""
    
    # User folders patterns (high priority)
    registry.register_pattern('shell', 'path', 
        r'(?:show|pokaż|list|wyświetl)\s+(?:user|użytkownik)\s+(?:folders?|foldery|katalogi|directories?)\b', 
        priority=10)
    registry.register_pattern('shell', 'path', 
        r'user\s+folders', 
        priority=10)
    
    # Generic path patterns (lower priority)
    registry.register_pattern('shell', 'path', 
        r'(?:w\s+)?(?:katalogu|folderze|ścieżce|directory|folder|path)?\s*[`"\']?([/~][\w\.\-/]+)[`"\']?', 
        priority=1)
    
    # Target patterns
    registry.register_pattern('shell', 'target', 
        r'(?:foldery|folders?|katalogi|directories?)', 
        priority=5)

def register_shell_post_processors(registry: EntityExtractionRegistry):
    """Register shell domain post-processors"""
    
    def process_user_folders(entities: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Process user folders patterns"""
        if 'path' in entities and entities['path']:
            path = entities['path']
            if re.search(r'foldery.*(?:użytkownika|usera|user)|(?:użytkownika|usera|user).*foldery', path, re.IGNORECASE):
                entities['path'] = '~'
        elif 'path' not in entities or not entities['path']:
            text_lower = text.lower()
            if re.search(r'user\s+folders|show\s+list\s+user\s+folders', text_lower):
                entities['path'] = '~'
        return entities
    
    registry.register_post_processor('shell', process_user_folders)
```

## Phase 3: Pipeline Component Decoupling (Medium Priority)

### 3.1 Define Interfaces
**File**: `src/nlp2cmd/generation/interfaces.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class IntentDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> DetectionResult:
        pass

class EntityExtractor(ABC):
    @abstractmethod
    def extract(self, text: str, domain: str) -> ExtractionResult:
        pass

class TemplateSelector(ABC):
    @abstractmethod
    def select_template(self, domain: str, intent: str, entities: Dict[str, Any]) -> str:
        pass

class CommandGenerator(ABC):
    @abstractmethod
    def generate(self, domain: str, intent: str, entities: Dict[str, Any]) -> str:
        pass
```

### 3.2 Refactor Pipeline
**File**: `src/nlp2cmd/generation/pipeline.py`

```python
class CommandGenerationPipeline:
    """Decoupled pipeline with injectable components"""
    
    def __init__(self, 
                 intent_detector: IntentDetector,
                 entity_extractor: EntityExtractor,
                 template_selector: TemplateSelector,
                 command_generator: CommandGenerator):
        self.intent_detector = intent_detector
        self.entity_extractor = entity_extractor
        self.template_selector = template_selector
        self.command_generator = command_generator
    
    def process(self, text: str) -> PipelineResult:
        # Detect intent
        detection = self.intent_detector.detect(text)
        
        # Extract entities
        extraction = self.entity_extractor.extract(text, detection.domain)
        
        # Select template
        template = self.template_selector.select_template(
            detection.domain, 
            detection.intent, 
            extraction.entities
        )
        
        # Generate command
        command = self.command_generator.generate(
            detection.domain,
            detection.intent,
            extraction.entities
        )
        
        return PipelineResult(
            input_text=text,
            domain=detection.domain,
            intent=detection.intent,
            entities=extraction.entities,
            command=command,
            template_used=template,
            success=True,
            source="refactored_rules"
        )
```

## Phase 4: Test Coverage Enhancement (Medium Priority)

### 4.1 Property-Based Tests
**File**: `tests/test_command_generation_properties.py`

```python
import pytest
from hypothesis import given, strategies as st
from nlp2cmd.generation.pipeline import CommandGenerationPipeline

class TestCommandGenerationProperties:
    """Property-based tests for command generation"""
    
    @given(st.text(min_size=1, max_size=100))
    def test_consistent_output_for_similar_queries(self, query):
        """Test that semantically similar queries generate consistent commands"""
        # Implementation using property-based testing
        pass
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
    def test_pipeline_composition(self, queries):
        """Test that pipeline composition works correctly"""
        pass
```

### 4.2 Cross-Intent Consistency Tests
**File**: `tests/test_cross_intent_consistency.py`

```python
import pytest

class TestCrossIntentConsistency:
    """Test consistency across different intents with same semantic meaning"""
    
    @pytest.mark.parametrize("queries", [
        ["show user folders", "list user folders", "display user directories"],
        ["show files in home", "list home files", "display files in ~"],
        ["find python files", "search for python files", "look for .py files"]
    ])
    def test_semantic_consistency(self, queries):
        """Test that semantically equivalent queries generate similar commands"""
        pipeline = CommandGenerationPipeline()
        results = [pipeline.process(q) for q in queries]
        
        # All should have the same domain and similar command structure
        domains = [r.domain for r in results]
        assert all(d == domains[0] for d in domains), f"Inconsistent domains: {domains}"
        
        # Check that commands are functionally equivalent
        commands = [r.command for r in results]
        # Add equivalence checking logic
```

## Phase 5: Configuration-Driven Logic (Medium Priority)

### 5.1 Configuration Loader
**File**: `src/nlp2cmd/config/loader.py`

```python
import json
from pathlib import Path
from typing import Dict, Any

class ConfigurationLoader:
    """Load and validate configuration files"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
    
    def load_template_mappings(self) -> Dict[str, Any]:
        """Load template mapping configuration"""
        file_path = self.config_dir / "template_mappings.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_entity_patterns(self) -> Dict[str, Any]:
        """Load entity pattern configuration"""
        file_path = self.config_dir / "entity_patterns.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""
        # Implementation of validation logic
        pass
```

## Implementation Timeline

### Sprint 1 (2 weeks)
- [ ] Create template selection strategy interface
- [ ] Implement ContextAwareTemplateStrategy
- [ ] Refactor TemplateGenerator to use strategy
- [ ] Create basic configuration schema
- [ ] Add unit tests for new components

### Sprint 2 (2 weeks)
- [ ] Create EntityExtractionRegistry
- [ ] Migrate existing patterns to registry
- [ ] Implement post-processing system
- [ ] Add comprehensive tests for entity extraction

### Sprint 3 (2 weeks)
- [ ] Define component interfaces
- [ ] Refactor pipeline with dependency injection
- [ ] Implement property-based tests
- [ ] Add cross-intent consistency tests

### Sprint 4 (1 week)
- [ ] Implement configuration loader
- [ ] Create configuration validation
- [ ] Add integration tests
- [ ] Update documentation

## Success Criteria

### Functional
- [ ] All existing functionality preserved
- [ ] New configuration system works correctly
- [ ] Cross-intent consistency achieved
- [ ] Test coverage > 90%

### Non-Functional
- [ ] Code complexity reduced by 30%
- [ ] Configuration changes don't require code deployment
- [ ] New domain addition takes < 1 hour
- [ ] Build time under 2 minutes

## Risk Mitigation

### Technical Risks
- **Breaking changes**: Implement feature flags for gradual rollout
- **Performance degradation**: Benchmark critical paths
- **Configuration errors**: Implement validation and defaults

### Project Risks
- **Timeline delays**: Prioritize core functionality first
- **Resource constraints**: Focus on high-impact changes
- **Knowledge gaps**: Pair programming and documentation

This refactoring plan provides a structured approach to improving the nlp2cmd architecture while maintaining backward compatibility and ensuring future maintainability.
