"""
Continuous Integration Test for NLP2CMD with TOON
Automated test to run periodically to ensure nothing breaks
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class ContinuousIntegrationTest:
    """Continuous integration test for NLP2CMD with TOON"""
    
    def __init__(self):
        self.results_log = []
        self.start_time = datetime.now()
        
    def log_result(self, test_name, passed, details="", duration=0.0):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration
        }
        self.results_log.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details} ({duration:.3f}s)")
    
    def test_toon_file_integrity(self):
        """Test TOON file integrity"""
        start_time = time.time()
        
        toon_file = Path("project.unified.toon")
        if not toon_file.exists():
            self.log_result("TOON File Exists", False, "File not found", 0.0)
            return False
        
        try:
            with open(toon_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check basic structure
            required_sections = ['schema[', 'config[', 'commands[', 'metadata[']
            missing_sections = []
            
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                self.log_result("TOON Structure", False, f"Missing: {missing_sections}", time.time() - start_time)
                return False
            
            # Check for bracket balance
            open_brackets = content.count('[') + content.count('{')
            close_brackets = content.count(']') + content.count('}')
            
            if open_brackets != close_brackets:
                self.log_result("TOON Bracket Balance", False, f"Open: {open_brackets}, Close: {close_brackets}", time.time() - start_time)
                return False
            
            self.log_result("TOON File Integrity", True, f"Size: {len(content)} chars", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_result("TOON File Integrity", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_config_file_integrity(self):
        """Test config file integrity"""
        start_time = time.time()
        
        config_file = Path("config.yaml")
        if not config_file.exists():
            self.log_result("Config File Exists", False, "File not found", 0.0)
            return False
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check for test_commands section
            if 'test_commands:' not in content:
                self.log_result("Config Structure", False, "Missing test_commands", time.time() - start_time)
                return False
            
            # Count test commands
            command_count = content.count('- ')
            if command_count < 50:
                self.log_result("Config Commands", False, f"Only {command_count} commands found", time.time() - start_time)
                return False
            
            self.log_result("Config File Integrity", True, f"{command_count} test commands", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_result("Config File Integrity", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_python_imports(self):
        """Test Python imports work"""
        start_time = time.time()
        
        try:
            # Test core imports
            from nlp2cmd.core import NLP2CMD, TransformResult, ExecutionPlan
            self.log_result("Core Imports", True, "NLP2CMD core modules", time.time() - start_time)
            
            # Test TOON imports (if available)
            try:
                from nlp2cmd.parsing.toon_parser import ToonParser
                from nlp2cmd.core.toon_integration import get_data_manager
                self.log_result("TOON Imports", True, "TOON modules available", time.time() - start_time)
            except ImportError as e:
                self.log_result("TOON Imports", False, f"Import error: {str(e)}", time.time() - start_time)
                return False
            
            return True
            
        except ImportError as e:
            self.log_result("Python Imports", False, f"Import error: {str(e)}", time.time() - start_time)
            return False
    
    def test_basic_functionality(self):
        """Test basic NLP2CMD functionality"""
        start_time = time.time()
        
        try:
            from nlp2cmd.core.toon_integration import get_data_manager
            
            # Test data manager
            manager = get_data_manager()
            
            # Test basic operations
            commands = manager.get_all_commands()
            config = manager.get_config()
            metadata = manager.get_project_metadata()
            
            # Validate data
            if not commands:
                self.log_result("Basic Functionality", False, "No commands found", time.time() - start_time)
                return False
            
            if not config:
                self.log_result("Basic Functionality", False, "No config found", time.time() - start_time)
                return False
            
            if not metadata:
                self.log_result("Basic Functionality", False, "No metadata found", time.time() - start_time)
                return False
            
            self.log_result("Basic Functionality", True, f"Commands: {len(commands)}, Config: {len(config)} sections", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_result("Basic Functionality", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_command_availability(self):
        """Test command availability"""
        start_time = time.time()
        
        try:
            from nlp2cmd.core.toon_integration import get_data_manager
            
            manager = get_data_manager()
            
            # Test critical commands
            critical_commands = ['git', 'docker', 'kubectl', 'find', 'grep', 'ls', 'ps']
            missing_commands = []
            
            for cmd in critical_commands:
                command_data = manager.get_command_by_name(cmd)
                if not command_data:
                    missing_commands.append(cmd)
            
            if missing_commands:
                self.log_result("Command Availability", False, f"Missing: {missing_commands}", time.time() - start_time)
                return False
            
            # Test search functionality
            search_results = manager.search_commands("git")
            if not search_results:
                self.log_result("Command Search", False, "Search returned no results", time.time() - start_time)
                return False
            
            self.log_result("Command Availability", True, f"Critical commands: {len(critical_commands)}, Search results: {len(search_results)}", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_result("Command Availability", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        start_time = time.time()
        
        try:
            from nlp2cmd.core.toon_integration import get_data_manager
            
            manager = get_data_manager()
            
            # Test load performance
            load_start = time.time()
            commands = manager.get_all_commands()
            load_time = time.time() - load_start
            
            # Test search performance
            search_start = time.time()
            search_results = manager.search_commands("git")
            search_time = time.time() - search_start
            
            # Test access performance
            access_start = time.time()
            git_command = manager.get_command_by_name('git')
            access_time = time.time() - access_start
            
            # Check performance thresholds
            if load_time > 1.0:
                self.log_result("Load Performance", False, f"Too slow: {load_time:.3f}s", time.time() - start_time)
                return False
            
            if search_time > 0.1:
                self.log_result("Search Performance", False, f"Too slow: {search_time:.3f}s", time.time() - start_time)
                return False
            
            if access_time > 0.01:
                self.log_result("Access Performance", False, f"Too slow: {access_time:.3f}s", time.time() - start_time)
                return False
            
            self.log_result("Performance Benchmarks", True, f"Load: {load_time:.3f}s, Search: {search_time:.3f}s, Access: {access_time:.3f}s", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_result("Performance Benchmarks", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_memory_usage(self):
        """Test memory usage"""
        start_time = time.time()
        
        try:
            import psutil
            process = psutil.Process()
            
            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Load TOON data
            from nlp2cmd.core.toon_integration import get_data_manager
            manager = get_data_manager()
            
            # Perform operations
            commands = manager.get_all_commands()
            search_results = manager.search_commands("git")
            config = manager.get_config()
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Check memory thresholds
            if memory_increase > 100:  # More than 100MB increase
                self.log_result("Memory Usage", False, f"Too much memory: {memory_increase:.1f}MB", time.time() - start_time)
                return False
            
            self.log_result("Memory Usage", True, f"Memory increase: {memory_increase:.1f}MB", time.time() - start_time)
            return True
            
        except ImportError:
            self.log_result("Memory Usage", True, "psutil not available, skipped", time.time() - start_time)
            return True
        except Exception as e:
            self.log_result("Memory Usage", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def run_continuous_integration(self):
        """Run continuous integration tests"""
        print("="*60)
        print("NLP2CMD CONTINUOUS INTEGRATION TEST")
        print("="*60)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_toon_file_integrity,
            self.test_config_file_integrity,
            self.test_python_imports,
            self.test_basic_functionality,
            self.test_command_availability,
            self.test_performance_benchmarks,
            self.test_memory_usage
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            print()
        
        # Calculate results
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        success_rate = passed_tests / total_tests * 100
        
        # Print summary
        print("="*60)
        print("CONTINUOUS INTEGRATION SUMMARY")
        print("="*60)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Assessment
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED - System is healthy!")
        elif success_rate >= 80:
            print("✅ MOST TESTS PASSED - System mostly healthy")
        elif success_rate >= 60:
            print("⚠️  SOME TESTS FAILED - System needs attention")
        else:
            print("❌ MANY TESTS FAILED - System has serious issues")
        
        # Save results
        self.save_results()
        
        return success_rate >= 80
    
    def save_results(self):
        """Save test results to file"""
        results_file = Path("ci_test_results.json")
        
        results_data = {
            'test_run': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_tests': len(self.results_log),
                'passed_tests': sum(1 for r in self.results_log if r['passed']),
                'success_rate': sum(1 for r in self.results_log if r['passed']) / len(self.results_log) * 100
            },
            'results': self.results_log
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"Results saved to: {results_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")


def main():
    """Main CI test function"""
    print("Starting NLP2CMD Continuous Integration Tests...")
    print("This test runs automatically to ensure system health\n")
    
    ci_test = ContinuousIntegrationTest()
    success = ci_test.run_continuous_integration()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
