# 📋 NLP2CMD - Lista Zadań (TODO)

**Wersja:** 0.3.0 (Thermodynamic Edition)  
**Data aktualizacji:** 2026-01-22  
**Status:** 488 testów ✅ | 75 plików | 21K+ linii kodu

---

## 🎯 Priorytety Wersji

| Wersja | Cel | Status |
|--------|-----|--------|
| v0.1.0 | Core DSL Adapters | ✅ DONE |
| v0.2.0 | LLM Planner Architecture | ✅ DONE |
| v0.3.0 | Thermodynamic Computing | ✅ DONE |
| v0.4.0 | LLM Integration | 🔄 IN PROGRESS |
| v0.5.0 | MCP Protocol | 📅 PLANNED |
| v1.0.0 | Production Ready | 📅 PLANNED |

---

## ✅ UKOŃCZONE (v0.1.0 - v0.3.0)

### Core Framework
- [x] DSL Adapters (SQL, Shell, Docker, Kubernetes, DQL)
- [x] Schema Registry (11 formatów plików)
- [x] Validators (Syntax, SQL, Shell, Docker, K8s)
- [x] Environment Analyzer
- [x] Feedback Loop System
- [x] CLI Interface

### LLM Planner Architecture (v0.2.0)
- [x] Decision Router
- [x] Action Registry (19 akcji)
- [x] Plan Executor (foreach, variables, conditions)
- [x] LLM Planner (stub)
- [x] Result Aggregator

### Infrastructure (v0.2.0)
- [x] Docker multi-stage build
- [x] docker-compose (6 serwisów)
- [x] E2E Test Suite (77 testów)
- [x] Makefile (30+ komend)

### Thermodynamic Computing (v0.3.0)
- [x] Langevin Sampler
- [x] Energy Models (Quadratic, Constraint)
- [x] Domain Energy Models (Scheduling, Allocation, Routing)
- [x] Thermodynamic Router
- [x] Majority Voter (energy, entropy, cluster)
- [x] Energy Estimator
- [x] Entropy Production Regularizer
- [x] 26 testów termodynamicznych

---

## 🔴 v0.4.0 - LLM Integration (NASTĘPNA)

### P0: Krytyczne

- [ ] **LLM Adapter Interface**
  - [ ] Abstract LLMProvider class
  - [ ] Request/Response models
  - [ ] Streaming support
  - [ ] Token counting

- [ ] **OpenAI Integration**
  - [ ] GPT-4 / GPT-4o adapter
  - [ ] Function calling support
  - [ ] Structured outputs (JSON mode)
  - [ ] Retry logic + rate limiting

- [ ] **Anthropic Integration**
  - [ ] Claude adapter
  - [ ] Tool use support
  - [ ] Extended thinking

- [ ] **Local LLM Support**
  - [ ] Ollama adapter
  - [ ] vLLM adapter
  - [ ] Bielik-7B integration

### P1: Ważne

- [ ] **Multi-turn Self-Correction**
  - [ ] Execute → Validate → Correct loop
  - [ ] Max turns configuration
  - [ ] Domain-specific error hints
  - [ ] Early stopping on success

- [ ] **Majority Voting Enhancement**
  - [ ] K-sample generation
  - [ ] Semantic clustering
  - [ ] Confidence scoring
  - [ ] Cost-aware voting

- [ ] **Chain-of-Thought Reasoning**
  - [ ] Structured reasoning format
  - [ ] Step-by-step decomposition
  - [ ] Reasoning traces in output

---

## 🟠 v0.3.x/v0.4.x - Lightweight NLP (Regex → NLP) (IN PROGRESS)

Cel: stopniowo zastąpić `KeywordIntentDetector` + `RegexEntityExtractor` lekkim NLP (preferowany: `spaCy` bez ciężkich modeli), **bez utraty wydajności** i z bezpiecznym fallbackiem do obecnych reguł.

### P0: Minimalny PoC (Shell / find) (1-2 dni)
- [ ] **Feature flag + wiring**
  - [ ] `NLP2CMD_SEMANTIC_NLP=1` włącza nowy backend tylko dla `--dsl shell`
  - [ ] brak spaCy / błąd inicjalizacji → fallback do `RuleBasedBackend`
  - [ ] `NLP2CMD_SPACY_MODEL` pozwala wybrać model (domyślnie: `spacy.blank('pl')`)

- [ ] **Semantic backend (light)**
  - [ ] `SemanticShellBackend(NLPBackend)` generuje `ExecutionPlan(intent='file_search', ...)`
  - [ ] ekstrakcja: `path`, `size` (+ operator), `age/mtime` (+ operator), `extension`
  - [ ] obsługa PL porównań:
    - [ ] `większe/mniejsze niż`, `powyżej/poniżej`, `nie większe niż`
    - [ ] `starsze/nowsze niż`, `ostatnio zmienione`
  - [ ] confidence score + heurystyki (np. wykryto size+unit => high)

- [ ] **Regresje krytyczne (smoke)**
  - [ ] `Znajdź pliki większe niż 1MB` → `-size +1M` i bez `*.większe`
  - [ ] `Znajdź pliki mniejsze niż 10KB` → `-size -10K`
  - [ ] `Znajdź logi starsze niż 7 dni` → `-mtime +7` + `-name '*.log'`

### P1: spaCy textcat jako lekki klasyfikator intencji (2-4 dni)
- [ ] **Autogeneracja datasetu z `adapter.INTENTS.patterns`**
  - [ ] `patterns` jako pozytywne przykłady (PL+EN)
  - [ ] balansowanie klas + proste augmentacje

