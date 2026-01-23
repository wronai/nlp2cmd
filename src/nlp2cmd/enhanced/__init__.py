"""
Integration module for the enhanced dynamic NLP2CMD implementation.

This module provides the main entry point for using the improved nlp2cmd
with dynamic schema extraction, shell-gpt integration, and enhanced NLP capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from nlp2cmd.core import NLP2CMD, NLPBackend, TransformResult
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry
from nlp2cmd.nlp_enhanced import HybridNLPBackend, ShellGPTBackend


class EnhancedNLP2CMD(NLP2CMD):
    """
    Enhanced NLP2CMD with dynamic schema capabilities.
    
    This class extends the base NLP2CMD with:
    - Dynamic schema extraction from OpenAPI, shell help, Python code
    - Shell-gpt integration for intelligent command generation
    - Hybrid NLP processing with multiple backends
    - No hardcoded keywords - everything is extracted dynamically
    """
    
    def __init__(
        self,
        nlp_backend: Optional[Union[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize enhanced NLP2CMD.
        
        Args:
            nlp_backend: Type of NLP backend ("hybrid", "shell_gpt", "rule_based")
            config: Configuration dictionary
        """
        self.schema_registry = DynamicSchemaRegistry()
        self.config = config or {}
        adapter = DynamicAdapter(
            schema_registry=self.schema_registry,
            config=self.config.get("adapter_config"),
            safety_policy=self.config.get("safety_policy"),
        )

        backend_obj = None
        if isinstance(nlp_backend, str):
            if nlp_backend == "shell_gpt":
                backend_obj = ShellGPTBackend(schema_registry=self.schema_registry, config=self.config)
            elif nlp_backend == "hybrid":
                backend_obj = HybridNLPBackend(schema_registry=self.schema_registry, config=self.config)
            elif nlp_backend in {"rule_based", "rules"}:
                backend_obj = None
            else:
                backend_obj = HybridNLPBackend(schema_registry=self.schema_registry, config=self.config)
        elif nlp_backend is not None:
            backend_obj = nlp_backend
        
        # Initialize parent class
        super().__init__(
            adapter=adapter,
            nlp_backend=backend_obj,
            validator=self.config.get("validator"),
            feedback_analyzer=self.config.get("feedback_analyzer"),
            validation_mode=self.config.get("validation_mode", "normal"),
            auto_fix=self.config.get("auto_fix", False),
        )

    def get_available_commands(self, category: Optional[str] = None) -> List[str]:
        """Backward compatible helper: returns action ids from AppSpec."""
        spec = getattr(self.adapter, "_spec", None)
        if spec is None:
            return []
        return [a.id for a in spec.actions]
    
    def get_command_categories(self) -> List[str]:
        return []
    
    def search_commands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        spec = getattr(self.adapter, "_spec", None)
        if spec is None:
            return []

        q = (query or "").lower()
        out: list[dict[str, Any]] = []
        for a in spec.actions:
            if q and q not in a.id.lower() and q not in (a.description or "").lower():
                continue
            out.append({"id": a.id, "type": a.type, "dsl_kind": a.dsl_kind, "description": a.description})
            if len(out) >= limit:
                break
        return out
    
    def get_command_help(self, command_name: str) -> Optional[str]:
        return None
    
    def transform_with_explanation(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> TransformResult:
        """
        Transform natural language with detailed explanation.
        
        This method provides additional metadata about how the transformation
        was performed, including which schemas were used.
        """
        result = self.transform(text, context, dry_run)
        
        if result.is_success:
            # With AppSpecAdapter, action selection/rendering details live in ActionIR.
            if isinstance(result.metadata.get("action_ir"), dict):
                result.metadata.setdefault(
                    "explanation",
                    str(result.metadata["action_ir"].get("explanation") or ""),
                )
        
        return result
    
    def export_schemas(self, format: str = "json") -> str:
        raise NotImplementedError("AppSpec is the canonical schema format; export is handled by app2schema")
    
    def analyze_query(self, text: str) -> Dict[str, Any]:
        """Analyze a natural language query without generating a command."""
        spec = getattr(self.adapter, "_spec", None)
        if spec is None:
            return {
                "query": text,
                "detected_intent": "",
                "confidence": 0.0,
                "extracted_entities": {},
                "matching_commands": [],
            }

        q = (text or "").lower()
        matches: list[dict[str, Any]] = []
        for a in spec.actions:
            if q and q not in a.id.lower() and q not in (a.description or "").lower():
                continue
            matches.append({"id": a.id, "type": a.type, "dsl_kind": a.dsl_kind, "description": a.description})
            if len(matches) >= 5:
                break

        return {
            "query": text,
            "detected_intent": "",
            "confidence": 0.0,
            "extracted_entities": {},
            "matching_commands": matches,
        }


