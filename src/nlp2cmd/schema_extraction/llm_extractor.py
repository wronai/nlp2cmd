"""LLM-powered schema extractor using LiteLLM."""

import json
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from nlp2cmd.schema_extraction import (
    CommandSchema,
    CommandParameter,
    ExtractedSchema,
    ShellHelpExtractor,
)


class LLMSchemaExtractor:
    """Extract command schemas using LLM assistance."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize LLM extractor with configuration."""
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is required. Install with: pip install litellm")
        
        self.config = config or {}
        self.model = self.config.get("model", "ollama/qwen2.5-coder:7b")
        self.api_base = self.config.get("api_base", "http://localhost:11434")
        self.api_key = self.config.get("api_key", "")
        self.temperature = self.config.get("temperature", 0.1)
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.timeout = self.config.get("timeout", 30)
        
        # Configure litellm
        litellm.api_base = self.api_base
        if self.api_key:
            litellm.api_key = self.api_key
        litellm.timeout = self.timeout
        
        # Fallback extractor
        self.fallback_extractor = ShellHelpExtractor()
    
    def _build_extraction_prompt(self, command: str, help_text: str) -> str:
        """Build prompt for LLM schema extraction."""
        prompt = f"""You are a command line expert. Analyze the following command help output and extract a structured schema.

Command: {command}
Help Output:
{help_text[:3000]}  # Limit to avoid token limits

Extract the following information in JSON format:
1. description: A brief description of what the command does
2. category: The category of command (e.g., "file", "process", "network", "system")
3. parameters: List of parameters with:
   - name: parameter name
   - type: data type (string, integer, boolean, array, object)
   - description: what the parameter does
   - required: whether it's required (true/false)
   - location: where it appears (option, argument, flag)
4. examples: 2-3 realistic usage examples
5. template: A template for common usage patterns with placeholders like {{path}}, {{file}}, {{number}}

Focus on practical usage patterns. For template, use examples like:
- find: "find {{path}} -type f -size {{size}} -mtime -{{days}}"
- grep: "grep -r {{pattern}} {{path}}"
- tar: "tar -czf {{archive}}.tar.gz {{source}}"

Return only valid JSON without explanation:
{{
  "description": "...",
  "category": "...",
  "parameters": [...],
  "examples": [...],
  "template": "..."
}}"""
        return prompt
    
    def extract_from_command(self, command: str) -> ExtractedSchema:
        """Extract schema using LLM assistance."""
        try:
            # First get help text using fallback extractor
            help_schema = self.fallback_extractor.extract_from_command(command)
            help_text = "\n".join(help_schema.commands[0].examples) if help_schema.commands else ""
            
            # If no help available, return basic schema
            if not help_text:
                return self._create_basic_schema(command)
            
            # Use LLM to enhance the schema
            print(f"[LLMExtractor] Requesting schema for {command}...")
            response = completion(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": self._build_extraction_prompt(command, help_text)
                }],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                api_base=self.api_base,
            )
            
            # Get response content
            content = response.choices[0].message.content
            print(f"[LLMExtractor] Got response for {command}: {content[:100]}...")
            
            if not content:
                raise ValueError("Empty response from LLM")
            
            # Parse LLM response - handle potential formatting issues
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    llm_data = json.loads(json_match.group())
                else:
                    llm_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[LLMExtractor] Failed to parse JSON for {command}: {e}")
                print(f"[LLMExtractor] Raw response: {content}")
                raise ValueError(f"Invalid JSON response: {e}")
            
            # Build enhanced schema
            parameters = []
            for param in llm_data.get("parameters", []):
                parameters.append(CommandParameter(
                    name=param.get("name", ""),
                    type=param.get("type", "string"),
                    description=param.get("description", ""),
                    required=param.get("required", False),
                    location=param.get("location", "unknown"),
                ))
            
            schema = CommandSchema(
                name=command,
                description=llm_data.get("description", f"{command} command"),
                category=llm_data.get("category", "general"),
                parameters=parameters,
                examples=llm_data.get("examples", [f"{command} --help"]),
                patterns=[command, llm_data.get("description", "").lower()],
                source_type="llm_enhanced",
                metadata={
                    "llm_model": self.model,
                    "enhanced": True,
                },
                template=llm_data.get("template"),
            )
            
            print(f"[LLMExtractor] Successfully enhanced {command}")
            return ExtractedSchema(
                source=command,
                source_type="llm_enhanced",
                commands=[schema],
                metadata={"model": self.model},
            )
            
        except Exception as e:
            print(f"[LLMExtractor] Failed to extract {command} with LLM: {e}")
            print(f"[LLMExtractor] Falling back to basic extraction...")
            return self.fallback_extractor.extract_from_command(command)
    
    def _create_basic_schema(self, command: str) -> ExtractedSchema:
        """Create a basic schema when no help is available."""
        schema = CommandSchema(
            name=command,
            description=f"{command} command",
            category="general",
            parameters=[],
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="basic",
            metadata={"no_help": True},
        )
        
        return ExtractedSchema(
            source=command,
            source_type="basic",
            commands=[schema],
            metadata={"no_help": True},
        )
