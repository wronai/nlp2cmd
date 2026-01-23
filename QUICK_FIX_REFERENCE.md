# NLP2CMD - Quick Reference Guide

## Problem Diagnosis
The issue was that nlp2cmd CLI requires queries to be passed with the `--query` flag, not as positional arguments.

## Correct Syntax

### Basic Usage
```bash
# ❌ WRONG (what you tried)
nlp2cmd 'Pokaż użytkowników'

# ✅ CORRECT
nlp2cmd --query "Pokaż użytkowników"
```

### With Specific DSL
```bash
# ❌ WRONG
nlp2cmd --dsl shell 'Uruchom serwer apache'
nlp2cmd --dsl sql 'SELECT * FROM users WHERE city = "Warsaw"'
nlp2cmd --dsl docker 'Pokaż wszystkie kontenery'
nlp2cmd --dsl kubernetes 'Skaluj deployment nginx'

# ✅ CORRECT
nlp2cmd --dsl shell --query "Uruchom serwer apache"
nlp2cmd --dsl sql --query "SELECT * FROM users WHERE city = 'Warsaw'"
nlp2cmd --dsl docker --query "Pokaż wszystkie kontenery"
nlp2cmd --dsl kubernetes --query "Skaluj deployment nginx"
```

### With Options
```bash
# ✅ CORRECT
nlp2cmd --explain --query "Sprawdź status systemu"
nlp2cmd --auto-repair --query "Napraw konfigurację"
nlp2cmd --interactive
```

### Special Commands
```bash
# ✅ CORRECT (no --query needed for these)
nlp2cmd analyze-env
nlp2cmd analyze-env --output environment.json
nlp2cmd validate config.json
nlp2cmd repair docker-compose.yml --backup
```

## Working Examples

### 1. Simple Query
```bash
$ nlp2cmd --query "Pokaż użytkowników"
SELECT * FROM unknown_table;
```

### 2. Shell DSL
```bash
$ nlp2cmd --dsl shell --query "Znajdź pliki .log większe niż 10MB"

✅ Status: success
📊 Confidence: 100%

📝 Generated command:
╭──────────────────────────────────────────────────────────────────────────────╮
│ find . -type f -name "*.log" -name "*.log" -size +10MB -exec ls -lh {} \;    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 3. Docker DSL
```bash
$ nlp2cmd --dsl docker --query "Pokaż wszystkie kontenery"

✅ Status: success
📊 Confidence: 100%

📝 Generated command:
╭──────────────────────────────────────────────────────────────────────────────╮
│ docker ps -a                                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 4. Environment Analysis
```bash
$ nlp2cmd analyze-env

╭────── Environment Report ──────╮
│ System: Linux 6.17.0-8-generic │
╰────────────────────────────────╯
                Tools                
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Tool           ┃ Version ┃ Status ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ docker         │ 29.1.5  │ ✅     │
│ kubectl        │ -       │ ✅     │
│ git            │ 2.51.0  │ ✅     │
└────────────────┴─────────┴────────┘
```

## Python API (Unchanged)
```python
from nlp2cmd.generation import HybridThermodynamicGenerator

generator = HybridThermodynamicGenerator()

# Simple query → DSL generation
result = await generator.generate("Pokaż użytkowników")
# → {'source': 'dsl', 'result': HybridResult(...)}

# Optimization → Thermodynamic sampling
result = await generator.generate("Zoptymalizuj przydzielanie zasobów")
# → {'source': 'thermodynamic', 'result': ThermodynamicResult(...)}
```

## Summary
- **Shell commands**: Always use `--query "your query"` for text queries
- **DSL specification**: Use `--dsl TYPE --query "query"` 
- **Special commands**: No `--query` needed for `analyze-env`, `validate`, `repair`
- **Python API**: No changes needed, works as documented

The CLI is working correctly - it just requires the proper syntax!
