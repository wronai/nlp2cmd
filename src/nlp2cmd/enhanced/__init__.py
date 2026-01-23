"""
Integration module for the enhanced dynamic NLP2CMD implementation.

This module provides the main entry point for using the improved nlp2cmd
with dynamic schema extraction, shell-gpt integration, and enhanced NLP capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from nlp2cmd.core import NLP2CMD, TransformResult
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

    def register_schema_source(self, source: Union[str, List[str]], source_type: str = "auto") -> None:
        if isinstance(source, list):
            for src in source:
                self.register_schema_source(src, source_type=source_type)
            return

        try:
            extracted = self.adapter.register_schema_source(str(source), source_type=source_type)
            if isinstance(extracted, list):
                total = sum(len(s.commands) for s in extracted)
                print(f"Registered schema from {source}: {total} commands")
            else:
                print(f"Registered schema from {source}: {len(extracted.commands)} commands")
        except Exception as e:
            print(f"Failed to register schema from {source}: {e}")

    def get_available_commands(self, category: Optional[str] = None) -> List[str]:
        commands = self.schema_registry.get_all_commands()
        if category:
            commands = [c for c in commands if c.category == category]
        return [c.name for c in commands]

    def get_command_categories(self) -> List[str]:
        return sorted({c.category for c in self.schema_registry.get_all_commands() if c.category})

    def search_commands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        matches = self.schema_registry.search_commands(query, limit=limit)
        return [
            {
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "source_type": c.source_type,
            }
            for c in matches
        ]

    def get_command_help(self, command_name: str) -> Optional[str]:
        get_help = getattr(self.adapter, "get_command_help", None)
        if callable(get_help):
            return get_help(command_name)
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
            matching_commands = self.adapter._find_matching_commands(
                result.plan.intent, result.plan.entities, text
            )
            if matching_commands:
                used_schema = matching_commands[0]
                result.metadata.update(
                    {
                        "used_schema": used_schema.name,
                        "schema_source": used_schema.source_type,
                        "schema_category": used_schema.category,
                        "explanation": f"Generated command using {used_schema.source_type} schema '{used_schema.name}'",
                    }
                )
            else:
                result.metadata.setdefault(
                    "explanation",
                    "Generated command using fallback pattern matching",
                )

        return result
    
    def export_schemas(self, format: str = "json") -> str:
        return self.schema_registry.export_schemas(format)
    
    def analyze_query(self, text: str) -> Dict[str, Any]:
        """Analyze a natural language query without generating a command."""
        if hasattr(self.nlp_backend, "generate_plan"):
            plan = self.nlp_backend.generate_plan(text)
        else:
            intent, confidence = self.nlp_backend.extract_intent(text)
            entities = self.nlp_backend.extract_entities(text)
            entity_dict = {e.name: e.value for e in entities}
            plan = type(
                "Plan",
                (),
                {"intent": intent, "confidence": confidence, "entities": entity_dict, "text": text},
            )()

        matching_commands = self.schema_registry.search_commands(text, limit=5)
        return {
            "query": text,
            "detected_intent": plan.intent,
            "confidence": plan.confidence,
            "extracted_entities": plan.entities,
            "matching_commands": [
                {
                    "name": cmd.name,
                    "description": cmd.description,
                    "category": cmd.category,
                }
                for cmd in matching_commands
            ],
        }


def create_enhanced_nlp2cmd(
    schemas: Optional[List[Union[str, Dict[str, Any]]]] = None,
    nlp_backend: str = "hybrid",
    config: Optional[Dict[str, Any]] = None,
) -> EnhancedNLP2CMD:
    if config is None:
        config = {}

    if schemas is None:
        schemas = ["find", "grep", "git", "docker"]

    nlp2cmd = EnhancedNLP2CMD(nlp_backend=nlp_backend, config=config)

    for schema in schemas:
        if isinstance(schema, dict):
            source = schema.get("source")
            source_type = schema.get("type", "auto")
            if source:
                nlp2cmd.register_schema_source(str(source), source_type=str(source_type))
        else:
            nlp2cmd.register_schema_source(str(schema), source_type="auto")

    return nlp2cmd


