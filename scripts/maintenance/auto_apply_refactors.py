#!/usr/bin/env python3
"""Automated script to apply refactors directly to source files."""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def apply_keywords_refactor():
    """Apply refactor to keywords.py file."""
    print("🔧 Applying refactor to keywords.py...")
    
    keywords_path = Path(__file__).parent.parent.parent / "src" / "nlp2cmd" / "generation" / "keywords.py"
    
    # Read the file
    with open(keywords_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the _detect_normalized method
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if "def _detect_normalized(self, text_lower: str) -> DetectionResult:" in line:
            start_idx = i
        elif start_idx is not None and line.strip() and not line.startswith("    ") and not line.startswith("\t"):
            end_idx = i
            break
    
    if start_idx is None:
        print("   ❌ Could not find _detect_normalized method")
        return False
    
    # Read the refactored methods
    with open(Path(__file__).parent / "refactor_detect_normalized.py", 'r', encoding='utf-8') as f:
        refactor_content = f.read()
    
    # Extract helper methods and main method
    helper_methods = []
    main_method = None
    
    # Parse the refactor file to extract methods
    current_method = []
    in_method = False
    method_name = None
    
    for line in refactor_content.split('\n'):
        if line.startswith('def _detect_') or line.startswith('def _apply_shell_'):
            if current_method:
                method_code = '\n'.join(current_method)
                if method_name:
                    helper_methods.append((method_name, method_code))
            current_method = [line]
            method_name = line.split('(')[0].replace('def ', '')
            in_method = True
        elif in_method:
            current_method.append(line)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # End of method
                method_code = '\n'.join(current_method[:-1])
                if method_name:
                    helper_methods.append((method_name, method_code))
                current_method = []
                in_method = False
                method_name = None
    
    # Build the new file content
    new_lines = lines[:start_idx]
    
    # Add helper methods first
    new_lines.append("\n# Helper methods for intent detection (refactored for reduced complexity)\n")
    for name, code in helper_methods:
        if name.startswith('_detect_'):
            new_lines.append(f"{code}\n\n")
    
    # Add the main refactored method
    main_method_code = '''def _detect_normalized(self, text_lower: str) -> DetectionResult:
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
'''
    
    new_lines.append(main_method_code)
    new_lines.extend(lines[end_idx:])
    
    # Write the file
    with open(keywords_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("   ✅ Successfully applied refactor to keywords.py")
    return True


def apply_templates_refactor():
    """Apply refactor to templates.py file."""
    print("🔧 Applying refactor to templates.py...")
    
    templates_path = Path(__file__).parent.parent.parent / "src" / "nlp2cmd" / "generation" / "templates.py"
    
    # Read the file
    with open(templates_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Read the refactored methods
    with open(Path(__file__).parent / "refactor_shell_entities.py", 'r', encoding='utf-8') as f:
        refactor_content = f.read()
    
    # Extract helper methods
    helper_methods = []
    current_method = []
    in_method = False
    method_name = None
    
    for line in refactor_content.split('\n'):
        if line.startswith('def _apply_shell_') and 'defaults' in line:
            if current_method:
                method_code = '\n'.join(current_method)
                if method_name:
                    helper_methods.append((method_name, method_code))
            current_method = [line]
            method_name = line.split('(')[0].replace('def ', '')
            in_method = True
        elif in_method:
            current_method.append(line)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#'):
                # End of method
                method_code = '\n'.join(current_method[:-1])
                if method_name:
                    helper_methods.append((method_name, method_code))
                current_method = []
                in_method = False
                method_name = None
    
    # Find and replace the _apply_shell_intent_specific_defaults method
    pattern = r'(\s+def _apply_shell_intent_specific_defaults\(self[^:]+:\s*"""[^"]*"""[\s\S]*?)(?=\n    def |\n\nclass |\Z)'
    
    new_method = '''    def _apply_shell_intent_specific_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        """Refactored intent-specific defaults with reduced complexity."""
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
            self._apply_shell_browser_defaults(intent, entities, result)'''
    
    # Replace the method
    new_content = re.sub(pattern, new_method, content, flags=re.MULTILINE | re.DOTALL)
    
    # Add helper methods before the main method
    insert_pos = new_content.find('def _apply_shell_intent_specific_defaults(')
    if insert_pos > 0:
        helper_code = '\n\n    # Helper methods for shell intent defaults (refactored for reduced complexity)\n'
        for name, code in helper_methods:
            # Fix indentation (add 4 spaces)
            indented_code = '\n'.join('    ' + line if line.strip() else line for line in code.split('\n'))
            helper_code += f'\n{indented_code}\n'
        
        new_content = new_content[:insert_pos] + helper_code + new_content[insert_pos:]
    
    # Write the file
    with open(templates_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("   ✅ Successfully applied refactor to templates.py")
    return True


def main():
    """Main function to apply refactors."""
    print("🚀 Automatically applying cyclomatic complexity refactors...\n")
    
    # Apply refactors
    keywords_success = apply_keywords_refactor()
    templates_success = apply_templates_refactor()
    
    if keywords_success and templates_success:
        print("\n✅ All refactors applied successfully!")
        print("\n📋 Next steps:")
        print("1. Run tests to verify functionality")
        print("2. Review the changes")
        print("3. Commit the changes")
        
        # Run tests
        print("\n🧪 Running tests...")
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/unit/test_refactored_methods.py", "-v"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
        
        return 0
    else:
        print("\n❌ Some refactors failed to apply")
        return 1


if __name__ == "__main__":
    sys.exit(main())
