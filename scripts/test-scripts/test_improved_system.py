"""
Test Improved System
Tests the NLP2CMD system after applying high priority fixes
"""

import subprocess
import sys
import time
from pathlib import Path

class ImprovedSystemTester:
    """Test the improved NLP2CMD system"""
    
    def __init__(self):
        self.test_results = []
        
    def run_command_test(self, command_input, expected_domain=None, expected_intent=None):
        """Run a single command test"""
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, "-m", "nlp2cmd.cli.main", command_input],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).parent
            )
            execution_time = time.time() - start_time
            
            # Parse output
            output = result.stdout
            lines = output.strip().split('\n')
            
            generated_command = ""
            detected_domain = "unknown"
            detected_intent = "unknown"
            
            # Extract command
            for line in lines:
                if line.strip() and not line.startswith("📊") and not line.startswith("🤖"):
                    generated_command = line.strip()
                    break
            
            # Extract domain and intent
            for line in lines:
                if "Domain:" in line:
                    detected_domain = line.split("Domain:")[1].strip()
                elif "Intent:" in line:
                    detected_intent = line.split("Intent:")[1].strip()
            
            success = result.returncode == 0
            
            # Check expectations
            domain_match = expected_domain is None or detected_domain == expected_domain
            intent_match = expected_intent is None or detected_intent == expected_intent
            
            test_result = {
                'input': command_input,
                'success': success,
                'execution_time': execution_time,
                'generated_command': generated_command,
                'detected_domain': detected_domain,
                'detected_intent': detected_intent,
                'expected_domain': expected_domain,
                'expected_intent': expected_intent,
                'domain_match': domain_match,
                'intent_match': intent_match,
                'overall_match': domain_match and intent_match
            }
            
            return test_result
            
        except Exception as e:
            return {
                'input': command_input,
                'success': False,
                'execution_time': 0,
                'error': str(e),
                'overall_match': False
            }
    
    def test_polish_file_operations(self):
        """Test Polish file operations that were failing before"""
        print("🔧 Testing Polish File Operations")
        print("-" * 50)
        
        test_cases = [
            ("pokaż pliki", "shell", "list"),
            ("lista plików w folderze", "shell", "list"),
            ("znajdź pliki .log", "shell", "find"),
            ("usuń plik stary.txt", "shell", "delete"),
            ("utwórz katalog nowy", "shell", "create"),
            ("zmień nazwę pliku", "shell", "rename"),
            ("kopiuj plik", "shell", "copy")
        ]
        
        results = []
        passed = 0
        
        for command_input, expected_domain, expected_intent in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input, expected_domain, expected_intent)
            results.append(result)
            
            if result['overall_match']:
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - Expected: {expected_domain}/{expected_intent}")
                print(f"         Got: {result['detected_domain']}/{result['detected_intent']}")
        
        success_rate = (passed / len(test_cases)) * 100
        print(f"\nPolish File Operations: {passed}/{len(test_cases)} ({success_rate:.1f}%)")
        
        self.test_results.append({
            'category': 'Polish File Operations',
            'passed': passed,
            'total': len(test_cases),
            'success_rate': success_rate,
            'results': results
        })
        
        return success_rate
    
    def test_polish_process_operations(self):
        """Test Polish process operations"""
        print("\n🔧 Testing Polish Process Operations")
        print("-" * 50)
        
        test_cases = [
            ("pokaż procesy", "shell", "list_processes"),
            ("zabij proces 1234", "shell", "process_kill"),
            ("uruchom usługę nginx", "shell", "service_start"),
            ("zatrzymaj usługę nginx", "shell", "service_stop"),
            ("restartuj usługę nginx", "shell", "service_restart"),
            ("monitor systemowy", "shell", "process"),
            ("sprawdź użycie CPU", "shell", "process")
        ]
        
        results = []
        passed = 0
        
        for command_input, expected_domain, expected_intent in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input, expected_domain, expected_intent)
            results.append(result)
            
            if result['overall_match']:
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - Expected: {expected_domain}/{expected_intent}")
                print(f"         Got: {result['detected_domain']}/{result['detected_intent']}")
        
        success_rate = (passed / len(test_cases)) * 100
        print(f"\nPolish Process Operations: {passed}/{len(test_cases)} ({success_rate:.1f}%)")
        
        self.test_results.append({
            'category': 'Polish Process Operations',
            'passed': passed,
            'total': len(test_cases),
            'success_rate': success_rate,
            'results': results
        })
        
        return success_rate
    
    def test_polish_sql_operations(self):
        """Test Polish SQL operations"""
        print("\n🔧 Testing Polish SQL Operations")
        print("-" * 50)
        
        test_cases = [
            ("pokaż użytkowników", "sql", "show"),
            ("znajdź użytkowników z Warszawy", "sql", "select"),
            ("dodaj nowego użytkownika", "sql", "insert"),
            ("zaktualizuj email użytkownika", "sql", "update"),
            ("usuń stare rekordy", "sql", "delete"),
            ("policz użytkowników", "sql", "aggregate"),
            ("grupuj użytkowników po mieście", "sql", "aggregate")
        ]
        
        results = []
        passed = 0
        
        for command_input, expected_domain, expected_intent in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input, expected_domain, expected_intent)
            results.append(result)
            
            if result['overall_match']:
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - Expected: {expected_domain}/{expected_intent}")
                print(f"         Got: {result['detected_domain']}/{result['detected_intent']}")
        
        success_rate = (passed / len(test_cases)) * 100
        print(f"\nPolish SQL Operations: {passed}/{len(test_cases)} ({success_rate:.1f}%)")
        
        self.test_results.append({
            'category': 'Polish SQL Operations',
            'passed': passed,
            'total': len(test_cases),
            'success_rate': success_rate,
            'results': results
        })
        
        return success_rate
    
    def test_docker_operations(self):
        """Test Docker operations"""
        print("\n🔧 Testing Docker Operations")
        print("-" * 50)
        
        test_cases = [
            ("docker ps", "docker", "list"),
            ("pokaż wszystkie kontenery", "docker", "list_all"),
            ("docker uruchom nginx", "docker", "run"),
            ("docker zatrzymaj nginx", "docker", "stop"),
            ("docker start nginx", "docker", "start"),
            ("docker logs nginx", "docker", "logs"),
            ("docker compose up", "docker", "compose")
        ]
        
        results = []
        passed = 0
        
        for command_input, expected_domain, expected_intent in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input, expected_domain, expected_intent)
            results.append(result)
            
            if result['overall_match']:
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - Expected: {expected_domain}/{expected_intent}")
                print(f"         Got: {result['detected_domain']}/{result['detected_intent']}")
        
        success_rate = (passed / len(test_cases)) * 100
        print(f"\nDocker Operations: {passed}/{len(test_cases)} ({success_rate:.1f}%)")
        
        self.test_results.append({
            'category': 'Docker Operations',
            'passed': passed,
            'total': len(test_cases),
            'success_rate': success_rate,
            'results': results
        })
        
        return success_rate
    
    def test_performance(self):
        """Test system performance"""
        print("\n🔧 Testing System Performance")
        print("-" * 50)
        
        quick_commands = ["ls", "pwd", "date", "whoami"]
        times = []
        
        for cmd in quick_commands:
            print(f"Testing: {cmd}")
            result = self.run_command_test(cmd)
            times.append(result['execution_time'])
            print(f"  ⏱️  {result['execution_time']:.3f}s")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        performance_good = avg_time < 2.0 and max_time < 5.0
        
        print(f"\nPerformance Results:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Status: {'✅ Good' if performance_good else '❌ Needs improvement'}")
        
        self.test_results.append({
            'category': 'Performance',
            'passed': 1 if performance_good else 0,
            'total': 1,
            'success_rate': 100 if performance_good else 0,
            'avg_time': avg_time,
            'max_time': max_time
        })
        
        return 100 if performance_good else 0
    
    def run_improved_tests(self):
        """Run all improved system tests"""
        print("🚀 TESTING IMPROVED NLP2CMD SYSTEM")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        test_results = {
            'polish_file_ops': self.test_polish_file_operations(),
            'polish_process_ops': self.test_polish_process_operations(),
            'polish_sql_ops': self.test_polish_sql_operations(),
            'docker_ops': self.test_docker_operations(),
            'performance': self.test_performance()
        }
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate overall results
        total_passed = sum(r['passed'] for r in self.test_results)
        total_tests = sum(r['total'] for r in self.test_results)
        overall_success_rate = (total_passed / total_tests) * 100
        
        # Generate summary
        self.generate_summary(test_results, overall_success_rate, total_time)
        
        return overall_success_rate
    
    def generate_summary(self, test_results, overall_success_rate, total_time):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("🎯 IMPROVED SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Total Tests: {sum(r['total'] for r in self.test_results)}")
        print(f"Passed: {sum(r['passed'] for r in self.test_results)}")
        print(f"Failed: {sum(r['total'] for r in self.test_results) - sum(r['passed'] for r in self.test_results)}")
        print(f"Duration: {total_time:.2f}s")
        print()
        
        print("Results by Category:")
        for result in self.test_results:
            status = "✅" if result['success_rate'] >= 70 else "⚠️" if result['success_rate'] >= 50 else "❌"
            print(f"  {status} {result['category']}: {result['passed']}/{result['total']} ({result['success_rate']:.1f}%)")
        
        print("\n📈 Comparison with Original Results:")
        print("  Original: 49/101 (48.5%)")
        print(f"  Improved: {sum(r['passed'] for r in self.test_results)}/{sum(r['total'] for r in self.test_results)} ({overall_success_rate:.1f}%)")
        improvement = overall_success_rate - 48.5
        print(f"  Improvement: +{improvement:.1f}%")
        
        print("\n🎯 Assessment:")
        if overall_success_rate >= 80:
            print("🌉 EXCELLENT: System meets production standards!")
            print("   All critical fixes working effectively")
        elif overall_success_rate >= 70:
            print("✅ GOOD: System significantly improved!")
            print("   Most fixes working, minor tuning needed")
        elif overall_success_rate >= 60:
            print("⚠️  FAIR: System shows improvement")
            print("   Some fixes working, more work needed")
        else:
            print("❌ POOR: System needs more work")
            print("   Fixes not effective enough")
        
        print("\n🔧 Fix Effectiveness:")
        for category, rate in test_results.items():
            if rate >= 70:
                print(f"  ✅ {category}: Highly effective")
            elif rate >= 50:
                print(f"  ⚠️  {category}: Moderately effective")
            else:
                print(f"  ❌ {category}: Needs improvement")

def main():
    """Main test function"""
    print("🚀 Testing Improved NLP2CMD System")
    print("This test validates the effectiveness of applied fixes\n")
    
    tester = ImprovedSystemTester()
    success_rate = tester.run_improved_tests()
    
    if success_rate >= 70:
        print("\n🎉 System improvement successful!")
        print("Ready for production deployment.")
    else:
        print("\n⚠️  System needs more work.")
        print("Continue refining the fixes.")

if __name__ == "__main__":
    main()
