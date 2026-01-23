#!/usr/bin/env python3
"""Test schema generation for 100 commands with and without LLM."""

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


def test_schema_generation(use_llm: bool, output_suffix: str) -> Dict:
    """Test schema generation for all commands."""
    config = load_config()
    commands = config.get("test_commands", [])
    
    print(f"\n{'='*60}")
    print(f"Testing {'WITH' if use_llm else 'WITHOUT'} LLM")
    print(f"Commands to test: {len(commands)}")
    print(f"{'='*60}")
    
    # Initialize registry
    llm_config = config.get("schema_generation", {}).get("llm", {}) if use_llm else None
    registry = DynamicSchemaRegistry(
        auto_save_path=f"./schemas_{output_suffix}.json",
        use_llm=use_llm,
        llm_config=llm_config
    )
    
    results = {
        "total": len(commands),
        "successful": 0,
        "failed": 0,
        "with_templates": 0,
        "errors": [],
        "timing": {
            "start": time.time(),
            "end": None,
            "duration": None
        }
    }
    
    # Process commands in batches
    batch_size = config.get("schema_generation", {}).get("batch_size", 10)
    
    for i in range(0, len(commands), batch_size):
        batch = commands[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(commands)-1)//batch_size + 1}")
        
        for cmd in batch:
            try:
                start_time = time.time()
                schema = registry.register_shell_help(cmd)
                end_time = time.time()
                
                results["successful"] += 1
                
                # Check if template was generated
                if schema.commands and schema.commands[0].template:
                    results["with_templates"] += 1
                
                print(f"  ✓ {cmd} ({end_time - start_time:.2f}s)", end="")
                if schema.commands and schema.commands[0].template:
                    print(f" [template: {schema.commands[0].template[:30]}...]")
                else:
                    print()
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"command": cmd, "error": str(e)})
                print(f"  ✗ {cmd}: {e}")
    
    results["timing"]["end"] = time.time()
    results["timing"]["duration"] = results["timing"]["end"] - results["timing"]["start"]
    
    # Save detailed results
    results_file = Path(f"test_results_{output_suffix}.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY ({'WITH' if use_llm else 'WITHOUT'} LLM)")
    print(f"{'='*60}")
    print(f"Total commands: {results['total']}")
    print(f"Successful: {results['successful']} ({results['successful']/results['total']*100:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print(f"With templates: {results['with_templates']} ({results['with_templates']/results['total']*100:.1f}%)")
    print(f"Total time: {results['timing']['duration']:.2f}s")
    print(f"Average per command: {results['timing']['duration']/results['total']:.2f}s")
    
    if results["errors"]:
        print(f"\nFailed commands:")
        for error in results["errors"][:10]:  # Show first 10
            print(f"  - {error['command']}: {error['error']}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")
    
    return results


def compare_results():
    """Compare results between LLM and non-LLM approaches."""
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}")
    
    # Load results
    with open("test_results_no_llm.json", 'r') as f:
        no_llm = json.load(f)
    
    with open("test_results_with_llm.json", 'r') as f:
        with_llm = json.load(f)
    
    # Compare metrics
    print(f"{'Metric':<20} {'No LLM':<15} {'With LLM':<15} {'Improvement':<15}")
    print("-" * 65)
    
    metrics = [
        ("Success rate", no_llm["successful"]/no_llm["total"], with_llm["successful"]/with_llm["total"]),
        ("Template rate", no_llm["with_templates"]/no_llm["total"], with_llm["with_templates"]/with_llm["total"]),
        ("Avg time (s)", no_llm["timing"]["duration"]/no_llm["total"], with_llm["timing"]["duration"]/with_llm["total"]),
    ]
    
    for metric, no_val, with_val in metrics:
        if metric == "Avg time (s)":
            improvement = f"{(no_val/with_val - 1)*100:.1f}%" if with_val > 0 else "N/A"
        else:
            improvement = f"{(with_val - no_val)*100:.1f}%"
        print(f"{metric:<20} {no_val*100:<15.1f}% {with_val*100:<15.1f}% {improvement:<15}")
    
    # Show examples of improved templates
    print(f"\n{'='*60}")
    print("EXAMPLE IMPROVEMENTS")
    print(f"{'='*60}")
    
    # Load schemas for comparison
    with open("./schemas_no_llm.json", 'r') as f:
        no_llm_schemas = json.load(f)
    
    with open("./schemas_with_llm.json", 'r') as f:
        with_llm_schemas = json.load(f)
    
    improvements = []
    for cmd in no_llm_schemas["schemas"]:
        if cmd in with_llm_schemas["schemas"]:
            no_template = no_llm_schemas["schemas"][cmd]["commands"][0].get("template")
            with_template = with_llm_schemas["schemas"][cmd]["commands"][0].get("template")
            
            if no_template != with_template and with_template:
                improvements.append((cmd, no_template, with_template))
    
    # Show top improvements
    for cmd, no_template, with_template in improvements[:10]:
        print(f"\n{cmd}:")
        print(f"  Without LLM: {no_template or 'None'}")
        print(f"  With LLM:    {with_template}")


def main():
    """Main test function."""
    print("NLP2CMD Schema Generation Test")
    print("Testing 100 commands with and without LLM assistance")
    
    # Test without LLM
    no_llm_results = test_schema_generation(use_llm=False, output_suffix="no_llm")
    
    # Test with LLM
    with_llm_results = test_schema_generation(use_llm=True, output_suffix="with_llm")
    
    # Compare results
    compare_results()


if __name__ == "__main__":
    main()
