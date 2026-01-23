#!/usr/bin/env python3
"""
Comprehensive Command Scanner with Full Option Detection

This module scans commands to extract ALL available options:
1. Parse help text for options
2. Extract from man pages
3. Detect argument types
4. Infer option relationships
5. Generate complete parameter lists
"""

import sys
sys.path.insert(0, './src')

import re
import subprocess
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from nlp2cmd.schema_extraction import (
    DynamicSchemaRegistry,
    ExtractedSchema,
    CommandSchema,
    CommandParameter
)


class OptionType(Enum):
    """Types of command options."""
    FLAG = "flag"           # Boolean flag (-v, --verbose)
    VALUE = "value"         # Requires value (-f FILE, --file=FILE)
    MULTIPLE = "multiple"   # Multiple values (-f file1,file2)
    OPTIONAL = "optional"   # Optional value [-f FILE]
    LIST = "list"          # List of choices (--format=json|yaml|xml)


@dataclass
class ParsedOption:
    """Parsed command option."""
    name: str
    short: Optional[str] = None
    long: Optional[str] = None
    type: OptionType = OptionType.FLAG
    description: str = ""
    default_value: Optional[str] = None
    choices: List[str] = field(default_factory=list)
    required: bool = False
    repeatable: bool = False
    argument_name: str = ""
    mutually_exclusive: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


