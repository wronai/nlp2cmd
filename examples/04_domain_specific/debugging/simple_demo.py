#!/usr/bin/env python3
"""
NLP2CMD - Przykłady użycia (wersja demonstracyjna)

Pokazuje koncepcje użycia NLP2CMD zarówno przez Python API jak i przez shell.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_separator as _print_separator
from _demo_helpers import print_rule


def print_separator(title):
    """Drukuj separator z tytułem."""
    _print_separator(title, leading_newline=True, width=80)


def demo_python_api_concept():
    """Demonstracja koncepcji Python API."""
    print_separator("Python API - Koncepcja użycia")
    
    print("🐍 Import i inicjalizacja:")
    print("""
from nlp2cmd.generation import HybridThermodynamicGenerator

generator = HybridThermodynamicGenerator()

# Proste zapytanie → DSL generation
result = await generator.generate("Pokaż użytkowników")
# → {'source': 'dsl', 'result': HybridResult(...)}

# Optymalizacja → Thermodynamic sampling  
result = await generator.generate("Zoptymalizuj przydzielanie zasobów")
# → {'source': 'thermodynamic', 'result': ThermodynamicResult(...)}
""")
    
    print("📝 Przykładowe zapytania:")
    
    examples = [
        ("Pokaż użytkowników", "dsl", "who, cut -d: -f1 /etc/passwd"),
        ("Znajdź pliki .log większe niż 10MB", "dsl", "find . -name '*.log' -size +10M"),
        ("Zoptymalizuj zużycie pamięci", "thermodynamic", "free -h && echo 'Optimization: clear caches'"),
        ("Sprawdź status Docker", "dsl", "systemctl status docker"),
        ("Minimalizuj koszty transportu", "thermodynamic", "Linear programming solution"),
    ]
    
    for query, expected_type, sample_output in examples:
        print(f"\n🔍 Zapytanie: {query}")
        print(f"📊 Typ: {expected_type}")
        print(f"⚡ Przykładowy wynik: {sample_output}")


def demo_shell_commands():
    """Demonstracja komend shell."""
    print_separator("Shell Commands - Bezpośrednie użycie")
    
    print("💻 Instalacja:")
    print("pip install nlp2cmd")
    print()
    
    print("🚀 Podstawowe użycie:")
    shell_examples = [
        ("Proste zapytanie", "nlp2cmd --query 'Pokaż użytkowników'"),
        ("Określony DSL", "nlp2cmd --dsl shell --query 'Znajdź pliki .tmp'"),
        ("SQL", "nlp2cmd --dsl sql --query 'SELECT * FROM users WHERE city = \"Warsaw\"'"),
        ("Docker", "nlp2cmd --dsl docker --query 'Pokaż wszystkie kontenery'"),
        ("Kubernetes", "nlp2cmd --dsl kubernetes --query 'Skaluj deployment nginx'"),
        ("Z wyjaśnieniem", "nlp2cmd --explain --query 'Sprawdź status systemu'"),
        ("Auto-repair", "nlp2cmd --auto-repair --query 'Napraw konfigurację'"),
        ("Interaktywny", "nlp2cmd --interactive"),
    ]
    
    for description, command in shell_examples:
        print(f"\n📋 {description}:")
        print(f"   {command}")
    
    print("\n🔍 Analiza środowiska:")
    print("   nlp2cmd analyze-env")
    print("   nlp2cmd analyze-env --output environment.json")
    
    print("\n✅ Walidacja i naprawa:")
    print("   nlp2cmd validate config.json")
    print("   nlp2cmd repair docker-compose.yml --backup")


def demo_mixed_workflow():
    """Demonstracja mieszanego workflow."""
    print_separator("Mieszany Workflow - Python + Shell")
    
    print("🔄 Scenariusz: Optymalizacja systemu")
    print()
    
    print("1️⃣ Krok 1: Analiza środowiska (shell)")
    print("   $ nlp2cmd analyze-env")
    print("   📊 Wynik: System Linux, 8GB RAM, Docker dostępny")
    print()
    
    print("2️⃣ Krok 2: Generowanie rozwiązań (Python)")
    print("""
import asyncio
from nlp2cmd.generation import HybridThermodynamicGenerator

