"""
Medycyna i Healthcare - Harmonogramowanie sal i zarządzanie zasobami

Demonstruje użycie NLP2CMD do optymalizacji procesów
medycznych i zarządzania szpitalem.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_or_scheduling():
    start_time = time.time()
    """Harmonogramowanie sal operacyjnych."""
    print("=" * 70)
    print("  Healthcare - Operating Room Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Harmonogramowanie sal operacyjnych
    result = await thermo.generate("""
        Zaplanuj operacje na 5 sal przez tydzień:
        - 80 zaplanowanych operacji
        - Różne czasy trwania (30 min - 8h)
        - Niektóre wymagają specjalistycznego sprzętu
        - Priorytet dla przypadków pilnych
        - Czas na sterylizację między operacjami: 30 min
        
        Maksymalizuj wykorzystanie sal, minimalizuj nadgodziny.
    """)
    
    print(result.decoded_output)
    print(f"\n📊 Scheduling metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_nurse_scheduling():
    start_time = time.time()
    """Grafik dyżurów pielęgniarek."""
    print("\n" + "=" * 70)
    print("  Healthcare - Nurse Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Grafik pielęgniarek
    result = await thermo.generate("""
        Ułóż grafik dla 30 pielęgniarek na miesiąc:
        - 3 zmiany: dzienna, wieczorna, nocna
        - Min 2 dni wolne między nockami
        - Max 5 dni pracy z rzędu
        - Weekendy: max 2 w miesiącu
        - Uwzględnij preferencje i urlopy
        
        Zapewnij minimum 5 osób na zmianę, sprawiedliwy rozkład.
    """)
    
    print(f"\n👩‍⚕️ Nurse schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_patient_allocation():
    start_time = time.time()
    """Alokacja pacjentów do ramion badania klinicznego."""
    print("\n" + "=" * 70)
    print("  Healthcare - Clinical Trial Patient Allocation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Alokacja pacjentów do badania klinicznego
    result = await thermo.generate("""
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
    """)
    
    print(f"\n🧪 Clinical trial allocation:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_emergency_department():
    start_time = time.time()
    """Optymalizacja pracy oddziału ratunkowego."""
    print("\n" + "=" * 70)
    print("  Healthcare - Emergency Department Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja oddziału ratunkowego
    result = await thermo.generate("""
        Zoptymalizuj pracę oddziału ratunkowego:
        - 15 łóżek, 3 gabinety lekarskie
        - Pacjenci przybywają wg rozkładu Poisson (średnio 20/h)
        - Kategoria czerwona: natychmiastowa
        - Kategoria żółta: do 60 min
        - Kategoria zielona: do 2h
        
        Minimalizuj czas oczekiwania, optymalizuj personel.
    """)
    
    print(f"\n🚑 Emergency department flow:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_ambulance_dispatch():
    start_time = time.time()
    """Dyspozycja karetek pogotowia."""
    print("\n" + "=" * 70)
    print("  Healthcare - Ambulance Dispatch Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja dyspozycji karetek
    result = await thermo.generate("""
        Zoptymalizuj dyspozycję 10 karetek w mieście:
        - 5 baz rozmieszczonych w mieście
        - Średnio 15 wezwań na godzinę
        - Czas dojazdu: średnio 8 min
        - Priorytety: życie zagrożone < 5 min, inne < 15 min
        
        Minimalizuj średni czas dojazdu, optymalizuj pozycjonowanie baz.
    """)
    
    print(f"\n🚑 Ambulance dispatch:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_icu_bed_management():
    start_time = time.time()
    """Zarządzanie łóżkami na OIOM."""
    print("\n" + "=" * 70)
    print("  Healthcare - ICU Bed Management")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Zarządzanie łóżkami OIOM
    result = await thermo.generate("""
        Zoptymalizuj zarządzanie 20 łóżkami OIOM:
        - Przyjęcia wg skali NEWS 2-9
        - Średni pobyt: 5 dni
        - 10% pacjentów wymaga wentylacji
        - Personel: 1 pielęgniarka na 2 pacjentów
        
        Maksymalizuj wykorzystanie, minimalizuj czas oczekiwania.
    """)
    
    print(f"\n🏥 ICU bed management:")
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_pharmacy_inventory():
    start_time = time.time()
    """Zarządzanie zapasami w aptece szpitalnej."""
    print("\n" + "=" * 70)
    print("  Healthcare - Pharmacy Inventory Management")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Zarządzanie zapasami leków
    result = await thermo.generate("""
        Zoptymalizuj zapasy 500 leków w aptece:
        - Koszt przechowywania: 5% wartości/miesiąc
        - Koszt braku: 100x koszt leku
        - Lead time: 1-7 dni
        - Sezonowość: grypa +200% zimą
        
        Minimalizuj całkowity koszt przy 99% dostępności.
    """)
    
    start_time = time.time()
    print(f"\n💊 Pharmacy inventory policy:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")


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
