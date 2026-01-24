# NLP2CMD Schema Systems

## 📚 Related Documentation

- **[Documentation Hub](README.md)** - Entry point for all docs
- **[Schema Usage Guide](SCHEMA_USAGE_GUIDE.md)** - Practical usage and flows
- **[Schema Complete Guide](SCHEMA_COMPLETE_GUIDE.md)** - Deep dive
- **[Versioned Schemas](VERSIONED_SCHEMAS.md)** - Versioning and evolution

## Table of Contents

1. [Schema-Based Generation](#schema-based-generation)
2. [Versioned Schemas](#versioned-schemas)
3. [Intelligent Generation](#intelligent-generation)
4. [Storage Systems](#storage-systems)
5. [API Reference](#api-reference)

## Schema-Based Generation

### Overview
The schema-based generation system uses dynamically extracted command schemas to generate accurate shell commands.

### Components

#### SchemaDrivenGenerator
```python
from nlp2cmd.schema_based.generator import SchemaBasedGenerator

generator = SchemaDrivenGenerator()
generator.learn_from_schema(schema)
command = generator.generate_command("find", {"pattern": "*.py"})
```

#### SchemaDrivenAdapter
```python
from nlp2cmd.schema_based.adapter import SchemaDrivenAppSpecAdapter

adapter = SchemaDrivenAppSpecAdapter(schema_registry=registry)
nlp = NLP2CMD(adapter=adapter)
result = nlp.transform("list containers")
```

## Versioned Schemas

### Per-Command Storage
Each command schema is stored in its own JSON file:

```json
{
  "command": "docker",
  "version": "2.0.0",
  "description": "Docker container management",
  "template": "docker {subcommand} {options}",
  "parameters": [...],
  "examples": [...]
}
```

### Version Management
```python
from nlp2cmd.storage.versioned_store import VersionedSchemaStore

store = VersionedSchemaStore("./schemas")
store.store_schema_version(schema, "2.1.0", make_active=True)
versions = store.list_versions("docker")
```

## Intelligent Generation

### Version-Aware Generation
The system detects command versions and adapts syntax:

```python
from nlp2cmd.intelligent.version_aware_generator import VersionAwareCommandGenerator

generator = VersionAwareCommandGenerator(schema_store)
command, metadata = generator.generate_command("list containers")
# Automatically detects Docker version and uses appropriate schema
```

### Command Detection
```python
from nlp2cmd.intelligent.command_detector import CommandDetector

detector = CommandDetector()
command = detector.detect_command("show all running containers")
# Returns: "docker"
```

## Storage Systems

### PerCommandSchemaStore
- Individual JSON files for each command
- Automatic indexing
- Category organization
- Backup and restore support

### VersionedSchemaStore
- Version tracking
- Schema comparison
- Migration support
- Rollback capability

## API Reference

### DynamicSchemaRegistry
```python
registry = DynamicSchemaRegistry(
    use_per_command_storage=True,
    storage_dir="./schemas",
    use_llm=True,
    llm_config={...}
)

# Register schemas
schema = registry.register_shell_help("docker")
schema = registry.register_appspec("appspec.yaml")
schemas = registry.register_dynamic_export("export.json")

# Get schemas
schema = registry.get_command_by_name("docker")
matches = registry.find_matching_commands("list containers")
```

### Schema Classes
```python
@dataclass
class CommandSchema:
    name: str
    description: str
    category: str
    parameters: List[CommandParameter]
    examples: List[str]
    patterns: List[str]
    source_type: str
    metadata: Dict[str, Any]
    template: Optional[str]

@dataclass
class ExtractedSchema:
    source: str
    source_type: str
    commands: List[CommandSchema]
    metadata: Dict[str, Any]
```

## Examples

### Basic Usage
```python
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter

# Initialize with dynamic adapter
adapter = DynamicAdapter()
nlp = NLP2CMD(adapter=adapter)

# Transform query
result = nlp.transform("find all python files")
print(result.command)  # find . -name "*.py"
```

### Advanced Usage
```python
from nlp2cmd.intelligent import IntelligentNLP2CMD

# Initialize with version-aware generation
nlp = IntelligentNLP2CMD(storage_dir="./schemas")

# Transform with version detection
ir = nlp.transform("list containers", detect_version=True)
print(f"Command: {ir.dsl}")
print(f"Version detected: {ir.metadata.get('detected_version')}")
```

## Best Practices

1. **Use Persistent Storage**
   ```python
   registry = DynamicSchemaRegistry(use_per_command_storage=True)
   ```

2. **Enable Version Detection**
   ```python
   nlp = IntelligentNLP2CMD()
   result = nlp.transform(query, detect_version=True)
   ```

3. **Learn from Feedback**
   ```python
   nlp.learn_from_feedback(query, generated, corrected)
   ```

4. **Cache Results**
   ```python
   registry.save_cache("schemas.json")
   registry.load_cache("schemas.json")
   ```

## Migration Guide

### From v0.1 to v0.2
1. Replace hardcoded templates with schema-driven generation
2. Enable persistent storage
3. Use version-aware generation for compatibility
4. Update adapter initialization

## Troubleshooting

### Common Issues

1. **Schema Not Found**
   - Check if command is registered
   - Verify storage directory permissions
   - Run schema generation

2. **Version Detection Fails**
   - Ensure command is installed
   - Check version command output
   - Verify pattern matching

3. **Storage Issues**
   - Check directory permissions
   - Verify disk space
   - Check file encoding
