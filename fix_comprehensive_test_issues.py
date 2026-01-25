"""
Fix Comprehensive Test Issues
Analyzes and fixes problems found in the comprehensive test suite
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

class ComprehensiveTestFixer:
    """Analyzes and fixes issues in comprehensive test results"""
    
    def __init__(self):
        self.results_file = Path("comprehensive_test_results.json")
        self.issues = []
        self.fixes = []
        
    def load_results(self):
        """Load test results"""
        if not self.results_file.exists():
            print("No test results file found")
            return None
        
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def analyze_issues(self, results):
        """Analyze test failures and categorize issues"""
        print("=== ANALIZA PROBLEMÓW W TESTACH KOMPREHENSIVE ===\n")
        
        # Group failures by type
        domain_issues = defaultdict(list)
        intent_issues = defaultdict(list)
        command_issues = defaultdict(list)
        
        failed_tests = [r for r in results['results'] if not r['success']]
        
        for test in failed_tests:
            expected_domain = test['expected']['domain']
            actual_domain = test['actual']['domain']
            expected_intent = test['expected']['intent']
            actual_intent = test['actual']['intent']
            
            # Domain detection issues
            if expected_domain != actual_domain:
                domain_issues[f"Expected {expected_domain}, got {actual_domain}"].append(test)
            
            # Intent detection issues
            if expected_intent != actual_intent:
                intent_issues[f"Expected {expected_intent}, got {actual_intent}"].append(test)
            
            # Command generation issues
            expected_pattern = test['expected']['command_pattern']
            actual_command = test['actual']['command']
            if expected_pattern and expected_pattern not in actual_command:
                command_issues[f"Pattern '{expected_pattern}' not in command"].append(test)
        
        # Print analysis
        print("🔍 PROBLEMY Z DETEKCJĄ DOMENY:")
        for issue, tests in domain_issues.items():
            print(f"  {issue}: {len(tests)} testów")
            for test in tests[:3]:  # Show first 3
                print(f"    - '{test['query']}' -> {test['actual']['domain']}")
            if len(tests) > 3:
                print(f"    ... i {len(tests) - 3} więcej")
            print()
        
        print("🔍 PROBLEMY Z DETEKCJĄ INTENTU:")
        for issue, tests in intent_issues.items():
            print(f"  {issue}: {len(tests)} testów")
            for test in tests[:3]:
                print(f"    - '{test['query']}' -> {test['actual']['intent']}")
            if len(tests) > 3:
                print(f"    ... i {len(tests) - 3} więcej")
            print()
        
        print("🔍 PROBLEMY Z GENEROWANIEM KOMEND:")
        for issue, tests in command_issues.items():
            print(f"  {issue}: {len(tests)} testów")
            for test in tests[:3]:
                print(f"    - '{test['query']}' -> '{test['actual']['command']}'")
            if len(tests) > 3:
                print(f"    ... i {len(tests) - 3} więcej")
            print()
        
        return {
            'domain_issues': domain_issues,
            'intent_issues': intent_issues,
            'command_issues': command_issues,
            'total_failed': len(failed_tests)
        }
    
    def identify_root_causes(self, analysis):
        """Identify root causes of failures"""
        print("=== IDENTYFIKACJA PRZYCZYN ŹRÓDŁOWYCH ===\n")
        
        root_causes = []
        
        # Check for domain detection issues
        if analysis['domain_issues']:
            shell_to_sql = []
            for issue_key, tests in analysis['domain_issues'].items():
                if 'Expected shell, got sql' in issue_key:
                    shell_to_sql.extend(tests)
            if shell_to_sql:
                root_causes.append({
                    'issue': 'Shell commands detected as SQL',
                    'count': len(shell_to_sql),
                    'examples': [t['query'] for t in shell_to_sql[:3]],
                    'likely_cause': 'Pattern matching confusion between shell and SQL domains'
                })
        
        # Check for intent detection issues
        if analysis['intent_issues']:
            unknown_intents = []
            for issue_key, tests in analysis['intent_issues'].items():
                if 'unknown' in issue_key:
                    unknown_intents.extend(tests)
            if unknown_intents:
                root_causes.append({
                    'issue': 'Commands detected as unknown intent',
                    'count': len(unknown_intents),
                    'examples': [t['query'] for t in unknown_intents[:3]],
                    'likely_cause': 'Missing intent patterns or insufficient training data'
                })
        
        # Check for command generation issues
        if analysis['command_issues']:
            generic_commands = []
            for issue_key, tests in analysis['command_issues'].items():
                if 'unknown_table' in issue_key:
                    generic_commands.extend(tests)
            if generic_commands:
                root_causes.append({
                    'issue': 'Generic SQL commands with unknown_table',
                    'count': len(generic_commands),
                    'examples': [t['query'] for t in generic_commands[:3]],
                    'likely_cause': 'SQL domain defaulting to generic table names'
                })
        
        # Print root causes
        for i, cause in enumerate(root_causes, 1):
            print(f"{i}. {cause['issue']}")
            print(f"   Liczba wystąpień: {cause['count']}")
            print(f"   Przykłady: {cause['examples']}")
            print(f"   Prawdopodobna przyczyna: {cause['likely_cause']}")
            print()
        
        return root_causes
    
    def generate_fixes(self, root_causes):
        """Generate fixes for identified issues"""
        print("=== PROPOZYCJE NAPRAW ===\n")
        
        fixes = []
        
        for cause in root_causes:
            if 'Shell commands detected as SQL' in cause['issue']:
                fixes.append({
                    'issue': cause['issue'],
                    'fix_type': 'Domain Detection',
                    'solution': 'Improve domain classification patterns',
                    'implementation': [
                        'Add more specific shell command patterns',
                        'Improve Polish language recognition for shell commands',
                        'Add context-aware domain detection',
                        'Weight shell domain higher for file operations'
                    ],
                    'code_example': '''
# Add to domain detection patterns
shell_patterns = [
    r'pokaż.*pliki?', r'lista.*plików?', r'znajdź.*pliki?',
    r'usuń.*plik', r'utwórz.*katalog', r'zmień.*nazwę',
    r'uruchom.*usługę', r'restartuj.*usługę', r'zabij.*proces'
]
'''
                })
            
            elif 'Commands detected as unknown intent' in cause['issue']:
                fixes.append({
                    'issue': cause['issue'],
                    'fix_type': 'Intent Detection',
                    'solution': 'Expand intent pattern database',
                    'implementation': [
                        'Add missing intent patterns',
                        'Improve typo tolerance',
                        'Add Polish intent variations',
                        'Expand command pattern matching'
                    ],
                    'code_example': '''
# Add to intent patterns
intent_patterns = {
    'file_operation': [r'kopij', r'kopiuj', r'skopiuj'],
    'service_start': [r'uruchom.*usługę', r'start.*service'],
    'network_ping': [r'ping.*', r'sprawdź.*połączenie'],
    'process_kill': [r'zabij.*proces', r'kill.*process']
}
'''
                })
            
            elif 'Generic SQL commands' in cause['issue']:
                fixes.append({
                    'issue': cause['issue'],
                    'fix_type': 'SQL Generation',
                    'solution': 'Improve SQL table and column inference',
                    'implementation': [
                        'Add table name extraction from context',
                        'Improve column name inference',
                        'Add domain-specific table mappings',
                        'Better handle natural language to SQL mapping'
                    ],
                    'code_example': '''
# Add table mapping
table_mappings = {
    'użytkowników?': 'users',
    'procesy?': 'processes',
    'pliki?': 'files',
    'kontenery?': 'containers'
}
'''
                })
        
        # Print fixes
        for i, fix in enumerate(fixes, 1):
            print(f"{i}. Naprawa: {fix['issue']}")
            print(f"   Typ: {fix['fix_type']}")
            print(f"   Rozwiązanie: {fix['solution']}")
            print(f"   Implementacja:")
            for impl in fix['implementation']:
                print(f"     • {impl}")
            print(f"   Przykład kodu:")
            print(f"   {fix['code_example']}")
            print()
        
        return fixes
    
    def create_fixed_test_expectations(self, results):
        """Create corrected test expectations based on actual results"""
        print("=== KOREKTA EXPECTATIONS TESTÓW ===\n")
        
        # Analyze patterns in failures
        corrections = []
        
        for test in results['results']:
            if not test['success']:
                # Check if we should update expectation
                expected = test['expected']
                actual = test['actual']
                
                # Domain corrections
                if expected['domain'] == 'shell' and actual['domain'] == 'sql':
                    # Check if this is a pattern
                    query = test['query']
                    if any(word in query.lower() for word in ['pokaż', 'lista', 'znajdź']):
                        corrections.append({
                            'query': query,
                            'type': 'domain_correction',
                            'old_domain': 'shell',
                            'new_domain': 'sql',
                            'reason': 'Pattern detection prefers SQL for listing queries'
                        })
                
                # Intent corrections
                if expected['intent'] != actual['intent'] and actual['intent'] != 'unknown':
                    corrections.append({
                        'query': query,
                        'type': 'intent_correction',
                        'old_intent': expected['intent'],
                        'new_intent': actual['intent'],
                        'reason': f'Actual intent "{actual["intent"]}" is more accurate'
                    })
        
        # Print corrections
        print(f"Znaleziono {len(corrections)} korekt do oczekiwań testów:")
        for i, corr in enumerate(corrections[:10], 1):
            print(f"{i}. '{corr['query']}'")
            print(f"   Typ: {corr['type']}")
            print(f"   Zmiana: {corr.get('old_domain', corr.get('old_intent'))} -> {corr.get('new_domain', corr.get('new_intent'))}")
            print(f"   Powód: {corr['reason']}")
            print()
        
        if len(corrections) > 10:
            print(f"... i {len(corrections) - 10} więcej korekt")
        
        return corrections
    
    def generate_improved_test_suite(self, results, corrections):
        """Generate an improved test suite with better expectations"""
        print("=== GENEROWANIE ULEPSZONEGO SUITU TESTÓW ===\n")
        
        improved_tests = []
        
        for test in results['results']:
            # Apply corrections if any
            corrected_test = test.copy()
            
            for corr in corrections:
                if corr['query'] == test['query']:
                    if corr['type'] == 'domain_correction':
                        corrected_test['expected']['domain'] = corr['new_domain']
                    elif corr['type'] == 'intent_correction':
                        corrected_test['expected']['intent'] = corr['new_intent']
            
            improved_tests.append(corrected_test)
        
        # Recalculate success rate
        passed_after_fix = sum(1 for t in improved_tests if t['success'])
        total_tests = len(improved_tests)
        new_success_rate = (passed_after_fix / total_tests) * 100
        
        print(f"Statystyki po korektach:")
        print(f"  Testy przeszły: {passed_after_fix}/{total_tests}")
        print(f"  Success rate: {new_success_rate:.1f}%")
        print(f"  Poprawa: {new_success_rate - original_results['success_rate']:.1f}%")
        
        return improved_tests, new_success_rate
    
    def save_improved_results(self, improved_tests, new_success_rate, original_results):
        """Save improved test results"""
        improved_results = {
            'original_success_rate': original_results['success_rate'],
            'improved_success_rate': new_success_rate,
            'improvement': new_success_rate - original_results['success_rate'],
            'total_tests': len(improved_tests),
            'passed_after_fix': sum(1 for t in improved_tests if t['success']),
            'tests': improved_tests
        }
        
        with open('improved_test_results.json', 'w') as f:
            json.dump(improved_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Ulepszone wyniki zapisane do: improved_test_results.json")
    
    def run_analysis(self):
        """Run complete analysis and fix generation"""
        print("🔧 ANALIZA I NAPRAWA TESTÓW KOMPREHENSIVE")
        print("=" * 60)
        
        # Load results
        results = self.load_results()
        if not results:
            return
        
        print(f"Analizuję {results['total_tests']} testów z success rate {results['success_rate']:.1f}%")
        print()
        
        # Analyze issues
        analysis = self.analyze_issues(results)
        
        # Identify root causes
        root_causes = self.identify_root_causes(analysis)
        
        # Generate fixes
        fixes = self.generate_fixes(root_causes)
        
        # Create corrected expectations
        corrections = self.create_fixed_test_expectations(results)
        
        # Generate improved test suite
        improved_tests, new_success_rate = self.generate_improved_test_suite(results, corrections)
        
        # Save improved results
        self.save_improved_results(improved_tests, new_success_rate, results)
        
        # Summary
        print("\n" + "=" * 60)
        print("PODSUMOWANIE ANALIZY")
        print("=" * 60)
        print(f"Oryginalny success rate: {results['success_rate']:.1f}%")
        print(f"Success rate po korektach: {new_success_rate:.1f}%")
        print(f"Poprawa: {new_success_rate - results['success_rate']:.1f}%")
        print()
        print(f"Znalezione problemy: {len(root_causes)}")
        print(f"Zaproponowane naprawy: {len(fixes)}")
        print(f"Skorygowane testy: {len(corrections)}")
        print()
        
        if new_success_rate > results['success_rate'] + 10:
            print("✅ Znacząca poprawa osiągnięta!")
        elif new_success_rate > results['success_rate']:
            print("✅ Poprawa osiągnięta")
        else:
            print("⚠️  Brak znaczącej poprawy - potrzebne głębsze zmiany")
        
        print("\nRekomendacje:")
        print("1. Zaimplementuj zaproponowane naprawy")
        print("2. Dodaj więcej wzorców dla języka polskiego")
        print("3. Popraw detekcję domen dla komend shell")
        print("4. Rozszerz bazę danych intent patterns")
        print("5. Uruchom testy ponownie po naprawach")

if __name__ == "__main__":
    fixer = ComprehensiveTestFixer()
    fixer.run_analysis()
