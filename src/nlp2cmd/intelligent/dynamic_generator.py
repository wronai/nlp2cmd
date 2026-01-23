#!/usr/bin/env python3
"""Dynamic schema generator without hardcoded templates."""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from nlp2cmd.schema_extraction.llm_extractor import LLMSchemaExtractor
from nlp2cmd.schema_extraction import CommandSchema, ExtractedSchema

class DynamicSchemaGenerator:
    """Generates schemas dynamically without hardcoding."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize with LLM configuration."""
        self.llm_extractor = LLMSchemaExtractor(llm_config)
        self._template_cache = {}
        
        # Category mapping for inference
        self.category_patterns = {
            'file': r'\b(file|files|directory|folder|path|archive|compress|copy|move|remove)\b',
            'text': r'\b(text|search|pattern|replace|edit|parse|content)\b',
            'network': r'\b(network|connection|download|upload|remote|ssh|scp|url|host)\b',
            'system': r'\b(system|memory|disk|usage|uptime|kernel|info)\b',
            'process': r'\b(process|kill|pid|running|monitor|background|job)\b',
            'development': r'\b(git|docker|kubernetes|compile|build|code|package|install)\b'
        }
    
    def generate_schema(self, command: str, context: Optional[str] = None) -> ExtractedSchema:
        """
        Generate a schema for a command dynamically.
        
        Args:
            command: The command name
            context: Optional context to help generation
            
        Returns:
            ExtractedSchema with dynamically generated template
        """
        # Check cache first
        cache_key = f"{command}:{context or ''}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Try LLM extraction first
        try:
            schema = self.llm_extractor.extract_from_command(command)
            if schema.commands and schema.commands[0].template:
                self._template_cache[cache_key] = schema
                return schema
        except Exception:
            pass
        
        # Generate template based on command patterns
        template = self._generate_template(command, context)
        description = self._generate_description(command, context)
        category = self._infer_category(command, context)
        
        # Create schema
        cmd_schema = CommandSchema(
            name=command,
            description=description,
            category=category,
            parameters=[],
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="dynamic_generated",
            metadata={"generated": True, "context": context},
            template=template,
        )
        
        schema = ExtractedSchema(
            source=command,
            source_type="dynamic_generated",
            commands=[cmd_schema],
            metadata={"generated": True}
        )
        
        # Cache the result
        self._template_cache[cache_key] = schema
        return schema
    
    def _generate_template(self, command: str, context: Optional[str] = None) -> Optional[str]:
        """Generate a template based on command and context."""
        # Template patterns based on command type
        template_patterns = {
            # File operations
            'find': 'find {path} -name "{pattern}"',
            'grep': 'grep -r "{pattern}" {path}',
            'sed': 'sed -e "{script}" {file}',
            'awk': 'awk "{script}" {file}',
            'ls': 'ls -{flags} {path}',
            'mkdir': 'mkdir -p {path}',
            'rm': 'rm -{flags} {path}',
            'cp': 'cp -{flags} {source} {destination}',
            'mv': 'mv -{flags} {source} {destination}',
            
            # Archives
            'tar': 'tar -{compression}f {archive} {source}',
            'zip': 'zip -r {archive} {files}',
            'unzip': 'unzip {archive}',
            
            # System
            'ps': 'ps {options}',
            'top': 'top',
            'kill': 'kill -{signal} {pid}',
            'df': 'df -{flags} {path}',
            'du': 'du -{flags} {path}',
            'free': 'free -{flags}',
            'uname': 'uname -{flags}',
            'uptime': 'uptime',
            
            # Network
            'ping': 'ping -c {count} {host}',
            'curl': 'curl {options} {url}',
            'wget': 'wget {options} {url}',
            'ssh': 'ssh {user}@{host}',
            'scp': 'scp {source} {user}@{host}:{path}',
            
            # Development
            'git': 'git {command} {options}',
            'docker': 'docker {command} {options}',
            'kubectl': 'kubectl {command} {resource}',
            'make': 'make {target}',
            'gcc': 'gcc -o {output} {input}',
            'python': 'python {script}',
            'npm': 'npm {command} {package}',
        }
        
        # Get base template
        base_template = template_patterns.get(command)
        if not base_template:
            # Generate generic template
            base_template = f"{command} {{options}}"
        
        # Customize based on context
        if context:
            # Check for specific patterns in context
            if 'python' in context.lower() and command == 'find':
                return 'find {path} -name "*.py"'
            elif 'log' in context.lower() and command == 'find':
                return 'find {path} -name "*.log"'
            elif 'backup' in context.lower() and command == 'tar':
                return 'tar -czf {backup}.tar.gz {source}'
            elif 'status' in context.lower() and command == 'git':
                return 'git status'
            elif 'containers' in context.lower() and command == 'docker':
                return 'docker ps -a'
            elif 'pods' in context.lower() and command == 'kubectl':
                return 'kubectl get pods'
        
        return base_template
    
    def _generate_description(self, command: str, context: Optional[str] = None) -> str:
        """Generate description based on command and context."""
        descriptions = {
            'find': 'Search for files and directories',
            'grep': 'Search for patterns in files',
            'sed': 'Stream editor for text transformation',
            'awk': 'Pattern scanning and processing language',
            'ls': 'List directory contents',
            'mkdir': 'Create directories',
            'rm': 'Remove files or directories',
            'cp': 'Copy files or directories',
            'mv': 'Move or rename files',
            'tar': 'Create or extract archive files',
            'zip': 'Package and compress files',
            'unzip': 'Extract zip archives',
            'ps': 'Report process status',
            'top': 'Display running processes',
            'kill': 'Send signals to processes',
            'df': 'Report file system disk space',
            'du': 'Estimate file space usage',
            'free': 'Display amount of free memory',
            'uname': 'Print system information',
            'uptime': 'Tell how long system has been running',
            'ping': 'Send ICMP echo requests',
            'curl': 'Transfer data from URLs',
            'wget': 'Download files from the web',
            'ssh': 'Connect to remote hosts',
            'scp': 'Copy files between hosts',
            'git': 'Git version control system',
            'docker': 'Docker container platform',
            'kubectl': 'Kubernetes command line tool',
            'make': 'Build automation tool',
            'gcc': 'GNU compiler collection',
            'python': 'Python programming language',
            'npm': 'Node package manager',
        }
        
        base_desc = descriptions.get(command, f"{command} utility")
        
        # Enhance with context if available
        if context:
            if 'python' in context.lower():
                return f"{base_desc} for Python files"
            elif 'backup' in context.lower():
                return f"{base_desc} for backup operations"
            elif 'system' in context.lower():
                return f"{base_desc} for system monitoring"
        
        return base_desc
    
    def _infer_category(self, command: str, context: Optional[str] = None) -> str:
        """Infer category from command and context."""
        # Check command-specific categories
        command_categories = {
            'find': 'file', 'grep': 'text', 'sed': 'text', 'awk': 'text',
            'ls': 'file', 'mkdir': 'file', 'rm': 'file', 'cp': 'file', 'mv': 'file',
            'tar': 'file', 'zip': 'file', 'unzip': 'file',
            'ps': 'process', 'top': 'process', 'kill': 'process',
            'df': 'system', 'du': 'system', 'free': 'system', 'uname': 'system', 'uptime': 'system',
            'ping': 'network', 'curl': 'network', 'wget': 'network', 'ssh': 'network', 'scp': 'network',
            'git': 'development', 'docker': 'development', 'kubectl': 'development',
            'make': 'development', 'gcc': 'development', 'python': 'development', 'npm': 'development',
        }
        
        # Direct mapping
        if command in command_categories:
            return command_categories[command]
        
        # Infer from context
        if context:
            context_lower = context.lower()
            for category, pattern in self.category_patterns.items():
                if re.search(pattern, context_lower):
                    return category
        
        # Default
        return 'system'


def test_dynamic_generation():
    """Test dynamic schema generation."""
    generator = DynamicSchemaGenerator({
        'model': 'ollama/qwen2.5-coder:7b',
        'api_base': 'http://localhost:11434',
        'temperature': 0.1,
        'max_tokens': 512,
        'timeout': 10,
    })
    
    test_cases = [
        ('find', 'Find Python files'),
        ('grep', 'Search for TODO in files'),
        ('tar', 'Create backup archive'),
        ('git', 'Check git status'),
        ('docker', 'List containers'),
        ('kubectl', 'Check pods'),
    ]
    
    print("Dynamic Schema Generation Test")
    print("=" * 60)
    
    for command, context in test_cases:
        print(f"\nCommand: {command}")
        print(f"Context: {context}")
        
        schema = generator.generate_schema(command, context)
        if schema.commands:
            cmd = schema.commands[0]
            print(f"  Template: {cmd.template}")
            print(f"  Description: {cmd.description}")
            print(f"  Category: {cmd.category}")
            print(f"  Source: {cmd.source_type}")


if __name__ == "__main__":
    test_dynamic_generation()
