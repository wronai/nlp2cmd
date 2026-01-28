#!/usr/bin/env python3
"""
Debug generator - sprawdzenie czy generator używa nowego kodu
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do importów
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_rule

from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator
from nlp2cmd.generation.keywords import KeywordIntentDetector


async def debug_generator():
    """Debug generator internals."""
    print("🔍 Debugowanie generator internals")
    print_rule(width=50, char="=")
    
    # Sprawdź czy mamy nową wersję KeywordIntentDetector
    detector = KeywordIntentDetector()
    
    # Sprawdź czy nasze nowe patterns są załadowane
    shell_patterns = detector.patterns.get('shell', {})
    print(f"Shell patterns count: {len(shell_patterns)}")
    print(f"Shell intents: {list(shell_patterns.keys())}")
    
    # Sprawdź czy nasze nowe domain boosters są załadowane
    shell_boosters = detector.DOMAIN_BOOSTERS.get('shell', [])
    print(f"Shell boosters count: {len(shell_boosters)}")
    print(f"Shell boosters: {shell_boosters[:5]}...")
    
    # Sprawdź czy nasze nowe priority intents są załadowane
    shell_priority_intents = detector.PRIORITY_INTENTS.get('shell', [])
    print(f"Shell priority intents: {shell_priority_intents}")
    
    # Test detection bezpośrednio
    test_query = "usuń wszystkie pliki .tmp"
    print(f"\nDirect detection test: '{test_query}'")
    result = detector.detect(test_query)
    print(f"  Domain: {result.domain}")
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Matched keyword: {result.matched_keyword}")
    
    # Test przez generator
    generator = HybridThermodynamicGenerator()
    print(f"\nGenerator test: '{test_query}'")
    gen_result = await generator.generate(test_query)
    
    if hasattr(gen_result, 'result') and hasattr(gen_result.result, 'domain'):
        domain = gen_result.result.domain
        intent = gen_result.result.intent
        command = gen_result.result.command
    elif hasattr(gen_result, 'domain'):
        domain = gen_result.domain
        intent = gen_result.intent
        command = gen_result.command
    else:
        domain = "unknown"
        intent = "unknown"
        command = str(gen_result)
    
    print(f"  Domain: {domain}")
    print(f"  Intent: {intent}")
    print(f"  Command: {command}")
    
    # Sprawdź czy generator używa tego samego detectora
    print(f"\nChecking generator internals:")
    print(f"Generator DSL generator type: {type(generator.dsl_generator)}")
    if hasattr(generator.dsl_generator, 'rules'):
        print(f"Generator rules type: {type(generator.dsl_generator.rules)}")
        if hasattr(generator.dsl_generator.rules, 'detector'):
            print(f"Generator detector type: {type(generator.dsl_generator.rules.detector)}")
            gen_detector = generator.dsl_generator.rules.detector
            gen_shell_patterns = gen_detector.patterns.get('shell', {})
            print(f"Generator shell patterns count: {len(gen_shell_patterns)}")


if __name__ == "__main__":
    asyncio.run(debug_generator())
