"""
Comprehensive tests for DSL Adapters.
"""

import pytest
from nlp2cmd import (
    SQLAdapter,
    ShellAdapter,
    DockerAdapter,
    KubernetesAdapter,
    DQLAdapter,
)


class TestSQLAdapterComprehensive:
    """Comprehensive tests for SQL Adapter."""
    
    @pytest.fixture
    def adapter(self):
        return SQLAdapter(dialect="postgresql")
    
    def test_simple_select(self, adapter):
        """Test simple SELECT generation."""
        plan = {
            "intent": "select",
            "entities": {"table": "users"}
        }
        result = adapter.generate(plan)
        assert "SELECT" in result
        assert "users" in result
    
    def test_select_with_columns(self, adapter):
        """Test SELECT with specific columns."""
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": ["id", "name", "email"]
            }
        }
        result = adapter.generate(plan)
        assert "id" in result
        assert "name" in result
        assert "email" in result
    
    def test_select_with_where(self, adapter):
        """Test SELECT with WHERE clause."""
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "filters": [
                    {"field": "status", "operator": "=", "value": "active"}
                ]
            }
        }
        result = adapter.generate(plan)
        assert "WHERE" in result
        assert "status" in result
    
    def test_select_with_limit(self, adapter):
        """Test SELECT with LIMIT."""
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "limit": 10
            }
        }
        result = adapter.generate(plan)
        assert "LIMIT" in result
        assert "10" in result
    
    def test_insert(self, adapter):
        """Test INSERT generation."""
        plan = {
            "intent": "insert",
            "entities": {
                "table": "users",
                "values": {"name": "John", "email": "john@example.com"}
            }
        }
        result = adapter.generate(plan)
        assert "INSERT INTO" in result
        assert "users" in result
    
    def test_update(self, adapter):
        """Test UPDATE generation."""
        plan = {
            "intent": "update",
            "entities": {
                "table": "users",
                "values": {"status": "inactive"},
                "filters": [{"field": "id", "operator": "=", "value": 1}]
            }
        }
        result = adapter.generate(plan)
        assert "UPDATE" in result
        assert "SET" in result
        assert "WHERE" in result
    
    def test_delete(self, adapter):
        """Test DELETE generation."""
        plan = {
            "intent": "delete",
            "entities": {
                "table": "logs",
                "filters": [{"field": "created_at", "operator": "<", "value": "2024-01-01"}]
            }
        }
        result = adapter.generate(plan)
        assert "DELETE FROM" in result
        assert "WHERE" in result
    
    def test_aggregate_count(self, adapter):
        """Test aggregate COUNT query generation."""
        plan = {
            "intent": "aggregate",
            "entities": {
                "table": "orders",
                "aggregations": [
                    {"function": "COUNT", "field": "*"},
                ]
            }
        }
        result = adapter.generate(plan)
        assert "COUNT" in result


class TestShellAdapterComprehensive:
    """Comprehensive tests for Shell Adapter."""
    
    @pytest.fixture
    def adapter(self):
        return ShellAdapter()
    
    def test_basic_generation(self, adapter):
        """Test basic shell command generation."""
        plan = {
            "intent": "execute",
            "entities": {
                "command": "ls -la"
            }
        }
        result = adapter.generate(plan)
        assert result is not None


class TestDockerAdapterComprehensive:
    """Comprehensive tests for Docker Adapter."""
    
    @pytest.fixture
    def adapter(self):
        return DockerAdapter()
    
    def test_docker_ps(self, adapter):
        """Test docker ps generation."""
        plan = {
            "intent": "list",
            "entities": {
                "all": True
            }
        }
        result = adapter.generate(plan)
        assert "docker" in result
    
    def test_docker_logs(self, adapter):
        """Test docker logs generation."""
        plan = {
            "intent": "logs",
            "entities": {
                "container": "web",
                "tail": 100
            }
        }
        result = adapter.generate(plan)
        assert "docker logs" in result


class TestKubernetesAdapterComprehensive:
    """Comprehensive tests for Kubernetes Adapter."""
    
    @pytest.fixture
    def adapter(self):
        return KubernetesAdapter()
    
    def test_kubectl_get_pods(self, adapter):
        """Test kubectl get pods generation."""
        plan = {
            "intent": "get",
            "entities": {
                "resource_type": "pods",
                "namespace": "default"
            }
        }
        result = adapter.generate(plan)
        assert "kubectl get pods" in result
    
    def test_kubectl_get_deployments(self, adapter):
        """Test kubectl get deployments generation."""
        plan = {
            "intent": "get",
            "entities": {
                "resource_type": "deployments",
                "namespace": "production"
            }
        }
        result = adapter.generate(plan)
        assert "kubectl" in result
        assert "deployment" in result
    
    def test_kubectl_apply(self, adapter):
        """Test kubectl apply generation."""
        plan = {
            "intent": "apply",
            "entities": {
                "file": "deployment.yaml"
            }
        }
        result = adapter.generate(plan)
        assert "kubectl apply" in result
    
    def test_kubectl_scale(self, adapter):
        """Test kubectl scale generation."""
        plan = {
            "intent": "scale",
            "entities": {
                "deployment": "api-server",
                "replicas": 5
            }
        }
        result = adapter.generate(plan)
        assert "scale" in result


class TestDQLAdapterComprehensive:
    """Comprehensive tests for DQL Adapter."""
    
    @pytest.fixture
    def adapter(self):
        return DQLAdapter()
    
    def test_query_generation(self, adapter):
        """Test DQL query generation."""
        plan = {
            "intent": "select",
            "entities": {
                "entity": "User",
                "alias": "u"
            }
        }
        result = adapter.generate(plan)
        # DQL generates PHP QueryBuilder code
        assert result is not None
        assert "createQueryBuilder" in result
