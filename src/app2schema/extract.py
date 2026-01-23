from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional, Union

import httpx

from nlp2cmd.schema_extraction import (
    ExtractedSchema,
    OpenAPISchemaExtractor,
    PythonCodeExtractor,
    ShellHelpExtractor,
)


SourceType = Literal["auto", "openapi", "shell", "python"]


@dataclass
class App2SchemaResult:
    schemas: list[ExtractedSchema]
    detected_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_export_dict(self, raw: bool = False) -> dict[str, Any]:
        sources: dict[str, Any] = {}

        for schema in self.schemas:
            sources[schema.source] = {
                "source_type": schema.source_type,
                "commands": [
                    {
                        "name": cmd.name,
                        "description": cmd.description,
                        "category": cmd.category,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                                "default": p.default,
                                "choices": p.choices,
                                "pattern": p.pattern,
                                "example": p.example,
                            }
                            for p in cmd.parameters
                        ],
                        "examples": cmd.examples,
                        "patterns": cmd.patterns,
                        "source_type": cmd.source_type,
                        "metadata": cmd.metadata,
                    }
                    for cmd in schema.commands
                ],
                "metadata": schema.metadata,
            }

        if raw:
            return sources

        return {
            "format": "nlp2cmd.dynamic_schema_export",
            "version": 1,
            "detected_type": self.detected_type,
            "sources": sources,
            "metadata": self.metadata,
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

    if source_type == "python":
        p = Path(target_str)
        if p.exists():
            schema = python_extractor.extract_from_file(p)
        else:
            schema = python_extractor.extract_from_source(target_str)
        return App2SchemaResult(
            schemas=[schema],
            detected_type="python",
            metadata={"target": target_str},
        )

    raise ValueError(f"Unsupported source_type: {source_type}")


def extract_schema_to_file(
    target: Union[str, Path],
    out_path: Union[str, Path],
    *,
    source_type: SourceType = "auto",
    discover_openapi: bool = True,
    raw: bool = False,
) -> Path:
    result = extract_schema(
        target,
        source_type=source_type,
        discover_openapi=discover_openapi,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = result.to_export_dict(raw=raw)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return out_path
