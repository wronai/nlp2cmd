# 🔬 NLP2CMD v0.3.0+ - Architektura Termodynamiczna (Whitelam Framework)

## 📖 Kontekst: Framework Whitelama

**Źródło:** "Generative thermodynamic computing" (arXiv:2506.15121, Whitelam 2025)

**Kluczowa idea:** Zamiast używać sieci neuronowej do "odszumiania" (jak w diffusion models), wykorzystujemy naturalną ewolucję fizycznego układu stochastycznego (dynamika Langevina). Dane "wyłaniają się z szumu" wprost z dynamiki termodynamicznej.

**Formuła uczenia:**
```
Maksymalizuj prawdopodobieństwo generowania odwróconych trajektorii procesu "zaszumiania"
→ generacja z minimalną emisją ciepła (minimalna dysypacja)
```

---

## 🎯 Twoja Teza: Setki Wyspecjalizowanych Agentów

**Tak, masz rację!** To fundamentalna zmiana paradygmatu:

```
[Stary model]
LLM → długa odpowiedź tekstowa (droga inferencja)

[Nowy model - Whitelam/Bielik]
LLM (Bielik) → formalizacja + warunek c → Langevin/EBM sampler → rozwiązanie
                    ↓
         "setki wyspecjalizowanych agentów"
```

### Dlaczego to zmiana paradygmatu?

1. **Rozdzielenie ról:**
   - LLM: semantyka, rozumowanie, formalizacja (krótkie)
   - Samplery: ciężkie obliczenia (zrównoleglialne)

2. **Orchestracja:**
   - Router decyduje który sampler użyć
   - Wiele samplerów może działać równolegle
   - Wyniki agregowane

3. **Efektywność energetyczna:**
   - LLM nie generuje długich odpowiedzi
   - Ciężar obliczeniowy w samplerach (potencjalnie analogowych)
   - Zrównoleglenie bez kosztów sekwencyjnej generacji tokenów

---

## 🏗️ Proponowana Architektura NLP2CMD v0.3.0 (Thermodynamic Edition)

```
┌─────────────────────────────────────────────────────────────────┐
│                    NLP2CMD Thermodynamic                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Router    │────▶│  Formalizer │────▶│ Orchestrator│       │
│  │  (Intent)   │     │   (Bielik)  │     │  (Parallel) │       │
│  └─────────────┘     └─────────────┘     └──────┬──────┘       │
│                                                  │               │
│         ┌────────────────┬───────────────┬──────┴─────┐        │
│         ▼                ▼               ▼            ▼        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐  │
│  │ SQL Agent  │  │Shell Agent │  │ K8s Agent  │  │Langevin │  │
│  │ (Classic)  │  │ (Classic)  │  │ (Classic)  │  │ Sampler │  │
│  └────────────┘  └────────────┘  └────────────┘  └─────────┘  │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐  │
│  │Constraint  │  │  Schedule  │  │  Resource  │  │   EBM   │  │
│  │  Solver    │  │  Planner   │  │ Allocator  │  │ Sampler │  │
│  └────────────┘  └────────────┘  └────────────┘  └─────────┘  │
│                                                                 │
│         ┌────────────────┴───────────────┐                     │
│         ▼                                ▼                     │
│  ┌─────────────┐                 ┌─────────────┐               │
│  │ Aggregator  │                 │   Cache     │               │
│  │  (Results)  │                 │ (Semantic)  │               │
│  └─────────────┘                 └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🆕 Nowe Komponenty do Implementacji

### 1. Langevin Sampler Module

```python
# src/nlp2cmd/thermodynamic/langevin.py

@dataclass
class LangevinConfig:
    """Configuration for Langevin dynamics sampler."""
    mu: float = 1.0           # Mobility coefficient
    kT: float = 1.0           # Thermal energy (temperature)
    dt: float = 0.01          # Time step
    n_steps: int = 1000       # Number of steps
    dim: int = 64             # Latent dimension


