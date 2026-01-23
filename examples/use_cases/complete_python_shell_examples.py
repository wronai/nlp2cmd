#!/usr/bin/env python3
"""
NLP2CMD - Kompletne przykłady użycia: Python API + Shell Commands

Demonstruje oba sposoby użycia NLP2CMD:
1. Przez Python API (HybridThermodynamicGenerator)
2. Przez komendy shell bezpośrednio

Autor: NLP2CMD Team
Wersja: 1.0.4
"""

import asyncio
import subprocess
import time
from pathlib import Path
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator


def print_separator(title: str):
    """Drukuj ładny separator z tytułem."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(query: str, result: dict, elapsed: float, source: str = "Python API"):
    """Wyświetl wynik w standardowym formacie."""
    print(f"\n📝 Zapytanie: {query}")
    print(f"🔧 Źródło: {source}")
    
    if result['source'] == 'dsl':
        print(f"⚡ Komenda: {result['result'].command}")
        print(f"🎯 Domena: {result['result'].domain}")
        print(f"📊 Pewność: {result['result'].confidence:.2f}")
    else:  # thermodynamic
        print(f"🧪 Rozwiązanie: {result['result'].decoded_output}")
        if result['result'].solution_quality:
            print(f"✅ Wykonalne: {result['result'].solution_quality.is_feasible}")
            print(f"📈 Jakość: {result['result'].solution_quality.optimality_gap:.2f}")
    
    print(f"⏱️  Latencja: {elapsed:.1f}ms")


async def demo_python_api():
    """Demonstracja użycia Python API."""
    print_separator("Python API - Przykłady użycia")
    
    generator = HybridThermodynamicGenerator()
    
    # Przykłady zapytań pokazujące różne scenariusze
    examples = [
        # Proste zapytania → DSL generation
        ("Pokaż użytkowników", "dsl"),
        ("Znajdź pliki .log większe niż 10MB", "dsl"),
        ("Uruchom serwer nginx", "dsl"),
        
        # Optymalizacja → Thermodynamic sampling
        ("Zoptymalizuj przydzielanie zasobów", "thermodynamic"),
        ("Minimalizuj koszty transportu", "thermodynamic"),
        ("Znajdź optymalne ustawienia parametrów", "thermodynamic"),
        
        # Złożone operacje systemowe
        ("Sprawdź stan systemu i zasobów", "dsl"),
        ("Stwórz backup i skompresuj dane", "dsl"),
    ]
    
    print("🐍 Użycie przez Python API:")
    print("from nlp2cmd.generation import HybridThermodynamicGenerator")
    print("generator = HybridThermodynamicGenerator()")
    print("result = await generator.generate('twoje zapytanie')")
    print()
    
    for query, expected_source in examples:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)
        
        # Weryfikacja źródła
        if result['source'] != expected_source:
            print(f"⚠️  Oczekiwano źródła: {expected_source}, otrzymano: {result['source']}")


def demo_shell_commands():
    """Demonstracja komend shell."""
    print_separator("Shell Commands - Bezpośrednie użycie w terminalu")
    
    # Przykłady komend shell z nlp2cmd
    shell_examples = [
        # Podstawowe komendy
        "nlp2cmd 'Pokaż użytkowników'",
        "nlp2cmd 'Znajdź pliki .tmp do usunięcia'",
        "nlp2cmd 'Sprawdź użycie dysku'",
        
        # Z opcjami
        "nlp2cmd --dsl shell 'Uruchom serwer apache'",
        "nlp2cmd --explain 'Zoptymalizuj zużycie pamięci'",
        "nlp2cmd --auto-repair 'Napraw konfigurację nginx'",
        
        # Interaktywny tryb
        "nlp2cmd --interactive",
        
        # Analityczne komendy
        "nlp2cmd analyze-env",
        "nlp2cmd validate config.json",
        "nlp2cmd repair docker-compose.yml --backup",
        
        # Termodynamiczne zapytania
        "nlp2cmd 'Zoptymalizuj rozkład obciążenia'",
        "nlp2cmd 'Minimalizuj czas odpowiedzi serwera'",
    ]
    
    print("💻 Użycie przez komendy shell:")
    print("# Instalacja:")
    print("pip install nlp2cmd")
    print()
    print("# Podstawowe użycie:")
    print("nlp2cmd 'twoje zapytanie w języku naturalnym'")
    print()
    print("# Z opcjami:")
    print("nlp2cmd --dsl shell 'polecenie shell'")
    print("nlp2cmd --dsl sql 'zapytanie SQL'")
    print("nlp2cmd --dsl docker 'komenda Docker'")
    print("nlp2cmd --dsl kubernetes 'komenda K8s'")
    print()
    print("# Tryb interaktywny:")
    print("nlp2cmd --interactive")
    print()
    print("# Analiza środowiska:")
    print("nlp2cmd analyze-env --output environment.json")
    print()
    print("# Walidacja i naprawa plików:")
    print("nlp2cmd validate plik.conf")
    print("nlp2cmd repair plik.conf --backup")
    print()
    print("\n📋 Przykłady komend:")
    
    for cmd in shell_examples:
        print(f"  {cmd}")


async def demo_mixed_usage():
    """Demonstracja mieszanego użycia Python + shell."""
    print_separator("Mieszane użycie - Python + Shell")
    
    print("🔄 Scenariusz: Analiza systemu + optymalizacja")
    print()
    
    # Krok 1: Analiza środowiska przez shell
    print("1️⃣ Analiza środowiska (shell):")
    print("   $ nlp2cmd analyze-env")
    
    try:
        result = subprocess.run(
            ["nlp2cmd", "analyze-env"], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        if result.returncode == 0:
            print("   ✅ Analiza zakończona pomyślnie")
        else:
            print(f"   ⚠️ Błąd: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("   ℹ️ Symulacja wyników analizy środowiska")
        print("   🖥️ System: Linux")
        print("   🛠️ Narzędzia: docker, kubectl, python3")
        print("   📁 Pliki konfiguracyjne: 5 znalezionych")
    
    print()
    
    # Krok 2: Generowanie komend przez Python API
    print("2️⃣ Generowanie komend optymalizacyjnych (Python API):")
    
    generator = HybridThermodynamicGenerator()
    
    optimization_queries = [
        "Zoptymalizuj zużycie pamięci w systemie",
        "Zoptymalizuj przydzielanie CPU dla procesów",
        "Minimalizuj czas odpowiedzi aplikacji",
    ]
    
    for query in optimization_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)
        
        # Krok 3: Wykonanie komendy przez shell
        if result['source'] == 'dsl' and result['result'].command:
            cmd = result['result'].command
            print(f"   🔄 Wykonanie: {cmd}")
            
            # Symulacja wykonania (bez faktycznego uruchamiania)
            print("   ℹ️ Symulacja wykonania komendy...")
            print("   ✅ Komenda wykonana pomyślnie")


def demo_advanced_features():
    """Demonstracja zaawansowanych funkcji."""
    print_separator("Zaawansowane funkcje")
    
    print("🚀 Zaawansowane opcje Python API:")
    print("""
