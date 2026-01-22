"""
Energia i Utilities - Optymalizacja systemów energetycznych

Demonstruje użycie NLP2CMD do optymalizacji procesów
w energetyce i utilities.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_unit_commitment():
    start_time = time.time()
    """Harmonogramowanie pracy elektrowni (Unit Commitment)."""
    print("=" * 70)
    print("  Energy - Power Plant Scheduling (Unit Commitment)")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Unit commitment problem
    result = await thermo.generate("""
        Zaplanuj pracę 10 bloków energetycznych na 24h:
        - 3x węglowe (500 MW, slow ramp)
        - 4x gazowe (200 MW, fast ramp)
        - 2x wodne (100 MW, instant)
        - 1x jądrowa (1000 MW, must-run)
        
        Prognoza zapotrzebowania: peak 2500 MW o 19:00
        Minimalizuj koszty paliwa i emisję CO2.
    """)
    
    print(result.decoded_output)
    print(f"\n⚡ Generation schedule metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_renewable_integration():
    start_time = time.time()
    """Integracja OZE z siecią."""
    print("\n" + "=" * 70)
    print("  Energy - Renewable Energy Integration")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Integracja OZE
    result = await thermo.generate("""
        Zoptymalizuj wykorzystanie OZE w regionie:
        - Farmy wiatrowe: 500 MW (zmienna produkcja)
        - Farmy PV: 300 MW (tylko dzień)
        - Magazyny energii: 100 MWh
        - Elektrownie szczytowe: 200 MW
        
        Prognoza wiatru i słońca na 48h dostępna.
        Maksymalizuj udział OZE, minimalizuj curtailment.
    """)
    
    print(f"\n🌬️ Renewable integration:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_water_distribution():
    start_time = time.time()
    """Optymalizacja sieci wodociągowej."""
    print("\n" + "=" * 70)
    print("  Energy - Water Distribution Network")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Sieć wodociągowa
    result = await thermo.generate("""
        Zoptymalizuj pracę 5 pompowni w sieci wodociągowej:
        - Zapotrzebowanie zmienne w ciągu doby
        - Zbiorniki wyrównawcze (pojemność 10,000 m³)
        - Taryfy energii: tańsza nocą
        - Min ciśnienie w sieci: 3 bar
        
        Minimalizuj koszty energii, zapewnij ciągłość dostaw.
    """)
    
    print(f"\n💧 Water distribution:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_gas_network():
    start_time = time.time()
    """Optymalizacja sieci gazowej."""
    print("\n" + "=" * 70)
    print("  Energy - Gas Network Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Sieć gazowa
    result = await thermo.generate("""
        Zoptymalizuj przesył gazu w sieci:
        - 1000 km rurociągów, 5 stacji kompresorowych
        - Zapotrzebowanie: zimą 500 MCM/h, latem 200 MCM/h
        - Magazyny gazu: 200 MCM pojemności
        - Kontrakty długoterminowe: 300 MCM/dzień
        
        Minimalizaj koszty kompresji, zapewnij stabilność.
    """)
    
    print(f"\n🔥 Gas network optimization:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_electric_vehicle_charging():
    start_time = time.time()
    """Zarządzanie stacjami ładowania EV."""
    print("\n" + "=" * 70)
    print("  Energy - EV Charging Station Management")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Ładowanie EV
    result = await thermo.generate("""
        Zoptymalizuj ładowanie 1000 pojazdów elektrycznych:
        - 50 stacji ładowania (10x fast 150kW, 40x slow 22kW)
        - Ceny energii: dynamiczne (0.3-1.5 PLN/kWh)
        - Zapotrzebowanie: 20-60 kWh per pojazd
        - Czas ładowania: 30 min (fast), 4h (slow)
        
        Minimalizuj koszty, unikaj przeciążenia sieci.
    """)
    
    print(f"\n🔋 EV charging schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_demand_response():
    start_time = time.time()
    """Programy Demand Response."""
    print("\n" + "=" * 70)
    print("  Energy - Demand Response Programs")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Demand response
    result = await thermo.generate("""
        Zaprojektuj program Demand Response:
        - 10,000 uczestników, max 100 MW redukcji
        - Wyzwalanie: szczyt obciążenia, awarie sieci
        - Incentywy: 2 PLN/kWh za redukcję
        - Segmenty: przemysł, handel, gospodarstwa domowe
        
        Maksymalizuj udział, minimalizuj koszty programu.
    """)
    
    print(f"\n📊 Demand response program:")
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_microgrid():
    start_time = time.time()
    """Optymalizacja mikrosieci."""
    print("\n" + "=" * 70)
    print("  Energy - Microgrid Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Mikrosieć
    result = await thermo.generate("""
        Zoptymalizuj mikrosieć przemysłową:
        - PV: 2 MW, wiatr: 1 MW, baterie: 5 MWh
        - Zapotrzebowanie: 1.5 MW (dzienne), 0.3 MW (nocne)
        - Koszty energii z sieci: 0.8 PLN/kWh
        - Możliwość sprzedaży nadwyżek: 0.6 PLN/kWh
        
        Minimalizuj koszty, maksymalizuj autokonsumpcję.
    """)
    
    start_time = time.time()
    print(f"\n🏭 Microgrid operation:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")


async def main():
    """Uruchom wszystkie demonstracje energetyczne."""
    await demo_unit_commitment()
    await demo_renewable_integration()
    await demo_water_distribution()
    await demo_gas_network()
    await demo_electric_vehicle_charging()
    await demo_demand_response()
    await demo_microgrid()
    
    print("\n" + "=" * 70)
    print("  Energy & Utilities demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
