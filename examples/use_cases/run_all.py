"""
NLP2CD Use Cases - Uruchom wszystkie demonstracje

Ten skrypt uruchamia wszystkie przykłady zastosowań NLP2CMD
w różnych dziedzinach: IT, nauce, biznesie.
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do importów
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Importy wszystkich modułów demonstracyjnych
from devops_automation import main as devops_main
from dsl_commands_demo import main as dsl_main
from shell_validation import main as validation_main
from data_science_ml import main as ds_main
from bioinformatics import main as bio_main
from logistics_supply_chain import main as logistics_main
from finance_trading import main as finance_main
from healthcare import main as healthcare_main
from education import main as education_main
from smart_cities import main as smart_cities_main
from energy_utilities import main as energy_main
from physics_simulations import main as physics_main


async def run_all_demos():
    """Uruchom wszystkie demonstracje."""
    print("🚀 NLP2CMD - Kompletny zestaw demonstracji")
    print("=" * 70)
    print("Przykłady zastosowań w IT, nauce i biznesie")
    print("=" * 70)
    
    demos = [
        ("Shell DSL Commands", dsl_main),
        ("IT & DevOps", devops_main),
        ("Data Science & ML", ds_main),
        ("Bioinformatyka", bio_main),
        ("Logistyka & Supply Chain", logistics_main),
        ("Finanse & Trading", finance_main),
        ("Medycyna & Healthcare", healthcare_main),
        ("Edukacja", education_main),
        ("Smart Cities & IoT", smart_cities_main),
        ("Energia & Utilities", energy_main),
        ("Fizyka & Symulacje", physics_main),
    ]
    
    total_time = 0
    successful_demos = 0
    
    for name, demo_func in demos:
        print(f"\n{'='*70}")
        print(f"  Uruchamianie: {name}")
        print(f"{'='*70}")
        
        try:
            import time
            start_time = time.time()
            
            await demo_func()
            
            elapsed = time.time() - start_time
            total_time += elapsed
            successful_demos += 1
            
            print(f"\n✅ {name} ukończone (czas: {elapsed:.1f}s)")
            
        except Exception as e:
            print(f"\n❌ Błąd w {name}: {str(e)}")
            continue
        
        # Przerwa między demonstracjami (usunięta)
        if demos.index((name, demo_func)) < len(demos) - 1:
            print("\n" + "-"*50)
            # input("Naciśnij Enter, aby kontynuować do następnej demonstracji...")
    
    # Podsumowanie
    print(f"\n{'='*70}")
    print("  PODSUMOWANIE WSZYSTKICH DEMONSTRACJI")
    print(f"{'='*70}")
    print(f"Ukończone: {successful_demos}/{len(demos)} demonstracji")
    print(f"Całkowity czas: {total_time:.1f} sekund")
    print(f"Średni czas: {total_time/successful_demos:.1f} sekund/demo")
    
    if successful_demos == len(demos):
        print("\n🎉 Wszystkie demonstracje ukończone pomyślnie!")
    else:
        print(f"\n⚠️  {len(demos) - successful_demos} demonstracji nie ukończone")
    
    print(f"\n{'='*70}")


def print_summary_table():
    """Wyświetl tabelę podsumowującą zastosowania."""
    print("\n📊 TABELA ZASTOSOWAŃ NLP2CMD")
    print("=" * 70)
    
    applications = [
        ("IT & DevOps", "Scheduling, Automation", "80% redukcja pracy manualnej"),
        ("Data Science", "Hyperparameter opt.", "Szybsza konwergencja modeli"),
        ("Bioinformatyka", "Pipeline scheduling", "10x szybsza analiza"),
        ("Logistyka", "VRP, Warehouse", "20-30% redukcja kosztów"),
        ("Finanse", "Portfolio opt.", "Lepszy risk-adjusted return"),
        ("Medycyna", "OR scheduling", "15% więcej operacji"),
        ("Edukacja", "Timetabling", "Zero konfliktów"),
        ("Smart Cities", "Traffic, Grid", "20% redukcja zatorów"),
        ("Energia", "Unit commitment", "10% redukcja kosztów"),
        ("Fizyka", "Experiment scheduling", "Maks. wykorzystanie beam time"),
    ]
    
    print(f"{'Dziedzina':<20} {'Typ problemu':<25} {'Główna korzyść':<25}")
    print("-" * 70)
    
    for domain, problem_type, benefit in applications:
        print(f"{domain:<20} {problem_type:<25} {benefit:<25}")


if __name__ == "__main__":
    print("🚀 NLP2CD Use Cases - Kompletny zestaw demonstracji")
    print("\nDostępne opcje:")
    print("  python run_all.py          - Uruchom wszystkie demonstracje")
    print("  python run_all.py --summary - Pokaż tylko tabelę zastosowań")
    
    if "--summary" in sys.argv:
        print_summary_table()
    else:
        asyncio.run(run_all_demos())
        print_summary_table()
