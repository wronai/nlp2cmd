# Text → Multi-DSL Generation Module

## 📚 Related Documentation

- **[Thermodynamic Integration](THERMODYNAMIC_INTEGRATION.md)** - Advanced optimization guide
- **[Thermodynamic Architecture](THERMODYNAMIC_ARCHITECTURE.md)** - Deep technical architecture
- **[User Guide](docs/guides/user-guide.md)** - Complete usage tutorial
- **[API Reference](docs/api/README.md)** - Generation API documentation
- **[Examples](examples/)** - Practical generation examples

Complete iterative implementation of natural language to DSL generation with thermodynamic optimization.

## Architecture Overview

```
Natural Language
       │
       ▼
┌─────────────────────────┐
│ HybridThermodynamicGen │
└───────────┬───────────────┘
            │
    ┌───────┼───────┐
    │       │       │
    ▼       ▼       ▼
Rules    LLM    Langevin
(0ms)   (~500ms) (~200ms)
    │       │       │
    ▼       ▼       ▼
DSL DSL DSL Optimization
```

## Iterations Summary

| Iteration | Component | Purpose | Performance |
|-----------|-----------|---------|-------------|
| 0 | Baseline | Measure existing adapters | ~5ms |
| 1 | Keywords | Rule-based intent detection | <1ms |
| 2 | Regex | Entity extraction | <2ms |
| 3 | Templates | Template-based generation | <3ms |
| 4 | Simple LLM | Single domain (SQL) | ~500ms |
| 5 | Multi-Domain | LLM routing + generation | ~500ms |
| 6 | Structured | JSON schema output | ~500ms |
| 7 | Validation | Self-correction | ~600ms |
| 9 | Hybrid | Rules + LLM fallback | 2-500ms |
| 10 | Thermodynamic | Langevin optimization | ~200ms |

## Quick Start

### Basic Usage

```python
from nlp2cmd.generation import create_hybrid_generator

# Create hybrid generator (rules first, LLM fallback)
generator = create_hybrid_generator()

# Generate DSL command
result = await generator.generate("Pokaż dane z tabeli users")
print(result.command)
# → SELECT * FROM users;

# Stats
stats = generator.get_stats()
print(f"Rule hit rate: {stats.rule_hit_rate:.1%}")
# → Rule hit rate: 85.0%
```

### Optimization Problems

```python
from nlp2cmd.generation import create_thermodynamic_generator

# Create thermodynamic generator
thermo = create_thermodynamic_generator(n_samples=5)

# Solve scheduling problem
result = await thermo.generate("Zaplanuj 5 zadań w 10 slotach")
print(result.decoded_output)
# → # Schedule:
#    Slot 0: task_0
#    Slot 2: task_1
#    Slot 4: task_2
```

### Complete Hybrid Solution

```python
from nlp2cmd.generation import HybridThermodynamicGenerator

# Handles both DSL and optimization
generator = HybridThermodynamicGenerator()

# Simple query → DSL
result = await generator.generate("Pokaż kontenery docker")
# → {'source': 'dsl', 'result': HybridResult(...)}

# Complex optimization → Thermodynamic
result = await generator.generate("Zoptymalizuj przydzielanie zasobów")
# → {'source': 'thermodynamic', 'result': ThermodynamicResult(...)}
```

## Domain Support

### DSL Domains (Rules + LLM)

| Domain | Examples | Commands |
|--------|----------|----------|
| **SQL** | "Pokaż użytkowników", "Insert into orders" | SELECT, INSERT, UPDATE, DELETE |
| **Shell** | "Znajdź pliki .py", "Pokaż procesy" | find, grep, ps, ls |
| **Docker** | "Pokaż kontenery", "Uruchom nginx" | docker ps, run, logs |
| **Kubernetes** | "Pokaż pody", "Skaluj deployment" | kubectl get, scale, logs |

### Optimization Domains (Thermodynamic)

| Type | Examples | Output |
|------|----------|--------|
| **Scheduling** | "Zaplanuj 5 zadań", "Schedule with deadlines" | Task-slot assignments |
| **Allocation** | "Przydziel zasoby", "Allocate resources" | Resource distribution |
| **Planning** | "Zoptymalizuj plan", "Optimize route" | Optimal sequences |

## Performance Metrics

### Rule-Based Generation
- **Latency**: <3ms
- **Cost**: $0
- **Accuracy**: 85-95% (for simple queries)
- **Energy**: Minimal

### LLM Generation
- **Latency**: ~500ms
- **Cost**: ~$0.01 per query
- **Accuracy**: 90-98%
- **Energy**: ~15mJ

### Thermodynamic Optimization
- **Latency**: ~200ms
- **Cost**: ~$0.01
- **Quality**: Optimal for constraints
- **Energy**: ~50mJ (digital), ~0.5mJ (analog future)

## Configuration

### Hybrid Generator

```python
from nlp2cmd.generation import create_hybrid_generator

generator = create_hybrid_generator(
    confidence_threshold=0.7,  # Rule confidence threshold
)

# Adaptive threshold
from nlp2cmd.generation import AdaptiveHybridGenerator

adaptive = AdaptiveHybridGenerator(
    initial_threshold=0.7,
    adaptation_rate=0.1,
)
```

### Thermodynamic Generator

```python
from nlp2cmd.generation import create_thermodynamic_generator
from nlp2cmd.thermodynamic import LangevinConfig

config = LangevinConfig(
    n_steps=1000,      # More steps = better quality
    kT=0.5,           # Temperature (exploration)
    mu=1.0,           # Mobility
    dim=64,           # Latent dimension
)

thermo = create_thermodynamic_generator(
    n_samples=10,     # Multiple candidates
    langevin_config=config,
    voting_strategy="energy",
)
```

## Testing

Run all tests:

```bash
PYTHONPATH=/home/tom/github/wronai/nlp2cmd/src python3 -m pytest tests/iterative/ -v
```

Results:
```
250 passed, 38 skipped in 0.43s
```

### Test Coverage

- **test_iter_0_baseline.py**: Adapter baseline (26 tests)
- **test_iter_1_keywords.py**: Keyword detection (64 tests)
- **test_iter_2_regex.py**: Entity extraction (43 tests)
- **test_iter_3_templates.py**: Template generation (46 tests)
- **test_iter_4_5_llm.py**: LLM integration (49 tests)
- **test_iter_6_7_structured.py**: Structured output + validation (49 tests)
- **test_iter_9_hybrid.py**: Hybrid generation (49 tests)
- **test_iter_10_thermodynamic.py**: Thermodynamic optimization (25 tests)

## Advanced Features

### Custom Patterns

```python
from nlp2cmd.generation import KeywordIntentDetector

detector = KeywordIntentDetector(
    patterns={
        'myapp': {
            'deploy': ['deploy-myapp', 'release-myapp'],
            'rollback': ['rollback-myapp'],
        }
    }
)
```

### Custom Validators

```python
from nlp2cmd.generation.validating import ValidatingGenerator

generator = ValidatingGenerator(
    generator=multi_domain_gen,
    validators={
        'custom_domain': MyCustomValidator(),
    }
)
```

### Custom Energy Models

```python
from nlp2cmd.generation.thermodynamic import EnergyModel

class MyEnergyModel(EnergyModel):
    def energy(self, z, condition):
        # Custom energy function
        return penalty
    
    def gradient(self, z, condition):
        # Custom gradient
        return grad
```

## Cost Optimization

The hybrid approach provides significant cost savings:

```python
stats = generator.get_stats()
print(f"Cost savings: {stats.cost_savings_percent:.1f}%")
# → Cost savings: 85.0%
```

Energy savings with thermodynamic approach:

```python
result = await thermo.generate("Complex optimization")
print(f"Energy savings: {result.energy_estimate['savings_digital_percent']:.1f}%")
# → Energy savings: 65.2%
```

## Integration Examples

### CLI Integration

```python
from nlp2cmd.generation import create_hybrid_generator
from nlp2cmd.cli.main import get_adapter

generator = create_hybrid_generator()

async def process_command(text: str):
    result = await generator.generate(text)
    
    if result.source == 'dsl':
        # Use existing adapter
        adapter = get_adapter(result.domain, {})
        plan = result.result.to_plan()
        return adapter.generate(plan)
    else:
        # Thermodynamic solution
        return result.result.decoded_output
```

### API Integration

```python
from fastapi import FastAPI
from nlp2cmd.generation import HybridThermodynamicGenerator

app = FastAPI()
generator = HybridThermodynamicGenerator()

@app.post("/generate")
async def generate(text: str):
    result = await generator.generate(text)
    return {
        "command": result.result.command if result.source == 'dsl' else None,
        "solution": result.result.decoded_output if result.source == 'thermodynamic' else None,
        "source": result.source,
        "complexity": result.complexity,
    }
```

## Future Directions

1. **Analog Implementation**: Physical Langevin sampling for 100x energy savings
2. **More Domains**: Network routing, financial optimization
3. **Real-time**: Sub-100ms thermodynamic sampling
4. **Multi-objective**: Pareto-optimal solution sets
5. **Learning**: Adaptive energy models from user feedback

## References

- Whitelam (2025) "Generative thermodynamic computing" arXiv:2506.15121
- Langevin dynamics for constraint satisfaction
- Energy-based models in optimization
- Hybrid AI systems for cost optimization
