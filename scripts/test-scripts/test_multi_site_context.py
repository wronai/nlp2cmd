#!/usr/bin/env python3
"""
Test Multi-Site Web Schema Context Detection.

Tests browser domain detection using extracted web schemas
from multiple websites: GitHub, Google, Amazon.
"""

import subprocess
import json
import time
from typing import Dict, List, Any

def test_multi_site_context():
    """Test multi-site web schema context detection."""
    
    print("🌐 Testing Multi-Site Web Schema Context Detection")
    print("=" * 60)
    
    # Test queries for different sites
    multi_site_queries = [
        # GitHub-specific queries
        ("znajdź repozytorium na github", "browser", "web_action", "github"),
        ("wyszukaj użytkownika github", "browser", "web_action", "github"),
        ("kliknij sign in na github", "browser", "web_action", "github"),
        
        # Google-specific queries
        ("wpisz coś w google search", "browser", "web_action", "google"),
        ("wyszukaj w google", "browser", "web_action", "google"),
        ("kliknij aplikacje google", "browser", "web_action", "google"),
        ("wyczyść wyszukiwarkę google", "browser", "web_action", "google"),
        
        # Amazon-specific queries
        ("szukaj na amazon", "browser", "web_action", "amazon"),
        ("znajdź produkt na amazon", "browser", "web_action", "amazon"),
        ("wyszukaj książki amazon", "browser", "web_action", "amazon"),
        ("kliknij koszyk amazon", "browser", "web_action", "amazon"),
        
        # General web queries
        ("przejdź do strony", "browser", "navigate", "general"),
        ("wypełnij formularz", "browser", "fill_form", "general"),
        ("kliknij przycisk", "browser", "click", "general"),
        ("wpisz tekst w wyszukiwarce", "browser", "web_action", "general"),
        
        # Complex multi-site queries
        ("wyszukaj python tutorial w google", "browser", "web_action", "google"),
        ("znajdź książkę o nlp na amazon", "browser", "web_action", "amazon"),
        ("sprawdź repozytorium nlp2cmd na github", "browser", "web_action", "github"),
    ]
    
    results = []
    
    for query, expected_domain, expected_intent, expected_site in multi_site_queries:
        print(f"\n🔍 Testing: '{query}'")
        print(f"   Expected: {expected_domain}/{expected_intent} (site: {expected_site})")
        
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
            
            # Check if domain matches
            domain_success = domain == expected_domain
            intent_success = intent == expected_intent
            overall_success = domain_success and intent_success
            
            status = "✅ PASS" if overall_success else "❌ FAIL"
            
            print(f"   Got: {domain}/{intent} (confidence: {confidence:.2f})")
            print(f"   Command: {command}")
            print(f"   Domain: {'✅' if domain_success else '❌'} | Intent: {'✅' if intent_success else '❌'}")
            print(f"   {status}")
            
            results.append({
                'query': query,
                'expected_domain': expected_domain,
                'expected_intent': expected_intent,
                'expected_site': expected_site,
                'actual_domain': domain,
                'actual_intent': intent,
                'command': command,
                'confidence': confidence,
                'domain_success': domain_success,
                'intent_success': intent_success,
                'overall_success': overall_success
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'query': query,
                'expected_domain': expected_domain,
                'expected_intent': expected_intent,
                'expected_site': expected_site,
                'actual_domain': "error",
                'actual_intent': "error",
                'command': "",
                'confidence': 0.0,
                'domain_success': False,
                'intent_success': False,
                'overall_success': False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MULTI-SITE WEB SCHEMA CONTEXT SUMMARY")
    print("=" * 60)
    
    total = len(results)
    domain_passed = sum(1 for r in results if r['domain_success'])
    intent_passed = sum(1 for r in results if r['intent_success'])
    overall_passed = sum(1 for r in results if r['overall_success'])
    
    domain_success_rate = (domain_passed / total) * 100 if total > 0 else 0
    intent_success_rate = (intent_passed / total) * 100 if total > 0 else 0
    overall_success_rate = (overall_passed / total) * 100 if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Domain Detection: {domain_passed}/{total} ({domain_success_rate:.1f}%) ✅")
    print(f"Intent Detection: {intent_passed}/{total} ({intent_success_rate:.1f}%) ✅")
    print(f"Overall Success: {overall_passed}/{total} ({overall_success_rate:.1f}%) ✅")
    
    # Show failed tests
    if overall_passed < total:
        print("\n❌ Failed Tests:")
        for result in results:
            if not result['overall_success']:
                print(f"  - '{result['query']}' (site: {result['expected_site']})")
                print(f"    Expected: {result['expected_domain']}/{result['expected_intent']}")
                print(f"    Got: {result['actual_domain']}/{result['actual_intent']}")
                print(f"    Command: {result['command']}")
                print()
    
    # Site-specific breakdown
    site_stats = {}
    for result in results:
        site = result['expected_site']
        if site not in site_stats:
            site_stats[site] = {"total": 0, "passed": 0, "domain_passed": 0}
        site_stats[site]["total"] += 1
        if result['domain_success']:
            site_stats[site]["domain_passed"] += 1
        if result['overall_success']:
            site_stats[site]["passed"] += 1
    
    print(f"\n📊 Results by Site:")
    for site, stats in site_stats.items():
        success_rate = (stats["passed"] / stats["total"]) * 100
        domain_rate = (stats["domain_passed"] / stats["total"]) * 100
        print(f"  {site}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%) | Domain: {domain_rate:.1f}%")
    
    # Confidence analysis
    confidences = [r['confidence'] for r in results if r['confidence'] > 0]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"\n📈 Average Confidence: {avg_confidence:.2f}")
        print(f"📈 Confidence Range: {min(confidences):.2f} - {max(confidences):.2f}")
    
    # Save results
    with open('/home/tom/github/wronai/nlp2cmd/multi_site_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'domain_passed': domain_passed,
                'intent_passed': intent_passed,
                'overall_passed': overall_passed,
                'domain_success_rate': domain_success_rate,
                'intent_success_rate': intent_success_rate,
                'overall_success_rate': overall_success_rate,
                'avg_confidence': avg_confidence if confidences else 0.0,
                'site_stats': site_stats
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: multi_site_test_results.json")

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
    test_multi_site_context()