class LangevinSampler:
    """
    Thermodynamic sampler using overdamped Langevin dynamics.
    
    Implements: ż = -μ∇V(z;c) + √(2μkT) ξ(t)
    
    Where:
    - z: latent state
    - c: condition from LLM
    - V: energy function (learnable)
    - ξ: white noise
    """
    
    def __init__(self, energy_model: EnergyModel, config: LangevinConfig):
        self.energy = energy_model
        self.config = config
    
    def sample(self, condition: torch.Tensor, n_samples: int = 1) -> torch.Tensor:
        """Generate samples via Langevin dynamics."""
        z = torch.randn(n_samples, self.config.dim)  # Start from noise
        
        for step in range(self.config.n_steps):
            # Compute energy gradient
            grad_V = self.energy.gradient(z, condition)
            
            # Langevin update
            noise = torch.randn_like(z)
            z = z - self.config.mu * grad_V * self.config.dt \
                + math.sqrt(2 * self.config.mu * self.config.kT * self.config.dt) * noise
        
        return z
    
    def estimate_entropy_production(self, trajectory: torch.Tensor) -> float:
        """
        Estimate entropy production along trajectory.
        Lower = more reversible = better generative quality.
        """
        # Compute heat dissipation Q along trajectory
        Q = 0.0
        for t in range(len(trajectory) - 1):
            dz = trajectory[t+1] - trajectory[t]
            grad_V = self.energy.gradient(trajectory[t])
            Q += torch.dot(grad_V, dz)
        return Q.item()
```

### 2. Energy-Based Model for Constraints

```python
# src/nlp2cmd/thermodynamic/energy.py

class ConstraintEnergy(nn.Module):
    """
    Energy function for constraint satisfaction problems.
    
    V(z; c) = Σ_a λ_a φ_a(z; c)
    
    Where:
    - φ_a: penalty functions for constraint violations
    - λ_a: weights (learnable or fixed)
    """
    
    def __init__(self, constraint_types: List[str]):
        super().__init__()
        self.penalties = nn.ModuleDict({
            ct: ConstraintPenalty(ct) for ct in constraint_types
        })
        self.lambdas = nn.ParameterDict({
            ct: nn.Parameter(torch.ones(1)) for ct in constraint_types
        })
    
    def forward(self, z: torch.Tensor, condition: dict) -> torch.Tensor:
        """Compute total energy."""
        total_energy = 0.0
        for name, penalty in self.penalties.items():
            if name in condition.get('constraints', {}):
                constraint_spec = condition['constraints'][name]
                violation = penalty(z, constraint_spec)
                total_energy += self.lambdas[name] * violation
        return total_energy
    
    def gradient(self, z: torch.Tensor, condition: dict) -> torch.Tensor:
        """Compute energy gradient ∇V(z;c)."""
        z.requires_grad_(True)
        V = self.forward(z, condition)
        grad = torch.autograd.grad(V, z, create_graph=True)[0]
        return grad


class SchedulingEnergy(ConstraintEnergy):
    """Energy model for scheduling problems."""
    
    CONSTRAINT_TYPES = [
        'no_overlap',       # Tasks can't overlap
        'resource_limit',   # Resource capacity constraints
        'precedence',       # Task ordering constraints
        'deadline',         # Deadline constraints
        'preference',       # Soft preferences
    ]
    
    def __init__(self):
        super().__init__(self.CONSTRAINT_TYPES)


class AllocationEnergy(ConstraintEnergy):
    """Energy model for resource allocation."""
    
    CONSTRAINT_TYPES = [
        'capacity',         # Don't exceed capacity
        'demand',           # Meet demand
        'balance',          # Load balancing
        'cost',             # Minimize cost
    ]
```

### 3. Thermodynamic Router

```python
# src/nlp2cmd/thermodynamic/router.py

