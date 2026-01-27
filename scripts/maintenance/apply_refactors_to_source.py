#!/usr/bin/env python3
"""Apply the cyclomatic complexity refactors permanently to source files."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from refactor_detect_normalized import apply_refactor_to_keyword_detector
from refactor_shell_entities import apply_refactor_to_template_generator


def apply_to_keywords_py():
    """Apply refactor to keywords.py file."""
    print("🔧 Applying refactor to keywords.py...")
    
    # Read the original file
    keywords_path = Path(__file__).parent.parent.parent / "src" / "nlp2cmd" / "generation" / "keywords.py"
    with open(keywords_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Store original methods
    original_methods = []
    
    # Apply refactor in memory
    original_detect_normalized = apply_refactor_to_keyword_detector()
    original_methods.append(original_detect_normalized)
    
    # Now we need to write the refactored code to the file
    # This is a simplified version - in production you'd want more sophisticated diff/patch
    print("   ⚠️  Manual application required for keywords.py")
    print("   Please copy the refactored methods from the in-memory version")
    
    return original_methods


def apply_to_templates_py():
    """Apply refactor to templates.py file."""
    print("🔧 Applying refactor to templates.py...")
    
    # Read the original file
    templates_path = Path(__file__).parent.parent.parent / "src" / "nlp2cmd" / "generation" / "templates.py"
    with open(templates_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Store original methods
    original_methods = []
    
    # Apply refactor in memory
    original_apply_shell_intent_specific_defaults = apply_refactor_to_template_generator()
    original_methods.append(original_apply_shell_intent_specific_defaults)
    
    print("   ⚠️  Manual application required for templates.py")
    print("   Please copy the refactored methods from the in-memory version")
    
    return original_methods


def create_patch_files():
    """Create patch files for manual application."""
    print("\n📝 Creating patch files...")
    
    # Create patch for keywords.py
    keywords_patch = Path(__file__).parent / "keywords.py.patch"
    with open(keywords_patch, 'w', encoding='utf-8') as f:
        f.write("""# Patch for keywords.py - Replace _detect_normalized method
# Location: around line 1278-1397

def _detect_normalized(self, text_lower: str) -> DetectionResult:
    \"\"\"Refactored detect method with reduced complexity.\"\"\"
    # Try ML classifier first for high-confidence matches (fastest, <1ms)
    result = self._detect_ml_classifier(text_lower)
    if result:
        return result
    
    # Try multilingual schema matching for high-confidence matches
    result = self._detect_schema_matcher(text_lower)
    if result:
        return result
    
    # ML classifier fallback for medium confidence (still useful)
    result = self._detect_ml_medium_confidence()
    if result:
        return result
    
    # Detect explicit domain-specific matches
    result = self._detect_explicit_matches(text_lower)
    if result:
        return result
    
    # Detect matches from priority intents and general patterns
    result = self._detect_pattern_matches(text_lower)
    if result:
        return result
    
    # Try fuzzy matching if available
    result = self._detect_fuzzy_match(text_lower)
    if result:
        return result
    
    # Fallback: Try multilingual fuzzy schema matching
    result = self._detect_schema_fallback(text_lower)
    if result:
        return result
    
    # Semantic matching fallback for typos and paraphrases (slower)
    result = self._detect_semantic_fallback(text_lower)
    if result:
        return result
    
    return DetectionResult(
        domain='unknown',
        intent='unknown',
        confidence=0.0,
        matched_keyword=None,
    )

# Add the helper methods before _detect_normalized
def _detect_ml_classifier(self, text_lower: str) -> Optional[DetectionResult]:
    \"\"\"Try ML classifier for high-confidence matches (fastest, <1ms).\"\"\"
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
        # Store for medium confidence fallback
        self._last_ml_result = ml_result
    return None

# ... (other helper methods from refactor_detect_normalized.py)
""")
    
    # Create patch for templates.py
    templates_patch = Path(__file__).parent / "templates.py.patch"
    with open(templates_patch, 'w', encoding='utf-8') as f:
        f.write("""# Patch for templates.py - Replace _apply_shell_intent_specific_defaults method
# Location: around line 900-1311

def _apply_shell_intent_specific_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    \"\"\"Refactored intent-specific defaults with reduced complexity.\"\"\"
    # File operations
    file_handlers = {
        'file_search': self._shell_intent_file_search,
        'file_content': self._shell_intent_file_content,
        'file_tail': self._shell_intent_file_tail,
        'file_size': self._shell_intent_file_size,
        'file_rename': self._shell_intent_file_rename,
        'file_delete_all': self._shell_intent_file_delete_all,
        'dir_create': self._shell_intent_dir_create,
        'remove_all': self._shell_intent_remove_all,
        'file_operation': self._shell_intent_file_operation,
    }
    
    # Check file handlers first
    handler = file_handlers.get(intent)
    if handler:
        handler(entities, result)
        return
    
    # Dispatch to category-specific handlers
    if intent.startswith('backup'):
        self._apply_shell_backup_defaults(intent, entities, result)
    elif intent.startswith('system'):
        self._apply_shell_system_defaults(intent, entities, result)
    elif intent.startswith('dev'):
        self._apply_shell_dev_defaults(intent, entities, result)
    elif intent.startswith('security'):
        self._apply_shell_security_defaults(intent, entities, result)
    elif intent.startswith('text_search'):
        self._apply_shell_text_search_defaults(intent, entities, result)
    elif intent.startswith('network'):
        self._apply_shell_network_defaults(intent, entities, result)
    elif intent.startswith('disk'):
        self._apply_shell_disk_defaults(intent, entities, result)
    elif intent.startswith('process'):
        self._apply_shell_process_defaults(intent, entities, result)
    elif intent.startswith('service'):
        self._apply_shell_service_defaults(intent, entities, result)
    elif intent in ('open_url', 'open_browser', 'browse', 'search_web', 'browser_history', 'browser_bookmarks'):
        self._apply_shell_browser_defaults(intent, entities, result)

# Add the helper methods before _apply_shell_intent_specific_defaults
def _apply_shell_backup_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    \"\"\"Apply backup-related defaults.\"\"\"
    backup_handlers = {
        'backup_create': self._shell_intent_backup_create,
        'backup_copy': self._shell_intent_backup_copy,
        'backup_restore': self._shell_intent_backup_restore,
        'backup_integrity': self._shell_intent_backup_integrity,
        'backup_status': self._shell_intent_backup_path,
        'backup_cleanup': self._shell_intent_backup_path,
        'backup_size': self._shell_intent_backup_size,
    }
    
    handler = backup_handlers.get(intent)
    if handler:
        handler(entities, result)

# ... (other helper methods from refactor_shell_entities.py)
""")
    
    print(f"   ✅ Created {keywords_patch}")
    print(f"   ✅ Created {templates_patch}")


def main():
    """Main function to apply refactors."""
    print("🚀 Applying cyclomatic complexity refactors to source files...\n")
    
    # Apply refactors
    keywords_methods = apply_to_keywords_py()
    templates_methods = apply_to_templates_py()
    
    # Create patch files
    create_patch_files()
    
    print("\n📋 Next steps:")
    print("1. Review the generated patch files")
    print("2. Manually apply the patches to the source files")
    print("3. Run tests to verify functionality")
    print("4. Commit the changes")
    
    print("\n✨ Refactoring prepared for application!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
