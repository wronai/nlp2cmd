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
        """Create schema with predefined template for common commands."""
        # Predefined templates and descriptions for commands with minimal help
        command_defs = {
            'wget': {'template': 'wget {options} {url}', 'desc': 'Download files from the web', 'cat': 'network'},
            'ping': {'template': 'ping -c {count} {host}', 'desc': 'Send ICMP echo requests to test connectivity', 'cat': 'network'},
            'df': {'template': 'df -h {path}', 'desc': 'Report file system disk space usage', 'cat': 'system'},
            'du': {'template': 'du -sh {path}', 'desc': 'Estimate file space usage', 'cat': 'system'},
            'free': {'template': 'free -h', 'desc': 'Display amount of free and used memory', 'cat': 'system'},
            'uname': {'template': 'uname -a', 'desc': 'Print system information', 'cat': 'system'},
            'whoami': {'template': 'whoami', 'desc': 'Print current user name', 'cat': 'system'},
            'id': {'template': 'id -u', 'desc': 'Print user and group information', 'cat': 'system'},
            'date': {'template': 'date +"%Y-%m-%d"', 'desc': 'Print or set the system date', 'cat': 'system'},
            'uptime': {'template': 'uptime', 'desc': 'Tell how long the system has been running', 'cat': 'system'},
            'which': {'template': 'which {command}', 'desc': 'Locate a command in the PATH', 'cat': 'system'},
            'whereis': {'template': 'whereis {command}', 'desc': 'Locate binary and manual files', 'cat': 'system'},
            'history': {'template': 'history {count}', 'desc': 'Display command history', 'cat': 'system'},
            'alias': {'template': 'alias {name}="{value}"', 'desc': 'Create or display aliases', 'cat': 'system'},
            'export': {'template': 'export {variable}={value}', 'desc': 'Set environment variables', 'cat': 'system'},
            'ps': {'template': 'ps aux', 'desc': 'List running processes', 'cat': 'process'},
            'top': {'template': 'top', 'desc': 'Display running processes dynamically', 'cat': 'process'},
            'kill': {'template': 'kill -{signal} {pid}', 'desc': 'Send a signal to a process', 'cat': 'process'},
            'ss': {'template': 'ss -tuln', 'desc': 'Display socket statistics', 'cat': 'network'},
            'lsof': {'template': 'lsof -i :{port}', 'desc': 'List open files', 'cat': 'system'},
            'systemctl': {'template': 'systemctl {action} {service}', 'desc': 'Control systemd services', 'cat': 'system'},
            'service': {'template': 'service {name} {action}', 'desc': 'Run System V init scripts', 'cat': 'system'},
            'killall': {'template': 'killall {process}', 'desc': 'Kill processes by name', 'cat': 'process'},
            'echo': {'template': 'echo "{message}"', 'desc': 'Display a message', 'cat': 'system'},
            'printf': {'template': 'printf "{format}" {args}', 'desc': 'Format and print data', 'cat': 'system'},
            'cat': {'template': 'cat {file}', 'desc': 'Display file contents', 'cat': 'text'},
            'less': {'template': 'less {file}', 'desc': 'View file interactively', 'cat': 'text'},
            'more': {'template': 'more {file}', 'desc': 'View file page by page', 'cat': 'text'},
            'head': {'template': 'head -n {count} {file}', 'desc': 'Display first lines of file', 'cat': 'text'},
            'tail': {'template': 'tail -n {count} {file}', 'desc': 'Display last lines of file', 'cat': 'text'},
            'sort': {'template': 'sort {options} {file}', 'desc': 'Sort lines of text', 'cat': 'text'},
            'uniq': {'template': 'uniq {options} {file}', 'desc': 'Remove duplicate lines', 'cat': 'text'},
            'wc': {'template': 'wc -l {file}', 'desc': 'Count lines in file', 'cat': 'text'},
            'tr': {'template': 'tr "{from}" "{to}"', 'desc': 'Translate characters', 'cat': 'text'},
            'cut': {'template': 'cut -d {delimiter} -f {field} {file}', 'desc': 'Extract columns', 'cat': 'text'},
            'paste': {'template': 'paste -d {delimiter} {file1} {file2}', 'desc': 'Merge lines', 'cat': 'text'},
            'split': {'template': 'split -l {lines} {file}', 'desc': 'Split file into pieces', 'cat': 'text'},
            'xargs': {'template': 'xargs {command}', 'desc': 'Build and execute commands', 'cat': 'text'},
            'ssh': {'template': 'ssh {user}@{host} "{command}"', 'desc': 'Connect to remote host', 'cat': 'network'},
            'scp': {'template': 'scp {file} {user}@{host}:{path}', 'desc': 'Copy files remotely', 'cat': 'network'},
            'rsync': {'template': 'rsync -av {source} {destination}', 'desc': 'Sync files remotely', 'cat': 'network'},
            'zip': {'template': 'zip {archive}.zip {files}', 'desc': 'Compress files to ZIP', 'cat': 'file'},
            'unzip': {'template': 'unzip {archive}.zip', 'desc': 'Extract ZIP files', 'cat': 'file'},
            'gzip': {'template': 'gzip {file}', 'desc': 'Compress with GZIP', 'cat': 'file'},
            'gunzip': {'template': 'gunzip {file}.gz', 'desc': 'Extract GZIP files', 'cat': 'file'},
            'tar': {'template': 'tar -czf {archive}.tar.gz {source}', 'desc': 'Create tar archive', 'cat': 'file'},
            'chmod': {'template': 'chmod {permissions} {file}', 'desc': 'Change file permissions', 'cat': 'file'},
            'chown': {'template': 'chown {owner}:{group} {file}', 'desc': 'Change file ownership', 'cat': 'file'},
            'chgrp': {'template': 'chgrp {group} {file}', 'desc': 'Change group ownership', 'cat': 'file'},
            'find': {'template': 'find {path} -name "{pattern}"', 'desc': 'Search for files', 'cat': 'file'},
            'locate': {'template': 'locate {pattern}', 'desc': 'Find files by name', 'cat': 'file'},
            'which': {'template': 'which {command}', 'desc': 'Locate command in PATH', 'cat': 'system'},
            'whereis': {'template': 'whereis {command}', 'desc': 'Locate binary files', 'cat': 'system'},
            'type': {'template': 'type {command}', 'desc': 'Show command type', 'cat': 'system'},
            'man': {'template': 'man {command}', 'desc': 'Show manual page', 'cat': 'system'},
            'info': {'template': 'info {command}', 'desc': 'Show info documentation', 'cat': 'system'},
            'help': {'template': 'help {command}', 'desc': 'Show help for command', 'cat': 'system'},
            'history': {'template': 'history {count}', 'desc': 'Display command history', 'cat': 'system'},
            'alias': {'template': 'alias {name}="{value}"', 'desc': 'Create command alias', 'cat': 'system'},
            'export': {'template': 'export {variable}={value}', 'desc': 'Set environment variable', 'cat': 'system'},
            'bg': {'template': 'bg {job_id}', 'desc': 'Resume job in background', 'cat': 'process'},
            'fg': {'template': 'fg {job_id}', 'desc': 'Resume job in foreground', 'cat': 'process'},
            'jobs': {'template': 'jobs', 'desc': 'List active jobs', 'cat': 'process'},
            'disown': {'template': 'disown {job_id}', 'desc': 'Remove job from shell', 'cat': 'process'},
            'nice': {'template': 'nice -n {level} {command}', 'desc': 'Run command with priority', 'cat': 'process'},
            'renice': {'template': 'renice {priority} -p {pid}', 'desc': 'Change process priority', 'cat': 'process'},
            'ionice': {'template': 'ionice -c {class} -n {level} {command}', 'desc': 'Set I/O priority', 'cat': 'process'},
            'timeout': {'template': 'timeout {duration} {command}', 'desc': 'Run command with timeout', 'cat': 'process'},
            'flock': {'template': 'flock {file} {command}', 'desc': 'Execute with file lock', 'cat': 'system'},
            'screen': {'template': 'screen -r {session}', 'desc': 'Attach to screen session', 'cat': 'system'},
            'tmux': {'template': 'tmux attach -t {session}', 'desc': 'Attach to tmux session', 'cat': 'system'},
            'vim': {'template': 'vim {file}', 'desc': 'Edit file with Vim', 'cat': 'development'},
            'nano': {'template': 'nano {file}', 'desc': 'Edit file with Nano', 'cat': 'development'},
            'emacs': {'template': 'emacs {file}', 'desc': 'Edit file with Emacs', 'cat': 'development'},
            'code': {'template': 'code {file}', 'desc': 'Open in VS Code', 'cat': 'development'},
            'python': {'template': 'python {script}.py', 'desc': 'Run Python script', 'cat': 'development'},
            'python3': {'template': 'python3 {script}.py', 'desc': 'Run Python 3 script', 'cat': 'development'},
            'pip': {'template': 'pip install {package}', 'desc': 'Install Python package', 'cat': 'development'},
            'pip3': {'template': 'pip3 install {package}', 'desc': 'Install Python 3 package', 'cat': 'development'},
            'npm': {'template': 'npm install {package}', 'desc': 'Install Node package', 'cat': 'development'},
            'yarn': {'template': 'yarn install', 'desc': 'Install Node dependencies', 'cat': 'development'},
            'node': {'template': 'node {script}.js', 'desc': 'Run Node script', 'cat': 'development'},
            'java': {'template': 'java {class}', 'desc': 'Run Java program', 'cat': 'development'},
            'javac': {'template': 'javac {file}.java', 'desc': 'Compile Java file', 'cat': 'development'},
            'gcc': {'template': 'gcc -o {output} {input}.c', 'desc': 'Compile C code', 'cat': 'development'},
            'g++': {'template': 'g++ -o {output} {input}.cpp', 'desc': 'Compile C++ code', 'cat': 'development'},
            'make': {'template': 'make {target}', 'desc': 'Build with Make', 'cat': 'development'},
            'cmake': {'template': 'cmake {path}', 'desc': 'Configure with CMake', 'cat': 'development'},
            'cargo': {'template': 'cargo {command}', 'desc': 'Rust package manager', 'cat': 'development'},
            'rustc': {'template': 'rustc {file}.rs', 'desc': 'Compile Rust code', 'cat': 'development'},
            'go': {'template': 'go run {file}.go', 'desc': 'Run Go program', 'cat': 'development'},
            'ruby': {'template': 'ruby {script}.rb', 'desc': 'Run Ruby script', 'cat': 'development'},
            'gem': {'template': 'gem install {gem}', 'desc': 'Install Ruby gem', 'cat': 'development'},
            'perl': {'template': 'perl {script}.pl', 'desc': 'Run Perl script', 'cat': 'development'},
            'php': {'template': 'php {script}.php', 'desc': 'Run PHP script', 'cat': 'development'},
            'kubectl': {'template': 'kubectl {command} {resource}', 'desc': 'Kubernetes control', 'cat': 'development'},
            'docker': {'template': 'docker {subcommand} {options}', 'desc': 'Docker container manager', 'cat': 'development'},
            'docker-compose': {'template': 'docker-compose {command}', 'desc': 'Docker Compose tool', 'cat': 'development'},
            'git': {'template': 'git {command} {options}', 'desc': 'Git version control', 'cat': 'development'},
            'curl': {'template': 'curl {options} {url}', 'desc': 'Transfer data with URL', 'cat': 'network'},
            'wget': {'template': 'wget {options} {url}', 'desc': 'Download files from web', 'cat': 'network'},
            'ping': {'template': 'ping -c {count} {host}', 'desc': 'Test network connectivity', 'cat': 'network'},
            'netstat': {'template': 'netstat {options}', 'desc': 'Display network connections', 'cat': 'network'},
            'ss': {'template': 'ss -tuln', 'desc': 'Display socket statistics', 'cat': 'network'},
            'lsof': {'template': 'lsof -i :{port}', 'desc': 'List open files', 'cat': 'system'},
            'systemctl': {'template': 'systemctl {action} {service}', 'desc': 'Control systemd services', 'cat': 'system'},
            'service': {'template': 'service {name} {action}', 'desc': 'Run System V scripts', 'cat': 'system'},
            'ps': {'template': 'ps aux', 'desc': 'List running processes', 'cat': 'process'},
            'top': {'template': 'top', 'desc': 'Display processes dynamically', 'cat': 'process'},
            'kill': {'template': 'kill -{signal} {pid}', 'desc': 'Send signal to process', 'cat': 'process'},
            'killall': {'template': 'killall {process}', 'desc': 'Kill processes by name', 'cat': 'process'},
            'pkill': {'template': 'pkill {pattern}', 'desc': 'Kill processes by pattern', 'cat': 'process'},
            'pgrep': {'template': 'pgrep {pattern}', 'desc': 'Find processes by pattern', 'cat': 'process'},
            'pidof': {'template': 'pidof {program}', 'desc': 'Find PID of program', 'cat': 'process'},
            'nice': {'template': 'nice -n {level} {command}', 'desc': 'Run with modified priority', 'cat': 'process'},
            'renice': {'template': 'renice {priority} -p {pid}', 'desc': 'Change process priority', 'cat': 'process'},
            'ionice': {'template': 'ionice -c {class} {command}', 'desc': 'Set I/O scheduling', 'cat': 'process'},
            'nohup': {'template': 'nohup {command}', 'desc': 'Run immune to hangups', 'cat': 'process'},
            'bg': {'template': 'bg {job_id}', 'desc': 'Resume in background', 'cat': 'process'},
            'fg': {'template': 'fg {job_id}', 'desc': 'Resume in foreground', 'cat': 'process'},
            'jobs': {'template': 'jobs', 'desc': 'List active jobs', 'cat': 'process'},
            'disown': {'template': 'disown {job_id}', 'desc': 'Remove from shell', 'cat': 'process'},
            'df': {'template': 'df -h {path}', 'desc': 'Report disk space usage', 'cat': 'system'},
            'du': {'template': 'du -sh {path}', 'desc': 'Estimate file space usage', 'cat': 'system'},
            'free': {'template': 'free -h', 'desc': 'Display memory usage', 'cat': 'system'},
            'uname': {'template': 'uname -a', 'desc': 'Print system information', 'cat': 'system'},
            'whoami': {'template': 'whoami', 'desc': 'Print current user', 'cat': 'system'},
            'id': {'template': 'id -u', 'desc': 'Print user ID', 'cat': 'system'},
            'date': {'template': 'date +"%Y-%m-%d"', 'desc': 'Print system date', 'cat': 'system'},
            'cal': {'template': 'cal {month} {year}', 'desc': 'Display calendar', 'cat': 'system'},
            'uptime': {'template': 'uptime', 'desc': 'System uptime', 'cat': 'system'},
            'time': {'template': 'time {command}', 'desc': 'Time command execution', 'cat': 'system'},
            'sleep': {'template': 'sleep {seconds}', 'desc': 'Pause execution', 'cat': 'system'},
            'watch': {'template': 'watch -n {interval} {command}', 'desc': 'Run command repeatedly', 'cat': 'system'},
            'ls': {'template': 'ls -la {path}', 'desc': 'List directory contents', 'cat': 'file'},
            'mkdir': {'template': 'mkdir -p {path}', 'desc': 'Create directories', 'cat': 'file'},
            'rm': {'template': 'rm -rf {path}', 'desc': 'Remove files', 'cat': 'file'},
            'cp': {'template': 'cp -r {source} {dest}', 'desc': 'Copy files', 'cat': 'file'},
            'mv': {'template': 'mv {source} {dest}', 'desc': 'Move files', 'cat': 'file'},
            'find': {'template': 'find {path} -name "{pattern}"', 'desc': 'Search for files', 'cat': 'file'},
            'grep': {'template': 'grep -r "{pattern}" {path}', 'desc': 'Search text patterns', 'cat': 'text'},
            'sed': {'template': 'sed -e "{script}" {file}', 'desc': 'Stream editor', 'cat': 'text'},
            'awk': {'template': 'awk "{script}" {file}', 'desc': 'Pattern processor', 'cat': 'text'},
            'sort': {'template': 'sort {options} {file}', 'desc': 'Sort text lines', 'cat': 'text'},
        }
        
        cmd_def = command_defs.get(command, {
            'template': None,
            'desc': f"{command} utility",
            'cat': 'system'
        })
        
        schema = CommandSchema(
            name=command,
            description=cmd_def['desc'],
            category=cmd_def['cat'],
            parameters=[],
            examples=[f"{command} --help"],
            patterns=[command],
            source_type="predefined_template",
            metadata={"predefined": True},
            template=cmd_def['template'],
        )
        
        return ExtractedSchema(
            source=command,
            source_type="predefined_template",
            commands=[schema],
            metadata={"predefined": True},
        )
    
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
