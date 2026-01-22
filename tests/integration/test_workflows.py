"""
Integration tests for NLP2CMD.

These tests verify the complete flow from natural language
to command generation with validation and feedback.
"""

import pytest
import tempfile
from pathlib import Path

from nlp2cmd import (
    NLP2CMD,
    SQLAdapter,
    ShellAdapter,
    DockerAdapter,
    KubernetesAdapter,
    FeedbackAnalyzer,
    SchemaRegistry,
    EnvironmentAnalyzer,
)
from nlp2cmd.validators import SQLValidator, ShellValidator


class TestSQLIntegration:
    """Integration tests for SQL workflow."""

    @pytest.fixture
    def sql_setup(self):
        """Setup SQL adapter with full context."""
        adapter = SQLAdapter(
            dialect="postgresql",
            schema_context={
                "tables": ["users", "orders", "products"],
                "columns": {
                    "users": ["id", "name", "email", "status"],
                    "orders": ["id", "user_id", "total", "status"],
                    "products": ["id", "name", "price"],
                },
                "relations": {
                    "orders.user_id": "users.id",
                }
            }
        )
        validator = SQLValidator()
        analyzer = FeedbackAnalyzer()

        return {
            "adapter": adapter,
            "validator": validator,
            "analyzer": analyzer,
            "nlp": NLP2CMD(
                adapter=adapter,
                validator=validator,
                feedback_analyzer=analyzer,
            )
        }

    def test_full_select_flow(self, sql_setup):
        """Test complete SELECT flow with validation."""
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*",
                "filters": [
                    {"field": "status", "operator": "=", "value": "active"}
                ]
            }
        }

        # Generate
        command = sql_setup["adapter"].generate(plan)
        assert "SELECT" in command
        assert "users" in command

        # Validate
        validation = sql_setup["validator"].validate(command)
        assert validation.is_valid

        # Analyze
        feedback = sql_setup["analyzer"].analyze(
            original_input="Show active users",
            generated_output=command,
            dsl_type="sql"
        )
        assert feedback.is_success

    def test_select_with_join_flow(self, sql_setup):
        """Test SELECT with JOIN flow."""
        plan = {
            "intent": "select",
            "entities": {
                "table": "orders",
                "columns": ["orders.id", "orders.total", "users.name"],
                "joins": [
                    {"type": "INNER", "table": "users", "on": "orders.user_id = users.id"}
                ],
                "limit": 10
            }
        }

        command = sql_setup["adapter"].generate(plan)

        assert "JOIN" in command
        assert "users" in command
        assert "LIMIT 10" in command

    def test_aggregate_flow(self, sql_setup):
        """Test aggregation flow."""
        plan = {
            "intent": "aggregate",
            "entities": {
                "base_table": "orders",
                "aggregations": [
                    {"function": "SUM", "field": "total", "alias": "total_sales"},
                    {"function": "COUNT", "field": "*", "alias": "order_count"},
                ],
                "grouping": ["user_id"]
            }
        }

        command = sql_setup["adapter"].generate(plan)

        assert "SUM" in command
        assert "COUNT" in command
        assert "GROUP BY" in command


class TestShellIntegration:
    """Integration tests for Shell workflow."""

    @pytest.fixture
    def shell_setup(self):
        """Setup Shell adapter."""
        adapter = ShellAdapter(shell_type="bash")
        validator = ShellValidator()
        analyzer = FeedbackAnalyzer()

        return {
            "adapter": adapter,
            "validator": validator,
            "analyzer": analyzer,
        }

    def test_file_search_flow(self, shell_setup):
        """Test file search flow."""
        plan = {
            "intent": "file_search",
            "entities": {
                "target": "files",
                "filters": [
                    {"attribute": "size", "operator": ">", "value": "100M"}
                ]
            }
        }

        command = shell_setup["adapter"].generate(plan)

        assert "find" in command
        assert "-size" in command

        validation = shell_setup["validator"].validate(command)
        assert validation.is_valid

    def test_docker_command_flow(self, shell_setup):
        """Test Docker command through Shell."""
        plan = {
            "intent": "docker",
            "entities": {
                "action": "ps"
            }
        }

        command = shell_setup["adapter"].generate(plan)
        assert "docker ps" in command

    def test_safety_check_flow(self, shell_setup):
        """Test safety check for dangerous commands."""
        dangerous_command = "rm -rf /"

        safety = shell_setup["adapter"].check_safety(dangerous_command)

        assert not safety["allowed"]


class TestDockerIntegration:
    """Integration tests for Docker workflow."""

    @pytest.fixture
    def docker_setup(self):
        """Setup Docker adapter."""
        return DockerAdapter()

    def test_run_container_flow(self, docker_setup):
        """Test running a container."""
        plan = {
            "intent": "container_run",
            "entities": {
                "image": "nginx",
                "name": "web",
                "ports": ["8080:80"],
                "detach": True
            }
        }

        command = docker_setup.generate(plan)

        assert "docker run" in command
        assert "-d" in command
        assert "nginx" in command

        # Verify tag is added
        assert ":latest" in command or "nginx:" in command

    def test_compose_file_generation(self, docker_setup):
        """Test docker-compose file generation."""
        spec = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["8080:80"],
                },
                "db": {
                    "image": "postgres:15",
                    "environment": {"POSTGRES_PASSWORD": "secret"},
                }
            }
        }

        yaml_content = docker_setup.generate_compose_file(spec)

        assert "nginx" in yaml_content
        assert "postgres" in yaml_content
        assert "services" in yaml_content