class ThermodynamicRouter:
    """
    Routes problems to appropriate solver:
    - Classic DSL agents for simple queries
    - Langevin/EBM for constraint satisfaction
    """
    
    THERMODYNAMIC_INTENTS = {
        'schedule',         # Scheduling problems
        'allocate',         # Resource allocation
        'optimize',         # General optimization
        'sample',           # Bayesian sampling
        'plan',             # Planning with constraints
        'route',            # Routing/TSP problems
    }
    
    CLASSIC_INTENTS = {
        'query',            # SQL queries
        'execute',          # Shell commands
        'deploy',           # Docker/K8s
        'transform',        # Data transformation
    }
    
    def route(self, intent: str, complexity: float) -> str:
        """
        Decide solver type based on intent and complexity.
        
        Returns: 'classic' | 'langevin' | 'hybrid'
        """
        if intent in self.THERMODYNAMIC_INTENTS:
            if complexity > 0.7:
                return 'langevin'
            else:
                return 'hybrid'  # Langevin + classic verification
        else:
            return 'classic'
```

### 4. Parallel Orchestrator

```python
# src/nlp2cmd/thermodynamic/orchestrator.py

class ThermodynamicOrchestrator:
    """
    Orchestrates parallel execution of multiple samplers.
    
    Key features:
    - Parallel sampling (setki agentów)
    - Majority voting across samples
    - Energy-based ranking
    - Entropy production monitoring
    """
    
    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents
        self.executor = ThreadPoolExecutor(max_workers=32)
    
    async def solve_parallel(
        self,
        problem: Problem,
        n_parallel: int = 8,
        voting: str = 'energy'  # 'energy' | 'majority' | 'best'
    ) -> Solution:
        """
        Solve problem with parallel samplers.
        
        1. Dispatch to n_parallel agents
        2. Collect solutions
        3. Vote/select best
        """
        # Parallel execution
        futures = []
        for i in range(n_parallel):
            agent = self.select_agent(problem)
            future = self.executor.submit(agent.solve, problem, seed=i)
            futures.append(future)
        
        # Collect results
        solutions = [f.result() for f in as_completed(futures)]
        
        # Vote
        if voting == 'energy':
            # Select lowest energy solution
            return min(solutions, key=lambda s: s.energy)
        elif voting == 'majority':
            # Select most common solution
            return self.majority_vote(solutions)
        else:
            # Select best by custom metric
            return max(solutions, key=lambda s: s.score)
    
    def estimate_energy_savings(
        self,
        problem: Problem,
        classic_tokens: int,
        langevin_steps: int
    ) -> dict:
        """
        Estimate energy savings vs pure LLM approach.
        
        Classic LLM: ~1-5J per 1000 tokens (GPU inference)
        Langevin (digital): ~0.1-0.5J per 1000 steps
        Langevin (analog): ~0.001-0.01J per 1000 steps (theoretical)
        """
        llm_energy = classic_tokens * 0.003  # ~3mJ per token
        langevin_digital = langevin_steps * 0.0003  # ~0.3mJ per step
        langevin_analog = langevin_steps * 0.00001  # ~0.01mJ per step (future)
        
        return {
            'llm_only': llm_energy,
            'hybrid_digital': llm_energy * 0.1 + langevin_digital,
            'hybrid_analog': llm_energy * 0.1 + langevin_analog,
            'savings_digital': (llm_energy - (llm_energy * 0.1 + langevin_digital)) / llm_energy,
            'savings_analog': (llm_energy - (llm_energy * 0.1 + langevin_analog)) / llm_energy,
        }
```

### 5. Entropy Production Regularizer

```python
# src/nlp2cmd/thermodynamic/regularizer.py

