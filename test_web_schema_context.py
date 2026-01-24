#!/usr/bin/env python3
"""
Test Web Schema Context Detection with Enhanced NLP.

Tests browser domain detection using extracted web schemas
from real websites like GitHub.
"""

import subprocess
import json
import time
from typing import Dict, List, Any

def test_web_schema_context():
    """Test web schema context detection."""
    
    print("🌐 Testing Web Schema Context Detection")
    print("=" * 50)
    
    # Test queries that should match web schema actions
    web_queries = [
        # GitHub-specific queries
        ("wpisz tekst w wyszukiwarce github", "browser", "web_action"),
        ("kliknij przycisk sign in na github", "browser", "web_action"),
        ("type text in github search", "browser", "web_action"),
        ("click sign in button", "browser", "web_action"),
        ("znajdź pole feedback na github", "browser", "web_action"),
        ("wypełnij formularz na github", "browser", "web_action"),
        
        # General web queries
        ("przejdź do github", "browser", "navigate"),
        ("otwórz stronę github", "browser", "navigate"),
        ("kliknij link", "browser", "click"),
        ("wypełnij formularz", "browser", "fill_form"),
        
        # Mixed queries that should be detected as browser
        ("chcę coś wyszukać na stronie", "browser", "web_action"),
        ("kliknij przycisk na stronie", "browser", "web_action"),
        ("wpisz dane w formularzu", "browser", "web_action"),
    ]
    
    results = []
    
    for query, expected_domain, expected_intent in web_queries:
        print(f"\n🔍 Testing: '{query}'")
        print(f"   Expected: {expected_domain}/{expected_intent}")
        
        try:
            result = subprocess.run(
                ["nlp2cmd", "--query", query, "--explain"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd="/home/tom/github/wronai/nlp2cmd"
            )
            
            output = result.stdout
            lines = output.strip().split('\n')
            
            # Parse results
            command = ""
            domain = "unknown"
            confidence = 0.0
            
            for line in lines:
                if line.strip() and not line.startswith("📊") and not line.startswith("Source:") and not line.startswith("Domain:") and not line.startswith("Confidence:") and not line.startswith("Latency:"):
                    command = line.strip()
                    break
            
            for line in lines:
                if line.startswith("Domain:"):
                    domain = line.split("Domain:")[1].strip()
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.split("Confidence:")[1].strip())
                    except:
                        pass
            
            # Infer intent from command
            intent = infer_intent_from_command(command, domain)
            
            success = (domain == expected_domain and intent == expected_intent)
            status = "✅ PASS" if success else "❌ FAIL"
            
            print(f"   Got: {domain}/{intent} (confidence: {confidence:.2f})")
            print(f"   Command: {command}")
            print(f"   {status}")
            
            results.append({
                'query': query,
                'expected': f"{expected_domain}/{expected_intent}",
                'actual': f"{domain}/{intent}",
                'command': command,
                'confidence': confidence,
                'success': success
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'query': query,
                'expected': f"{expected_domain}/{expected_intent}",
                'actual': "error",
                'command': "",
                'confidence': 0.0,
                'success': False
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 WEB SCHEMA CONTEXT SUMMARY")
    print("=" * 50)
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Show failed tests
    if failed > 0:
        print("\n❌ Failed Tests:")
        for result in results:
            if not result['success']:
                print(f"  - '{result['query']}'")
                print(f"    Expected: {result['expected']}")
                print(f"    Got: {result['actual']}")
                print(f"    Command: {result['command']}")
                print()
    
    # Show confidence analysis
    confidences = [r['confidence'] for r in results if r['confidence'] > 0]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"📈 Average Confidence: {avg_confidence:.2f}")
        print(f"📈 Confidence Range: {min(confidences):.2f} - {max(confidences):.2f}")
    
    # Domain breakdown
    domain_stats = {}
    for result in results:
        domain = result['actual'].split('/')[0] if '/' in result['actual'] else result['actual']
        if domain not in domain_stats:
            domain_stats[domain] = {"total": 0, "passed": 0}
        domain_stats[domain]["total"] += 1
        if result['success']:
            domain_stats[domain]["passed"] += 1
    
    print(f"\n📊 Results by Domain:")
    for domain, stats in domain_stats.items():
        success_rate = (stats["passed"] / stats["total"]) * 100
        print(f"  {domain}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
    
    # Save results
    with open('/home/tom/github/wronai/nlp2cmd/web_schema_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'success_rate': success_rate,
                'avg_confidence': avg_confidence if confidences else 0.0,
                'domain_stats': domain_stats
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: web_schema_test_results.json")

def infer_intent_from_command(command: str, domain: str) -> str:
    """Infer intent from generated command."""
    if domain == "browser":
        if "navigate" in command or "open_url" in command:
            return "navigate"
        elif "click" in command:
            return "click"
        elif "type" in command or "fill" in command:
            return "web_action"
        elif "fill_form" in command:
            return "fill_form"
        else:
            return "web_action"
    elif domain == "shell":
        if "ls" in command:
            return "list"
        elif "find" in command:
            return "find"
        elif "cp" in command:
            return "copy"
        elif "rm" in command:
            return "delete"
        elif "mkdir" in command:
            return "create"
        elif "ps" in command:
            return "list_processes"
        elif "kill" in command:
            return "process_kill"
        elif "systemctl start" in command:
            return "service_start"
        elif "systemctl stop" in command:
            return "service_stop"
        elif "systemctl restart" in command:
            return "service_restart"
        elif "reboot" in command:
            return "reboot"
        elif "ping" in command:
            return "network_ping"
        elif "netstat" in command:
            return "network_port"
        elif "ip addr" in command:
            return "network_ip"
    elif domain == "docker":
        if "docker ps" in command and "-a" in command:
            return "list_all"
        elif "docker ps" in command:
            return "list"
        elif "docker images" in command:
            return "images"
        elif "docker run" in command:
            return "run"
        elif "docker stop" in command:
            return "stop"
        elif "docker start" in command:
            return "start"
        elif "docker rm" in command:
            return "remove"
        elif "docker logs" in command:
            return "logs"
        elif "docker exec" in command:
            return "exec"
        elif "docker build" in command:
            return "build"
        elif "docker compose" in command:
            return "compose"
    elif domain == "kubernetes":
        if "kubectl get" in command:
            return "list"
        elif "kubectl describe" in command:
            return "describe"
        elif "kubectl logs" in command:
            return "logs"
        elif "kubectl scale" in command:
            return "scale"
        elif "kubectl delete" in command:
            return "delete"
        elif "kubectl apply" in command:
            return "apply"
    elif domain == "sql":
        if "SELECT" in command and "WHERE" in command:
            return "select"
        elif "SELECT" in command and ("COUNT" in command or "AVG" in command or "SUM" in command):
            return "aggregate"
        elif "SELECT" in command:
            return "show"
        elif "INSERT" in command:
            return "insert"
        elif "UPDATE" in command:
            return "update"
        elif "DELETE" in command:
            return "delete"
        elif "SHOW TABLES" in command:
            return "show_tables"
    
    return "unknown"

if __name__ == "__main__":
    test_web_schema_context()
