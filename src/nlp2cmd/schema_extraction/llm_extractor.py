"""LLM-powered schema extractor using LiteLLM."""

import json
import os
import re
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
  "description": "Specific description of what {command} does (not just '{command} command')",
  "category": "file|text|network|system|process|development",
  "template": "Practical template using {{placeholders}} for arguments",
  "examples": ["{command} example1", "{command} example2"]
}}

Rules:
- Use {{double braces}} for placeholders in template
- Be specific in description
- Choose the most specific category
- Template should be practical and commonly used

JSON:"""
        return prompt
    
    def extract_from_command(self, command: str) -> ExtractedSchema:
        """Extract schema using LLM assistance."""
        try:
            # First get help text using fallback extractor
            help_schema = self.fallback_extractor.extract_from_command(command)
            help_text = "\n".join(help_schema.commands[0].examples) if help_schema.commands else ""
            
            # If no help or too short, return basic schema with predefined template
            if not help_text or len(help_text) < 20:
                print(f"[LLMExtractor] Using predefined template for {command}")
                return self._create_schema_with_template(command)
            
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
            template = llm_data.get("template", "")
            
            # Validate and fix template
            template = self._validate_and_fix_template(command, template)
            
            # Fix category if too generic
            category = llm_data.get("category", "system")
            if category == "general":
                category = self._infer_category(command, help_text)
            
            # Fix description if generic
            description = llm_data.get("description", f"{command} command")
            if description == f"{command} command":
                description = self._generate_description(command, help_text)
            
            schema = CommandSchema(
                name=command,
                description=description,
                category=category,
                parameters=[],  # Skip parameters for speed
                examples=llm_data.get("examples", [f"{command} --help"]),
                patterns=[command],
                source_type="llm_enhanced",
                metadata={
                    "llm_model": self.model,
                    "enhanced": True,
                },
                template=template,
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
    
    def _validate_and_fix_template(self, command: str, template: str) -> str:
        """Validate and fix template syntax."""
        if not template:
            return None
        
        # Fix common issues
        # 1. Replace [] with {} for optional arguments
        template = re.sub(r'\[([^\]]+)\]', r'{\1}', template)
        
        # 2. Fix single braces to double braces
        template = re.sub(r'(?<!{){(?!{)([^}]+)}(?!})', r'{{\1}}', template)
        
        # 3. Remove overly complex templates
        if len(template) > 200:
            # Simplify to basic pattern
            if command in ['netstat', 'ss', 'lsof']:
                template = f"{command} {{options}}"
            else:
                template = f"{command} {{{{args}}}}"
        
        # 4. Fix specific known patterns
        fixes = {
            'netstat': 'netstat {options}',
            'ss': 'ss {options}',
            'lsof': 'lsof {options}',
            'ps': 'ps {options}',
            'top': 'top {options}',
        }
        
        if command in fixes and len(template) > 100:
            template = fixes[command]
        
        return template
    
    def _infer_category(self, command: str, help_text: str) -> str:
        """Infer category from command and help text."""
        # Category mapping based on command patterns
        file_commands = {'find', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'tar', 'zip', 'chmod', 'chown'}
        text_commands = {'grep', 'sed', 'awk', 'sort', 'uniq', 'wc', 'tr', 'cut', 'head', 'tail'}
        network_commands = {'ping', 'curl', 'wget', 'netstat', 'ss', 'lsof', 'ssh', 'scp', 'rsync'}
        process_commands = {'ps', 'top', 'kill', 'killall', 'nice', 'renice', 'jobs', 'bg', 'fg'}
        system_commands = {'df', 'du', 'free', 'uname', 'whoami', 'id', 'date', 'uptime', 'systemctl', 'service'}
        dev_commands = {'git', 'docker', 'kubectl', 'python', 'gcc', 'make', 'cargo', 'npm', 'pip'}
        
        if command in file_commands:
            return "file"
        elif command in text_commands:
            return "text"
        elif command in network_commands:
            return "network"
        elif command in process_commands:
            return "process"
        elif command in system_commands:
            return "system"
        elif command in dev_commands:
            return "development"
        else:
            # Try to infer from help text
            if 'file' in help_text.lower():
                return "file"
            elif 'text' in help_text.lower() or 'pattern' in help_text.lower():
                return "text"
            elif 'network' in help_text.lower() or 'connection' in help_text.lower():
                return "network"
            elif 'process' in help_text.lower() or 'pid' in help_text.lower():
                return "process"
            elif 'system' in help_text.lower():
                return "system"
            else:
                return "system"  # Default to system instead of general
    
    def _generate_description(self, command: str, help_text: str) -> str:
        """Generate a better description from help text."""
        # Try to extract first line from help
        lines = help_text.split('\n')[:3]
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                # Clean up the line
                if len(line) > 20:
                    return line.rstrip('.')
        
        # Fallback to command-specific descriptions
        descriptions = {
            'ps': 'List running processes',
            'top': 'Display running processes dynamically',
            'netstat': 'Display network connections',
            'ss': 'Display socket statistics',
            'lsof': 'List open files',
            'df': 'Report file system disk space usage',
            'du': 'Estimate file space usage',
            'free': 'Display amount of free and used memory',
            'uname': 'Print system information',
            'whoami': 'Print current user name',
            'id': 'Print user and group information',
            'date': 'Print or set the system date and time',
            'uptime': 'Tell how long the system has been running',
            'systemctl': 'Control the systemd system and service manager',
            'service': 'Run a System V init script',
            'kill': 'Send a signal to a process',
            'killall': 'Kill processes by name',
        }
        
        return descriptions.get(command, f"{command} utility")
    
    def _create_schema_with_template(self, command: str) -> ExtractedSchema:
        """Create schema with dynamically generated template."""
        # Import dynamic generator inside method to avoid circular import
        from nlp2cmd.intelligent.dynamic_generator import DynamicSchemaGenerator
        
        # Use dynamic generator instead of hardcoded templates
        generator = DynamicSchemaGenerator(self.config)
        return generator.generate_schema(command)
    
    def _create_basic_schema(self, command: str) -> ExtractedSchema:
        """Create a basic schema using intelligent analysis."""
        # Use intelligent analysis instead of hardcoded values
        category = self._intelligent_category_detection(command)
        description = self._intelligent_description_extraction(command)
        template = self._intelligent_template_generation(command, category)
        
        schema = CommandSchema(
            name=command,
            description=description,
            category=category,
            parameters=[],
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="basic_intelligent",
            metadata={"intelligent_generation": True},
            template=template,
        )
        
        return ExtractedSchema(
            source=command,
            source_type="basic_intelligent",
            commands=[schema],
            metadata={"intelligent_generation": True},
        )
    
    def _intelligent_category_detection(self, command: str) -> str:
        """Detect command category using intelligent analysis."""
        # Category patterns based on command behavior
        patterns = {
            'file': {
                'commands': ['find', 'ls', 'mkdir', 'rm', 'cp', 'mv', 'chmod', 'chown'],
                'keywords': ['file', 'directory', 'copy', 'move', 'remove', 'list', 'permissions']
            },
            'text': {
                'commands': ['grep', 'sed', 'awk', 'sort', 'uniq', 'wc', 'tr', 'cut'],
                'keywords': ['text', 'search', 'replace', 'pattern', 'filter', 'count']
            },
            'network': {
                'commands': ['curl', 'wget', 'ping', 'netstat', 'ssh', 'scp', 'rsync'],
                'keywords': ['network', 'download', 'upload', 'connection', 'transfer', 'remote']
            },
            'system': {
                'commands': ['ps', 'top', 'kill', 'free', 'df', 'du', 'uptime', 'uname'],
                'keywords': ['process', 'memory', 'disk', 'system', 'load', 'usage']
            },
            'archive': {
                'commands': ['tar', 'zip', 'unzip', 'gzip', 'gunzip'],
                'keywords': ['archive', 'compress', 'extract', 'zip', 'tar']
            },
            'development': {
                'commands': ['gcc', 'make', 'python', 'python3', 'node', 'npm', 'pip'],
                'keywords': ['compile', 'build', 'run', 'install', 'package']
            },
            'container': {
                'commands': ['docker', 'kubectl', 'podman'],
                'keywords': ['container', 'image', 'pod', 'kubernetes', 'docker']
            },
            'version_control': {
                'commands': ['git', 'svn', 'hg'],
                'keywords': ['git', 'repository', 'commit', 'branch', 'merge', 'clone']
            }
        }
        
        command_lower = command.lower()
        
        # Direct command matching
        for category, info in patterns.items():
            if command in info['commands']:
                return category
        
        # Keyword matching
        for category, info in patterns.items():
            for keyword in info['keywords']:
                if keyword in command_lower:
                    return category
        
        # Heuristic based detection
        if any(x in command for x in ['find', 'locate', 'whereis', 'which']):
            return 'file'
        elif any(x in command for x in ['grep', 'search', 'filter']):
            return 'text'
        elif any(x in command for x in ['http', 'ftp', 'ssh']):
            return 'network'
        elif any(x in command for x in ['kill', 'ps', 'top']):
            return 'system'
        
        return 'general'
    
    def _intelligent_description_extraction(self, command: str) -> str:
        """Extract description using intelligent patterns."""
        # Description templates based on category
        templates = {
            'file': f"{command} - File and directory manipulation utility",
            'text': f"{command} - Text processing and pattern matching tool",
            'network': f"{command} - Network communication and transfer utility",
            'system': f"{command} - System monitoring and process management",
            'archive': f"{command} - Archive and compression tool",
            'development': f"{command} - Development and build tool",
            'container': f"{command} - Container orchestration utility",
            'version_control': f"{command} - Version control system tool",
            'general': f"{command} - Command line utility"
        }
        
        category = self._intelligent_category_detection(command)
        return templates.get(category, f"{command} utility")
    
    def _intelligent_template_generation(self, command: str, category: str) -> str:
        """Generate template based on command category and patterns."""
        # Base templates by category
        base_templates = {
            'file': "{command} {options} {path}",
            'text': "{command} {options} {pattern} {file}",
            'network': "{command} {options} {url}",
            'system': "{command} {options}",
            'archive': "{command} {options} {archive}",
            'development': "{command} {options} {input}",
            'container': "{command} {subcommand} {options}",
            'version_control': "{command} {action} {options}",
            'general': "{command} {options}"
        }
        
        template = base_templates.get(category, "{command} {options}")
        
        # Command-specific adjustments
        if command == 'find':
            template = "find {path} -name '{pattern}'"
        elif command == 'grep':
            template = "grep {options} '{pattern}' {file}"
        elif command == 'docker':
            template = "docker {subcommand} {options}"
        elif command == 'kubectl':
            template = "kubectl {resource} {action} {options}"
        elif command == 'git':
            template = "git {action} {options}"
        
        return template
