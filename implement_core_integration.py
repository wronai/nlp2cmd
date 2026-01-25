"""
Implement Core Integration for Polish Language Support
This script implements the actual integration of Polish patterns with NLP2CMD core system
"""

import json
import sys
import re
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class CoreIntegrator:
    """Integrates Polish language support with NLP2CMD core system"""
    
    def __init__(self):
        self.fixes_loaded = False
        self.polish_patterns = {}
        self.intent_mappings = {}
        self.table_mappings = {}
        self.domain_weights = {}
        
    def load_polish_fixes(self):
        """Load all Polish language fixes"""
        print("🔧 Loading Polish Language Fixes")
        print("-" * 50)
        
        # Load Polish shell patterns
        patterns_file = Path("polish_shell_patterns.json")
        if patterns_file.exists():
            with open(patterns_file, 'r', encoding='utf-8') as f:
                self.polish_patterns = json.load(f)
            print(f"✅ Loaded Polish shell patterns: {sum(len(p) for p in self.polish_patterns.values())} patterns")
        else:
            print("❌ Polish shell patterns file not found")
            return False
        
        # Load Polish intent mappings
        intent_file = Path("polish_intent_mappings.json")
        if intent_file.exists():
            with open(intent_file, 'r', encoding='utf-8') as f:
                self.intent_mappings = json.load(f)
            print(f"✅ Loaded Polish intent mappings: {len(self.intent_mappings)} mappings")
        else:
            print("❌ Polish intent mappings file not found")
            return False
        
        # Load Polish table mappings
        table_file = Path("polish_table_mappings.json")
        if table_file.exists():
            with open(table_file, 'r', encoding='utf-8') as f:
                self.table_mappings = json.load(f)
            print(f"✅ Loaded Polish table mappings: {len(self.table_mappings)} mappings")
        else:
            print("❌ Polish table mappings file not found")
            return False
        
        # Load domain weights
        weights_file = Path("domain_weights.json")
        if weights_file.exists():
            with open(weights_file, 'r', encoding='utf-8') as f:
                self.domain_weights = json.load(f)
            print(f"✅ Loaded domain weights: {len(self.domain_weights)} domains")
        else:
            print("❌ Domain weights file not found")
            return False
        
        self.fixes_loaded = True
        print("✅ All Polish fixes loaded successfully")
        return True
    
    def enhance_domain_detection(self):
        """Enhance domain detection with Polish patterns"""
        print("\n🔧 Enhancing Domain Detection")
        print("-" * 50)
        
        if not self.fixes_loaded:
            print("❌ Polish fixes not loaded")
            return False
        
        # Create enhanced domain detection patterns
        enhanced_patterns = {
            "shell": {
                "polish_patterns": [],
                "english_patterns": [
                    r"ls", r"pwd", r"cd", r"mkdir", r"rm", r"cp", r"mv",
                    r"ps", r"kill", r"top", r"free", r"ping", r"netstat"
                ],
                "weight": 1.0
            },
            "sql": {
                "polish_patterns": [],
                "english_patterns": [
                    r"SELECT", r"INSERT", r"UPDATE", r"DELETE", r"CREATE",
                    r"DROP", r"ALTER", r"FROM", r"WHERE", r"GROUP BY"
                ],
                "weight": 1.0
            },
            "docker": {
                "polish_patterns": [],
                "english_patterns": [
                    r"docker", r"container", r"image", r"run", r"stop",
                    r"start", r"ps", r"logs", r"exec", r"compose"
                ],
                "weight": 1.0
            },
            "kubernetes": {
                "polish_patterns": [],
                "english_patterns": [
                    r"kubectl", r"pod", r"service", r"deployment",
                    r"scale", r"apply", r"delete", r"describe", r"get"
                ],
                "weight": 1.0
            }
        }
        
        # Add Polish patterns to domains
        for category, patterns in self.polish_patterns.items():
            if category == "file_operations":
                enhanced_patterns["shell"]["polish_patterns"].extend(patterns)
            elif category == "process_operations":
                enhanced_patterns["shell"]["polish_patterns"].extend(patterns)
            elif category == "system_operations":
                enhanced_patterns["shell"]["polish_patterns"].extend(patterns)
        
        # Add domain weights
        for domain, weights in self.domain_weights.items():
            if domain in enhanced_patterns:
                enhanced_patterns[domain]["weight"] = weights.get("base_weight", 1.0)
        
        # Save enhanced patterns
        enhanced_file = Path("enhanced_domain_patterns.json")
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_patterns, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Enhanced domain patterns saved to: {enhanced_file}")
        
        # Show statistics
        for domain, config in enhanced_patterns.items():
            polish_count = len(config["polish_patterns"])
            english_count = len(config["english_patterns"])
            print(f"   {domain}: {polish_count} Polish + {english_count} English patterns")
        
        return True
    
    def create_enhanced_intent_detector(self):
        """Create enhanced intent detector with Polish mappings"""
        print("\n🔧 Creating Enhanced Intent Detector")
        print("-" * 50)
        
        if not self.fixes_loaded:
            print("❌ Polish fixes not loaded")
            return False
        
        # Create enhanced intent mappings
        enhanced_intents = {
            "shell": {
                "file_operations": {
                    "english_patterns": [
                        r"list", r"show", r"display", r"find", r"search",
                        r"copy", r"move", r"delete", r"remove", r"create",
                        r"make", r"rename", r"change"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "process_operations": {
                    "english_patterns": [
                        r"process", r"kill", r"start", r"stop", r"restart",
                        r"status", r"monitor", r"check", r"run"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "system_operations": {
                    "english_patterns": [
                        r"memory", r"disk", r"space", r"network", r"ping",
                        r"port", r"address", r"ip", r"connection"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                }
            },
            "sql": {
                "query_operations": {
                    "english_patterns": [
                        r"select", r"show", r"get", r"find", r"search",
                        r"list", r"display", r"retrieve"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "modification_operations": {
                    "english_patterns": [
                        r"insert", r"add", r"create", r"update", r"modify",
                        r"delete", r"remove", r"drop"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "aggregation_operations": {
                    "english_patterns": [
                        r"count", r"sum", r"avg", r"min", r"max",
                        r"group", r"aggregate", r"calculate"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                }
            },
            "docker": {
                "container_operations": {
                    "english_patterns": [
                        r"run", r"start", r"stop", r"restart", r"pause",
                        r"unpause", r"kill", r"rm", r"remove"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "management_operations": {
                    "english_patterns": [
                        r"ps", r"list", r"show", r"logs", r"inspect",
                        r"stats", r"top", r"exec", r"attach"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "compose_operations": {
                    "english_patterns": [
                        r"compose", r"up", r"down", r"build", r"pull",
                        r"push", r"logs", r"ps", r"stop", r"start"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                }
            },
            "kubernetes": {
                "pod_operations": {
                    "english_patterns": [
                        r"pod", r"pods", r"get", r"describe", r"logs",
                        r"exec", r"delete", r"create", r"apply"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "deployment_operations": {
                    "english_patterns": [
                        r"deployment", r"deployments", r"scale", r"rollout",
                        r"restart", r"undo", r"history", r"status"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                },
                "service_operations": {
                    "english_patterns": [
                        r"service", r"services", r"expose", r"port-forward",
                        r"proxy", r"get", r"describe", r"delete"
                    ],
                    "polish_patterns": [],
                    "polish_mappings": {}
                }
            }
        }
        
        # Add Polish mappings to shell intents
        shell_intents = enhanced_intents["shell"]
        for polish, english in self.intent_mappings.items():
            if english in ["copy", "move", "delete", "create", "rename", "find", "show", "list"]:
                shell_intents["file_operations"]["polish_mappings"][polish] = english
            elif english in ["start", "stop", "restart", "kill", "monitor", "check"]:
                shell_intents["process_operations"]["polish_mappings"][polish] = english
            elif english in ["show", "check", "open"]:
                shell_intents["system_operations"]["polish_mappings"][polish] = english
        
        # Add Polish table mappings to SQL
        sql_intents = enhanced_intents["sql"]
        for polish_pattern, english_table in self.table_mappings.items():
            # Add to query operations
            if any(word in polish_pattern for word in ["pokaż", "znajdź", "lista"]):
                sql_intents["query_operations"]["polish_mappings"][polish_pattern] = english_table
        
        # Save enhanced intents
        enhanced_intents_file = Path("enhanced_intents.json")
        with open(enhanced_intents_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_intents, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Enhanced intents saved to: {enhanced_intents_file}")
        
        # Show statistics
        for domain, intents in enhanced_intents.items():
            total_mappings = sum(len(intent_cat["polish_mappings"]) for intent_cat in intents.values())
            print(f"   {domain}: {total_mappings} Polish mappings")
        
        return True
    
    def create_polish_language_module(self):
        """Create a Polish language module for NLP2CMD"""
        print("\n🔧 Creating Polish Language Module")
        print("-" * 50)
        
        polish_module_code = '''
"""
Polish Language Support Module for NLP2CMD
Provides Polish language patterns and mappings
"""

import json
import re
from pathlib import Path

class PolishLanguageSupport:
    """Polish language support for NLP2CMD"""
    
    def __init__(self):
        self.patterns = {}
        self.intent_mappings = {}
        self.table_mappings = {}
        self.domain_weights = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load Polish language patterns"""
        try:
            # Load Polish shell patterns
            patterns_file = Path("polish_shell_patterns.json")
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            
            # Load Polish intent mappings
            intent_file = Path("polish_intent_mappings.json")
            if intent_file.exists():
                with open(intent_file, 'r', encoding='utf-8') as f:
                    self.intent_mappings = json.load(f)
            
            # Load Polish table mappings
            table_file = Path("polish_table_mappings.json")
            if table_file.exists():
                with open(table_file, 'r', encoding='utf-8') as f:
                    self.table_mappings = json.load(f)
            
            # Load domain weights
            weights_file = Path("domain_weights.json")
            if weights_file.exists():
                with open(weights_file, 'r', encoding='utf-8') as f:
                    self.domain_weights = json.load(f)
                    
        except Exception as e:
            print(f"Error loading Polish patterns: {e}")
    
    def normalize_polish_text(self, text):
        """Normalize Polish text for better matching"""
        # Convert to lowercase
        text = text.lower()
        
        # Handle common Polish diacritics variations
        diacritic_map = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'a', 'Ć': 'c', 'Ę': 'e', 'Ł': 'l', 'Ń': 'n',
            'Ó': 'o', 'Ś': 's', 'Ź': 'z', 'Ż': 'z'
        }
        
        for polish, latin in diacritic_map.items():
            text = text.replace(polish, latin)
        
        return text
    
    def match_polish_patterns(self, text, domain):
        """Match Polish patterns for given domain"""
        if domain not in self.patterns:
            return []
        
        matches = []
        normalized_text = self.normalize_polish_text(text)
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, normalized_text, re.IGNORECASE):
                        matches.append({
                            'category': category,
                            'pattern': pattern,
                            'match': True
                        })
                except re.error:
                    continue
        
        return matches
    
    def translate_polish_intent(self, text):
        """Translate Polish intent to English"""
        normalized_text = self.normalize_polish_text(text)
        
        for polish, english in self.intent_mappings.items():
            if polish in normalized_text:
                return english
        
        return None
    
    def translate_polish_table(self, text):
        """Translate Polish table name to English"""
        normalized_text = self.normalize_polish_text(text)
        
        for polish_pattern, english_table in self.table_mappings.items():
            try:
                if re.search(polish_pattern, normalized_text, re.IGNORECASE):
                    return english_table
            except re.error:
                continue
        
        return None
    
    def get_domain_weight(self, domain):
        """Get domain weight for Polish text"""
        return self.domain_weights.get(domain, {}).get("base_weight", 1.0)
    
    def enhance_domain_detection(self, text, base_domain):
        """Enhance domain detection with Polish patterns"""
        # Check if Polish patterns suggest a different domain
        polish_matches = self.match_polish_patterns(text, "shell")
        
        if polish_matches and base_domain == "sql":
            # Polish file operations detected, prefer shell
            return "shell"
        
        return base_domain
    
    def enhance_intent_detection(self, text, base_intent):
        """Enhance intent detection with Polish mappings"""
        # Try to translate Polish intent
        translated_intent = self.translate_polish_intent(text)
        
        if translated_intent:
            return translated_intent
        
        return base_intent

# Global instance
polish_support = PolishLanguageSupport()

def get_polish_support():
    """Get Polish language support instance"""
    return polish_support
'''
        
        # Save Polish language module
        module_file = Path("src/nlp2cmd/polish_support.py")
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write(polish_module_code)
        
        print(f"✅ Polish language module created: {module_file}")
        return True
    
    def create_core_integration_patch(self):
        """Create patch for core integration"""
        print("\n🔧 Creating Core Integration Patch")
        print("-" * 50)
        
        # Read current core.py
        core_file = Path("src/nlp2cmd/core.py")
        if not core_file.exists():
            print("❌ Core file not found")
            return False
        
        with open(core_file, 'r', encoding='utf-8') as f:
            core_content = f.read()
        
        # Create integration patch
        integration_code = '''
# Polish Language Support Integration
try:
    from .polish_support import get_polish_support
    polish_support = get_polish_support()
    POLISH_SUPPORT_ENABLED = True
except ImportError:
    polish_support = None
    POLISH_SUPPORT_ENABLED = False

# Enhanced domain detection with Polish support
def enhanced_domain_detection(query, base_domain):
    """Enhanced domain detection with Polish language support"""
    if not POLISH_SUPPORT_ENABLED:
        return base_domain
    
    # Use Polish support to enhance domain detection
    return polish_support.enhance_domain_detection(query, base_domain)

# Enhanced intent detection with Polish support
def enhanced_intent_detection(query, base_intent):
    """Enhanced intent detection with Polish language support"""
    if not POLISH_SUPPORT_ENABLED:
        return base_intent
    
    # Use Polish support to enhance intent detection
    return polish_support.enhance_intent_detection(query, base_intent)
'''
        
        # Find where to insert the integration code
        # Look for imports section
        import_end = core_content.find("import")
        if import_end == -1:
            import_end = 0
        
        # Find the end of imports section
        lines = core_content.split('\n')
        import_line_count = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import') or line.strip().startswith('from'):
                import_line_count = i + 1
        
        # Insert integration code after imports
        if import_line_count > 0:
            lines.insert(import_line_count, integration_code)
            patched_content = '\n'.join(lines)
        else:
            patched_content = integration_code + '\n' + core_content
        
        # Save patched core
        patched_file = Path("src/nlp2cmd/core_patched.py")
        with open(patched_file, 'w', encoding='utf-8') as f:
            f.write(patched_content)
        
        print(f"✅ Core integration patch created: {patched_file}")
        
        # Also create a backup of original
        backup_file = Path("src/nlp2cmd/core_backup.py")
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(core_content)
        
        print(f"✅ Core backup created: {backup_file}")
        
        return True
    
    def create_adapter_patches(self):
        """Create patches for adapters"""
        print("\n🔧 Creating Adapter Patches")
        print("-" * 50)
        
        adapters = [
            "src/nlp2cmd/adapters/shell.py",
            "src/nlp2cmd/adapters/sql.py",
            "src/nlp2cmd/adapters/docker.py",
            "src/nlp2cmd/adapters/kubernetes.py"
        ]
        
        for adapter_path in adapters:
            adapter_file = Path(adapter_path)
            if adapter_file.exists():
                with open(adapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create backup
                backup_path = adapter_path.replace('.py', '_backup.py')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Add Polish support integration
                polish_integration = '''
# Polish Language Support Integration
try:
    from ..polish_support import get_polish_support
    polish_support = get_polish_support()
    POLISH_SUPPORT_ENABLED = True
except ImportError:
    polish_support = None
    POLISH_SUPPORT_ENABLED = False
'''
                
                # Insert after imports
                lines = content.split('\n')
                import_line_count = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import') or line.strip().startswith('from'):
                        import_line_count = i + 1
                
                if import_line_count > 0:
                    lines.insert(import_line_count, polish_integration)
                    patched_content = '\n'.join(lines)
                else:
                    patched_content = polish_integration + '\n' + content
                
                # Save patched adapter
                patched_path = adapter_path.replace('.py', '_patched.py')
                with open(patched_path, 'w', encoding='utf-8') as f:
                    f.write(patched_content)
                
                print(f"✅ Adapter patch created: {patched_path}")
            else:
                print(f"⚠️  Adapter not found: {adapter_path}")
        
        return True
    
    def create_integration_script(self):
        """Create final integration script"""
        print("\n🔧 Creating Final Integration Script")
        print("-" * 50)
        
        integration_script = '''#!/usr/bin/env python3
"""
Final Integration Script for Polish Language Support
Applies all patches and enables Polish language support in NLP2CMD
"""

import shutil
import sys
from pathlib import Path

def apply_core_patch():
    """Apply core patch"""
    print("🔧 Applying core patch...")
    
    core_backup = Path("src/nlp2cmd/core_backup.py")
    core_patched = Path("src/nlp2cmd/core_patched.py")
    core_current = Path("src/nlp2cmd/core.py")
    
    if core_patched.exists():
        # Backup current core
        if core_current.exists():
            shutil.copy2(core_current, core_backup)
        
        # Apply patch
        shutil.copy2(core_patched, core_current)
        print("✅ Core patch applied")
        return True
    else:
        print("❌ Core patch not found")
        return False

def apply_adapter_patches():
    """Apply adapter patches"""
    print("🔧 Applying adapter patches...")
    
    adapters = [
        "src/nlp2cmd/adapters/shell.py",
        "src/nlp2cmd/adapters/sql.py", 
        "src/nlp2cmd/adapters/docker.py",
        "src/nlp2cmd/adapters/kubernetes.py"
    ]
    
    success_count = 0
    
    for adapter in adapters:
        adapter_path = Path(adapter)
        patched_path = adapter_path.replace('.py', '_patched.py')
        
        if patched_path.exists():
            # Apply patch
            shutil.copy2(patched_path, adapter_path)
            print(f"✅ {adapter} patch applied")
            success_count += 1
        else:
            print(f"❌ {adapter} patch not found")
    
    return success_count == len(adapters)

def verify_integration():
    """Verify integration"""
    print("🔍 Verifying integration...")
    
    try:
        # Try to import Polish support
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from nlp2cmd.polish_support import get_polish_support
        polish_support = get_polish_support()
        
        print("✅ Polish support module imported successfully")
        
        # Check if patterns are loaded
        if polish_support.patterns:
            print(f"✅ Polish patterns loaded: {len(polish_support.patterns)} categories")
        
        if polish_support.intent_mappings:
            print(f"✅ Intent mappings loaded: {len(polish_support.intent_mappings)} mappings")
        
        if polish_support.table_mappings:
            print(f"✅ Table mappings loaded: {len(polish_support.table_mappings)} mappings")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration verification failed: {e}")
        return False

def main():
    """Main integration function"""
    print("🚀 Applying Polish Language Support Integration")
    print("=" * 60)
    
    # Apply core patch
    core_success = apply_core_patch()
    
    # Apply adapter patches
    adapters_success = apply_adapter_patches()
    
    # Verify integration
    verification_success = verify_integration()
    
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION RESULTS")
    print("=" * 60)
    
    print(f"Core patch: {'✅ Applied' if core_success else '❌ Failed'}")
        print(f"Adapter patches: {'✅ Applied' if adapters_success else '❌ Failed'}")
        print(f"Verification: {'✅ Passed' if verification_success else '❌ Failed'}")
        
        if core_success and adapters_success and verification_success:
            print("\\n🎉 Integration successful!")
            print("Polish language support is now enabled in NLP2CMD")
            print("\\nNext steps:")
            print("1. Test Polish commands")
            print("2. Run comprehensive test suite")
            print("3. Monitor performance improvements")
        else:
            print("\\n⚠️  Integration incomplete")
            print("Please check the errors above and retry")
    
    return core_success and adapters_success and verification_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        # Save integration script
        script_file = Path("apply_polish_integration.py")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(integration_script)
        
        # Make it executable
        script_file.chmod(0o755)
        
        print(f"✅ Final integration script created: {script_file}")
        return True
    
    def run_integration(self):
        """Run the complete integration"""
        print("🚀 Running Complete Integration")
        print("=" * 60)
        
        # Step 1: Load Polish fixes
        if not self.load_polish_fixes():
            print("❌ Failed to load Polish fixes")
            return False
        
        # Step 2: Enhance domain detection
        if not self.enhance_domain_detection():
            print("❌ Failed to enhance domain detection")
            return False
        
        # Step 3: Create enhanced intent detector
        if not self.create_enhanced_intent_detector():
            print("❌ Failed to create enhanced intent detector")
            return False
        
        # Step 4: Create Polish language module
        if not self.create_polish_language_module():
            print("❌ Failed to create Polish language module")
            return False
        
        # Step 5: Create core integration patch
        if not self.create_core_integration_patch():
            print("❌ Failed to create core integration patch")
            return False
        
        # Step 6: Create adapter patches
        if not self.create_adapter_patches():
            print("❌ Failed to create adapter patches")
            return False
        
        # Step 7: Create final integration script
        if not self.create_integration_script():
            print("❌ Failed to create integration script")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 INTEGRATION PREPARATION COMPLETE")
        print("=" * 60)
        
        print("✅ All integration components created successfully")
        print("✅ Ready to apply Polish language support")
        print("\nNext step:")
        print("Run: python3 apply_polish_integration.py")
        
        return True

def main():
    """Main integration function"""
    print("🔧 NLP2CMD Polish Language Support Integration")
    print("=" * 60)
    
    integrator = CoreIntegrator()
    success = integrator.run_integration()
    
    if success:
        print("\n🎉 Integration preparation successful!")
        print("Polish language support is ready to be applied")
    else:
        print("\n❌ Integration preparation failed")
        print("Please check the errors above")
    
    return success

if __name__ == "__main__":
    main()
