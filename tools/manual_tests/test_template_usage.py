#!/usr/bin/env python3
"""Test template usage in NLP2CMD."""

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def test_template_usage():
    """Test if NLP2CMD is using our templates."""
    
    print("Testing Template Usage in NLP2CMD")
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
        auto_save_path="./template_test_schemas.json",
        use_llm=True,
        llm_config=llm_config
    )
    
    # Load schema for find
    schema = registry.register_shell_help("find")
    print(f"\nFind schema template: {schema.commands[0].template}")
    
    # Create NLP2CMD
    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test with specific query
    query = "Find all Python files"
    print(f"\nQuery: {query}")
    
    result = nlp.transform(query)
    print(f"Generated: {result.command}")
    
    # Check what template should be used
    find_template = schema.commands[0].template
    print(f"Expected template: {find_template}")
    
    # Let's check the internal process
    print(f"\nDebug info:")
    print(f"  Intent: {result.metadata.get('intent', 'N/A')}")
    print(f"  Confidence: {result.metadata.get('confidence', 'N/A')}")

if __name__ == "__main__":
    test_template_usage()
