#!/usr/bin/env python3
"""
Enhanced Automatic Schema Generation with LLM and Non-LLM Methods

This module provides improved schema generation with:
1. Multiple extraction strategies
2. Fallback mechanisms
3. Quality scoring
4. Automatic validation
5. Hybrid LLM/non-LLM approach
"""

import sys
sys.path.insert(0, './src')

import re
import subprocess
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from nlp2cmd.schema_extraction import (
    DynamicSchemaRegistry,
    ExtractedSchema,
    CommandSchema,
    CommandParameter
)


class ExtractionStrategy(Enum):
    """Available extraction strategies."""
    HELP_TEXT = "help_text"
    MAN_PAGE = "man_page"
    LLM_INFERENCE = "llm_inference"
    PATTERN_MATCHING = "pattern_matching"
    HYBRID = "hybrid"


@dataclass
class ExtractionResult:
    """Result of schema extraction."""
    schema: Optional[ExtractedSchema] = None
    strategy: ExtractionStrategy = ExtractionStrategy.HELP_TEXT
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedSchemaExtractor:
    """Enhanced schema extractor with multiple strategies."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize extractor with configuration."""
        self.llm_config = llm_config or {
            "model": "ollama/qwen2.5-coder:7b",
            "api_base": "http://localhost:11434",
            "temperature": 0.1,
            "max_tokens": 1024,
            "timeout": 15,
        }
        
        # Strategy success tracking
        self.strategy_stats = {
            strategy: {"attempts": 0, "successes": 0}
            for strategy in ExtractionStrategy
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "min_parameters": 0,
            "min_examples": 1,
            "min_confidence": 0.5,
        }
        
        # Initialize components
        self.registry = DynamicSchemaRegistry(
            use_per_command_storage=True,
            storage_dir="./command_schemas"
        )
    
    def extract_schema(self, command: str, strategy: Optional[ExtractionStrategy] = None) -> ExtractionResult:
        """Extract schema using best available strategy."""
        
        # Determine strategy
        if strategy is None:
            strategy = self._select_strategy(command)
        
        # Update stats
        self.strategy_stats[strategy]["attempts"] += 1
        
        # Try extraction
        result = self._extract_with_strategy(command, strategy)
        
        # Update success stats
        if result.schema:
            self.strategy_stats[strategy]["successes"] += 1
        
        # Validate and enhance
        if result.schema:
            result.schema = self._validate_and_enhance(result.schema)
            result.confidence = self._calculate_confidence(result.schema)
        
        return result
    
    def _select_strategy(self, command: str) -> ExtractionStrategy:
        """Select best strategy for command."""
        
        # Check if LLM is available
        if self._is_llm_available():
            # Use hybrid for complex commands
            if self._is_complex_command(command):
                return ExtractionStrategy.HYBRID
            else:
                return ExtractionStrategy.LLM_INFERENCE
        
        # Fall back to non-LLM strategies
        if self._has_man_page(command):
            return ExtractionStrategy.MAN_PAGE
        
        return ExtractionStrategy.HELP_TEXT
    
    def _extract_with_strategy(self, command: str, strategy: ExtractionStrategy) -> ExtractionResult:
        """Extract schema using specific strategy."""
        
        result = ExtractionResult(strategy=strategy)
        
        try:
            if strategy == ExtractionStrategy.HELP_TEXT:
                result = self._extract_from_help(command)
            elif strategy == ExtractionStrategy.MAN_PAGE:
                result = self._extract_from_man(command)
            elif strategy == ExtractionStrategy.LLM_INFERENCE:
                result = self._extract_with_llm(command)
            elif strategy == ExtractionStrategy.PATTERN_MATCHING:
                result = self._extract_from_patterns(command)
            elif strategy == ExtractionStrategy.HYBRID:
                result = self._extract_hybrid(command)
        except Exception as e:
            result.errors.append(str(e))
        
        return result
    
    def _extract_from_help(self, command: str) -> ExtractionResult:
        """Extract schema from command help text."""
        result = ExtractionResult(strategy=ExtractionStrategy.HELP_TEXT)
        
        try:
            # Get help text
            help_text = self._get_help_text(command)
            if not help_text:
                result.errors.append("No help text available")
                return result
            
            # Parse help text
            schema = self._parse_help_text(command, help_text)
            result.schema = schema
            result.metadata["help_length"] = len(help_text)
            
        except Exception as e:
            result.errors.append(f"Help extraction failed: {e}")
        
        return result
    
    def _extract_from_man(self, command: str) -> ExtractionResult:
        """Extract schema from man page."""
        result = ExtractionResult(strategy=ExtractionStrategy.MAN_PAGE)
        
        try:
            # Get man page
            man_text = self._get_man_page(command)
            if not man_text:
                result.errors.append("No man page available")
                return result
            
            # Parse man page
            schema = self._parse_man_page(command, man_text)
            result.schema = schema
            result.metadata["man_length"] = len(man_text)
            
        except Exception as e:
            result.errors.append(f"Man extraction failed: {e}")
        
        return result
    
    def _extract_with_llm(self, command: str) -> ExtractionResult:
        """Extract schema using LLM inference."""
        result = ExtractionResult(strategy=ExtractionStrategy.LLM_INFERENCE)
        
        try:
            # Get basic info
            help_text = self._get_help_text(command) or ""
            
            # Create prompt for LLM
            prompt = self._create_llm_prompt(command, help_text)
            
            # Call LLM
            response = self._call_llm(prompt)
            
            # Parse response
            schema = self._parse_llm_response(command, response)
            result.schema = schema
            result.metadata["llm_tokens"] = len(response.split())
            
        except Exception as e:
            result.errors.append(f"LLM extraction failed: {e}")
        
        return result
    
    def _extract_hybrid(self, command: str) -> ExtractionResult:
        """Extract schema using hybrid approach."""
        result = ExtractionResult(strategy=ExtractionStrategy.HYBRID)
        
        # Try help text first
        help_result = self._extract_from_help(command)
        
        # If good, enhance with LLM
        if help_result.schema and self._calculate_confidence(help_result.schema) > 0.6:
            try:
                # Enhance with LLM
                enhanced = self._enhance_with_llm(help_result.schema)
                result.schema = enhanced
                result.metadata["base_strategy"] = "help_text"
                result.metadata["enhanced_by"] = "llm"
            except:
                # Fall back to help result
                result.schema = help_result.schema
                result.metadata["base_strategy"] = "help_text"
        else:
            # Try LLM directly
            llm_result = self._extract_with_llm(command)
            result.schema = llm_result.schema
            result.metadata["base_strategy"] = "llm"
        
        result.errors.extend(help_result.errors)
        
        return result
    
    def _extract_from_patterns(self, command: str) -> ExtractionResult:
        """Extract schema using pattern matching."""
        result = ExtractionResult(strategy=ExtractionStrategy.PATTERN_MATCHING)
        
        # Use predefined patterns
        schema = self._create_schema_from_patterns(command)
        result.schema = schema
        result.metadata["pattern_count"] = len(self._get_command_patterns(command))
        
        return result
    
    def _get_help_text(self, command: str) -> str:
        """Get help text for command."""
        try:
            # Try --help
            result = subprocess.run(
                [command, '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout + result.stderr
            
            # Try -h
            result = subprocess.run(
                [command, '-h'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout + result.stderr
        except:
            pass
        
        return ""
    
    def _get_man_page(self, command: str) -> str:
        """Get man page content."""
        try:
            result = subprocess.run(
                ['man', command],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        
        return ""
    
    def _parse_help_text(self, command: str, help_text: str) -> ExtractedSchema:
        """Parse help text into schema."""
        
        # Extract description
        description = self._extract_description(help_text)
        
        # Extract options
        parameters = self._extract_options(help_text)
        
        # Extract examples
        examples = self._extract_examples(command, help_text)
        
        # Create schema
        cmd_schema = CommandSchema(
            name=command,
            description=description,
            category=self._detect_category(command, help_text),
            parameters=parameters,
            examples=examples,
            patterns=[command],
            source_type="help_text",
            metadata={"help_parsed": True},
            template=self._generate_template(command, parameters)
        )
        
        return ExtractedSchema(
            source=command,
            source_type="help_text",
            commands=[cmd_schema],
            metadata={"extraction_method": "help_text"}
        )
    
    def _parse_man_page(self, command: str, man_text: str) -> ExtractedSchema:
        """Parse man page into schema."""
        
        # Man pages are structured differently
        sections = self._parse_man_sections(man_text)
        
        description = sections.get("DESCRIPTION", [""])[0]
        synopsis = sections.get("SYNOPSIS", [""])[0]
        
        # Extract options from OPTIONS section
        options_text = "\n".join(sections.get("OPTIONS", []))
        parameters = self._extract_options(options_text)
        
        # Extract examples from EXAMPLES section
        examples_text = "\n".join(sections.get("EXAMPLES", []))
        examples = self._extract_examples(command, examples_text)
        
        cmd_schema = CommandSchema(
            name=command,
            description=description,
            category=self._detect_category(command, man_text),
            parameters=parameters,
            examples=examples,
            patterns=[command],
            source_type="man_page",
            metadata={"man_parsed": True, "synopsis": synopsis},
            template=self._generate_template_from_synopsis(synopsis)
        )
        
        return ExtractedSchema(
            source=command,
            source_type="man_page",
            commands=[cmd_schema],
            metadata={"extraction_method": "man_page"}
        )
    
    def _create_llm_prompt(self, command: str, help_text: str) -> str:
        """Create prompt for LLM."""
        
        prompt = f"""Analyze the command '{command}' and create a structured schema.

Help text:
{help_text[:2000]}

Return a JSON with this structure:
{{
    "name": "{command}",
    "description": "Brief description of the command",
    "category": "one of: file, text, network, system, archive, development, container, version_control, security, database, general",
    "parameters": [
        {{
            "name": "parameter_name",
            "type": "string|integer|boolean|file|url",
            "description": "What this parameter does",
            "required": true|false,
            "default": "default_value_if_any",
            "choices": ["option1", "option2"],
            "location": "option|argument"
        }}
    ],
    "examples": ["example1", "example2", "example3"],
    "template": "{command} {{param1}} {{param2}}",
    "patterns": ["{command}", "pattern2"]
}}

Only return valid JSON."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        try:
            import requests
            
            response = requests.post(
                f"{self.llm_config['api_base']}/api/generate",
                json={
                    "model": self.llm_config["model"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.llm_config["temperature"],
                        "num_predict": self.llm_config["max_tokens"]
                    }
                },
                timeout=self.llm_config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"LLM API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Failed to call LLM: {e}")
    
    def _parse_llm_response(self, command: str, response: str) -> ExtractedSchema:
        """Parse LLM response into schema."""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            
            data = json.loads(json_match.group())
            
            # Create schema
            parameters = []
            for p in data.get("parameters", []):
                parameters.append(CommandParameter(
                    name=p.get("name", ""),
                    type=p.get("type", "string"),
                    description=p.get("description", ""),
                    required=p.get("required", False),
                    default=p.get("default"),
                    choices=p.get("choices", []),
                    location=p.get("location", "unknown")
                ))
            
            cmd_schema = CommandSchema(
                name=data.get("name", command),
                description=data.get("description", ""),
                category=data.get("category", "general"),
                parameters=parameters,
                examples=data.get("examples", []),
                patterns=data.get("patterns", [command]),
                source_type="llm",
                metadata={"llm_generated": True},
                template=data.get("template", f"{command} {{options}}")
            )
            
            return ExtractedSchema(
                source=command,
                source_type="llm",
                commands=[cmd_schema],
                metadata={"extraction_method": "llm"}
            )
            
        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {e}")
    
    def _enhance_with_llm(self, schema: ExtractedSchema) -> ExtractedSchema:
        """Enhance existing schema with LLM."""
        
        if not schema.commands:
            return schema
        
        cmd_schema = schema.commands[0]
        
        # Create enhancement prompt
        prompt = f"""Improve this command schema for '{cmd_schema.name}'.

Current schema:
- Description: {cmd_schema.description}
- Category: {cmd_schema.category}
- Parameters: {len(cmd_schema.parameters)}
- Examples: {len(cmd_schema.examples)}

Suggest improvements:
1. Better description
2. Missing parameters
3. More examples
4. Better template

Return JSON with improved values."""
        
        try:
            response = self._call_llm(prompt)
            
            # Parse and apply improvements
            improvements = self._parse_llm_response(cmd_schema.name, response)
            if improvements.commands:
                improved = improvements.commands[0]
                
                # Merge improvements
                if improved.description and len(improved.description) > len(cmd_schema.description):
                    cmd_schema.description = improved.description
                if improved.parameters:
                    cmd_schema.parameters.extend(improved.parameters)
                if improved.examples:
                    cmd_schema.examples.extend(improved.examples)
                if improved.template:
                    cmd_schema.template = improved.template
                
                cmd_schema.metadata["llm_enhanced"] = True
        
        except:
            # Keep original if enhancement fails
            pass
        
        return schema
    
    def _create_schema_from_patterns(self, command: str) -> ExtractedSchema:
        """Create schema from predefined patterns."""
        
        patterns = self._get_command_patterns(command)
        category = self._detect_category_from_patterns(command, patterns)
        
        cmd_schema = CommandSchema(
            name=command,
            description=f"{command} command",
            category=category,
            parameters=self._get_default_parameters(category),
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="pattern_matching",
            metadata={"pattern_based": True},
            template=self._get_default_template(command, category)
        )
        
        return ExtractedSchema(
            source=command,
            source_type="pattern_matching",
            commands=[cmd_schema],
            metadata={"extraction_method": "pattern_matching"}
        )
    
    def _validate_and_enhance(self, schema: ExtractedSchema) -> ExtractedSchema:
        """Validate and enhance schema."""
        
        if not schema.commands:
            return schema
        
        cmd_schema = schema.commands[0]
        
        # Ensure minimum requirements
        if not cmd_schema.description:
            cmd_schema.description = f"{cmd_schema.name} command"
        
        if not cmd_schema.examples:
            cmd_schema.examples = [f"{cmd_schema.name} --help"]
        
        if not cmd_schema.template:
            cmd_schema.template = f"{cmd_schema.name} {{options}}"
        
        # Add common parameters if missing
        if not cmd_schema.parameters:
            cmd_schema.parameters = self._get_common_parameters(cmd_schema.category)
        
        # Add metadata
        cmd_schema.metadata["validated"] = True
        cmd_schema.metadata["enhanced"] = True
        
        return schema
    
    def _calculate_confidence(self, schema: ExtractedSchema) -> float:
        """Calculate confidence score for schema."""
        
        if not schema.commands:
            return 0.0
        
        cmd_schema = schema.commands[0]
        score = 0.0
        
        # Description quality
        if cmd_schema.description and len(cmd_schema.description) > 20:
            score += 0.2
        
        # Parameters
        if len(cmd_schema.parameters) > 0:
            score += 0.2
            if len(cmd_schema.parameters) > 3:
                score += 0.1
        
        # Examples
        if len(cmd_schema.examples) >= self.quality_thresholds["min_examples"]:
            score += 0.2
            if len(cmd_schema.examples) > 3:
                score += 0.1
        
        # Template
        if cmd_schema.template and "{" in cmd_schema.template:
            score += 0.1
        
        # Source type
        if schema.source_type in ["help_text", "man_page", "llm"]:
            score += 0.1
        
        return min(score, 1.0)
    
    def _is_llm_available(self) -> bool:
        """Check if LLM is available."""
        try:
            import requests
            response = requests.get(f"{self.llm_config['api_base']}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _is_complex_command(self, command: str) -> bool:
        """Check if command is complex and needs LLM."""
        complex_commands = [
            'docker', 'kubectl', 'git', 'aws', 'gcloud', 'terraform',
            'ansible', 'make', 'cmake', 'gcc', 'python'
        ]
        return command in complex_commands
    
    def _has_man_page(self, command: str) -> bool:
        """Check if command has man page."""
        try:
            result = subprocess.run(
                ['man', '-w', command],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    # Helper methods (simplified for brevity)
    def _extract_description(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                return line[:200]
        return ""
    
    def _extract_options(self, text: str) -> List[CommandParameter]:
        parameters = []
        for match in re.finditer(r'^\s*(-[a-zA-Z]),?\s*.*$', text, re.MULTILINE):
            option = match.group(1)
            parameters.append(CommandParameter(
                name=option[1:],
                type="boolean",
                description=f"Option {option}",
                required=False,
                location="option"
            ))
        return parameters[:10]  # Limit to 10
    
    def _extract_examples(self, command: str, text: str) -> List[str]:
        examples = []
        if command in text:
            for line in text.split('\n'):
                if command in line and not line.startswith('#'):
                    examples.append(line.strip())
        return examples[:5]  # Limit to 5
    
    def _detect_category(self, command: str, text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ['container', 'docker', 'pod']):
            return 'container'
        elif any(word in text_lower for word in ['git', 'repository', 'commit']):
            return 'version_control'
        elif any(word in text_lower for word in ['network', 'http', 'url']):
            return 'network'
        elif any(word in text_lower for word in ['process', 'memory', 'cpu']):
            return 'system'
        return 'general'
    
    def _generate_template(self, command: str, parameters: List[CommandParameter]) -> str:
        if parameters:
            return f"{command} {{options}}"
        return f"{command}"
    
    def _parse_man_sections(self, man_text: str) -> Dict[str, List[str]]:
        sections = {}
        current_section = None
        current_lines = []
        
        for line in man_text.split('\n'):
            if line.isupper() and len(line) < 20:
                if current_section:
                    sections[current_section] = current_lines
                current_section = line
                current_lines = []
            else:
                current_lines.append(line)
        
        if current_section:
            sections[current_section] = current_lines
        
        return sections
    
    def _generate_template_from_synopsis(self, synopsis: str) -> str:
        # Extract command pattern from synopsis
        parts = synopsis.split()
        if parts:
            return " ".join(parts[:3])  # Simple template
        return "{command} {options}"
    
    def _get_command_patterns(self, command: str) -> List[str]:
        # Predefined patterns for common commands
        return [command]
    
    def _detect_category_from_patterns(self, command: str, patterns: List[str]) -> str:
        return 'general'
    
    def _get_default_parameters(self, category: str) -> List[CommandParameter]:
        return [
            CommandParameter(
                name="help",
                type="boolean",
                description="Show help",
                required=False,
                location="option"
            )
        ]
    
    def _get_common_parameters(self, category: str) -> List[CommandParameter]:
        return self._get_default_parameters(category)
    
    def _get_default_template(self, command: str, category: str) -> str:
        return f"{command} {{options}}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        stats = {"strategy_performance": {}}
        
        for strategy, data in self.strategy_stats.items():
            success_rate = 0
            if data["attempts"] > 0:
                success_rate = data["successes"] / data["attempts"]
            
            stats["strategy_performance"][strategy.value] = {
                "attempts": data["attempts"],
                "successes": data["successes"],
                "success_rate": success_rate
            }
        
        return stats


def main():
    """Demonstrate enhanced schema generation."""
    
    print("=" * 60)
    print("ENHANCED SCHEMA GENERATION")
    print("=" * 60)
    
    # Initialize extractor
    extractor = EnhancedSchemaExtractor()
    
    # Test commands
    test_commands = [
        "docker",
        "kubectl", 
        "git",
        "find",
        "tar",
        "nonexistent_command"  # Should fail gracefully
    ]
    
    results = []
    
    for command in test_commands:
        print(f"\nExtracting schema for: {command}")
        print("-" * 40)
        
        result = extractor.extract_schema(command)
        results.append(result)
        
        if result.schema:
            cmd_schema = result.schema.commands[0]
            print(f"✓ Strategy: {result.strategy.value}")
            print(f"✓ Confidence: {result.confidence:.2f}")
            print(f"✓ Category: {cmd_schema.category}")
            print(f"✓ Parameters: {len(cmd_schema.parameters)}")
            print(f"✓ Examples: {len(cmd_schema.examples)}")
            print(f"✓ Template: {cmd_schema.template}")
        else:
            print(f"✗ Failed: {result.errors}")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("EXTRACTION STATISTICS")
    print("=" * 60)
    
    stats = extractor.get_statistics()
    for strategy, data in stats["strategy_performance"].items():
        print(f"{strategy:20}: {data['successes']:3}/{data['attempts']:3} "
              f"({data['success_rate']:.1%})")
    
    # Save successful schemas
    print("\nSaving schemas...")
    for result in results:
        if result.schema and result.confidence > 0.5:
            extractor.registry.register_schema(result.schema)
    
    print(f"Saved {len(extractor.registry.schemas)} schemas")


if __name__ == "__main__":
    main()
