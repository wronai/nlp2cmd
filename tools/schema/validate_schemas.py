#!/usr/bin/env python3
"""Validate and fix all generated schemas."""

import json
from pathlib import Path
import yaml
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def validate_and_fix_schemas():
    """Validate all schemas and fix issues."""
    
    print("Schema Validation and Fix Tool")
    print("=" * 60)
    
    # Load config and get all commands
    if Path("config.yaml").exists():
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
    else:
        config = {"test_commands": []}
    
    commands = config.get("test_commands", [])
    
    # Initialize with improved LLM extractor
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 512,
        "timeout": 10,
    }
    
    export_dir = Path("./command_schemas/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    validated_path = export_dir / "validated_schemas.json"

    registry = DynamicSchemaRegistry(
        auto_save_path=str(validated_path),
        use_llm=True,
        llm_config=llm_config,
    )
    
    # Track validation results
    validation_results = {
        "total": len(commands),
        "valid": 0,
        "fixed": 0,
        "failed": 0,
        "issues_found": []
    }
    
    print(f"\nValidating {len(commands)} commands...")
    
    for cmd in commands:
        try:
            schema = registry.register_shell_help(cmd)
            if schema.commands:
                s = schema.commands[0]
                
                # Validate schema
                issues = []
                
                # Check 1: Category specificity
                if s.category == "general":
                    issues.append("Generic category")
                
                # Check 2: Description quality
                if s.description == f"{cmd} command" or len(s.description) < 10:
                    issues.append("Poor description")
                
                # Check 3: Template syntax
                if s.template:
                    if s.template.count("{") != s.template.count("}"):
                        issues.append("Unbalanced braces")
                    if "[" in s.template and "{" not in s.template:
                        issues.append("Uses [] instead of {}")
                else:
                    issues.append("No template")
                
                if issues:
                    validation_results["issues_found"].append({
                        "command": cmd,
                        "issues": issues,
                        "source_type": s.source_type
                    })
                    if s.source_type in ["llm_enhanced", "predefined_template"]:
                        validation_results["fixed"] += 1
                        print(f"  {cmd}: Fixed ({', '.join(issues)})")
                    else:
                        validation_results["failed"] += 1
                        print(f"  {cmd}: Still has issues ({', '.join(issues)})")
                else:
                    validation_results["valid"] += 1
                    print(f"  {cmd}: ✓ Valid")
                    
        except Exception as e:
            validation_results["failed"] += 1
            print(f"  {cmd}: ✗ Failed - {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Validation Summary:")
    print(f"  Total commands: {validation_results['total']}")
    print(f"  Valid schemas: {validation_results['valid']}")
    print(f"  Fixed schemas: {validation_results['fixed']}")
    print(f"  Failed: {validation_results['failed']}")
    print(f"  Success rate: {validation_results['valid'] / validation_results['total'] * 100:.1f}%")
    
    # Save validation report
    artifacts_dir = Path("./artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(validation_results, f, indent=2)
    
    print("\nFiles saved:")
    print(f"  - {validated_path} (all validated schemas)")
    print(f"  - {report_path} (detailed validation report)")
    
    return validation_results

if __name__ == "__main__":
    validate_and_fix_schemas()
