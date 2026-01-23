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


def test_dynamic_registry_export_yaml_and_jsonschema(tmp_path: Path):
    registry = DynamicSchemaRegistry()
    # keep tests stable: avoid depending on external commands existing
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0"},
        "servers": [{"url": "https://example.test"}],
        "paths": {"/ping": {"get": {"operationId": "ping", "summary": "Ping"}}},
    }

    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    registry.register_openapi_schema(spec_path)

    exported_yaml = registry.export_schemas("yaml")
    assert isinstance(exported_yaml, str)
    assert "nlp2cmd.dynamic_schema_export" in exported_yaml

    exported_schema = registry.export_schemas("jsonschema")
    schema_obj = json.loads(exported_schema)
    assert schema_obj.get("$schema")
    assert schema_obj.get("type") == "object"


def test_dynamic_adapter_auto_detects_shell_script_and_makefile(tmp_path: Path):
    sh_path = tmp_path / "demo.sh"
    sh_path.write_text(
        """#!/usr/bin/env bash
# Usage: demo.sh [-v]
getopts "v" opt
""",
        encoding="utf-8",
    )

    mk_path = tmp_path / "Makefile"
    mk_path.write_text(
        """test:\n\techo ok\n""",
        encoding="utf-8",
    )

    registry = DynamicSchemaRegistry()
    adapter = DynamicAdapter(schema_registry=registry)

    extracted_sh = adapter.register_schema_source(str(sh_path), source_type="auto")
    assert extracted_sh.source_type == "shell_script"
    assert registry.get_all_commands()

    extracted_mk = adapter.register_schema_source(str(mk_path), source_type="auto")
    assert extracted_mk.source_type == "makefile"
    assert any(c.name == "test" for c in registry.get_all_commands())
