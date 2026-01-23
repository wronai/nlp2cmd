#!/usr/bin/env python3
"""Practical example of using dynamic schema cache."""

from pathlib import Path
from nlp2cmd.schema_extraction import DynamicSchemaRegistry
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd import NLP2CMD

def main():
    cache_file = Path("./schema_cache.json")
    
    # Create registry
    registry = DynamicSchemaRegistry()
    
    # Try to load from cache first
    loaded = registry.load_cache(cache_file)
    print(f"Loaded {loaded} schemas from cache")
    
    if loaded == 0:
        print("Cache miss - extracting schemas...")
        # Extract schemas for common commands
        common_commands = ['find', 'grep', 'ps', 'df', 'tar', 'git', 'docker']
        
        for cmd in common_commands:
            try:
                registry.register_shell_help(cmd)
                print(f"Extracted schema for {cmd}")
            except Exception as e:
                print(f"Failed to extract {cmd}: {e}")
        
        # Save to cache for next run
        registry.save_cache(cache_file)
        print(f"Saved {len(registry.schemas)} schemas to cache")
    
    # Show some templates
    print("\nGenerated templates:")
    for cmd_name in ['find', 'grep', 'tar']:
        cmd = registry.get_command_by_name(cmd_name)
        if cmd and cmd.template:
            print(f"  {cmd_name}: {cmd.template}")
    
    # Use with NLP2CMD
    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test commands
    test_queries = [
        "Find files larger than 100MB",
        "Search for TODO comments",
        "Compress logs directory",
    ]
    
    print("\nGenerated commands:")
    for query in test_queries:
        result = nlp.transform(query)
        print(f"  Q: {query}")
        print(f"  A: {result.command}\n")

if __name__ == "__main__":
    main()
