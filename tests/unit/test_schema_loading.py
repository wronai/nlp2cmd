"""
Test schema loading and registration functionality.

This module tests schema registry, built-in schemas,
and custom schema registration capabilities.
"""

import pytest
from pathlib import Path
import tempfile
import os

from src.nlp2cmd.schemas import SchemaRegistry, FileFormatSchema


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return SchemaRegistry()

    def test_builtin_schemas_registered(self):
        """Test that built-in schemas are registered."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        assert registry.has_schema("dockerfile")
        assert registry.has_schema("docker-compose")
        assert registry.has_schema("kubernetes-deployment")
        assert registry.has_schema("github-workflow")
        assert registry.has_schema("env-file")

    def test_get_schema(self):
        """Test getting schema by name."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")

        assert schema is not None
        assert schema.name == "Dockerfile"
        assert "Dockerfile" in schema.extensions

    def test_get_nonexistent_schema(self):
        """Test getting non-existent schema."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("nonexistent")
        assert schema is None

    def test_register_custom_schema(self):
        """Test registering custom schema."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        
        custom_schema = FileFormatSchema(
            name="Custom Format",
            extensions=["*.custom"],
            mime_types=["application/x-custom"],
            validator=lambda c: {"valid": True, "errors": [], "warnings": []},
            parser=lambda c: {"content": c},
            generator=lambda d: d.get("content", ""),
        )

        registry.register("custom", custom_schema)

        assert registry.has_schema("custom")
        retrieved = registry.get("custom")
        assert retrieved.name == "Custom Format"

    def test_list_schemas(self):
        """Test listing all schemas."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schemas = registry.list_schemas()

        assert isinstance(schemas, list)
        assert len(schemas) > 0
        assert all(isinstance(name, str) for name in schemas)

    def test_unregister_schema(self):
        """Test unregistering a schema."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        
        # First register a custom schema
        custom_schema = FileFormatSchema(
            name="Test Schema",
            extensions=["*.test"],
            mime_types=["application/x-test"],
            validator=lambda c: {"valid": True, "errors": [], "warnings": []},
            parser=lambda c: {"content": c},
            generator=lambda d: d.get("content", ""),
        )
        registry.register("test", custom_schema)

        assert registry.has_schema("test")

        # Unregister it
        registry.unregister("test")

        assert not registry.has_schema("test")

    def test_unregister_builtin_schema(self):
        """Test that built-in schemas cannot be unregistered."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        
        with pytest.raises(ValueError, match="Cannot unregister built-in schema"):
            registry.unregister("dockerfile")

    def test_schema_metadata(self):
        """Test schema metadata."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        
        assert hasattr(schema, 'name')
        assert hasattr(schema, 'extensions')
        assert hasattr(schema, 'mime_types')
        assert hasattr(schema, 'description')

    def test_schema_extensions_case_insensitive(self):
        """Test that schema extensions are case insensitive."""
        from src.nlp2cmd.schemas import SchemaRegistry
        registry = SchemaRegistry()
        schema = registry.get("dockerfile")
        
        # Should match various case combinations
        assert registry.find_schema_for_file("Dockerfile") is not None
        assert registry.find_schema_for_file("dockerfile") is not None
        assert registry.find_schema_for_file("DOCKERFILE") is not None
        assert registry.find_schema_for_file("Dockerfile.*") is not None


class TestFileFormatSchema:
    """Tests for FileFormatSchema."""

    def test_schema_creation(self):
        """Test creating a schema."""
        def dummy_validator(content):
            return {"valid": True, "errors": [], "warnings": []}
        
        def dummy_parser(content):
            return {"parsed": content}
        
        def dummy_generator(data):
            return data.get("content", "")
        
        schema = FileFormatSchema(
            name="Test Schema",
            extensions=["*.test", "*.example"],
            mime_types=["application/x-test"],
            validator=dummy_validator,
            parser=dummy_parser,
            generator=dummy_generator,
            description="A test schema for testing"
        )
        
        assert schema.name == "Test Schema"
        assert "*.test" in schema.extensions
        assert "*.example" in schema.extensions
        assert "application/x-test" in schema.mime_types
        assert schema.description == "A test schema for testing"

    def test_schema_validation_interface(self):
        """Test schema validation interface."""
        def test_validator(content):
            if "invalid" in content:
                return {"valid": False, "errors": ["Contains invalid content"], "warnings": []}
            return {"valid": True, "errors": [], "warnings": []}
        
        def test_parser(content):
            return {"parsed": content}
        
        def test_generator(data):
            return data.get("content", "")
        
        schema = FileFormatSchema(
            name="Test Schema",
            extensions=["*.test"],
            mime_types=["application/x-test"],
            validator=test_validator,
            parser=test_parser,
            generator=test_generator
        )

        # Test valid content
        result = schema.validate("valid content")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # Test invalid content
        result = schema.validate("invalid content")
        assert result["valid"] is False
        assert len(result["errors"]) == 1

    def test_schema_parser_interface(self):
        """Test schema parser interface."""
        def test_parser(content):
            return {"parsed": content.upper(), "lines": content.split('\n')}
        
        def test_generator(data):
            return data.get("content", "")
        
        schema = FileFormatSchema(
            name="Test Schema",
            extensions=["*.test"],
            mime_types=["application/x-test"],
            validator=lambda c: {"valid": True, "errors": [], "warnings": []},
            parser=test_parser,
            generator=test_generator
        )

        result = schema.parse("test content")
        assert result["parsed"] == "TEST CONTENT"
        assert "test content" in result["lines"]

    def test_schema_generator_interface(self):
        """Test schema generator interface."""
        def test_generator(data):
            return f"Generated: {data.get('value', '')}"

        schema = FileFormatSchema(
            name="Test Schema",
            extensions=["*.test"],
            generator=test_generator,
        )

        result = schema.generate({"value": "test"})
        assert result == "Generated: test"

    def test_schema_with_all_interfaces(self):
        """Test schema with all interfaces implemented."""
        def validator(content):
            return {"valid": len(content) > 0, "errors": [], "warnings": []}

        def parser(content):
            return {"length": len(content), "words": content.split()}

        def generator(data):
            return " ".join(data.get("words", []))

        schema = FileFormatSchema(
            name="Complete Schema",
            extensions=["*.complete"],
            mime_types=["application/x-complete"],
            validator=validator,
            parser=parser,
            generator=generator,
        )

        # Test full cycle
        content = "hello world test"
        validation = schema.validate(content)
        assert validation["valid"] is True

        parsed = schema.parse(content)
        assert parsed["length"] == 16  # "hello world test" has 16 characters
        assert "hello" in parsed["words"]

        generated = schema.generate(parsed)
        assert generated == content

    def test_schema_extension_patterns(self):
        """Test various extension patterns."""
        schema = FileFormatSchema(
            name="Pattern Schema",
            extensions=["*.py", "Dockerfile*", "config.*", "README*"],
        )

        # Test various patterns
        assert schema.matches_extension("test.py")
        assert schema.matches_extension("Dockerfile.dev")
        assert schema.matches_extension("config.yaml")
        assert schema.matches_extension("README.md")
        
        # Test non-matching
        assert not schema.matches_extension("test.txt")
        assert not schema.matches_extension("Dockerfile.txt.backup")

    def test_schema_mime_type_matching(self):
        """Test MIME type matching."""
        schema = FileFormatSchema(
            name="MIME Schema",
            mime_types=["application/json", "text/yaml", "application/x-yaml"],
        )

        assert schema.matches_mime_type("application/json")
        assert schema.matches_mime_type("text/yaml")
        assert not schema.matches_mime_type("text/plain")
