"""
Integration module for the enhanced dynamic NLP2CMD implementation.

This module provides the main entry point for using the improved nlp2cmd
with dynamic schema extraction, shell-gpt integration, and enhanced NLP capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from nlp2cmd.core import NLP2CMD, TransformResult
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.nlp_enhanced import HybridNLPBackend, ShellGPTBackend
from nlp2cmd.schema_extraction import DynamicSchemaRegistry


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
        schema_registry: Optional[DynamicSchemaRegistry] = None,
        nlp_backend: Optional[str] = "hybrid",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize enhanced NLP2CMD.
        
        Args:
            schema_registry: Pre-configured schema registry
            nlp_backend: Type of NLP backend ("hybrid", "shell_gpt", "rule_based")
            config: Configuration dictionary
        """
        self.config = config or {}
        self.schema_registry = schema_registry or DynamicSchemaRegistry()
        
        # Initialize dynamic adapter
        adapter = DynamicAdapter(
            schema_registry=self.schema_registry,
            config=self.config.get("adapter_config"),
            safety_policy=self.config.get("safety_policy"),
        )
        
        # Initialize NLP backend
        if nlp_backend == "hybrid":
            backend = HybridNLPBackend(
                schema_registry=self.schema_registry,
                config=self.config.get("nlp_config"),
            )
        elif nlp_backend == "shell_gpt":
            backend = ShellGPTBackend(
                schema_registry=self.schema_registry,
                config=self.config.get("nlp_config"),
            )
        else:  # rule_based or fallback
            backend = None
        
        # Initialize parent class
        super().__init__(
            adapter=adapter,
            nlp_backend=backend,
            validator=self.config.get("validator"),
            feedback_analyzer=self.config.get("feedback_analyzer"),
            validation_mode=self.config.get("validation_mode", "normal"),
            auto_fix=self.config.get("auto_fix", False),
        )
        
        # Register initial schemas if provided
        initial_schemas = self.config.get("initial_schemas", [])
        for schema_source in initial_schemas:
            self.register_schema_source(schema_source)
    
    def register_schema_source(
        self,
        source: Union[str, List[str]],
        source_type: str = "auto",
        category: Optional[str] = None,
    ) -> None:
        """
        Register schema sources for dynamic command extraction.
        
        Args:
            source: URL, file path, or command name(s)
            source_type: Type of source ("auto", "openapi", "shell", "python")
            category: Optional category for organization
        """
        if isinstance(source, list):
            for src in source:
                self._register_single_source(src, source_type, category)
        else:
            self._register_single_source(source, source_type, category)
    
    def _register_single_source(self, source: str, source_type: str, category: Optional[str]) -> None:
        """Register a single schema source."""
        try:
            schema = self.adapter.register_schema_source(source, source_type)
            
            # Apply category if specified
            if category:
                for command in schema.commands:
                    command.category = category
            
            print(f"Registered schema from {source}: {len(schema.commands)} commands")
        
        except Exception as e:
            print(f"Failed to register schema from {source}: {e}")
    
    def get_available_commands(self, category: Optional[str] = None) -> List[str]:
        """Get list of available commands, optionally filtered by category."""
        if category:
            commands = self.adapter.get_commands_by_category(category)
        else:
            commands = self.adapter.registry.get_all_commands()
        
        return [cmd.name for cmd in commands]
    
    def get_command_categories(self) -> List[str]:
        """Get list of all command categories."""
        return self.adapter.get_command_categories()
    
    def search_commands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for commands matching the query."""
        commands = self.adapter.search_commands(query, limit)
        
        results = []
        for cmd in commands:
            results.append({
                "name": cmd.name,
                "description": cmd.description,
                "category": cmd.category,
                "source_type": cmd.source_type,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                    }
                    for p in cmd.parameters
                ],
                "examples": cmd.examples,
            })
        
        return results
    
    def get_command_help(self, command_name: str) -> Optional[str]:
        """Get detailed help for a specific command."""
        return self.adapter.get_command_help(command_name)
    
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
        
        # Add explanation metadata
        if result.is_success:
            # Find which command schema was used
            matching_commands = self.adapter._find_matching_commands(
                result.plan.intent, result.plan.entities, text
            )
            
            if matching_commands:
                used_schema = matching_commands[0]
                result.metadata.update({
                    "used_schema": used_schema.name,
                    "schema_source": used_schema.source_type,
                    "schema_category": used_schema.category,
                    "explanation": f"Generated command using {used_schema.source_type} schema '{used_schema.name}'",
                })
            else:
                result.metadata.update({
                    "explanation": "Generated command using fallback pattern matching",
                })
        
        return result
    
    def export_schemas(self, format: str = "json") -> str:
        """Export all registered schemas."""
        return self.adapter.registry.export_schemas(format)
    
    def analyze_query(self, text: str) -> Dict[str, Any]:
        """Analyze a natural language query without generating a command."""
        # Extract intent and entities
        if hasattr(self.nlp_backend, 'generate_plan'):
            plan = self.nlp_backend.generate_plan(text)
        else:
            intent, confidence = self.nlp_backend.extract_intent(text)
            entities = self.nlp_backend.extract_entities(text)
            plan = type('Plan', (), {
                'intent': intent,
                'confidence': confidence,
                'entities': {e.name: e.value for e in entities}
            })()
        
        # Find matching commands
        matching_commands = self.adapter.search_commands(text, limit=5)
        
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
                    "relevance_score": self._calculate_relevance(cmd, plan),
                }
                for cmd in matching_commands
            ],
        }
    
    def _calculate_relevance(self, command: Any, plan: Any) -> float:
        """Calculate relevance score between command and plan."""
        score = 0.0
        
        # Intent matching
        if plan.intent.lower() in command.name.lower():
            score += 0.5
        elif command.name.lower() in plan.intent.lower():
            score += 0.3
        
        # Entity matching
        for param in command.parameters:
            if param.name in plan.entities:
                score += 0.2
        
        # Pattern matching
        query_lower = plan.text.lower() if hasattr(plan, 'text') else ""
        for pattern in command.patterns:
            if any(word in query_lower for word in pattern.lower().split()):
                score += 0.1
                break
        
        return min(score, 1.0)


# Convenience function for quick usage
def create_enhanced_nlp2cmd(
    schemas: Optional[List[Union[str, Dict[str, Any]]]] = None,
    nlp_backend: str = "hybrid",
    config: Optional[Dict[str, Any]] = None,
) -> EnhancedNLP2CMD:
    """
    Create an enhanced NLP2CMD instance with common configurations.
    
    Args:
        schemas: List of schema sources to register
        nlp_backend: Type of NLP backend to use
        config: Configuration options
    
    Returns:
        Configured EnhancedNLP2CMD instance
    """
    if config is None:
        config = {}
    
    # Set up default schemas if none provided
    if schemas is None:
        schemas = [
            # Common shell commands
            "find", "grep", "git", "docker", "curl", "wget",
            # Example OpenAPI specs (these would be real URLs in practice)
            # "https://api.example.com/openapi.json",
        ]
    
    # Create instance
    nlp2cmd = EnhancedNLP2CMD(
        nlp_backend=nlp_backend,
        config=config,
    )
    
    # Register schemas
    for schema in schemas:
        if isinstance(schema, dict):
            # Schema with metadata
            source = schema.get("source")
            source_type = schema.get("type", "auto")
            category = schema.get("category")
            if source:
                nlp2cmd.register_schema_source(source, source_type, category)
        else:
            # Simple string source
            nlp2cmd.register_schema_source(schema)
    
    return nlp2cmd


# Example usage and demo functions
def demo_dynamic_extraction():
    """Demonstrate dynamic schema extraction capabilities."""
    print("=== Dynamic NLP2CMD Demo ===\n")
    
    # Create enhanced instance
    nlp2cmd = create_enhanced_nlp2cmd(
        schemas=["find", "git", "docker"],
        nlp_backend="hybrid"
    )
    
    # Show available commands
    print("Available commands:")
    for category in nlp2cmd.get_command_categories():
        commands = nlp2cmd.get_available_commands(category)
        print(f"  {category}: {', '.join(commands[:5])}{'...' if len(commands) > 5 else ''}")
    
    print("\n=== Query Examples ===")
    
    # Test queries
    test_queries = [
        "find all Python files in the current directory",
        "show git status",
        "list running docker containers",
        "copy file.txt to backup/",
        "check disk usage",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Analyze query
        analysis = nlp2cmd.analyze_query(query)
        print(f"Intent: {analysis['detected_intent']} (confidence: {analysis['confidence']:.2f})")
        print(f"Entities: {analysis['extracted_entities']}")
        
        if analysis['matching_commands']:
            best_match = analysis['matching_commands'][0]
            print(f"Best match: {best_match['name']} - {best_match['description']}")
        
        # Transform to command
        result = nlp2cmd.transform_with_explanation(query)
        if result.is_success:
            print(f"Generated: {result.command}")
            print(f"Explanation: {result.metadata.get('explanation', 'No explanation available')}")
        else:
            print(f"Failed: {result.errors}")
    
    print("\n=== Schema Export ===")
    schemas_json = nlp2cmd.export_schemas("json")
    print(f"Exported {len(schemas_json)} characters of schema data")


if __name__ == "__main__":
    demo_dynamic_extraction()
