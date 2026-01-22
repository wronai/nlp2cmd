# NLP2CMD

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Natural Language to Domain-Specific Commands** - Production-ready framework for transforming natural language into DSL commands with full safety, validation, and observability.

## 🏗️ Architecture v0.2.0: LLM as Planner + Typed Actions

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   NLP Layer     │ → Intent + Entities
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Decision Router │ → Direct OR LLM Planner?
└────────┬────────┘
         │
┌────────┴────────┐
│                 │
▼                 ▼
┌──────────┐   ┌─────────────┐
│  Direct  │   │ LLM Planner │ → JSON Plan
└────┬─────┘   └──────┬──────┘
     │                │
     └───────┬────────┘
             │
             ▼
┌─────────────────┐
│ Plan Validator  │ → Check against Action Registry
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Plan Executor  │ → Execute Typed Actions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Result Aggregator│ → Format Output
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   User Output   │
└─────────────────┘
```

**Key Principle: LLM plans. Code executes. System controls.**

## ✨ Features

### Core Capabilities
- 🗣️ **5 DSL Adapters**: SQL, Shell, Docker, Kubernetes, DQL (Doctrine)
- 📁 **11 File Format Schemas**: Dockerfile, docker-compose, K8s manifests, GitHub workflows, .env, and more
- 🛡️ **Safety Policies**: Allowlist-based action control, no eval/shell execution
- 🔄 **Multi-step Plans**: Support for `foreach` loops and variable references between steps

### New Architecture Components (v0.2.0)
- 🔀 **Decision Router**: Intelligently routes queries to direct execution or LLM planner
- 📋 **Action Registry**: Central registry of 19+ typed actions with full validation
- ⚡ **Plan Executor**: Executes multi-step plans with tracing, retry, and error handling
- 🤖 **LLM Planner**: Generates JSON plans constrained to allowed actions
- 📊 **Result Aggregator**: Multiple output formats (text, table, JSON, markdown)

### Security Features
- ✅ No direct LLM access to system
- ✅ Typed actions (no eval/shell)
- ✅ Allowlist of permitted actions
- ✅ Full plan validation before execution
- ✅ Traceable execution (trace_id per request)

## 🚀 Quick Start

### Installation

```bash
pip install nlp2cmd
```

Or from source:

```bash
git clone https://github.com/example/nlp2cmd.git
cd nlp2cmd
pip install -e ".[dev]"
```

### Basic Usage (New Architecture)

```python
from nlp2cmd import (
    DecisionRouter,
    RoutingDecision,
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    ResultAggregator,
    OutputFormat,
    get_registry,
)

# Initialize components
router = DecisionRouter()
executor = PlanExecutor()
aggregator = ResultAggregator()

# Route a query
routing = router.route(
    intent="select",
    entities={"table": "users"},
    text="show all users",
    confidence=0.9,
)

if routing.decision == RoutingDecision.DIRECT:
    # Simple query - direct execution
    plan = ExecutionPlan(steps=[
        PlanStep(action="sql_select", params={"table": "users"})
    ])
else:
    # Complex query - use LLM Planner
    from nlp2cmd import LLMPlanner
    planner = LLMPlanner(llm_client=your_llm_client)
    result = planner.plan(intent="select", entities={}, text="...")
    plan = result.plan

# Execute and format results
exec_result = executor.execute(plan)
output = aggregator.aggregate(exec_result, format=OutputFormat.TABLE)
print(output.data)
```

### Multi-Step Plans with Foreach

```python
# Define a multi-step plan
plan = ExecutionPlan(steps=[
    PlanStep(
        action="shell_find",
        params={"glob": "*.log"},
        store_as="log_files",
    ),
    PlanStep(
        action="shell_count_pattern",
        foreach="log_files",  # Iterate over results
        params={"file": "$item", "pattern": "ERROR"},
        store_as="error_counts",
    ),
    PlanStep(
        action="summarize_results",
        params={"data": "$error_counts"},
    ),
])

# Execute with tracing
result = executor.execute(plan)
print(f"Trace ID: {result.trace_id}")
print(f"Duration: {result.total_duration_ms}ms")
```

### Legacy Usage (SQL Adapter)

```python
from nlp2cmd import NLP2CMD, SQLAdapter

# Initialize with SQL adapter
nlp = NLP2CMD(adapter=SQLAdapter(dialect="postgresql"))