class EntropyProductionRegularizer:
    """
    Regularizer based on Whitelam's principle:
    
    L = -E[log P(ω̃)] + λ E[Q(ω̃)]
    
    Where Q is heat (entropy production) along trajectory.
    Lower entropy production = more reversible = better generative quality.
    """
    
    def __init__(self, lambda_entropy: float = 0.1):
        self.lambda_entropy = lambda_entropy
    
    def compute_loss(
        self,
        log_prob: torch.Tensor,
        trajectory: torch.Tensor,
        energy_model: EnergyModel
    ) -> torch.Tensor:
        """
        Compute regularized loss.
        
        Args:
            log_prob: Log probability of generated samples
            trajectory: Full sampling trajectory
            energy_model: Energy function
        
        Returns:
            Regularized loss = -log_prob + λ * entropy_production
        """
        # Standard generative loss
        generative_loss = -log_prob.mean()
        
        # Entropy production along trajectory
        entropy_prod = self._estimate_entropy_production(trajectory, energy_model)
        
        return generative_loss + self.lambda_entropy * entropy_prod
    
    def _estimate_entropy_production(
        self,
        trajectory: torch.Tensor,
        energy_model: EnergyModel
    ) -> torch.Tensor:
        """
        Estimate entropy production (heat dissipation).
        
        For overdamped Langevin:
        σ = (1/kT) ∫ F·v dt ≈ Σ (∇V · Δz) / kT
        """
        sigma = 0.0
        for t in range(len(trajectory) - 1):
            dz = trajectory[t+1] - trajectory[t]
            grad_V = energy_model.gradient(trajectory[t])
            sigma += torch.sum(grad_V * dz)
        return sigma / self.kT
```

---

## 📋 Nowa Lista Ulepszeń (z Thermodynamic Framework)

### 🔴 KRYTYCZNE (Core Thermodynamic)

| # | Feature | Opis | Priorytet |
|---|---------|------|-----------|
| 1 | **LangevinSampler** | Core sampler z dynamiką Langevina | P0 |
| 2 | **EnergyModels** | Modele energii dla różnych domen (scheduling, allocation, planning) | P0 |
| 3 | **ThermodynamicRouter** | Router decydujący: classic vs Langevin | P0 |
| 4 | **ParallelOrchestrator** | Zrównoleglenie samplerów | P0 |

### 🟡 WAŻNE (Energy Efficiency)

| # | Feature | Opis | Priorytet |
|---|---------|------|-----------|
| 5 | **EntropyRegularizer** | Regularizacja przez produkcję entropii | P1 |
| 6 | **EnergyEstimator** | Szacowanie zużycia energii (LLM vs Langevin) | P1 |
| 7 | **HybridPlanner** | LLM formalizuje, Langevin rozwiązuje | P1 |
| 8 | **BatchSampling** | Batch processing dla wielu problemów | P1 |

### 🟢 ROZSZERZENIA (Domain Agents)

| # | Feature | Opis | Priorytet |
|---|---------|------|-----------|
| 9 | **SchedulingAgent** | Agent do harmonogramowania (Langevin-based) | P2 |
| 10 | **AllocationAgent** | Agent do alokacji zasobów | P2 |
| 11 | **RoutingAgent** | Agent TSP/VRP z EBM | P2 |
| 12 | **BayesianSampler** | Posterior sampling dla inference | P2 |
| 13 | **LatentGenerator** | Generacja w przestrzeni latent (multimodal) | P2 |

### 🔵 PRZYSZŁOŚĆ (Hardware Integration)

| # | Feature | Opis | Priorytet |
|---|---------|------|-----------|
| 14 | **AnalogInterface** | Interface do hardware analogowego | P3 |
| 15 | **EdgeDeployment** | Deployment na edge devices | P3 |
| 16 | **FPGABackend** | FPGA accelerator dla Langevin | P3 |

---

## 🧮 Szacowanie Oszczędności Energii

### Scenariusz: Planowanie z ograniczeniami

**Klasyczne podejście (pure LLM):**
```
- Input: 500 tokenów (opis problemu)
- Output: 2000 tokenów (reasoning + solution)
- Total: 2500 tokenów
- Energia: 2500 × 3mJ = 7.5J
```

**Podejście Whitelam/Bielik:**
```
- LLM (formalizacja): 500 + 200 = 700 tokenów × 3mJ = 2.1J
- Langevin sampling: 5000 kroków × 0.3mJ = 1.5J
- Total: 3.6J
- Oszczędność: 52%
```

**Z hardware analogowym (przyszłość):**
```
- LLM (formalizacja): 2.1J
- Langevin (analog): 5000 kroków × 0.01mJ = 0.05J
- Total: 2.15J
- Oszczędność: 71%
```

---

## 🔄 Przepływ Danych

```
User Input (NL)
     │
     ▼
