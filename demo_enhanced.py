#!/usr/bin/env python3
"""
Demo script showcasing the enhanced dynamic NLP2CMD implementation.

This script demonstrates:
- Dynamic schema extraction from multiple sources
- Shell-gpt integration for intelligent command generation
- Enhanced NLP processing without hardcoded keywords
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nlp2cmd.enhanced import create_enhanced_nlp2cmd, demo_dynamic_extraction


def main():
    """Run the enhanced NLP2CMD demo."""
    print("🚀 Enhanced NLP2CMD Demo")
    print("=" * 50)
    
    # Create enhanced instance
    print("\n📦 Initializing enhanced NLP2CMD with dynamic schemas...")
    nlp2cmd = create_enhanced_nlp2cmd(
        schemas=["find", "grep", "git", "docker"],  # Common shell commands
        nlp_backend="hybrid"  # Use shell-gpt + fallbacks
    )
    
    print(f"✅ Loaded {len(nlp2cmd.get_available_commands())} commands")
    print(f"📂 Categories: {', '.join(nlp2cmd.get_command_categories())}")
    
    # Demo queries
    demo_queries = [
        "find all Python files in the current directory",
        "show git status", 
        "list running docker containers",
        "search for 'error' in log files",
        "copy file.txt to backup directory",
    ]
    
    print("\n🔍 Processing Natural Language Queries:")
    print("-" * 40)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        
        try:
            # Analyze the query
            analysis = nlp2cmd.analyze_query(query)
            print(f"   🎯 Intent: {analysis['detected_intent']}")
            print(f"   📊 Confidence: {analysis['confidence']:.2f}")
            print(f"   🏷️  Entities: {analysis['extracted_entities']}")
            
            if analysis['matching_commands']:
                best_match = analysis['matching_commands'][0]
                print(f"   ✨ Best match: {best_match['name']}")
                print(f"   📝 Description: {best_match['description']}")
            
            # Transform to command
            result = nlp2cmd.transform_with_explanation(query)
            if result.is_success:
                print(f"   ⚡ Generated: {result.command}")
                print(f"   💡 Explanation: {result.metadata.get('explanation', 'N/A')}")
            else:
                print(f"   ❌ Failed: {result.errors}")
                
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    
    # Show schema export
    print("\n📤 Schema Export Sample:")
    print("-" * 30)
    schemas_json = nlp2cmd.export_schemas("json")
    print(f"Exported {len(schemas_json)} characters of schema data")
    
    # Show first command details
    commands = nlp2cmd.get_available_commands()
    if commands:
        first_cmd = commands[0]
        help_text = nlp2cmd.get_command_help(first_cmd)
        if help_text:
            print(f"\n📖 Command Help for '{first_cmd}':")
            print(help_text[:300] + "..." if len(help_text) > 300 else help_text)
    
    print("\n🎉 Demo completed!")
    print("\nKey improvements:")
    print("• ✅ No hardcoded keywords - all extracted dynamically")
    print("• ✅ Multiple schema sources (OpenAPI, shell help, Python code)")
    print("• ✅ Shell-gpt integration for intelligent understanding")
    print("• ✅ Enhanced NLP with hybrid backends")
    print("• ✅ Better accuracy and flexibility")
    
    print("\nTo run the full demo with more examples:")
    print("  python -c \"from nlp2cmd.enhanced import demo_dynamic_extraction; demo_dynamic_extraction()\"")


if __name__ == "__main__":
    main()