class TestKubernetesIntegration:
    """Integration tests for Kubernetes workflow."""

    @pytest.fixture
    def k8s_setup(self):
        """Setup Kubernetes adapter."""
        return KubernetesAdapter()

    def test_kubectl_get_flow(self, k8s_setup):
        """Test kubectl get command."""
        plan = {
            "intent": "get",
            "entities": {
                "resource_type": "pods",
                "namespace": "default"
            }
        }

        command = k8s_setup.generate(plan)

        assert "kubectl get pods" in command
        assert "-n default" in command

    def test_manifest_generation(self, k8s_setup):
        """Test Kubernetes manifest generation."""
        spec = {
            "kind": "Deployment",
            "name": "web",
            "namespace": "default",
            "image": "nginx:alpine",
            "replicas": 3
        }

        manifest = k8s_setup.generate_manifest(spec)

        assert "apiVersion" in manifest
        assert "kind: Deployment" in manifest
        assert "nginx" in manifest


class TestSchemaIntegration:
    """Integration tests for Schema validation."""

    @pytest.fixture
    def registry(self):
        """Setup schema registry."""
        return SchemaRegistry()

    def test_dockerfile_validation_flow(self, registry):
        """Test Dockerfile validation flow."""
        content = """FROM python:3.11
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
"""

        result = registry.validate(content, "dockerfile")
        assert result["valid"]

    def test_compose_validation_flow(self, registry):
        """Test docker-compose validation flow."""
        content = """version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
"""

        result = registry.validate(content, "docker-compose")
        assert result["valid"]

    def test_file_repair_flow(self, registry):
        """Test file repair flow."""
        # Compose file with old version
        content = """version: '2'
services:
  web:
    image: nginx
"""

        result = registry.repair(content, "docker-compose", auto_fix=True)

        # Should have changes or warnings
        assert "changes" in result


class TestFeedbackIntegration:
    """Integration tests for feedback loop."""

    @pytest.fixture
    def feedback_setup(self):
        """Setup feedback components."""
        return {
            "analyzer": FeedbackAnalyzer(),
        }

    def test_feedback_with_errors(self, feedback_setup):
        """Test feedback analysis with errors."""
        feedback = feedback_setup["analyzer"].analyze(
            original_input="Show users",
            generated_output="SELECT * FROM users WHERE (id = 1",
            validation_errors=["Unbalanced parentheses"],
            dsl_type="sql"
        )

        assert not feedback.is_success
        assert len(feedback.errors) > 0

    def test_feedback_with_warnings(self, feedback_setup):
        """Test feedback analysis with warnings."""
        feedback = feedback_setup["analyzer"].analyze(
            original_input="Delete all users",
            generated_output="DELETE FROM users",
            validation_errors=["DELETE without WHERE"],
            dsl_type="sql"
        )

        # Should have errors or warnings
        assert len(feedback.errors) > 0 or len(feedback.warnings) > 0

    def test_feedback_success(self, feedback_setup):
        """Test feedback for successful command."""
        feedback = feedback_setup["analyzer"].analyze(
            original_input="Show all users",
            generated_output="SELECT * FROM users",
            validation_errors=[],
            dsl_type="sql"
        )

        assert feedback.is_success


class TestEnvironmentIntegration:
    """Integration tests for environment analysis."""

    @pytest.fixture
    def env_analyzer(self):
        """Setup environment analyzer."""
        return EnvironmentAnalyzer()

    def test_full_environment_analysis(self, env_analyzer):
        """Test complete environment analysis."""
        # Basic analysis
        env = env_analyzer.analyze()
        assert "os" in env
        assert "shell" in env

        # Full report
        report = env_analyzer.full_report()
        assert report.os_info is not None

    def test_config_file_discovery(self, env_analyzer):
        """Test config file discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            compose = Path(tmpdir) / "docker-compose.yml"
            compose.write_text("version: '3.8'\nservices: {}")

            configs = env_analyzer.find_config_files(Path(tmpdir))

            assert len(configs) >= 1

    def test_command_validation(self, env_analyzer):
        """Test command validation against environment."""
        # Shell builtin should always work
        result = env_analyzer.validate_command("echo hello", context={})
        assert result["valid"]


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_sql_nlp_to_execution(self):
        """Test complete NLP to SQL execution flow."""
        # Setup
        adapter = SQLAdapter(
            dialect="postgresql",
            schema_context={"tables": ["users"]}
        )
        validator = SQLValidator()
        analyzer = FeedbackAnalyzer()
        nlp = NLP2CMD(
            adapter=adapter,
            validator=validator,
            feedback_analyzer=analyzer
        )

        # Generate command from plan
        plan = {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*"
            }
        }
        command = adapter.generate(plan)

        # Validate
        validation = validator.validate(command)

        # Analyze feedback
        feedback = analyzer.analyze(
            original_input="Show all users",
            generated_output=command,
            validation_errors=validation.errors,
            validation_warnings=validation.warnings,
            dsl_type="sql"
        )

        # Verify complete flow
        assert command is not None
        assert "SELECT" in command
        assert validation.is_valid
        assert feedback.is_success

    def test_docker_file_repair_flow(self):
        """Test Dockerfile repair end-to-end."""
        registry = SchemaRegistry()

        # Bad Dockerfile
        dockerfile = """FROM python
COPY . .
RUN pip install requirements.txt
"""

        # Validate
        validation = registry.validate(dockerfile, "dockerfile")

        # Repair
        repaired = registry.repair(dockerfile, "dockerfile", auto_fix=True)

        # Verify flow completed
        assert validation is not None
        assert repaired is not None
        assert "changes" in repaired
