from __future__ import annotations

import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
import re
import unicodedata
from pathlib import Path
from typing import Any, Literal, Optional, Union

import httpx
from jsonschema import Draft7Validator

from nlp2cmd.schema_extraction import (
    ExtractedSchema,
    MakefileExtractor,
    OpenAPISchemaExtractor,
    PythonCodeExtractor,
    ShellScriptExtractor,
    ShellHelpExtractor,
    CommandParameter,
    CommandSchema,
)


SourceType = Literal[
    "auto",
    "openapi",
    "shell",
    "python",
    "python_package",
    "shell_script",
    "makefile",
    "web",
    "web_runtime",
]


APP2SCHEMA_APPSPEC_JSON_SCHEMA_V1: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["format", "version", "app", "actions"],
    "properties": {
        "format": {"type": "string", "const": "app2schema.appspec"},
        "version": {"type": "integer", "minimum": 1},
        "app": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "kind", "source", "metadata"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "kind": {"type": "string"},
                "source": {"type": "string"},
                "metadata": {"type": "object"},
            },
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "id",
                    "type",
                    "description",
                    "dsl",
                    "params",
                    "schema",
                    "match",
                    "executor",
                    "metadata",
                    "tags",
                ],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "type": {"type": "string", "minLength": 1},
                    "description": {"type": "string"},
                    "dsl": {
                        "type": "object",
                        "additionalProperties": True,
                        "required": ["kind", "output_format"],
                        "properties": {
                            "kind": {"type": "string"},
                            "output_format": {"type": "string"},
                            "template": {},
                        },
                    },
                    "params": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "additionalProperties": True,
                            "required": ["type", "required"],
                            "properties": {
                                "type": {"type": "string"},
                                "required": {"type": "boolean"},
                                "description": {"type": "string"},
                                "default": {},
                                "enum": {"type": "array", "items": {"type": "string"}},
                                "pattern": {"type": ["string", "null"]},
                                "location": {"type": "string"},
                            },
                        },
                    },
                    "schema": {"type": "object"},
                    "match": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["patterns", "examples"],
                        "properties": {
                            "patterns": {"type": "array", "items": {"type": "string"}},
                            "examples": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "executor": {
                        "type": "object",
                        "additionalProperties": True,
                        "required": ["kind", "config"],
                        "properties": {
                            "kind": {"type": "string"},
                            "config": {"type": "object"},
                        },
                    },
                    "metadata": {"type": "object"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "metadata": {"type": "object"},
    },
}


def validate_appspec(payload: dict[str, Any]) -> None:
    validator = Draft7Validator(APP2SCHEMA_APPSPEC_JSON_SCHEMA_V1)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = "/".join(str(p) for p in first.path)
        raise ValueError(f"app2schema appspec validation failed at '{path}': {first.message}")


def _slugify(value: str) -> str:
    txt = unicodedata.normalize("NFKD", value)
    txt = txt.encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"[^a-zA-Z0-9]+", "-", txt).strip("-").lower()
    return txt or "item"


class _SimpleDomParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._stack: list[dict[str, Any]] = []
        self.elements: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        attr_dict = {k: (v if v is not None else "") for k, v in attrs}
        node = {"tag": tag.lower(), "attrs": attr_dict, "text": ""}
        self._stack.append(node)

    def handle_endtag(self, tag: str):
        if not self._stack:
            return
        node = self._stack.pop()
        if node.get("tag") != tag.lower():
            return
        self.elements.append(node)

    def handle_data(self, data: str):
        if not self._stack:
            return
        txt = (data or "").strip()
        if not txt:
            return
        self._stack[-1]["text"] = (self._stack[-1].get("text") or "") + " " + txt


