#!/usr/bin/env python3
"""
Test script for typo tolerance in enhanced context detection.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nlp2cmd.generation.enhanced_context import get_enhanced_detector

def test_typo_tolerance():
    """Test typo tolerance in enhanced context detection."""
    
    test_cases = [
        # Original queries
        ("show user files", "shell", "find"),
        ("pokaż pliki użytkownika", "shell", "find"),
        ("list files in user folder", "shell", "list"),
        ("znajdź pliki w folderze użytkownika", "shell", "find"),
        
        # Typo variations
        ("shwo user files", "shell", "find"),  # show -> shwo
        ("pokaz pliki uzytkownika", "shell", "find"),  # użytkownika -> uzytkownika
        ("list files in user floder", "shell", "list"),  # folder -> floder
        ("znajdz pliki w folderze uzytkownika", "shell", "find"),  # znajdź -> znajdz
        
        # More severe typos
        ("shwo user fils", "shell", "find"),  # files -> fils
        ("pokaz pliki uzytkownika", "shell", "find"),  # użytkownika -> uzytkownika
        ("list fils in user floder", "shell", "list"),  # files -> fils, folder -> floder
        ("znajdz pliki w folderze uzytkownka", "shell", "find"),  # użytkownika -> uzytkownka
        
        # Mixed language typos
        ("shwo pliki user", "shell", "find"),  # Mixed Polish/English
        ("pokaż files użytkownika", "shell", "find"),  # Mixed Polish/English
        ("show pliki w folderze", "shell", "list"),  # Mixed Polish/English
    ]
    
    detector = get_enhanced_detector()
    
    print("🔍 Testing Typo Tolerance in Enhanced Context Detection")
    print("=" * 60)
    
    results = []
    for query, expected_domain, expected_intent in test_cases:
        try:
            match = detector.get_best_match(query)
            
            if match:
                domain_correct = match.domain == expected_domain
                intent_correct = match.intent == expected_intent
                success = domain_correct and intent_correct
                
                results.append({
                    'query': query,
                    'expected_domain': expected_domain,
                    'expected_intent': expected_intent,
                    'actual_domain': match.domain,
                    'actual_intent': match.intent,
                    'combined_score': match.combined_score,
                    'success': success
                })
                
                status = "✅" if success else "❌"
                print(f"{status} '{query}'")
                print(f"   Expected: {expected_domain}/{expected_intent}")
                print(f"   Got: {match.domain}/{match.intent} (score: {match.combined_score:.3f})")
                print()
            else:
                results.append({
                    'query': query,
                    'expected_domain': expected_domain,
                    'expected_intent': expected_intent,
                    'actual_domain': 'unknown',
                    'actual_intent': 'unknown',
                    'combined_score': 0.0,
                    'success': False
                })
                
                print(f"❌ '{query}'")
                print(f"   Expected: {expected_domain}/{expected_intent}")
                print(f"   Got: No match")
                print()
                
        except Exception as e:
            print(f"❌ '{query}' - Error: {e}")
            print()
    
    # Summary
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100
    
    print("=" * 60)
    print(f"📊 TYPO TOLERANCE SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    # Failed tests
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print("❌ Failed Tests:")
        for test in failed_tests:
            print(f"   '{test['query']}'")
            print(f"   Expected: {test['expected_domain']}/{test['expected_intent']}")
            print(f"   Got: {test['actual_domain']}/{test['actual_intent']}")
            print()
    
    # Score analysis
    scores = [r['combined_score'] for r in results if r['combined_score'] > 0]
    if scores:
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        print(f"📈 SCORE ANALYSIS")
        print(f"Average Score: {avg_score:.3f}")
        print(f"Min Score: {min_score:.3f}")
        print(f"Max Score: {max_score:.3f}")
        print()
    
    # Recommendations
    if success_rate < 70:
        print("🔧 RECOMMENDATIONS:")
        print("1. Add fuzzy matching for typos")
        print("2. Implement Levenshtein distance")
        print("3. Use phonetic similarity")
        print("4. Add more typo variations to patterns")
        print()
    elif success_rate < 85:
        print("🔧 RECOMMENDATIONS:")
        print("1. Add more typo variations to patterns")
        print("2. Improve semantic similarity for typos")
        print("3. Lower threshold for typo detection")
        print()
    else:
        print("✅ Typo tolerance is working well!")
        print()
    
    return success_rate

if __name__ == "__main__":
    success_rate = test_typo_tolerance()
    sys.exit(0 if success_rate >= 70 else 1)
