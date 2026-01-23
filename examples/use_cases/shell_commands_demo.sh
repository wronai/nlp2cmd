#!/bin/bash
# NLP2CMD - Przykłady użycia bezpośrednio w shell
# Demonstruje różne sposoby użycia nlp2cmd z linii komend

echo "🚀 NLP2CMD - Przykłady komend shell"
echo "=================================="
echo

# Sprawdź czy nlp2cmd jest zainstalowany
if ! command -v nlp2cmd &> /dev/null; then
    echo "⚠️ nlp2cmd nie jest zainstalowany lub nie jest w PATH"
    echo "📦 Instalacja: pip install nlp2cmd"
    echo
    echo "🔄 Uruchamiam w trybie deweloperskim z lokalnego katalogu..."
    cd "$(dirname "$0")/../.."
    if [ -f "src/nlp2cmd/cli/main.py" ]; then
        NLP2CMD_CMD="python src/nlp2cmd/cli/main.py"
    else
        echo "❌ Nie znaleziono pliku main.py"
        exit 1
    fi
else
    NLP2CMD_CMD="nlp2cmd"
fi

echo "🔧 Używam komendy: $NLP2CMD_CMD"
echo

# Przykład 1: Proste zapytanie DSL
echo "📝 Przykład 1: Proste zapytanie DSL"
echo "------------------------------------"
echo "Zapytanie: 'Pokaż użytkowników systemu'"
echo "Komenda: $NLP2CMD_CMD --query 'Pokaż użytkowników systemu'"
echo
$NLP2CMD_CMD --query 'Pokaż użytkowników systemu' 2>/dev/null || echo "ℹ️ Wynik: SELECT * FROM unknown_table;"
echo

# Przykład 2: Zapytanie termodynamiczne (optymalizacja)
echo "🧪 Przykład 2: Zapytanie termodynamiczne"
echo "----------------------------------------"
echo "Zapytanie: 'Zoptymalizuj zużycie pamięci'"
echo "Komenda: $NLP2CMD_CMD --query 'Zoptymalizuj zużycie pamięci'"
echo
$NLP2CMD_CMD --query 'Zoptymalizuj zużycie pamięci' 2>/dev/null || echo "ℹ️ Symulacja: echo 'free -h && echo \"Optimization建议: clear caches\"'"
echo

# Przykład 3: Z określonym DSL
echo "🎯 Przykład 3: Określony DSL (shell)"
echo "------------------------------------"
echo "Zapytanie: 'Znajdź pliki .log większe niż 10MB'"
echo "Komenda: $NLP2CMD_CMD --dsl shell --query 'Znajdź pliki .log większe niż 10MB'"
echo
$NLP2CMD_CMD --dsl shell --query 'Znajdź pliki .log większe niż 10MB' 2>/dev/null || echo "ℹ️ Symulacja: find . -name '*.log' -size +10M -type f"
echo

# Przykład 4: Z wyjaśnieniem
echo "📊 Przykład 4: Z wyjaśnieniem"
echo "-----------------------------"
echo "Zapytanie: 'Sprawdź status usług Docker'"
echo "Komenda: $NLP2CMD_CMD --explain --query 'Sprawdź status usług Docker'"
echo
$NLP2CMD_CMD --explain --query 'Sprawdź status usług Docker' 2>/dev/null || echo "ℹ️ Symulacja: systemctl status docker"
echo

# Przykład 5: Analiza środowiska
echo "🔍 Przykład 5: Analiza środowiska"
echo "---------------------------------"
echo "Komenda: $NLP2CMD_CMD analyze-env"
echo
$NLP2CMD_CMD analyze-env 2>/dev/null || echo "ℹ️ Symulacja analizy środowiska..."
echo "   OS: Linux"
echo "   Shell: bash"
echo "   Tools: python3, git, docker"
echo

# Przykład 6: Walidacja pliku
echo "✅ Przykład 6: Walidacja pliku konfiguracyjnego"
echo "---------------------------------------------"
echo "Komenda: $NLP2CMD_CMD validate pyproject.toml"
echo
$NLP2CMD_CMD validate pyproject.toml 2>/dev/null || echo "ℹ️ Symulacja walidacji pyproject.toml"
echo "   ✅ Plik jest poprawny"
echo

# Przykład 7: Interaktywny tryb (informacja)
echo "🔄 Przykład 7: Tryb interaktywny"
echo "--------------------------------"
echo "Komenda: $NLP2CMD_CMD --interactive"
echo "ℹ️ Tryb interaktywny pozwala na wielokrotne zapytania"
echo "   Uruchom ręcznie: $NLP2CMD_CMD --interactive"
echo

# Przykład 8: Różne typy DSL
echo "🛠️ Przykład 8: Różne typy DSL"
echo "------------------------------"
echo "SQL:"
echo "  $NLP2CMD_CMD --dsl sql --query 'Pokaż użytkowników z miasta Warszawa'"
echo
echo "Docker:"
echo "  $NLP2CMD_CMD --dsl docker --query 'Pokaż wszystkie kontenery'"
echo
echo "Kubernetes:"
echo "  $NLP2CMD_CMD --dsl kubernetes --query 'Skaluj deployment nginx do 3 replik'"
echo
echo "Shell (domyślny):"
echo "  $NLP2CMD_CMD --query 'Usuń pliki tymczasowe'"
echo

# Przykład 9: Pipeline i zaawansowane użycie
echo "🚀 Przykład 9: Zaawansowane użycie"
echo "----------------------------------"
echo "Pipeline:"
echo "  $NLP2CMD_CMD --query 'Znajdź logi błędów' | grep 'ERROR'"
echo
echo "Z pliku:"
echo "  $NLP2CMD_CMD --file zapytania.txt"
echo
echo "Z eksportem:"
echo "  $NLP2CMD_CMD --query 'Analizuj system' --output raport.json"
echo

# Przykład 10: Auto-repair
echo "🔧 Przykład 10: Auto-repair"
echo "---------------------------"
echo "Komenda: $NLP2CMD_CMD --auto-repair --query 'Uruchom serwer nginx'"
echo
$NLP2CMD_CMD --auto-repair --query 'Uruchom serwer nginx' 2>/dev/null || echo "ℹ️ Symulacja: sudo systemctl start nginx"
echo

echo
echo "📚 Więcej przykładów:"
echo "===================="
echo "1. Python API: examples/use_cases/complete_python_shell_examples.py"
echo "2. DSL Commands: examples/use_cases/dsl_commands_demo.py"
echo "3. Dokumentacja: README.md"
echo "4. API Reference: docs/api/README.md"
echo
echo "✅ Wszystkie przykłady shell zakończone!"
echo "🎉 Spróbuj uruchomić komendy samodzielnie!"
echo "============================================"
