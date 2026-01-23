#!/usr/bin/env python3
"""Quick test of first 3 batches (30 commands)."""

import json
import time
from pathlib import Path

from nlp2cmd.schema_extraction import DynamicSchemaRegistry


def test_first_30():
    """Test first 30 commands in batches of 10."""
    
    # First 30 commands from config
    commands = [
        'find', 'grep', 'sed', 'awk', 'ls', 'mkdir', 'rm', 'cp', 'mv',
        'ps', 'top', 'kill', 'killall', 'systemctl', 'service', 'docker', 'docker-compose', 'kubectl', 'git',
        'curl', 'wget', 'ping', 'netstat', 'ss', 'lsof', 'df', 'du', 'free', 'uname'
    ]
    
    # Split into 3 batches
    batches = [commands[i:i+10] for i in range(0, 30, 10)]
    
    print("Quick Test - First 30 Commands in Batches of 10")
    print("=" * 60)
    
    # LLM config
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 1024,
    }
    
    all_results = []
    
    for i, batch in enumerate(batches, 1):
        print(f"\nBatch {i}: {', '.join(batch)}")
        print("-" * 60)
        
        # Test with LLM
        registry = DynamicSchemaRegistry(
            auto_save_path=f"./quick_batch_{i}_llm.json",
            use_llm=True,
            llm_config=llm_config
        )
        
        batch_results = []
        
        for cmd in batch:
            try:
                start = time.time()
                schema = registry.register_shell_help(cmd)
                duration = time.time() - start
                
                if schema.commands:
                    cmd_schema = schema.commands[0]
                    result = {
                        "command": cmd,
                        "success": True,
                        "source_type": cmd_schema.source_type,
                        "template": cmd_schema.template,
                        "category": cmd_schema.category,
                        "time": duration
                    }
                    print(f"  ✓ {cmd} ({duration:.1f}s) [{cmd_schema.source_type}]")
                    if cmd_schema.template:
                        print(f"    {cmd_schema.template}")
                else:
                    result = {"command": cmd, "success": False}
                    print(f"  ✗ {cmd}: No schema")
                    
            except Exception as e:
                result = {"command": cmd, "success": False, "error": str(e)}
                print(f"  ✗ {cmd}: {e}")
            
            batch_results.append(result)
        
        all_results.extend(batch_results)
        
        # Quick summary for batch
        successful = sum(1 for r in batch_results if r.get("success", False))
        with_templates = sum(1 for r in batch_results if r.get("template"))
        llm_enhanced = sum(1 for r in batch_results if r.get("source_type") == "llm_enhanced")
        
        print(f"\nBatch {i} Summary: {successful}/10 successful, {with_templates} with templates, {llm_enhanced} LLM enhanced")
    
    # Overall summary
    total_successful = sum(1 for r in all_results if r.get("success", False))
    total_templates = sum(1 for r in all_results if r.get("template"))
    total_llm = sum(1 for r in all_results if r.get("source_type") == "llm_enhanced")
    
    print("\n" + "=" * 60)
    print("Overall Summary:")
    print(f"  Total: 30 commands")
    print(f"  Successful: {total_successful}/30 ({total_successful/30*100:.1f}%)")
    print(f"  With templates: {total_templates}/30 ({total_templates/30*100:.1f}%)")
    print(f"  LLM enhanced: {total_llm}/30 ({total_llm/30*100:.1f}%)")
    
    # Save results
    with open("quick_test_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\nResults saved to: quick_test_results.json")


if __name__ == "__main__":
    test_first_30()