# Z kontekstem środowiska
context = {
    'os': 'linux',
    'shell': 'bash',
    'available_tools': ['docker', 'kubectl'],
    'environment_variables': {'PATH': '/usr/bin:/bin'}
}
result = await generator.generate('zapytanie', context=context)

# Batch processing
queries = ['zapytanie1', 'zapytanie2', 'zapytanie3']
results = await asyncio.gather(*[
    generator.generate(q) for q in queries
])
""")
    
    print("🚀 Zaawansowane opcje Shell:")
    print("""
# Pipeline komend
nlp2cmd 'znajdź logi błędów' | nlp2cmd 'filtruj ostatnie 24h'

# Z pliku wejściowego
nlp2cmd --file queries.txt

# Eksport wyników
nlp2cmd 'analizuj system' --output results.json

# Custom DSL
nlp2cmd --dsl custom 'zapytanie w custom DSL'
""")


async def main():
    """Główna funkcja demonstracyjna."""
    print("🎯 NLP2CMD - Kompletne przykłady użycia")
    print("📚 Python API + Shell Commands")
    print("=" * 80)
    
    start_total = time.time()
    
    # Sekcje demonstracyjne
    await demo_python_api()
    demo_shell_commands()
    await demo_mixed_usage()
    demo_advanced_features()
    
    total_time = (time.time() - start_total) * 1000
    
    print_separator("Podsumowanie")
    print(f"⏱️ Całkowity czas demonstracji: {total_time:.1f}ms")
    print()
    print("✅ Wersja: 1.0.4")
    print("📖 Dokumentacja: https://github.com/wronai/nlp2cmd")
    print("🐛 Bug reports: https://github.com/wronai/nlp2cmd/issues")
    print()
    print("🎉 Dzięki za użycie NLP2CMD!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
