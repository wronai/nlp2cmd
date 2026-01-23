# Plan Refaktoryzacji Projektu nlp2cmd

## 1. Moduły z dużą liczbą funkcji (>20) - WYSOKI PRIORYTET

### Moduły testowe requiring refactoring:
- [ ] `tests/iterative/test_iter_2_regex.py` - 41 funkcji → Podział na moduły: test_extraction, test_postprocessing, test_accuracy
- [ ] `tests/iterative/test_iter_3_templates.py` - 43 funkcji → Podział na: test_sql_templates, test_shell_templates, test_docker_templates, test_k8s_templates
- [ ] `tests/iterative/test_iter_1_keywords.py` - 40 funkcji → Podział na: test_sql_keywords, test_shell_keywords, test_docker_keywords, test_k8s_keywords
- [ ] `tests/unit/test_validators_comprehensive.py` - 49 funkcji → Podział na: test_sql_validators, test_shell_validators, test_docker_validators, test_k8s_validators
- [ ] `tests/unit/test_schemas_comprehensive.py` - 43 funkcji → Podział na: test_schema_loading, test_schema_validation, test_schema_management
- [ ] `tests/unit/test_core_comprehensive.py` - 34 funkcji → Podział na: test_execution_plan, test_transform_result, test_nlp_integration

### Moduły produkcyjne:
- [ ] `termo2.py` - 29 funkcji → Podział na osobne pliki dla każdego problemu optymalizacyjnego
- [ ] `tests/conftest.py` - 19 funkcji → Podział na moduły: fixtures/adapters.py, fixtures/docker.py, fixtures/k8s.py, fixtures/sql.py

## 2. Funkcje z dużą liczbą linii (>50) - ŚREDNI PRIORYTET

- [ ] `demo_thermodynamic_improved` w `termo_demo.py` - 46 linii → Ekstrakcja metod: setup_demo(), run_demo(), analyze_results()
- [ ] `demo_hybrid_thermodynamic_improved` w `termo_demo.py` - 47 linii → Podział na mniejsze funkcje
- [ ] `benchmark_latency` w `termo_demo.py` - 44 linii → Ekstrakcja: setup_benchmark(), run_tests(), analyze_performance()
- [ ] `bump_version` w `bump_version.py` - 45 linii → Podział na: read_version(), update_version(), write_version()
- [ ] `sample_k8s_deployment` w `tests/conftest.py` - 34 linii → Ekstrakcja do fixtures/k8s.py

## 3. Funkcje z wysoką złożonością cyklomatyczną (CC > 10) - ŚREDNI PRIORYTET

- [ ] `VRPSolver.solve` w `termo2.py` - CC=9 → Ekstrakcja: calculate_distances(), perturb_routes(), check_feasibility()
- [ ] `ORScheduler.schedule` w `termo2.py` - CC=9 → Ekstrakcja: check_compatibility(), assign_surgeries(), optimize_schedule()
- [ ] `UnitCommitmentSolver.solve` w `termo2.py` - CC=6 → Ekstrakcja: calculate_demand(), allocate_units(), optimize_cost()
- [ ] `GenomicPipelineScheduler.schedule` w `termo2.py` - CC=5 → Ekstrakcja: estimate_resources(), check_dependencies(), create_schedule()

## 4. Eliminacja duplikacji kodu - ŚREDNI PRIORYTET

### Testy:
- [ ] Stworzenie `tests/base/test_base_adapter.py` z wspólnymi metodami testowymi
- [ ] Stworzenie `tests/base/test_base_generator.py` dla generatorów
- [ ] Użycie parametryzowanych testów dla podobnych przypadków

### Adaptery DSL:
- [ ] Stworzenie `src/nlp2cmd/adapters/common/base_command_generator.py`
- [ ] Wydzielenie logiki walidacji do `src/nlp2cmd/adapters/common/validators.py`
- [ ] Stworzenie wspólnych utilities w `src/nlp2cmd/adapters/common/utils.py`

## 5. Reorganizacja modułów - NISKI PRIORYTET

### Monitoring:
- [ ] Połączenie `resources.py` i `token_costs.py` w `monitoring/metrics.py`
- [ ] Stworzenie interfejsu `MetricCollector` w `monitoring/interfaces.py`

### Termo2.py refactoring:
- [ ] `termo2/hyperparameter_optimization.py` - klasa HyperparameterOptimizer
- [ ] `termo2/vehicle_routing.py` - klasa VRPSolver
- [ ] `termo2/or_scheduling.py` - klasa ORScheduler
- [ ] `termo2/unit_commitment.py` - klasa UnitCommitmentSolver
- [ ] `termo2/genomic_pipeline.py` - klasa GenomicPipelineScheduler
- [ ] `termo2/base_solver.py` - wspólna klasa bazowa

## 6. Poprawki strukturalne - NISKI PRIORYTET

- [ ] Stworzenie `src/nlp2cmd/common/` dla wspólnych utilities
- [ ] Dodanie type hints do wszystkich funkcji publicznych
- [ ] Poprawa dokumentacji docstring w kluczowych modułach
- [ ] Dodanie bardziej szczegółowych error messages

## 7. Testy regresji - WYSOKI PRIORYTET

- [ ] Stworzenie testów regresji przed refaktoryzacją
- [ ] Uruchomienie pełnego zestawu testów po każdej zmianie
- [ ] Dodanie testów coverage dla nowych modułów

## 8. Harmonogram

### Tydzień 1-2: Moduły testowe
- Podział dużych plików testowych
- Stworzenie klas bazowych testów
- Migracja testów do nowych struktur

### Tydzień 3-4: Funkcje produkcyjne
- Refaktoryzacja długich funkcji
- Podział termo2.py na mniejsze moduły
- Redukcja złożoności cyklomatycznej

### Tydzień 5: Eliminacja duplikacji
- Stworzenie wspólnych utilities
- Refaktoryzacja adapterów
- Poprawa modułów monitoringu

### Tydzień 6: Finalizacja
- Testy regresji
- Poprawki dokumentacji
- Code review i optymalizacje

## 9. Metryki sukcesu

- [ ] Żaden moduł nie ma >20 funkcji
- [ ] Żadna funkcja nie ma >50 linii
- [ ] Złożoność cyklomatyczna <10 dla wszystkich funkcji
- [ ] Coverage testów >90%
- [ ] Brak duplikacji kodu (wykryte przez tools)

## 10. Ryzyka

- **Ryzyko:** Breaking changes w API
- **Mitigacja:** Zachowanie backward compatibility, wersjonowanie API

- **Ryzyko:** Regresja w funkcjonalności
- **Mitigacja:** Kompleksowe testy regresji, stopniowe wdrażanie

- **Ryzyko:** Zwiększenie złożoności budowy
- **Mitigacja:** Dobra dokumentacja, clear migration path
