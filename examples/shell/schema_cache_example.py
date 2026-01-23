#!/usr/bin/env python3
"""Practical example of using AppSpec cache."""

from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import AppSpecAdapter

def main():
    cache_file = Path("./appspec_cache.json")

    # Cache miss -> generate AppSpec
    if not cache_file.exists():
        print("Cache miss - generating AppSpec...")
        common_commands = ["find", "grep", "ps", "df", "tar", "git", "docker"]
        first = True
        for cmd in common_commands:
            try:
                extract_appspec_to_file(cmd, cache_file, source_type="shell", merge=not first)
                first = False
                print(f"Extracted AppSpec for {cmd}")
            except Exception as e:
                print(f"Failed to extract {cmd}: {e}")

    adapter = AppSpecAdapter(appspec_path=cache_file)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test commands
    test_queries = [
        "Find files larger than 100MB",
        "Search for TODO comments",
        "Compress logs directory",
    ]
    
    print("\nGenerated actions (ActionIR.dsl):")
    for query in test_queries:
        ir = nlp.transform_ir(query)
        print(f"  Q: {query}")
        print(f"  A: {ir.dsl}\n")

if __name__ == "__main__":
    main()
