"""
Fizyka i symulacje - Planowanie eksperymentów i optymalizacja parametrów

Demonstruje użycie NLP2CMD do optymalizacji procesów
badawczych w fizyce i symulacjach.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_particle_collision():
    start_time = time.time()
    """Planowanie eksperymentów w akceleratorze cząstek."""
    print("=" * 70)
    print("  Physics - Particle Collision Experiment Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Planowanie eksperymentów
    result = await thermo.generate("""
        Zaplanuj 24h beam time w akceleratorze:
        - 8 grup badawczych, każda potrzebuje 2-4h
        - Niektóre eksperymenty wymagają specyficznej energii wiązki
        - Zmiana energii zajmuje 30 min
        - Priorytet dla eksperymentów z deadline'em publikacji
        
        Minimalizuj czas na zmiany konfiguracji.
    """)
    
    print(result.decoded_output)
    print(f"\n⚛️ Beam time schedule:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_molecular_dynamics():
    start_time = time.time()
    """Optymalizacja parametrów symulacji MD."""
    print("\n" + "=" * 70)
    print("  Physics - Molecular Dynamics Simulation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Parametry symulacji MD
    result = await thermo.generate("""
        Optymalizuj parametry symulacji MD wody TIP4P:
        - timestep: 0.5-2.0 fs
        - cutoff radius: 8-12 Å
        - temperature: 298-320 K
        - pressure: 1 atm (NPT ensemble)
        
        Minimalizuj energy drift przy zachowaniu accuracy.
    """)
    
    print(f"\n🔬 MD simulation parameters:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_telescope_scheduling():
    start_time = time.time()
    """Harmonogram obserwacji teleskopowych."""
    print("\n" + "=" * 70)
    print("  Physics - Telescope Observation Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Obserwacje teleskopowe
    result = await thermo.generate("""
        Zaplanuj obserwacje na 8-godzinną noc:
        - 15 obiektów do obserwacji
        - Różne czasy ekspozycji (5-60 min)
        - Niektóre obiekty widoczne tylko w określonych godzinach
        - Minimalizuj czas na przesunięcie teleskopu między obiektami
        - Priorytet dla obiektów bliskich horyzontowi (krótkie okno)
    """)
    
    print(f"\n🔭 Telescope schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_quantum_computing():
    start_time = time.time()
    """Optymalizacja obwodów kwantowych."""
    print("\n" + "=" * 70)
    print("  Physics - Quantum Circuit Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja obwodów kwantowych
    result = await thermo.generate("""
        Zoptymalizuj obwód kwantowy dla algorytmu Grovera:
        - 10 qubitów, 20 bramek
        - Czas koherencji: 100 μs
        - Czas bramki: 1 μs
        - Błędy: 0.1% per bramka
        
        Minimalizuj głębokość, maksymalizuj fidelity.
    """)
    
    print(f"\n⚛️ Quantum circuit optimization:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_climate_modeling():
    start_time = time.time()
    """Optymalizacja parametrów modelu klimatu."""
    print("\n" + "=" * 70)
    print("  Physics - Climate Model Parameter Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Parametry modelu klimatu
    result = await thermo.generate("""
        Kalibruj parametry modelu klimatu:
        - Cloud cover fraction: 0.3-0.7
        - Albedo: 0.2-0.4
        - Climate sensitivity: 2.0-4.5°C
        - Ocean heat uptake: 0.5-2.0 W/m²/K
        
        Dopasuj do danych obserwacyjnych 1970-2020.
    """)
    
    print(f"\n🌍 Climate model calibration:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_particle_physics():
    start_time = time.time()
    """Analiza danych z fizyki cząstek."""
    print("\n" + "=" * 70)
    print("  Physics - Particle Physics Data Analysis")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Analiza danych
    result = await thermo.generate("""
        Zoptymalizuj analizę danych z detektora cząstek:
        - 1M zdarzeń, 1000 zmiennych each
        - Cuts: pT > 20 GeV, |η| < 2.5
        - Background suppression: factor 1000
        - Signal efficiency: > 50%
        
        Maksymalizuj significance = S/√(S+B).
    """)
    
    print(f"\n📊 Particle physics analysis:")
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_materials_science():
    start_time = time.time()
    """Optymalizacja eksperymentów materiałoznawstwa."""
    print("\n" + "=" * 70)
    print("  Physics - Materials Science Experiments")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Eksperymenty materiałoznawcze
    result = await thermo.generate("""
        Zaplanuj eksperymenty badawcze nowych materiałów:
        - 50 próbek, różne kompozycje
        - Testy: wytrzymałość, twardość, przewodnictwo
        - Czas testu: 2h/próbka
        - 5 maszyn testowych dostępnych
        
        Minimalizuj całkowity czas, optymalizuj wykorzystanie.
    """)
    
    start_time = time.time()
    print(f"\n🔬 Materials science experiments:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")


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
