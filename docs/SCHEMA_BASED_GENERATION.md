# Schema-Based Command Generation

This document describes the schema-based command generation system that replaces hardcoded templates with dynamic learning from schemas.

## Overview

The new system:
- Uses schemas instead of hardcoded templates
- Learns from existing command examples
- Improves through user feedback
- Generates commands based on learned patterns

## Components

### 1. SchemaBasedGenerator

Located in `src/nlp2cmd/schema_based/generator.py`

Main features:
- Extracts patterns from existing schemas
- Generates commands based on learned patterns
- Improves through usage feedback

```python
from nlp2cmd.schema_based import SchemaBasedGenerator

generator = SchemaBasedGenerator(llm_config)
command = generator.generate_command('find', {'path': '/home', 'pattern': '*.py'})
```

### 2. SchemaRegistry

Located in `src/nlp2cmd/schema_based/generator.py`

Manages schema collection and learning:
- Loads schemas from JSON files
- Registers new schemas
- Saves improvements

```python
from nlp2cmd.schema_based import SchemaRegistry

registry = SchemaRegistry()
registry.load_from_file('schemas.json')
registry.register_schema(new_schema)
registry.save_improvements('improved.json')
```

### 3. SchemaDrivenAppSpecAdapter

Located in `src/nlp2cmd/schema_based/adapter.py`

Enhanced AppSpec adapter with schema-based generation:
- Integrates with AppSpec format
- Uses schema registry for generation
- Learns from feedback

```python
from nlp2cmd.schema_based import SchemaDrivenAppSpecAdapter

adapter = SchemaDrivenAppSpecAdapter(
    appspec_path='appspec.json',
    llm_config=llm_config
)
```

## Migration from Templates

### Old System (Templates)

```python
# Hardcoded templates
templates = {
    'find': 'find {path} -name "{pattern}"',
    'grep': 'grep {pattern} {file}',
    # ...
}
```

### New System (Schemas)

```python
# Learn from schemas
schema = ExtractedSchema(
    source='find',
    commands=[CommandSchema(
        name='find',
        examples=['find . -name "*.py"', 'find /home -type f'],
        # ...
    )]
)
registry.register_schema(schema)
```

## Learning Process

1. **Initial Learning**: Load existing schemas
2. **Pattern Extraction**: Extract patterns from examples
3. **Generation**: Use patterns to generate commands
4. **Feedback Loop**: Learn from user corrections

## Example Usage

```python
# Initialize system
from nlp2cmd.schema_based import SchemaRegistry

registry = SchemaRegistry(llm_config)

# Load existing schemas
registry.load_from_file('validated_schemas.json')

# Generate command
command = registry.generate_command('find', {
    'path': '/home/user',
    'pattern': '*.py'
})

# Learn from feedback
registry.improve_from_feedback(
    'find Python files',
    'find /path',
    'find . -name "*.py"'
)

# Save improvements
registry.save_improvements('improved_schemas.json')
```

## Benefits

1. **No Hardcoding**: No need to predefine templates
2. **Adaptive**: Learns from actual usage
3. **Extensible**: Can learn new commands
4. **Context-Aware**: Considers context in generation
5. **Improving**: Gets better over time

## Integration with NLP2CMD

The schema-based system integrates seamlessly with NLP2CMD:

```python
from nlp2cmd import NLP2CMD
from nlp2cmd.schema_based import SchemaDrivenAppSpecAdapter

adapter = SchemaDrivenAppSpecAdapter(
    appspec_path='shell_tools.json',
    llm_config=llm_config
)

nlp = NLP2CMD(adapter=adapter)
result = nlp.transform_ir('Find Python files')
```

## File Structure

```
src/nlp2cmd/schema_based/
├── __init__.py          # Module exports
├── generator.py         # SchemaBasedGenerator and SchemaRegistry
└── adapter.py          # SchemaDrivenAppSpecAdapter
```

## Configuration

```python
llm_config = {
    "model": "ollama/qwen2.5-coder:7b",
    "api_base": "http://localhost:11434",
    "temperature": 0.1,
    "max_tokens": 512,
    "timeout": 10,
}
```

## Best Practices

1. **Start with good schemas**: Provide quality initial schemas
2. **Collect feedback**: Enable user feedback for improvement
3. **Save improvements**: Persist learned improvements
4. **Validate generations**: Check generated commands
5. **Monitor quality**: Track generation success rate

## Future Enhancements

1. **ML-based pattern extraction**: Use ML for better pattern recognition
2. **Context prediction**: Predict context from natural language
3. **Multi-step commands**: Support for command sequences
4. **Parameter validation**: Validate generated parameters
5. **Performance optimization**: Cache frequently used patterns