def _extract_web_dom_schema(
    target: str,
    *,
    http_client: Optional[httpx.Client] = None,
    runtime: bool = False,
) -> ExtractedSchema:
    html = ""
    source = target
    base_url: Optional[str] = None

    if target.startswith(("http://", "https://")):
        if runtime:
            try:
                from playwright.sync_api import sync_playwright  # type: ignore
            except Exception as e:
                raise ImportError("Playwright is required for web_runtime extraction") from e

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(target)
                page.wait_for_timeout(1000)
                html = page.content()
                base_url = str(page.url)
                browser.close()
        else:
            http = http_client or httpx.Client(follow_redirects=True, timeout=10.0)
            close_client = http_client is None
            try:
                resp = http.get(target)
                resp.raise_for_status()
                html = resp.text
                base_url = str(resp.url)
            finally:
                if close_client:
                    http.close()
    else:
        p = Path(target)
        if p.exists() and p.is_file():
            html = p.read_text(encoding="utf-8", errors="replace")
            source = str(p)
        else:
            html = target
            source = "inline_html"

    parser = _SimpleDomParser()
    parser.feed(html)

    commands: list[CommandSchema] = []
    seen_names: set[str] = set()

    def add_command(cmd: CommandSchema) -> None:
        if cmd.name in seen_names:
            i = 2
            base = cmd.name
            while f"{base}_{i}" in seen_names:
                i += 1
            cmd.name = f"{base}_{i}"
        seen_names.add(cmd.name)
        commands.append(cmd)

    for el in parser.elements:
        tag = str(el.get("tag") or "").lower()
        attrs = dict(el.get("attrs") or {})
        text = str(el.get("text") or "").strip()
        el_id = str(attrs.get("id") or "").strip()
        el_name = str(attrs.get("name") or "").strip()
        aria_label = str(attrs.get("aria-label") or "").strip()
        placeholder = str(attrs.get("placeholder") or "").strip()
        input_type = str(attrs.get("type") or "").strip().lower()

        selector = ""
        if el_id:
            selector = f"#{el_id}"
        elif el_name:
            selector = f"{tag}[name=\"{el_name}\"]"
        elif aria_label:
            selector = f"{tag}[aria-label=\"{aria_label}\"]"
        elif placeholder and tag in {"input", "textarea"}:
            selector = f"{tag}[placeholder=\"{placeholder}\"]"
        elif text and len(text) <= 60 and tag in {"button", "a"}:
            selector = f"text={text}"

        if tag in {"button", "a"}:
            title = text or aria_label or el_id or el_name or tag
            slug = _slugify(title)
            add_command(
                CommandSchema(
                    name=f"gui.click.{slug}",
                    description=f"click {title}".strip(),
                    category="web",
                    parameters=[],
                    examples=[],
                    patterns=["click", "kliknij", "press", "button", title.lower() if title else ""],
                    source_type="web_dom",
                    metadata={
                        "action": "click",
                        "selector": selector,
                        "tag": tag,
                        "text": text,
                        "id": el_id,
                        "name": el_name,
                        "input_type": input_type,
                        "base_url": base_url,
                    },
                )
            )
            continue

        if tag in {"input", "textarea"}:
            if input_type in {"submit", "button", "reset"}:
                continue
            title = aria_label or placeholder or el_id or el_name or tag
            slug = _slugify(title)
            add_command(
                CommandSchema(
                    name=f"gui.type.{slug}",
                    description=f"type into {title}".strip(),
                    category="web",
                    parameters=[
                        CommandParameter(
                            name="value",
                            type="string",
                            description="",
                            required=True,
                            location="body",
                        )
                    ],
                    examples=[],
                    patterns=["type", "fill", "wpisz", title.lower() if title else ""],
                    source_type="web_dom",
                    metadata={
                        "action": "type",
                        "selector": selector,
                        "tag": tag,
                        "text": text,
                        "id": el_id,
                        "name": el_name,
                        "input_type": input_type,
                        "base_url": base_url,
                    },
                )
            )
            continue

        if tag == "select":
            title = aria_label or el_id or el_name or tag
            slug = _slugify(title)
            add_command(
                CommandSchema(
                    name=f"gui.select.{slug}",
                    description=f"select option in {title}".strip(),
                    category="web",
                    parameters=[
                        CommandParameter(
                            name="value",
                            type="string",
                            description="",
                            required=True,
                            location="body",
                        )
                    ],
                    examples=[],
                    patterns=["select", "choose", "wybierz", title.lower() if title else ""],
                    source_type="web_dom",
                    metadata={
                        "action": "select",
                        "selector": selector,
                        "tag": tag,
                        "text": text,
                        "id": el_id,
                        "name": el_name,
                        "base_url": base_url,
                    },
                )
            )

    return ExtractedSchema(
        source=source,
        source_type="web_dom",
        commands=commands,
        metadata={"base_url": base_url},
    )


