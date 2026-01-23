import json
from pathlib import Path

from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.core import NLP2CMD


def test_appspec_http_action_ir_renders_curl_with_base_url_and_locations(tmp_path: Path):
    appspec = {
        "format": "app2schema.appspec",
        "version": 1,
        "app": {"name": "Test API", "kind": "http", "source": "inline", "metadata": {}},
        "actions": [
            {
                "id": "http.getUser",
                "type": "http",
                "description": "Get user",
                "dsl": {"kind": "http", "output_format": "raw"},
                "params": {
                    "userId": {"type": "string", "required": True, "location": "path"},
                    "verbose": {"type": "boolean", "required": False, "location": "query"},
                },
                "schema": {"method": "GET", "path": "/users/{userId}", "base_url": "https://example.test"},
                "match": {"patterns": ["get user"], "examples": []},
                "executor": {"kind": "http", "config": {}},
                "metadata": {},
                "tags": [],
            }
        ],
        "metadata": {},
    }

    appspec_path = tmp_path / "appspec.json"
    appspec_path.write_text(json.dumps(appspec), encoding="utf-8")

    adapter = AppSpecAdapter(appspec_path=appspec_path)
    nlp = NLP2CMD(adapter=adapter)

    ir = nlp.transform_ir("get user userId=123 verbose=true")
    assert ir.dsl.startswith("curl -X GET ")
    assert "https://example.test/users/123" in ir.dsl
    assert "verbose=True" in ir.dsl or "verbose=true" in ir.dsl


def test_transform_ir_is_available_for_appspec_adapter(tmp_path: Path):
    appspec = {
        "format": "app2schema.appspec",
        "version": 1,
        "app": {"name": "Demo", "kind": "shell", "source": "inline", "metadata": {}},
        "actions": [
            {
                "id": "shell.echo",
                "type": "shell",
                "description": "echo",
                "dsl": {"kind": "shell", "output_format": "raw", "template": "echo {text}"},
                "params": {"text": {"type": "string", "required": True, "location": "arg"}},
                "schema": {"command": "echo"},
                "match": {"patterns": ["echo"], "examples": []},
                "executor": {"kind": "shell", "config": {}},
                "metadata": {},
                "tags": [],
            }
        ],
        "metadata": {},
    }
    appspec_path = tmp_path / "appspec.json"
    appspec_path.write_text(json.dumps(appspec), encoding="utf-8")

    nlp = NLP2CMD(adapter=AppSpecAdapter(appspec_path=appspec_path))
    ir = nlp.transform_ir("echo text=hello")
    assert ir.to_dict()["format"] == "nlp2cmd.action_ir"
