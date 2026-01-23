#!/usr/bin/env python3
"""Compare schema generation with and without LLM for selected commands."""

import json
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def compare_schemas():
    """Compare schemas generated with and without LLM."""
    commands = ["find", "grep", "tar", "docker", "git", "curl", "wget", "ps"]
    
    print("Comparing schema generation with and without LLM\n")
    print("="*80)
    print(f"{'Command':<10} {'Method':<15} {'Template':<40} {'Category':<10}")
    print("="*80)
    
    # Test without LLM
    registry_no_llm = DynamicSchemaRegistry(use_llm=False)
    
    # Test with LLM
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 1024,  # Reduced for speed
    }
    registry_with_llm = DynamicSchemaRegistry(use_llm=True, llm_config=llm_config)
    
    results = []
    
    for cmd in commands:
        # Without LLM
        try:
            schema_no_llm = registry_no_llm.register_shell_help(cmd)
            if schema_no_llm.commands:
                no_llm_template = schema_no_llm.commands[0].template or "None"
                no_llm_category = schema_no_llm.commands[0].category
            else:
                no_llm_template = "Failed"
                no_llm_category = "N/A"
        except Exception as e:
            no_llm_template = f"Error: {str(e)[:20]}"
            no_llm_category = "N/A"
        
        # With LLM
        try:
            schema_with_llm = registry_with_llm.register_shell_help(cmd)
            if schema_with_llm.commands:
                with_llm_template = schema_with_llm.commands[0].template or "None"
                with_llm_category = schema_with_llm.commands[0].category
            else:
                with_llm_template = "Failed"
                with_llm_category = "N/A"
        except Exception as e:
            with_llm_template = f"Error: {str(e)[:20]}"
            with_llm_category = "N/A"
        
        # Print comparison
        print(f"{cmd:<10} {'No LLM':<15} {no_llm_template[:40]:<40} {no_llm_category:<10}")
        print(f"{cmd:<10} {'With LLM':<15} {with_llm_template[:40]:<40} {with_llm_category:<10}")
        print("-"*80)
        
        results.append({
            "command": cmd,
            "no_llm": {"template": no_llm_template, "category": no_llm_category},
            "with_llm": {"template": with_llm_template, "category": with_llm_category},
        })
    
    # Summary
    print("\nSUMMARY:")
    print("- Commands with better templates using LLM:")
    for r in results:
        if (r["with_llm"]["template"] != "None" and 
            r["with_llm"]["template"] != "Failed" and
            r["no_llm"]["template"] == "None"):
            print(f"  - {r['command']}: {r['with_llm']['template']}")
    
    print("\n- Commands with different categorization:")
    for r in results:
        if (r["no_llm"]["category"] != r["with_llm"]["category"] and 
            r["no_llm"]["category"] != "N/A" and 
            r["with_llm"]["category"] != "N/A"):
            print(f"  - {r['command']}: {r['no_llm']['category']} -> {r['with_llm']['category']}")

if __name__ == "__main__":
    compare_schemas()
