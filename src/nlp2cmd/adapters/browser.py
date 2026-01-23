from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy
from nlp2cmd.ir import ActionIR


@dataclass
class BrowserSafetyPolicy(SafetyPolicy):
    enabled: bool = True


class BrowserAdapter(BaseDSLAdapter):
    """Minimal adapter that turns NL into dom_dql.v1 navigation (Playwright)."""

    DSL_NAME = "browser"
    DSL_VERSION = "1.0"

    INTENTS = {
        "browse": {
            "patterns": [
                "otwórz przeglądark",
                "otworz przegladark",
                "open browser",
                "wejdź na",
                "wejdz na",
                "go to",
                "navigate to",
                "open",
            ],
            "required_entities": [],
            "optional_entities": ["url"],
        }
    }

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        safety_policy: Optional[SafetyPolicy] = None,
    ):
        super().__init__(config, safety_policy or BrowserSafetyPolicy())
        self.last_action_ir: Optional[ActionIR] = None

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        t = (text or "").strip()
        if not t:
            return None

        # Prefer explicit scheme.
        m = re.search(r"(https?://\S+)", t, flags=re.IGNORECASE)
        if m:
            return m.group(1).rstrip(".,)")

        # Domain-like tokens (google.com, example.org/path)
        m = re.search(
            r"\b([a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+)(/\S*)?\b",
            t,
            flags=re.IGNORECASE,
        )
        if m:
            host = m.group(1)
            path = m.group(2) or ""
            return f"https://{host}{path}"

        return None
    
    @staticmethod
    def _extract_type_text(text: str) -> Optional[str]:
        """Extract text to type from patterns like 'wpisz w pole: nlp2cmd' or 'type: hello'."""
        patterns = [
            r'(?:wpisz|type|input|napisz)\s+(?:w\s+pole)?:?\s*(.+?)(?:\s*,?\s*(?:oraz|and|i)\s+(?:naciśnij|nacisnij|press|hit)\s+(?:enter|return)|$)',
            r'(?:wpisz|type|input|napisz)\s+(?:tekst|text)?\s*["\'](.+?)["\']',
            r'(?:wpisz|type)\s+(.+?)(?:\s+w\s+pole|\s+in\s+field|$)',
        ]
        
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                # Clean up common trailing phrases
                extracted = re.sub(r',?\s*(?:oraz|and|i)\s+(?:naciśnij|nacisnij|press|hit)\s+(?:enter|return).*$', '', extracted, flags=re.IGNORECASE)
                extracted = extracted.rstrip(',').strip()
                return extracted if extracted else None
        
        return None
    
    @staticmethod
    def _has_type_action(text: str) -> bool:
        """Check if text contains typing action."""
        type_keywords = ['wpisz', 'type', 'input', 'napisz', 'wpisać']
        return any(kw in text.lower() for kw in type_keywords)
    
    @staticmethod
    def _has_press_enter_action(text: str) -> bool:
        """Check if text contains press enter action."""
        enter_patterns = [
            r'(?:naciśnij|nacisnij|press|hit)\s+(?:enter|return)',
            r'(?:oraz|and|i)\s+enter',
        ]
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in enter_patterns)

    def generate(self, plan: dict[str, Any]) -> str:
        text = str(plan.get("text") or plan.get("query") or "")
        entities = plan.get("entities") if isinstance(plan.get("entities"), dict) else {}

        url = None
        if isinstance(entities, dict):
            u = entities.get("url") or entities.get("target")
            if isinstance(u, str) and u.strip():
                url = u.strip()

        url = url or self._extract_url(text)
        if not url:
            self.last_action_ir = None
            return "# Could not generate command"

        # Check if there's a typing action in the query
        type_text = self._extract_type_text(text)
        
        if type_text and self._has_type_action(text):
            # Multi-step action: goto + type (+ optional press enter)
            actions = [
                {"action": "goto", "url": url},
                {"action": "type", "selector": "input[name='q'], input[type='search'], textarea", "text": type_text},
            ]
            
            # Add press enter action if detected
            if self._has_press_enter_action(text):
                actions.append({"action": "press", "key": "Enter"})
            
            payload = {
                "dsl": "dom_dql.v1",
                "actions": actions,
                "url": url,
            }
            
            explanation_parts = [f"goto {url}", f"type '{type_text}'"]
            if self._has_press_enter_action(text):
                explanation_parts.append("press Enter")
            
            self.last_action_ir = ActionIR(
                action_id="dom.goto_and_type" if not self._has_press_enter_action(text) else "dom.goto_type_enter",
                dsl=json.dumps(payload, ensure_ascii=False),
                dsl_kind="dom",  # type: ignore[arg-type]
                params={"url": url, "type_text": type_text, "press_enter": self._has_press_enter_action(text)},
                output_format="raw",  # type: ignore[arg-type]
                confidence=float(plan.get("confidence") or 0.8),
                explanation=f"browser adapter: {' and '.join(explanation_parts)}",
                metadata={"url": url, "type_text": type_text, "press_enter": self._has_press_enter_action(text)},
            )
        else:
            # Simple goto action
            payload = {
                "dsl": "dom_dql.v1",
                "action": "goto",
                "url": url,
                "params": {},
            }

            self.last_action_ir = ActionIR(
                action_id="dom.goto",
                dsl=json.dumps(payload, ensure_ascii=False),
                dsl_kind="dom",  # type: ignore[arg-type]
                params={"url": url},
                output_format="raw",  # type: ignore[arg-type]
                confidence=float(plan.get("confidence") or 0.8),
                explanation="browser adapter: goto",
                metadata={"url": url},
            )

        return self.last_action_ir.dsl

    def validate_syntax(self, command: str) -> dict[str, Any]:
        try:
            payload = json.loads(command)
        except Exception as e:
            return {"valid": False, "errors": [f"Invalid JSON: {e}"]}

        if not isinstance(payload, dict) or payload.get("dsl") != "dom_dql.v1":
            return {"valid": False, "errors": ["Not dom_dql.v1"]}

        if not isinstance(payload.get("url"), str) or not payload.get("url"):
            return {"valid": False, "errors": ["Missing url"]}

        actions = payload.get("actions")
        if isinstance(actions, list):
            errors: list[str] = []
            if not actions:
                errors.append("Empty actions")
            for i, a in enumerate(actions):
                if not isinstance(a, dict):
                    errors.append(f"Action {i}: not an object")
                    continue
                act = str(a.get("action") or "")
                if act in {"goto", "navigate"}:
                    continue
                if act in {"type", "click", "press", "select"}:
                    if act in {"type", "click", "select"} and not str(a.get("selector") or ""):
                        errors.append(f"Action {i}: missing selector")
                    if act == "type" and not str(a.get("text") or ""):
                        errors.append(f"Action {i}: missing text")
                    if act == "press" and not str(a.get("key") or ""):
                        errors.append(f"Action {i}: missing key")
                    continue
                errors.append(f"Action {i}: unsupported action: {act}")

            if errors:
                return {"valid": False, "errors": errors}

            return {"valid": True, "errors": []}

        if str(payload.get("action") or "") not in {"goto", "navigate"}:
            return {"valid": False, "errors": ["Unsupported action"]}

        return {"valid": True, "errors": []}
