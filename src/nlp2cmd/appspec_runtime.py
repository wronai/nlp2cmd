from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class AppAction:
    id: str
    type: str
    dsl_kind: str
    dsl: dict[str, Any]
    description: str
    params: dict[str, Any]
    schema: dict[str, Any]
    match: dict[str, Any]


@dataclass
class AppSpec:
    app: dict[str, Any]
    actions: list[AppAction]

    def get_action(self, action_id: str) -> Optional[AppAction]:
        for a in self.actions:
            if a.id == action_id:
                return a
        return None


def load_appspec(path: str | Path) -> AppSpec:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    if data.get("format") != "app2schema.appspec":
        raise ValueError("Not an AppSpec file")

    actions: list[AppAction] = []
    for a in data.get("actions", []) or []:
        dsl = a.get("dsl") or {}
        actions.append(
            AppAction(
                id=str(a.get("id")),
                type=str(a.get("type")),
                dsl_kind=str(dsl.get("kind")),
                dsl=dict(dsl),
                description=str(a.get("description") or ""),
                params=dict(a.get("params") or {}),
                schema=dict(a.get("schema") or {}),
                match=dict(a.get("match") or {}),
            )
        )

    return AppSpec(app=dict(data.get("app") or {}), actions=actions)
