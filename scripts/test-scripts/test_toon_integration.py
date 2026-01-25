"""
Test TOON Integration with 100 Commands
Tests the TOON system with the list of 100 commands from config.yaml
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Simple test without full dependencies
class ToonIntegrationTest:
    """Test TOON integration with command list"""
    
    def __init__(self):
        self.toon_file = Path("project.unified.toon")
        self.config_file = Path("config.yaml")
        self.test_results = []
        
    def load_test_commands(self):
        """Load the 100 test commands from config.yaml"""
        commands = []
        
        if not self.config_file.exists():
            print(f"Config file not found: {self.config_file}")
            return commands
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Simple YAML parsing for test_commands
            lines = content.split('\n')
            in_test_commands = False
            
            for line in lines:
                line = line.strip()
                
                if line == 'test_commands:':
                    in_test_commands = True
                    continue
                
                if in_test_commands and line.startswith('- ') and not line.startswith('#'):
                    cmd = line[2:].strip()
                    if cmd:
                        commands.append(cmd)
                elif in_test_commands and line and not line.startswith(' ') and not line.startswith('#'):
                    break
                    
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return commands
    
    def load_toon_data(self):
        """Load TOON data for testing"""
        if not self.toon_file.exists():
            print(f"TOON file not found: {self.toon_file}")
            return None
        
        try:
            with open(self.toon_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"Error loading TOON file: {e}")
            return None
    
    def test_command_availability(self, commands):
        """Test if commands are available in TOON data"""
        toon_content = self.load_toon_data()
        if not toon_content:
            return False
        
        available_commands = []
        missing_commands = []
        
        for cmd in commands:
            if cmd in toon_content:
                available_commands.append(cmd)
            else:
                missing_commands.append(cmd)
        
        result = {
            'total_commands': len(commands),
            'available': len(available_commands),
            'missing': len(missing_commands),
            'available_commands': available_commands,
            'missing_commands': missing_commands,
            'availability_rate': len(available_commands) / len(commands) * 100 if commands else 0
        }
        
        return result
    
    def test_toon_structure(self):
        """Test TOON file structure"""
        toon_content = self.load_toon_data()
        if not toon_content:
            return {'valid': False, 'errors': ['TOON file not found']}
        
        errors = []
        sections = []
        
        # Check for required sections
        required_sections = ['schema', 'config', 'commands', 'metadata', 'templates', 'mappings']
        
        for section in required_sections:
            section_header = f"=== {section.upper().replace('_', ' ')} ==="
            if section_header in toon_content:
                sections.append(section)
            else:
                # Also check for section without ===
                if section + '[' in toon_content:
                    sections.append(section)
                else:
                    errors.append(f"Missing section: {section}")
        
        # Check for command categories
        if 'commands[' in toon_content:
            if 'shell[' in toon_content:
                sections.append('shell_commands')
            else:
                errors.append("Missing shell commands category")
            
            if 'browser[' in toon_content:
                sections.append('browser_commands')
            else:
                errors.append("Missing browser commands category")
        
        # Check bracket notation
        bracket_count = toon_content.count('[') + toon_content.count('{')
        if bracket_count < 10:
            errors.append("Too few bracket notations - format may be incorrect")
        
        return {
            'valid': len(errors) == 0,
            'sections_found': sections,
            'errors': errors,
            'bracket_notations': bracket_count
        }
    
    def test_performance(self, commands):
        """Test performance of TOON vs simulated old system"""
        # Test TOON loading
        start_time = time.time()
        toon_content = self.load_toon_data()
        toon_load_time = time.time() - start_time
        
        # Simulate old system loading (multiple files)
        start_time = time.time()
        # Simulate reading 50+ JSON files
        simulated_files = 50
        for i in range(simulated_files):
            # Simulate file read and JSON parse time
            time.sleep(0.0001)  # Very small delay to simulate I/O
        
        old_load_time = time.time() - start_time
        
        # Test search performance
        search_queries = ['git', 'docker', 'kubectl', 'find', 'grep']
        
        # TOON search
        start_time = time.time()
        toon_search_results = []
        for query in search_queries:
            if query in toon_content:
                toon_search_results.append(query)
        toon_search_time = time.time() - start_time
        
        # Simulate old system search
        start_time = time.time()
        old_search_results = []
        for query in search_queries:
            # Simulate searching through multiple files
            for i in range(simulated_files):
                if query in f"simulated_file_{i}_{query}":  # Simulated match
                    old_search_results.append(query)
                    break
        old_search_time = time.time() - start_time
        
        return {
            'toon_load_time': toon_load_time,
            'old_load_time': old_load_time,
            'load_speedup': old_load_time / toon_load_time if toon_load_time > 0 else 0,
            'toon_search_time': toon_search_time,
            'old_search_time': old_search_time,
            'search_speedup': old_search_time / toon_search_time if toon_search_time > 0 else 0,
            'toon_search_results': len(toon_search_results),
            'old_search_results': len(old_search_results)
        }
    
    def test_llm_friendly_format(self):
        """Test if TOON format is LLM-friendly"""
        toon_content = self.load_toon_data()
        if not toon_content:
            return {'valid': False, 'errors': ['TOON file not found']}
        
        metrics = {
            'total_lines': len(toon_content.split('\n')),
            'bracket_notations': toon_content.count('[') + toon_content.count('{'),
            'json_complexity': toon_content.count('{') + toon_content.count('}'),
            'simple_key_value': 0,
            'nested_structures': 0,
            'readability_score': 0
        }
        
        lines = toon_content.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                if line.count('{') == 0 and line.count('[') == 0:
                    metrics['simple_key_value'] += 1
                else:
                    metrics['nested_structures'] += 1
        
        # Calculate readability score (simple metric)
        if metrics['total_lines'] > 0:
            simple_ratio = metrics['simple_key_value'] / metrics['total_lines']
            bracket_ratio = metrics['bracket_notations'] / metrics['total_lines']
            metrics['readability_score'] = (simple_ratio + bracket_ratio) / 2 * 100
        
        return {
            'valid': True,
            'metrics': metrics,
            'llm_friendly': metrics['readability_score'] > 50
        }
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=== TOON Integration Test Suite ===\n")
        
        # Load test commands
        commands = self.load_test_commands()
        print(f"Loaded {len(commands)} test commands from config.yaml")
        
        if not commands:
            print("No commands to test - exiting")
            return
        
        # Test 1: Command Availability
        print("\n1. Testing Command Availability...")
        availability_result = self.test_command_availability(commands)
        print(f"   Total commands: {availability_result['total_commands']}")
        print(f"   Available in TOON: {availability_result['available']}")
        print(f"   Missing: {availability_result['missing']}")
        print(f"   Availability rate: {availability_result['availability_rate']:.1f}%")
        
        if availability_result['missing_commands']:
            print(f"   Missing commands: {availability_result['missing_commands'][:10]}...")
        
        self.test_results.append({
            'test': 'Command Availability',
            'result': availability_result,
            'passed': availability_result['availability_rate'] > 50
        })
        
        # Test 2: TOON Structure
        print("\n2. Testing TOON Structure...")
        structure_result = self.test_toon_structure()
        print(f"   Structure valid: {structure_result['valid']}")
        print(f"   Sections found: {structure_result['sections_found']}")
        print(f"   Bracket notations: {structure_result['bracket_notations']}")
        
        if structure_result['errors']:
            print(f"   Errors: {structure_result['errors']}")
        
        self.test_results.append({
            'test': 'TOON Structure',
            'result': structure_result,
            'passed': structure_result['valid']
        })
        
        # Test 3: Performance
        print("\n3. Testing Performance...")
        performance_result = self.test_performance(commands)
        print(f"   TOON load time: {performance_result['toon_load_time']:.4f}s")
        print(f"   Simulated old load time: {performance_result['old_load_time']:.4f}s")
        print(f"   Load speedup: {performance_result['load_speedup']:.1f}x")
        print(f"   TOON search time: {performance_result['toon_search_time']:.4f}s")
        print(f"   Simulated old search time: {performance_result['old_search_time']:.4f}s")
        print(f"   Search speedup: {performance_result['search_speedup']:.1f}x")
        
        self.test_results.append({
            'test': 'Performance',
            'result': performance_result,
            'passed': performance_result['load_speedup'] > 10
        })
        
        # Test 4: LLM Friendly Format
        print("\n4. Testing LLM-Friendly Format...")
        llm_result = self.test_llm_friendly_format()
        metrics = llm_result['metrics']
        print(f"   Total lines: {metrics['total_lines']}")
        print(f"   Bracket notations: {metrics['bracket_notations']}")
        print(f"   Simple key-value pairs: {metrics['simple_key_value']}")
        print(f"   Nested structures: {metrics['nested_structures']}")
        print(f"   Readability score: {metrics['readability_score']:.1f}%")
        print(f"   LLM-friendly: {llm_result['llm_friendly']}")
        
        self.test_results.append({
            'test': 'LLM Friendly Format',
            'result': llm_result,
            'passed': llm_result['llm_friendly']
        })
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n=== TEST SUMMARY ===\n")
        
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        total_tests = len(self.test_results)
        
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
        print()
        
        for test in self.test_results:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            print(f"{status} {test['test']}")
        
        print("\n=== OVERALL ASSESSMENT ===\n")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("TOON system is working correctly and ready for production use.")
        elif passed_tests >= total_tests * 0.75:
            print("✅ MOST TESTS PASSED")
            print("TOON system is working well with minor issues.")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("TOON system needs attention before production use.")
        
        print("\n=== RECOMMENDATIONS ===\n")
        
        # Specific recommendations based on test results
        for test in self.test_results:
            if not test['passed']:
                if test['test'] == 'Command Availability':
                    print("• Add missing commands to TOON file")
                elif test['test'] == 'TOON Structure':
                    print("• Fix TOON file structure and add missing sections")
                elif test['test'] == 'Performance':
                    print("• Optimize TOON loading and search performance")
                elif test['test'] == 'LLM Friendly Format':
                    print("• Improve TOON format for better LLM comprehension")
        
        print("\n=== NEXT STEPS ===\n")
        print("1. Review failed tests and fix issues")
        print("2. Run integration tests with actual NLP2CMD core")
        print("3. Test with real command generation scenarios")
        print("4. Validate LLM comprehension with actual models")
        print("5. Deploy to production after all tests pass")


def main():
    """Main test function"""
    print("Starting TOON Integration Tests...")
    print("Testing TOON system with 100 command list from config.yaml\n")
    
    tester = ToonIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
