#!/usr/bin/env python3
"""Intelligent schema generator without hardcoded keywords."""

import json
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from nlp2cmd.schema_extraction import (
    DynamicSchemaRegistry, 
    ExtractedSchema, 
    CommandSchema,
    CommandParameter
)
from nlp2cmd.storage.versioned_store import VersionedSchemaStore


@dataclass
class CommandInfo:
    """Information about a command."""
    name: str
    category: str
    description: str
    common_options: List[str]
    examples: List[str]
    help_available: bool = True


class IntelligentSchemaExtractor:
    """Extracts schemas using intelligent analysis instead of hardcoded keywords."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize the extractor."""
        self.llm_config = llm_config or {
            "model": "ollama/qwen2.5-coder:7b",
            "api_base": "http://localhost:11434",
            "temperature": 0.1,
            "max_tokens": 512,
            "timeout": 10,
        }
        
        # Initialize components
        self.registry = DynamicSchemaRegistry(
            use_per_command_storage=True,
            storage_dir="./command_schemas",
            use_llm=True,
            llm_config=self.llm_config
        )
        
        # Cache for command analysis
        self.command_cache = {}
        
        # Pattern library for intelligent analysis
        self.patterns = {
            'option_flag': r'^-([a-zA-Z])$',
            'long_option': r'^--([a-zA-Z][a-zA-Z0-9_-]*)$',
            'argument': r'^[a-zA-Z0-9_/.-]+$',
            'file_path': r'^[/~][a-zA-Z0-9_/.-]*$',
            'url': r'^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?$',
            'port': r'^:\d+$',
            'number': r'^\d+$',
            'size': r'^\d+[KMGT]?B?$',
        }
    
    def analyze_command(self, command: str) -> CommandInfo:
        """Analyze a command to understand its structure."""
        if command in self.command_cache:
            return self.command_cache[command]
        
        # Get help text
        help_text = self._get_help_text(command)
        
        # Extract information using intelligent analysis
        info = self._extract_command_info(command, help_text)
        
        # Cache result
        self.command_cache[command] = info
        
        return info
    
    def _get_help_text(self, command: str) -> str:
        """Get help text for a command."""
        try:
            # Try --help first
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
            
            # Try man page
            result = subprocess.run(
                ['man', command],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout + result.stderr
                
        except Exception:
            pass
        
        return ""
    
    def _extract_command_info(self, command: str, help_text: str) -> CommandInfo:
        """Extract command information from help text."""
        # Category detection based on command purpose
        category = self._detect_category(command, help_text)
        
        # Description extraction
        description = self._extract_description(command, help_text)
        
        # Common options extraction
        common_options = self._extract_options(help_text)
        
        # Examples extraction
        examples = self._extract_examples(command, help_text)
        
        return CommandInfo(
            name=command,
            category=category,
            description=description,
            common_options=common_options,
            examples=examples,
            help_available=bool(help_text.strip())
        )
    
    def _detect_category(self, command: str, help_text: str) -> str:
        """Detect command category based on purpose."""
        # Category keywords
        categories = {
            'file': ['file', 'directory', 'copy', 'move', 'remove', 'find', 'list'],
            'text': ['text', 'search', 'replace', 'sort', 'filter', 'pattern'],
            'network': ['network', 'connection', 'download', 'upload', 'http', 'url'],
            'system': ['system', 'process', 'memory', 'disk', 'uptime', 'load'],
            'development': ['compile', 'build', 'test', 'package', 'install'],
            'container': ['docker', 'container', 'image', 'pod', 'kubernetes'],
            'version_control': ['git', 'repository', 'commit', 'branch', 'merge'],
            'security': ['encrypt', 'decrypt', 'ssh', 'ssl', 'certificate', 'key'],
            'database': ['database', 'sql', 'query', 'table', 'backup'],
        }
        
        help_lower = help_text.lower()
        command_lower = command.lower()
        
        # Score each category
        scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in command_lower:
                    score += 3
                if keyword in help_lower:
                    score += 1
            scores[category] = score
        
        # Return category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return 'general'
    
    def _extract_description(self, command: str, help_text: str) -> str:
        """Extract command description."""
        lines = help_text.split('\n')
        
        # Look for description in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                # Skip if it looks like an option
                if not re.match(r'^-|\s+-', line):
                    return line[:200]  # Limit length
        
        # Fallback to first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()[:200]
        
        return f"{command} command"
    
    def _extract_options(self, help_text: str) -> List[str]:
        """Extract common options from help text."""
        options = []
        
        # Find option definitions
        for match in re.finditer(r'^\s*(-[a-zA-Z]),?\s*.*$', help_text, re.MULTILINE):
            option = match.group(1)
            options.append(option)
        
        for match in re.finditer(r'^\s*(--[a-zA-Z][a-zA-Z0-9_-]*)\s.*$', help_text, re.MULTILINE):
            option = match.group(1)
            options.append(option)
        
        # Common options to include
        common = {
            'file': ['-f', '--file', '-o', '--output'],
            'text': ['-i', '--ignore-case', '-r', '--recursive'],
            'system': ['-h', '--help', '-v', '--verbose'],
            'network': ['-p', '--port', '-t', '--timeout'],
        }
        
        # Add common options based on category
        for category, opts in common.items():
            if category in help_text.lower():
                options.extend(opts)
        
        return list(set(options))  # Remove duplicates
    
    def _extract_examples(self, command: str, help_text: str) -> List[str]:
        """Extract usage examples."""
        examples = []
        
        # Look for "EXAMPLES" section
        examples_section = re.search(r'EXAMPLES:(.*?)(?=\n[A-Z]|\Z)', help_text, re.DOTALL | re.IGNORECASE)
        if examples_section:
            for line in examples_section.group(1).split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and command in line:
                    examples.append(line)
        
        # Look for usage patterns
        usage_match = re.search(r'Usage:.*?(?=\n)', help_text, re.IGNORECASE)
        if usage_match:
            usage = usage_match.group(0)
            # Clean up usage line
            usage = re.sub(r'Usage:\s*', '', usage)
            usage = re.sub(r'\[.*?\]', '', usage)  # Remove optional parts
            examples.append(usage.strip())
        
        # Generate basic examples if none found
        if not examples:
            examples = [
                f"{command} --help",
                f"man {command}"
            ]
        
        return examples[:5]  # Limit to 5 examples
    
    def generate_schema(self, command: str, force_update: bool = False) -> Optional[ExtractedSchema]:
        """Generate schema for a command."""
        # Check if already exists
        if not force_update and command in self.registry.schemas:
            return self.registry.schemas[command]
        
        # Analyze command
        info = self.analyze_command(command)
        
        # Generate parameters
        parameters = self._generate_parameters(info)
        
        # Create command schema
        cmd_schema = CommandSchema(
            name=info.name,
            description=info.description,
            category=info.category,
            parameters=parameters,
            examples=info.examples,
            patterns=self._generate_patterns(info),
            source_type="intelligent_extraction",
            metadata={
                "generated_at": datetime.now().isoformat(),
                "help_available": info.help_available,
                "common_options": info.common_options
            },
            template=self._generate_template(info)
        )
        
        # Create extracted schema
        schema = ExtractedSchema(
            source=command,
            source_type="intelligent",
            commands=[cmd_schema],
            metadata={
                "extraction_method": "intelligent_analysis",
                "llm_assisted": True
            }
        )
        
        # Register schema
        self.registry.schemas[command] = schema
        self.registry._auto_save()
        
        return schema
    
    def _generate_parameters(self, info: CommandInfo) -> List[CommandParameter]:
        """Generate parameters based on command analysis."""
        params = []
        
        # Add common options as parameters
        for option in info.common_options[:10]:  # Limit to 10
            param_type = "boolean"
            if option.startswith('--'):
                name = option[2:].replace('-', '_')
            else:
                name = option[1:]
            
            # Determine type based on option name
            if any(word in name for word in ['file', 'input', 'output']):
                param_type = "file"
            elif any(word in name for word in ['port', 'count', 'number', 'size']):
                param_type = "integer"
            elif any(word in name for word in ['time', 'timeout']):
                param_type = "string"
            
            params.append(CommandParameter(
                name=name,
                type=param_type,
                description=f"Option {option}",
                required=False,
                location="option"
            ))
        
        # Add file parameter for file-based commands
        if info.category in ['file', 'text']:
            params.append(CommandParameter(
                name="file",
                type="file",
                description="File to process",
                required=False,
                location="argument"
            ))
        
        # Add pattern parameter for search commands
        if info.category == 'text' or 'search' in info.description.lower():
            params.append(CommandParameter(
                name="pattern",
                type="string",
                description="Search pattern",
                required=False,
                location="argument"
            ))
        
        return params
    
    def _generate_patterns(self, info: CommandInfo) -> List[str]:
        """Generate matching patterns."""
        patterns = [info.name]
        
        # Add category-based patterns
        if info.category == 'file':
            patterns.extend([f"{info.name} file", f"{info.name} directory"])
        elif info.category == 'text':
            patterns.extend([f"{info.name} pattern", f"{info.name} text"])
        elif info.category == 'network':
            patterns.extend([f"{info.name} url", f"{info.name} host"])
        
        return patterns
    
    def _generate_template(self, info: CommandInfo) -> str:
        """Generate command template."""
        template_parts = [info.name]
        
        # Add common options
        if info.common_options:
            template_parts.append("{options}")
        
        # Add arguments based on category
        if info.category == 'file':
            template_parts.append("{file}")
        elif info.category == 'text':
            template_parts.append("{pattern}")
        elif info.category == 'network':
            template_parts.append("{url}")
        
        return " ".join(template_parts)
    
    def batch_generate(self, commands: List[str], force_update: bool = False) -> Dict[str, bool]:
        """Generate schemas for multiple commands."""
        results = {}
        
        for command in commands:
            try:
                schema = self.generate_schema(command, force_update)
                results[command] = schema is not None
                print(f"{'✓' if schema else '✗'} {command}")
            except Exception as e:
                print(f"✗ {command}: {e}")
                results[command] = False
        
        return results


def main():
    """Main function to generate schemas for all commands."""
    
    # Read commands from cmd.txt or cmd.csv
    commands = []
    
    # Try cmd.csv first
    if Path('./cmd.csv').exists():
        print("Loading commands from cmd.csv...")
        with open('./cmd.csv') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row[1] and not row[1].startswith('#'):
                    cmd = row[1].split()[0] if row[1].split() else None
                    if cmd and cmd not in commands:
                        commands.append(cmd)
    
    # Try cmd.txt
    elif Path('./cmd.txt').exists():
        print("Loading commands from cmd.txt...")
        with open('./cmd.txt') as f:
            for line in f:
                cmd = line.strip()
                if cmd and cmd not in commands:
                    commands.append(cmd)
    else:
        print("Creating default command list...")
        commands = [
            'find', 'grep', 'sed', 'awk', 'ls', 'mkdir', 'rm', 'cp', 'mv',
            'ps', 'top', 'kill', 'docker', 'kubectl', 'git', 'curl', 'wget',
            'tar', 'zip', 'ssh', 'python3', 'npm', 'gcc', 'make'
        ]
    
    print(f"\nGenerating schemas for {len(commands)} commands...\n")
    
    # Initialize extractor
    extractor = IntelligentSchemaExtractor()
    
    # Generate schemas
    results = extractor.batch_generate(commands, force_update=True)
    
    # Summary
    successful = sum(results.values())
    print(f"\n✅ Generated {successful}/{len(commands)} schemas")
    print(f"📁 Schemas saved to: ./command_schemas/")
    
    # Show statistics
    print("\nSchema statistics:")
    print("-" * 40)
    
    categories = {}
    for command, success in results.items():
        if success:
            schema = extractor.registry.schemas.get(command)
            if schema and schema.commands:
                cat = schema.commands[0].category
                categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count} commands")
    
    # Export to JSON
    export_file = './generated_schemas.json'
    extractor.registry.save_cache(export_file)
    print(f"\n💾 All schemas exported to: {export_file}")


if __name__ == "__main__":
    import csv
    main()