async def optimize_system():
    generator = HybridThermodynamicGenerator()
    
    # Analiza zasobów
    resource_analysis = await generator.generate(
        "Zoptymalizuj zużycie pamięci i CPU"
    )
    
    # Generowanie komend
    cleanup_commands = await generator.generate(
        "Wyczyść niepotrzebne pliki i cache"
    )
    
    return resource_analysis, cleanup_commands
""")
    
    print("3️⃣ Krok 3: Wykonanie komend (shell)")
    print("   $ nlp2cmd 'Wyczyść cache systemowy'")
    print("   $ nlp2cmd 'Uruchom garbage collection'")
    print()
    
    print("4️⃣ Krok 4: Walidacja (shell)")
    print("   $ nlp2cmd analyze-env")
    print("   ✅ Poprawa: 20% mniej zużycia pamięci")


def demo_advanced_patterns():
    """Demonstracja zaawansowanych wzorców."""
    print_separator("Zaawansowane Wzorce Użycia")
    
    print("🚀 Batch Processing (Python):")
    print("""
queries = [
    'Sprawdź status usług',
    'Znajdź duże pliki', 
    'Analizuj logi błędów',
    'Zoptymalizuj konfigurację'
]

results = await asyncio.gather(*[
    generator.generate(q) for q in queries
])
""")
    
    print("🔄 Pipeline (Shell):")
    print("   $ nlp2cmd --query 'Znajdź logi błędów' | grep 'CRITICAL' | wc -l")
    print()
    
    print("📁 Z pliku (Shell):")
    print("   $ echo 'Sprawdź CPU\\nSprawdź pamięć\\nSprawdź dysk' > queries.txt")
    print("   $ nlp2cmd --file queries.txt")
    print()
    
    print("🎯 Kontekstowe zapytania (Python):")
    print("""
context = {
    'environment': 'production',
    'available_tools': ['docker', 'kubectl'],
    'constraints': {'max_memory': '4GB'}
}

result = await generator.generate(
    'Zoptymalizuj deployment',
    context=context
)
""")


def demo_real_world_examples():
    """Demonstracja rzeczywistych przypadków użycia."""
    print_separator("Rzeczywiste Przypadki Użycia")
    
    use_cases = [
        {
            "title": "DevOps Automation",
            "python": """
# Monitorowanie i optymalizacja
status = await generator.generate("Sprawdź status wszystkich usług")
optimization = await generator.generate("Zoptymalizuj konfigurację nginx")
""",
            "shell": "nlp2cmd 'Deploy aplikacji i sprawdź status'"
        },
        {
            "title": "Data Science",
            "python": """
# Analiza danych
analysis = await generator.generate("Znajdź outliery w zbiorze danych")
visualization = await generator.generate("Stwórz wykres rozkładu")
""",
            "shell": "nlp2cmd --dsl sql 'Analizuj trendy sprzedaży z ostatniego miesiąca'"
        },
        {
            "title": "System Administration",
            "python": """
# Zarządzanie systemem
cleanup = await generator.generate("Wyczyść stare logi i pliki tymczasowe")
security = await generator.generate("Sprawdź bezpieczeństwo systemu")
""",
            "shell": "nlp2cmd 'Wykonaj pełną konserwację systemu'"
        }
    ]
    
    for use_case in use_cases:
        print(f"\n🎯 {use_case['title']}:")
        print("Python API:")
        print(use_case['python'])
        print("Shell:")
        print(f"   {use_case['shell']}")


def main():
    """Główna funkcja demonstracyjna."""
    print("🎯 NLP2CMD - Kompletne przykłady użycia")
    print("📚 Python API + Shell Commands")
    print_rule(width=80, char="=")
    
    demo_python_api_concept()
    demo_shell_commands()
    demo_mixed_workflow()
    demo_advanced_patterns()
    demo_real_world_examples()
    
    print_separator("Podsumowanie")
    print("✅ Wersja: 1.0.4")
    print("📖 Dokumentacja: https://github.com/wronai/nlp2cmd")
    print("🚀 Start:")
    print("   Python: from nlp2cmd.generation import HybridThermodynamicGenerator")
    print("   Shell: nlp2cmd 'twoje zapytanie'")
    print()
    print("🎉 Wybierz odpowiedni sposób dla swoich potrzeb!")
    print_rule(width=80, char="=")


if __name__ == "__main__":
    main()
