from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DSLKind = Literal["sql", "graphql", "dom", "shell", "http", "python", "gui"]
OutputFormat = Literal["raw", "json", "table", "text", "html"]


@dataclass
class ActionIR:
    action_id: str
    dsl: str
    dsl_kind: DSLKind
    params: dict[str, Any] = field(default_factory=dict)
    output_format: OutputFormat = "raw"
    confidence: float = 0.0
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "nlp2cmd.action_ir",
            "version": 1,
            "action_id": self.action_id,
            "dsl": self.dsl,
            "dsl_kind": self.dsl_kind,
            "params": self.params,
            "output_format": self.output_format,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }
