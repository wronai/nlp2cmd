# Examples Guide

This guide provides a comprehensive overview of all NLP2CMD examples, organized by use case and complexity.

## 🗂️ Examples Structure

```
examples/
├── use_cases/                    # Real-world scenarios
│   ├── shell_commands_demo.sh    # Complete CLI examples
│   ├── simple_demo_examples.py   # Python API + Shell concepts
│   ├── complete_python_shell_examples.py # Full Python API
│   ├── dsl_commands_demo.py      # Direct DSL generation
│   ├── devops_automation.py      # DevOps workflows
│   ├── data_science_ml.py        # Data science workflows
│   ├── healthcare.py             # Healthcare applications
│   ├── finance_trading.py         # Financial operations
│   ├── smart_cities.py           # Urban management
│   └── ...
├── architecture/                 # System architecture demos
│   └── end_to_end_demo.py       # Complete workflow
├── sql/                         # SQL examples
│   ├── basic_sql.py            # Simple queries
│   ├── advanced_sql.py         # Complex queries
│   └── sql_workflows.py        # SQL pipelines
├── shell/                       # Shell examples
│   ├── basic_shell.py          # Common operations
│   ├── feedback_loop.py        # Interactive feedback
│   └── environment_analysis.py # System analysis
├── docker/                      # Docker examples
│   ├── basic_docker.py         # Container operations
│   └── file_repair.py          # Dockerfile repair
├── kubernetes/                  # Kubernetes examples
│   └── basic_kubernetes.py     # K8s operations
├── pipelines/                   # Pipeline examples
│   ├── log_analysis.py         # Log processing
│   └── infrastructure_health.py # System monitoring
└── validation/                  # Validation examples
    └── config_validation.py    # File validation
```

## 🚀 Quick Start Examples

### 1. CLI Usage Examples

**File:** `examples/use_cases/shell_commands_demo.sh`

The fastest way to see NLP2CMD in action:

```bash
# Run the complete CLI demo
./examples/use_cases/shell_commands_demo.sh

# Individual examples
nlp2cmd --query "Pokaż użytkowników"
nlp2cmd --dsl docker --query "Pokaż wszystkie kontenery"
nlp2cmd --dsl shell --query "Znajdź pliki .log większe niż 10MB"
nlp2cmd analyze-env
```

**What you'll learn:**
- Basic CLI syntax
- Different DSL types
- Environment analysis
- File validation

### 2. Python API Concepts

**File:** `examples/use_cases/simple_demo_examples.py`

Conceptual overview without installation requirements:

```bash
python3 examples/use_cases/simple_demo_examples.py
```

**What you'll learn:**
- Python API concepts
- Shell command patterns
- Mixed workflow approaches
- Real-world use cases

### 3. Complete Python API

**File:** `examples/use_cases/complete_python_shell_examples.py`

Full Python API with actual functionality:

```python
from nlp2cmd.generation import HybridThermodynamicGenerator

generator = HybridThermodynamicGenerator()

# DSL generation
result = await generator.generate("Pokaż użytkowników")

# Thermodynamic optimization
result = await generator.generate("Zoptymalizuj przydzielanie zasobów")
```

**What you'll learn:**
- HybridThermodynamicGenerator usage
- DSL vs thermodynamic routing
- Context-aware queries
- Performance patterns

## 📚 Domain-Specific Examples

### SQL Examples

**Basic SQL** (`examples/sql/basic_sql.py`)
```python
from nlp2cmd import NLP2CMD, SQLAdapter

nlp = NLP2CMD(adapter=SQLAdapter(dialect="postgresql"))

# Simple queries
result = nlp.transform("Pokaż wszystkich użytkowników")
print(result.command)  # SELECT * FROM users;

# Complex queries
result = nlp.transform("Pokaż użytkowników z Warszawy, którzy zarejestrowali się w ostatnim miesiącu")
print(result.command)  # SELECT * FROM users WHERE city = 'Warszawa' AND created_at >= NOW() - INTERVAL '1 month';
```

**Advanced SQL** (`examples/sql/advanced_sql.py`)
- Joins and subqueries
- Aggregation functions
- Window functions
- Complex filtering

### Shell Examples

**Basic Shell** (`examples/shell/basic_shell.py`)
```python
from nlp2cmd import NLP2CMD, ShellAdapter

nlp = NLP2CMD(adapter=ShellAdapter())

# File operations
result = nlp.transform("Znajdź pliki większe niż 100MB")
print(result.command)  # find . -size +100M -type f

# Process management
result = nlp.transform("Pokaż procesy zużywające najwięcej pamięci")
print(result.command)  # ps aux --sort=-%mem | head
```

**Environment Analysis** (`examples/shell/environment_analysis.py`)
- System monitoring
- Resource usage
- Network analysis
- Security checks

### Docker Examples

