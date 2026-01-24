# NLP2CMD Schema System - Complete Guide

## 📚 Related Documentation

- **[Documentation Hub](README.md)** - Entry point for all docs
- **[Schema Systems](SCHEMA_SYSTEMS.md)** - Overview of schema subsystems
- **[Schema Usage Guide](SCHEMA_USAGE_GUIDE.md)** - Practical usage and flows
- **[Versioned Schemas](VERSIONED_SCHEMAS.md)** - Versioning and evolution

## Where Schemas are Used

### 1. **Schema Extraction Location**

```python
# Main file: src/nlp2cmd/schema_extraction/__init__.py
class DynamicSchemaRegistry:
    """Manages all command schemas"""
    
    def register_shell_help(self, command: str) -> ExtractedSchema
    def get_command_by_name(self, command: str) -> CommandSchema
    def find_matching_commands(self, query: str) -> List[CommandMatch]
```

### 2. **Schema Storage Location**

```text
command_schemas/
├── commands/           # Individual command schemas
│   ├── docker.json    # Docker command schema
│   ├── kubectl.json   # Kubernetes schema
│   ├── git.json       # Git command schema
│   └── ...            # 45 total schemas
├── categories/        # Category indexes
└── index.json        # Master index of all commands
```

### 3. **Schema Usage in Generation**

```python
# src/nlp2cmd/adapters/dynamic.py
class DynamicAdapter:
    """Uses schemas to generate commands"""
    
    def __init__(self, schema_registry: DynamicSchemaRegistry):
        self.registry = schema_registry
    
    # When user provides prompt:
    # 1. Find matching commands using schemas
    # 2. Select best match
    # 3. Generate command using schema template
```

## Complete Flow Example

### Step 1: Extract Schema from Command

```bash
# Command: docker --version
# Output: Docker version 29.1.5, build 0e6fee6
```

### Step 2: Parse and Create Schema

```jsonc
# Resulting schema in command_schemas/commands/docker.json:
{
  "command": "docker",
  "version": "1.0",
  "description": "A self-sufficient runtime for containers",
  "category": "shell",
  "template": "docker {subcommand} {options}",
  "parameters": [
    {
      "name": "subcommand",
      "type": "string",
      "required": true,
      "choices": ["ps", "run", "stop", "rm"]
    }
  ],
  "examples": ["docker ps", "docker run nginx"],
  "patterns": ["docker"]
}
```

### Step 3: Store Persistently

```python
# Saved to: ./command_schemas/commands/docker.json
# Indexed in: ./command_schemas/index.json
```

### Step 4: Load When Needed

```python
registry = DynamicSchemaRegistry(storage_dir="./command_schemas")
schema = registry.get_command_by_name("docker")
# Returns: CommandSchema object with all details
```

### Step 5: Generate Command from User Prompt

```python
# User prompt: "list all containers"
# 1. Detect command: "docker" (matches patterns)
# 2. Load schema: docker.json
# 3. Extract context: "list" -> "ps", "containers" -> default
# 4. Apply template: docker {subcommand} {options}
# 5. Result: "docker ps -a"
```

## Running Examples

### 1. Basic Docker Example

```python
# examples/docker/basic_docker.py
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

# Initialize with schemas
registry = DynamicSchemaRegistry(storage_dir="./command_schemas")
adapter = DynamicAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)

# Generate commands
queries = [
    "list containers",
    "run nginx on port 80",
    "stop all containers"
]

for query in queries:
    result = nlp.transform(query)
    print(f"{query} -> {result.command}")
```

### 2. Version-Aware Example

```python
# demos/demo_version_detection.py
from nlp2cmd.intelligent.version_aware_generator import VersionAwareCommandGenerator

generator = VersionAwareCommandGenerator()

# Automatically detects version and adapts
command, metadata = generator.generate_command("list containers")
print(f"Command: {command}")
print(f"Docker version detected: {metadata['detected_version']}")
print(f"Schema version used: {metadata['schema_version']}")
```

## Key API Methods

### Schema Registry

```python
registry = DynamicSchemaRegistry()

# Extract new schema
schema = registry.register_shell_help("new_command")

# Get existing schema
schema = registry.get_command_by_name("docker")

# Find matching commands
matches = registry.find_matching_commands("list containers")

# List all commands
commands = registry.list_all_commands()
```

### Command Generation

```python
# Using DynamicAdapter
adapter = DynamicAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)
result = nlp.transform("user prompt")

# Using Version-Aware Generator
generator = VersionAwareCommandGenerator()
command, metadata = generator.generate_command("user prompt")
```

## Managing Schemas

### Update All Schemas

```bash
python3 tools/schema/update_schemas.py --force
```

### Generate Schema for Specific Command

```python
registry.register_shell_help("kubectl", force_update=True)
```

### Export/Import Schemas

```python
# Export all schemas
registry.save_cache("all_schemas.json")

# Load schemas
registry.load_cache("all_schemas.json")
```

## File Locations Summary

| Purpose | Location |
| --------- | ---------- |
| Schema extraction code | `./src/nlp2cmd/schema_extraction/` |
| Schema storage | `./command_schemas/` |
| Individual schemas | `./command_schemas/commands/*.json` |
| Dynamic adapter | `./src/nlp2cmd/adapters/dynamic.py` |
| Version-aware generator | `./src/nlp2cmd/intelligent/version_aware_generator.py` |
| Schema-based generator | `./src/nlp2cmd/schema_based/generator.py` |
| Documentation | `./docs/SCHEMA_SYSTEMS.md` |

## Quick Start Commands

```bash
# 1. Generate schemas for common commands
python3 tools/schema/update_schemas.py --force

# 2. Generate commands from prompts
python3 tools/generation/generate_cmd_simple.py

# 3. Run schema flow demonstration
python3 demos/schema_flow_demo.py

# 4. Run version detection demo
python3 demos/demo_version_detection.py

# 5. Test with specific command
python3 -c "
from nlp2cmd.schema_extraction import DynamicSchemaRegistry
r = DynamicSchemaRegistry()
s = r.register_shell_help('docker')
print(s.commands[0].template)
"
```

## Troubleshooting

### Schema Not Found

```python
# Check if schema exists
if command not in registry.schemas:
    # Generate it
    registry.register_shell_help(command)
```

### Command Generation Fails

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check schema template
schema = registry.get_command_by_name("docker")
print(f"Template: {schema.template}")
```

### Update Schemas

```bash
# Force regenerate all schemas
python3 tools/schema/update_schemas.py --force

# Check storage
ls -la command_schemas/commands/
```

This complete guide shows how schemas are extracted, stored, and used to generate commands from user prompts in NLP2CMD.
