#!/usr/bin/env python3
"""
Non-LLM Enhanced Schema Generation

This module provides improved schema generation without LLM dependency:
1. Help text parsing
2. Man page extraction
3. Pattern matching
4. Template inference
5. Quality validation
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


class NonLLMStrategy(Enum):
    """Available non-LLM strategies."""
    HELP_TEXT = "help_text"
    MAN_PAGE = "man_page"
    PATTERN_MATCHING = "pattern_matching"
    TEMPLATE_INFERENCE = "template_inference"
    EXAMPLE_EXTRACTION = "example_extraction"


@dataclass
class SchemaQuality:
    """Schema quality metrics."""
    completeness: float = 0.0
    accuracy: float = 0.0
    usefulness: float = 0.0
    overall: float = 0.0


class NonLLMSchemaExtractor:
    """Non-LLM schema extractor with multiple strategies."""
    
    def __init__(self):
        """Initialize extractor."""
        self.registry = DynamicSchemaRegistry(
            use_per_command_storage=True,
            storage_dir="./command_schemas"
        )
        
        # Command patterns and templates
        self.command_patterns = self._load_command_patterns()
        self.template_library = self._load_template_library()
        
        # Quality weights
        self.quality_weights = {
            "has_description": 0.2,
            "has_parameters": 0.2,
            "has_examples": 0.2,
            "has_template": 0.2,
            "has_patterns": 0.2
        }
    
    def extract_schema(self, command: str) -> ExtractedSchema:
        """Extract schema using best non-LLM strategy."""
        
        # Try strategies in order
        strategies = [
            NonLLMStrategy.HELP_TEXT,
            NonLLMStrategy.MAN_PAGE,
            NonLLMStrategy.PATTERN_MATCHING,
            NonLLMStrategy.TEMPLATE_INFERENCE
        ]
        
        best_schema = None
        best_quality = SchemaQuality()
        
        for strategy in strategies:
            try:
                schema = self._extract_with_strategy(command, strategy)
                quality = self._evaluate_quality(schema)
                
                if quality.overall > best_quality.overall:
                    best_schema = schema
                    best_quality = quality
                
                # Early exit if high quality
                if quality.overall > 0.8:
                    break
                    
            except Exception as e:
                print(f"Strategy {strategy.value} failed for {command}: {e}")
        
        # Enhance if found
        if best_schema:
            best_schema = self._enhance_schema(best_schema)
            best_schema.metadata["extraction_strategies"] = [s.value for s in strategies]
            best_schema.metadata["quality_score"] = best_quality.overall
        
        return best_schema or self._create_fallback_schema(command)
    
    def _extract_with_strategy(self, command: str, strategy: NonLLMStrategy) -> ExtractedSchema:
        """Extract schema using specific strategy."""
        
        if strategy == NonLLMStrategy.HELP_TEXT:
            return self._extract_from_help(command)
        elif strategy == NonLLMStrategy.MAN_PAGE:
            return self._extract_from_man(command)
        elif strategy == NonLLMStrategy.PATTERN_MATCHING:
            return self._extract_from_patterns(command)
        elif strategy == NonLLMStrategy.TEMPLATE_INFERENCE:
            return self._extract_from_templates(command)
    
    def _extract_from_help(self, command: str) -> ExtractedSchema:
        """Extract from command help text."""
        
        help_text = self._get_help_text(command)
        if not help_text:
            raise ValueError("No help text available")
        
        # Parse components
        description = self._parse_description(help_text)
        parameters = self._parse_parameters(help_text)
        examples = self._parse_examples(command, help_text)
        template = self._infer_template(command, parameters, examples)
        
        cmd_schema = CommandSchema(
            name=command,
            description=description,
            category=self._detect_category(command, help_text),
            parameters=parameters,
            examples=examples,
            patterns=[command],
            source_type="help_text",
            metadata={"help_length": len(help_text)},
            template=template
        )
        
        return ExtractedSchema(
            source=command,
            source_type="help_text",
            commands=[cmd_schema],
            metadata={"strategy": "help_text"}
        )
    
    def _extract_from_man(self, command: str) -> ExtractedSchema:
        """Extract from man page."""
        
        man_text = self._get_man_page(command)
        if not man_text:
            raise ValueError("No man page available")
        
        # Parse man sections
        sections = self._parse_man_sections(man_text)
        
        description = sections.get("DESCRIPTION", [""])[0]
        synopsis = sections.get("SYNOPSIS", [""])[0]
        
        # Extract from OPTIONS section
        options_text = "\n".join(sections.get("OPTIONS", []))
        parameters = self._parse_parameters(options_text)
        
        # Extract from EXAMPLES section
        examples_text = "\n".join(sections.get("EXAMPLES", []))
        examples = self._parse_examples(command, examples_text)
        
        template = self._parse_template_from_synopsis(synopsis)
        
        cmd_schema = CommandSchema(
            name=command,
            description=description,
            category=self._detect_category(command, man_text),
            parameters=parameters,
            examples=examples,
            patterns=[command],
            source_type="man_page",
            metadata={"man_parsed": True, "synopsis": synopsis},
            template=template
        )
        
        return ExtractedSchema(
            source=command,
            source_type="man_page",
            commands=[cmd_schema],
            metadata={"strategy": "man_page"}
        )
    
    def _extract_from_patterns(self, command: str) -> ExtractedSchema:
        """Extract from predefined patterns."""
        
        if command not in self.command_patterns:
            raise ValueError(f"No pattern for command: {command}")
        
        pattern_info = self.command_patterns[command]
        
        cmd_schema = CommandSchema(
            name=command,
            description=pattern_info["description"],
            category=pattern_info["category"],
            parameters=self._create_parameters_from_pattern(pattern_info),
            examples=pattern_info["examples"],
            patterns=pattern_info["patterns"],
            source_type="pattern_matching",
            metadata={"pattern_based": True},
            template=pattern_info["template"]
        )
        
        return ExtractedSchema(
            source=command,
            source_type="pattern_matching",
            commands=[cmd_schema],
            metadata={"strategy": "pattern_matching"}
        )
    
    def _extract_from_templates(self, command: str) -> ExtractedSchema:
        """Extract from template library."""
        
        # Find matching templates
        templates = self._find_matching_templates(command)
        
        if not templates:
            raise ValueError(f"No templates for command: {command}")
        
        # Use best template
        best_template = templates[0]
        
        cmd_schema = CommandSchema(
            name=command,
            description=f"{command} command",
            category=best_template["category"],
            parameters=best_template["parameters"],
            examples=best_template["examples"],
            patterns=[command],
            source_type="template_inference",
            metadata={"template_based": True},
            template=best_template["template"]
        )
        
        return ExtractedSchema(
            source=command,
            source_type="template_inference",
            commands=[cmd_schema],
            metadata={"strategy": "template_inference"}
        )
    
    def _enhance_schema(self, schema: ExtractedSchema) -> ExtractedSchema:
        """Enhance schema with additional information."""
        
        if not schema.commands:
            return schema
        
        cmd_schema = schema.commands[0]
        
        # Add common parameters if missing
        if not cmd_schema.parameters:
            cmd_schema.parameters = self._get_common_parameters(cmd_schema.category)
        
        # Add more examples if needed
        if len(cmd_schema.examples) < 3:
            cmd_schema.examples.extend(self._generate_examples(cmd_schema))
        
        # Improve template
        if not cmd_schema.template or cmd_schema.template == f"{cmd_schema.name} {{options}}":
            cmd_schema.template = self._improve_template(cmd_schema)
        
        # Add metadata
        cmd_schema.metadata["enhanced"] = True
        cmd_schema.metadata["enhancement_version"] = "1.0"
        
        return schema
    
    def _evaluate_quality(self, schema: ExtractedSchema) -> SchemaQuality:
        """Evaluate schema quality."""
        
        if not schema.commands:
            return SchemaQuality()
        
        cmd_schema = schema.commands[0]
        score = 0.0
        
        # Description
        if cmd_schema.description and len(cmd_schema.description) > 10:
            score += self.quality_weights["has_description"]
        
        # Parameters
        if cmd_schema.parameters:
            score += self.quality_weights["has_parameters"]
            if len(cmd_schema.parameters) > 2:
                score += 0.1
        
        # Examples
        if cmd_schema.examples:
            score += self.quality_weights["has_examples"]
            if len(cmd_schema.examples) > 2:
                score += 0.1
        
        # Template
        if cmd_schema.template and "{" in cmd_schema.template:
            score += self.quality_weights["has_template"]
        
        # Patterns
        if cmd_schema.patterns:
            score += self.quality_weights["has_patterns"]
        
        return SchemaQuality(overall=score)
    
    def _create_fallback_schema(self, command: str) -> ExtractedSchema:
        """Create fallback schema."""
        
        cmd_schema = CommandSchema(
            name=command,
            description=f"{command} command",
            category="general",
            parameters=[
                CommandParameter(
                    name="help",
                    type="boolean",
                    description="Show help",
                    required=False,
                    location="option"
                )
            ],
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="fallback",
            metadata={"fallback": True},
            template=f"{command} {{options}}"
        )
        
        return ExtractedSchema(
            source=command,
            source_type="fallback",
            commands=[cmd_schema],
            metadata={"strategy": "fallback"}
        )
    
    # Helper methods
    def _get_help_text(self, command: str) -> str:
        """Get help text."""
        for flag in ['--help', '-h']:
            try:
                result = subprocess.run(
                    [command, flag],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout + result.stderr
            except:
                continue
        return ""
    
    def _get_man_page(self, command: str) -> str:
        """Get man page."""
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
    
    def _parse_description(self, text: str) -> str:
        """Parse description from text."""
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                return line[:200]
        return ""
    
    def _parse_parameters(self, text: str) -> List[CommandParameter]:
        """Parse parameters from text."""
        parameters = []
        
        # Short options
        for match in re.finditer(r'^\s*(-[a-zA-Z]),?\s*(.*)$', text, re.MULTILINE):
            option = match.group(1)
            desc = match.group(2).strip()
            
            parameters.append(CommandParameter(
                name=option[1:],
                type="boolean",
                description=desc[:100],
                required=False,
                location="option"
            ))
        
        # Long options
        for match in re.finditer(r'^\s*(--[a-zA-Z][a-zA-Z0-9_-]*)\s*(.*)$', text, re.MULTILINE):
            option = match.group(1)
            desc = match.group(2).strip()
            
            param_type = "boolean"
            if "=" in option:
                param_type = "string"
                option = option.split("=")[0]
            
            parameters.append(CommandParameter(
                name=option[2:],
                type=param_type,
                description=desc[:100],
                required=False,
                location="option"
            ))
        
        return parameters[:10]  # Limit to 10
    
    def _parse_examples(self, command: str, text: str) -> List[str]:
        """Parse examples from text."""
        examples = []
        
        # Look for command usage
        for line in text.split('\n'):
            if command in line and not line.startswith('#'):
                example = line.strip()
                if example and len(example) < 100:
                    examples.append(example)
        
        return examples[:5]  # Limit to 5
    
    def _infer_template(self, command: str, parameters: List[CommandParameter], examples: List[str]) -> str:
        """Infer template from parameters and examples."""
        
        # Use examples to infer template
        if examples:
            # Find most common pattern
            patterns = []
            for example in examples:
                parts = example.split()
                if parts[0] == command:
                    pattern = command
                    for part in parts[1:]:
                        if part.startswith('-'):
                            pattern += " {options}"
                        else:
                            pattern += " {arg}"
                    patterns.append(pattern)
            
            if patterns:
                # Return most common pattern
                return max(set(patterns), key=patterns.count)
        
        # Default template
        if parameters:
            return f"{command} {{options}}"
        return f"{command}"
    
    def _detect_category(self, command: str, text: str) -> str:
        """Detect command category."""
        text_lower = text.lower()
        
        categories = {
            'container': ['container', 'docker', 'pod', 'kubernetes'],
            'version_control': ['git', 'repository', 'commit', 'branch'],
            'network': ['network', 'http', 'url', 'connection'],
            'system': ['process', 'memory', 'cpu', 'system'],
            'file': ['file', 'directory', 'copy', 'move', 'remove'],
            'text': ['text', 'search', 'pattern', 'replace'],
            'archive': ['archive', 'compress', 'extract', 'tar', 'zip'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _parse_man_sections(self, man_text: str) -> Dict[str, List[str]]:
        """Parse man page sections."""
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
    
    def _parse_template_from_synopsis(self, synopsis: str) -> str:
        """Parse template from synopsis."""
        # Extract command pattern
        parts = synopsis.split()
        if parts:
            template = parts[0]
            for part in parts[1:]:
                if part.startswith('[') and part.endswith(']'):
                    template += " {options}"
                elif part.startswith('<') and part.endswith('>'):
                    template += f" {{{part[1:-1]}}}"
            return template
        return "{command} {options}"
    
    def _load_command_patterns(self) -> Dict[str, Dict]:
        """Load predefined command patterns."""
        return {
            'docker': {
                'description': 'Docker container management',
                'category': 'container',
                'examples': ['docker ps', 'docker run nginx', 'docker stop container_id'],
                'patterns': ['docker'],
                'template': 'docker {subcommand} {options}'
            },
            'kubectl': {
                'description': 'Kubernetes command line tool',
                'category': 'container',
                'examples': ['kubectl get pods', 'kubectl apply -f file.yaml'],
                'patterns': ['kubectl'],
                'template': 'kubectl {resource} {action} {options}'
            },
            'git': {
                'description': 'Git version control',
                'category': 'version_control',
                'examples': ['git status', 'git add .', 'git commit -m "message"'],
                'patterns': ['git'],
                'template': 'git {action} {options}'
            },
            'find': {
                'description': 'Find files',
                'category': 'file',
                'examples': ['find . -name "*.py"', 'find / -type f -size +100M'],
                'patterns': ['find'],
                'template': 'find {path} -name "{pattern}"'
            },
            'tar': {
                'description': 'Archive utility',
                'category': 'archive',
                'examples': ['tar -czf archive.tar.gz dir/', 'tar -xzf archive.tar.gz'],
                'patterns': ['tar'],
                'template': 'tar {options} {archive} {files}'
            }
        }
    
    def _load_template_library(self) -> Dict[str, List[Dict]]:
        """Load template library."""
        return {
            'file': [
                {
                    'category': 'file',
                    'parameters': [
                        CommandParameter('path', 'string', 'File path', False, location='argument')
                    ],
                    'examples': ['ls -la', 'ls /home/user'],
                    'template': 'ls {options} {path}'
                }
            ],
            'system': [
                {
                    'category': 'system',
                    'parameters': [],
                    'examples': ['ps aux', 'ps -ef'],
                    'template': 'ps {options}'
                }
            ]
        }
    
    def _create_parameters_from_pattern(self, pattern_info: Dict) -> List[CommandParameter]:
        """Create parameters from pattern info."""
        return [
            CommandParameter(
                name="options",
                type="string",
                description="Command options",
                required=False,
                location="option"
            )
        ]
    
    def _find_matching_templates(self, command: str) -> List[Dict]:
        """Find matching templates for command."""
        matching = []
        
        for category, templates in self.template_library.items():
            for template in templates:
                # Simple matching logic
                matching.append(template)
        
        return matching
    
    def _get_common_parameters(self, category: str) -> List[CommandParameter]:
        """Get common parameters for category."""
        common = [
            CommandParameter(
                name="help",
                type="boolean",
                description="Show help",
                required=False,
                location="option"
            )
        ]
        
        if category == 'file':
            common.append(
                CommandParameter(
                    name="verbose",
                    type="boolean",
                    description="Verbose output",
                    required=False,
                    location="option"
                )
            )
        
        return common
    
    def _generate_examples(self, cmd_schema: CommandSchema) -> List[str]:
        """Generate additional examples."""
        examples = []
        
        if cmd_schema.template:
            # Generate from template
            template = cmd_schema.template
            if '{options}' in template:
                examples.append(template.replace('{options}', '--help'))
        
        return examples
    
    def _improve_template(self, cmd_schema: CommandSchema) -> str:
        """Improve command template."""
        
        # Base template
        template = f"{cmd_schema.name} {{options}}"
        
        # Category-specific improvements
        if cmd_schema.category == 'file':
            template = f"{cmd_schema.name} {{options}} {{path}}"
        elif cmd_schema.category == 'container':
            template = f"{cmd_schema.name} {{subcommand}} {{options}}"
        
        return template
    
    def batch_extract(self, commands: List[str]) -> Dict[str, ExtractedSchema]:
        """Extract schemas for multiple commands."""
        
        results = {}
        
        for command in commands:
            print(f"Extracting schema for: {command}")
            try:
                schema = self.extract_schema(command)
                results[command] = schema
                
                # Show quality
                quality = self._evaluate_quality(schema)
                status = "✓" if quality.overall > 0.5 else "⚠"
                print(f"  {status} Quality: {quality.overall:.2f}")
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results[command] = None
        
        return results


def main():
    """Demonstrate non-LLM schema extraction."""
    
    print("=" * 60)
    print("NON-LLM SCHEMA EXTRACTION")
    print("=" * 60)
    
    # Initialize extractor
    extractor = NonLLMSchemaExtractor()
    
    # Test commands
    test_commands = [
        "docker",
        "kubectl",
        "git",
        "find",
        "tar",
        "ls",
        "ps",
        "grep"
    ]
    
    # Extract schemas
    results = extractor.batch_extract(test_commands)
    
    # Show summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for s in results.values() if s is not None)
    print(f"Successfully extracted: {successful}/{len(test_commands)}")
    
    # Save schemas
    print("\nSaving schemas...")
    for command, schema in results.items():
        if schema:
            # Store in registry
            extractor.registry.schemas[command] = schema
    
    # Auto-save
    extractor.registry._auto_save()
    print(f"Saved {len(extractor.registry.schemas)} schemas to storage")


if __name__ == "__main__":
    main()