# Transform natural language to SQL
result = nlp.transform("Pokaż wszystkich użytkowników z Warszawy")
print(result.command)  # SELECT * FROM users WHERE city = 'Warszawa';
```

## 📋 Action Registry

```python
from nlp2cmd import get_registry

registry = get_registry()

# List all domains
print(registry.list_domains())
# ['sql', 'shell', 'docker', 'kubernetes', 'utility']

# List actions by domain
print(registry.list_actions(domain="sql"))
# ['sql_select', 'sql_insert', 'sql_update', 'sql_delete', 'sql_aggregate']

# Get destructive actions (require confirmation)
print(registry.get_destructive_actions())
# ['sql_insert', 'sql_update', 'sql_delete', 'docker_run', ...]

# Generate LLM prompt with available actions
prompt = registry.to_llm_prompt(domain="sql")
```

## 🔧 DSL Support

| DSL | Adapter | Status |
|-----|---------|--------|
| SQL (PostgreSQL, MySQL, SQLite) | `SQLAdapter` | ✅ Stable |
| Shell (Bash, Zsh) | `ShellAdapter` | ✅ Stable |
| DQL (Doctrine) | `DQLAdapter` | ✅ Stable |
| Docker / Docker Compose | `DockerAdapter` | ✅ Stable |
| Kubernetes | `KubernetesAdapter` | ✅ Stable |

## 📁 Supported File Formats

- Dockerfile
- docker-compose.yml
- Kubernetes manifests (Deployment, Service, Ingress, ConfigMap)
- SQL migrations
- .env files
- nginx.conf
- GitHub Actions workflows
- Prisma Schema
- Terraform (.tf)
- .editorconfig
- package.json

## 📊 Output Formats

```python
from nlp2cmd import ResultAggregator, OutputFormat

aggregator = ResultAggregator()

# Text format (default)
result = aggregator.aggregate(exec_result, format=OutputFormat.TEXT)

# ASCII Table
result = aggregator.aggregate(exec_result, format=OutputFormat.TABLE)

# JSON (for programmatic use)
result = aggregator.aggregate(exec_result, format=OutputFormat.JSON)

# Markdown (for documentation)
result = aggregator.aggregate(exec_result, format=OutputFormat.MARKDOWN)

# Summary (for dashboards)
result = aggregator.aggregate(exec_result, format=OutputFormat.SUMMARY)
```

## 🛡️ Safety

The framework enforces safety at multiple levels:

1. **Action Allowlist**: Only registered actions can be executed
2. **Parameter Validation**: Full type checking and constraints
3. **Plan Validation**: All plans validated before execution
4. **No Code Generation**: LLM only produces JSON plans, not executable code
5. **Destructive Action Marking**: Actions that modify state are flagged

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific component tests
pytest tests/unit/test_router.py -v
pytest tests/unit/test_registry.py -v
pytest tests/unit/test_executor.py -v

# With coverage
pytest --cov=nlp2cmd --cov-report=html
```

## 📁 Project Structure

```
nlp2cmd/
├── src/nlp2cmd/
│   ├── __init__.py       # Main exports
│   ├── core.py           # Core NLP2CMD class
│   ├── router/           # Decision Router
│   ├── registry/         # Action Registry
│   ├── executor/         # Plan Executor
│   ├── planner/          # LLM Planner
│   ├── aggregator/       # Result Aggregator
│   ├── adapters/         # DSL Adapters (SQL, Shell, Docker, K8s, DQL)
│   ├── schemas/          # File Format Schemas
│   ├── feedback/         # Feedback Loop
│   ├── environment/      # Environment Analyzer
│   └── validators/       # Validators
├── tests/
│   ├── unit/            # Unit tests (~150 tests)
│   └── integration/     # Integration tests
├── examples/
│   ├── architecture/    # End-to-end demos
│   ├── sql/            # SQL examples
│   ├── shell/          # Shell examples
│   └── docker/         # Docker examples
└── docs/               # Documentation
```

## 🔖 Version History

### v0.2.0 (Current)
- New architecture: LLM as Planner + Typed Actions
- Decision Router for intelligent query routing
- Action Registry with 19+ typed actions
- Plan Executor with foreach, conditions, and retry
- Result Aggregator with multiple output formats
- Full observability (trace_id, duration tracking)
- 150+ tests

### v0.1.0
- Initial release
- 5 DSL adapters
- 11 file format schemas
- Safety policies
- Feedback loop

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [spaCy](https://spacy.io/) - NLP processing
- [Anthropic Claude](https://anthropic.com/) - LLM integration
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
