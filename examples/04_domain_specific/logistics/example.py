"""
Logistyka i Supply Chain - VRP i optymalizacja magazynowa

Demonstruje użycie NLP2CMD do rozwiązywania problemów
logistycznych i optymalizacji łańcucha dostaw.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo


async def demo_vehicle_routing():
    """Optymalizacja tras dostaw (VRP)."""
    # Optymalizacja tras dostaw
    result = await run_thermo_demo(
        "Logistyka - Vehicle Routing Problem (VRP)",
        """
        Zaplanuj trasy dla 5 pojazdów dostawczych:
        - 30 punktów dostawy w Warszawie
        - Pojemność każdego pojazdu: 100 paczek
        - Okna czasowe dostaw (np. 9:00-12:00)
        - Minimalizuj całkowity dystans i liczbę pojazdów
    """,
    )
    
    print(result.decoded_output)
    print(f"\n📊 Routing metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_warehouse_optimization():
    """Optymalizacja rozmieszczenia produktów w magazynie."""
    # Optymalizacja rozmieszczenia w magazynie
    result = await run_thermo_demo(
        "Logistyka - Warehouse Slot Allocation",
        """
        Przydziel 500 SKU do 1000 lokalizacji w magazynie:
        - Produkty fast-moving blisko strefy pakowania
        - Produkty ciężkie na dolnych półkach
        - Produkty często kupowane razem blisko siebie
        - Produkty niebezpieczne w wydzielonej strefie
        
        Minimalizuj średni czas kompletacji zamówienia.
    """,
        leading_newline=True,
    )
    
    print(f"\n📦 Warehouse layout:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_production_scheduling():
    """Harmonogramowanie produkcji."""
    # Harmonogramowanie produkcji
    result = await run_thermo_demo(
        "Logistyka - Production Scheduling",
        """
        Zaplanuj produkcję na 5 liniach przez tydzień:
        - 20 różnych produktów
        - Różne czasy przezbrojenia między produktami
        - Minimalne partie produkcyjne
        - Terminy realizacji zamówień (deadlines)
        
        Minimalizuj opóźnienia i czas przezbrojeń.
    """,
        leading_newline=True,
    )
    
    print(f"\n🏭 Production schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_inventory_optimization():
    """Optymalizacja zapasów."""
    # Optymalizacja poziomów zapasów
    result = await run_thermo_demo(
        "Logistyka - Inventory Optimization",
        """
        Zoptymalizuj zapasy dla 100 produktów:
        - Koszt utrzymania: 15% wartości rocznie
        - Koszt zamówienia: 50 PLN per zamówienie
        - Koszt braku towaru: 200% wartości
        - Lead time: 2-14 dni w zależności od dostawcy
        
        Minimalizuj całkowity koszt przy 95% service level.
    """,
        leading_newline=True,
    )
    
    print(f"\n📊 Inventory policy:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_supply_chain_network():
    """Optymalizacja sieci łańcucha dostaw."""
    # Projektowanie sieci dostaw
    result = await run_thermo_demo(
        "Logistyka - Supply Chain Network Design",
        """
        Zaprojektuj sieć dystrybucji dla Polski:
        - 3 centra dystrybucyjne (Warszawa, Kraków, Gdańsk)
        - 50 miast docelowych
        - Koszty transportu: 0.5 PLN/km
        - Koszty magazynowania: 10 PLN/m²/miesiąc
        - Czas dostawy: max 48h
        
        Minimalizuj całkowity koszt przy zachowaniu SLA.
    """,
        leading_newline=True,
    )
    
    print(f"\n🌐 Supply chain network:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_cross_docking():
    """Optymalizacja cross-docking."""
    # Optymalizacja cross-dock
    result = await run_thermo_demo(
        "Logistyka - Cross-Docking Optimization",
        """
        Zoptymalizuj operacje cross-dock:
        - 2 doki przyjęcia, 4 doki wysyłki
        - 100 przesyłek dziennie
        - Czas przeładunku: 15 min
        - Pojazdy przyjeżdżają co 30 min
        
        Minimalizuj czas przeładunku i kolejkowanie.
    """,
        leading_newline=True,
    )
    
    print(f"\n🚚 Cross-docking operations:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def main():
    """Uruchom wszystkie demonstracje logistyczne."""
    await demo_vehicle_routing()
    await demo_warehouse_optimization()
    await demo_production_scheduling()
    await demo_inventory_optimization()
    await demo_supply_chain_network()
    await demo_cross_docking()

    print_separator("Logistics demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
