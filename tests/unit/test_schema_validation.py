"""
Test schema validation functionality.

This module tests schema validation, error handling,
and validation rule enforcement for different file formats.
"""

import pytest
from pathlib import Path
import tempfile
import os

from nlp2cmd.schemas import SchemaRegistry, FileFormatSchema
from nlp2cmd.validators import ValidationResult


class TestSchemaValidation:
    """Tests for schema validation functionality."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_dockerfile_validation(self):
        """Test Dockerfile validation."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        # Valid Dockerfile
        valid_dockerfile = """
FROM nginx:latest
COPY . /app
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""".strip()

        result = schema.validate(valid_dockerfile)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # Invalid Dockerfile (missing FROM)
        invalid_dockerfile = """
COPY . /app
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""".strip()

        result = schema.validate(invalid_dockerfile)
        assert result["valid"] is False
        assert any("FROM" in error.upper() for error in result["errors"])

    def test_docker_compose_validation(self):
        """Test docker-compose validation."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("docker-compose")
        assert schema is not None

        # Valid docker-compose
        valid_compose = """
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
""".strip()

        result = schema.validate(valid_compose)
        assert result["valid"] is True

        # Invalid docker-compose (missing version)
        invalid_compose = """
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
""".strip()

        result = schema.validate(invalid_compose)
        assert result["valid"] is False
        assert any("version" in error.lower() for error in result["errors"])

    def test_kubernetes_deployment_validation(self):
        """Test Kubernetes deployment validation."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("kubernetes-deployment")
        assert schema is not None

        # Valid deployment
        valid_deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: app
        image: nginx:latest
""".strip()

        result = schema.validate(valid_deployment)
        assert result["valid"] is True

        # Invalid deployment (missing selector)
        invalid_deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: app
        image: nginx:latest
""".strip()

        result = schema.validate(invalid_deployment)
        assert result["valid"] is False
        assert any("selector" in error.lower() for error in result["errors"])

    def test_env_file_validation(self):
        """Test .env file validation."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("env-file")
        assert schema is not None

        # Valid .env file
        valid_env = """
DATABASE_URL=postgresql://localhost:5432/db
DEBUG=true
PORT=8080
""".strip()

        result = schema.validate(valid_env)
        assert result["valid"] is True

        # Invalid .env file (invalid format)
        invalid_env = """
DATABASE_URL postgresql://localhost:5432/db  # Missing =
DEBUG=true
INVALID LINE WITH SPACES
""".strip()

        result = schema.validate(invalid_env)
        assert result["valid"] is False
        assert len(result["errors"]) >= 1

    def test_github_workflow_validation(self):
        """Test GitHub workflow validation."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("github-workflow")
        assert schema is not None

        # Valid workflow
        valid_workflow = """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: npm test
""".strip()

        result = schema.validate(valid_workflow)
        assert result["valid"] is True

        # Invalid workflow (missing jobs)
        invalid_workflow = """
name: CI
on: [push, pull_request]
# Missing jobs section
""".strip()

        result = schema.validate(invalid_workflow)
        assert result["valid"] is False
        assert any("jobs" in error.lower() for error in result["errors"])

    def test_validation_warnings(self):
        """Test validation warnings."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        # Dockerfile with potential issues (warnings)
        dockerfile_with_warnings = """
FROM ubuntu:latest
RUN apt-get update && apt-get install -y curl
CMD ["bash"]
""".strip()

        result = schema.validate(dockerfile_with_warnings)
        # Should be valid but with warnings about latest tag, cleanup, etc.
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_custom_validation_rules(self):
        """Test custom validation rules."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        
        def custom_validator(content):
            errors = []
            warnings = []
            
            # Custom rule: must contain "CUSTOM_MARKER" (case-insensitive)
            if "custom_marker" not in content.lower():
                errors.append("Missing required CUSTOM_MARKER")
            
            # Custom warning: prefer uppercase
            if content != content.upper():
                warnings.append("Consider using uppercase")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }

        custom_schema = FileFormatSchema(
            name="Custom Validation",
            extensions=["*.custom"],
            validator=custom_validator,
        )

        # Test content without marker
        result = custom_schema.validate("some content")
        assert result["valid"] is False
        assert "Missing required CUSTOM_MARKER" in result["errors"]

        # Test content with marker but lowercase
        result = custom_schema.validate("custom_marker content")
        assert result["valid"] is True
        assert "Consider using uppercase" in result["warnings"]

    def test_validation_performance(self):
        """Test validation performance."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        # Large Dockerfile content
        large_content = "FROM nginx:latest\n" + "# Comment\n" * 1000 + "CMD ['nginx']"

        import time
        start_time = time.time()
        
        for _ in range(100):
            schema.validate(large_content)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100 * 1000  # Convert to ms

        # Should be fast (<10ms per validation)
        assert avg_time < 10, f"Validation too slow: {avg_time:.1f}ms average"

    def test_validation_error_context(self):
        """Test validation error context information."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        invalid_content = """
FROM nginx:latest
COPY . /app
RUN invalid_command_that_does_not_exist
CMD ["nginx"]
""".strip()

        result = schema.validate(invalid_content)
        assert result["valid"] is False
        
        # Check if errors include context (line numbers, etc.)
        for error in result["errors"]:
            assert isinstance(error, str)
            assert len(error) > 0

    def test_partial_validation(self):
        """Test partial validation for incomplete content."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        # Partial Dockerfile (missing CMD)
        partial_content = """
FROM nginx:latest
COPY . /app
EXPOSE 80
""".strip()

        result = schema.validate(partial_content)
        # Should be invalid with appropriate error
        assert result["valid"] is False
        assert any("CMD" in error.upper() or "command" in error.lower() 
                   for error in result["errors"])

    def test_validation_with_comments(self):
        """Test validation handles comments correctly."""
        from nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        assert schema is not None

        # Dockerfile with comments
        content_with_comments = """
# This is a comment
FROM nginx:latest  # Use nginx image
COPY . /app        # Copy application code
# Expose port 80
EXPOSE 80
CMD ["nginx"]       # Start nginx
""".strip()

        result = schema.validate(content_with_comments)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
