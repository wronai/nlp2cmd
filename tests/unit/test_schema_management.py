"""
Test schema management and lifecycle functionality.

This module tests schema discovery, loading from files,
dynamic registration, and schema management operations.
"""

import pytest
from pathlib import Path
import tempfile
import os
import json

from nlp2cmd.schemas import SchemaRegistry, FileFormatSchema


class TestSchemaDiscovery:
    """Tests for schema discovery functionality."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_find_schema_for_file(self, registry):
        """Test finding schema for a file."""
        # Test known extensions
        assert registry.find_schema_for_file("Dockerfile") is not None
        assert registry.find_schema_for_file("docker-compose.yml") is not None
        assert registry.find_schema_for_file("deployment.yaml") is not None
        assert registry.find_schema_for_file(".env") is not None

    def test_find_schema_for_unknown_file(self, registry):
        """Test finding schema for unknown file."""
        assert registry.find_schema_for_file("unknown.xyz") is None
        assert registry.find_schema_for_file("no_extension") is None

    def test_find_schema_by_mime_type(self, registry):
        """Test finding schema by MIME type."""
        # Test known MIME types
        assert registry.find_schema_by_mime_type("application/x-yaml") is not None
        assert registry.find_schema_by_mime_type("application/json") is not None

    def test_find_schema_by_unknown_mime_type(self, registry):
        """Test finding schema by unknown MIME type."""
        assert registry.find_schema_by_mime_type("application/unknown") is None

    def test_schema_priority_ordering(self, registry):
        """Test schema priority ordering when multiple schemas match."""
        # Create custom schema that conflicts with built-in
        custom_schema = FileFormatSchema(
            name="Custom Docker",
            extensions=["Dockerfile*"],
            priority=100,  # Higher priority than built-in
        )
        registry.register("custom-docker", custom_schema)

        # Should return the higher priority schema
        found = registry.find_schema_for_file("Dockerfile")
        assert found.name == "Custom Docker"

    def test_schema_caching(self, registry):
        """Test that schema lookups are cached."""
        # First lookup
        schema1 = registry.find_schema_for_file("Dockerfile")
        
        # Second lookup should return same object (cached)
        schema2 = registry.find_schema_for_file("Dockerfile")
        
        assert schema1 is schema2


class TestSchemaFileLoading:
    """Tests for loading schemas from files."""

    @pytest.fixture
    def temp_schema_dir(self):
        """Create temporary directory for schema files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_load_schema_from_json(self, temp_schema_dir):
        """Test loading schema from JSON file."""
        schema_data = {
            "name": "JSON Schema",
            "extensions": ["*.json"],
            "mime_types": ["application/json"],
            "description": "A JSON file schema",
            "validation_rules": [
                {
                    "type": "json_syntax",
                    "required": True
                }
            ]
        }

        schema_file = temp_schema_dir / "json_schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)

        registry = SchemaRegistry()
        registry.load_from_file(schema_file)

        assert registry.has_schema("json_schema")
        schema = registry.get("json_schema")
        assert schema.name == "JSON Schema"
        assert "*.json" in schema.extensions

    def test_load_schema_from_yaml(self, temp_schema_dir):
        """Test loading schema from YAML file."""
        yaml_content = """
name: YAML Schema
extensions:
  - "*.yaml"
  - "*.yml"
mime_types:
  - application/x-yaml
  - text/yaml
description: A YAML file schema
validation_rules:
  - type: yaml_syntax
    required: true
""".strip()

        schema_file = temp_schema_dir / "yaml_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(yaml_content)

        registry = SchemaRegistry()
        registry.load_from_file(schema_file)

        assert registry.has_schema("yaml_schema")
        schema = registry.get("yaml_schema")
        assert schema.name == "YAML Schema"
        assert "*.yaml" in schema.extensions

    def test_load_schema_directory(self, temp_schema_dir):
        """Test loading all schemas from a directory."""
        # Create multiple schema files
        schemas = {
            "schema1.json": {
                "name": "Schema 1",
                "extensions": ["*.s1"],
                "mime_types": ["application/x-s1"]
            },
            "schema2.yaml": """
name: Schema 2
extensions:
  - "*.s2"
mime_types:
  - application/x-s2
""".strip()
        }

        for filename, content in schemas.items():
            schema_file = temp_schema_dir / filename
            if filename.endswith('.json'):
                with open(schema_file, 'w') as f:
                    json.dump(content, f)
            else:
                with open(schema_file, 'w') as f:
                    f.write(content)

        registry = SchemaRegistry()
        registry.load_from_directory(temp_schema_dir)

        assert registry.has_schema("schema1")
        assert registry.has_schema("schema2")

    def test_load_invalid_schema_file(self, temp_schema_dir):
        """Test loading invalid schema file."""
        invalid_schema = temp_schema_dir / "invalid.json"
        with open(invalid_schema, 'w') as f:
            f.write("{ invalid json content")

        registry = SchemaRegistry()
        
        with pytest.raises(Exception):  # Should raise parsing error
            registry.load_from_file(invalid_schema)

    def test_load_schema_missing_required_fields(self, temp_schema_dir):
        """Test loading schema with missing required fields."""
        incomplete_schema = {
            "name": "Incomplete Schema"
            # Missing extensions
        }

        schema_file = temp_schema_dir / "incomplete.json"
        with open(schema_file, 'w') as f:
            json.dump(incomplete_schema, f)

        registry = SchemaRegistry()
        
        with pytest.raises(ValueError, match="Missing required field"):
            registry.load_from_file(schema_file)


