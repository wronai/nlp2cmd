#!/usr/bin/env python3
"""
Example: Infrastructure Health Check

Demonstrates checking health across multiple infrastructure layers:
- Docker containers
- Kubernetes pods
- Database connections
- System resources

Shows cross-domain workflows and result aggregation.
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
    ActionSchema,
    ParamSchema,
    ParamType,
)

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_rule, print_separator
 
 
# =============================================================================
# Mock Handlers
# =============================================================================
 
def mock_docker_ps(**kwargs):
    """Mock: List Docker containers."""
    return [
        {"id": "abc123", "name": "web-1", "status": "running", "cpu": "2.1%", "memory": "256MB"},
        {"id": "def456", "name": "api-1", "status": "running", "cpu": "15.3%", "memory": "512MB"},
        {"id": "ghi789", "name": "db-1", "status": "running", "cpu": "8.2%", "memory": "1.2GB"},
        {"id": "jkl012", "name": "cache-1", "status": "running", "cpu": "0.5%", "memory": "128MB"},
    ]
 
 
def mock_k8s_get(resource: str, **kwargs):
    """Mock: Get Kubernetes resources."""
    resources = {
        "pods": [
            {"name": "api-server-abc", "status": "Running", "restarts": 0, "node": "node-1"},
            {"name": "api-server-def", "status": "Running", "restarts": 1, "node": "node-2"},
            {"name": "worker-ghi", "status": "Running", "restarts": 0, "node": "node-1"},
            {"name": "worker-jkl", "status": "CrashLoopBackOff", "restarts": 5, "node": "node-3"},
        ],
        "deployments": [
            {"name": "api-server", "ready": "2/2", "available": 2},
            {"name": "worker", "ready": "1/2", "available": 1},
        ],
        "nodes": [
            {"name": "node-1", "status": "Ready", "cpu": "45%", "memory": "60%"},
            {"name": "node-2", "status": "Ready", "cpu": "30%", "memory": "40%"},
            {"name": "node-3", "status": "NotReady", "cpu": "95%", "memory": "90%"},
        ],
    }
    return resources.get(resource, [])
 
 
def mock_sql_select(table: str, **kwargs):
    """Mock: SQL query."""
    if table == "health_checks":
        return [
            {"service": "database", "status": "healthy", "latency_ms": 5},
            {"service": "cache", "status": "healthy", "latency_ms": 2},
            {"service": "queue", "status": "degraded", "latency_ms": 150},
        ]
    return []
 
 
def mock_process_list(**kwargs):
    """Mock: System process list."""
    return [
        {"pid": 1, "name": "systemd", "cpu": 0.1, "memory": 0.5},
        {"pid": 1234, "name": "python", "cpu": 15.2, "memory": 8.3},
        {"pid": 5678, "name": "nginx", "cpu": 2.1, "memory": 1.2},
        {"pid": 9012, "name": "postgres", "cpu": 5.5, "memory": 12.4},
    ]
 
 
def check_health(data, **kwargs):
    """Custom handler: Analyze health status."""
    issues = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Check for unhealthy pods
                if item.get("status") == "CrashLoopBackOff":
                    issues.append(f"Pod {item.get('name')} is crashing")
                if item.get("restarts", 0) > 3:
                    issues.append(f"Pod {item.get('name')} has high restarts: {item.get('restarts')}")
                # Check for unhealthy nodes
                if item.get("status") == "NotReady":
                    issues.append(f"Node {item.get('name')} is not ready")
                # Check for degraded services
                if item.get("status") == "degraded":
                    issues.append(f"Service {item.get('service')} is degraded")
    
    return {
        "total_items": len(data) if isinstance(data, list) else 1,
        "issues_found": len(issues),
        "issues": issues,
        "status": "CRITICAL" if len(issues) > 2 else "WARNING" if issues else "HEALTHY",
    }
 
 
def main():
    print_separator("  Infrastructure Health Check", width=60)
    
    # Initialize
    registry = get_registry()
    executor = PlanExecutor(registry=registry)
    aggregator = ResultAggregator()
    
    # Register mock handlers
    executor.register_handler("docker_ps", mock_docker_ps)
    executor.register_handler("k8s_get", mock_k8s_get)
    executor.register_handler("sql_select", mock_sql_select)
    executor.register_handler("shell_process_list", mock_process_list)
    
    # Register custom health check action
    registry.register(ActionSchema(
        name="check_health",
        description="Analyze health status of resources",
        domain="utility",
        params=[ParamSchema(name="data", type=ParamType.ANY)],
        returns=ParamType.DICT,
    ))
    executor.register_handler("check_health", check_health)
    
    # Define health check plan
    plan = ExecutionPlan(
        steps=[
            # Check Docker containers
            PlanStep(
                action="docker_ps",
                params={},
                store_as="containers",
            ),
            
            # Check Kubernetes pods
            PlanStep(
                action="k8s_get",
                params={"resource": "pods"},
                store_as="pods",
            ),
            
            # Check Kubernetes nodes
            PlanStep(
                action="k8s_get",
                params={"resource": "nodes"},
                store_as="nodes",
            ),
            
            # Check service health from database
            PlanStep(
                action="sql_select",
                params={"table": "health_checks"},
                store_as="services",
            ),
            
            # Analyze pod health
            PlanStep(
                action="check_health",
                params={"data": "$pods"},
                store_as="pod_health",
            ),
            
            # Analyze node health
            PlanStep(
                action="check_health",
                params={"data": "$nodes"},
                store_as="node_health",
            ),
            
            # Analyze service health
            PlanStep(
                action="check_health",
                params={"data": "$services"},
                store_as="service_health",
            ),
        ],
        metadata={
            "name": "Infrastructure Health Check",
            "version": "1.0",
        }
    )
    
    print("\n📋 Health Check Plan:")
    print_rule(width=40)
    print(f"  Steps: {len(plan.steps)}")
    print(f"  Domains: Docker, Kubernetes, SQL")
    
    # Execute
    print("\n⚡ Running health checks...")
    result = executor.execute(plan)
    
    print(f"\n✅ Checks Complete")
    print(f"   Trace ID: {result.trace_id}")
    print(f"   Duration: {result.total_duration_ms:.2f}ms")
    
    # Extract results
    containers = result.steps[0].result
    pods = result.steps[1].result
    nodes = result.steps[2].result
    services = result.steps[3].result
    pod_health = result.steps[4].result
    node_health = result.steps[5].result
    service_health = result.steps[6].result
    
    # Display Docker status
    print("\n🐳 Docker Containers:")
    print_rule(width=40)
    print(f"  Running: {len(containers)}")
    for c in containers:
        print(f"    • {c['name']}: {c['status']} (CPU: {c['cpu']}, Mem: {c['memory']})")
    
    # Display Kubernetes status
    print("\n☸️  Kubernetes Pods:")
    print_rule(width=40)
    running = len([p for p in pods if p["status"] == "Running"])
    print(f"  Running: {running}/{len(pods)}")
    for p in pods:
        icon = "✓" if p["status"] == "Running" else "✗"
        restarts = f" (restarts: {p['restarts']})" if p["restarts"] > 0 else ""
        print(f"    {icon} {p['name']}: {p['status']}{restarts}")
    
    print("\n🖥️  Kubernetes Nodes:")
    print_rule(width=40)
    for n in nodes:
        icon = "✓" if n["status"] == "Ready" else "✗"
        print(f"    {icon} {n['name']}: {n['status']} (CPU: {n['cpu']}, Mem: {n['memory']})")
    
    # Display service health
    print("\n🔌 Service Health:")
    print_rule(width=40)
    for s in services:
        icon = "✓" if s["status"] == "healthy" else "⚠️"
        print(f"    {icon} {s['service']}: {s['status']} ({s['latency_ms']}ms)")
    
    # Overall health summary
    print_separator("  HEALTH SUMMARY", leading_newline=True, width=60)
    
    all_health = [pod_health, node_health, service_health]
    total_issues = sum(h["issues_found"] for h in all_health)
    
    print(f"\n  {'Component':<20} {'Status':<12} {'Issues':<10}")
    print_rule(width=42, indent="  ")
    print(f"  {'Pods':<20} {pod_health['status']:<12} {pod_health['issues_found']:<10}")
    print(f"  {'Nodes':<20} {node_health['status']:<12} {node_health['issues_found']:<10}")
    print(f"  {'Services':<20} {service_health['status']:<12} {service_health['issues_found']:<10}")
    print_rule(width=42, indent="  ")
    
    overall_status = "CRITICAL" if total_issues > 3 else "WARNING" if total_issues > 0 else "HEALTHY"
    status_icon = "🔴" if overall_status == "CRITICAL" else "🟡" if overall_status == "WARNING" else "🟢"
    
    print(f"\n  {status_icon} Overall Status: {overall_status}")
    print(f"     Total Issues: {total_issues}")
    
    # List all issues
    if total_issues > 0:
        print("\n  ⚠️  Issues Found:")
        for health in all_health:
            for issue in health["issues"]:
                print(f"      • {issue}")


if __name__ == "__main__":
    main()
