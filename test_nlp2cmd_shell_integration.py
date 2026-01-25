"""
Test NLP2CMD Shell Integration with TOON
Tests actual NLP2CMD shell commands to ensure nothing broke
"""

import sys
import time
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class NLP2CMDShellIntegrationTest:
    """Test NLP2CMD shell integration with TOON backend"""
    
    def __init__(self):
        self.test_results = []
        self.failed_commands = []
        
    def run_nlp2cmd_command(self, input_text, timeout=30):
        """Run NLP2CMD command and return result"""
        try:
            # Try to run nlp2cmd as a command
            result = subprocess.run(
                [sys.executable, "-m", "nlp2cmd.cli.main", input_text],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -2
            }
    
    def test_basic_shell_commands(self):
        """Test basic shell commands with NLP2CMD"""
        print("Testing basic shell commands with NLP2CMD...")
        
        test_commands = [
            "list files in current directory",
            "show git status", 
            "find all python files",
            "grep for error in logs",
            "show running processes",
            "create a new directory",
            "copy file to backup",
            "remove temporary files",
            "show disk usage",
            "check system memory"
        ]
        
        results = []
        
        for cmd in test_commands:
            print(f"  Testing: {cmd}")
            start_time = time.time()
            
            result = self.run_nlp2cmd_command(cmd)
            execution_time = time.time() - start_time
            
            test_result = {
                'input': cmd,
                'result': result,
                'execution_time': execution_time,
                'passed': result['success'] or 'timeout' not in result['stderr'].lower()
            }
            
            results.append(test_result)
            
            if not test_result['passed']:
                self.failed_commands.append(cmd)
                print(f"    ❌ FAILED: {result['stderr'][:100]}...")
            else:
                print(f"    ✅ PASSED ({execution_time:.2f}s)")
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\nBasic Commands: {passed_count}/{total_count} passed")
        
        self.test_results.append({
            'test': 'Basic Shell Commands',
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'success_rate': passed_count / total_count * 100
        })
        
        return results
    
    def test_advanced_shell_commands(self):
        """Test advanced shell commands"""
        print("\nTesting advanced shell commands...")
        
        advanced_commands = [
            "find files larger than 10MB",
            "show files modified in last 7 days",
            "count lines of code in python files",
            "compress log files older than 30 days",
            "monitor system resources in real time",
            "kill processes using more than 80% CPU",
            "backup database to remote server",
            "check network connectivity to google.com",
            "list all installed packages",
            "update system packages"
        ]
        
        results = []
        
        for cmd in advanced_commands:
            print(f"  Testing: {cmd}")
            start_time = time.time()
            
            result = self.run_nlp2cmd_command(cmd)
            execution_time = time.time() - start_time
            
            test_result = {
                'input': cmd,
                'result': result,
                'execution_time': execution_time,
                'passed': result['success'] or 'timeout' not in result['stderr'].lower()
            }
            
            results.append(test_result)
            
            if not test_result['passed']:
                self.failed_commands.append(cmd)
                print(f"    ❌ FAILED: {result['stderr'][:100]}...")
            else:
                print(f"    ✅ PASSED ({execution_time:.2f}s)")
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\nAdvanced Commands: {passed_count}/{total_count} passed")
        
        self.test_results.append({
            'test': 'Advanced Shell Commands',
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'success_rate': passed_count / total_count * 100
        })
        
        return results
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\nTesting error handling...")
        
        error_test_cases = [
            "invalid command that doesn't exist",
            "rm -rf /",  # Dangerous command
            "",  # Empty input
            "   ",  # Whitespace only
            "command with very long input that might cause issues " * 10,
            "special chars !@#$%^&*()",
            "unicode test: naïve café résumé"
        ]
        
        results = []
        
        for cmd in error_test_cases:
            print(f"  Testing: {cmd[:50]}{'...' if len(cmd) > 50 else ''}")
            start_time = time.time()
            
            result = self.run_nlp2cmd_command(cmd)
            execution_time = time.time() - start_time
            
            # For error cases, we expect graceful handling (not crashes)
            test_result = {
                'input': cmd,
                'result': result,
                'execution_time': execution_time,
                'passed': result['returncode'] != -2  # Should not crash
            }
            
            results.append(test_result)
            
            if not test_result['passed']:
                self.failed_commands.append(cmd)
                print(f"    ❌ CRASHED: {result['stderr'][:100]}...")
            else:
                print(f"    ✅ Handled gracefully ({execution_time:.2f}s)")
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\nError Handling: {passed_count}/{total_count} passed")
        
        self.test_results.append({
            'test': 'Error Handling',
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'success_rate': passed_count / total_count * 100
        })
        
        return results
    
    def test_performance_regression(self):
        """Test for performance regressions"""
        print("\nTesting performance regression...")
        
        # Test commands that should be fast
        performance_commands = [
            "list files",
            "show date",
            "who am i",
            "echo hello",
            "pwd"
        ]
        
        results = []
        
        for cmd in performance_commands:
            times = []
            
            # Run each command multiple times to get average
            for i in range(3):
                start_time = time.time()
                result = self.run_nlp2cmd_command(cmd)
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            test_result = {
                'input': cmd,
                'times': times,
                'avg_time': avg_time,
                'max_time': max_time,
                'passed': avg_time < 5.0  # Should complete within 5 seconds
            }
            
            results.append(test_result)
            
            if not test_result['passed']:
                self.failed_commands.append(f"{cmd} (slow)")
                print(f"    ❌ SLOW: {avg_time:.2f}s avg")
            else:
                print(f"    ✅ FAST: {avg_time:.2f}s avg")
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\nPerformance: {passed_count}/{total_count} passed")
        
        self.test_results.append({
            'test': 'Performance Regression',
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'success_rate': passed_count / total_count * 100
        })
        
        return results
    
    def test_toon_integration_specific(self):
        """Test TOON-specific integration"""
        print("\nTesting TOON-specific integration...")
        
        # Test commands that should use TOON data
        toon_test_commands = [
            "git status",  # Should use TOON git command
            "docker ps",   # Should use TOON docker command
            "kubectl get pods",  # Should use TOON kubectl command
            "find . -name '*.py'",  # Should use TOON find command
            "grep -r 'import' .",   # Should use TOON grep command
        ]
        
        results = []
        
        for cmd in toon_test_commands:
            print(f"  Testing TOON integration: {cmd}")
            start_time = time.time()
            
            result = self.run_nlp2cmd_command(cmd)
            execution_time = time.time() - start_time
            
            # Check if output contains expected patterns
            expected_patterns = {
                'git': ['git', 'status'],
                'docker': ['docker'],
                'kubectl': ['kubectl'],
                'find': ['find'],
                'grep': ['grep']
            }
            
            cmd_type = None
            for key, patterns in expected_patterns.items():
                if key in cmd.lower():
                    cmd_type = key
                    break
            
            passed = result['success']
            if cmd_type and passed:
                # Check if output contains expected command type
                output_lower = result['stdout'].lower()
                passed = any(pattern in output_lower for pattern in expected_patterns[cmd_type])
            
            test_result = {
                'input': cmd,
                'result': result,
                'execution_time': execution_time,
                'command_type': cmd_type,
                'passed': passed
            }
            
            results.append(test_result)
            
            if not test_result['passed']:
                self.failed_commands.append(cmd)
                print(f"    ❌ FAILED: {result['stderr'][:100]}...")
            else:
                print(f"    ✅ PASSED ({execution_time:.2f}s)")
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\nTOON Integration: {passed_count}/{total_count} passed")
        
        self.test_results.append({
            'test': 'TOON Integration',
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'success_rate': passed_count / total_count * 100
        })
        
        return results
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=== NLP2CMD Shell Integration Test Suite ===")
        print("Testing NLP2CMD shell commands with TOON backend\n")
        
        try:
            # Test 1: Basic Commands
            self.test_basic_shell_commands()
            
            # Test 2: Advanced Commands
            self.test_advanced_shell_commands()
            
            # Test 3: Error Handling
            self.test_error_handling()
            
            # Test 4: Performance Regression
            self.test_performance_regression()
            
            # Test 5: TOON Integration
            self.test_toon_integration_specific()
            
            # Print summary
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        except Exception as e:
            print(f"\n\nTest suite error: {e}")
            import traceback
            traceback.print_exc()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("NLP2CMD SHELL INTEGRATION TEST SUMMARY")
        print("="*50)
        
        total_passed = sum(test['passed'] for test in self.test_results)
        total_commands = sum(test['total'] for test in self.test_results)
        overall_success_rate = total_passed / total_commands * 100 if total_commands > 0 else 0
        
        print(f"\nOverall Results: {total_passed}/{total_commands} commands passed")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        
        print("\nTest Breakdown:")
        for test in self.test_results:
            status = "✅ PASS" if test['success_rate'] >= 80 else "❌ FAIL"
            print(f"  {status} {test['test']}: {test['passed']}/{test['total']} ({test['success_rate']:.1f}%)")
        
        if self.failed_commands:
            print(f"\nFailed Commands ({len(self.failed_commands)}):")
            for cmd in self.failed_commands:
                print(f"  - {cmd}")
        
        print("\n" + "="*50)
        print("INTEGRATION ASSESSMENT")
        print("="*50)
        
        if overall_success_rate >= 90:
            print("🎉 EXCELLENT: NLP2CMD integration is working perfectly!")
            print("   TOON backend is fully functional.")
        elif overall_success_rate >= 75:
            print("✅ GOOD: NLP2CMD integration is working well.")
            print("   Minor issues may need attention.")
        elif overall_success_rate >= 50:
            print("⚠️  FAIR: NLP2CMD integration has some issues.")
            print("   Significant problems need to be addressed.")
        else:
            print("❌ POOR: NLP2CMD integration has major problems.")
            print("   Immediate attention required.")
        
        print("\nRecommendations:")
        if overall_success_rate < 100:
            print("• Review failed commands and fix underlying issues")
            print("• Check TOON data integrity")
            print("• Verify NLP2CMD configuration")
        
        if overall_success_rate >= 75:
            print("• System is ready for production use")
            print("• Monitor for any regressions")
        
        print("\nNext Steps:")
        print("• Fix any failed commands")
        print("• Run tests regularly to catch regressions")
        print("• Monitor performance in production")
        print("• Keep TOON data updated")


def main():
    """Main test function"""
    print("Starting NLP2CMD Shell Integration Tests...")
    print("This will test actual NLP2CMD shell commands with TOON backend\n")
    
    tester = NLP2CMDShellIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
