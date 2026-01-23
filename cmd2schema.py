#!/usr/bin/env python3
"""
cmd2schema - Command to Schema Generator

This module provides functionality to generate schemas from command-line tools.
It can analyze installed commands and create JSON schemas that nlp2cmd can use.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from datetime import datetime

try:
    from nlp2cmd.schema_extraction import ShellHelpExtractor, LLMSchemaExtractor
    from nlp2cmd.schema_extraction import CommandSchema, ExtractedSchema
except ImportError:
    print("Error: nlp2cmd not installed. Please run: pip install -e .")
    sys.exit(1)


class CommandSchemaGenerator:
    """Generate schemas for command-line tools."""
    
    def __init__(self, output_dir: str = "generated_schemas", use_llm: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_llm = use_llm
        
        # Initialize extractors
        self.shell_extractor = ShellHelpExtractor()
        
        if use_llm:
            try:
                self.llm_extractor = LLMSchemaExtractor()
            except ImportError as e:
                print(f"Warning: LLM extractor not available: {e}")
                self.use_llm = False
    
    def generate_schema(self, command: str) -> Dict[str, Any]:
        """Generate schema for a single command."""
        print(f"Generating schema for: {command}")
        
        # Check if command exists
        if not self._command_exists(command):
            print(f"Command '{command}' not found, creating placeholder schema")
            return self._create_placeholder_schema(command)
        
        # Try to extract schema
        try:
            if self.use_llm and hasattr(self, 'llm_extractor'):
                # Use LLM extractor
                extracted = self.llm_extractor.extract_from_command(command)
            else:
                # Use shell help extractor
                extracted = self.shell_extractor.extract_from_command(command)
            
            if extracted.commands:
                schema = extracted.commands[0]
                return self._schema_to_dict(schema)
            else:
                print(f"No schema extracted for {command}, using template")
                return self._create_template_schema(command)
                
        except Exception as e:
            print(f"Error extracting schema for {command}: {e}")
            return self._create_template_schema(command)
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _schema_to_dict(self, schema: CommandSchema) -> Dict[str, Any]:
        """Convert CommandSchema object to dictionary."""
        return {
            "name": schema.name,
            "description": schema.description,
            "category": schema.category,
            "template": schema.template,
            "examples": schema.examples,
            "patterns": schema.patterns,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "choices": p.choices,
                    "location": p.location
                } for p in schema.parameters
            ],
            "source_type": schema.source_type,
            "metadata": schema.metadata,
            "generated_at": datetime.now().isoformat()
        }
    
    def _create_placeholder_schema(self, command: str) -> Dict[str, Any]:
        """Create a placeholder schema for missing commands."""
        return {
            "name": command,
            "description": f"Command: {command} (not installed)",
            "category": "unknown",
            "template": f"{command} {{options}}",
            "examples": [f"{command} --help"],
            "patterns": [command],
            "parameters": [],
            "source_type": "placeholder",
            "metadata": {
                "installed": False,
                "note": "Command is not installed on this system"
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _create_template_schema(self, command: str) -> Dict[str, Any]:
        """Create a schema from predefined templates."""
        templates = {
            "docker": {
                "description": "Docker container management",
                "category": "container",
                "template": "docker {subcommand} {options}",
                "examples": [
                    "docker run -d nginx",
                    "docker ps -a",
                    "docker logs container_name",
                    "docker stop container_name",
                    "docker rmi image_name",
                    "docker build -t image_name ."
                ]
            },
            "nginx": {
                "description": "Nginx web server",
                "category": "web",
                "template": "nginx {options}",
                "examples": [
                    "nginx -v",
                    "nginx -t",
                    "nginx -s reload",
                    "nginx -s stop"
                ]
            }
        }
        
        template = templates.get(command, {
            "description": f"Command: {command}",
            "category": "system",
            "template": f"{command} {{options}}",
            "examples": [f"{command} --help"]
        })
        
        return {
            "name": command,
            "description": template["description"],
            "category": template["category"],
            "template": template["template"],
            "examples": template["examples"],
            "patterns": [command],
            "parameters": [],
            "source_type": "template",
            "metadata": {
                "installed": self._command_exists(command)
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_schemas(self, commands: List[str]) -> None:
        """Generate schemas for multiple commands."""
        results = {}
        
        for command in commands:
            schema = self.generate_schema(command)
            results[command] = schema
            
            # Save individual schema
            schema_file = self.output_dir / f"{command}.json"
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)
            print(f"Saved schema: {schema_file}")
        
        # Save combined schema file
        combined_file = self.output_dir / "all_schemas.json"
        with open(combined_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Saved combined schemas: {combined_file}")
    
    def install_command(self, command: str) -> bool:
        """Attempt to install a command (placeholder for future implementation)."""
        print(f"Installation not implemented for: {command}")
        print("Please install manually:")
        
        install_instructions = {
            "docker": "Visit https://docs.docker.com/get-docker/",
            "nginx": "sudo apt-get install nginx (Ubuntu/Debian) or sudo yum install nginx (RHEL/CentOS)",
            "kubectl": "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl && sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl"
        }
        
        print(install_instructions.get(command, f"Check package manager for {command}"))
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate schemas from command-line tools")
    parser.add_argument("commands", nargs="*", help="Commands to generate schemas for")
    parser.add_argument("--output", "-o", default="generated_schemas", help="Output directory")
    parser.add_argument("--llm", action="store_true", help="Use LLM for schema generation")
    parser.add_argument("--install", help="Attempt to install the specified command")
    parser.add_argument("--list", action="store_true", help="List available schemas")
    
    args = parser.parse_args()
    
    generator = CommandSchemaGenerator(output_dir=args.output, use_llm=args.llm)
    
    if args.install:
        generator.install_command(args.install)
        return
    
    if args.list:
        schema_dir = Path(args.output)
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.json"):
                if schema_file.name != "all_schemas.json":
                    print(f"- {schema_file.stem}")
        else:
            print("No schemas directory found")
        return
    
    # Default commands if none provided
    if not args.commands:
        args.commands = ["docker", "nginx", "kubectl", "git", "curl"]
    
    generator.generate_schemas(args.commands)


if __name__ == "__main__":
    main()
