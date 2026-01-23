from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy
from nlp2cmd.appspec_runtime import AppSpec, load_appspec
from nlp2cmd.ir import ActionIR
from nlp2cmd.schema_driven import SchemaDrivenNLP2CMD


@dataclass
class AppSpecAdapterConfig:
    appspec_path: Optional[str] = None


class AppSpecAdapter(BaseDSLAdapter):
    DSL_NAME = "appspec"
    DSL_VERSION = "1.0"

    def __init__(
        self,
        *,
        appspec: Optional[AppSpec] = None,
        appspec_path: Optional[str | Path] = None,
        config: Optional[AdapterConfig] = None,
        safety_policy: Optional[SafetyPolicy] = None,
    ):
        super().__init__(config=config, safety_policy=safety_policy)

        self._spec: Optional[AppSpec] = None
        self._engine: Optional[SchemaDrivenNLP2CMD] = None
        self.last_action_ir: Optional[ActionIR] = None

        if appspec is not None:
            self.set_spec(appspec)
        elif appspec_path is not None:
            self.load_from_file(appspec_path)

    def load_from_file(self, path: str | Path) -> None:
        spec = load_appspec(path)
        self.set_spec(spec)

    def set_spec(self, spec: AppSpec) -> None:
        self._spec = spec
        self._engine = SchemaDrivenNLP2CMD(spec)

    def generate(self, plan: dict[str, Any]) -> str:
        if self._engine is None:
            raise ValueError("AppSpecAdapter requires an AppSpec (load_from_file / set_spec)")

        text = plan.get("text") or plan.get("query") or ""
        if not text:
            text = str(plan.get("intent") or "")

        ir = self._engine.transform(str(text))
        self.last_action_ir = ir
        return ir.dsl

    def validate_syntax(self, command: str) -> dict[str, Any]:
        if not command or not str(command).strip():
            return {"valid": False, "errors": ["DSL is empty"], "warnings": []}
        return {"valid": True, "errors": [], "warnings": []}

    def check_safety(self, command: str) -> dict[str, Any]:
        # When AppSpec renders to shell commands, support a stricter policy shape.
        policy = self.config.safety_policy
        blocked = getattr(policy, "blocked_commands", None)
        require_confirm = getattr(policy, "require_confirmation_for", None)

        if isinstance(blocked, list) or isinstance(require_confirm, list):
            cmd_l = (command or "").lower()

            if isinstance(blocked, list):
                for pattern in blocked:
                    if isinstance(pattern, str) and pattern.lower() in cmd_l:
                        return {
                            "allowed": False,
                            "reason": f"Command contains blocked pattern: {pattern}",
                            "alternatives": [],
                        }

            requires_confirmation = False
            if isinstance(require_confirm, list):
                for pattern in require_confirm:
                    if isinstance(pattern, str) and pattern.lower() in cmd_l:
                        requires_confirmation = True
                        break

            return {"allowed": True, "requires_confirmation": requires_confirmation}

        return super().check_safety(command)
