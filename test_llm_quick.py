#!/usr/bin/env python3
"""Quick test of LLM schema extraction for a few commands."""

import json
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def test_llm_extraction():
    """Test LLM extraction for a few commands."""
    print("Testing LLM schema extraction...")
    
    # Test commands
    commands = ["find", "grep", "tar", "docker", "git"]
    
    # Initialize with LLM
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 2048,
    }
    
    registry = DynamicSchemaRegistry(
        auto_save_path="./test_llm_schemas.json",
        use_llm=True,
        llm_config=llm_config
    )
    
    print(f"\nExtracting schemas for {len(commands)} commands...")
    
    for cmd in commands:
        try:
            schema = registry.register_shell_help(cmd)
            if schema.commands:
                cmd_schema = schema.commands[0]
                print(f"\n{cmd}:")
                print(f"  Description: {cmd_schema.description[:80]}...")
                print(f"  Category: {cmd_schema.category}")
                print(f"  Parameters: {len(cmd_schema.parameters)}")
                print(f"  Template: {cmd_schema.template or 'None'}")
                print(f"  Source: {cmd_schema.source_type}")
        except Exception as e:
            print(f"\n{cmd}: FAILED - {e}")
    
    print("\nResults saved to: test_llm_schemas.json")

if __name__ == "__main__":
    test_llm_extraction()
