# NLP2CMD Command Testing Scripts

This directory contains scripts to test Docker commands through nlp2cmd with automatic schema generation.

## Scripts Overview

### 1. `test_nlp2cmd_commands.sh`

Basic script to test Docker commands through nlp2cmd.

**Features:**

- Checks if nlp2cmd is installed
- Tests 6 predefined Docker commands
- Uses both `docker` and `auto` DSL modes
- Shows command outputs and explanations

**Usage:**

```bash
./test_nlp2cmd_commands.sh [--help] [--verbose]
```

### 2. `test_nlp2cmd_enhanced.sh`

Enhanced version with schema generation and logging.

**Features:**

- Automatic command detection and schema generation (app2schema)
- Comprehensive logging to `nlp2cmd_test.log`
- Interactive command execution
- Schema management in `command_schemas/`
- Support for dry-run mode

**Usage:**

```bash
./test_nlp2cmd_enhanced.sh [options]

Options:
  --help, -h     Show help message
  --verbose      Enable verbose output
  --dry-run      Only check commands without executing
  --schemas      Show only generated schemas
```

### 3. **app2schema** (Python module)

Python module for generating command schemas.

**Features:**

- Analyzes installed commands
- Generates appspec JSON schemas for nlp2cmd
- Supports multiple source types (shell, Python, OpenAPI, etc.)
- Handles missing commands with placeholder schemas

**Usage:**

```bash
# Generate schema for a specific command
python -m app2schema docker --type shell -o docker.appspec.json

# Generate with auto-detection
python -m app2schema nginx -o nginx.appspec.json

# Generate from other sources
python -m app2schema myapi.yml --type openapi -o api.appspec.json
python -m app2schema myscript.py --type python -o script.appspec.json
```

## Test Commands

The scripts test the following Docker commands:

1. "Run nginx on port 8080"
2. "List all running containers"
3. "Show logs for web container"
4. "Stop all containers"
5. "Remove unused images"
6. "Build image from current directory tagged as myapp"

## How It Works

### Command Detection

The scripts automatically detect if required commands (docker, nginx) are installed. If not, they:

1. Generate a placeholder schema
2. Provide installation instructions
3. Allow continuing without the command

### Schema Generation (app2schema)

When a command is not found, the system:

1. Uses `python -m app2schema` to generate a schema
2. Creates an appspec JSON file for the command
3. Saves the schema in `command_schemas/` directory
4. Uses the schema to help nlp2cmd understand the command

### Example Generated Schema (appspec format)

```json
{
  "format": "app2schema.appspec",
  "version": 1,
  "app": {
    "name": "docker",
    "kind": "shell",
    "source": "generated",
    "metadata": {}
  },
  "actions": [
    {
      "id": "shell.docker",
      "type": "shell",
      "description": "Docker container management",
      "dsl": {
        "kind": "shell",
        "output_format": "raw"
      },
      "params": {},
      "schema": {
        "command": "docker"
      },
      "match": {
        "patterns": ["docker"],
        "examples": ["docker run -d nginx", "docker ps -a"]
      },
      "executor": {
        "kind": "shell",
        "config": {}
      },
      "metadata": {
        "installed": true
      },
      "tags": []
    }
  ],
  "metadata": {}
}
```

## Installation Requirements

1. **nlp2cmd**: Automatically installed from source if not present
2. **Python 3.8+**: Required for the scripts
3. **Docker**: Optional but recommended for full testing
4. **nginx**: Optional for nginx-specific tests

## Output

### Enhanced Script Output

The enhanced script provides:

- Colored console output
- Detailed log file (`nlp2cmd_test.log`)
- Generated command execution prompts
- Success/failure statistics
- Schema visualization

### Log File Format

```text
nlp2cmd Test Log - 2024-01-23 10:30:00
=========================
[INFO] Checking nlp2cmd Installation
[SUCCESS] nlp2cmd is installed
...
```

## Troubleshooting

### Command Not Found

If a command is not found:

1. The script generates a placeholder schema
2. Installation instructions are provided
3. Tests continue with limited functionality

### Permission Errors

Make scripts executable:

```bash
chmod +x test_nlp2cmd_commands.sh
chmod +x test_nlp2cmd_enhanced.sh
chmod +x cmd2schema.py
```

### nlp2cmd Installation Issues

If nlp2cmd is not found:

1. Ensure you're in the nlp2cmd repository directory
2. Run: `pip install -e .`
3. Check your Python path

## Advanced Usage

### Custom Commands

To test custom commands, modify the `COMMANDS` array in the scripts:

```bash
COMMANDS=(
    "My custom command"
    "Another test case"
)
```

### Custom Schema Generation

To generate schemas for custom commands:

```bash
# Generate schema for a shell command
python -m app2schema mycommand --type shell -o mycommand.appspec.json

# Generate from Python script
python -m app2schema myscript.py --type python -o myscript.appspec.json

# Generate from OpenAPI spec
python -m app2schema api.yaml --type openapi -o api.appspec.json
```

### Integration with nlp2cmd

The generated appspec schemas can be used with nlp2cmd:

```bash
nlp2cmd --query "run nginx on port 8080" --dsl appspec --appspec docker.appspec.json
```

## How Generated Schemas Help nlp2cmd

The generated schemas can be used by nlp2cmd to:

1. Better understand command structures
2. Provide more accurate command generation
3. Handle missing commands gracefully
4. Offer contextual help and examples

## Future Enhancements

Planned improvements:

1. Automatic command installation (with user permission)
2. Schema validation and testing
3. Integration with package managers
4. Cloud-based schema sharing
5. Real-time command learning
