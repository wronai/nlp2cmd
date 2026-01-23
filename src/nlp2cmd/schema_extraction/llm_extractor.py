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
        
        # Simple cache
        self._cache = {}
    
    def _build_extraction_prompt(self, command: str, help_text: str) -> str:
        """Build prompt for LLM schema extraction."""
        prompt = f"""Extract command schema for: {command}

Help output:
{help_text[:2000]}

Return JSON with:
{{
  "description": "Brief description",
  "category": "file|text|network|system|general",
  "template": "Template with {{placeholders}}",
  "examples": ["example1", "example2"]
}}

JSON:"""
        return prompt
    
    def extract_from_command(self, command: str) -> ExtractedSchema:
        """Extract schema using LLM assistance."""
        try:
            # First get help text using fallback extractor
            help_schema = self.fallback_extractor.extract_from_command(command)
            help_text = "\n".join(help_schema.commands[0].examples) if help_schema.commands else ""
            
            # If no help or too short, return basic schema
            if not help_text or len(help_text) < 50:
                print(f"[LLMExtractor] Skipping {command} - insufficient help text")
                return self._create_basic_schema(command)
            
            # Skip built-in commands that typically don't benefit from LLM
            builtin_commands = {'cd', 'echo', 'pwd', 'exit', 'export', 'alias', 'history', 'jobs', 'fg', 'bg', 'kill', 'top'}
            if command in builtin_commands:
                print(f"[LLMExtractor] Skipping {command} - built-in command")
                return help_schema
            
            # Check cache first
            cache_key = f"{command}:{hash(help_text[:100])}"
            if cache_key in self._cache:
                print(f"[LLMExtractor] Using cached result for {command}")
                cached_schema = self._cache[cache_key]
                # Update the command name in case of reuse
                cached_schema.commands[0].name = command
                return cached_schema
            
            # Use LLM to enhance the schema
            print(f"[LLMExtractor] Requesting schema for {command}...")
            response = completion(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": self._build_extraction_prompt(command, help_text)
                }],
                temperature=self.temperature,
                max_tokens=512,  # Reduced for speed
                timeout=10,  # Shorter timeout
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
                # Try to extract template with regex fallback
                template_match = re.search(r'template["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                template = template_match.group(1) if template_match else None
                llm_data = {
                    "description": f"{command} command",
                    "category": "general",
                    "template": template,
                    "examples": [f"{command} --help"]
                }
            
            # Build enhanced schema (simplified)
            schema = CommandSchema(
                name=command,
                description=llm_data.get("description", f"{command} command"),
                category=llm_data.get("category", "general"),
                parameters=[],  # Skip parameters for speed
                examples=llm_data.get("examples", [f"{command} --help"]),
                patterns=[command],
                source_type="llm_enhanced",
                metadata={
                    "llm_model": self.model,
                    "enhanced": True,
                },
                template=llm_data.get("template"),
            )
            
            print(f"[LLMExtractor] Successfully enhanced {command}")
            
            # Cache the result
            self._cache[cache_key] = ExtractedSchema(
                source=command,
                source_type="llm_enhanced",
                commands=[schema],
                metadata={"model": self.model},
            )
            
            return self._cache[cache_key]
            
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
