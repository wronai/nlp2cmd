"""
Edukacja - Planowanie zajęć i optymalizacja procesu nauczania

Demonstruje użycie NLP2CMD do optymalizacji procesów
edukacyjnych i zarządzania uczelnią.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_course_timetabling():
    start_time = time.time()
    """Układanie planu zajęć na uczelni."""
    print("=" * 70)
    print("  Education - Course Timetabling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Planowanie zajęć
    result = await thermo.generate("""
        Ułóż plan zajęć dla Wydziału Informatyki:
        - 50 kursów, 200 grup
        - 30 sal (różne pojemności)
        - 80 wykładowców (różna dostępność)
        
        Ograniczenia:
        - Student nie może mieć nakładających się zajęć
        - Max 6h zajęć dziennie dla studenta
        - Wykładowca max 4h z rzędu
        - Laboratoria tylko w salach komputerowych
        
        Minimalizuj "okienka" między zajęciami.
    """)
    
    print(result.decoded_output)
    print(f"\n📊 Timetabling metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_exam_scheduling():
    start_time = time.time()
    """Harmonogram sesji egzaminacyjnej."""
    print("\n" + "=" * 70)
    print("  Education - Exam Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Harmonogram egzaminów
    result = await thermo.generate("""
        Zaplanuj 100 egzaminów w 2 tygodnie:
        - 5000 studentów
        - Student nie może mieć 2 egzaminów tego samego dnia
        - Min 1 dzień przerwy między egzaminami tego samego studenta
        - Sale egzaminacyjne o różnej pojemności
        
        Minimalizuj konflikty i maksymalizuj czas na przygotowanie.
    """)
    
    print(f"\n📝 Exam schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_learning_path():
    start_time = time.time()
    """Personalizacja ścieżki nauki."""
    print("\n" + "=" * 70)
    print("  Education - Learning Path Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Personalizacja ścieżki nauki
    result = await thermo.generate("""
        Zaplanuj ścieżkę nauki programowania dla studenta:
        - Cel: Full-stack developer w 6 miesięcy
        - Dostępny czas: 20h/tydzień
        - Obecny poziom: podstawy Pythona
        
        Kursy do wyboru: 30 kursów, różne zależności
        Optymalizuj kolejność dla najszybszego postępu.
    """)
    
    print(f"\n🎓 Learning path:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_classroom_allocation():
    start_time = time.time()
    """Alokacja sal wykładowych."""
    print("\n" + "=" * 70)
    print("  Education - Classroom Allocation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Alokacja sal
    result = await thermo.generate("""
        Przydziel 200 zajęć do 50 sal:
        - Sale: 10x małe (20-30 osób), 30x średnie (50-100), 10x duże (100+)
        - Laboratoria: 5x komputerowe, 3x chemiczne, 2x fizyczne
        - Preferencje: wykłady w dużych salach, lab w specjalistycznych
        
        Minimalizuj dystans między zajęciami dla studentów.
    """)
    
    print(f"\n🏫 Classroom allocation:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_student_grouping():
    start_time = time.time()
    """Tworzenie grup projektowych."""
    print("\n" + "=" * 70)
    print("  Education - Student Group Formation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Grupowanie studentów
    result = await thermo.generate("""
        Stwórz 40 grup projektowych z 200 studentów:
        - Grupy po 4-5 osób
        - Zbalansuj umiejętności: programowanie, design, prezentacja
        - Unikaj grupowania przyjaciół (preferencje)
        - Maksymalizuj różnorodność w grupach
        
        Minimalizuj niezgodności preferencji.
    """)
    
    print(f"\n👥 Student groups:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_resource_optimization():
    start_time = time.time()
    """Optymalizacja zasobów edukacyjnych."""
    print("\n" + "=" * 70)
    print("  Education - Educational Resource Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja zasobów
    result = await thermo.generate("""
        Zoptymalizuj wykorzystanie zasobów na uczelni:
        - 100 wykładowców, 50 asystentów
        - 200 sal, 20 laboratoriów
        - Biblioteka: 500 miejsc, 24/7
        - Wymagania: 5000 studentów, różne kierunki
        
        Maksymalizuj dostępność, minimalizuj koszty.
    """)
    
    print(f"\n📚 Resource optimization:")
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_curriculum_planning():
    start_time = time.time()
    """Planowanie programu nauczania."""
    print("\n" + "=" * 70)
    print("  Education - Curriculum Planning")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Planowanie programu
    result = await thermo.generate("""
        Zaprojektuj program studiów informatycznych:
        - 7 semestrów, 180 ECTS
        - Podstawy: matematyka, programowanie, algorytmy
        - Specjalizacje: AI, Security, Web, Mobile
        - Praktyki: 6 miesięcy, 30 ECTS
        
        Zapewnij zgodność z wymaganiami ACM/IEEE.
    """)
    
    start_time = time.time()
    print(f"\n📖 Curriculum design:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")


async def main():
    """Uruchom wszystkie demonstracje edukacyjne."""
    await demo_course_timetabling()
    await demo_exam_scheduling()
    await demo_learning_path()
    await demo_classroom_allocation()
    await demo_student_grouping()
    await demo_resource_optimization()
    await demo_curriculum_planning()
    
    print("\n" + "=" * 70)
    print("  Education demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
