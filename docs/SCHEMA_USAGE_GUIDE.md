# How to Use Schemas in NLP2CMD - Complete Guide

## Overview

This guide explains how schemas are extracted from commands and used to generate commands based on user prompts.

## 1. Where Schemas are Defined and Used

### Core Files

#### Schema Extraction
```python
# src/nlp2cmd/schema_extraction/__init__.py
class DynamicSchemaRegistry:
    """Main registry for managing command schemas"""
    
    def register_shell_help(self, command: str) -> ExtractedSchema
    def register_appspec(self, appspec_path: str) -> ExtractedSchema
    def register_dynamic_export(self, file_path: str) -> List[ExtractedSchema]
```

#### Schema Storage
```python
# src/nlp2cmd/storage/per_command_store.py
class PerCommandSchemaStore:
    """Stores each command schema in individual JSON files"""
    
    def store_schema(self, schema: ExtractedSchema) -> bool
    def load_schema(self, command: str) -> Optional[ExtractedSchema]
    def list_commands(self) -> List[str]
```

#### Schema-Based Generation
```python
# src/nlp2cmd/schema_based/generator.py
class SchemaBasedGenerator:
    """Generates commands using learned schemas"""
    
    def learn_from_schema(self, schema: ExtractedSchema)
    def generate_command(self, command: str, context: Dict) -> str
```

## 2. Schema Extraction Process

### Step 1: Extract Schema from Command
```python
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

# Initialize registry
registry = DynamicSchemaRegistry(
    use_per_command_storage=True,
    storage_dir="./command_schemas"
)

# Extract schema from command help
schema = registry.register_shell_help("docker")
print(f"Extracted schema for {schema.commands[0].name}")
print(f"Template: {schema.commands[0].template}")
```

### Step 2: Schema Structure
```json
{
  "command": "docker",
  "version": "1.0",
  "description": "Docker container management",
  "category": "container",
  "parameters": [
    {
      "name": "subcommand",
      "type": "string",
      "description": "Docker subcommand",
      "required": true,
      "choices": ["ps", "run", "stop", "rm"]
    }
  ],
  "examples": [
    "docker ps",
    "docker run nginx",
    "docker stop container_id"
  ],
  "template": "docker {subcommand} {options}"
}
```

### Step 3: Storage
```bash
command_schemas/
├── commands/
│   ├── docker.json      # Individual command schema
│   ├── kubectl.json
│   └── git.json
├── categories/
│   ├── container.json   # Category index
│   └── version_control.json
└── index.json          # Master index
```

## 3. Using Schemas for Command Generation

### Method 1: SchemaDrivenAdapter
```python
from nlp2cmd.schema_based.adapter import SchemaDrivenAppSpecAdapter
from nlp2cmd import NLP2CMD

# Initialize with schema-driven adapter
adapter = SchemaDrivenAppSpecAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)

# Transform user prompt
result = nlp.transform("list all running containers")
print(result.command)  # Output: docker ps
```

### Method 2: Direct Schema Generation
```python
from nlp2cmd.schema_based.generator import SchemaBasedGenerator

# Load schema
schema = registry.get_command_by_name("docker")

# Create generator
generator = SchemaBasedGenerator()
generator.learn_from_schema(schema)

# Generate command
context = {"action": "list", "resource": "containers"}
command = generator.generate_command("docker", context)
print(command)  # Output: docker ps
```

### Method 3: Intelligent Version-Aware Generation
```python
from nlp2cmd.intelligent.version_aware_generator import VersionAwareCommandGenerator

# Initialize with version detection
generator = VersionAwareCommandGenerator(schema_store=registry)

# Generate with automatic version detection
command, metadata = generator.generate_command("list containers")
print(f"Command: {command}")
print(f"Detected version: {metadata['detected_version']}")
print(f"Schema used: v{metadata['schema_version']}")
```

## 4. Complete Example: From Prompt to Command

### Step 1: User Prompt
```python
user_prompt = "show all running docker containers"
```

### Step 2: Command Detection
```python
from nlp2cmd.intelligent.command_detector import CommandDetector

detector = CommandDetector()
detected_command = detector.detect_command(user_prompt)
# Returns: "docker"
```

### Step 3: Schema Loading
```python
schema = registry.get_command_by_name(detected_command)
# Loads: ./command_schemas/commands/docker.json
```

### Step 4: Context Extraction
```python
context = {
    "action": "show",
    "state": "running",
    "resource": "containers"
}
```

### Step 5: Command Generation
```python
generator = SchemaBasedGenerator()
generator.learn_from_schema(schema)
command = generator.generate_command(detected_command, context)
# Returns: "docker ps"
```

