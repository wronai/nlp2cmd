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
import json
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nlp2cmd.enhanced import create_enhanced_nlp2cmd
from app2schema import extract_schema_to_file


def main():
    """Run the enhanced NLP2CMD demo."""
    print("🚀 Enhanced NLP2CMD Demo")
    print("=" * 50)

    tmp_dir = Path(tempfile.mkdtemp(prefix="nlp2cmd_demo_"))
    shell_export_path = tmp_dir / "shell_commands.json"
    web_export_path = tmp_dir / "web_schema.json"

    print("\n🧩 Step 1: app2schema → generate schemas")
    print("-" * 40)

    # Generate schemas for system commands (static via help output)
    extract_schema_to_file("git", shell_export_path, source_type="shell", merge=True)
    extract_schema_to_file("df", shell_export_path, source_type="shell", merge=True)
    extract_schema_to_file("du", shell_export_path, source_type="shell", merge=True)

    # Generate a simple web schema from static HTML (no Playwright required)
    html = """
    <html>
      <body>
        <button id=\"login-button\">Login</button>
        <input id=\"username\" placeholder=\"Username\" />
        <input id=\"password\" placeholder=\"Password\" type=\"password\" />
      </body>
    </html>
    """.strip()

    html_path = tmp_dir / "page.html"
    html_path.write_text(html, encoding="utf-8")
    extract_schema_to_file(str(html_path), web_export_path, source_type="web")

    print(f"✅ Wrote shell schema export: {shell_export_path}")
    print(f"✅ Wrote web schema export: {web_export_path}")

    print("\n🧠 Step 2: NLP2CMD → load schemas (import dynamic export)")
    print("-" * 40)

    nlp2cmd = create_enhanced_nlp2cmd(
        schemas=[
            {"source": str(shell_export_path), "type": "auto", "category": "shell"},
            {"source": str(web_export_path), "type": "auto", "category": "web"},
        ],
        nlp_backend="hybrid",
        config={
            "adapter_config": {
                "custom_options": {
                    "load_common_commands": False,
                }
            }
        },
    )
    
    print(f"✅ Loaded {len(nlp2cmd.get_available_commands())} commands")
    print(f"📂 Categories: {', '.join(nlp2cmd.get_command_categories())}")
    
    # Demo queries
    demo_queries = [
        "show git status",
        "show disk usage",
        "check disk usage for current directory",
        "click login",
        "type \"admin\" into username",
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
    print("• ✅ app2schema generates validated schema exports (static + web)")
    print("• ✅ NLP2CMD can import schema exports instead of hardcoded keywords")
    print("• ✅ Supports system commands (git/df/du) and GUI actions (web DOM → DQL)")
    print("• ✅ Hybrid NLP backends still supported")


if __name__ == "__main__":
    main()
