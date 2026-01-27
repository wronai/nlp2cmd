# Prosty Makefile dla NLP2CMD Examples

## Jak używać?

### Uruchom pojedynczą grupę przykładów:
```bash
make 01_basics          # Podstawowe przykłady
make 02_benchmarks      # Testy wydajności
make 03_integrations    # Integracje
make 04_domain_specific # Przykłady domenowe
make 05_advanced_features # Zaawansowane funkcje
make 06_tools_and_utilities # Narzędzia
```

### Uruchom WSZYSTKIE przykłady:
```bash
make all
```

### Pokaż listę wszystkich przykładów:
```bash
make list
```

### Wyczyść pliki tymczasowe:
```bash
make clean
```

### Pokaż pomoc:
```bash
make help
```

## UWAGA

Przykłady wymagają zainstalowanych modułów:
- `nlp2cmd` - główny moduł
- `app2schema` - do generowania schematów
- Inne zależności według potrzeb

Aby uruchomić przykłady, upewnij się że masz zainstalowane wszystkie wymagane pakiety.