@dataclass
class App2SchemaResult:
    schemas: list[ExtractedSchema]
    detected_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_appspec_dict(self) -> dict[str, Any]:
        actions: list[dict[str, Any]] = []

        app_name = "app"
        app_kind = self.detected_type
        app_source = self.metadata.get("target") or ""

        for extracted in self.schemas:
            if extracted.metadata.get("title"):
                app_name = str(extracted.metadata.get("title"))

            for cmd in extracted.commands:
                action_type = cmd.source_type
                dsl_kind = "shell"

                if cmd.source_type == "openapi":
                    action_type = "http"
                    dsl_kind = "http"
                elif cmd.source_type in {"python_click", "python_generic"}:
                    action_type = "python"
                    dsl_kind = "python"
                elif cmd.source_type == "shell_help":
                    action_type = "shell"
                    dsl_kind = "shell"

                action_id = f"{action_type}.{cmd.name}"

                params: dict[str, Any] = {}
                for p in cmd.parameters:
                    params[p.name] = {
                        "type": p.type,
                        "required": p.required,
                        "description": p.description,
                        "default": p.default,
                        "enum": p.choices,
                        "pattern": p.pattern,
                        "location": p.location,
                    }

                actions.append(
                    {
                        "id": action_id,
                        "type": action_type,
                        "description": cmd.description,
                        "dsl": {
                            "kind": dsl_kind,
                            "output_format": "raw",
                            "template": cmd.metadata.get("template"),
                        },
                        "params": params,
                        "schema": cmd.metadata,
                        "match": {"patterns": cmd.patterns, "examples": cmd.examples},
                        "executor": {"kind": dsl_kind, "config": {}},
                        "metadata": {"source": extracted.source, "source_type": extracted.source_type},
                        "tags": list(cmd.metadata.get("tags", []) or []),
                    }
                )

        return {
            "format": "app2schema.appspec",
            "version": 1,
            "app": {
                "name": app_name,
                "kind": app_kind,
                "source": app_source,
                "metadata": self.metadata,
            },
            "actions": actions,
            "metadata": {},
        }


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def discover_openapi_spec_url(
    base_url: str,
    *,
    client: Optional[httpx.Client] = None,
    timeout_s: float = 5.0,
) -> Optional[str]:
    base_url = _normalize_base_url(base_url)

    if any(base_url.endswith(ext) for ext in (".json", ".yaml", ".yml")):
        return base_url

    candidates = [
        f"{base_url}/openapi.json",
        f"{base_url}/openapi.yaml",
        f"{base_url}/openapi.yml",
        f"{base_url}/swagger.json",
        f"{base_url}/swagger.yaml",
        f"{base_url}/swagger.yml",
        f"{base_url}/v3/api-docs",
        f"{base_url}/v3/api-docs.yaml",
        f"{base_url}/v3/api-docs.yml",
    ]

    http = client or httpx.Client(follow_redirects=True, timeout=timeout_s)
    close_client = client is None

    try:
        for url in candidates:
            try:
                resp = http.get(url)
                if resp.status_code >= 400:
                    continue

                content_type = (resp.headers.get("content-type") or "").lower()
                if "json" in content_type:
                    try:
                        data = resp.json()
                    except Exception:
                        continue

                    if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                        return url

                if "yaml" in content_type or url.endswith((".yaml", ".yml")):
                    # Heuristic: avoid importing yaml here; OpenAPISchemaExtractor will parse.
                    text = resp.text
                    if "openapi:" in text or "swagger:" in text:
                        return url
            except httpx.HTTPError:
                continue

        return None
    finally:
        if close_client:
            http.close()