## 5. Running Examples

### Example 1: Docker Operations
```python
# examples/docker/basic_docker.py
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter

# Initialize
adapter = DynamicAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)

# Test queries
queries = [
    "list containers",
    "run nginx on port 80",
    "stop all containers",
    "show container logs"
]

for query in queries:
    result = nlp.transform(query)
    print(f"Query: {query}")
    print(f"Command: {result.command}")
    print()
```

### Example 2: Kubernetes Operations
```python
# examples/kubernetes/basic_kubernetes.py
from nlp2cmd.schema_based.adapter import SchemaDrivenAppSpecAdapter

adapter = SchemaDrivenAppSpecAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)

# Kubernetes queries
queries = [
    "list all pods",
    "get services",
    "scale deployment to 3 replicas",
    "check pod logs"
]

for query in queries:
    result = nlp.transform(query)
    print(f"{query} -> {result.command}")
```

### Example 3: File Operations
```python
# examples/shell/basic_shell.py
from nlp2cmd.intelligent import IntelligentNLP2CMD

# Initialize with intelligent generation
nlp = IntelligentNLP2CMD(storage_dir="./command_schemas")

# File operations
result = nlp.transform("find all python files")
# Output: find . -name "*.py"

result = nlp.transform("compress logs directory")
# Output: tar -czf logs.tar.gz logs/
```

## 6. Schema Management

### Generate Schemas for Commands
```bash
# Generate schemas for all commands in cmd.csv
python3 update_schemas.py --force

# Generate schemas from prompts
python3 generate_cmd_simple.py
```

### View Stored Schemas
```python
# List all stored commands
commands = registry.list_all_commands()
print(f"Available commands: {commands}")

# Get specific schema
schema = registry.get_command_by_name("docker")
print(f"Docker schema: {schema.commands[0].template}")
```

### Update Schema
```python
# Force update schema
schema = registry.register_shell_help("docker", force_update=True)

# Save to persistent storage
registry._auto_save()
```

## 7. Key Locations

### Source Code
- `src/nlp2cmd/schema_extraction/` - Schema extraction logic
- `src/nlp2cmd/schema_based/` - Schema-based generation
- `src/nlp2cmd/storage/` - Persistent storage
- `src/nlp2cmd/intelligent/` - Intelligent generation

### Examples
- `examples/docker/basic_docker.py` - Docker examples
- `examples/kubernetes/basic_kubernetes.py` - Kubernetes examples
- `examples/shell/basic_shell.py` - Shell command examples

### Storage
- `command_schemas/commands/` - Individual command schemas
- `command_schemas/index.json` - Master index

### Documentation
- `docs/SCHEMA_SYSTEMS.md` - Complete system documentation
- `docs/VERSIONED_SCHEMAS.md` - Version management guide

## 8. Quick Start Script

```python
#!/usr/bin/env python3
"""Quick start example for NLP2CMD schemas"""

from nlp2cmd import NLP2CMD
from nlp2cmd.schema_extraction import DynamicSchemaRegistry
from nlp2cmd.adapters.dynamic import DynamicAdapter

def main():
    # Initialize registry with storage
    registry = DynamicSchemaRegistry(
        use_per_command_storage=True,
        storage_dir="./command_schemas"
    )
    
    # Ensure schemas are loaded
    if not registry.schemas:
        print("No schemas found. Generating...")
        # Generate schemas for common commands
        commands = ["docker", "kubectl", "git", "find", "grep"]
        for cmd in commands:
            registry.register_shell_help(cmd)
    
    # Initialize NLP2CMD
    adapter = DynamicAdapter(schema_registry=registry)
    nlp = NLP2CMD(adapter=adapter)
    
    # Test queries
    test_queries = [
        "list docker containers",
        "show git status",
        "find python files",
        "grep for pattern in file"
    ]
    
    print("NLP2CMD Schema-Based Generation:")
    print("=" * 50)
    
    for query in test_queries:
        try:
            result = nlp.transform(query)
            print(f"Query: {query}")
            print(f"Command: {result.command}")
            print()
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"Total schemas loaded: {len(registry.schemas)}")

if __name__ == "__main__":
    main()
```

## 9. Troubleshooting

### Schema Not Found
```python
# Check if schema exists
if command not in registry.schemas:
    # Generate it
    registry.register_shell_help(command)
```

### Command Generation Fails
```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Check schema structure
schema = registry.get_command_by_name(command)
print(f"Schema template: {schema.commands[0].template}")
```

### Storage Issues
```python
# Check storage directory
import os
if not os.path.exists("./command_schemas"):
    os.makedirs("./command_schemas")
```
