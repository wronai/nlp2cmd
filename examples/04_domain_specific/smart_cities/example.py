"""
Smart Cities & IoT - Optymalizacja systemów miejskich

Demonstruje użycie NLP2CMD do optymalizacji procesów
w inteligentnych miastach i systemach IoT.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo


async def demo_traffic_optimization():
    """Optymalizacja sygnalizacji świetlnej."""
    # Optymalizacja świateł
    result = await run_thermo_demo(
        "Smart Cities - Traffic Light Optimization",
        """
        Zoptymalizuj cykle świateł na 20 skrzyżowaniach:
        - Dane o natężeniu ruchu (7:00-9:00 szczyt poranny)
        - Koordynacja "zielonej fali" na głównej arterii
        - Priorytet dla transportu publicznego
        - Min czas zielony dla pieszych: 15s
        
        Minimalizuj średni czas przejazdu przez miasto.
    """,
    )
    
    print(result.decoded_output)
    print(f"\n🚦 Traffic metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_smart_grid():
    """Bilansowanie obciążenia sieci energetycznej."""
    # Smart grid optimization
    result = await run_thermo_demo(
        "Smart Cities - Smart Grid Load Balancing",
        """
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
    """,
        leading_newline=True,
    )
    
    print(f"\n⚡ Smart grid schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_waste_management():
    """Optymalizacja tras wywozu odpadów."""
    # Optymalizacja wywozu odpadów
    result = await run_thermo_demo(
        "Smart Cities - Waste Collection Routing",
        """
        Zaplanuj trasy 10 śmieciarek na tydzień:
        - 500 punktów odbioru (różna częstotliwość)
        - Pojemność: 10 ton
        - Godziny pracy: 6:00-14:00
        - Unikaj centrum w godzinach szczytu
        - Smart bins z czujnikami wypełnienia
        
        Minimalizuj dystans i emisję CO2.
    """,
        leading_newline=True,
    )
    
    print(f"\n🗑️ Waste collection routes:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_public_transport():
    """Optymalizacja transportu publicznego."""
    # Optymalizacja transportu publicznego
    result = await run_thermo_demo(
        "Smart Cities - Public Transport Optimization",
        """
        Zoptymalizuj sieć autobusową:
        - 20 linii autobusowych, 100 autobusów
        - 200 przystanków, 50,000 pasażerów dziennie
        - Częstotliwość: co 10-30 min w szczycie, co 60 min poza
        - Koszt przejazdu: 3 PLN, budżet: 100,000 PLN/dzień
        
        Maksymalizuj pokrycie, minimalizaj czas podróży.
    """,
        leading_newline=True,
    )
    
    print(f"\n🚌 Public transport network:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_parking_management():
    """Zarządzanie parkingami."""
    # Zarządzanie parkingami
    result = await run_thermo_demo(
        "Smart Cities - Parking Management",
        """
        Zoptymalizuj system parkingowy:
        - 5 parkingów, 2000 miejsc
        - Strefy: centrum (10 PLN/h), peryferia (2 PLN/h)
        - Rezerwacje online, dynamic pricing
        - 5000 kierowców dziennie, 80% obłożenie w szczycie
        
        Maksymalizaj wykorzystanie, minimalizuj szukanie miejsc.
    """,
        leading_newline=True,
    )
    
    print(f"\n🅿️ Parking system:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_air_quality():
    """Monitorowanie i optymalizacja jakości powietrza."""
    # Jakość powietrza
    result = await run_thermo_demo(
        "Smart Cities - Air Quality Management",
        """
        Zoptymalizuj sieć monitoringu jakości powietrza:
        - 50 czujników PM2.5, PM10, NO2, O3
        - Koszt czujnika: 5000 PLN, budżet: 200,000 PLN
        - Priorytet: strefy przemysłowe, szkoły, szpitale
        - Czas aktualizacji: 5 min
        
        Maksymalizuj pokrycie obszarów wysokiego ryzyka.
    """,
        leading_newline=True,
    )
    
    print(f"\n🌬️ Air quality monitoring:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def demo_water_management():
    """Zarządzanie systemem wodociągowym."""
    # Zarządzanie wodą
    result = await run_thermo_demo(
        "Smart Cities - Water Management System",
        """
        Zoptymalizuj system wodociągowy:
        - 100 km rurociągów, 10 stacji pomp
        - 50,000 mieszkańców, 15,000 m³/dzień
        - Czujniki ciśnienia i przepływu co 1 min
        - Wykrywanie wycieków, predykcja popytu
        
        Minimalizuj straty wody, zapewnij ciągłość dostaw.
    """,
        leading_newline=True,
    )
    
    print(f"\n💧 Water management system:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def main():
    """Uruchom wszystkie demonstracje smart cities."""
    await demo_traffic_optimization()
    await demo_smart_grid()
    await demo_waste_management()
    await demo_public_transport()
    await demo_parking_management()
    await demo_air_quality()
    await demo_water_management()

    print_separator("Smart Cities demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
