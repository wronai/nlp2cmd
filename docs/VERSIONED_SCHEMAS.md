# Zarządzanie Wersjami Schematów Komend

Ten dokument wyjaśnia jak system przechowuje i zarządza wieloma wersjami schematów komend.

## Struktura Przechowywania

```
versioned_schemas/
├── commands/           # Aktywne wersje (domyślne)
│   ├── find.json      # Aktualnie aktywna wersja find
│   ├── docker.json    # Aktualnie aktywna wersja docker
│   └── ...
├── versions/          # Wszystkie wersje
│   ├── find/
│   │   ├── 1.0.0.json
│   │   ├── 1.1.0.json
│   │   └── 2.0.0.json
│   ├── docker/
│   │   ├── 1.0.0.json
│   │   └── 2.0.0.json
│   └── ...
├── categories/        # Indeksy kategorii
├── index.json         # Główny indeks
└── active_versions.json # Mapa aktywnych wersji
```

## Przykład: Różne Wersje Komendy

### Find v1.0.0 - Podstawowa wersja
```json
{
  "command": "find",
  "version": "1.0.0",
  "description": "Search for files",
  "template": "find {path} -name '{pattern}'",
  "examples": [
    "find . -name '*.py'",
    "find /home -type f"
  ]
}
```

### Find v1.1.0 - Z filtrami rozmiaru i czasu
```json
{
  "command": "find",
  "version": "1.1.0",
  "description": "Search for files with size and time constraints",
  "template": "find {path} -name '{pattern}' -size {size} -mtime {mtime}",
  "examples": [
    "find . -name '*.py'",
    "find /home -size +100M -mtime -7",
    "find . -mtime -30 -name '*.log'"
  ],
  "metadata": {
    "features": ["size_filter", "time_filter"]
  }
}
```

### Find v2.0.0 - Z regex i exec
```json
{
  "command": "find",
  "version": "2.0.0",
  "description": "Advanced file search with regex and exec capabilities",
  "template": "find {path} -{options} -{regex} -name '{pattern}' -exec {exec}",
  "examples": [
    "find . -regex '.*\\.py$'",
    "find /tmp -type f -exec rm -f {} \\;",
    "find . -name '*.log' -mtime +30 -exec gzip {} \\;"
  ],
  "metadata": {
    "breaking_changes": true,
    "features": ["regex", "exec"]
  }
}
```

## Użycie w Praktyce

### 1. Inicjalizacja z wersjonowaniem
```python
from nlp2cmd.storage.versioned_store import VersionedSchemaStore

# Utwórz magazyn z wersjonowaniem
store = VersionedSchemaStore("./my_command_schemas")

# Wczytaj istniejące schematy
registry = DynamicSchemaRegistry(
    use_per_command_storage=True,
    storage_dir="./my_command_schemas"
)
```

### 2. Dodawanie nowej wersji
```python
# Stwórz nową wersję schematu
new_version = ExtractedSchema(
    source="docker",
    commands=[...]
)

# Zapisz jako nową wersję
store.store_schema_version(new_version, "2.1.0", make_active=True)
```

### 3. Przełączanie między wersjami
```python
# Lista dostępnych wersji
versions = store.list_versions("docker")
# ['1.0.0', '2.0.0', '2.1.0']

# Ustaw aktywną wersję
store.set_active_version("docker", "2.0.0")

# Załaduj konkretną wersję
schema = store.load_schema_version("docker", "1.0.0")
```

### 4. Porównywanie wersji
```python
# Porównaj dwie wersje
diff = store.compare_versions("docker", "1.0.0", "2.0.0")
print(diff)
# {
#   "changes": {
#     "description": True,
#     "template": True,
#     "parameters": True
#   },
#   "parameter_changes": [
#     "Added parameter: orchestration",
#     "Changed required for action: False -> True"
#   ]
# }
```

## Scenariusze Użycia

