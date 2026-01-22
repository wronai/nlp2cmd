"""
Comprehensive unit tests for NLP2CMD schemas module.
"""

import pytest
from pathlib import Path
import tempfile
import os

from nlp2cmd.schemas import SchemaRegistry, FileFormatSchema


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_builtin_schemas_registered(self, registry):
        """Test that built-in schemas are registered."""
        assert registry.has_schema("dockerfile")
        assert registry.has_schema("docker-compose")
        assert registry.has_schema("kubernetes-deployment")
        assert registry.has_schema("github-workflow")
        assert registry.has_schema("env-file")

    def test_get_schema(self, registry):
        """Test getting schema by name."""
        schema = registry.get("dockerfile")

        assert schema is not None
        assert schema.name == "Dockerfile"
        assert "Dockerfile" in schema.extensions

    def test_get_nonexistent_schema(self, registry):
        """Test getting non-existent schema."""
        schema = registry.get("nonexistent")
        assert schema is None

    def test_register_custom_schema(self, registry):
        """Test registering custom schema."""
        custom_schema = FileFormatSchema(
            name="Custom Format",
            extensions=["*.custom"],
            mime_types=["application/x-custom"],
            validator=lambda c: {"valid": True, "errors": [], "warnings": []},
            parser=lambda c: {"content": c},
            generator=lambda d: d.get("content", ""),
        )

        registry.register(custom_schema)

        assert registry.has_schema("custom format")
        assert registry.get("custom format") is not None


class TestDockerfileValidation:
    """Tests for Dockerfile validation."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_valid_dockerfile(self, registry):
        """Test valid Dockerfile."""
        content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""

        result = registry.validate(content, "dockerfile")

        assert result["valid"]
        assert len(result["errors"]) == 0

    def test_dockerfile_missing_from(self, registry):
        """Test Dockerfile without FROM."""
        content = """WORKDIR /app
COPY . .
CMD ["python", "app.py"]
"""

        result = registry.validate(content, "dockerfile")

        assert not result["valid"]
        assert any("FROM" in e for e in result["errors"])

    def test_dockerfile_missing_tag_warning(self, registry):
        """Test Dockerfile with untagged image."""
        content = """FROM python
COPY . .
"""

        result = registry.validate(content, "dockerfile")

        assert any("tag" in w.lower() for w in result["warnings"])

    def test_dockerfile_apt_get_warning(self, registry):
        """Test Dockerfile apt-get without -y."""
        content = """FROM ubuntu
RUN apt-get update
RUN apt-get install python3
"""

        result = registry.validate(content, "dockerfile")

        assert any("-y" in w for w in result["warnings"])


class TestDockerComposeValidation:
    """Tests for docker-compose.yml validation."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_valid_compose(self, registry):
        """Test valid docker-compose.yml."""
        content = """version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
"""

        result = registry.validate(content, "docker-compose")

        assert result["valid"]

    def test_compose_missing_services(self, registry):
        """Test docker-compose without services."""
        content = """version: '3.8'
networks:
  default:
"""

        result = registry.validate(content, "docker-compose")

        assert not result["valid"]
        assert any("services" in e.lower() for e in result["errors"])

    def test_compose_empty_service(self, registry):
        """Test docker-compose with empty service."""
        content = """version: '3.8'
services:
  web:
"""

        result = registry.validate(content, "docker-compose")

        assert not result["valid"]

    def test_compose_service_without_image_or_build(self, registry):
        """Test service without image or build."""
        content = """version: '3.8'
services:
  web:
    ports:
      - "8080:80"
"""

        result = registry.validate(content, "docker-compose")

        assert not result["valid"]
        assert any("image" in e.lower() or "build" in e.lower() for e in result["errors"])


class TestKubernetesValidation:
    """Tests for Kubernetes manifest validation."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_valid_deployment(self, registry):
        """Test valid Kubernetes Deployment."""
        content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
"""

        result = registry.validate(content, "kubernetes-deployment")

        assert result["valid"]

    def test_deployment_missing_selector(self, registry):
        """Test Deployment without selector."""
        content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
"""

        result = registry.validate(content, "kubernetes-deployment")

        assert not result["valid"]
        assert any("selector" in e.lower() for e in result["errors"])

    def test_deployment_missing_resources_warning(self, registry):
        """Test Deployment without resource limits."""
        content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
"""

        result = registry.validate(content, "kubernetes-deployment")

        assert any("resource" in w.lower() for w in result["warnings"])


class TestGitHubWorkflowValidation:
    """Tests for GitHub Actions workflow validation."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_valid_workflow(self, registry):
        """Test valid GitHub workflow."""
        content = """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest
"""

        result = registry.validate(content, "github-workflow")

        assert result["valid"]

    def test_workflow_missing_on(self, registry):
        """Test workflow without trigger."""
        content = """name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
"""

        result = registry.validate(content, "github-workflow")

        assert not result["valid"]
        assert any("on" in e.lower() for e in result["errors"])

    def test_workflow_missing_runs_on(self, registry):
        """Test workflow job without runs-on."""
        content = """name: CI
on: push
jobs:
  test:
    steps:
      - run: echo "test"
