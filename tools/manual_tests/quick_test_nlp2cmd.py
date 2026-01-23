#!/usr/bin/env python3
"""Quick test of NLP2CMD with a few commands."""

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def quick_test():
    """Quick test of NLP2CMD command generation."""
    
    print("Quick NLP2CMD Test")
    print("=" * 60)
    
    # Initialize
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 512,
        "timeout": 10,
    }
    
    registry = DynamicSchemaRegistry(
        auto_save_path="./quick_test_schemas.json",
        use_llm=True,
        llm_config=llm_config
    )
    
    # Load schemas for test commands
    test_commands = ["find", "grep", "tar", "git", "docker"]
    
    print("\nLoading schemas:")
    for cmd in test_commands:
        try:
            schema = registry.register_shell_help(cmd)
            if schema.commands:
                print(f"  ✓ {cmd}: {schema.commands[0].template}")
        except Exception as e:
            print(f"  ✗ {cmd}: {e}")
    
    # Create NLP2CMD
    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test queries
    queries = [
        ("Find all Python files", "find"),
        ("Search for TODO in files", "grep"),
        ("Create backup archive", "tar"),
        ("Check git status", "git"),
        ("List Docker containers", "docker"),
    ]
    
    print("\nTesting command generation:")
    for query, expected_cmd in queries:
        print(f"\nQuery: {query}")
        try:
            result = nlp.transform(query)
            print(f"  Generated: {result.command}")
            if expected_cmd in result.command:
                print(f"  ✓ Contains {expected_cmd}")
            else:
                print(f"  ⚠ Expected {expected_cmd}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    quick_test()
