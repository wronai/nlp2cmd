"""
Medycyna i Healthcare - Harmonogramowanie sal i zarządzanie zasobami

Demonstruje użycie NLP2CMD do optymalizacji procesów
medycznych i zarządzania szpitalem.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, run_thermo_demo


async def demo_or_scheduling():
    """Harmonogramowanie sal operacyjnych."""
    # Harmonogramowanie sal operacyjnych
    result = await run_thermo_demo(
        "Healthcare - Operating Room Scheduling",
        """
        Zaplanuj operacje na 5 sal przez tydzień:
        - 80 zaplanowanych operacji
        - Różne czasy trwania (30 min - 8h)
        - Niektóre wymagają specjalistycznego sprzętu
        - Priorytet dla przypadków pilnych
        - Czas na sterylizację między operacjami: 30 min
        
        Maksymalizuj wykorzystanie sal, minimalizuj nadgodziny.
    """,
    )
    
    print(result.decoded_output)
    print(f"\n📊 Scheduling metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_nurse_scheduling():
    """Grafik dyżurów pielęgniarek."""
    # Grafik pielęgniarek
    result = await run_thermo_demo(
        "Healthcare - Nurse Scheduling",
        """
        Ułóż grafik dla 30 pielęgniarek na miesiąc:
        - 3 zmiany: dzienna, wieczorna, nocna
        - Min 2 dni wolne między nockami
        - Max 5 dni pracy z rzędu
        - Weekendy: max 2 w miesiącu
        - Uwzględnij preferencje i urlopy
        
        Zapewnij minimum 5 osób na zmianę, sprawiedliwy rozkład.
    """,
        leading_newline=True,
    )
    
    print(f"\n👩‍⚕️ Nurse schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_patient_allocation():
    """Alokacja pacjentów do ramion badania klinicznego."""
    # Alokacja pacjentów do badania klinicznego
    result = await run_thermo_demo(
        "Healthcare - Clinical Trial Patient Allocation",
        """
        Przydziel 200 pacjentów do 4 ramion badania:
        - Ramię A: nowy lek, max 60 pacjentów
        - Ramię B: lek + terapia, max 60 pacjentów
        - Ramię C: placebo, max 40 pacjentów
        - Ramię D: standard care, max 40 pacjentów
        
        Zbalansuj grupy pod względem:
        - Wieku (równomiernie 30-70 lat)
        - Płci (50/50)
        - Stadium choroby (I-IV)
        
        Minimalizuj bias, maksymalizuj power statystyczny.
    """,
        leading_newline=True,
    )
    
    print(f"\n🧪 Clinical trial allocation:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_emergency_department():
    """Optymalizacja pracy oddziału ratunkowego."""
    # Optymalizacja oddziału ratunkowego
    result = await run_thermo_demo(
        "Healthcare - Emergency Department Optimization",
        """
        Zoptymalizuj pracę oddziału ratunkowego:
        - 15 łóżek, 3 gabinety lekarskie
        - Pacjenci przybywają wg rozkładu Poisson (średnio 20/h)
        - Kategoria czerwona: natychmiastowa
        - Kategoria żółta: do 60 min
        - Kategoria zielona: do 2h
        
        Minimalizuj czas oczekiwania, optymalizuj personel.
    """,
        leading_newline=True,
    )
    
    print(f"\n🚑 Emergency department flow:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_ambulance_dispatch():
    """Dyspozycja karetek pogotowia."""
    # Optymalizacja dyspozycji karetek
    result = await run_thermo_demo(
        "Healthcare - Ambulance Dispatch Optimization",
        """
        Zoptymalizuj dyspozycję 10 karetek w mieście:
        - 5 baz rozmieszczonych w mieście
        - Średnio 15 wezwań na godzinę
        - Czas dojazdu: średnio 8 min
        - Priorytety: życie zagrożone < 5 min, inne < 15 min
        
        Minimalizuj średni czas dojazdu, optymalizuj pozycjonowanie baz.
    """,
        leading_newline=True,
    )
    
    print(f"\n🚑 Ambulance dispatch:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_icu_bed_management():
    """Zarządzanie łóżkami na OIOM."""
    # Zarządzanie łóżkami OIOM
    result = await run_thermo_demo(
        "Healthcare - ICU Bed Management",
        """
        Zoptymalizuj zarządzanie 20 łóżkami OIOM:
        - Przyjęcia wg skali NEWS 2-9
        - Średni pobyt: 5 dni
        - 10% pacjentów wymaga wentylacji
        - Personel: 1 pielęgniarka na 2 pacjentów
        
        Maksymalizuj wykorzystanie, minimalizuj czas oczekiwania.
    """,
        leading_newline=True,
    )
    
    print(f"\n🏥 ICU bed management:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def demo_pharmacy_inventory():
    """Zarządzanie zapasami w aptece szpitalnej."""
    # Zarządzanie zapasami leków
    result = await run_thermo_demo(
        "Healthcare - Pharmacy Inventory Management",
        """
        Zoptymalizuj zapasy 500 leków w aptece:
        - Koszt przechowywania: 5% wartości/miesiąc
        - Koszt braku: 100x koszt leku
        - Lead time: 1-7 dni
        - Sezonowość: grypa +200% zimą
        
        Minimalizuj całkowity koszt przy 99% dostępności.
    """,
        leading_newline=True,
    )
    
    print(f"\n💊 Pharmacy inventory policy:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def main():
    """Uruchom wszystkie demonstracje healthcare."""
    await demo_or_scheduling()
    await demo_nurse_scheduling()
    await demo_patient_allocation()
    await demo_emergency_department()
    await demo_ambulance_dispatch()
    await demo_icu_bed_management()
    await demo_pharmacy_inventory()
    
    print("\n" + "=" * 70)
    print("  Healthcare demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
