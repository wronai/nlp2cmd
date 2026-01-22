# Thermodynamic Optimization Integration

## Overview

The `nlp2cmd.generation.thermodynamic` module integrates Whitelam's generative thermodynamic computing framework for solving complex optimization problems that traditional DSL generation cannot handle.

## Architecture

```
Natural Language → HybridThermodynamicGenerator → Solution
                     │
                     ├─ Rule/LLM → DSL Commands (simple queries)
                     └─ Langevin → Optimization Solutions (complex problems)
```

## Key Components

### 1. ThermodynamicGenerator

Generates solutions using Langevin dynamics sampling:

```python
from nlp2cmd.generation import create_thermodynamic_generator

# Create generator
thermo = create_thermodynamic_generator(
    n_samples=5,      # Multiple solutions
    n_steps=500,      # Langevin steps
)

# Generate solution
result = await thermo.generate("Zaplanuj 5 zadań w 10 slotach")
print(result.decoded_output)
# → Schedule:
#    Slot 0: task_0
#    Slot 2: task_1
#    Slot 4: task_2
```

### 2. Energy Models

Domain-specific energy functions for constraint satisfaction:

- **SchedulingEnergy**: Task scheduling with deadlines and overlap penalties
- **AllocationEnergy**: Resource allocation with capacity constraints
- **ConstraintEnergy**: Generic constraint satisfaction

### 3. HybridThermodynamicGenerator

Routes between DSL generation and thermodynamic optimization:

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

## Problem Types

### Scheduling Problems

```
Input: "Zaplanuj 5 zadań w 10 slotach, zadanie 3 musi być przed slotem 5"
Output:
# Schedule:
  Slot 0: task_0
  Slot 2: task_1
  Slot 4: task_2
  Slot 6: task_3
  Slot 8: task_4
```

### Resource Allocation

```
Input: "Przydziel 3 zasoby do 4 konsumentów, nie przekraczaj pojemności"
Output:
# Allocation:
  Consumer 0: R0=0.25, R1=0.50, R2=0.25
  Consumer 1: R0=0.33, R1=0.33, R2=0.33
  Consumer 2: R0=0.20, R1=0.40, R2=0.40
  Consumer 3: R0=0.50, R1=0.25, R2=0.25
```

## Performance Characteristics

| Metric | DSL Generation | Thermodynamic |
|--------|----------------|----------------|
| **Latency** | ~2ms | ~150-500ms |
| **Cost** | $0 | ~$0.01 |
| **Accuracy** | High for simple queries | Optimal for constraints |
| **Energy** | Minimal | ~10-50mJ |

## Energy Efficiency

The thermodynamic approach provides significant energy savings:

```python
result = await thermo.generate("Complex scheduling problem")
print(result.energy_estimate)
# → {
#     'savings_digital_percent': 65.2,
#     'savings_analog_percent': 98.7,
#     'breakdown': {
#         'llm_formalization': 0.003,
#         'langevin_digital': 0.15,
#         'langevin_analog': 0.005
#     }
# }
```

## Usage Examples

### Basic Usage

```python
from nlp2cmd.generation import (
    create_hybrid_generator,
    create_thermodynamic_generator,
)

# Hybrid for mixed workloads
hybrid = create_hybrid_generator()
result = await hybrid.generate("Pokaż dane z tabeli users")
# → Uses rules (2ms, $0)

result = await hybrid.generate("Zaplanuj zadania z ograniczeniami")
# → Uses thermodynamic (~200ms, ~$0.01)
```

### Custom Energy Models

```python
from nlp2cmd.generation.thermodynamic import (
    ThermodynamicGenerator,
    ConstraintEnergy,
    LangevinConfig,
)

# Custom constraint energy
energy = ConstraintEnergy()
energy.add_penalty(
    "custom_constraint",
    lambda z, c: violation_function(z, c),
    lambda z, c: gradient_function(z, c),
    weight=10.0
)

generator = ThermodynamicGenerator(
    energy_model=energy,
    langevin_config=LangevinConfig(n_steps=1000)
)
```

### Batch Processing

```python
problems = [
    "Zaplanuj 3 zadania",
    "Przydziel 2 zasoby",
    "Zoptymalizuj trasę",
]

results = await thermo.generate_batch(problems)
for result in results:
    print(f"Problem: {result.problem.problem_type}")
    print(f"Energy: {result.energy:.2f}")
    print(f"Solution: {result.decoded_output}\n")
```

## Configuration

### Langevin Parameters

```python
from nlp2cmd.thermodynamic import LangevinConfig

config = LangevinConfig(
    mu=1.0,              # Mobility coefficient
    kT=0.5,              # Thermal energy
    dt=0.01,             # Time step
    n_steps=1000,        # Integration steps
    dim=64,              # Latent dimension
    record_trajectory=True,
)

thermo = create_thermodynamic_generator(
    langevin_config=config,
    n_samples=10,
    voting_strategy="energy",
)
```

### Voting Strategies

- **energy**: Select lowest energy solution
- **entropy**: Select lowest entropy production
- **combined**: Weighted combination
- **cluster**: Most similar solution cluster

## Integration with Existing DSL

The thermodynamic generator integrates seamlessly with existing DSL adapters:

```python
# Standard DSL generation
from nlp2cmd.generation import create_hybrid_generator

hybrid = create_hybrid_generator()

# Mixed workload
queries = [
    "SELECT * FROM users",           # → SQL (rules)
    "docker ps -a",                 # → Docker (rules)
    "Zaplanuj zadania z terminami",  # → Scheduling (thermo)
    "kubectl get pods",              # → K8s (rules)
]

for query in queries:
    result = await hybrid.generate(query)
    print(f"{query} → {result['source']}")
```

## Testing

Run the full test suite:

```bash
PYTHONPATH=/home/tom/github/wronai/nlp2cmd/src python3 -m pytest \
    tests/iterative/test_iter_10_thermodynamic.py -v
```

## Future Extensions

1. **Analog Langevin**: Physical implementation for 100x energy savings
2. **More Energy Models**: TSP, knapsack, flow problems
3. **Multi-objective**: Pareto-optimal solutions
4. **Real-time**: Faster sampling for interactive use

## References

- Whitelam (2025) "Generative thermodynamic computing" arXiv:2506.15121
- Langevin dynamics for constraint satisfaction
- Energy-based models in optimization
