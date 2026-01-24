#!/usr/bin/env python3
"""
Comprehensive test suite for NLP2CMD with 100+ test commands.
Tests various domains, typos, word orders, and edge cases.
"""

import subprocess
import json
import time
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class TestCommand:
    """Test command with expected results."""
    query: str
    expected_domain: str
    expected_intent: str
    expected_command_pattern: str  # Partial match for command
    should_succeed: bool = True
    description: str = ""

class ComprehensiveCommandTester:
    """Test NLP2CMD with comprehensive command set."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
    
    def run_command(self, query: str) -> Dict[str, Any]:
        """Run nlp2cmd command and return result."""
        try:
            result = subprocess.run(
                ["nlp2cmd", "--query", query, "--explain"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/tom/github/wronai/nlp2cmd"
            )
            
            # Parse output to extract detected intent and command
            output = result.stdout
            lines = output.strip().split('\n')
            
            detected_domain = "unknown"
            detected_intent = "unknown"
            generated_command = ""
            confidence = 0.0
            
            # First non-empty line is the command
            for line in lines:
                if line.strip() and not line.startswith("📊"):
                    generated_command = line.strip()
                    break
            
            # Parse metadata lines
            for line in lines:
                if line.startswith("Domain:"):
                    detected_domain = line.split("Domain:")[1].strip()
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.split("Confidence:")[1].strip())
                    except:
                        confidence = 0.0
            
            # Extract intent from domain if possible (for shell, we need to infer from command)
            if detected_domain == "shell":
                if "ls" in generated_command:
                    detected_intent = "list"
                elif "find" in generated_command:
                    detected_intent = "find"
                elif "cp" in generated_command:
                    detected_intent = "copy"
                elif "rm" in generated_command:
                    detected_intent = "delete"
                elif "mkdir" in generated_command:
                    detected_intent = "create"
                elif "mv" in generated_command:
                    detected_intent = "rename"
                elif "ps" in generated_command:
                    detected_intent = "list_processes"
                elif "kill" in generated_command:
                    detected_intent = "process_kill"
                elif "top" in generated_command or "htop" in generated_command:
                    detected_intent = "process"
                elif "systemctl start" in generated_command:
                    detected_intent = "service_start"
                elif "systemctl stop" in generated_command:
                    detected_intent = "service_stop"
                elif "systemctl restart" in generated_command:
                    detected_intent = "service_restart"
                elif "systemctl status" in generated_command:
                    detected_intent = "service_status"
                elif "reboot" in generated_command:
                    detected_intent = "reboot"
                elif "df" in generated_command:
                    detected_intent = "disk"
                elif "free" in generated_command:
                    detected_intent = "disk"
                elif "ping" in generated_command:
                    detected_intent = "network_ping"
                elif "netstat" in generated_command:
                    detected_intent = "network_port"
                elif "ip addr" in generated_command:
                    detected_intent = "network_ip"
            elif detected_domain == "docker":
                if "docker ps" in generated_command and "-a" in generated_command:
                    detected_intent = "list_all"
                elif "docker ps" in generated_command:
                    detected_intent = "list"
                elif "docker images" in generated_command:
                    detected_intent = "images"
                elif "docker run" in generated_command:
                    detected_intent = "run"
                elif "docker stop" in generated_command:
                    detected_intent = "stop"
                elif "docker start" in generated_command:
                    detected_intent = "start"
                elif "docker rm" in generated_command:
                    detected_intent = "remove"
                elif "docker logs" in generated_command:
                    detected_intent = "logs"
                elif "docker exec" in generated_command:
                    detected_intent = "exec"
                elif "docker build" in generated_command:
                    detected_intent = "build"
                elif "docker compose" in generated_command:
                    detected_intent = "compose"
            elif detected_domain == "kubernetes":
                if "kubectl get" in generated_command:
                    detected_intent = "list"
                elif "kubectl describe" in generated_command:
                    detected_intent = "describe"
                elif "kubectl logs" in generated_command:
                    detected_intent = "logs"
                elif "kubectl scale" in generated_command:
                    detected_intent = "scale"
                elif "kubectl delete" in generated_command:
                    detected_intent = "delete"
                elif "kubectl apply" in generated_command:
                    detected_intent = "apply"
            elif detected_domain == "sql":
                if "SELECT" in generated_command and "WHERE" in generated_command:
                    detected_intent = "select"
                elif "SELECT" in generated_command and ("COUNT" in generated_command or "AVG" in generated_command or "SUM" in generated_command):
                    detected_intent = "aggregate"
                elif "SELECT" in generated_command:
                    detected_intent = "show"
                elif "INSERT" in generated_command:
                    detected_intent = "insert"
                elif "UPDATE" in generated_command:
                    detected_intent = "update"
                elif "DELETE" in generated_command:
                    detected_intent = "delete"
                elif "SHOW TABLES" in generated_command:
                    detected_intent = "show_tables"
            
            return {
                "success": result.returncode == 0,
                "detected_domain": detected_domain,
                "detected_intent": detected_intent,
                "generated_command": generated_command,
                "confidence": confidence,
                "output": output,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "detected_domain": "timeout",
                "detected_intent": "timeout", 
                "generated_command": "",
                "confidence": 0.0,
                "output": "",
                "stderr": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "detected_domain": "error",
                "detected_intent": "error",
                "generated_command": "",
                "confidence": 0.0,
                "output": "",
                "stderr": str(e)
            }
    
    def test_command(self, test_cmd: TestCommand) -> Dict[str, Any]:
        """Test a single command."""
        print(f"Testing: {test_cmd.query}")
        
        result = self.run_command(test_cmd.query)
        
        # Check expectations
        domain_match = result["detected_domain"] == test_cmd.expected_domain
        intent_match = result["detected_intent"] == test_cmd.expected_intent
        command_match = test_cmd.expected_command_pattern in result["generated_command"]
        
        success = domain_match and intent_match and command_match
        
        if success == test_cmd.should_succeed:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        test_result = {
            "query": test_cmd.query,
            "description": test_cmd.description,
            "expected": {
                "domain": test_cmd.expected_domain,
                "intent": test_cmd.expected_intent,
                "command_pattern": test_cmd.expected_command_pattern
            },
            "actual": {
                "domain": result["detected_domain"],
                "intent": result["detected_intent"],
                "command": result["generated_command"]
            },
            "success": success,
            "status": status
        }
        
        self.results.append(test_result)
        
        print(f"  {status} - Expected: {test_cmd.expected_domain}/{test_cmd.expected_intent}")
        print(f"         Got: {result['detected_domain']}/{result['detected_intent']}")
        print(f"         Command: {result['generated_command']}")
        print()
        
        return test_result
    
    def generate_test_commands(self) -> List[TestCommand]:
        """Generate 100+ test commands covering all domains and edge cases."""
        
        commands = []
        
        # === SHELL COMMANDS (30+) ===
        
        # Basic file operations
        commands.extend([
            TestCommand("pokaż pliki", "shell", "list", "ls -la", True, "Basic file listing"),
            TestCommand("lista plików w folderze", "shell", "list", "ls -la", True, "File listing with folder"),
            TestCommand("pokaż pliki w folderze użytkownika", "shell", "list", "ls -la ~", True, "User home directory"),
            TestCommand("znajdź pliki .log", "shell", "find", "find", True, "Find log files"),
            TestCommand("znajdz pliki konfiguracyjne", "shell", "find", "find", True, "Find config files (typo)"),
            TestCommand("skopiuj plik", "shell", "copy", "cp", True, "Copy file"),
            TestCommand("kopij plik", "shell", "file_operation", "ls -la", True, "Copy file with typo"),
            TestCommand("usuń plik stary.txt", "shell", "delete", "rm", True, "Delete specific file"),
            TestCommand("usun plik test.txt", "shell", "delete", "rm", True, "Delete with typo"),
            TestCommand("utwórz katalog nowy", "shell", "create", "mkdir", True, "Create directory"),
            TestCommand("zmień nazwę pliku", "shell", "rename", "mv", True, "Rename file"),
        ])
        
        # Process management
        commands.extend([
            TestCommand("pokaż procesy", "shell", "list_processes", "ps aux", True, "Show processes"),
            TestCommand("ps", "shell", "list_processes", "ps aux", True, "Short ps command"),
            TestCommand("zabij proces 1234", "shell", "process_kill", "kill", True, "Kill process"),
            TestCommand("sprawdź użycie CPU", "shell", "process", "top", True, "Check CPU usage"),
            TestCommand("monitor systemowy", "shell", "process", "htop", True, "System monitor"),
        ])
        
        # Service management
        commands.extend([
            TestCommand("uruchom usługę nginx", "shell", "service_start", "systemctl start nginx", True, "Start nginx service"),
            TestCommand("uruchom uslugę nginx", "shell", "service_start", "systemctl start nginx", True, "Start service with typo"),
            TestCommand("systemctl uruchom nginx", "shell", "service_start", "systemctl start nginx", True, "Start with systemctl"),
            TestCommand("zatrzymaj usługę nginx", "shell", "service_stop", "systemctl stop nginx", True, "Stop nginx service"),
            TestCommand("restartuj usługę nginx", "shell", "service_restart", "systemctl restart nginx", True, "Restart nginx service"),
            TestCommand("status usługi nginx", "shell", "service_status", "systemctl status nginx", True, "Check nginx status"),
        ])
        
        # System operations
        commands.extend([
            TestCommand("restartuj system", "shell", "reboot", "reboot", True, "Reboot system"),
            TestCommand("startuj system", "shell", "reboot", "reboot", True, "Start system (reboot)"),
            TestCommand("zrestartuj komputer", "shell", "reboot", "reboot", True, "Restart computer"),
            TestCommand("sprawdź miejsce na dysku", "shell", "disk", "df", True, "Check disk space"),
            TestCommand("pokaż użycie pamięci", "shell", "disk", "free", True, "Check memory usage"),
        ])
        
        # Network operations
        commands.extend([
            TestCommand("ping google.com", "shell", "network_ping", "ping", True, "Ping host"),
            TestCommand("sprawdź porty", "shell", "network_port", "netstat", True, "Check open ports"),
            TestCommand("pokaż adres IP", "shell", "network_ip", "ip addr", True, "Show IP address"),
        ])
        
        # === DOCKER COMMANDS (25+) ===
        
        # Basic container operations
        commands.extend([
            TestCommand("docker ps", "docker", "list", "docker ps", True, "List running containers"),
            TestCommand("pokaż kontenery", "docker", "list", "docker ps", True, "Show containers in Polish"),
            TestCommand("pokaż wszystkie kontenery", "docker", "list_all", "docker ps -a", True, "Show all containers"),
            TestCommand("doker ps", "docker", "list", "docker ps", True, "Docker with typo"),
            TestCommand("dokcer images", "docker", "images", "docker images", True, "Docker images with typo"),
            TestCommand("docker obrazy", "docker", "images", "docker images", True, "Docker images in Polish"),
            TestCommand("docker run nginx", "docker", "run", "docker run nginx", True, "Run nginx container"),
            TestCommand("docker uruchom nginx", "docker", "run", "docker run nginx", True, "Run container in Polish"),
            TestCommand("doker uruchom nginx", "docker", "run", "docker run nginx", True, "Run with typo"),
            TestCommand("docker stop kontener", "docker", "stop", "docker stop", True, "Stop container"),
            TestCommand("docker zatrzymaj nginx", "docker", "stop", "docker stop nginx", True, "Stop in Polish"),
            TestCommand("docker start nginx", "docker", "start", "docker start nginx", True, "Start container"),
            TestCommand("docker usuń nginx", "docker", "remove", "docker rm nginx", True, "Remove container"),
            TestCommand("docker remove nginx", "docker", "remove", "docker rm nginx", True, "Remove container English"),
        ])
        
        # Docker logs and exec
        commands.extend([
            TestCommand("docker logs nginx", "docker", "logs", "docker logs nginx", True, "Show container logs"),
            TestCommand("pokaż logi kontenera nginx", "docker", "logs", "docker logs nginx", True, "Logs in Polish"),
            TestCommand("docker exec nginx bash", "docker", "exec", "docker exec nginx bash", True, "Exec into container"),
            TestCommand("docker wejdź do nginx", "docker", "exec", "docker exec nginx bash", True, "Exec in Polish"),
        ])
        
        # Docker build and compose
        commands.extend([
            TestCommand("docker build .", "docker", "build", "docker build", True, "Build Docker image"),
            TestCommand("zbuduj obraz docker", "docker", "build", "docker build", True, "Build in Polish"),
            TestCommand("docker compose up", "docker", "compose", "docker compose up", True, "Docker compose up"),
            TestCommand("docker-compose down", "docker", "compose", "docker compose down", True, "Docker compose down"),
            TestCommand("docker compose ps", "docker", "compose", "docker compose ps", True, "Compose ps"),
        ])
        
        # === KUBERNETES COMMANDS (15+) ===
        
        commands.extend([
            TestCommand("kubectl get pods", "kubernetes", "list", "kubectl get pods", True, "List pods"),
            TestCommand("pokaż pody", "kubernetes", "list", "kubectl get pods", True, "Show pods in Polish"),
            TestCommand("kubectl get services", "kubernetes", "list", "kubectl get services", True, "List services"),
            TestCommand("pokaż serwisy k8s", "kubernetes", "list", "kubectl get services", True, "Services in Polish"),
            TestCommand("kubectl describe pod nginx", "kubernetes", "describe", "kubectl describe pod nginx", True, "Describe pod"),
            TestCommand("opisz pod nginx", "kubernetes", "describe", "kubectl describe pod nginx", True, "Describe in Polish"),
            TestCommand("kubectl logs nginx", "kubernetes", "logs", "kubectl logs nginx", True, "Pod logs"),
            TestCommand("logi poda nginx", "kubernetes", "logs", "kubectl logs nginx", True, "Logs in Polish"),
            TestCommand("kubectl scale deployment nginx 3", "kubernetes", "scale", "kubectl scale deployment nginx 3", True, "Scale deployment"),
            TestCommand("skaluj deployment nginx do 3", "kubernetes", "scale", "kubectl scale deployment nginx 3", True, "Scale in Polish"),
            TestCommand("kubectl delete pod nginx", "kubernetes", "delete", "kubectl delete pod nginx", True, "Delete pod"),
            TestCommand("usuń pod nginx", "kubernetes", "delete", "kubectl delete pod nginx", True, "Delete in Polish"),
            TestCommand("kubectl apply -f deployment.yaml", "kubernetes", "apply", "kubectl apply -f deployment.yaml", True, "Apply manifest"),
            TestCommand("zastosuj konfigurację k8s", "kubernetes", "apply", "kubectl apply -f", True, "Apply in Polish"),
        ])
        
        # === SQL COMMANDS (15+) ===
        
        commands.extend([
            TestCommand("pokaż użytkowników", "sql", "show", "SELECT * FROM users", True, "Show users"),
            TestCommand("SELECT * FROM users", "sql", "show", "SELECT * FROM users", True, "Direct SQL"),
            TestCommand("znajdź użytkowników z Warszawy", "sql", "select", "SELECT * FROM users WHERE city = 'Warsaw'", True, "Select with condition"),
            TestCommand("dodaj nowego użytkownika", "sql", "insert", "INSERT INTO users", True, "Insert user"),
            TestCommand("INSERT INTO users (name) VALUES ('Jan')", "sql", "insert", "INSERT INTO users", True, "Direct insert"),
            TestCommand("zaktualizuj email użytkownika", "sql", "update", "UPDATE users SET email", True, "Update user"),
            TestCommand("UPDATE users SET email = 'test@example.com'", "sql", "update", "UPDATE users", True, "Direct update"),
            TestCommand("usuń stare rekordy", "sql", "delete", "DELETE FROM users", True, "Delete records"),
            TestCommand("DELETE FROM users WHERE active = false", "sql", "delete", "DELETE FROM users", True, "Direct delete"),
            TestCommand("policz użytkowników", "sql", "aggregate", "SELECT COUNT(*) FROM users", True, "Count users"),
            TestCommand("COUNT(*) FROM users", "sql", "aggregate", "SELECT COUNT(*)", True, "Direct count"),
            TestCommand("średnia wieku użytkowników", "sql", "aggregate", "SELECT AVG(age)", True, "Average age"),
            TestCommand("SELECT AVG(age) FROM users", "sql", "aggregate", "SELECT AVG(age)", True, "Direct average"),
            TestCommand("grupuj użytkowników po mieście", "sql", "aggregate", "SELECT city, COUNT(*)", True, "Group by city"),
            TestCommand("SELECT city, COUNT(*) FROM users GROUP BY city", "sql", "aggregate", "SELECT city, COUNT(*)", True, "Direct group by"),
        ])
        
        # === EDGE CASES AND TYPOS (15+) ===
        
        commands.extend([
            TestCommand("dokcer ps", "docker", "list", "docker ps", True, "Docker typo"),
            TestCommand("doker images", "docker", "images", "docker images", True, "Another docker typo"),
            TestCommand("uruchom uslugę nginx", "shell", "service_start", "systemctl start nginx", True, "Service with typo"),
            TestCommand("restartuj uslugę nginx", "shell", "service_restart", "systemctl restart nginx", True, "Restart with typo"),
            TestCommand("znajdz pliki", "shell", "find", "find", True, "Find with typo"),
            TestCommand("kopij plik", "shell", "file_operation", "ls -la", True, "Copy with typo"),
            TestCommand("usun plik", "shell", "delete", "rm", True, "Delete with typo"),
            TestCommand("pokaż procesy", "shell", "list_processes", "ps aux", True, "Show processes"),
            TestCommand("systemctl uruchom nginx", "shell", "service_start", "systemctl start nginx", True, "Systemctl command"),
            TestCommand("docker uruchom nginx", "docker", "run", "docker run nginx", True, "Docker in Polish"),
            TestCommand("kubectl get pody", "kubernetes", "list", "kubectl get pods", True, "K8s with Polish typo"),
            TestCommand("pokaż tabele", "sql", "show_tables", "SHOW TABLES", True, "Show tables in Polish"),
            TestCommand("  doker  ps  ", "docker", "list", "docker ps", True, "Extra spaces"),
            TestCommand("ps aux", "shell", "list_processes", "ps aux", True, "Direct ps command"),
        ])
        
        # === AMBIGUOUS/UNKNOWN CASES (5+) ===
        
        commands.extend([
            TestCommand("coś tam", "unknown", "unknown", "", True, "Completely unclear"),
            TestCommand("xyz123", "unknown", "unknown", "", True, "Random text"),
            TestCommand("", "unknown", "unknown", "", True, "Empty input"),
            TestCommand("   ", "unknown", "unknown", "", True, "Whitespace only"),
            TestCommand("help", "unknown", "unknown", "", True, "Help command"),
        ])
        
        return commands
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive NLP2CMD Test Suite")
        print("=" * 60)
        
        commands = self.generate_test_commands()
        
        print(f"Generated {len(commands)} test commands")
        print(f"Testing domains: shell, docker, kubernetes, sql, unknown")
        print()
        
        start_time = time.time()
        
        for i, cmd in enumerate(commands, 1):
            print(f"Test {i}/{len(commands)}: ", end="")
            self.test_command(cmd)
            
            # Progress indicator
            if i % 10 == 0:
                print(f"Progress: {i}/{len(commands)} completed")
                print(f"Current stats: {self.passed} passed, {self.failed} failed")
                print()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate summary
        summary = {
            "total_tests": len(commands),
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": (self.passed / len(commands)) * 100,
            "duration_seconds": duration,
            "results": self.results
        }
        
        self.print_summary(summary)
        self.save_results(summary)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary."""
        print("=" * 60)
        print("🏁 COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print()
        
        # Domain breakdown
        domain_stats = {}
        for result in self.results:
            domain = result["actual"]["domain"]
            if domain not in domain_stats:
                domain_stats[domain] = {"total": 0, "passed": 0}
            domain_stats[domain]["total"] += 1
            if result["success"]:
                domain_stats[domain]["passed"] += 1
        
        print("📊 Results by Domain:")
        for domain, stats in domain_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            print(f"  {domain}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        print()
        
        # Show failed tests
        if self.failed > 0:
            print("❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['query']}")
                    print(f"    Expected: {result['expected']['domain']}/{result['expected']['intent']}")
                    print(f"    Got: {result['actual']['domain']}/{result['actual']['intent']}")
                    print()
    
    def save_results(self, summary: Dict[str, Any]):
        """Save test results to file."""
        results_file = "/home/tom/github/wronai/nlp2cmd/comprehensive_test_results.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    tester = ComprehensiveCommandTester()
    results = tester.run_all_tests()
