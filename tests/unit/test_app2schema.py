import json
from pathlib import Path

import pytest

from app2schema.extract import App2SchemaResult
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import (
    CommandParameter,
    CommandSchema,
    DynamicSchemaRegistry,
    ExtractedSchema,
)


def _make_demo_export_file(tmp_path: Path) -> Path:
    schema = ExtractedSchema(
        source="demo",
        source_type="shell_help",
        commands=[
            CommandSchema(
                name="demo_cmd",
                description="Demo command",
                category="demo",
                parameters=[
                    CommandParameter(
                        name="flag",
                        type="boolean",
                        description="A demo flag",
                        required=False,
                    ),
                    CommandParameter(
                        name="value",
                        type="string",
                        description="A demo value",
                        required=True,
                    ),
                ],
                examples=["demo_cmd --flag --value x"],
                patterns=["demo cmd"],
                source_type="shell_help",
                metadata={"command": "demo_cmd"},
            )
        ],
        metadata={"title": "Demo"},
    )

    export = App2SchemaResult(schemas=[schema], detected_type="shell")
    payload = export.to_export_dict(raw=False)

    out = tmp_path / "app2schema_export.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def test_app2schema_export_format(tmp_path: Path):
    out = _make_demo_export_file(tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))

    assert data["format"] == "nlp2cmd.dynamic_schema_export"
    assert data["version"] == 1
    assert data["detected_type"] == "shell"
    assert "sources" in data
    assert "demo" in data["sources"]


def test_dynamic_registry_register_dynamic_export(tmp_path: Path):
    export_file = _make_demo_export_file(tmp_path)

    registry = DynamicSchemaRegistry()
    imported = registry.register_dynamic_export(export_file)

    assert len(imported) == 1
    assert imported[0].source == "demo"
    assert len(imported[0].commands) == 1
    assert imported[0].commands[0].name == "demo_cmd"


def test_dynamic_adapter_auto_imports_app2schema_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    export_file = _make_demo_export_file(tmp_path)

    monkeypatch.setattr(DynamicAdapter, "_load_common_commands", lambda self: None)

    adapter = DynamicAdapter(schema_registry=DynamicSchemaRegistry())
    extracted = adapter.register_schema_source(str(export_file), source_type="auto")

    assert extracted.source_type == "dynamic_export_bundle"
    assert any(cmd.name == "demo_cmd" for cmd in extracted.commands)
    assert adapter.registry.get_command_by_name("demo_cmd") is not None
