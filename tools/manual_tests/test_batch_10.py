#!/usr/bin/env python3
"""Test schema generation in batches of 10 commands."""

import json
import time
from pathlib import Path
from typing import Dict, List

import yaml

from nlp2cmd.schema_extraction import DynamicSchemaRegistry


def load_config() -> Dict:
    """Load configuration from YAML file."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def test_batch(commands: List[str], batch_num: int, use_llm: bool, llm_config: Dict = None) -> Dict:
    """Test a batch of commands."""
    print(f"\n{'='*60}")
    print(f"Batch {batch_num} - Testing {'WITH' if use_llm else 'WITHOUT'} LLM")
    print(f"Commands: {', '.join(commands)}")
    print(f"{'='*60}")
    
    # Initialize registry
    registry = DynamicSchemaRegistry(
        auto_save_path=f"./batch_{batch_num}_{'llm' if use_llm else 'no_llm'}.json",
        use_llm=use_llm,
        llm_config=llm_config
    )
    
    results = {
        "batch": batch_num,
        "commands": commands,
        "use_llm": use_llm,
        "successful": 0,
        "failed": 0,
        "with_templates": 0,
        "errors": [],
        "timing": {
            "start": time.time(),
            "end": None,
            "duration": None
        },
        "schemas": {}
    }
    
    # Process each command
    for cmd in commands:
        try:
            start_time = time.time()
            schema = registry.register_shell_help(cmd)
            end_time = time.time()
            
            results["successful"] += 1
            
            # Store schema details
            if schema.commands:
                cmd_schema = schema.commands[0]
                results["schemas"][cmd] = {
                    "source_type": cmd_schema.source_type,
                    "template": cmd_schema.template,
                    "category": cmd_schema.category,
                    "parameters_count": len(cmd_schema.parameters),
                    "description": cmd_schema.description[:100] + "..." if len(cmd_schema.description) > 100 else cmd_schema.description,
                    "extraction_time": end_time - start_time
                }
                
                if cmd_schema.template:
                    results["with_templates"] += 1
                
                print(f"  ✓ {cmd} ({end_time - start_time:.2f}s) [{cmd_schema.source_type}]")
                if cmd_schema.template:
                    print(f"    Template: {cmd_schema.template}")
                    
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"command": cmd, "error": str(e)})
            print(f"  ✗ {cmd}: {e}")
    
    results["timing"]["end"] = time.time()
    results["timing"]["duration"] = results["timing"]["end"] - results["timing"]["start"]
    
    # Save batch results
    batch_file = Path(f"batch_{batch_num}_{'llm' if use_llm else 'no_llm'}_results.json")
    with open(batch_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print batch summary
    print(f"\nBatch {batch_num} Summary:")
    print(f"  Successful: {results['successful']}/{len(commands)}")
    print(f"  With templates: {results['with_templates']}")
    print(f"  Time: {results['timing']['duration']:.2f}s")
    
    return results


def main():
    """Main test function."""
    config = load_config()
    all_commands = config.get("test_commands", [])
    
    # Split into batches of 10
    batch_size = 10
    batches = [all_commands[i:i+batch_size] for i in range(0, len(all_commands), batch_size)]
    
    print(f"NLP2CMD Batch Testing")
    print(f"Total commands: {len(all_commands)}")
    print(f"Batch size: {batch_size}")
    print(f"Number of batches: {len(batches)}")
    
    # Configuration for LLM
    llm_config = config.get("schema_generation", {}).get("llm", {})
    
    # Test all batches
    all_results = {"no_llm": [], "with_llm": []}
    
    for i, batch in enumerate(batches, 1):
        print(f"\n{'#'*80}")
        print(f"# PROCESSING BATCH {i}/{len(batches)}")
        print(f"{'#'*80}")
        
        # Test without LLM
        no_llm_result = test_batch(batch, i, use_llm=False)
        all_results["no_llm"].append(no_llm_result)
        
        # Test with LLM
        with_llm_result = test_batch(batch, i, use_llm=True, llm_config=llm_config)
        all_results["with_llm"].append(with_llm_result)
        
        # Small pause between batches
        time.sleep(1)
    
    # Generate summary report
    print(f"\n{'#'*80}")
    print(f"# FINAL SUMMARY")
    print(f"{'#'*80}")
    
    summary = {
        "total_commands": len(all_commands),
        "total_batches": len(batches),
        "no_llm": {
            "total_successful": sum(r["successful"] for r in all_results["no_llm"]),
            "total_with_templates": sum(r["with_templates"] for r in all_results["no_llm"]),
            "total_time": sum(r["timing"]["duration"] for r in all_results["no_llm"]),
        },
        "with_llm": {
            "total_successful": sum(r["successful"] for r in all_results["with_llm"]),
            "total_with_templates": sum(r["with_templates"] for r in all_results["with_llm"]),
            "total_time": sum(r["timing"]["duration"] for r in all_results["with_llm"]),
        }
    }
    
    print(f"\nOverall Results:")
    print(f"{'Metric':<25} {'No LLM':<15} {'With LLM':<15} {'Improvement':<15}")
    print("-" * 70)
    
    # Success rate
    no_llm_rate = summary["no_llm"]["total_successful"] / summary["total_commands"] * 100
    with_llm_rate = summary["with_llm"]["total_successful"] / summary["total_commands"] * 100
    print(f"{'Success Rate':<25} {no_llm_rate:<15.1f}% {with_llm_rate:<15.1f}% {with_llm_rate-no_llm_rate:+.1f}%")
    
    # Template rate
    no_llm_template_rate = summary["no_llm"]["total_with_templates"] / summary["total_commands"] * 100
    with_llm_template_rate = summary["with_llm"]["total_with_templates"] / summary["total_commands"] * 100
    print(f"{'Template Rate':<25} {no_llm_template_rate:<15.1f}% {with_llm_template_rate:<15.1f}% {with_llm_template_rate-no_llm_template_rate:+.1f}%")
    
    # Time
    no_llm_avg_time = summary["no_llm"]["total_time"] / summary["total_commands"]
    with_llm_avg_time = summary["with_llm"]["total_time"] / summary["total_commands"]
    time_improvement = (no_llm_avg_time / with_llm_avg_time - 1) * 100 if with_llm_avg_time > 0 else 0
    print(f"{'Avg Time/Command':<25} {no_llm_avg_time:<15.2f}s {with_llm_avg_time:<15.2f}s {time_improvement:+.1f}%")
    
    # Save summary
    summary_file = Path("batch_test_summary.json")
    with open(summary_file, 'w') as f:
        json.dump({
            "summary": summary,
            "detailed_results": all_results
        }, f, indent=2)
    
    print(f"\nFiles generated:")
    print(f"  - batch_*_no_llm.json (schemas without LLM)")
    print(f"  - batch_*_llm.json (schemas with LLM)")
    print(f"  - batch_*_no_llm_results.json (results without LLM)")
    print(f"  - batch_*_llm_results.json (results with LLM)")
    print(f"  - batch_test_summary.json (overall summary)")


if __name__ == "__main__":
    main()
