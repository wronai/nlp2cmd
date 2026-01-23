import json
from pathlib import Path

import pytest

from app2schema.extract import App2SchemaResult, extract_appspec_to_file, extract_schema
from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.core import NLP2CMD
from nlp2cmd.schema_extraction import (
    CommandParameter,
    CommandSchema,
    ExtractedSchema,
)


def _make_demo_appspec_file(tmp_path: Path) -> Path:
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
    payload = export.to_appspec_dict()

    out = tmp_path / "appspec.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def test_app2schema_appspec_format(tmp_path: Path):
    out = _make_demo_appspec_file(tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))

    assert data["format"] == "app2schema.appspec"
    assert data["version"] == 1
    assert "app" in data
    assert "actions" in data
    assert any(a.get("id", "").startswith("shell.") for a in data.get("actions", []))


def test_appspec_adapter_produces_action_ir(tmp_path: Path):
    appspec_file = _make_demo_appspec_file(tmp_path)

    adapter = AppSpecAdapter(appspec_path=appspec_file)
    nlp = NLP2CMD(adapter=adapter)

    ir = nlp.transform_ir("demo cmd")
    assert ir.action_id
    assert ir.dsl is not None
    assert ir.to_dict()["format"] == "nlp2cmd.action_ir"


def test_app2schema_extract_shell_script_auto(tmp_path: Path):
    script_path = tmp_path / "demo.sh"
    script_path.write_text(
        """#!/usr/bin/env bash
# Demo script
# Usage: demo.sh [--name NAME] [-v]

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      NAME="$2"; shift 2;;
    -v)
      VERBOSE=1; shift;;
    *)
      shift;;
  esac
done
""",
        encoding="utf-8",
    )

    out_path = tmp_path / "appspec.json"
    written = extract_appspec_to_file(script_path, out_path, source_type="auto")
    assert written.exists()

    adapter = AppSpecAdapter(appspec_path=written)
    nlp = NLP2CMD(adapter=adapter)

    ir = nlp.transform_ir("demo.sh --name x")
    assert ir.action_id
    assert ir.dsl is not None
    assert ir.to_dict()["format"] == "nlp2cmd.action_ir"


def test_app2schema_extract_makefile_auto(tmp_path: Path):
    makefile_path = tmp_path / "Makefile"
    makefile_path.write_text(
        """# Build targets
NAME = demo

.PHONY: test
test:
\techo running tests for $(NAME)
""",
        encoding="utf-8",
    )

    out_path = tmp_path / "appspec.json"
    written = extract_appspec_to_file(makefile_path, out_path, source_type="auto")
    assert written.exists()

    adapter = AppSpecAdapter(appspec_path=written)
    nlp = NLP2CMD(adapter=adapter)

    ir = nlp.transform_ir("make test")
    assert ir.action_id
    assert ir.dsl is not None
    assert ir.to_dict()["format"] == "nlp2cmd.action_ir"


def test_app2schema_extract_schema_to_file_roundtrip_shell_script(tmp_path: Path):
    script_path = tmp_path / "demo.sh"
    script_path.write_text(
        """#!/usr/bin/env bash
# Usage: demo.sh [-v]
getopts "v" opt
""",
        encoding="utf-8",
    )

    out_path = tmp_path / "appspec.json"
    written = extract_appspec_to_file(script_path, out_path, source_type="auto")
    assert written.exists()

    nlp = NLP2CMD(adapter=AppSpecAdapter(appspec_path=written))
    ir = nlp.transform_ir("demo v=true")
    assert ir.to_dict()["format"] == "nlp2cmd.action_ir"
