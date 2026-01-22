"""
Smart Cities & IoT - Optymalizacja systemów miejskich

Demonstruje użycie NLP2CMD do optymalizacji procesów
w inteligentnych miastach i systemach IoT.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_traffic_optimization():
    start_time = time.time()
    """Optymalizacja sygnalizacji świetlnej."""
    print("=" * 70)
    print("  Smart Cities - Traffic Light Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja świateł
    result = await thermo.generate("""
        Zoptymalizuj cykle świateł na 20 skrzyżowaniach:
        - Dane o natężeniu ruchu (7:00-9:00 szczyt poranny)
        - Koordynacja "zielonej fali" na głównej arterii
        - Priorytet dla transportu publicznego
        - Min czas zielony dla pieszych: 15s
        
        Minimalizuj średni czas przejazdu przez miasto.
    """)
    
    print(result.decoded_output)
    print(f"\n🚦 Traffic metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_smart_grid():
    start_time = time.time()
    """Bilansowanie obciążenia sieci energetycznej."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Smart Grid Load Balancing")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Smart grid optimization
    result = await thermo.generate("""
        Zbalansuj obciążenie sieci Smart Grid:
        - 10,000 gospodarstw domowych
        - 500 prosumentów z panelami PV
        - 200 stacji ładowania EV
        - Szczyt wieczorny: 18:00-21:00
        
        Zaplanuj:
        - Ładowanie EV (przesuń poza szczyt)
        - Rozładowanie magazynów energii
        - Dynamic pricing dla demand response
        
        Minimalizuj peak load i koszty.
    """)
    
    print(f"\n⚡ Smart grid schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_waste_management():
    start_time = time.time()
    """Optymalizacja tras wywozu odpadów."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Waste Collection Routing")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja wywozu odpadów
    result = await thermo.generate("""
        Zaplanuj trasy 10 śmieciarek na tydzień:
        - 500 punktów odbioru (różna częstotliwość)
        - Pojemność: 10 ton
        - Godziny pracy: 6:00-14:00
        - Unikaj centrum w godzinach szczytu
        - Smart bins z czujnikami wypełnienia
        
        Minimalizuj dystans i emisję CO2.
    """)
    
    print(f"\n🗑️ Waste collection routes:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_public_transport():
    start_time = time.time()
    """Optymalizacja transportu publicznego."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Public Transport Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja transportu publicznego
    result = await thermo.generate("""
        Zoptymalizuj sieć autobusową:
        - 20 linii autobusowych, 100 autobusów
        - 200 przystanków, 50,000 pasażerów dziennie
        - Częstotliwość: co 10-30 min w szczycie, co 60 min poza
        - Koszt przejazdu: 3 PLN, budżet: 100,000 PLN/dzień
        
        Maksymalizuj pokrycie, minimalizaj czas podróży.
    """)
    
    print(f"\n🚌 Public transport network:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_parking_management():
    start_time = time.time()
    """Zarządzanie parkingami."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Parking Management")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Zarządzanie parkingami
    result = await thermo.generate("""
        Zoptymalizuj system parkingowy:
        - 5 parkingów, 2000 miejsc
        - Strefy: centrum (10 PLN/h), peryferia (2 PLN/h)
        - Rezerwacje online, dynamic pricing
        - 5000 kierowców dziennie, 80% obłożenie w szczycie
        
        Maksymalizaj wykorzystanie, minimalizuj szukanie miejsc.
    """)
    
    print(f"\n🅿️ Parking system:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_air_quality():
    start_time = time.time()
    """Monitorowanie i optymalizacja jakości powietrza."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Air Quality Management")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Jakość powietrza
    result = await thermo.generate("""
        Zoptymalizuj sieć monitoringu jakości powietrza:
        - 50 czujników PM2.5, PM10, NO2, O3
        - Koszt czujnika: 5000 PLN, budżet: 200,000 PLN
        - Priorytet: strefy przemysłowe, szkoły, szpitale
        - Czas aktualizacji: 5 min
        
        Maksymalizuj pokrycie obszarów wysokiego ryzyka.
    """)
    
    print(f"\n🌬️ Air quality monitoring:")
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_water_management():
    start_time = time.time()
    """Zarządzanie systemem wodociągowym."""
    print("\n" + "=" * 70)
    print("  Smart Cities - Water Management System")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Zarządzanie wodą
    result = await thermo.generate("""
        Zoptymalizuj system wodociągowy:
        - 100 km rurociągów, 10 stacji pomp
        - 50,000 mieszkańców, 15,000 m³/dzień
        - Czujniki ciśnienia i przepływu co 1 min
        - Wykrywanie wycieków, predykcja popytu
        
        Minimalizuj straty wody, zapewnij ciągłość dostaw.
    """)
    
    start_time = time.time()
    print(f"\n💧 Water management system:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")


async def main():
    """Uruchom wszystkie demonstracje smart cities."""
    await demo_traffic_optimization()
    await demo_smart_grid()
    await demo_waste_management()
    await demo_public_transport()
    await demo_parking_management()
    await demo_air_quality()
    await demo_water_management()
    
    print("\n" + "=" * 70)
    print("  Smart Cities demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
