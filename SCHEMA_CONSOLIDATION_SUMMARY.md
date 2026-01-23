# Schema Directory Consolidation Summary

## Changes Made

All schema storage has been consolidated to use only the `command_schemas/` directory.

### Files Updated

1. **test_nlp2cmd_enhanced.sh**
   - Changed `SCHEMA_DIR` from `generated_schemas` to `command_schemas`

2. **run_all_tests.sh**
   - Updated schema generation paths to use `command_schemas/docker.appspec.json` and `command_schemas/nginx.appspec.json`

3. **TEST_SCRIPTS_README.md**
   - Updated documentation to reference `command_schemas/` directory
   - Updated features list to mention "Schema management in `command_schemas/`"

4. **intelligent_schema_generator.py**
   - Changed export file from `generated_schemas.json` to `command_schemas.json`

5. **cmd2schema.py** (deprecated but updated for consistency)
   - Changed default output directory from `generated_schemas` to `command_schemas`

6. **src/app2schema/extract.py**
   - Fixed indentation error (missing class name for `App2SchemaResult`)

### Directories Cleaned Up

- Removed `generated_schemas/` directory
- Moved existing schemas from `generated_schemas/` to `command_schemas/`

### Current Directory Structure

```text
command_schemas/
├── categories/      # Schema categories
├── commands/        # Individual command schemas
├── docker.appspec.json
├── docker.json
├── index.json
└── nginx.json
```

### Usage Examples

```bash
# Generate schema to command_schemas
python -m app2schema docker --type shell -o command_schemas/docker.appspec.json

# Run tests (schemas saved to command_schemas/)
./test_nlp2cmd_enhanced.sh

# All schemas now in one place
ls command_schemas/
```

## Benefits

1. **Single Source of Truth**: All schemas are now stored in one consistent location
2. **Cleaner Repository**: Removed duplicate schema directories
3. **Better Organization**: `command_schemas/` is the standard location used throughout the codebase
4. **Consistency**: All tools and scripts now use the same directory
