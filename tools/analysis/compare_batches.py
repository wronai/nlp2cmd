#!/usr/bin/env python3
"""Compare batch results between LLM and non-LLM approaches."""

import json
from pathlib import Path


def compare_batch_files():
    """Compare results from batch files."""
    
    print("Batch Comparison Tool")
    print("=" * 60)
    
    # Find all batch files
    batch_files = {}
    for file in Path(".").glob("batch_*_results.json"):
        parts = file.stem.split("_")
        batch_num = int(parts[1])
        method = parts[2]
        
        if batch_num not in batch_files:
            batch_files[batch_num] = {}
        batch_files[batch_num][method] = file
    
    # Compare each batch
    for batch_num in sorted(batch_files.keys()):
        print(f"\nBatch {batch_num}:")
        print("-" * 40)
        
        if "no_llm" in batch_files[batch_num] and "llm" in batch_files[batch_num]:
            with open(batch_files[batch_num]["no_llm"]) as f:
                no_llm = json.load(f)
            with open(batch_files[batch_num]["llm"]) as f:
                with_llm = json.load(f)
            
            print(f"{'Command':<12} {'No LLM':<20} {'With LLM':<20} {'Better':<10}")
            print("-" * 62)
            
            for cmd in no_llm["commands"]:
                no_llm_schema = no_llm["schemas"].get(cmd, {})
                with_llm_schema = with_llm["schemas"].get(cmd, {})
                
                no_llm_template = no_llm_schema.get("template", "None")[:18]
                with_llm_template = with_llm_schema.get("template", "None")[:18]
                
                # Determine which is better
                better = "Tie"
                if no_llm_template == "None" and with_llm_template != "None":
                    better = "LLM"
                elif no_llm_template != "None" and with_llm_template == "None":
                    better = "No LLM"
                elif with_llm_schema.get("source_type") == "llm_enhanced":
                    better = "LLM"
                
                print(f"{cmd:<12} {no_llm_template:<20} {with_llm_template:<20} {better:<10}")
            
            # Summary
            no_llm_templates = no_llm["with_templates"]
            llm_templates = with_llm["with_templates"]
            
            print(f"\nBatch {batch_num} Summary:")
            print(f"  Templates - No LLM: {no_llm_templates}, With LLM: {llm_templates}")
            print(f"  Improvement: {llm_templates - no_llm_templates:+d} templates")
    
    # Overall comparison if quick test results exist
    if Path("quick_test_results.json").exists():
        print("\n" + "=" * 60)
        print("Quick Test Analysis (30 commands):")
        print("-" * 60)
        
        with open("quick_test_results.json") as f:
            results = json.load(f)
        
        # Group by source type
        source_types = {}
        for r in results:
            if r.get("success"):
                st = r.get("source_type", "unknown")
                if st not in source_types:
                    source_types[st] = []
                source_types[st].append(r)
        
        for st, cmds in source_types.items():
            with_templates = sum(1 for c in cmds if c.get("template"))
            print(f"\n{st}:")
            print(f"  Count: {len(cmds)}")
            print(f"  With templates: {with_templates}")
            print(f"  Examples:")
            for c in cmds[:3]:
                if c.get("template"):
                    print(f"    {c['command']}: {c['template']}")


if __name__ == "__main__":
    compare_batch_files()