class TestSchemaLifecycle:
    """Tests for schema lifecycle management."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_schema_versioning(self, registry):
        """Test schema versioning support."""
        v1_schema = FileFormatSchema(
            name="Versioned Schema",
            extensions=["*.v1"],
            version="1.0.0",
        )
        
        v2_schema = FileFormatSchema(
            name="Versioned Schema",
            extensions=["*.v2"],
            version="2.0.0",
        )

        registry.register("schema_v1", v1_schema)
        registry.register("schema_v2", v2_schema)

        assert registry.get_version("schema_v1", "1.0.0") is not None
        assert registry.get_version("schema_v2", "2.0.0") is not None
        assert registry.get_version("schema_v1", "2.0.0") is None

    def test_schema_deprecation(self, registry):
        """Test schema deprecation."""
        deprecated_schema = FileFormatSchema(
            name="Deprecated Schema",
            extensions=["*.old"],
            deprecated=True,
            deprecation_message="Use new_schema instead",
        )

        registry.register("deprecated", deprecated_schema)

        schema = registry.get("deprecated")
        assert schema.deprecated is True
        assert "new_schema" in schema.deprecation_message

    def test_schema_dependencies(self, registry):
        """Test schema dependencies."""
        base_schema = FileFormatSchema(
            name="Base Schema",
            extensions=["*.base"],
        )

        extended_schema = FileFormatSchema(
            name="Extended Schema",
            extensions=["*.ext"],
            dependencies=["base"],
        )

        registry.register("base", base_schema)
        registry.register("extended", extended_schema)

        # Check dependency resolution
        dependencies = registry.get_dependencies("extended")
        assert "base" in dependencies

    def test_schema_reload(self, registry):
        """Test reloading schemas."""
        original_schema = FileFormatSchema(
            name="Reload Test",
            extensions=["*.test"],
            version="1.0.0",
        )

        registry.register("reload", original_schema)
        assert registry.get("reload").version == "1.0.0"

        # Update schema
        updated_schema = FileFormatSchema(
            name="Reload Test Updated",
            extensions=["*.test"],
            version="2.0.0",
        )

        registry.reload("reload", updated_schema)
        assert registry.get("reload").version == "2.0.0"
        assert registry.get("reload").name == "Reload Test Updated"

    def test_schema_export_import(self, registry):
        """Test exporting and importing schemas."""
        # Create test schema
        test_schema = FileFormatSchema(
            name="Export Test",
            extensions=["*.export"],
            mime_types=["application/x-export"],
            description="A schema for testing export/import",
        )

        registry.register("export_test", test_schema)

        # Export schema
        exported = registry.export_schema("export_test")
        
        # Create new registry and import
        new_registry = SchemaRegistry()
        new_registry.import_schema("imported_test", exported)

        assert new_registry.has_schema("imported_test")
        imported = new_registry.get("imported_test")
        assert imported.name == "Export Test"
        assert "*.export" in imported.extensions


class TestSchemaValidation:
    """Tests for schema validation rules."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_validate_registry_integrity(self, registry):
        """Test registry integrity validation."""
        # Should pass for clean registry
        assert registry.validate_integrity()

        # Manually corrupt registry (simulate)
        registry._schemas["corrupted"] = "not a schema object"
        
        with pytest.raises(ValueError, match="Registry integrity"):
            registry.validate_integrity()

    def test_schema_self_validation(self, registry):
        """Test schema self-validation."""
        schema = registry.get("dockerfile")
        
        # Schema should validate itself
        assert schema.self_validate()

    def test_cross_schema_validation(self, registry):
        """Test cross-schema validation."""
        # Check for conflicting extensions
        conflicts = registry.find_extension_conflicts()
        
        # Should not have conflicts in clean registry
        assert len(conflicts) == 0

        # Add conflicting schema
        conflict_schema = FileFormatSchema(
            name="Conflict Test",
            extensions=["Dockerfile"],  # Same as built-in
        )
        registry.register("conflict", conflict_schema)

        conflicts = registry.find_extension_conflicts()
        assert len(conflicts) > 0
        assert any("Dockerfile" in conflict for conflict in conflicts)
