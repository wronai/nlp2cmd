from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from nlp2cmd.appspec_runtime import AppAction, AppSpec
from nlp2cmd.ir import ActionIR


@dataclass
class MatchResult:
    action: AppAction
    score: float


class SchemaDrivenNLP2CMD:
    def __init__(self, spec: AppSpec):
        self.spec = spec

    def transform(self, text: str) -> ActionIR:
        match = self._select_action(text)
        params = self._extract_params(match.action, text)
        dsl = self._render_dsl(match.action, params, text)

        output_format = str(match.action.dsl.get("output_format") or "raw")

        return ActionIR(
            action_id=match.action.id,
            dsl=dsl,
            dsl_kind=match.action.dsl_kind,  # type: ignore[arg-type]
            params=params,
            output_format=output_format,  # type: ignore[arg-type]
            confidence=min(max(match.score, 0.0), 1.0),
            explanation=f"schema-driven match score={match.score:.2f}",
            metadata={"action_type": match.action.type},
        )

    def _select_action(self, text: str) -> MatchResult:
        text_lower = text.lower()
        best: Optional[MatchResult] = None

        for action in self.spec.actions:
            score = 0.0
            patterns = list((action.match or {}).get("patterns", []) or [])
            examples = list((action.match or {}).get("examples", []) or [])

            for p in patterns:
                if isinstance(p, str) and p and p.lower() in text_lower:
                    score += 0.6
                    break

            for ex in examples:
                if isinstance(ex, str) and ex:
                    ex_words = [w for w in re.split(r"\W+", ex.lower()) if w]
                    if ex_words and any(w in text_lower for w in ex_words[:3]):
                        score += 0.2
                        break

            score += min(len(patterns), 5) * 0.02

            if best is None or score > best.score:
                best = MatchResult(action=action, score=score)

        if best is None:
            raise ValueError("AppSpec has no actions")

        return best

    def _extract_params(self, action: AppAction, text: str) -> dict[str, Any]:
        params: dict[str, Any] = {}

        tokens = re.split(r"\s+", text.strip())
        for tok in tokens:
            if "=" not in tok:
                continue
            key, value = tok.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if key not in action.params:
                continue

            spec = action.params.get(key) or {}
            t = str(spec.get("type") or "string")

            if t == "integer":
                try:
                    params[key] = int(value)
                except ValueError:
                    params[key] = value
            elif t == "number":
                try:
                    params[key] = float(value)
                except ValueError:
                    params[key] = value
            elif t == "boolean":
                params[key] = value.lower() in {"1", "true", "yes", "y", "on"}
            else:
                params[key] = value

        return params

    def _render_dsl(self, action: AppAction, params: dict[str, Any], text: str) -> str:
        template = action.dsl.get("template")
        if isinstance(template, str) and template.strip():
            try:
                return template.format(**params, text=text)
            except Exception:
                return template

        if action.dsl_kind == "http":
            return self._render_http(action, params)

        if action.dsl_kind == "shell":
            return self._render_shell(action, params)

        return f"# action={action.id} (provide dsl.template to render), params={params}"

    def _render_http(self, action: AppAction, params: dict[str, Any]) -> str:
        schema = action.schema or {}
        method = str(schema.get("method") or "GET").upper()
        path = str(schema.get("path") or "/")
        base_url = str(schema.get("base_url") or "")

        for name, p in (action.params or {}).items():
            if str((p or {}).get("location") or "") == "path" and name in params:
                path = path.replace("{" + name + "}", str(params[name]))

        url = path
        if base_url and not url.startswith(("http://", "https://")):
            if url.startswith("/"):
                url = base_url.rstrip("/") + url
            else:
                url = base_url.rstrip("/") + "/" + url

        query_parts: list[str] = []
        for name, p in (action.params or {}).items():
            if str((p or {}).get("location") or "") == "query" and name in params:
                query_parts.append(f"{name}={params[name]}")
        if query_parts:
            url += "?" + "&".join(query_parts)

        parts = ["curl", "-X", method, url, "-H", "Content-Type: application/json"]

        body: dict[str, Any] = {}
        for name, p in (action.params or {}).items():
            if str((p or {}).get("location") or "") == "body" and name in params:
                body[name] = params[name]

        if body and method in {"POST", "PUT", "PATCH"}:
            import json

            parts.extend(["-d", json.dumps(body)])

        return " ".join(parts)

    def _render_shell(self, action: AppAction, params: dict[str, Any]) -> str:
        schema = action.schema or {}
        cmd = str(schema.get("command") or "")

        if not cmd:
            m = re.match(r"^shell\.(.+)$", action.id)
            if m:
                cmd = m.group(1)
            else:
                cmd = action.id

        parts = [cmd]
        for name, value in params.items():
            spec = action.params.get(name) or {}
            loc = str(spec.get("location") or "option")
            t = str(spec.get("type") or "string")

            if loc not in {"option", "arg", "unknown"}:
                continue

            flag = "--" + name.replace("_", "-")
            if t == "boolean":
                if value:
                    parts.append(flag)
            else:
                parts.extend([flag, str(value)])

        return " ".join(parts)
