#!/usr/bin/env python3
"""
Test Polish Language Integration
Tests the Polish language support after integration
"""

import subprocess
import sys
import time
from pathlib import Path

class PolishIntegrationTester:
    """Test Polish language integration"""
    
    def __init__(self):
        self.test_results = []
        
    def run_command_test(self, command_input):
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
            
            return {
                'input': command_input,
                'success': success,
                'execution_time': execution_time,
                'generated_command': generated_command,
                'detected_domain': detected_domain,
                'detected_intent': detected_intent
            }
            
        except Exception as e:
            return {
                'input': command_input,
                'success': False,
                'execution_time': 0,
                'error': str(e),
                'detected_domain': 'unknown',
                'detected_intent': 'unknown'
            }
    
    def test_polish_file_operations(self):
        """Test Polish file operations"""
        print("🔧 Testing Polish File Operations")
        print("-" * 50)
        
        test_cases = [
            "pokaż pliki",
            "lista plików w folderze", 
            "znajdź pliki .log",
            "usuń plik stary.txt",
            "utwórz katalog nowy",
            "zmień nazwę pliku",
            "kopiuj plik"
        ]
        
        results = []
        passed = 0
        
        for command_input in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input)
            results.append(result)
            
            # Check if Polish support is working
            if result['success'] and result['detected_domain'] != 'unknown':
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - {result['detected_domain']}/{result['detected_intent']}")
                if 'error' in result:
                    print(f"    Error: {result['error']}")
        
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
            "pokaż procesy",
            "zabij proces 1234",
            "uruchom usługę nginx",
            "zatrzymaj usługę nginx",
            "restartuj usługę nginx",
            "monitor systemowy",
            "sprawdź użycie CPU"
        ]
        
        results = []
        passed = 0
        
        for command_input in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input)
            results.append(result)
            
            if result['success'] and result['detected_domain'] != 'unknown':
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - {result['detected_domain']}/{result['detected_intent']}")
        
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
            "pokaż użytkowników",
            "znajdź użytkowników z Warszawy",
            "dodaj nowego użytkownika",
            "zaktualizuj email użytkownika",
            "usuń stare rekordy",
            "policz użytkowników",
            "grupuj użytkowników po mieście"
        ]
        
        results = []
        passed = 0
        
        for command_input in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input)
            results.append(result)
            
            if result['success'] and result['detected_domain'] != 'unknown':
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - {result['detected_domain']}/{result['detected_intent']}")
        
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
    
    def test_basic_functionality(self):
        """Test basic functionality still works"""
        print("\n🔧 Testing Basic Functionality")
        print("-" * 50)
        
        test_cases = [
            "ls",
            "pwd",
            "date",
            "whoami"
        ]
        
        results = []
        passed = 0
        
        for command_input in test_cases:
            print(f"Testing: {command_input}")
            result = self.run_command_test(command_input)
            results.append(result)
            
            if result['success']:
                passed += 1
                print(f"  ✅ PASS - {result['detected_domain']}/{result['detected_intent']}")
            else:
                print(f"  ❌ FAIL - {result['detected_domain']}/{result['detected_intent']}")
        
        success_rate = (passed / len(test_cases)) * 100
        print(f"\nBasic Functionality: {passed}/{len(test_cases)} ({success_rate:.1f}%)")
        
        self.test_results.append({
            'category': 'Basic Functionality',
            'passed': passed,
            'total': len(test_cases),
            'success_rate': success_rate,
            'results': results
        })
        
        return success_rate
    
    def run_polish_integration_tests(self):
        """Run all Polish integration tests"""
        print("🚀 TESTING POLISH LANGUAGE INTEGRATION")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        test_results = {
            'polish_file_ops': self.test_polish_file_operations(),
            'polish_process_ops': self.test_polish_process_operations(),
            'polish_sql_ops': self.test_polish_sql_operations(),
            'basic_functionality': self.test_basic_functionality()
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
        print("🎯 POLISH INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Total Tests: {sum(r['total'] for r in self.test_results)}")
        print(f"Passed: {sum(r['passed'] for r in self.test_results)}")
        print(f"Failed: {sum(r['total'] for r in self.test_results) - sum(r['passed'] for r in self.test_results)}")
        print(f"Duration: {total_time:.2f}s")
        print()
        
        print("Results by Category:")
        for result in self.test_results:
            status = "✅" if result['success_rate'] >= 50 else "⚠️" if result['success_rate'] >= 25 else "❌"
            print(f"  {status} {result['category']}: {result['passed']}/{result['total']} ({result['success_rate']:.1f}%)")
        
        print("\n📈 Integration Assessment:")
        if overall_success_rate >= 70:
            print("🌉 EXCELLENT: Polish integration successful!")
            print("   Polish language support is working effectively")
        elif overall_success_rate >= 50:
            print("✅ GOOD: Polish integration partially working!")
            print("   Some Polish commands working, room for improvement")
        elif overall_success_rate >= 25:
            print("⚠️  FAIR: Polish integration shows some progress")
            print("   Integration partially successful, needs more work")
        else:
            print("❌ POOR: Polish integration needs significant work")
            print("   Integration issues need to be resolved")
        
        print("\n🔧 Integration Status:")
        polish_working = any(r['category'].startswith('Polish') and r['success_rate'] > 0 for r in self.test_results)
        basic_working = any(r['category'] == 'Basic Functionality' and r['success_rate'] >= 75 for r in self.test_results)
        
        print(f"  Polish Support: {'✅ Working' if polish_working else '❌ Not Working'}")
        print(f"  Basic Functionality: {'✅ Working' if basic_working else '❌ Broken'}")
        
        if polish_working and basic_working:
            print("\n🎉 Integration Status: SUCCESS")
            print("Polish language support has been successfully integrated!")
        elif basic_working:
            print("\n⚠️  Integration Status: PARTIAL")
            print("Basic functionality preserved, Polish support needs work")
        else:
            print("\n❌ Integration Status: FAILED")
            print("Integration has broken basic functionality")

def main():
    """Main test function"""
    print("🚀 Testing Polish Language Integration")
    print("This test validates the Polish language support integration\n")
    
    tester = PolishIntegrationTester()
    success_rate = tester.run_polish_integration_tests()
    
    if success_rate >= 50:
        print("\n🎉 Polish integration test completed successfully!")
        print("Polish language support is working.")
    else:
        print("\n⚠️  Polish integration test shows issues.")
        print("Further work needed on Polish language support.")

if __name__ == "__main__":
    main()