class ComprehensiveCommandScanner:
    """Scanner that extracts ALL command options."""
    
    def __init__(self):
        """Initialize scanner."""
        self.logger = logging.getLogger(__name__)
        self.registry = DynamicSchemaRegistry(
            use_per_command_storage=True,
            storage_dir="./command_schemas"
        )
        
        # Option parsing patterns
        self.option_patterns = {
            # Short and long options
            'short_long': r'^\s*(-([a-zA-Z])),?\s*(--([a-zA-Z][a-zA-Z0-9_-]*))?\s*(.*)$',
            'long_only': r'^\s*(--([a-zA-Z][a-zA-Z0-9_-]*))(?:=(\S+))?\s*(.*)$',
            'short_only': r'^\s*(-([a-zA-Z]))\s*(.*)$',
            
            # Value indicators
            'equals_value': r'--([a-zA-Z][a-zA-Z0-9_-]*)=(\S+)',
            'space_value': r'--([a-zA-Z][a-zA-Z0-9_-]*)\s+<(\S+)>',
            'bracket_value': r'\[(-\w|--\w+)\s*(\S+)\]',
            
            # Multiple values
            'comma_separated': r'--([a-zA-Z][a-zA-Z0-9_-]*)=(.*?,.*)',
            'repeatable': r'--([a-zA-Z][a-zA-Z0-9_-]*)\s+\.\.\.',
            
            # Choices
            'choices': r'\{([^}]+)\}',
            'pipe_choices': r'--\w+\s+(?:\w+\|)+\w+',
        }
        
        # Type detection patterns
        self.type_patterns = {
            'file': r'<(file|path|filename|directory|dir)>',
            'number': r'<(num|number|count|size|length|port)>',
            'int': r'<(int|integer)>',
            'float': r'<(float|double)>',
            'string': r'<(str|string|text|name|value|pattern)>',
            'url': r'<(url|uri)>',
            'date': r'<(date|time)>',
            'format': r'<(format|fmt)>',
        }
        
        # Known command signatures
        self.command_signatures = self._load_command_signatures()
    
    def scan_command(self, command: str) -> ExtractedSchema:
        """Scan command and extract ALL options."""
        
        self.logger.info(f"Scanning command: {command}")
        
        # Collect all information
        help_text = self._get_help_text(command)
        man_text = self._get_man_page(command)
        version_text = self._get_version_text(command)
        
        # Parse all options
        options = self._parse_all_options(command, help_text, man_text)
        
        # Detect option relationships
        self._detect_relationships(options)
        
        # Create parameters
        parameters = self._create_parameters_from_options(options)
        
        # Generate examples
        examples = self._generate_comprehensive_examples(command, options)
        
        # Infer template
        template = self._generate_comprehensive_template(command, options)
        
        # Create schema
        cmd_schema = CommandSchema(
            name=command,
            description=self._extract_description(help_text or man_text),
            category=self._detect_category(command, help_text + man_text),
            parameters=parameters,
            examples=examples,
            patterns=self._generate_patterns(command, options),
            source_type="comprehensive_scan",
            metadata={
                "scan_version": "2.0",
                "options_count": len(options),
                "has_help": bool(help_text),
                "has_man": bool(man_text),
                "version": version_text.strip(),
                "comprehensive": True
            },
            template=template
        )
        
        return ExtractedSchema(
            source=command,
            source_type="comprehensive_scan",
            commands=[cmd_schema],
            metadata={"scan_method": "comprehensive"}
        )
    
    def _parse_all_options(self, command: str, help_text: str, man_text: str) -> List[ParsedOption]:
        """Parse all options from help and man pages."""
        
        options = {}
        
        # Parse help text
        if help_text:
            help_options = self._parse_options_from_text(help_text, "help")
            for opt in help_options:
                key = self._get_option_key(opt)
                options[key] = opt
        
        # Parse man page
        if man_text:
            man_options = self._parse_options_from_text(man_text, "man")
            for opt in man_options:
                key = self._get_option_key(opt)
                if key in options:
                    # Merge information
                    options[key] = self._merge_options(options[key], opt)
                else:
                    options[key] = opt
        
        # Add known options for command
        if command in self.command_signatures:
            known_options = self.command_signatures[command]["options"]
            for opt_data in known_options:
                opt = self._create_option_from_signature(opt_data)
                key = self._get_option_key(opt)
                if key not in options:
                    options[key] = opt
        
        return list(options.values())
    
    def _parse_options_from_text(self, text: str, source: str) -> List[ParsedOption]:
        """Parse options from text."""
        
        options = []
        lines = text.split('\n')
        
        for line in lines:
            # Skip empty lines and headers
            line = line.strip()
            if not line or line.isupper() or line.startswith('USAGE:'):
                continue
            
            # Try different patterns
            option = self._parse_option_line(line)
            if option:
                option.description = self._clean_description(line)
                options.append(option)
        
        return options
    
    def _parse_option_line(self, line: str) -> Optional[ParsedOption]:
        """Parse a single option line."""
        
        # Pattern 1: -f, --file=FILE
        match = re.match(self.option_patterns['short_long'], line)
        if match:
            groups = match.groups()
            short = groups[0] if len(groups) > 0 else None
            long_opt = groups[1] if len(groups) > 1 else None
            long_name = groups[2] if len(groups) > 2 else None
            desc = groups[3] if len(groups) > 3 else ""
            
            option = ParsedOption()
            
            if short:
                option.short = short
                option.name = short[1:]
            
            if long_name:
                option.long = f"--{long_name}"
                if not option.name:
                    option.name = long_name
            
            # Detect type from description
            option.type, option.argument_name = self._detect_option_type(desc)
            
            return option
        
        # Pattern 2: --file=FILE
        match = re.match(self.option_patterns['long_only'], line)
        if match:
            long_opt, value, desc = match.groups()
            option = ParsedOption()
            option.long = long_opt
            option.name = long_opt[2:]
            
            if value:
                option.type = OptionType.VALUE
                option.argument_name = value.upper()
            else:
                option.type, option.argument_name = self._detect_option_type(desc)
            
            return option
        
        # Pattern 3: -f FILE
        match = re.match(self.option_patterns['short_only'], line)
        if match:
            short, desc = match.groups()
            option = ParsedOption()
            option.short = short
            option.name = short[1:]
            option.type, option.argument_name = self._detect_option_type(desc)
            
            return option
        
        return None
    
    def _detect_option_type(self, description: str) -> Tuple[OptionType, str]:
        """Detect option type from description."""
        
        desc_upper = description.upper()
        
        # Check for equals value
        if '=' in description:
            name = description.split('=')[1].split()[0]
            return OptionType.VALUE, name
        
        # Check for angle brackets
        match = re.search(r'<([^>]+)>', description)
        if match:
            arg_name = match.group(1)
            
            # Check for specific types
            for type_name, pattern in self.type_patterns.items():
                if re.search(pattern, f"<{arg_name}>"):
                    return OptionType.VALUE, arg_name.upper()
            
            return OptionType.VALUE, arg_name.upper()
        
        # Check for brackets (optional)
        match = re.search(r'\[([^\]]+)\]', description)
        if match and not match.group(1).startswith('-'):
            return OptionType.OPTIONAL, match.group(1).upper()
        
        # Check for choices
        match = re.search(self.option_patterns['choices'], description)
        if match:
            choices = [c.strip() for c in match.group(1).split('|')]
            return OptionType.LIST, "CHOICE"
        
        # Check for repeatable
        if '...' in description or 'can be used' in description.lower():
            return OptionType.MULTIPLE, "VALUE"
        
        # Default to flag
        return OptionType.FLAG, ""
    
    def _detect_relationships(self, options: List[ParsedOption]):
        """Detect relationships between options."""
        
        # Look for mutual exclusion patterns
        for opt in options:
            desc = opt.description.lower()
            
            # "either ... or ..."
            if 'either ' in desc:
                match = re.search(r'either\s+(\w+)\s+or\s+(\w+)', desc)
                if match:
                    opt.mutually_exclusive.extend([match.group(1), match.group(2)])
            
            # "requires ..."
            if 'requires ' in desc:
                match = re.search(r'requires\s+(\w+)', desc)
                if match:
                    opt.depends_on.append(match.group(1))
            
            # "conflicts with ..."
            if 'conflicts with ' in desc:
                match = re.search(r'conflicts with\s+(\w+)', desc)
                if match:
                    opt.mutually_exclusive.append(match.group(1))
    
    def _create_parameters_from_options(self, options: List[ParsedOption]) -> List[CommandParameter]:
        """Create CommandParameter objects from parsed options."""
        
        parameters = []
        
        for opt in options:
            # Determine parameter type
            param_type = "boolean"
            if opt.type == OptionType.VALUE:
                param_type = self._map_option_type_to_param_type(opt.argument_name)
            elif opt.type == OptionType.LIST:
                param_type = "string"
            
            param = CommandParameter(
                name=opt.name,
                type=param_type,
                description=opt.description,
                required=opt.required,
                default=opt.default_value,
                choices=opt.choices,
                location="option"
            )
            
            parameters.append(param)
        
        # Sort by name
        parameters.sort(key=lambda p: p.name)
        
        return parameters
    
    def _map_option_type_to_param_type(self, arg_name: str) -> str:
        """Map argument name to parameter type."""
        
        arg_lower = arg_name.lower()
        
        if any(word in arg_lower for word in ['file', 'path', 'dir', 'directory']):
            return "file"
        elif any(word in arg_lower for word in ['num', 'int', 'count', 'port']):
            return "integer"
        elif any(word in arg_lower for word in ['size', 'float', 'double']):
            return "float"
        elif any(word in arg_lower for word in ['url', 'uri']):
            return "url"
        elif any(word in arg_lower for word in ['date', 'time']):
            return "string"
        
        return "string"
    
    def _generate_comprehensive_examples(self, command: str, options: List[ParsedOption]) -> List[str]:
        """Generate comprehensive examples using various options."""
        
        examples = []
        
        # Basic usage
        examples.append(f"{command} --help")
        
        # Common option combinations
        if options:
            # Find common options
            verbose = next((o for o in options if 'verb' in o.name.lower()), None)
            output = next((o for o in options if 'output' in o.name.lower() or o.name == 'f'), None)
            file_opt = next((o for o in options if 'file' in o.name.lower()), None)
            
            # Generate combinations
            if verbose and output:
                if output.type == OptionType.VALUE:
                    examples.append(f"{command} {verbose.short or verbose.long} {output.long}=output.txt")
                else:
                    examples.append(f"{command} {verbose.short or verbose.long} {output.long}")
            
            if file_opt and file_opt.type == OptionType.VALUE:
                examples.append(f"{command} {file_opt.long}=filename")
        
        # Add command-specific examples
        if command in self.command_signatures:
            examples.extend(self.command_signatures[command]["examples"])
        
        return examples[:10]  # Limit to 10
    
    def _generate_comprehensive_template(self, command: str, options: List[ParsedOption]) -> str:
        """Generate comprehensive template."""
        
        if not options:
            return f"{command}"
        
        # Group options by type
        required = [o for o in options if o.required]
        common = [o for o in options if not o.required and o.type != OptionType.FLAG][:5]
        
        template_parts = [command]
        
        # Add required options
        for opt in required:
            if opt.long:
                template_parts.append(f"{opt.long}=<{opt.argument_name or 'value'}>")
            elif opt.short:
                template_parts.append(f"{opt.short} <{opt.argument_name or 'value'}>")
        
        # Add common options placeholder
        if common:
            template_parts.append("[options]")
        
        # Add arguments placeholder
        template_parts.append("[args...]")
        
        return " ".join(template_parts)
    
    def _generate_patterns(self, command: str, options: List[ParsedOption]) -> List[str]:
        """Generate matching patterns."""
        
        patterns = [command]
        
        # Add patterns with common options
        for opt in options[:3]:
            if opt.long:
                patterns.append(f"{command} {opt.long}")
            elif opt.short:
                patterns.append(f"{command} {opt.short}")
        
        # Add category patterns
        category = self._detect_category(command, "")
        if category == 'container':
            patterns.extend([f"{command} *container*", f"{command} *image*"])
        elif category == 'file':
            patterns.extend([f"{command} *file*", f"{command} *directory*"])
        
        return patterns
    
    def _get_option_key(self, option: ParsedOption) -> str:
        """Get unique key for option."""
        if option.long:
            return option.long
        elif option.short:
            return option.short
        else:
            return option.name
    
    def _merge_options(self, opt1: ParsedOption, opt2: ParsedOption) -> ParsedOption:
        """Merge two options."""
        
        # Use opt1 as base, add info from opt2
        if not opt1.description and opt2.description:
            opt1.description = opt2.description
        
        if not opt1.argument_name and opt2.argument_name:
            opt1.argument_name = opt2.argument_name
        
        if opt1.type == OptionType.FLAG and opt2.type != OptionType.FLAG:
            opt1.type = opt2.type
        
        # Merge metadata
        opt1.mutually_exclusive.extend(opt2.mutually_exclusive)
        opt1.depends_on.extend(opt2.depends_on)
        
        return opt1
    
    def _create_option_from_signature(self, opt_data: Dict) -> ParsedOption:
        """Create option from signature data."""
        
        option = ParsedOption(
            name=opt_data["name"],
            type=OptionType(opt_data.get("type", "flag")),
            description=opt_data.get("description", ""),
            required=opt_data.get("required", False)
        )
        
        if "short" in opt_data:
            option.short = f"-{opt_data['short']}"
        if "long" in opt_data:
            option.long = f"--{opt_data['long']}"
        
        return option
    
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
    
    def _get_version_text(self, command: str) -> str:
        """Get version information."""
        for flag in ['--version', '-v', '-V']:
            try:
                result = subprocess.run(
                    [command, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout + result.stderr
            except:
                continue
        return ""
    
    def _extract_description(self, text: str) -> str:
        """Extract command description."""
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Usage:'):
                return line[:200]
        return ""
    
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
    
    def _clean_description(self, line: str) -> str:
        """Clean option description."""
        # Remove option part
        parts = line.split(None, 2)
        if len(parts) > 2:
            desc = parts[2]
        else:
            desc = ""
        
        # Clean up
        desc = re.sub(r'\s+', ' ', desc.strip())
        
        return desc
    
    def _load_command_signatures(self) -> Dict[str, Dict]:
        """Load known command signatures."""
        return {
            'docker': {
                'options': [
                    {
                        'name': 'detach',
                        'short': 'd',
                        'long': '--detach',
                        'type': 'flag',
                        'description': 'Run container in background'
                    },
                    {
                        'name': 'interactive',
                        'short': 'i',
                        'long': '--interactive',
                        'type': 'flag',
                        'description': 'Keep STDIN open'
                    },
                    {
                        'name': 'tty',
                        'short': 't',
                        'long': '--tty',
                        'type': 'flag',
                        'description': 'Allocate a pseudo-TTY'
                    },
                    {
                        'name': 'publish',
                        'short': 'p',
                        'long': '--publish',
                        'type': 'value',
                        'description': 'Publish a container\'s port(s)',
                        'argument_name': 'port'
                    },
                    {
                        'name': 'volume',
                        'short': 'v',
                        'long': '--volume',
                        'type': 'value',
                        'description': 'Bind mount a volume',
                        'argument_name': 'volume'
                    },
                    {
                        'name': 'env',
                        'short': 'e',
                        'long': '--env',
                        'type': 'value',
                        'description': 'Set environment variables',
                        'argument_name': 'env'
                    },
                    {
                        'name': 'rm',
                        'long': '--rm',
                        'type': 'flag',
                        'description': 'Automatically remove the container'
                    },
                    {
                        'name': 'name',
                        'long': '--name',
                        'type': 'value',
                        'description': 'Assign a name to the container',
                        'argument_name': 'name'
                    }
                ],
                'examples': [
                    'docker run -d -p 80:80 nginx',
                    'docker run -it --rm ubuntu bash',
                    'docker run -v /host:/container alpine'
                ]
            },
            'kubectl': {
                'options': [
                    {
                        'name': 'namespace',
                        'short': 'n',
                        'long': '--namespace',
                        'type': 'value',
                        'description': 'Kubernetes namespace',
                        'argument_name': 'namespace'
                    },
                    {
                        'name': 'selector',
                        'short': 'l',
                        'long': '--selector',
                        'type': 'value',
                        'description': 'Selector (label query) to filter on',
                        'argument_name': 'selector'
                    },
                    {
                        'name': 'output',
                        'short': 'o',
                        'long': '--output',
                        'type': 'value',
                        'description': 'Output format',
                        'argument_name': 'format'
                    },
                    {
                        'name': 'watch',
                        'short': 'w',
                        'long': '--watch',
                        'type': 'flag',
                        'description': 'After listing/watching the specified resource'
                    },
                    {
                        'name': 'all_namespaces',
                        'short': 'A',
                        'long': '--all-namespaces',
                        'type': 'flag',
                        'description': 'List resources from all namespaces'
                    }
                ],
                'examples': [
                    'kubectl get pods -n kube-system',
                    'kubectl get pods -l app=nginx',
                    'kubectl get pods -o yaml'
                ]
            },
            'git': {
                'options': [
                    {
                        'name': 'verbose',
                        'short': 'v',
                        'long': '--verbose',
                        'type': 'flag',
                        'description': 'Be more verbose'
                    },
                    {
                        'name': 'quiet',
                        'short': 'q',
                        'long': '--quiet',
                        'type': 'flag',
                        'description': 'Be more quiet'
                    },
                    {
                        'name': 'message',
                        'short': 'm',
                        'long': '--message',
                        'type': 'value',
                        'description': 'Commit message',
                        'argument_name': 'msg'
                    },
                    {
                        'name': 'all',
                        'short': 'a',
                        'long': '--all',
                        'type': 'flag',
                        'description': 'Include all files'
                    },
                    {
                        'name': 'force',
                        'short': 'f',
                        'long': '--force',
                        'type': 'flag',
                        'description': 'Force operation'
                    }
                ],
                'examples': [
                    'git add -A',
                    'git commit -m "Initial commit"',
                    'git push -f origin main'
                ]
            }
        }
    
    def scan_multiple_commands(self, commands: List[str]) -> Dict[str, ExtractedSchema]:
        """Scan multiple commands."""
        
        results = {}
        
        for command in commands:
            print(f"\n{'='*60}")
            print(f"Scanning: {command}")
            print('='*60)
            
            try:
                schema = self.scan_command(command)
                results[command] = schema
                
                # Show results
                if schema.commands:
                    cmd_schema = schema.commands[0]
                    print(f"✓ Description: {cmd_schema.description}")
                    print(f"✓ Category: {cmd_schema.category}")
                    print(f"✓ Options found: {len(cmd_schema.parameters)}")
                    print(f"✓ Template: {cmd_schema.template}")
                    
                    # Show first few options
                    print("\nFirst 5 options:")
                    for param in cmd_schema.parameters[:5]:
                        meta = param.metadata or {}
                        short = f" ({meta.get('short')})" if meta.get('short') else ""
                        long = meta.get('long', '')
                        print(f"  {long}{short} - {param.description[:50]}")
                
            except Exception as e:
                print(f"✗ Failed: {e}")
                results[command] = None
        
        return results


def main():
    """Demonstrate comprehensive command scanning."""
    
    print("=" * 60)
    print("COMPREHENSIVE COMMAND SCANNER")
    print("=" * 60)
    
    # Initialize scanner
    scanner = ComprehensiveCommandScanner()
    
    # Test commands
    test_commands = [
        "docker",
        "kubectl",
        "git",
        "find",
        "tar",
        "grep"
    ]
    
    # Scan all commands
    results = scanner.scan_multiple_commands(test_commands)
    
    # Save results
    print("\n" + "=" * 60)
    print("SAVING SCHEMAS")
    print("=" * 60)
    
    saved = 0
    for command, schema in results.items():
        if schema:
            # Store in registry
            scanner.registry.schemas[command] = schema
            saved += 1
    
    # Save to disk
    scanner.registry._auto_save()
    print(f"Saved {saved} comprehensive schemas to storage")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("SCAN STATISTICS")
    print("=" * 60)
    
    total_options = 0
    for command, schema in results.items():
        if schema and schema.commands:
            options = len(schema.commands[0].parameters)
            total_options += options
            print(f"{command:10}: {options:3} options")
    
    print(f"\nTotal options scanned: {total_options}")


if __name__ == "__main__":
    main()
