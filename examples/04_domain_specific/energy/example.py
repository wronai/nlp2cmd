"""
Energia i Utilities - Optymalizacja systemów energetycznych

Demonstruje użycie NLP2CMD do optymalizacji procesów
w energetyce i utilities.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo


async def demo_unit_commitment():
    """Harmonogramowanie pracy elektrowni (Unit Commitment)."""
    # Unit commitment problem
    result = await run_thermo_demo(
        "Energy - Power Plant Scheduling (Unit Commitment)",
        """
        Zaplanuj pracę 10 bloków energetycznych na 24h:
        - 3x węglowe (500 MW, slow ramp)
        - 4x gazowe (200 MW, fast ramp)
        - 2x wodne (100 MW, instant)
        - 1x jądrowa (1000 MW, must-run)
        
        Prognoza zapotrzebowania: peak 2500 MW o 19:00
        Minimalizuj koszty paliwa i emisję CO2.
    """,
    )
    
    print(result.decoded_output)
    print(f"\n⚡ Generation schedule metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_renewable_integration():
    """Integracja OZE z siecią."""
    # Integracja OZE
    result = await run_thermo_demo(
        "Energy - Renewable Energy Integration",
        """
        Zoptymalizuj wykorzystanie OZE w regionie:
        - Farmy wiatrowe: 500 MW (zmienna produkcja)
        - Farmy PV: 300 MW (tylko dzień)
        - Magazyny energii: 100 MWh
        - Elektrownie szczytowe: 200 MW
        
        Prognoza wiatru i słońca na 48h dostępna.
        Maksymalizuj udział OZE, minimalizuj curtailment.
    """,
        leading_newline=True,
    )
    
    print(f"\n🌬️ Renewable integration:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_water_distribution():
    """Optymalizacja sieci wodociągowej."""
    # Sieć wodociągowa
    result = await run_thermo_demo(
        "Energy - Water Distribution Network",
        """
        Zoptymalizuj pracę 5 pompowni w sieci wodociągowej:
        - Zapotrzebowanie zmienne w ciągu doby
        - Zbiorniki wyrównawcze (pojemność 10,000 m³)
        - Taryfy energii: tańsza nocą
        - Min ciśnienie w sieci: 3 bar
        
        Minimalizuj koszty energii, zapewnij ciągłość dostaw.
    """,
        leading_newline=True,
    )
    
    print(f"\n💧 Water distribution:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_gas_network():
    """Optymalizacja sieci gazowej."""
    # Sieć gazowa
    result = await run_thermo_demo(
        "Energy - Gas Network Optimization",
        """
        Zoptymalizuj przesył gazu w sieci:
        - 1000 km rurociągów, 5 stacji kompresorowych
        - Zapotrzebowanie: zimą 500 MCM/h, latem 200 MCM/h
        - Magazyny gazu: 200 MCM pojemności
        - Kontrakty długoterminowe: 300 MCM/dzień
        
        Minimalizaj koszty kompresji, zapewnij stabilność.
    """,
        leading_newline=True,
    )
    
    print(f"\n🔥 Gas network optimization:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_electric_vehicle_charging():
    """Zarządzanie stacjami ładowania EV."""
    # Ładowanie EV
    result = await run_thermo_demo(
        "Energy - EV Charging Station Management",
        """
        Zoptymalizuj ładowanie 1000 pojazdów elektrycznych:
        - 50 stacji ładowania (10x fast 150kW, 40x slow 22kW)
        - Ceny energii: dynamiczne (0.3-1.5 PLN/kWh)
        - Zapotrzebowanie: 20-60 kWh per pojazd
        - Czas ładowania: 30 min (fast), 4h (slow)
        
        Minimalizuj koszty, unikaj przeciążenia sieci.
    """,
        leading_newline=True,
    )
    
    print(f"\n🔋 EV charging schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_demand_response():
    """Programy Demand Response."""
    # Demand response
    result = await run_thermo_demo(
        "Energy - Demand Response Programs",
        """
        Zaprojektuj program Demand Response:
        - 10,000 uczestników, max 100 MW redukcji
        - Wyzwalanie: szczyt obciążenia, awarie sieci
        - Incentywy: 2 PLN/kWh za redukcję
        - Segmenty: przemysł, handel, gospodarstwa domowe
        
        Maksymalizuj udział, minimalizuj koszty programu.
    """,
        leading_newline=True,
    )
    
    print(f"\n📊 Demand response program:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def demo_microgrid():
    """Optymalizacja mikrosieci."""
    # Mikrosieć
    result = await run_thermo_demo(
        "Energy - Microgrid Optimization",
        """
        Zoptymalizuj mikrosieć przemysłową:
        - PV: 2 MW, wiatr: 1 MW, baterie: 5 MWh
        - Zapotrzebowanie: 1.5 MW (dzienne), 0.3 MW (nocne)
        - Koszty energii z sieci: 0.8 PLN/kWh
        - Możliwość sprzedaży nadwyżek: 0.6 PLN/kWh
        
        Minimalizuj koszty, maksymalizuj autokonsumpcję.
    """,
        leading_newline=True,
    )
    
    print(f"\n🏭 Microgrid operation:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def main():
    """Uruchom wszystkie demonstracje energetyczne."""
    await demo_unit_commitment()
    await demo_renewable_integration()
    await demo_water_distribution()
    await demo_gas_network()
    await demo_electric_vehicle_charging()
    await demo_demand_response()
    await demo_microgrid()

    print_separator("Energy & Utilities demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
