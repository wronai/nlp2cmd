"""
E2E Test Fixtures and Configuration.
"""

import os
import sys
import pytest
from pathlib import Path
from typing import Any, Generator

# Add src to Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from nlp2cmd import (
    DecisionRouter,
    RouterConfig,
    ActionRegistry,
    get_registry,
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    LLMPlanner,
    PlannerConfig,
    ResultAggregator,
    OutputFormat,
)


def pytest_configure(config):
    """Configure pytest for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "service: mark test as service mode test"
    )


@pytest.fixture(scope="session")
def e2e_config():
    """E2E test configuration."""
    return {
        "default_host": "127.0.0.1",
        "default_port": 8001,
        "startup_timeout": 30,
        "request_timeout": 10,
        "test_env_file": "test_e2e.env"
    }


# =============================================================================
# Environment Configuration
# =============================================================================

def get_env_or_default(key: str, default: str) -> str:
    """Get environment variable or return default."""
    return os.environ.get(key, default)


@pytest.fixture(scope="session")
def postgres_config() -> dict[str, str]:
    """PostgreSQL configuration from environment."""
    return {
        "host": get_env_or_default("POSTGRES_HOST", "localhost"),
        "port": get_env_or_default("POSTGRES_PORT", "5432"),
        "user": get_env_or_default("POSTGRES_USER", "nlp2cmd"),
        "password": get_env_or_default("POSTGRES_PASSWORD", "nlp2cmd_test"),
        "database": get_env_or_default("POSTGRES_DB", "nlp2cmd_test"),
    }


# =============================================================================
# Core Component Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def action_registry() -> ActionRegistry:
    """Global action registry."""
    return get_registry()


@pytest.fixture
def decision_router() -> DecisionRouter:
    """Decision router for query routing."""
    return DecisionRouter(RouterConfig(
        simple_intents=["select", "get", "list", "show", "count", "describe"],
        complex_intents=["analyze", "compare", "report", "migrate", "audit"],
        entity_threshold=5,
        confidence_threshold=0.6,
    ))


@pytest.fixture
def plan_executor(action_registry) -> PlanExecutor:
    """Plan executor with mock handlers."""
    executor = PlanExecutor(registry=action_registry)
    
    # Register mock handlers for testing
    _register_mock_handlers(executor)
    
    return executor


@pytest.fixture
def llm_planner(action_registry) -> LLMPlanner:
    """LLM planner (rule-based fallback for tests)."""
    return LLMPlanner(
        registry=action_registry,
        config=PlannerConfig(
            max_steps=10,
            include_examples=True,
        ),
    )


@pytest.fixture
def result_aggregator() -> ResultAggregator:
    """Result aggregator for formatting output."""
    return ResultAggregator(default_format=OutputFormat.TEXT)


# =============================================================================
# Mock Handlers
# =============================================================================

def _register_mock_handlers(executor: PlanExecutor) -> None:
    """Register mock handlers for e2e testing."""
    
    # SQL Handlers
    executor.register_handler("sql_select", mock_sql_select)
    executor.register_handler("sql_insert", mock_sql_insert)
    executor.register_handler("sql_update", mock_sql_update)
    executor.register_handler("sql_delete", mock_sql_delete)
    executor.register_handler("sql_aggregate", mock_sql_aggregate)
    
    # Shell Handlers
    executor.register_handler("shell_find", mock_shell_find)
    executor.register_handler("shell_read_file", mock_shell_read_file)
    executor.register_handler("shell_count_pattern", mock_shell_count_pattern)
    executor.register_handler("shell_process_list", mock_shell_process_list)
    
    # Docker Handlers
    executor.register_handler("docker_ps", mock_docker_ps)
    executor.register_handler("docker_run", mock_docker_run)
    executor.register_handler("docker_stop", mock_docker_stop)
    executor.register_handler("docker_logs", mock_docker_logs)
    
    # Kubernetes Handlers
    executor.register_handler("k8s_get", mock_k8s_get)
    executor.register_handler("k8s_scale", mock_k8s_scale)
    executor.register_handler("k8s_logs", mock_k8s_logs)


# =============================================================================
# Mock SQL Handlers
# =============================================================================

MOCK_USERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "status": "active", "city": "Warsaw"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "status": "active", "city": "Krakow"},
    {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "status": "inactive", "city": "Warsaw"},
    {"id": 4, "name": "Diana Ross", "email": "diana@example.com", "status": "active", "city": "Gdansk"},
    {"id": 5, "name": "Edward Norton", "email": "edward@example.com", "status": "pending", "city": "Poznan"},
]

MOCK_ORDERS = [
    {"id": 1, "user_id": 1, "order_number": "ORD-001", "status": "completed", "total": 2949.98},
    {"id": 2, "user_id": 1, "order_number": "ORD-002", "status": "completed", "total": 449.99},
    {"id": 3, "user_id": 2, "order_number": "ORD-003", "status": "shipped", "total": 1349.98},
    {"id": 4, "user_id": 4, "order_number": "ORD-004", "status": "pending", "total": 999.99},
]

MOCK_PRODUCTS = [
    {"id": 1, "name": "Business Laptop", "price": 2499.99, "category": "Electronics", "stock": 50},
    {"id": 2, "name": "Smartphone Pro", "price": 999.99, "category": "Electronics", "stock": 100},
    {"id": 3, "name": "Standing Desk", "price": 599.99, "category": "Furniture", "stock": 25},
    {"id": 4, "name": "Office Chair", "price": 349.99, "category": "Furniture", "stock": 40},
]


def mock_sql_select(table: str, columns: list = None, filters: list = None, **kwargs) -> list:
    """Mock SQL SELECT handler."""
    data_map = {
        "users": MOCK_USERS,
        "orders": MOCK_ORDERS,
        "products": MOCK_PRODUCTS,
    }
    
    data = data_map.get(table, [])
    
    # Apply simple filters
    if filters:
        for f in filters:
            f_lower = f.lower()
            if "status = 'active'" in f_lower:
                data = [r for r in data if r.get("status") == "active"]
            elif "status = 'completed'" in f_lower:
                data = [r for r in data if r.get("status") == "completed"]
            elif "city = 'warsaw'" in f_lower:
                data = [r for r in data if r.get("city") == "Warsaw"]
            elif "category = 'electronics'" in f_lower:
                data = [r for r in data if r.get("category") == "Electronics"]
    
    # Apply column selection
    if columns and columns != ["*"]:
        data = [{col: r.get(col) for col in columns if col in r} for r in data]
    
    return data


def mock_sql_insert(table: str, values: dict, **kwargs) -> int:
    """Mock SQL INSERT handler."""
    return 1  # Return number of inserted rows


def mock_sql_update(table: str, values: dict, filters: list, **kwargs) -> int:
    """Mock SQL UPDATE handler."""
    return len(filters) if filters else 0  # Simulate affected rows


def mock_sql_delete(table: str, filters: list, **kwargs) -> int:
    """Mock SQL DELETE handler."""
    return 1 if filters else 0


def mock_sql_aggregate(table: str, aggregations: list, grouping: list = None, **kwargs) -> list:
    """Mock SQL aggregate handler."""
    data_map = {
        "users": MOCK_USERS,
        "orders": MOCK_ORDERS,
        "products": MOCK_PRODUCTS,
    }
    
    data = data_map.get(table, [])
    
    if grouping:
        # Simulate GROUP BY
        groups = {}
        for row in data:
            key = tuple(row.get(g) for g in grouping)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        
        result = []
        for key, rows in groups.items():
            row_result = {g: k for g, k in zip(grouping, key)}
            row_result["count"] = len(rows)
            result.append(row_result)
        return result
    
    # Simple aggregation
    return [{"count": len(data)}]


# =============================================================================
# Mock Shell Handlers
# =============================================================================

def mock_shell_find(glob: str = "*", path: str = ".", **kwargs) -> list:
    """Mock shell find handler."""
    if "*.log" in glob:
        return ["/var/log/app.log", "/var/log/error.log", "/var/log/access.log"]
    if "*.py" in glob:
        return ["main.py", "utils.py", "config.py", "test_app.py"]
    if "*.json" in glob:
        return ["package.json", "config.json", "data.json"]
    return ["file1.txt", "file2.txt", "readme.md"]


def mock_shell_read_file(path: str, encoding: str = "utf-8", **kwargs) -> str:
    """Mock shell file read handler."""
    if "error.log" in path:
        return "ERROR: Connection failed\nERROR: Timeout\nWARNING: High memory\nERROR: Disk full"
    if "app.log" in path:
        return "INFO: Started\nINFO: Processing\nERROR: Failed\nINFO: Completed"
    return f"Contents of {path}"


def mock_shell_count_pattern(file: str, pattern: str, **kwargs) -> int:
    """Mock shell grep/count handler."""
    counts = {
        "/var/log/app.log": {"ERROR": 15, "WARNING": 42, "INFO": 230},
        "/var/log/error.log": {"ERROR": 127, "WARNING": 8, "INFO": 5},
        "/var/log/access.log": {"ERROR": 3, "WARNING": 5, "200": 1500, "404": 45},
    }
    return counts.get(file, {}).get(pattern, 0)


def mock_shell_process_list(filter: str = None, sort_by: str = None, limit: int = 10, **kwargs) -> list:
    """Mock shell process list handler."""
    processes = [
        {"pid": 1, "name": "systemd", "cpu": 0.1, "memory": 0.5},
        {"pid": 1234, "name": "python", "cpu": 15.2, "memory": 8.3},
        {"pid": 5678, "name": "nginx", "cpu": 2.1, "memory": 1.2},
        {"pid": 9012, "name": "postgres", "cpu": 5.5, "memory": 12.4},
        {"pid": 3456, "name": "redis", "cpu": 1.0, "memory": 2.1},
    ]
    
    if filter:
        processes = [p for p in processes if filter.lower() in p["name"].lower()]
    
    if sort_by and sort_by in ("cpu", "memory"):
        processes = sorted(processes, key=lambda x: x[sort_by], reverse=True)
    
    return processes[:limit]


# =============================================================================
# Mock Docker Handlers
# =============================================================================

def mock_docker_ps(all: bool = False, filter: str = None, **kwargs) -> list:
    """Mock docker ps handler."""
    containers = [
        {"id": "abc123", "name": "web-1", "image": "nginx:latest", "status": "running", "ports": "80:80"},
        {"id": "def456", "name": "api-1", "image": "python:3.12", "status": "running", "ports": "8000:8000"},
        {"id": "ghi789", "name": "db-1", "image": "postgres:16", "status": "running", "ports": "5432:5432"},
    ]
    
    if not all:
        containers = [c for c in containers if c["status"] == "running"]
    
    if filter:
        containers = [c for c in containers if filter.lower() in c["name"].lower()]
    
    return containers


def mock_docker_run(image: str, name: str = None, **kwargs) -> str:
    """Mock docker run handler."""
    return f"container_{name or 'random'}_id"


def mock_docker_stop(container: str, timeout: int = 10, **kwargs) -> bool:
    """Mock docker stop handler."""
    return True


def mock_docker_logs(container: str, tail: int = 100, **kwargs) -> str:
    """Mock docker logs handler."""
    return f"[INFO] Container {container} logs\n[INFO] Service started\n[INFO] Listening on port 8000"


# =============================================================================
# Mock Kubernetes Handlers
# =============================================================================

def mock_k8s_get(resource: str, name: str = None, namespace: str = "default", **kwargs) -> list:
    """Mock kubectl get handler."""
    resources = {
        "pods": [
            {"name": "api-server-abc123", "status": "Running", "restarts": 0, "age": "5d"},
            {"name": "api-server-def456", "status": "Running", "restarts": 1, "age": "5d"},
            {"name": "worker-ghi789", "status": "Running", "restarts": 0, "age": "3d"},
        ],
        "deployments": [
            {"name": "api-server", "ready": "2/2", "available": 2, "age": "10d"},
            {"name": "worker", "ready": "1/1", "available": 1, "age": "10d"},
        ],
        "services": [
            {"name": "api-server", "type": "ClusterIP", "cluster_ip": "10.0.0.1", "ports": "80/TCP"},
            {"name": "api-server-lb", "type": "LoadBalancer", "external_ip": "203.0.113.1", "ports": "443/TCP"},
        ],
    }
    
    result = resources.get(resource, [])
    
    if name:
        result = [r for r in result if name in r["name"]]
    
    return result


def mock_k8s_scale(deployment: str, replicas: int, namespace: str = "default", **kwargs) -> bool:
    """Mock kubectl scale handler."""
    return True


def mock_k8s_logs(pod: str, container: str = None, namespace: str = "default", tail: int = 100, **kwargs) -> str:
    """Mock kubectl logs handler."""
    return f"[INFO] Pod {pod} logs\n[INFO] Application started\n[INFO] Ready to serve requests"


# =============================================================================
# Helper Fixtures
# =============================================================================

@pytest.fixture
def sample_plans() -> dict[str, ExecutionPlan]:
    """Sample execution plans for testing."""
    return {
        "simple_select": ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ]),
        
        "filtered_select": ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={"table": "users", "filters": ["status = 'active'"]},
            ),
        ]),
        
        "multi_step_analysis": ExecutionPlan(steps=[
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
        ]),
        
        "k8s_status": ExecutionPlan(steps=[
            PlanStep(action="k8s_get", params={"resource": "pods"}),
        ]),
        
        "docker_status": ExecutionPlan(steps=[
            PlanStep(action="docker_ps", params={"all": False}),
        ]),
    }
