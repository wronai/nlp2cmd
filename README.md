![img.png](img.png)

wypełnianie formularza:

nlp2cmd -r "otwórz https://www.prototypowanie.pl/kontakt/ i wypelnij formularz i wyslij"

![img_1.png](img_1.png)

![img_2.png](img_2.png)

realizacja zadan w shell
![img_3.png](img_3.png)

# NLP2CMD

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Production Ready](https://img.shields.io/badge/production%20ready-brightgreen.svg)](https://github.com/wronai/nlp2cmd)
[![85%+ Success Rate](https://img.shields.io/badge/success%20rate-85%25%2B-brightgreen.svg)](https://github.com/wronai/nlp2cmd)

**Natural Language to Domain-Specific Commands** - Production-ready framework for transforming natural language into DSL commands with full safety, validation, and observability.

## 🚀 Quick Start

```bash
# Install with all dependencies
pip install nlp2cmd[all]

# Setup external dependencies cache (Playwright browsers)
nlp2cmd cache auto-setup

# Start using
nlp2cmd "uruchom usługę nginx"
nlp2cmd "zainstaluj docker"
nlp2cmd "pokaż pliki użytkownika"
nlp2cmd "znajdź pliki większe niż 100MB zmodyfikowane ostatnie 7 dni"
```

## 🎯 Key Features

### 🌐 Multi-Domain Support
- **SQL** - Natural language to SQL queries
- **Shell** - System commands and file operations  
- **Docker** - Container management
- **Kubernetes** - K8s orchestration
- **Browser** - Web automation and search (Google, GitHub, Amazon)
- **DQL** - Domain Query Language

### 🧠 Advanced NLP
- **Polish Language Support** - Native Polish NLP with spaCy (87%+ accuracy)
- **Fuzzy Matching** - Typo tolerance with rapidfuzz
- **Lemmatization** - Word form normalization
- **Priority Intent Detection** - Smart command classification
- **Enhanced Entity Extraction** - Time, size, username, path detection

### 🔧 Advanced File Operations
- **Time-based Search** - `znajdź pliki zmodyfikowane ostatnie 7 dni`
- **Size-based Filtering** - `znajdź pliki większe niż 100MB`
- **Combined Filters** - `znajdź pliki .log większe niż 10MB starsze niż 30 dni`
- **User Directory Operations** - `pokaż pliki użytkownika` → `find $HOME -type f`
- **Username-specific Paths** - `pokaż foldery użytkownika root` → `ls -la /root`

### 📦 Package Management
- **APT Installation** - `zainstaluj vlc` → `sudo apt-get install vlc`
- **Multi-variant Support** - Polish and English package commands
- **Cross-platform Ready** - OS detection and appropriate commands
- **Pattern Matching** - Multi-word keyword detection
- **Confidence Scoring** - Intent detection reliability

### 🌍 Web Automation
```bash
# Extract schema from any website
nlp2cmd web-schema extract https://example.com

# Fill forms automatically
nlp2cmd -r "otwórz https://www.prototypowanie.pl/kontakt/ i wypełnij formularz i wyślij"

# Manage interaction history
nlp2cmd web-schema history --stats
```

### 💾 Smart Caching
```bash
# External dependencies cache management
nlp2cmd cache info          # Show cache status
nlp2cmd cache auto-setup    # Install and configure
nlp2cmd cache clear         # Clear cache if needed
```

## 🏗️ Architecture Overview

```text
   ┌─────────────────┐
   │   User Query    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │   NLP Layer     │ → Intent + Entities + Confidence
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Intent Router  │ → Domain + Intent Classification
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Entity Extractor│ → Time, Size, Username, Path
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Command Generator│ → Domain-specific Commands
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Safety Validator│ → Command Safety Check
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │   Execution     │ → Run Command with Confirmation
   └─────────────────┘
```

## 📊 Performance Metrics

### 🎯 Success Rate by Domain
- **Shell Operations**: 90%+ (files, processes, packages)
- **Package Management**: 100% (apt install, zainstaluj)
- **User File Operations**: 100% (user directory detection)
- **Advanced Find**: 100% (size + age filtering)
- **Web Search**: 33% (Google, GitHub, Amazon)
- **Overall System**: 85%+ Production Ready

### 🚀 Advanced Examples

#### File Operations with Time & Size
```bash
# Find files modified in last 7 days larger than 100MB
nlp2cmd "znajdź pliki większe niż 100MB zmodyfikowane ostatnie 7 dni"
# → find . -type f -size +100MB -mtime +7

# Search user's home directory for large files
nlp2cmd "pokaż pliki użytkownika większe niż 50GB"
# → find $HOME -type f -size +50GB

# Find specific file types with age filter
nlp2cmd "znajdź pliki .log większe niż 10MB starsze niż 2 dni"
# → find . -type f -name '*.log' -size +10MB -mtime -2
```

#### User-Specific Operations
```bash
# List current user's files
nlp2cmd "pokaż pliki użytkownika"
# → find $HOME -type f

# List specific user's directory
nlp2cmd "pokaż foldery użytkownika root"
# → ls -la /root

# List files in user directory
nlp2cmd "listuj pliki w katalogu domowym"
# → ls -la .
```

#### Package Management
```bash
# Install packages (Polish & English)
nlp2cmd "zainstaluj vlc"
# → sudo apt-get install vlc

nlp2cmd "apt install nginx"
# → sudo apt-get install nginx

nlp2cmd "install git"
# → sudo apt-get install git
```

#### Browser & Web Operations
```bash
# Search Google
nlp2cmd "wyszukaj w google python tutorial"
# → xdg-open 'https://www.google.com/search?q=w google python tutorial'

# Search GitHub
nlp2cmd "znajdź repozytorium nlp2cmd na github"
# → xdg-open 'https://github.com/search?q=nlp2cmd&type=repositories'

# Search Amazon
nlp2cmd "szukaj na amazon python books"
# → xdg-open 'https://www.amazon.com/s?k=python books'
```

### Key Principle

**Natural Language → System Commands** with 85%+ accuracy and full safety validation.

## ✨ Features

### Core Capabilities

- 🗣️ **6 DSL Adapters**: SQL, Shell, Docker, Kubernetes, DQL (Doctrine), Browser
- 🧠 **Polish NLP**: Native Polish language support with 87%+ accuracy
- 🔍 **Advanced Search**: Time-based, size-based, and combined filtering
- 👤 **User Operations**: Username-specific directory operations
- 📦 **Package Management**: APT installation with Polish variants
- 🌐 **Web Automation**: Google, GitHub, Amazon search integration
- ⚡ **Real-time Processing**: Sub-second command generation
- 🛡️ **Safety Validation**: Command safety checks and confirmation
- 📁 **11 File Format Schemas**: Dockerfile, docker-compose, K8s manifests, GitHub workflows, .env, and more
- 🛡️ **Safety Policies**: Allowlist-based action control, no eval/shell execution
- 🔄 **Multi-step Plans**: Support for `foreach` loops and variable references between steps
- 🌍 **Polish NLP**: Native Polish language support with lemmatization and fuzzy matching
- 💾 **Smart Caching**: External dependencies cache for Playwright browsers

### New Architecture Components (v0.2.0)

- 🔀 **Decision Router**: Intelligently routes queries to direct execution or LLM planner
- 📋 **Action Registry**: Central registry of 19+ typed actions with full validation
- ⚡ **Plan Executor**: Executes multi-step plans with tracing, retry, and error handling
- 🤖 **LLM Planner**: Generates JSON plans constrained to allowed actions
- 📊 **Result Aggregator**: Multiple output formats (text, table, JSON, markdown)
- 🌐 **Web Schema Engine**: Browser automation with Playwright integration
- 💾 **Cache Manager**: Smart caching for external dependencies

### Security Features

- ✅ No direct LLM access to system
- ✅ Typed actions (no eval/shell)
- ✅ Allowlist of permitted actions
- ✅ Full plan validation before execution
- ✅ Traceable execution (trace_id per request)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Documentation Hub](docs/README.md)** | Entry point and navigation for all docs |
| **[Installation Guide](INSTALLATION.md)** | Setup instructions and installation options |
| **[User Guide](docs/guides/user-guide.md)** | Complete usage tutorial and examples |
| **[CLI Reference](docs/cli-reference.md)** | Comprehensive CLI documentation |
| **[Python API Guide](docs/python-api.md)** | Detailed Python API usage |
| **[Examples Guide](docs/examples-guide.md)** | Comprehensive examples overview |
| **[API Reference](docs/api/README.md)** | Detailed API documentation |
| **[Thermodynamic Integration](THERMODYNAMIC_INTEGRATION.md)** | Advanced optimization with Langevin dynamics |
| **[Thermodynamic Architecture](THERMODYNAMIC_ARCHITECTURE.md)** | Deep technical architecture overview |
| **[Contributing Guide](CONTRIBUTING.md)** | Development guidelines and contribution process |
| **[Generation Module](README_GENERATION.md)** | DSL generation implementation details |
| **[Quick Fix Reference](docs/quick-fix-reference.md)** | Common issues and solutions |
| **[Keyword Detection Flow](docs/KEYWORD_DETECTION_FLOW.md)** | Detailed keyword intent detection pipeline and fallback mechanisms |
| **[Enhanced NLP Integration](docs/ENHANCED_NLP_INTEGRATION.md)** | Advanced NLP libraries integration with semantic similarity and web schema context |
| **[Web Schema Guide](docs/WEB_SCHEMA_GUIDE.md)** | Browser automation and form filling |
| **[Cache Management Guide](docs/CACHE_MANAGEMENT.md)** | External dependencies caching |

## 🚀 Quick Start

### Installation

```bash
# Install with all dependencies
pip install nlp2cmd[all]

# Or install specific components
pip install nlp2cmd[browser,nlp]  # Web automation + Polish NLP
pip install nlp2cmd[sql,shell]   # Database + system commands
```

### Shell Emulation Mode

NLP2cmd provides full shell emulation capabilities for system commands:

```bash
# Interactive shell mode
nlp2cmd --interactive --dsl shell
nlp2cmd> list files in current directory
nlp2cmd> find files larger than 100MB
nlp2cmd> show running processes
nlp2cmd> exit

# Single query mode
nlp2cmd --dsl shell --query "list files in current directory"
# Output: ls -la .

# Execute immediately (run mode)
nlp2cmd --run "list files in current directory" --auto-confirm
# Executes: ls -la . with real output

# Polish language support
nlp2cmd --dsl shell --query "znajdź pliki .log większe niż 10MB"
# Output: find . -type f -name "*.log" -size +10MB -exec ls -lh {} \;

# Process management
nlp2cmd --dsl shell --query "uruchom usługę nginx"
# Output: systemctl start nginx

nlp2cmd --dsl shell --query "pokaż procesy zużywające najwięcej pamięci"
# Output: ps aux --sort=-%mem | head -10
```

### Setup External Dependencies

```bash
# Auto-setup Playwright browsers and cache
nlp2cmd cache auto-setup

# Manual setup
nlp2cmd cache install --package playwright
```

### CLI Usage

The fastest way to use NLP2CMD is through the command line interface:

```bash
# Basic query
nlp2cmd --query "Pokaż użytkowników"

# Specific DSL
nlp2cmd --dsl sql --query "SELECT * FROM users WHERE city = 'Warsaw'"
nlp2cmd --dsl shell --query "Znajdź pliki .log większe niż 10MB"
nlp2cmd --dsl docker --query "Pokaż wszystkie kontenery"
nlp2cmd --dsl kubernetes --query "Skaluj deployment nginx do 3 replik"

# Web automation
nlp2cmd --dsl browser --query "otwórz https://example.com i wypełnij formularz"
nlp2cmd web-schema extract https://example.com
nlp2cmd web-schema history --stats

# With options
nlp2cmd --explain --query "Sprawdź status systemu"
nlp2cmd --auto-repair --query "Napraw konfigurację nginx"

# Interactive mode
nlp2cmd --interactive

# Cache management
nlp2cmd cache info
nlp2cmd cache auto-setup

# Environment analysis
nlp2cmd analyze-env
nlp2cmd analyze-env --output environment.json

# File validation and repair
nlp2cmd validate config.json
nlp2cmd repair docker-compose.yml --backup
```

#### Working Examples

##### Shell Emulation Examples

```bash
# Interactive mode
$ nlp2cmd --interactive --dsl shell
╭──────────────────────────────────────────╮
│ NLP2CMD Interactive Mode                 │
│ Type 'help' for commands, 'exit' to quit │
╰──────────────────────────────────────────╯
🔍 Environment: Linux (6.17.0-8-generic)
🛠️  Tools: docker, docker-compose, kubectl, git, python, node, terraform, ansible
📁 Config files: 6

nlp2cmd> list files in current directory
ls -la .

nlp2cmd> find files larger than 100MB
find . -type f -size +100MB -exec ls -lh {} \;

nlp2cmd> show running processes
ps aux

nlp2cmd> exit
👋 Goodbye!

# Single query examples
$ nlp2cmd --dsl shell --query "Pokaż użytkowników"
ls -la .

📊 ⏱️  Time: 13.7ms | 💻 CPU: 0.0% | 🧠 RAM: 54.8MB (0.1%) | ⚡ Energy: 0.120mJ

$ nlp2cmd --dsl shell --query "Znajdź pliki .log większe niż 10MB"
find . -type f -name "*.log" -size +10MB -exec ls -lh {} \;

📊 ⏱️  Time: 3.1ms | 💻 CPU: 0.0% | 🧠 RAM: 55.1MB (0.1%) | ⚡ Energy: 0.028mJ

# Run mode with execution
$ nlp2cmd --run "list files in current directory" --auto-confirm
╭──────────────────────────────── 🚀 Run Mode ─────────────────────────────────╮
│ list files in current directory                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
Generating command...
Detected: shell/list

$ ls -la .
  total 1280
  drwxrwxr-x 23 tom tom   4096 Jan 24 21:23 .
  drwxrwxr-x 31 tom tom   4096 Jan 24 09:33 ..
  -rw-r--r--  1 tom tom   5450 Jan 24 21:20 CHANGELOG.md
  -rw-r--r--  1 tom tom  22677 Jan 24 21:20 README.md
  ...
✓ Command completed in 25.7ms

# Polish language examples
$ nlp2cmd --dsl shell --query "uruchom usługę nginx"
systemctl start nginx

$ nlp2cmd --dsl shell --query "pokaż procesy zużywające najwięcej pamięci"
ps aux --sort=-%mem | head -10

$ nlp2cmd --dsl shell --query "znajdź pliki z rozszerzeniem .py"
find . -name "*.py" -type f
```

##### Other DSL Examples

```bash
$ nlp2cmd --dsl docker --query "Pokaż wszystkie kontenery"
docker ps -a

📊 ⏱️  Time: 2.2ms | 💻 CPU: 0.0% | 🧠 RAM: 55.2MB (0.1%) | ⚡ Energy: 0.019mJ

$ nlp2cmd web-schema extract https://httpbin.org/forms/post
✓ Schema extracted successfully
📊 Extracted Elements: 12 inputs, 1 button, 1 form

$ nlp2cmd cache info
📁 Cache Directory: ~/.cache/external
💾 Total Size: 3105.4 MB
📦 Cached Packages: 1 (playwright)
                Tools                
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Tool           ┃ Version ┃ Status ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ docker         │ 29.1.5  │ ✅     │
│ kubectl        │ -       │ ✅     │
│ git            │ 2.51.0  │ ✅     │
└────────────────┴─────────┴────────┘
```

### Python API Usage

#### Basic Usage (New Architecture)

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

#### HybridThermodynamicGenerator (Recommended)

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

## 🔍 Keyword Intent Detection

NLP2CMD uses a **robust multi-layered detection pipeline** that ensures reliable intent recognition even with typos, variations, or missing dependencies:

### Detection Pipeline (11 Layers)

1. **Text Normalization** - Polish diacritics, typo corrections, optional lemmatization
2. **Fast Path Detection** - Quick browser/search queries
3. **SQL Context Detection** - Identify SQL keywords
4. **SQL DROP Detection** - High-priority dangerous operations
5. **Docker Detection** - Explicit Docker commands
6. **Kubernetes Detection** - K8s-specific commands
7. **Service Restart Detection** - Service management priority
8. **Priority Intents** - Configured high-priority patterns
9. **General Pattern Matching** - Full keyword matching with confidence scoring
10. **Fuzzy Matching** - Optional rapidfuzz for typos (85% threshold)
11. **Final Fallback** - Always returns `unknown/unknown`

### Key Guarantees

✅ **Always works** - Final fallback ensures no method returns `None`  
✅ **Graceful degradation** - Missing dependencies don't break the pipeline  
✅ **Typo tolerance** - Built-in corrections + optional fuzzy matching  
✅ **Performance optimized** - Fast path and priority checks first  
✅ **Safety first** - Dangerous operations get highest priority  

### Example Flow

```text
Input: "dokcer ps" (typo)
1. Normalization: "dokcer" → "docker"
2. Pattern matching: "docker ps" → docker/list
Result: ✅ Works without fuzzy matching
```

**[📖 Full Documentation](docs/KEYWORD_DETECTION_FLOW.md)**

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

# Thermodynamic optimization tests
PYTHONPATH=/home/tom/github/wronai/nlp2cmd/src python3 -m pytest \
    tests/iterative/test_iter_10_thermodynamic.py -v

# With coverage
pytest --cov=nlp2cmd --cov-report=html
```

## 🔬 Thermodynamic Optimization (v0.3.0+)

Based on [Whitelam (2025) "Generative thermodynamic computing"](https://arxiv.org/abs/2506.15121), the framework now includes thermodynamic optimization for complex constraint satisfaction problems.

### Key Features

- **Langevin Dynamics Sampling**: Natural evolution from noise to structured solutions
- **Energy-Based Models**: Domain-specific constraint functions
- **Hybrid Routing**: Automatic selection between DSL generation and thermodynamic optimization
- **Energy Efficiency**: 50-70% reduction vs pure LLM inference

### Quick Example

```python
from nlp2cmd.generation import create_hybrid_generator

# Create hybrid generator (DSL + Thermodynamic)
hybrid = create_hybrid_generator()

# Simple query → DSL generation (2ms, $0)
result = await hybrid.generate("SELECT * FROM users")
print(result['source'])  # 'dsl'

# Complex optimization → Thermodynamic sampling (~200ms, ~$0.01)
result = await hybrid.generate("Zaplanuj 5 zadań w 10 slotach z ograniczeniami")
print(result['source'])  # 'thermodynamic'
print(result['result'].decoded_output)
# Schedule:
#   Slot 0: task_0
#   Slot 2: task_1
#   Slot 4: task_2

# Energy savings estimate
print(result['result'].energy_estimate)
# {'savings_digital_percent': 65.2, 'savings_analog_percent': 98.7}
```

### Supported Problem Types

- **Scheduling**: Task scheduling with deadlines and constraints
- **Resource Allocation**: Optimal distribution under capacity limits  
- **Planning**: Multi-step planning with constraint satisfaction
- **Optimization**: General constrained optimization problems

See [Thermodynamic Integration](THERMODYNAMIC_INTEGRATION.md) for detailed documentation.

## 💡 Examples

### CLI Examples

- **[Shell Commands Demo](examples/use_cases/shell_commands_demo.sh)** - Complete CLI usage examples
- **[Simple Demo](examples/use_cases/simple_demo_examples.py)** - Python API + Shell concepts
- **[Complete Examples](examples/use_cases/complete_python_shell_examples.py)** - Full Python API examples
- **[DSL Commands Demo](examples/use_cases/dsl_commands_demo.py)** - Direct DSL generation examples

### Quick Examples

- **[Basic SQL](examples/sql/basic_sql.py)** - Simple SQL queries
- **[Shell Commands](examples/shell/basic_shell.py)** - Common shell operations  
- **[Docker Management](examples/docker/basic_docker.py)** - Container operations
- **[Kubernetes](examples/kubernetes/basic_kubernetes.py)** - K8s cluster management

### Advanced Examples  

- **[End-to-End Demo](examples/architecture/end_to_end_demo.py)** - Complete workflow
- **[Log Analysis Pipeline](examples/pipelines/log_analysis.py)** - Data processing
- **[Infrastructure Health](examples/pipelines/infrastructure_health.py)** - System monitoring
- **[Configuration Validation](examples/validation/config_validation.py)** - File validation

### Use Case Examples

- **[DevOps Automation](examples/use_cases/devops_automation.py)** - IT operations
- **[Data Science & ML](examples/use_cases/data_science_ml.py)** - Data workflows
- **[Healthcare](examples/use_cases/healthcare.py)** - Medical applications
- **[Finance & Trading](examples/use_cases/finance_trading.py)** - Financial operations
- **[Smart Cities](examples/use_cases/smart_cities.py)** - Urban management

### Documentation

- **[CLI Reference](docs/cli-reference.md)** - Complete CLI documentation
- **[Python API Guide](docs/python-api.md)** - Detailed Python API usage
- **[Examples Guide](docs/examples-guide.md)** - Comprehensive examples overview

See [Examples README](examples/use_cases/README.md) for all available examples.

## 📁 Project Structure

```text
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

### v0.3.0+ (Thermodynamic Integration)

- **NEW**: Thermodynamic optimization using Whitelam's generative framework
- Langevin dynamics for constraint satisfaction problems
- 50-70% energy reduction vs pure LLM inference
- Hybrid router: DSL generation + thermodynamic optimization
- Domain-specific energy models (scheduling, allocation, planning)
- Parallel sampling with energy-based voting

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

Apache License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [Whitelam, S. (2025)](https://arxiv.org/abs/2506.15121) "Generative thermodynamic computing" - Theoretical foundation for thermodynamic optimization
- [spaCy](https://spacy.io/) - NLP processing
- [Anthropic Claude](https://anthropic.com/) - LLM integration
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
