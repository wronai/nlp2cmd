"""
Logistyka i Supply Chain - VRP i optymalizacja magazynowa

Demonstruje użycie NLP2CMD do rozwiązywania problemów
logistycznych i optymalizacji łańcucha dostaw.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_vehicle_routing():
    start_time = time.time()
    """Optymalizacja tras dostaw (VRP)."""
    print("=" * 70)
    print("  Logistyka - Vehicle Routing Problem (VRP)")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja tras dostaw
    result = await thermo.generate("""
        Zaplanuj trasy dla 5 pojazdów dostawczych:
        - 30 punktów dostawy w Warszawie
        - Pojemność każdego pojazdu: 100 paczek
        - Okna czasowe dostaw (np. 9:00-12:00)
        - Minimalizuj całkowity dystans i liczbę pojazdów
    """)
    
    print(result.decoded_output)
    print(f"\n📊 Routing metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_warehouse_optimization():
    start_time = time.time()
    """Optymalizacja rozmieszczenia produktów w magazynie."""
    print("\n" + "=" * 70)
    print("  Logistyka - Warehouse Slot Allocation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja rozmieszczenia w magazynie
    result = await thermo.generate("""
        Przydziel 500 SKU do 1000 lokalizacji w magazynie:
        - Produkty fast-moving blisko strefy pakowania
        - Produkty ciężkie na dolnych półkach
        - Produkty często kupowane razem blisko siebie
        - Produkty niebezpieczne w wydzielonej strefie
        
        Minimalizuj średni czas kompletacji zamówienia.
    """)
    
    print(f"\n📦 Warehouse layout:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_production_scheduling():
    start_time = time.time()
    """Harmonogramowanie produkcji."""
    print("\n" + "=" * 70)
    print("  Logistyka - Production Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Harmonogramowanie produkcji
    result = await thermo.generate("""
        Zaplanuj produkcję na 5 liniach przez tydzień:
        - 20 różnych produktów
        - Różne czasy przezbrojenia między produktami
        - Minimalne partie produkcyjne
        - Terminy realizacji zamówień (deadlines)
        
        Minimalizuj opóźnienia i czas przezbrojeń.
    """)
    
    print(f"\n🏭 Production schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_inventory_optimization():
    start_time = time.time()
    """Optymalizacja zapasów."""
    print("\n" + "=" * 70)
    print("  Logistyka - Inventory Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja poziomów zapasów
    result = await thermo.generate("""
        Zoptymalizuj zapasy dla 100 produktów:
        - Koszt utrzymania: 15% wartości rocznie
        - Koszt zamówienia: 50 PLN per zamówienie
        - Koszt braku towaru: 200% wartości
        - Lead time: 2-14 dni w zależności od dostawcy
        
        Minimalizuj całkowity koszt przy 95% service level.
    """)
    
    print(f"\n📊 Inventory policy:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_supply_chain_network():
    start_time = time.time()
    """Optymalizacja sieci łańcucha dostaw."""
    print("\n" + "=" * 70)
    print("  Logistyka - Supply Chain Network Design")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Projektowanie sieci dostaw
    result = await thermo.generate("""
        Zaprojektuj sieć dystrybucji dla Polski:
        - 3 centra dystrybucyjne (Warszawa, Kraków, Gdańsk)
        - 50 miast docelowych
        - Koszty transportu: 0.5 PLN/km
        - Koszty magazynowania: 10 PLN/m²/miesiąc
        - Czas dostawy: max 48h
        
        Minimalizuj całkowity koszt przy zachowaniu SLA.
    """)
    
    print(f"\n🌐 Supply chain network:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_cross_docking():
    start_time = time.time()
    """Optymalizacja cross-docking."""
    print("\n" + "=" * 70)
    print("  Logistyka - Cross-Docking Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja cross-dock
    result = await thermo.generate("""
        Zoptymalizuj operacje cross-dock:
        - 2 doki przyjęcia, 4 doki wysyłki
        - 100 przesyłek dziennie
        - Czas przeładunku: 15 min
        - Pojazdy przyjeżdżają co 30 min
        
        Minimalizuj czas przeładunku i kolejkowanie.
    """)
    
    print(f"\n🚚 Cross-docking operations:")
    start_time = time.time()
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def main():
    """Uruchom wszystkie demonstracje logistyczne."""
    await demo_vehicle_routing()
    await demo_warehouse_optimization()
    await demo_production_scheduling()
    await demo_inventory_optimization()
    await demo_supply_chain_network()
    await demo_cross_docking()
    
    print("\n" + "=" * 70)
    print("  Logistics demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
