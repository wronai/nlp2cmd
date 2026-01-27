# App2Schema Example

This example demonstrates how to convert shell commands to AppSpec format and use them with NLP2CMD.

## Overview

The app2schema integration allows you to:
- Extract AppSpec definitions from shell commands
- Use the generated schema with NLP2CMD for command transformation
- Create dynamic schema-based command processors

## Running the Example

```bash
python example.py
```

This will:
1. Generate an AppSpec from a "git" command
2. Create an AppSpecAdapter from the generated schema
3. Transform a natural language command using the schema

## What You'll Learn

- How to use the app2schema library
- Creating AppSpecAdapters
- Integrating schema-based transformations with NLP2CMD