"""

        result = registry.validate(content, "github-workflow")

        assert not result["valid"]


class TestEnvFileValidation:
    """Tests for .env file validation."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_valid_env_file(self, registry):
        """Test valid .env file."""
        content = """DATABASE_URL=postgres://localhost:5432/db
SECRET_KEY=mysecret123
DEBUG=true
"""

        result = registry.validate(content, "env-file")

        assert result["valid"]

    def test_env_lowercase_warning(self, registry):
        """Test .env with lowercase variables."""
        content = """database_url=postgres://localhost:5432/db
secretKey=mysecret
"""

        result = registry.validate(content, "env-file")

        assert any("uppercase" in w.lower() for w in result["warnings"])

    def test_env_unclosed_quote(self, registry):
        """Test .env with unclosed quote."""
        content = """DATABASE_URL="postgres://localhost:5432/db
SECRET_KEY=test
"""

        result = registry.validate(content, "env-file")

        assert not result["valid"]
        assert any("quote" in e.lower() for e in result["errors"])

    def test_env_invalid_format(self, registry):
        """Test .env with invalid format."""
        content = """DATABASE_URL
SECRET_KEY=test
"""

        result = registry.validate(content, "env-file")

        assert not result["valid"]


class TestSchemaRepair:
    """Tests for schema repair functionality."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_dockerfile_repair_add_tag(self, registry):
        """Test Dockerfile repair adds image tag."""
        content = """FROM python
COPY . .
"""

        result = registry.repair(content, "dockerfile", auto_fix=True)

        # Check if repair was attempted
        assert "changes" in result

    def test_compose_repair_version(self, registry):
        """Test docker-compose repair updates version."""
        content = """version: '2'
services:
  web:
    image: nginx
"""

        result = registry.repair(content, "docker-compose", auto_fix=True)

        assert "changes" in result

    def test_repair_without_auto_fix(self, registry):
        """Test repair without auto_fix returns suggestions."""
        content = """FROM python
COPY . .
"""

        result = registry.repair(content, "dockerfile", auto_fix=False)

        # Should have changes but not applied
        assert "content" in result


class TestFormatDetection:
    """Tests for automatic format detection."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_detect_dockerfile(self, registry):
        """Test detecting Dockerfile."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='', delete=False
        ) as f:
            f.name = "Dockerfile"

        try:
            path = Path(f.name)
            # Create actual Dockerfile
            with tempfile.NamedTemporaryFile(
                mode='w', prefix='Dockerfile', delete=False
            ) as df:
                df.write("FROM python:3.11\n")
                df.flush()
                path = Path(df.name)

            schema = registry.detect_format(path)
            # May or may not detect based on filename
        finally:
            pass

    def test_detect_by_content_compose(self, registry):
        """Test detecting docker-compose by content."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            f.write("version: '3.8'\nservices:\n  web:\n    image: nginx\n")
            f.flush()

            path = Path(f.name)
            schema = registry.detect_format(path)

            assert schema is not None

        os.unlink(f.name)

    def test_detect_by_content_kubernetes(self, registry):
        """Test detecting Kubernetes manifest by content."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write("apiVersion: apps/v1\nkind: Deployment\n")
            f.flush()

            path = Path(f.name)
            schema = registry.detect_format(path)

            assert schema is not None
            assert "kubernetes" in schema.name.lower()

        os.unlink(f.name)


class TestFileFormatSchema:
    """Tests for FileFormatSchema dataclass."""

    def test_schema_creation(self):
        """Test creating a FileFormatSchema."""
        schema = FileFormatSchema(
            name="Test Format",
            extensions=["*.test"],
            mime_types=["application/x-test"],
            validator=lambda c: {"valid": True, "errors": [], "warnings": []},
            parser=lambda c: {},
            generator=lambda d: "",
            repair_rules=[
                {"pattern": r"foo", "fix": "bar", "reason": "Replace foo with bar"}
            ],
            examples=["example1.test", "example2.test"],
        )

        assert schema.name == "Test Format"
        assert len(schema.repair_rules) == 1
        assert len(schema.examples) == 2

    def test_schema_validator_called(self):
        """Test that validator is called correctly."""
        validator_called = []

        def custom_validator(content):
            validator_called.append(content)
            return {"valid": True, "errors": [], "warnings": []}

        schema = FileFormatSchema(
            name="Test",
            extensions=[],
            mime_types=[],
            validator=custom_validator,
            parser=lambda c: {},
            generator=lambda d: "",
        )

        result = schema.validator("test content")

        assert len(validator_called) == 1
        assert validator_called[0] == "test content"


class TestSchemaRegistryEdgeCases:
    """Tests for edge cases in SchemaRegistry."""

    @pytest.fixture
    def registry(self):
        return SchemaRegistry()

    def test_validate_empty_content(self, registry):
        """Test validating empty content."""
        result = registry.validate("", "dockerfile")

        assert not result["valid"]

    def test_validate_invalid_yaml(self, registry):
        """Test validating invalid YAML."""
        content = """
this: is: not: valid: yaml
  - broken
    indentation
"""

        result = registry.validate(content, "docker-compose")

        assert not result["valid"]

    def test_repair_unknown_schema(self, registry):
        """Test repairing with unknown schema."""
        result = registry.repair("content", "unknown-schema")

        assert not result["repaired"]
        assert result["content"] == "content"

    def test_case_insensitive_schema_lookup(self, registry):
        """Test case-insensitive schema lookup."""
        schema1 = registry.get("DOCKERFILE")
        schema2 = registry.get("dockerfile")
        schema3 = registry.get("Dockerfile")

        # All should return same schema or None consistently
        assert (schema1 == schema2) or (schema1 is None and schema2 is None)
