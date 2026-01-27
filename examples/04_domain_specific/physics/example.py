"""
Fizyka i symulacje - Planowanie eksperymentów i optymalizacja parametrów

Demonstruje użycie NLP2CMD do optymalizacji procesów
badawczych w fizyce i symulacjach.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, run_thermo_demo


async def demo_particle_collision():
    """Planowanie eksperymentów w akceleratorze cząstek."""
    # Planowanie eksperymentów
    result = await run_thermo_demo(
        "Physics - Particle Collision Experiment Scheduling",
        """
        Zaplanuj 24h beam time w akceleratorze:
        - 8 grup badawczych, każda potrzebuje 2-4h
        - Niektóre eksperymenty wymagają specyficznej energii wiązki
        - Zmiana energii zajmuje 30 min
        - Priorytet dla eksperymentów z deadline'em publikacji
        
        Minimalizuj czas na zmiany konfiguracji.
    """,
    )
    
    print(result.decoded_output)
    print(f"\n⚛️ Beam time schedule:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_molecular_dynamics():
    """Optymalizacja parametrów symulacji MD."""
    # Parametry symulacji MD
    result = await run_thermo_demo(
        "Physics - Molecular Dynamics Simulation",
        """
        Optymalizuj parametry symulacji MD wody TIP4P:
        - timestep: 0.5-2.0 fs
        - cutoff radius: 8-12 Å
        - temperature: 298-320 K
        - pressure: 1 atm (NPT ensemble)
        
        Minimalizuj energy drift przy zachowaniu accuracy.
    """,
        leading_newline=True,
    )
    
    print(f"\n🔬 MD simulation parameters:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_telescope_scheduling():
    """Harmonogram obserwacji teleskopowych."""
    # Obserwacje teleskopowe
    result = await run_thermo_demo(
        "Physics - Telescope Observation Scheduling",
        """
        Zaplanuj obserwacje na 8-godzinną noc:
        - 15 obiektów do obserwacji
        - Różne czasy ekspozycji (5-60 min)
        - Niektóre obiekty widoczne tylko w określonych godzinach
        - Minimalizuj czas na przesunięcie teleskopu między obiektami
        - Priorytet dla obiektów bliskich horyzontowi (krótkie okno)
    """,
        leading_newline=True,
    )
    
    print(f"\n🔭 Telescope schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_quantum_computing():
    """Optymalizacja obwodów kwantowych."""
    # Optymalizacja obwodów kwantowych
    result = await run_thermo_demo(
        "Physics - Quantum Circuit Optimization",
        """
        Zoptymalizuj obwód kwantowy dla algorytmu Grovera:
        - 10 qubitów, 20 bramek
        - Czas koherencji: 100 μs
        - Czas bramki: 1 μs
        - Błędy: 0.1% per bramka
        
        Minimalizuj głębokość, maksymalizuj fidelity.
    """,
        leading_newline=True,
    )
    
    print(f"\n⚛️ Quantum circuit optimization:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_climate_modeling():
    """Optymalizacja parametrów modelu klimatu."""
    # Parametry modelu klimatu
    result = await run_thermo_demo(
        "Physics - Climate Model Parameter Optimization",
        """
        Kalibruj parametry modelu klimatu:
        - Cloud cover fraction: 0.3-0.7
        - Albedo: 0.2-0.4
        - Climate sensitivity: 2.0-4.5°C
        - Ocean heat uptake: 0.5-2.0 W/m²/K
        
        Dopasuj do danych obserwacyjnych 1970-2020.
    """,
        leading_newline=True,
    )
    
    print(f"\n🌍 Climate model calibration:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_particle_physics():
    """Analiza danych z fizyki cząstek."""
    # Analiza danych
    result = await run_thermo_demo(
        "Physics - Particle Physics Data Analysis",
        """
        Zoptymalizuj analizę danych z detektora cząstek:
        - 1M zdarzeń, 1000 zmiennych each
        - Cuts: pT > 20 GeV, |η| < 2.5
        - Background suppression: factor 1000
        - Signal efficiency: > 50%
        
        Maksymalizuj significance = S/√(S+B).
    """,
        leading_newline=True,
    )
    
    print(f"\n📊 Particle physics analysis:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def demo_materials_science():
    """Optymalizacja eksperymentów materiałoznawstwa."""
    # Eksperymenty materiałoznawcze
    result = await run_thermo_demo(
        "Physics - Materials Science Experiments",
        """
        Zaplanuj eksperymenty badawcze nowych materiałów:
        - 50 próbek, różne kompozycje
        - Testy: wytrzymałość, twardość, przewodnictwo
        - Czas testu: 2h/próbka
        - 5 maszyn testowych dostępnych
        
        Minimalizuj całkowity czas, optymalizuj wykorzystanie.
    """,
        leading_newline=True,
    )
    
    print(f"\n🔬 Materials science experiments:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def main():
    """Uruchom wszystkie demonstracje fizyki."""
    await demo_particle_collision()
    await demo_molecular_dynamics()
    await demo_telescope_scheduling()
    await demo_quantum_computing()
    await demo_climate_modeling()
    await demo_particle_physics()
    await demo_materials_science()
    
    print("\n" + "=" * 70)
    print("  Physics & Simulations demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