- [ ] **Trenowanie i zapis małego modelu textcat**
  - [ ] artefakt modelu w `data/models/textcat_shell/` (lub cache user-level)
  - [ ] warmup + cache embeddingów

- [ ] **Backend wyboru intencji**
  - [ ] jeśli textcat confidence >= threshold → intent z textcat
  - [ ] inaczej → fallback do rule-based

### P2: ONNX (opcjonalnie, jeśli textcat nadal zbyt wolny/ciężki)
- [ ] **Opcjonalny runtime ONNX**
  - [ ] `onnxruntime` jako extra
  - [ ] eksport prostego klasyfikatora intencji do ONNX
  - [ ] benchmark: cold/warm latency + memory

### P3: Rozszerzenie na inne domeny
- [ ] Docker/Kubernetes: logi, nazwy zasobów, namespace, kontener
- [ ] SQL: tabela/kolumny/where (z zachowaniem obecnych heurystyk)

### Kryteria sukcesu
- [ ] Latencja warm dla prostych zapytań: <30ms (shell)
- [ ] Brak regresji w przypadkach krytycznych (większe/mniejsze/starsze/negacje)
- [ ] Feature-flag pozwala bezpiecznie wyłączyć NLP i wrócić do regexów

---

## 🟡 v0.5.0 - MCP Protocol

### P0: Krytyczne

- [ ] **MCP Server**
  - [ ] Tool definitions export
  - [ ] Tool execution endpoint
  - [ ] Resource management
  - [ ] Sampling support

- [ ] **MCP Client**
  - [ ] Tool discovery
  - [ ] Tool invocation
  - [ ] Server management

### P1: Ważne

- [ ] **Streaming Output**
  - [ ] AsyncIterator for results
  - [ ] WebSocket support
  - [ ] Progress callbacks

- [ ] **Plugin System**
  - [ ] Plugin manifest format
  - [ ] Dynamic loading
  - [ ] Plugin registry

---

## 🟢 v0.6.0 - Scale & Performance

### Action Registry Expansion
- [ ] Git actions (commit, push, branch, merge, rebase)
- [ ] HTTP/REST actions (GET, POST, PUT, DELETE, PATCH)
- [ ] File system actions (read, write, copy, move, delete)
- [ ] Cloud actions (AWS CLI, GCP, Azure)
- [ ] Database actions (migrations, backups, restore)
- [ ] Monitoring actions (Prometheus, Grafana)
- [ ] CI/CD actions (GitHub Actions, GitLab CI)
- [ ] Message queue actions (RabbitMQ, Kafka)

### Telemetry & Observability
- [ ] OpenTelemetry spans
- [ ] Prometheus metrics
- [ ] Structured logging (JSON)
- [ ] Dashboard templates

### Performance
- [ ] Caching layer (Redis/Memory)
- [ ] Batch processing
- [ ] Connection pooling
- [ ] Lazy loading

---

## 🔵 v1.0.0 - Production Ready

### GUI
- [ ] Web UI (React/Vue)
- [ ] Visual plan builder
- [ ] Execution dashboard
- [ ] History viewer

### Enterprise Features
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Cost estimation & budgets
- [ ] Usage analytics

### Documentation
- [ ] API reference (auto-generated)
- [ ] Tutorial series
- [ ] Video demos
- [ ] Deployment guides

### Quality
- [ ] 95%+ test coverage
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Accessibility compliance

---

## 🔬 v1.1.0+ - Thermodynamic Hardware (Future)

### Analog Computing Interface
- [ ] FPGA backend for Langevin
- [ ] Analog hardware driver
- [ ] Calibration tools
- [ ] Energy monitoring

### Edge Deployment
- [ ] ARM optimization
- [ ] Quantized models
- [ ] Offline mode
- [ ] Low-power mode

---

## 📊 Metryki Sukcesu

| Metryka | Obecna (v0.3.0) | Cel v0.4.0 | Cel v1.0.0 |
|---------|-----------------|------------|------------|
| Testy | 488 | 600 | 1000+ |
| Pokrycie kodu | ~75% | 85% | 95% |
| Akcje w Registry | 19 | 30 | 100+ |
| Wspierane LLM | 0 | 4 | 10+ |
| Linie kodu | 21K | 30K | 50K+ |
| Dokumentacja | 2.5K linii | 5K | 15K+ |

---

## 🐛 Znane Problemy

1. **LLMPlanner** - obecnie stub, wymaga integracji z prawdziwym LLM
2. **Thermodynamic Router** - brak automatycznej klasyfikacji problemu
3. **Energy Models** - gradient numeryczny (wolny), potrzebny analityczny
4. **Parallel Sampling** - brak GPU acceleration

---

## 💡 Pomysły do Rozważenia

1. **Thermodynamic Fine-tuning** - użycie entropy production jako loss
2. **Hybrid Analog-Digital** - część obliczeń na FPGA
3. **Federated Sampling** - rozproszone samplery na wielu maszynach
4. **Auto-Energy Model** - automatyczne uczenie funkcji energii z danych
5. **Whitelam Training** - trening przez reverse trajectory matching

---

## 📅 Timeline

```
2026-01        v0.3.0 Thermodynamic ✅
2026-02        v0.4.0 LLM Integration
2026-03        v0.5.0 MCP Protocol
2026-Q2        v0.6.0 Scale & Performance
2026-Q3        v1.0.0 Production Ready
2026-Q4        v1.1.0 Thermodynamic Hardware
```
