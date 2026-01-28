#!/usr/bin/env python3
"""
End-to-End Example: LLM as Planner + Typed Actions

This example demonstrates the complete architecture:
1. User input → NLP Layer (intent + entities)
2. Decision Router → determines if LLM needed
3. LLM Planner → generates multi-step plan (if needed)
4. Plan Validator → validates against action registry
5. Plan Executor → executes typed actions
6. Result Aggregator → formats output

Key principle: LLM plans. Code executes. System controls.

📚 Related Documentation:
- https://github.com/wronai/nlp2cmd/blob/main/docs/guides/user-guide.md
- https://github.com/wronai/nlp2cmd/blob/main/docs/api/README.md
- https://github.com/wronai/nlp2cmd/blob/main/THERMODYNAMIC_INTEGRATION.md

🚀 More Examples:
- https://github.com/wronai/nlp2cmd/tree/main/examples/use_cases
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_rule, print_separator

from nlp2cmd import (
    # Core NLP
    NLP2CMD,
    # Router
    DecisionRouter,
    RoutingDecision,
    RouterConfig,
    # Registry
    ActionRegistry,
    get_registry,
    # Planner
    LLMPlanner,
    PlannerConfig,
    # Executor
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    # Aggregator
    ResultAggregator,
    OutputFormat,
)


def print_section(title: str) -> None:
    """Print section header."""
    print_separator(f"  {title}", leading_newline=True, width=60)
    print()


def print_step(step: str) -> None:
    """Print step indicator."""
    print(f"\n→ {step}")
    print_rule(width=40)


# =============================================================================
# Mock action handlers (in production, these would do real work)
# =============================================================================

def mock_sql_select(table: str, columns: list = None, filters: list = None, **kwargs) -> list:
    """Mock SQL SELECT handler."""
    # Simulate database query
    mock_data = {
        "users": [
            {"id": 1, "name": "Alice", "status": "active", "orders": 5},
            {"id": 2, "name": "Bob", "status": "active", "orders": 3},
            {"id": 3, "name": "Charlie", "status": "inactive", "orders": 0},
        ],
        "orders": [
            {"id": 101, "user_id": 1, "total": 150.00},
            {"id": 102, "user_id": 1, "total": 200.00},
            {"id": 103, "user_id": 2, "total": 75.00},
        ],
        "logs": [
            {"timestamp": "2025-01-01", "level": "ERROR", "message": "Connection failed"},
            {"timestamp": "2025-01-02", "level": "INFO", "message": "Service started"},
            {"timestamp": "2025-01-03", "level": "ERROR", "message": "Timeout"},
        ],
    }
    
    data = mock_data.get(table, [])
    
    # Apply filters
    if filters:
        for f in filters:
            if "status = 'active'" in f:
                data = [r for r in data if r.get("status") == "active"]
            if "level = 'ERROR'" in f:
                data = [r for r in data if r.get("level") == "ERROR"]
    
    return data


def mock_shell_find(glob: str = "*", path: str = ".", **kwargs) -> list:
    """Mock shell find handler."""
    if "*.log" in glob:
        return ["/var/log/app.log", "/var/log/error.log", "/var/log/access.log"]
    if "*.py" in glob:
        return ["main.py", "utils.py", "config.py"]
    return ["file1.txt", "file2.txt"]


def mock_shell_count_pattern(file: str, pattern: str, **kwargs) -> int:
    """Mock shell grep/count handler."""
    # Simulate counting patterns
    counts = {
        "/var/log/app.log": {"ERROR": 15, "WARNING": 42},
        "/var/log/error.log": {"ERROR": 127, "WARNING": 8},
        "/var/log/access.log": {"ERROR": 3, "WARNING": 5},
    }
    
    return counts.get(file, {}).get(pattern, 0)


def mock_k8s_get(resource: str, namespace: str = "default", **kwargs) -> list:
    """Mock kubectl get handler."""
    mock_resources = {
        "pods": [
            {"name": "api-server-abc", "status": "Running", "restarts": 0},
            {"name": "worker-xyz", "status": "Running", "restarts": 2},
        ],
        "deployments": [
            {"name": "api-server", "replicas": "3/3", "available": 3},
            {"name": "worker", "replicas": "2/2", "available": 2},
        ],
    }
    
    return mock_resources.get(resource, [])


# =============================================================================
# Main demonstration
# =============================================================================

def main():
    print_section("NLP2CMD: LLM as Planner + Typed Actions Demo")
    
    # =========================================================================
    # Step 1: Initialize components
    # =========================================================================
    print_step("Step 1: Initialize Components")
    
    # Decision Router
    router = DecisionRouter(RouterConfig(
        simple_intents=["select", "get", "list", "show"],
        complex_intents=["analyze", "compare", "report"],
        entity_threshold=5,
    ))
    
    # Action Registry (use global with builtins)
    registry = get_registry()
    
    # LLM Planner (no LLM client = uses rule-based fallback)
    planner = LLMPlanner(registry=registry)
    
    # Plan Executor with mock handlers
    executor = PlanExecutor(registry=registry)
    executor.register_handler("sql_select", mock_sql_select)
    executor.register_handler("shell_find", mock_shell_find)
    executor.register_handler("shell_count_pattern", mock_shell_count_pattern)
    executor.register_handler("k8s_get", mock_k8s_get)
    
    # Result Aggregator
    aggregator = ResultAggregator(default_format=OutputFormat.TEXT)
    
    print("✓ All components initialized")
    print(f"  - Registry has {len(registry.list_actions())} actions across {len(registry.list_domains())} domains")
    
    # =========================================================================
    # Example 1: Simple Query (Direct Execution)
    # =========================================================================
    print_section("Example 1: Simple Query → Direct Execution")
    
    query1 = "show all active users"
    print(f"User: \"{query1}\"")
    
    # Simulated NLP Layer output
    detected_intent = "select"
    detected_entities = {"table": "users", "filters": ["status = 'active'"]}
    
    print(f"\n📝 NLP Layer:")
    print(f"   Intent: {detected_intent}")
    print(f"   Entities: {detected_entities}")
    
    # Decision Router
    routing = router.route(
        intent=detected_intent,
        entities=detected_entities,
        text=query1,
        confidence=0.9,
    )
    print(f"\n🔀 Decision Router:")
    print(f"   Decision: {routing.decision.value}")
    print(f"   Reason: {routing.reason}")
    
    if routing.decision == RoutingDecision.DIRECT:
        # Direct execution - create simple plan
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "users",
                    "filters": ["status = 'active'"],
                },
            ),
        ])
    else:
        # Use LLM Planner
        planning_result = planner.plan(
            intent="select",
            entities={"table": "users", "filters": ["status = 'active'"]},
            text=query1,
        )
        plan = planning_result.plan
    
    print(f"\n📋 Execution Plan:")
    for i, step in enumerate(plan.steps):
        print(f"   {i+1}. {step.action}({step.params})")
    
    # Execute
    exec_result = executor.execute(plan)
    
    print(f"\n⚡ Execution Result:")
    print(f"   Success: {exec_result.success}")
    print(f"   Duration: {exec_result.total_duration_ms:.1f}ms")
    print(f"   Trace ID: {exec_result.trace_id}")
    
    # Aggregate
    aggregated = aggregator.aggregate(exec_result, format=OutputFormat.TABLE)
    print(f"\n📊 Final Output:\n{aggregated.data}")
    
    # =========================================================================
    # Example 2: Complex Query (LLM Planner)
    # =========================================================================
    print_section("Example 2: Complex Query → LLM Planner")
    
    query2 = "for each log file, count ERROR occurrences and then summarize"
    print(f"User: \"{query2}\"")
    
    # Decision Router - should route to LLM
    routing = router.route(
        intent="file_search",
        entities={"pattern": "ERROR", "glob": "*.log"},
        text=query2,
        confidence=0.85,
    )
    print(f"\n🔀 Decision Router:")
    print(f"   Decision: {routing.decision.value}")
    print(f"   Reason: {routing.reason}")
    
    # Manual multi-step plan (simulating LLM output)
    plan = ExecutionPlan(steps=[
        PlanStep(
            action="shell_find",
            params={"glob": "*.log"},
            store_as="log_files",
        ),
        PlanStep(
            action="shell_count_pattern",
            foreach="log_files",
            params={"file": "$item", "pattern": "ERROR"},
            store_as="error_counts",
        ),
        PlanStep(
            action="summarize_results",
            params={"data": "$error_counts"},
        ),
    ])
    
    print(f"\n📋 Multi-Step Execution Plan:")
    for i, step in enumerate(plan.steps):
        foreach = f" [foreach: {step.foreach}]" if step.foreach else ""
        print(f"   {i+1}. {step.action}{foreach}")
        print(f"      params: {step.params}")
        if step.store_as:
            print(f"      store_as: ${step.store_as}")
    
    # Execute multi-step plan
    exec_result = executor.execute(plan)
    
    print(f"\n⚡ Execution Result:")
    print(f"   Success: {exec_result.success}")
    print(f"   Steps: {len(exec_result.steps)}")
    
    for step_result in exec_result.steps:
        status_icon = "✓" if step_result.status.value == "success" else "✗"
        iter_info = f" ({step_result.iterations} iterations)" if step_result.iterations > 1 else ""
        print(f"   {status_icon} Step {step_result.step_index + 1}: {step_result.action}{iter_info}")
        if step_result.result:
            print(f"      Result: {step_result.result}")
    
    # Aggregate with summary
    aggregated = aggregator.aggregate(exec_result)
    print(f"\n📊 Summary:\n{aggregated.summary}")
    
    # =========================================================================
    # Example 3: Show Action Registry
    # =========================================================================
    print_section("Example 3: Action Registry Overview")
    
    print("📚 Registered Domains:")
    for domain in sorted(registry.list_domains()):
        actions = registry.list_actions(domain=domain)
        print(f"   {domain}: {len(actions)} actions")
    
    print("\n🔴 Destructive Actions (require confirmation):")
    for action_name in registry.get_destructive_actions():
        schema = registry.get(action_name)
        print(f"   - {action_name}: {schema.description}")
    
    # =========================================================================
    # Example 4: Plan Validation
    # =========================================================================
    print_section("Example 4: Plan Validation")
    
    # Valid plan
    valid_plan = ExecutionPlan(steps=[
        PlanStep(action="sql_select", params={"table": "users"}),
    ])
    
    is_valid, errors = executor.validator.validate(valid_plan)
    print(f"Valid Plan: ✓ {is_valid}")
    
    # Invalid plan
    invalid_plan = ExecutionPlan(steps=[
        PlanStep(action="nonexistent_action", params={}),
    ])
    
    is_valid, errors = executor.validator.validate(invalid_plan)
    print(f"\nInvalid Plan: ✗ {is_valid}")
    print(f"   Errors: {errors}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_section("Architecture Summary")
    
    print("""
    ┌─────────────────┐
    │   User Query    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   NLP Layer     │ → Intent + Entities
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Decision Router │ → Direct OR LLM Planner?
    └────────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐   ┌─────────────┐
│  Direct  │   │ LLM Planner │ → JSON Plan
└────┬─────┘   └──────┬──────┘
     │                │
     └───────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Plan Validator  │ → Check against Action Registry
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Plan Executor  │ → Execute Typed Actions
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │Result Aggregator│ → Format Output
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   User Output   │
    └─────────────────┘

    Key Principles:
    ✓ LLM plans, Code executes
    ✓ Typed actions (no eval/shell)
    ✓ Allowlist of actions
    ✓ Full validation before execution
    ✓ Traceable execution (trace_id per request)
    """)


if __name__ == "__main__":
    main()
