#!/usr/bin/env python3
"""Test NLP2CMD command generation with validated schemas."""

import json
from pathlib import Path
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

def test_command_generation():
    """Test if NLP2CMD correctly generates commands using schemas."""
    
    print("Testing NLP2CMD Command Generation")
    print("=" * 60)
    
    # Test cases: query -> expected command pattern
    test_cases = [
        # File operations
        ("Find files larger than 100MB", "find"),
        ("Search for TODO in Python files", "grep"),
        ("Compress logs directory", "tar"),
        ("Copy file to backup", "cp"),
        ("Move old files to archive", "mv"),
        ("Remove temporary files", "rm"),
        
        # System monitoring
        ("Show running processes", "ps"),
        ("Check disk usage", "df"),
        ("Check memory usage", "free"),
        ("Show system uptime", "uptime"),
        
        # Network
        ("Test connection to google.com", "ping"),
        ("Download file from URL", "wget"),
        ("Check network connections", "netstat"),
        
        # Development
        ("Check git status", "git"),
        ("List Docker containers", "docker"),
        ("Check Kubernetes pods", "kubectl"),
    ]
    
    # Initialize registry with schemas
    llm_config = {
        "model": "ollama/qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "max_tokens": 512,
        "timeout": 10,
    }
    
    registry = DynamicSchemaRegistry(
        auto_save_path="./test_schemas.json",
        use_llm=True,
        llm_config=llm_config
    )
    
    # Load schemas for test commands
    test_commands = list(set([case[1] for case in test_cases]))
    print(f"\nLoading schemas for {len(test_commands)} commands...")
    
    for cmd in test_commands:
        try:
            registry.register_shell_help(cmd)
            print(f"  ✓ {cmd}")
        except Exception as e:
            print(f"  ✗ {cmd}: {e}")
    
    # Create NLP2CMD instance
    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test command generation
    print(f"\nTesting {len(test_cases)} queries:")
    print("-" * 60)
    
    results = {
        "total": len(test_cases),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for query, expected_cmd in test_cases:
        print(f"\nQuery: {query}")
        try:
            result = nlp.transform(query)
            generated_cmd = result.command
            
            # Check if expected command is in generated command
            if expected_cmd in generated_cmd:
                print(f"  ✓ Generated: {generated_cmd}")
                results["success"] += 1
            else:
                print(f"  ⚠ Generated: {generated_cmd} (expected {expected_cmd})")
                results["failed"] += 1
                results["errors"].append({
                    "query": query,
                    "expected": expected_cmd,
                    "generated": generated_cmd
                })
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results["failed"] += 1
            results["errors"].append({
                "query": query,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Total queries: {results['total']}")
    print(f"  Successful: {results['success']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success rate: {results['success']/results['total']*100:.1f}%")
    
    if results["errors"]:
        print("\nFailed cases:")
        for error in results["errors"][:5]:  # Show first 5
            if "error" in error:
                print(f"  - {error['query']}: {error['error']}")
            else:
                print(f"  - {error['query']}: expected '{error['expected']}', got '{error['generated']}'")
    
    # Save results
    with open("command_generation_test.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def test_template_usage():
    """Test if templates are being used correctly."""
    print("\n" + "=" * 60)
    print("Testing Template Usage")
    print("=" * 60)
    
    # Load schemas
    with open("test_schemas.json") as f:
        schemas = json.load(f)
    
    print("\nCommands with templates:")
    for cmd, schema in schemas["schemas"].items():
        template = schema["commands"][0].get("template")
        if template:
            print(f"  {cmd}: {template}")
    
    # Test specific template substitutions
    test_substitutions = [
        ("Find Python files", "find", "find {path} -name \"*.py\""),
        ("Search for error in logs", "grep", "grep {pattern} {path}"),
        ("Compress backup folder", "tar", "tar -czf {archive}.tar.gz {source}"),
    ]
    
    print("\nTesting template substitutions:")
    adapter = DynamicAdapter(schema_registry=DynamicSchemaRegistry())
    
    # Load schemas
    registry = DynamicSchemaRegistry(auto_save_path="./test_schemas.json")
    for cmd in ["find", "grep", "tar"]:
        try:
            schema = registry.register_shell_help(cmd)
            adapter.registry.register_shell_help(cmd)
        except:
            pass
    
    nlp = NLP2CMD(adapter=adapter)
    
    for query, cmd, expected_pattern in test_substitutions:
        print(f"\nQuery: {query}")
        try:
            result = nlp.transform(query)
            print(f"  Generated: {result.command}")
            print(f"  Expected pattern: {expected_pattern}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    # Run tests
    results = test_command_generation()
    test_template_usage()
    
    print(f"\nOverall: {'Tests completed successfully' if results['success'] > results['failed'] else 'Some tests failed'}")