def extract_schema(
    target: Union[str, Path],
    *,
    source_type: SourceType = "auto",
    discover_openapi: bool = True,
    http_client: Optional[httpx.Client] = None,
) -> App2SchemaResult:
    target_str = str(target)

    openapi_extractor = OpenAPISchemaExtractor(http_client=http_client)
    shell_extractor = ShellHelpExtractor()
    python_extractor = PythonCodeExtractor()
    shell_script_extractor = ShellScriptExtractor()
    makefile_extractor = MakefileExtractor()

    def extract_python_package(dir_path: Path, max_files: int = 100) -> App2SchemaResult:
        py_files = [p for p in sorted(dir_path.rglob("*.py")) if "__pycache__" not in p.parts]
        truncated = False
        if len(py_files) > max_files:
            py_files = py_files[:max_files]
            truncated = True

        schemas: list[ExtractedSchema] = []
        for p in py_files:
            try:
                schemas.append(python_extractor.extract_from_file(p))
            except Exception:
                continue

        return App2SchemaResult(
            schemas=schemas,
            detected_type="python_package",
            metadata={
                "target": str(dir_path),
                "python_files": len(py_files),
                "truncated": truncated,
            },
        )

    if source_type == "auto":
        if target_str.startswith(("http://", "https://")):
            detected = "openapi"

            spec_url = target_str
            if discover_openapi:
                discovered = discover_openapi_spec_url(target_str, client=http_client)
                if discovered:
                    spec_url = discovered

            schema = openapi_extractor.extract_from_url(spec_url)
            return App2SchemaResult(
                schemas=[schema],
                detected_type=detected,
                metadata={"target": target_str, "spec_url": spec_url},
            )

        p = Path(target_str)
        if p.exists():
            if p.is_dir():
                # Python package/directory
                if (p / "__init__.py").exists() or any(p.glob("*.py")):
                    return extract_python_package(p)
            if p.suffix in {".json", ".yaml", ".yml"}:
                schema = openapi_extractor.extract_from_file(p)
                return App2SchemaResult(
                    schemas=[schema],
                    detected_type="openapi",
                    metadata={"target": target_str},
                )
            if p.suffix in {".py", ".pyx"}:
                schema = python_extractor.extract_from_file(p)
                return App2SchemaResult(
                    schemas=[schema],
                    detected_type="python",
                    metadata={"target": target_str},
                )
            if p.suffix == ".sh":
                schema = shell_script_extractor.extract_from_file(p)
                return App2SchemaResult(
                    schemas=[schema],
                    detected_type="shell_script",
                    metadata={"target": target_str},
                )
            if p.name == "Makefile" or p.suffix == ".mk":
                schema = makefile_extractor.extract_from_file(p)
                return App2SchemaResult(
                    schemas=[schema],
                    detected_type="makefile",
                    metadata={"target": target_str},
                )
            if p.suffix in {".html", ".htm"}:
                schema = _extract_web_dom_schema(str(p), http_client=http_client)
                return App2SchemaResult(
                    schemas=[schema],
                    detected_type="web",
                    metadata={"target": target_str},
                )

        schema = shell_extractor.extract_from_command(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="shell",
            metadata={"target": target_str},
        )

    if source_type == "openapi":
        if target_str.startswith(("http://", "https://")):
            spec_url = target_str
            if discover_openapi:
                discovered = discover_openapi_spec_url(target_str, client=http_client)
                if discovered:
                    spec_url = discovered
            schema = openapi_extractor.extract_from_url(spec_url)
            return App2SchemaResult(
                schemas=[schema],
                detected_type="openapi",
                metadata={"target": target_str, "spec_url": spec_url},
            )

        schema = openapi_extractor.extract_from_file(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="openapi",
            metadata={"target": target_str},
        )

    if source_type == "shell":
        schema = shell_extractor.extract_from_command(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="shell",
            metadata={"target": target_str},
        )

    if source_type == "shell_script":
        schema = shell_script_extractor.extract_from_file(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="shell_script",
            metadata={"target": target_str},
        )

    if source_type == "makefile":
        schema = makefile_extractor.extract_from_file(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="makefile",
            metadata={"target": target_str},
        )

    if source_type == "python":
        p = Path(target_str)
        if p.exists():
            if p.is_dir():
                return extract_python_package(p)
            schema = python_extractor.extract_from_file(p)
            return App2SchemaResult(
                schemas=[schema],
                detected_type="python",
                metadata={"target": target_str},
            )

        schema = python_extractor.extract_from_source(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="python",
            metadata={"target": target_str},
        )

    if source_type == "python_package":
        p = Path(target_str)
        if not p.exists() or not p.is_dir():
            raise FileNotFoundError(f"Python package directory not found: {target_str}")
        return extract_python_package(p)

    if source_type == "web":
        schema = _extract_web_dom_schema(target_str, http_client=http_client, runtime=False)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="web",
            metadata={"target": target_str},
        )

    if source_type == "web_runtime":
        schema = _extract_web_dom_schema(target_str, http_client=http_client, runtime=True)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="web",
            metadata={"target": target_str},
        )

    raise ValueError(f"Unsupported source_type: {source_type}")


def extract_appspec_to_file(
    target: Union[str, Path],
    out_path: Union[str, Path],
    *,
    source_type: SourceType = "auto",
    discover_openapi: bool = True,
    validate: bool = True,
    merge: bool = False,
) -> Path:
    result = extract_schema(
        target,
        source_type=source_type,
        discover_openapi=discover_openapi,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_appspec_dict()

    if merge and out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            existing = None

        if isinstance(existing, dict) and existing.get("format") == "app2schema.appspec":
            existing_actions = existing.get("actions") if isinstance(existing.get("actions"), list) else []
            new_actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []

            merged_by_id: dict[str, dict[str, Any]] = {}
            for a in existing_actions:
                if isinstance(a, dict) and isinstance(a.get("id"), str):
                    merged_by_id[a["id"]] = a
            for a in new_actions:
                if isinstance(a, dict) and isinstance(a.get("id"), str):
                    merged_by_id[a["id"]] = a

            merged_actions = list(merged_by_id.values())

            existing_app = existing.get("app") if isinstance(existing.get("app"), dict) else {}
            new_app = payload.get("app") if isinstance(payload.get("app"), dict) else {}

            kind_existing = str(existing_app.get("kind") or "")
            kind_new = str(new_app.get("kind") or "")
            merged_kind = kind_existing or kind_new
            if kind_existing and kind_new and kind_existing != kind_new:
                merged_kind = "mixed"

            merged_app = dict(existing_app)
            merged_app.setdefault("name", new_app.get("name") or "app")
            merged_app["kind"] = merged_kind

            merged_meta = dict(existing.get("metadata") or {})
            merged_meta["merged"] = True

            payload = {
                "format": "app2schema.appspec",
                "version": int(existing.get("version") or payload.get("version") or 1),
                "app": merged_app,
                "actions": merged_actions,
                "metadata": merged_meta,
            }

    if validate:
        validate_appspec(payload)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path