### Scenariusz 1: Różne wersje na różnych maszynach
```python
# Sprawdź zainstalowaną wersję komendy
def get_installed_version(command):
    # W rzeczywistości: subprocess.run([command, '--version'])
    return "2.0.0"  # Symulacja

# Dostosuj schemat do wersji
docker_version = get_installed_version("docker")
store.set_active_version("docker", docker_version)

# Użyj odpowiedniego schematu
schema = store.load_schema_version("docker")
```

### Scenariusz 2: Migracja z nowszymi funkcjami
```python
# Stara wersja
old_schema = store.load_schema_version("kubectl", "1.18.0")

# Nowa wersja z nowymi funkcjami
new_schema = ExtractedSchema(
    source="kubectl",
    commands=[CommandSchema(
        name="kubectl",
        description="Kubernetes control with new features",
        examples=[
            "kubectl get pods",  # Stare
            "kubectl get pods --sort-by=.metadata.creationTimestamp",  # Nowe
        ]
    )]
)

# Zapisz jako nową wersję
store.store_schema_version(new_schema, "1.20.0")
```

### Scenariusz 3: Wsparcie dla wielu systemów
```python
# Różne argumenty dla różnych systemów
if system == "macos":
    # BSD wersja komend
    ls_schema = create_bsd_ls_schema()
    store.store_schema_version(ls_schema, "bsd-1.0.0")
elif system == "linux":
    # GNU wersja komend
    ls_schema = create_gnu_ls_schema()
    store.store_schema_version(ls_schema, "gnu-1.0.0")

# Wybierz odpowiednią wersję
version = "bsd-1.0.0" if system == "macos" else "gnu-1.0.0"
store.set_active_version("ls", version)
```

## Najlepsze Praktyki

### 1. Numerowanie Wersji
- Użyj semantycznego versioningu (semver): `MAJOR.MINOR.PATCH`
- `MAJOR`: zmiany breaking compatibility
- `MINOR`: nowe funkcje, wsteczna kompatybilność
- `PATCH`: poprawki błędów

### 2. Dokumentacja Zmian
```json
{
  "metadata": {
    "version": "2.0.0",
    "changelog": [
        "Added support for swarm mode",
        "Deprecated old API endpoints",
        "Breaking: changed parameter structure"
    ],
    "migration_guide": {
      "from": "1.x",
      "notes": "Update your scripts to use new parameter names"
    }
  }
}
```

### 3. Testowanie Kompatybilności
```python
def test_version_compatibility(old_version, new_version):
    """Test if new version is backward compatible."""
    old_schema = store.load_schema_version("docker", old_version)
    new_schema = store.load_schema_version("docker", new_version)
    
    # Sprawdź czy stare przykłady jeszcze działają
    for example in old_schema.commands[0].examples:
        if not validate_with_new_schema(example, new_schema):
            print(f"Warning: {example} may not work with v{new_version}")
```

### 4. Automatyczna Aktualizacja
```python
def auto_update_schema(command, new_help_text):
    """Automatically update schema if help text changed."""
    current = store.load_schema_version(command)
    new = extract_schema_from_help(new_help_text)
    
    if detect_significant_changes(current, new):
        # Automatycznie zwiększ wersję
        last_version = store.list_versions(command)[-1]
        next_version = increment_version(last_version)
        
        store.store_schema_version(new, next_version, make_active=True)
        print(f"Updated {command} to v{next_version}")
```

## Podsumowanie

System wersjonowania schematów pozwala na:
- ✅ Przechowywanie wielu wersji tej samej komendy
- ✅ Łatwe przełączanie między wersjami
- ✅ Porównywanie zmian między wersjami
- ✅ Dostosowywanie do środowiska
- ✅ Migrację z zachowaniem historii
- ✅ Wsparcie dla różnych systemów

Dzięki temu NLP2CMD może obsługiwać różne warianty komend na różnych systemach i wersjach.