**Basic Docker** (`examples/docker/basic_docker.py`)
```python
from nlp2cmd import NLP2CMD, DockerAdapter

nlp = NLP2CMD(adapter=DockerAdapter())

# Container operations
result = nlp.transform("Pokaż wszystkie kontenery")
print(result.command)  # docker ps -a

# Image management
result = nlp.transform("Usuń nieużywane obrazy Docker")
print(result.command)  # docker image prune -f
```

### Kubernetes Examples

**Basic Kubernetes** (`examples/kubernetes/basic_kubernetes.py`)
```python
from nlp2cmd import NLP2CMD, KubernetesAdapter

nlp = NLP2CMD(adapter=KubernetesAdapter())

# Deployment operations
result = nlp.transform("Skaluj deployment nginx do 3 replik")
print(result.command)  # kubectl scale deployment nginx --replicas=3

# Status checking
result = nlp.transform("Pokaż wszystkie pody w namespace default")
print(result.command)  # kubectl get pods -n default
```

## 🏭 Real-World Use Cases

### DevOps Automation

**File:** `examples/use_cases/devops_automation.py`

```python
from nlp2cmd.generation import HybridThermodynamicGenerator

async def devops_workflow():
    generator = HybridThermodynamicGenerator()
    
    # System health check
    health = await generator.generate("Sprawdź status wszystkich usług")
    
    # Log analysis
    logs = await generator.generate("Znajdź błędy w logach aplikacji")
    
    # Resource optimization
    optimization = await generator.generate("Zoptymalizuj zużycie zasobów")
    
    return {
        "health": health,
        "logs": logs,
        "optimization": optimization
    }
```

**Scenarios covered:**
- System monitoring
- Log analysis
- Resource optimization
- Automated deployments
- Backup procedures

### Data Science & ML

**File:** `examples/use_cases/data_science_ml.py`

```python
# Data analysis workflows
result = await generator.generate("Analizuj trendy sprzedaży z ostatniego kwartału")

# Model optimization
result = await generator.generate("Zoptymalizuj hiperparametry modelu")

# Data preprocessing
result = await generator.generate("Wyczyść i przygotuj dane do analizy")
```

**Scenarios covered:**
- Data analysis
- Model training
- Feature engineering
- Data validation
- Pipeline automation

### Healthcare Applications

**File:** `examples/use_cases/healthcare.py`

```python
# Patient data analysis
result = await generator.generate("Analizuj dane pacjentów z grupy ryzyka")

# Treatment optimization
result = await generator.generate("Zoptymalizuj harmonogram leczenia")

# Resource allocation
result = await generator.generate("Rozdziel personel medyczny zgodnie z obciążeniem")
```

**Scenarios covered:**
- Patient data analysis
- Treatment scheduling
- Resource optimization
- Medical imaging
- Clinical workflows

### Finance & Trading

**File:** `examples/use_cases/finance_trading.py`

```python
# Portfolio optimization
result = await generator.generate("Zoptymalizuj portfel inwestycyjny")

# Risk analysis
result = await generator.generate("Analizuj ryzyko kredytowe")

# Trading strategies
result = await generator.generate("Zaproponuj strategię handlową")
```

**Scenarios covered:**
- Portfolio optimization
- Risk assessment
- Trading algorithms
- Fraud detection
- Compliance checking

### Smart Cities

**File:** `examples/use_cases/smart_cities.py`

```python
# Traffic optimization
result = await generator.generate("Zoptymalizaj sygnalizację świetlną")

# Energy management
result = await generator.generate("Zarządzaj zużyciem energii w mieście")

# Public transport
result = await generator.generate("Zaplanuj trasy transportu publicznego")
```

**Scenarios covered:**
- Traffic management
- Energy optimization
- Public transport
- Waste management
- Urban planning

## 🔬 Advanced Examples

### Thermodynamic Optimization

**File:** `examples/use_cases/physics_simulations.py`

```python
from nlp2cmd.generation import HybridThermodynamicGenerator

async def complex_optimization():
    generator = HybridThermodynamicGenerator()
    
    # Complex scheduling problem
    result = await generator.generate(
        "Zaplanuj 50 zadań w 20 slotach z ograniczeniami zasobów"
    )
    
    if result['source'] == 'thermodynamic':
        print(f"Energy: {result['result'].energy}")
        print(f"Samples: {result['result'].n_samples}")
        print(f"Solution: {result['result'].decoded_output}")
```

### Multi-Step Workflows

**File:** `examples/pipelines/log_analysis.py`

```python
from nlp2cmd import PlanExecutor, ExecutionPlan, PlanStep

executor = PlanExecutor()

# Multi-step log analysis pipeline
plan = ExecutionPlan(steps=[
    PlanStep(action="shell_find", params={"glob": "*.log"}, store_as="log_files"),
    PlanStep(action="shell_count_pattern", foreach="log_files", 
             params={"file": "$item", "pattern": "ERROR"}, store_as="error_counts"),
    PlanStep(action="summarize_results", params={"data": "$error_counts"}),
])

result = executor.execute(plan)
```

