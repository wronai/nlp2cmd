"""
Edukacja - Planowanie zajęć i optymalizacja procesu nauczania

Demonstruje użycie NLP2CMD do optymalizacji procesów
edukacyjnych i zarządzania uczelnią.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo


async def demo_course_timetabling():
    """Układanie planu zajęć na uczelni."""
    # Planowanie zajęć
    result = await run_thermo_demo(
        "Education - Course Timetabling",
        """
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
    """,
    )
    
    print(result.decoded_output)
    print(f"\n📊 Timetabling metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_exam_scheduling():
    """Harmonogram sesji egzaminacyjnej."""
    # Harmonogram egzaminów
    result = await run_thermo_demo(
        "Education - Exam Scheduling",
        """
        Zaplanuj 100 egzaminów w 2 tygodnie:
        - 5000 studentów
        - Student nie może mieć 2 egzaminów tego samego dnia
        - Min 1 dzień przerwy między egzaminami tego samego studenta
        - Sale egzaminacyjne o różnej pojemności
        
        Minimalizuj konflikty i maksymalizuj czas na przygotowanie.
    """,
        leading_newline=True,
    )
    
    print(f"\n📝 Exam schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_learning_path():
    """Personalizacja ścieżki nauki."""
    # Personalizacja ścieżki nauki
    result = await run_thermo_demo(
        "Education - Learning Path Optimization",
        """
        Zaplanuj ścieżkę nauki programowania dla studenta:
        - Cel: Full-stack developer w 6 miesięcy
        - Dostępny czas: 20h/tydzień
        - Obecny poziom: podstawy Pythona
        
        Kursy do wyboru: 30 kursów, różne zależności
        Optymalizuj kolejność dla najszybszego postępu.
    """,
        leading_newline=True,
    )
    
    print(f"\n🎓 Learning path:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_classroom_allocation():
    """Alokacja sal wykładowych."""
    # Alokacja sal
    result = await run_thermo_demo(
        "Education - Classroom Allocation",
        """
        Przydziel 200 zajęć do 50 sal:
        - Sale: 10x małe (20-30 osób), 30x średnie (50-100), 10x duże (100+)
        - Laboratoria: 5x komputerowe, 3x chemiczne, 2x fizyczne
        - Preferencje: wykłady w dużych salach, lab w specjalistycznych
        
        Minimalizuj dystans między zajęciami dla studentów.
    """,
        leading_newline=True,
    )
    
    print(f"\n🏫 Classroom allocation:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_student_grouping():
    """Tworzenie grup projektowych."""
    # Grupowanie studentów
    result = await run_thermo_demo(
        "Education - Student Group Formation",
        """
        Stwórz 40 grup projektowych z 200 studentów:
        - Grupy po 4-5 osób
        - Zbalansuj umiejętności: programowanie, design, prezentacja
        - Unikaj grupowania przyjaciół (preferencje)
        - Maksymalizuj różnorodność w grupach
        
        Minimalizuj niezgodności preferencji.
    """,
        leading_newline=True,
    )
    
    print(f"\n👥 Student groups:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_resource_optimization():
    """Optymalizacja zasobów edukacyjnych."""
    # Optymalizacja zasobów
    result = await run_thermo_demo(
        "Education - Educational Resource Optimization",
        """
        Zoptymalizuj wykorzystanie zasobów na uczelni:
        - 100 wykładowców, 50 asystentów
        - 200 sal, 20 laboratoriów
        - Biblioteka: 500 miejsc, 24/7
        - Wymagania: 5000 studentów, różne kierunki
        
        Maksymalizuj dostępność, minimalizuj koszty.
    """,
        leading_newline=True,
    )
    
    print(f"\n📚 Resource optimization:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def demo_curriculum_planning():
    """Planowanie programu nauczania."""
    # Planowanie programu
    result = await run_thermo_demo(
        "Education - Curriculum Planning",
        """
        Zaprojektuj program studiów informatycznych:
        - 7 semestrów, 180 ECTS
        - Podstawy: matematyka, programowanie, algorytmy
        - Specjalizacje: AI, Security, Web, Mobile
        - Praktyki: 6 miesięcy, 30 ECTS
        
        Zapewnij zgodność z wymaganiami ACM/IEEE.
    """,
        leading_newline=True,
    )
    
    print(f"\n📖 Curriculum design:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def main():
    """Uruchom wszystkie demonstracje edukacyjne."""
    await demo_course_timetabling()
    await demo_exam_scheduling()
    await demo_learning_path()
    await demo_classroom_allocation()
    await demo_student_grouping()
    await demo_resource_optimization()
    await demo_curriculum_planning()

    print_separator("Education demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
