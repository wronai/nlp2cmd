"""
Pytest configuration and fixtures for NLP2CMD tests.
"""

import pytest
from pathlib import Path
import tempfile
import os

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import (
    SQLAdapter,
    ShellAdapter,
    DockerAdapter,
    KubernetesAdapter,
    SQLSafetyPolicy,
    ShellSafetyPolicy,
)
from nlp2cmd.schemas import SchemaRegistry
from nlp2cmd.feedback import FeedbackAnalyzer
from nlp2cmd.environment import EnvironmentAnalyzer


@pytest.fixture
def sql_adapter():
    """Provide a configured SQL adapter."""
    return SQLAdapter(
        dialect="postgresql",
        schema_context={
            "tables": ["users", "orders", "products"],
            "relations": {
                "orders.user_id": "users.id",
                "orders.product_id": "products.id",
            },
        },
    )


@pytest.fixture
def sql_adapter_strict():
    """Provide a SQL adapter with strict safety policy."""
    policy = SQLSafetyPolicy(
        allow_delete=False,
        allow_truncate=False,
        allow_drop=False,
        require_where_on_update=True,
        require_where_on_delete=True,
    )
    return SQLAdapter(dialect="postgresql", safety_policy=policy)


@pytest.fixture
def shell_adapter():
    """Provide a configured Shell adapter."""
    return ShellAdapter(
        shell_type="bash",
        environment_context={
            "os": "linux",
            "distro": "ubuntu",
            "available_tools": ["git", "docker", "kubectl"],
        },
    )


@pytest.fixture
def shell_adapter_strict():
    """Provide a Shell adapter with strict safety policy."""
    policy = ShellSafetyPolicy(
        allow_sudo=False,
        sandbox_mode=True,
    )
    return ShellAdapter(safety_policy=policy)


@pytest.fixture
def docker_adapter():
    """Provide a configured Docker adapter."""
    return DockerAdapter()


@pytest.fixture
def kubernetes_adapter():
    """Provide a configured Kubernetes adapter."""
    return KubernetesAdapter()


@pytest.fixture
def nlp2cmd_sql(sql_adapter):
    """Provide NLP2CMD instance with SQL adapter."""
    return NLP2CMD(adapter=sql_adapter)


@pytest.fixture
def nlp2cmd_shell(shell_adapter):
    """Provide NLP2CMD instance with Shell adapter."""
    return NLP2CMD(adapter=shell_adapter)


@pytest.fixture
def schema_registry():
    """Provide a SchemaRegistry instance."""
    return SchemaRegistry()


@pytest.fixture
def feedback_analyzer():
    """Provide a FeedbackAnalyzer instance."""
    return FeedbackAnalyzer()


@pytest.fixture
def environment_analyzer():
    """Provide an EnvironmentAnalyzer instance."""
    return EnvironmentAnalyzer()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dockerfile(temp_dir):
    """Create a sample Dockerfile for testing."""
    content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
    path = temp_dir / "Dockerfile"
    path.write_text(content)
    return path


@pytest.fixture
def sample_compose(temp_dir):
    """Create a sample docker-compose.yml for testing."""
    content = """version: "3.8"
services:
  web:
    build: .
    ports:
      - "8080:80"
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
"""
    path = temp_dir / "docker-compose.yml"
    path.write_text(content)
    return path


@pytest.fixture
def sample_env(temp_dir):
    """Create a sample .env file for testing."""
    content = """# Database configuration
DATABASE_URL=postgresql://localhost/mydb
DATABASE_USER=admin

# API Keys
API_KEY="super-secret-key"
DEBUG=true
"""
    path = temp_dir / ".env"
    path.write_text(content)
    return path


@pytest.fixture
def sample_k8s_deployment(temp_dir):
    """Create a sample Kubernetes deployment for testing."""
    content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.21
          ports:
            - containerPort: 80
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
"""
    path = temp_dir / "deployment.yaml"
    path.write_text(content)
    return path


# Test data fixtures
@pytest.fixture
def sql_test_plans():
    """Provide sample SQL execution plans."""
    return [
        {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*",
            },
        },
        {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": ["id", "name", "email"],
                "filters": [
                    {"field": "active", "operator": "=", "value": True}
                ],
                "ordering": [{"field": "created_at", "direction": "DESC"}],
                "limit": 10,
            },
        },
        {
            "intent": "aggregate",
            "entities": {
                "base_table": "orders",
                "aggregations": [
                    {"function": "COUNT", "field": "*", "alias": "total"}
                ],
                "grouping": ["status"],
            },
        },
    ]


@pytest.fixture
def shell_test_plans():
    """Provide sample Shell execution plans."""
    return [
        {
            "intent": "file_search",
            "entities": {
                "target": "files",
                "filters": [
                    {"attribute": "size", "operator": ">", "value": "100M"}
                ],
            },
        },
        {
            "intent": "process_monitoring",
            "entities": {
                "metric": "memory",
                "limit": 10,
            },
        },
    ]


# Markers
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_docker: marks tests that require Docker"
    )
