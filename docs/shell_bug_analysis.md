# Shell Command Generation Bug Analysis

## Bug Type: **Inconsistent Template Selection for Domain-Specific Commands**

### Problem Description
The nlp2cmd tool was generating different commands for semantically identical queries:
- `nlp2cmd "show user folders"` → `find ~ -maxdepth 1 -type d` (correct)
- `nlp2cmd "list user folders"` → `ls -la ~` (incorrect - missing directory filter)

Both queries should generate the same command that filters directories only.

### Root Cause Analysis

#### 1. **Intent Detection Inconsistency**
- Different intents were being detected for semantically similar queries:
  - "show user folders" → `list_dirs` intent
  - "list user folders" → `list` intent
- Both intents should map to the same behavior when the target is "directories"

#### 2. **Template Selection Logic Flaw**
- The template generator only checked for alternative templates when the primary template was missing
- Since `list` template existed, it never tried alternatives even when context demanded it
- Location: `src/nlp2cmd/generation/templates.py:621-630`

#### 3. **Entity Extraction Issues**
- Path extraction was generating `~folders` instead of `~`
- The regex patterns were not properly handling "user folders" pattern
- Target entity "folders" was extracted but not properly utilized

#### 4. **Adapter Logic Duplication**
- Similar logic was duplicated in multiple places:
  - Shell adapter `_generate_list` method
  - Template generator alternative template logic
  - Regex entity extraction patterns

### Technical Details

#### Files Modified:
1. **`src/nlp2cmd/generation/regex.py`**
   - Added specific patterns for "user folders" detection
   - Enhanced post-processing to map user folders to home directory

2. **`src/nlp2cmd/generation/templates.py`**
   - Added `list_dirs` template: `"find {path} -maxdepth 1 -type d"`
   - Modified template selection logic to always check alternatives for shell/list intent
   - Added context-aware template mapping

3. **`src/nlp2cmd/adapters/shell.py`**
   - Added fallback logic for folder detection in `_generate_list` method
   - Enhanced path cleaning for "folders" suffix

### Fix Implementation

#### Phase 1: Entity Extraction Fix
```python
# Added specific patterns for user folders
r'(?:show|pokaż|list|wyświetl)\s+(?:user|użytkownik)\s+(?:folders?|foldery|katalogi|directories?)\b'
r'user\s+folders'
```

#### Phase 2: Template Selection Fix
```python
# Special case: for shell domain with list intent, always check for alternatives
if domain == 'shell' and intent == 'list':
    alternative_template = self._find_alternative_template(domain, intent, entities)
    if alternative_template and alternative_template != intent:
        template = domain_templates.get(alternative_template)
```

#### Phase 3: Adapter Fallback
```python
# Check if we're listing folders based on target or full text
text = entities.get("text", "")
if (target and "folder" in target.lower()) or "folders" in str(text).lower():
    return f"find {path} -maxdepth 1 -type d"
```

## Required Refactoring to Prevent Future Issues

### 1. **Template Selection Architecture**
**Problem**: Ad-hoc template selection logic scattered across multiple files
**Solution**: Implement a centralized template selection strategy pattern

```python
class TemplateSelectionStrategy:
    """Centralized template selection with context awareness"""
    
    def select_template(self, domain: str, intent: str, entities: dict) -> str:
        # Unified logic for template selection
        pass
    
    def should_use_alternative(self, domain: str, intent: str, entities: dict) -> bool:
        # Consistent rules for alternative template usage
        pass
```

### 2. **Entity Extraction Standardization**
**Problem**: Inconsistent entity extraction patterns across domains
**Solution**: Create a unified entity extraction framework

```python
class EntityExtractionRegistry:
    """Registry for domain-specific entity extraction patterns"""
    
    def register_pattern(self, domain: str, entity_type: str, pattern: str, priority: int):
        # Standardized pattern registration
        pass
    
    def extract_entities(self, text: str, domain: str) -> dict:
        # Unified extraction logic
        pass
```

### 3. **Pipeline Component Decoupling**
**Problem**: Tight coupling between pipeline components
**Solution**: Implement proper dependency injection and interfaces

```python
class CommandGenerationPipeline:
    """Decoupled pipeline with injectable components"""
    
    def __init__(self, 
                 intent_detector: IntentDetector,
                 entity_extractor: EntityExtractor,
                 template_selector: TemplateSelector,
                 command_generator: CommandGenerator):
        # Proper dependency injection
        pass
```

### 4. **Configuration-Driven Logic**
**Problem**: Hard-coded business logic in code
**Solution**: Move rules to configuration files

```json
{
  "template_mappings": {
    "shell": {
      "list": {
        "conditions": [
          {"field": "target", "value": "directories", "template": "list_dirs"},
          {"field": "text", "pattern": "folders", "template": "list_dirs"}
        ]
      }
    }
  }
}
```

### 5. **Comprehensive Test Coverage**
**Problem**: Missing tests for edge cases and cross-intent scenarios
**Solution**: Implement property-based testing and scenario coverage

```python
class TestCommandGeneration:
    """Comprehensive test suite for command generation"""
    
    @pytest.mark.parametrize("query,expected", [
        ("show user folders", "find ~ -maxdepth 1 -type d"),
        ("list user folders", "find ~ -maxdepth 1 -type d"),
        ("display user directories", "find ~ -maxdepth 1 -type d"),
        # ... more test cases
    ])
    def test_consistent_folder_commands(self, query, expected):
        pass
```

## Implementation Priority

### High Priority (Immediate)
1. **Template Selection Refactoring** - Centralize selection logic
2. **Entity Extraction Standardization** - Unified extraction patterns
3. **Test Coverage** - Add comprehensive tests for fixed scenarios

### Medium Priority (Next Sprint)
1. **Configuration-Driven Logic** - Move rules to config files
2. **Pipeline Decoupling** - Implement proper interfaces

### Low Priority (Future)
1. **Architecture Documentation** - Document the improved architecture
2. **Performance Optimization** - Profile and optimize the refactored code

## Success Metrics
- **Consistency**: Semantically similar queries generate identical commands
- **Maintainability**: New domain additions require minimal code changes
- **Testability**: All edge cases covered by automated tests
- **Extensibility**: New rules can be added via configuration

## Lessons Learned
1. **Template selection should be context-aware, not just intent-based**
2. **Entity extraction patterns need comprehensive coverage of variations**
3. **Fallback mechanisms are essential for robustness**
4. **Cross-intent consistency is crucial for user experience**
5. **Configuration-driven logic reduces maintenance burden**

This analysis provides a roadmap for preventing similar issues in the future and improving the overall architecture of the nlp2cmd system.
