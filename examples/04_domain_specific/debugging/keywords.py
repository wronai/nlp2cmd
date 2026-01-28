#!/usr/bin/env python3
"""
Debug keyword patterns - sprawdzenie czy patterns są ładowane
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do importów
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_rule

from nlp2cmd.generation.keywords import KeywordIntentDetector


def debug_keywords():
    """Debug keyword patterns."""
    print("🔍 Debugowanie keyword patterns")
    print_rule(width=50, char="=")
    
    detector = KeywordIntentDetector()
    
    # Sprawdź patterns
    print("Shell patterns:")
    shell_patterns = detector.patterns.get('shell', {})
    for intent, keywords in shell_patterns.items():
        print(f"  {intent}: {keywords[:3]}...")  # Pokaż pierwsze 3
    
    print("\nDomain boosters:")
    print(f"  Shell: {detector.DOMAIN_BOOSTERS.get('shell', [])[:5]}...")
    
    # Test detection
    test_cases = [
        "znajdź pliki z rozszerzeniem .py",
        "skopiuj plik config.json do backup/",
        "usuń wszystkie pliki .tmp",
        "pokaż zawartość pliku /var/log/syslog",
        "pokaż użycie CPU i pamięci",
        "sprawdź działające procesy",
    ]
    
    print("\nDetection results:")
    for query in test_cases:
        result = detector.detect(query)
        print(f"  Query: {query}")
        print(f"    Domain: {result.domain}")
        print(f"    Intent: {result.intent}")
        print(f"    Confidence: {result.confidence}")
        print(f"    Matched keyword: {result.matched_keyword}")
        print()


if __name__ == "__main__":
    debug_keywords()