┌─────────────┐
│   Router    │  ← Klasyfikacja: classic vs thermodynamic
└──────┬──────┘
       │
       ├──────────────────────┬─────────────────────┐
       │                      │                     │
       ▼                      ▼                     ▼
┌─────────────┐        ┌─────────────┐       ┌─────────────┐
│  Classic    │        │  Formalizer │       │   Hybrid    │
│   Agent     │        │   (LLM)     │       │    Mode     │
└──────┬──────┘        └──────┬──────┘       └──────┬──────┘
       │                      │                     │
       │                      ▼                     │
       │               ┌─────────────┐              │
       │               │  Condition  │              │
       │               │     c       │              │
       │               └──────┬──────┘              │
       │                      │                     │
       │         ┌────────────┼────────────┐       │
       │         ▼            ▼            ▼       │
       │   ┌─────────┐  ┌─────────┐  ┌─────────┐  │
       │   │Langevin │  │Langevin │  │Langevin │  │
       │   │Sampler 1│  │Sampler 2│  │Sampler N│  │
       │   └────┬────┘  └────┬────┘  └────┬────┘  │
       │        │            │            │        │
       │        └────────────┼────────────┘        │
       │                     ▼                     │
       │              ┌─────────────┐              │
       │              │   Voting    │              │
       │              │ (Energy/MV) │              │
       │              └──────┬──────┘              │
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                      ┌─────────────┐
                      │  Aggregator │
                      └──────┬──────┘
                             │
                             ▼
                      ┌─────────────┐
                      │   Output    │
                      └─────────────┘
```

---

## 📝 Przykład Użycia

```python
from nlp2cmd import ThermodynamicNLP2CMD
from nlp2cmd.thermodynamic import LangevinSampler, SchedulingEnergy

# Initialize thermodynamic system
nlp = ThermodynamicNLP2CMD(
    llm="bielik-7b",  # For formalization
    samplers={
        'scheduling': LangevinSampler(
            energy_model=SchedulingEnergy(),
            config=LangevinConfig(n_steps=5000, kT=0.1)
        ),
    },
    parallel_workers=8
)

# Solve scheduling problem
result = nlp.solve("""
    Zaplanuj harmonogram 10 zadań na 3 maszyny.
    Każde zadanie trwa 1-4 godziny.
    Maszyna A może pracować 0-8h, B: 8-16h, C: całą dobę.
    Minimalizuj czas zakończenia wszystkich zadań.
""")

# Result contains:
# - solution: dict with task assignments
# - energy: final energy (quality metric)
# - entropy_production: reversibility metric
# - llm_tokens: tokens used by Bielik
# - langevin_steps: steps in sampler
# - energy_savings: estimated vs pure LLM
```

---

## 🎯 Podsumowanie

**Masz rację co do zmiany paradygmatu:**

1. ✅ **Setki wyspecjalizowanych agentów** - każdy z własnym modelem energii
2. ✅ **Orchestracja** - ThermodynamicRouter + ParallelOrchestrator
3. ✅ **Zrównoleglenie** - samplers działają niezależnie
4. ✅ **Optymalizacja zużycia** - LLM tylko formalizuje, ciężar w samplerach

**Kluczowe korzyści:**
- **Energia:** 50-70% oszczędności (z analog hardware nawet więcej)
- **Jakość:** Majority voting + energy-based ranking
- **Skalowalność:** Łatwe dodawanie nowych domain-specific agents
- **Przyszłość:** Gotowość na hardware analogowy

**Ograniczenia:**
- Działa najlepiej dla problemów z ograniczeniami (scheduling, allocation, planning)
- Nie zastępuje LLM dla czystego tekstu (Q&A, chat)
- Wymaga domain-specific energy models
