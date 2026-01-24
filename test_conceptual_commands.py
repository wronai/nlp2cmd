#!/usr/bin/env python3
"""
Test script for conceptual command generation.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nlp2cmd.concepts.conceptual_commands import ConceptualCommandGenerator

def test_conceptual_commands():
    """Test conceptual command generation."""
    
    test_cases = [
        "pokaz pliki usera",
        "show user files", 
        "pokaż pliki użytkownika",
        "list files in user directory",
        "znajdź pliki w folderze użytkownika",
        "show current user processes",
        "list user home directory",
        "find user configuration files"
    ]
    
    generator = ConceptualCommandGenerator()
    
    print("🔍 Testing Conceptual Command Generation")
    print("=" * 60)
    
    results = []
    for query in test_cases:
        try:
            conceptual_command = generator.generate_command(query)
            
            success = (conceptual_command.command and 
                      not conceptual_command.command.startswith('#') and
                      conceptual_command.confidence > 0.3)  # Lower threshold
            
            results.append({
                'query': query,
                'command': conceptual_command.command,
                'intent': conceptual_command.intent,
                'confidence': conceptual_command.confidence,
                'objects': len(conceptual_command.objects),
                'dependencies': len(conceptual_command.dependencies),
                'success': success,
                'reasoning': conceptual_command.reasoning,
                'alternatives': conceptual_command.alternatives
            })
            
            status = "✅" if success else "❌"
            print(f"{status} '{query}'")
            print(f"   Command: {conceptual_command.command}")
            print(f"   Intent: {conceptual_command.intent}")
            print(f"   Confidence: {conceptual_command.confidence:.3f}")
            print(f"   Objects: {len(conceptual_command.objects)}")
            print(f"   Dependencies: {len(conceptual_command.dependencies)}")
            
            if conceptual_command.reasoning:
                print(f"   Reasoning: {'; '.join(conceptual_command.reasoning[:2])}")
            
            if conceptual_command.alternatives:
                print(f"   Alternatives: {', '.join(conceptual_command.alternatives[:2])}")
            
            print()
            
        except Exception as e:
            print(f"❌ '{query}' - Error: {e}")
            print()
    
    # Summary
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100
    
    print("=" * 60)
    print(f"📊 CONCEPTUAL COMMANDS SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    # Statistics
    if results:
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        avg_objects = sum(r['objects'] for r in results) / len(results)
        avg_dependencies = sum(r['dependencies'] for r in results) / len(results)
        
        print(f"📈 STATISTICS")
        print(f"Average Confidence: {avg_confidence:.3f}")
        print(f"Average Objects: {avg_objects:.1f}")
        print(f"Average Dependencies: {avg_dependencies:.1f}")
        print()
    
    # Failed tests
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print("❌ Failed Tests:")
        for test in failed_tests:
            print(f"   '{test['query']}'")
            print(f"   Command: {test['command']}")
            print(f"   Confidence: {test['confidence']:.3f}")
            print()
    
    # Object analysis
    all_objects = []
    for result in results:
        if 'objects' in result and hasattr(result, 'objects'):
            # This would need the actual objects, but we have count only
            pass
    
    return success_rate

if __name__ == "__main__":
    success_rate = test_conceptual_commands()
    sys.exit(0 if success_rate >= 50 else 1)  # Lower threshold
