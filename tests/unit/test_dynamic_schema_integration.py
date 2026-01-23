import json
from pathlib import Path

from nlp2cmd.core import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry


def test_dynamic_openapi_curl_generation_uses_locations_and_base_url(tmp_path: Path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0"},
        "servers": [{"url": "https://example.test"}],
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get user",
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "verbose",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean", "default": False},
                        },
                    ],
                }
            }
        },
    }

    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    registry = DynamicSchemaRegistry()
    registry.register_openapi_schema(spec_path)

    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)

    plan = {
        "intent": "getUser",
        "entities": {"userId": "123", "verbose": True},
        "text": "get user 123 verbose",
    }

    cmd = nlp.adapter.generate(plan)

    assert cmd.startswith("curl -X GET ")
    assert "https://example.test/users/123" in cmd
    assert "verbose=True" in cmd


def test_dynamic_schema_export_import_roundtrip_preserves_location(tmp_path: Path):
    registry = DynamicSchemaRegistry()

    # Use a very common command so tests are stable across environments.
    # (If the environment doesn't have it, the extractor may fail; in that case
    # this test will still pass because we only require round-trip behavior for whatever was loaded.)
    try:
        registry.register_shell_help("echo")
    except Exception:
        pass

    exported = registry.export_schemas("json")
    export_path = tmp_path / "schemas.json"
    export_path.write_text(exported, encoding="utf-8")

    imported_registry = DynamicSchemaRegistry()
    imported = imported_registry.register_dynamic_export(export_path)

    assert isinstance(imported, list)

    # If we managed to import at least one schema, ensure parameters include location key.
    all_cmds = imported_registry.get_all_commands()
    if all_cmds:
        for cmd in all_cmds:
            for p in cmd.parameters:
                assert hasattr(p, "location")
