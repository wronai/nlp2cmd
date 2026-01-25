"""
Automated Monitoring Test for NLP2CMD with TOON
Periodic test to ensure system continues working over time
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class AutomatedMonitoringTest:
    """Automated monitoring for NLP2CMD with TOON"""
    
    def __init__(self):
        self.results_log = []
        self.start_time = datetime.now()
        self.log_file = Path("nlp2cmd_monitoring_log.json")
        
    def log_result(self, test_name, passed, details="", duration=0.0, metrics=None):
        """Log test result with metrics"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'metrics': metrics or {}
        }
        self.results_log.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details} ({duration:.3f}s)")
        
        if metrics:
            for key, value in metrics.items():
                print(f"    📊 {key}: {value}")
    
    def test_system_health(self):
        """Test overall system health"""
        start_time = time.time()
        
        try:
            # Test basic imports
            from nlp2cmd.core import NLP2CMD, TransformResult
            import_success = True
        except ImportError as e:
            import_success = False
            self.log_result("System Health - Imports", False, f"Import error: {e}", time.time() - start_time)
            return False
        
        # Test TOON file
        toon_file = Path("project.unified.toon")
        toon_exists = toon_file.exists()
        
        # Test config file
        config_file = Path("config.yaml")
        config_exists = config_file.exists()
        
        metrics = {
            'nlp2cmd_import': import_success,
            'toon_file_exists': toon_exists,
            'config_file_exists': config_exists
        }
        
        all_good = import_success and toon_exists and config_exists
        
        self.log_result("System Health", all_good, "Core components available", time.time() - start_time, metrics)
        return all_good
    
    def test_command_processing(self):
        """Test command processing speed and accuracy"""
        start_time = time.time()
        
        test_commands = [
            "list files",
            "show git status", 
            "find python files",
            "show processes"
        ]
        
        results = []
        total_time = 0
        
        for cmd in test_commands:
            cmd_start = time.time()
            try:
                # Run command using subprocess
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "nlp2cmd.cli.main", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=Path(__file__).parent
                )
                cmd_time = time.time() - cmd_start
                total_time += cmd_time
                
                success = result.returncode == 0
                results.append({
                    'command': cmd,
                    'success': success,
                    'time': cmd_time
                })
                
            except Exception as e:
                cmd_time = time.time() - cmd_start
                total_time += cmd_time
                results.append({
                    'command': cmd,
                    'success': False,
                    'time': cmd_time,
                    'error': str(e)
                })
        
        passed_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        avg_time = total_time / total_count if total_count > 0 else 0
        
        metrics = {
            'commands_tested': total_count,
            'commands_passed': passed_count,
            'success_rate': passed_count / total_count * 100,
            'avg_time': avg_time,
            'total_time': total_time
        }
        
        success = passed_count >= total_count * 0.8  # 80% success rate
        
        self.log_result("Command Processing", success, f"{passed_count}/{total_count} commands", time.time() - start_time, metrics)
        return success
    
    def test_performance_regression(self):
        """Test for performance regression"""
        start_time = time.time()
        
        # Test quick commands multiple times
        quick_commands = ["ls", "pwd", "date"]
        times = []
        
        for cmd in quick_commands:
            for i in range(3):  # 3 times each
                cmd_start = time.time()
                try:
                    import subprocess
                    result = subprocess.run(
                        [sys.executable, "-m", "nlp2cmd.cli.main", cmd],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=Path(__file__).parent
                    )
                    cmd_time = time.time() - cmd_start
                    times.append(cmd_time)
                except Exception:
                    times.append(5.0)  # Max time on error
        
        avg_time = sum(times) / len(times) if times else 0
        max_time = max(times) if times else 0
        
        # Performance thresholds
        avg_threshold = 2.0  # 2 seconds average
        max_threshold = 5.0  # 5 seconds max
        
        metrics = {
            'samples': len(times),
            'avg_time': avg_time,
            'max_time': max_time,
            'avg_threshold': avg_threshold,
            'max_threshold': max_threshold
        }
        
        success = avg_time < avg_threshold and max_time < max_threshold
        
        self.log_result("Performance Regression", success, f"Avg: {avg_time:.2f}s, Max: {max_time:.2f}s", time.time() - start_time, metrics)
        return success
    
    def test_toon_data_integrity(self):
        """Test TOON data integrity"""
        start_time = time.time()
        
        try:
            toon_file = Path("project.unified.toon")
            if not toon_file.exists():
                self.log_result("TOON Data Integrity", False, "TOON file not found", time.time() - start_time)
                return False
            
            with open(toon_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic checks
            size = len(content)
            bracket_balance = content.count('[') + content.count('{') == content.count(']') + content.count('}')
            
            # Check for key sections
            has_commands = 'commands[' in content
            has_config = 'config[' in content
            has_metadata = 'metadata[' in content
            
            metrics = {
                'file_size': size,
                'bracket_balance': bracket_balance,
                'has_commands': has_commands,
                'has_config': has_config,
                'has_metadata': has_metadata
            }
            
            success = bracket_balance and has_commands and has_config and has_metadata
            
            self.log_result("TOON Data Integrity", success, f"Size: {size} chars", time.time() - start_time, metrics)
            return success
            
        except Exception as e:
            self.log_result("TOON Data Integrity", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def test_memory_usage(self):
        """Test memory usage"""
        start_time = time.time()
        
        try:
            import psutil
            process = psutil.Process()
            
            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run some commands
            test_commands = ["list files", "git status", "find python files"]
            for cmd in test_commands:
                try:
                    import subprocess
                    subprocess.run(
                        [sys.executable, "-m", "nlp2cmd.cli.main", cmd],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=Path(__file__).parent
                    )
                except:
                    pass
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            metrics = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase
            }
            
            # Check if memory usage is reasonable (< 100MB increase)
            success = memory_increase < 100
            
            self.log_result("Memory Usage", success, f"Increase: {memory_increase:.1f}MB", time.time() - start_time, metrics)
            return success
            
        except ImportError:
            self.log_result("Memory Usage", True, "psutil not available, skipped", time.time() - start_time)
            return True
        except Exception as e:
            self.log_result("Memory Usage", False, f"Error: {str(e)}", time.time() - start_time)
            return False
    
    def load_historical_data(self):
        """Load historical monitoring data"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            return data.get('monitoring_sessions', [])
        except:
            return []
    
    def save_results(self):
        """Save monitoring results"""
        historical_data = self.load_historical_data()
        
        session_data = {
            'timestamp': self.start_time.isoformat(),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'results': self.results_log,
            'summary': {
                'total_tests': len(self.results_log),
                'passed_tests': sum(1 for r in self.results_log if r['passed']),
                'success_rate': sum(1 for r in self.results_log if r['passed']) / len(self.results_log) * 100 if self.results_log else 0
            }
        }
        
        historical_data.append(session_data)
        
        # Keep only last 30 days of data
        cutoff_date = datetime.now() - timedelta(days=30)
        historical_data = [s for s in historical_data if datetime.fromisoformat(s['timestamp']) > cutoff_date]
        
        save_data = {
            'monitoring_sessions': historical_data,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.log_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            print(f"Monitoring results saved to: {self.log_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")
    
    def analyze_trends(self):
        """Analyze trends from historical data"""
        historical_data = self.load_historical_data()
        
        if len(historical_data) < 2:
            print("📈 Trend Analysis: Insufficient data (need at least 2 sessions)")
            return
        
        recent_sessions = historical_data[-10:]  # Last 10 sessions
        success_rates = [s['summary']['success_rate'] for s in recent_sessions]
        
        if len(success_rates) >= 2:
            recent_avg = sum(success_rates[-3:]) / min(3, len(success_rates))
            older_avg = sum(success_rates[:-3]) / max(1, len(success_rates) - 3) if len(success_rates) > 3 else recent_avg
            
            trend = "📈 Improving" if recent_avg > older_avg else "📉 Declining" if recent_avg < older_avg else "➡️ Stable"
            
            print(f"📈 Trend Analysis: {trend}")
            print(f"    Recent success rate: {recent_avg:.1f}%")
            print(f"    Previous success rate: {older_avg:.1f}%")
    
    def run_automated_monitoring(self):
        """Run automated monitoring tests"""
        print("="*60)
        print("NLP2CMD AUTOMATED MONITORING")
        print("="*60)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all monitoring tests
        tests = [
            self.test_system_health,
            self.test_command_processing,
            self.test_performance_regression,
            self.test_toon_data_integrity,
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
        print("MONITORING SUMMARY")
        print("="*60)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Trend analysis
        self.analyze_trends()
        
        # Assessment
        if success_rate == 100:
            print("🎉 EXCELLENT: All systems healthy!")
        elif success_rate >= 80:
            print("✅ GOOD: Systems mostly healthy")
        elif success_rate >= 60:
            print("⚠️  FAIR: Some issues detected")
        else:
            print("❌ POOR: Significant issues detected")
        
        # Save results
        self.save_results()
        
        return success_rate >= 80
    
    def generate_report(self):
        """Generate monitoring report"""
        historical_data = self.load_historical_data()
        
        if not historical_data:
            print("No historical data available for report")
            return
        
        print("\n" + "="*60)
        print("MONITORING REPORT (Last 30 Days)")
        print("="*60)
        
        # Calculate statistics
        total_sessions = len(historical_data)
        success_rates = [s['summary']['success_rate'] for s in historical_data]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Find best and worst sessions
        best_session = max(historical_data, key=lambda s: s['summary']['success_rate'])
        worst_session = min(historical_data, key=lambda s: s['summary']['success_rate'])
        
        print(f"Total Sessions: {total_sessions}")
        print(f"Average Success Rate: {avg_success_rate:.1f}%")
        print(f"Best Session: {best_session['timestamp']} ({best_session['summary']['success_rate']:.1f}%)")
        print(f"Worst Session: {worst_session['timestamp']} ({worst_session['summary']['success_rate']:.1f}%)")
        
        # Recent performance
        recent_sessions = historical_data[-7:]  # Last 7 sessions
        recent_avg = sum(s['summary']['success_rate'] for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0
        
        print(f"Recent Average (7 sessions): {recent_avg:.1f}%")
        
        # Recommendations
        print("\nRecommendations:")
        if avg_success_rate >= 90:
            print("• System performance is excellent")
            print("• Continue regular monitoring")
        elif avg_success_rate >= 80:
            print("• System performance is good")
            print("• Monitor any declining trends")
        else:
            print("• System performance needs attention")
            print("• Investigate and fix failing tests")


def main():
    """Main monitoring function"""
    print("Starting NLP2CMD Automated Monitoring...")
    print("This test runs periodically to ensure system health\n")
    
    monitor = AutomatedMonitoringTest()
    success = monitor.run_automated_monitoring()
    
    # Generate report
    monitor.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