### Configuration Management

**File:** `examples/validation/config_validation.py`

```python
from nlp2cmd import SchemaRegistry

registry = SchemaRegistry()

# Validate configuration files
validation = registry.validate(content, "docker_compose")

# Repair configuration
repair = registry.repair(content, "docker_compose", auto_fix=True)

if repair["changes"]:
    print("Fixed issues:")
    for change in repair["changes"]:
        print(f"  - {change['reason']}")
```

## 🎯 Learning Path

### Beginner Level

1. **Start with CLI examples** (`shell_commands_demo.sh`)
   - Learn basic syntax
   - Understand DSL types
   - Try interactive mode

2. **Conceptual overview** (`simple_demo_examples.py`)
   - Understand Python API concepts
   - Learn shell command patterns
   - Explore use cases

### Intermediate Level

3. **Python API basics** (`complete_python_shell_examples.py`)
   - HybridThermodynamicGenerator
   - Context-aware queries
   - Error handling

4. **Domain-specific examples**
   - SQL: `examples/sql/basic_sql.py`
   - Shell: `examples/shell/basic_shell.py`
   - Docker: `examples/docker/basic_docker.py`

### Advanced Level

5. **Real-world use cases**
   - DevOps: `examples/use_cases/devops_automation.py`
   - Data Science: `examples/use_cases/data_science_ml.py`
   - Healthcare: `examples/use_cases/healthcare.py`

6. **Complex workflows**
   - Thermodynamic: `examples/use_cases/physics_simulations.py`
   - Pipelines: `examples/pipelines/log_analysis.py`
   - Architecture: `examples/architecture/end_to_end_demo.py`

## 🛠️ Running Examples

### Prerequisites

```bash
# Install NLP2CMD
pip install nlp2cmd

# For development mode
cd nlp2cmd
pip install -e .
```

### CLI Examples

```bash
# Make shell demo executable
chmod +x examples/use_cases/shell_commands_demo.sh

# Run CLI demo
./examples/use_cases/shell_commands_demo.sh

# Individual CLI commands
nlp2cmd --query "show all users"
nlp2cmd --dsl docker --query "list containers"
nlp2cmd analyze-env
```

### Python Examples

```bash
# Run Python examples
python3 examples/use_cases/simple_demo_examples.py
python3 examples/use_cases/complete_python_shell_examples.py
python3 examples/sql/basic_sql.py
python3 examples/use_cases/devops_automation.py
```

### Development Mode

```bash
# Set PYTHONPATH for development
export PYTHONPATH=/path/to/nlp2cmd/src:$PYTHONPATH

# Run with development version
python3 examples/use_cases/complete_python_shell_examples.py
```

## 📊 Performance Benchmarks

### DSL Generation

```python
# Simple queries: ~2-5ms
await generator.generate("show users")

# Medium complexity: ~5-15ms
await generator.generate("find files larger than 100MB modified in last week")

# Complex queries: ~15-50ms
await generator.generate("analyze system logs for security threats")
```

### Thermodynamic Optimization

```python
# Simple optimization: ~100-200ms
await generator.generate("optimize 5 tasks in 10 slots")

# Medium complexity: ~200-500ms
await generator.generate("allocate resources to 20 projects")

# Complex optimization: ~500-2000ms
await generator.generate("optimize city traffic with 1000 intersections")
```

## 🔧 Customization

### Adding Custom Examples

1. **Create new example file**
```python
# examples/use_cases/my_custom_example.py
from nlp2cmd.generation import HybridThermodynamicGenerator

async def custom_workflow():
    generator = HybridThermodynamicGenerator()
    # Your custom logic here
    pass
```

2. **Add to documentation**
   - Update this guide
   - Add to README examples section
   - Include in tests if needed

### Extending DSL Support

```python
# Custom adapter example
from nlp2cmd import BaseAdapter

class CustomAdapter(BaseAdapter):
    def transform(self, text: str, context: dict = None):
        # Custom transformation logic
        return "custom command"
```

## 🤝 Contributing Examples

When contributing examples:

1. **Follow the structure** - Use existing patterns
2. **Add documentation** - Explain the use case
3. **Include tests** - Unit tests for new examples
4. **Update guides** - Keep documentation current
5. **Performance notes** - Include timing information

## 📚 Additional Resources

- [CLI Reference](cli-reference.md) - Complete CLI documentation
- [Python API Guide](python-api.md) - Detailed API usage
- [User Guide](guides/user-guide.md) - Complete tutorial
- [Thermodynamic Integration](../THERMODYNAMIC_INTEGRATION.md) - Advanced optimization

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/wronai/nlp2cmd/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wronai/nlp2cmd/discussions)
- **Documentation**: [Full Docs](https://nlp2cmd.readthedocs.io/)
- **Examples**: Browse the `examples/` directory for more
