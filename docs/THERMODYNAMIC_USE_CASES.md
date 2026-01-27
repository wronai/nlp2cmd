# Thermodynamic Use Cases & Benefits

## 📚 Related Documentation

- **[Thermodynamic Integration](../THERMODYNAMIC_INTEGRATION.md)** - Core theory and architecture
- **[Examples Guide](examples-guide.md)** - How to run examples
- **[Python API Guide](python-api.md)** - Programmatic usage
- **[Use Cases](../examples/use_cases/README.md)** - Domain demos overview

## ✅ Quick Start

```bash
python3 examples/thermodynamic_example.py
python3 examples/use_cases/drug_discovery.py
```

## 1) Drug Discovery (Lead Optimization)

**Example:** `examples/use_cases/drug_discovery.py`

**Problem:** wielokryterialna optymalizacja cząsteczki (binding + ADMET)

**Solution (skrót):**

```text
Projected physicochemical profile:
  molecular_weight: 378.2
  logP: 2.7
  tpsa: 68.4
  hbd: 1.3
  hba: 5.4
  rotatable_bonds: 3.1
```

**Korzyści vs alternatywy:**

- **vs LLM-only:** energia oszczędzana dzięki samplingowi (45–57% mniejsze zużycie energii).
- **vs ręczne reguły/QSAR:** szybkie iteracje i równoczesna optymalizacja wielu kryteriów.
- **vs pełny docking:** redukcja kosztu wstępnego przeszukania przestrzeni kandydatów.

## 2) Healthcare Scheduling (OR + Nurse Rosters)

**Example:** `examples/use_cases/healthcare.py`

**Problem:** harmonogramowanie sal operacyjnych i grafiku personelu.

**Solution (skrót):**

- ułożenie harmonogramu z ograniczeniami czasu sterylizacji
- równoważenie obciążenia personelu i sal

**Korzyści vs alternatywy:**

- **vs manualne planowanie:** mniej konfliktów i szybszy time-to-schedule.
- **vs LLM-only:** stabilne spełnienie constraintów bez "hallucinated" terminów.

## 3) Bioinformatics Pipeline Scheduling

**Example:** `examples/use_cases/bioinformatics.py`

**Problem:** sekwencyjne kroki analizy genomowej z ograniczeniami RAM/CPU.

**Solution (skrót):**

- strategia równoległości dla FastQC/Alignment
- ograniczenia RAM per job są respektowane

**Korzyści vs alternatywy:**

- **vs ręczne skrypty:** lepsza równowaga throughput vs zasoby.
- **vs LLM-only:** ograniczenia sprzętowe traktowane jako twarde constrainty.

## 4) Logistics / Routing (VRP)

**Example:** `examples/use_cases/logistics_supply_chain.py`

**Problem:** minimalizacja dystansu przy zachowaniu okien czasowych.

**Solution (skrót):**

- optymalne trasy dla wielu pojazdów
- balans między dystansem a kosztami

**Korzyści vs alternatywy:**

- **vs heurystyki ad-hoc:** stabilniejsze wyniki przy wielu constraintach.
- **vs LLM-only:** brak naruszania ograniczeń liczby pojazdów i okien czasowych.

## 5) Physics / Experiment Scheduling

**Example:** `examples/use_cases/physics_simulations.py`

**Problem:** planowanie eksperymentów z czasami konfiguracji.

**Solution (skrót):**

- minimalizacja przełączeń konfiguracji
- priorytetyzacja zadań z deadline

**Korzyści vs alternatywy:**

- **vs LLM-only:** deterministyczna kontrola constraintów czasowych.
- **vs manualne harmonogramy:** krótszy czas konfiguracji i większa przepustowość.

## Custom Problem Types (Fallback Behavior)

Jeśli `problem_type` nie ma dedykowanego modelu energii, system używa `ConstraintEnergy`,
która zwraca tylko `raw_sample`. Możesz zmapować próbkę na zakresy:

```python
import math

from nlp2cmd.generation.thermodynamic import OptimizationProblem

raw_sample = result.solution.get("raw_sample", [])
constraints = {c["var"]: c for c in problem.constraints if c.get("type") == "range"}

projected = {}
for idx, var in enumerate(problem.variables):
    raw_value = raw_sample[idx] if idx < len(raw_sample) else 0.0
    if var in constraints:
        min_val = float(constraints[var]["min"])
        max_val = float(constraints[var]["max"])
        projected[var] = min_val + (max_val - min_val) / (1 + math.exp(-raw_value))

print(projected)
```

## Porównanie podejść (skrót)

| Podejście | Zalety | Ograniczenia |
| --- | --- | --- |
| DSL rules | <5 ms, zero kosztów LLM | Brak optymalizacji wielokryterialnej |
| LLM-only | Naturalne opisy, szybkie prototypowanie | Brak gwarancji constraintów |
| Thermodynamic | Constrainty + sampling + energia | Wymaga konfiguracji problemu |

---

**Tip:** dla szybkiej demonstracji uruchom `examples/thermodynamic_example.py`.
