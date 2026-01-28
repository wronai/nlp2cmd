#!/usr/bin/env python3
"""
Example: Log Analysis Pipeline

Demonstrates a multi-step log analysis workflow:
1. Find all log files
2. Count ERROR patterns in each
3. Count WARNING patterns in each
4. Generate summary report

Shows how to use foreach loops and variable references.
"""
import sys
from pathlib import Path

from nlp2cmd import (
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    ResultAggregator,
    OutputFormat,
    get_registry,
)

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_rule, print_separator

def mock_find_logs(**kwargs):
    """Mock: Find log files."""
    return [
        "/var/log/app.log",
        "/var/log/error.log",
        "/var/log/access.log",
        "/var/log/debug.log",
    ]


def mock_count_pattern(file: str, pattern: str, **kwargs):
    """Mock: Count pattern occurrences in file."""
    # Simulated counts for demonstration
    counts = {
        "/var/log/app.log": {"ERROR": 15, "WARNING": 42, "INFO": 230},
        "/var/log/error.log": {"ERROR": 127, "WARNING": 8, "INFO": 5},
        "/var/log/access.log": {"ERROR": 3, "WARNING": 5, "INFO": 1500},
        "/var/log/debug.log": {"ERROR": 0, "WARNING": 12, "INFO": 890},
    }
    return counts.get(file, {}).get(pattern, 0)


def mock_read_file(path: str, **kwargs):
    """Mock: Read file contents."""
    return f"Contents of {path}"


def main():
    print_separator("  Log Analysis Pipeline Example", width=60)
    
    # Initialize
    registry = get_registry()
    executor = PlanExecutor(registry=registry)
    aggregator = ResultAggregator()
    
    # Register mock handlers
    executor.register_handler("shell_find", mock_find_logs)
    executor.register_handler("shell_count_pattern", mock_count_pattern)
    executor.register_handler("shell_read_file", mock_read_file)
    
    # Define the analysis plan
    plan = ExecutionPlan(
        steps=[
            # Step 1: Find all log files
            PlanStep(
                action="shell_find",
                params={"glob": "*.log", "path": "/var/log"},
                store_as="log_files",
            ),
            
            # Step 2: Count ERROR in each file
            PlanStep(
                action="shell_count_pattern",
                foreach="log_files",
                params={"file": "$item", "pattern": "ERROR"},
                store_as="error_counts",
            ),
            
            # Step 3: Count WARNING in each file
            PlanStep(
                action="shell_count_pattern",
                foreach="log_files",
                params={"file": "$item", "pattern": "WARNING"},
                store_as="warning_counts",
            ),
            
            # Step 4: Summarize
            PlanStep(
                action="summarize_results",
                params={"data": "$error_counts"},
                store_as="summary",
            ),
        ],
        metadata={
            "name": "Log Analysis Pipeline",
            "description": "Analyze ERROR and WARNING patterns across log files",
        }
    )
    
    print("\n📋 Execution Plan:")
    print_rule(width=40)
    for i, step in enumerate(plan.steps, 1):
        foreach = f" [foreach: ${step.foreach}]" if step.foreach else ""
        print(f"  {i}. {step.action}{foreach}")
        print(f"     params: {step.params}")
        if step.store_as:
            print(f"     → store as: ${step.store_as}")
    
    # Execute
    print("\n⚡ Executing...")
    print_rule(width=40)
    result = executor.execute(plan)
    
    # Show results
    print(f"\n✅ Execution Complete")
    print(f"   Trace ID: {result.trace_id}")
    print(f"   Duration: {result.total_duration_ms:.2f}ms")
    print(f"   Success: {result.success}")
    
    print("\n📊 Step Results:")
    print_rule(width=40)
    
    for step_result in result.steps:
        status_icon = "✓" if step_result.status.value == "success" else "✗"
        iterations = f" ({step_result.iterations} files)" if step_result.iterations > 1 else ""
        
        print(f"\n  {status_icon} {step_result.action}{iterations}")
        print(f"     Duration: {step_result.duration_ms:.2f}ms")
        
        if step_result.result:
            # Format result based on type
            if isinstance(step_result.result, list):
                if len(step_result.result) <= 5:
                    print(f"     Result: {step_result.result}")
                else:
                    print(f"     Result: {step_result.result[:3]}... ({len(step_result.result)} items)")
            else:
                print(f"     Result: {step_result.result}")
    
    # Generate formatted output
    print("\n📈 Analysis Summary:")
    print_rule(width=40)
    
    # Get the counts from context
    log_files = result.steps[0].result
    error_counts = result.steps[1].result
    warning_counts = result.steps[2].result
    
    print(f"\n{'File':<30} {'ERRORs':<10} {'WARNINGs':<10}")
    print_rule(width=50)
    
    total_errors = 0
    total_warnings = 0
    
    for i, (file, errors, warnings) in enumerate(zip(log_files, error_counts, warning_counts)):
        filename = file.split("/")[-1]
        print(f"{filename:<30} {errors:<10} {warnings:<10}")
        total_errors += errors
        total_warnings += warnings
    
    print_rule(width=50)
    print(f"{'TOTAL':<30} {total_errors:<10} {total_warnings:<10}")
    
    # Critical threshold check
    print("\n🚨 Critical Issues:")
    print_rule(width=40)
    
    for i, (file, errors) in enumerate(zip(log_files, error_counts)):
        if errors > 100:
            print(f"  ⚠️  {file}: {errors} errors (CRITICAL)")
        elif errors > 50:
            print(f"  ⚡ {file}: {errors} errors (HIGH)")
    
    if total_errors == 0:
        print("  ✅ No critical issues found")


if __name__ == "__main__":
    main()
