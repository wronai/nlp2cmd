"""
Termodynamyczny generator - POPRAWIONY przykład użycia

Demonstruje poprawki w hybrydowym i termodynamicznym podejściu.

POPRAWKI:
1. [FIX] Router poprawnie identyfikuje problemy optymalizacyjne
2. [FIX] Alokacja używa prawidłowej liczby zasobów
3. [PERF] Adaptacyjne n_steps - szybsze wykonanie dla małych problemów
4. [FIX] Polskie słowa kluczowe UTF-8
"""

import asyncio
from nlp2cmd.generation import (
    create_hybrid_generator,
    HybridThermodynamicGenerator,
)

# Import poprawionej wersji
from nlp2cmd.generation.thermodynamic import (
    create_thermodynamic_generator,
    HybridThermodynamicGenerator as ImprovedHybridGenerator,
    ThermodynamicGenerator,
)


async def demo_hybrid():
    """Demonstracja generatora hybrydowego."""
    print("=" * 60)
    print("=== Hybrid Generator Demo ===")
    print("=" * 60)

    # Hybryda dla standardowych zapytań
    hybrid = create_hybrid_generator()

    queries = [
        "Pokaż dane z tabeli users",
        "Znajdź pliki .py w /home",
        "Pokaż uruchomione kontenery",
        "kubectl get pods",
    ]

    for query in queries:
        result = await hybrid.generate(query)
        print(f"\nQuery: {query}")
        print(f"  Source: {result.source}")
        print(f"  Command: {result.command}")
        print(f"  Latency: {result.latency_ms:.1f}ms")

    # Statystyki
    stats = hybrid.get_stats()
    print(f"\n📊 Stats:")
    print(f"  Rule hit rate: {stats.rule_hit_rate:.1%}")
    print(f"  Cost savings: {stats.cost_savings_percent:.1f}%")
    print()


async def demo_thermodynamic_improved():
    """Demonstracja POPRAWIONEGO generatora termodynamicznego."""
    print("=" * 60)
    print("=== IMPROVED Thermodynamic Generator Demo ===")
    print("=" * 60)

    # POPRAWIONY termodynamiczny generator z adaptacyjnymi krokami
    thermo = create_thermodynamic_generator(
        n_samples=5,
        n_steps=200,
        adaptive_steps=True  # NEW: włączone adaptacyjne kroki
    )

    problems = [
        # Test 1: Scheduling - powinno być szybkie (mało zadań)
        ("Zaplanuj 3 zadania w 5 slotach", "schedule", 3),

        # Test 2: Alokacja - POPRAWIONA liczba zasobów
        ("Przydziel 3 zasoby do 4 konsumentów", "allocate", 3),

        # Test 3: Scheduling z deadline
        ("Zaplanuj 5 zadań w 10 slotach, zadanie 2 przed slotem 5", "schedule", 5),
    ]

    for text, expected_type, expected_vars in problems:
        print(f"\n📝 Problem: {text}")

        result = await thermo.generate(text)

        # Walidacja
        type_ok = "✅" if result.problem.problem_type == expected_type else "❌"
        vars_ok = "✅" if len(result.problem.variables) == expected_vars else "❌"

        print(f"  {type_ok} Type: {result.problem.problem_type} (expected: {expected_type})")
        print(f"  {vars_ok} Variables: {len(result.problem.variables)} (expected: {expected_vars})")
        print(f"  Energy: {result.energy:.2f}")
        print(f"  Converged: {result.converged}")
        print(f"  ⚡ Latency: {result.latency_ms:.1f}ms")

        # Pokaż rozwiązanie
        if result.decoded_output:
            print(f"  Solution:\n{result.decoded_output}")

        if result.energy_estimate:
            savings = result.energy_estimate.get('savings_digital_percent', 0)
            print(f"  Energy savings: {savings:.1f}%")


async def demo_hybrid_thermodynamic_improved():
    """Demonstracja POPRAWIONEGO hybrydowego generatora."""
    print("\n" + "=" * 60)
    print("=== IMPROVED HybridThermodynamic Generator Demo ===")
    print("=" * 60)

    generator = ImprovedHybridGenerator()

    test_queries = [
        # DSL queries - powinny iść do DSL
        ("Pokaż użytkowników z tabeli users", "dsl"),
        ("kubectl get pods -n default", "dsl"),
        ("docker ps -a", "dsl"),

        # Optimization queries - POPRAWIONE: powinny iść do thermodynamic
        ("Zaplanuj 4 zadania w 8 slotach", "thermodynamic"),
        ("Przydziel 2 zasoby do 3 konsumentów", "thermodynamic"),  # BYŁO: dsl (błąd!)
        ("Optymalizuj harmonogram 5 zadań", "thermodynamic"),
    ]

    print("\n📋 Testing routing decisions:\n")

    correct = 0
    total = len(test_queries)

    for query, expected_source in test_queries:
        result = await generator.generate(query)
        actual_source = result['source']

        is_correct = actual_source == expected_source
        icon = "✅" if is_correct else "❌"

        if is_correct:
            correct += 1

        print(f"{icon} Query: {query}")
        print(f"   Expected: {expected_source}, Got: {actual_source}")
        print(f"   Complexity: {result['complexity']:.2f}")

        if actual_source == 'dsl':
            print(f"   Command: {result['result'].command}")
        else:
            print(
                f"   Solution: {result['result'].decoded_output[:50] if result['result'].decoded_output else 'N/A'}...")
        print()

    print(f"\n📊 Routing Accuracy: {correct}/{total} ({100 * correct / total:.0f}%)")


async def benchmark_latency():
    """Benchmark porównujący latencję przed/po poprawkach."""
    print("\n" + "=" * 60)
    print("=== Latency Benchmark ===")
    print("=" * 60)

    # Generator bez adaptacyjnych kroków (stary sposób)
    old_gen = create_thermodynamic_generator(
        n_samples=3,
        n_steps=500,
        adaptive_steps=False  # Wyłączone - jak w starej wersji
    )

    # Generator z adaptacyjnymi krokami (nowy sposób)
    new_gen = create_thermodynamic_generator(
        n_samples=3,
        n_steps=500,
        adaptive_steps=True  # Włączone - nowa wersja
    )

    test_problems = [
        "Zaplanuj 2 zadania w 4 slotach",  # Bardzo małe
        "Zaplanuj 5 zadań w 10 slotach",  # Średnie
        "Zaplanuj 10 zadań w 20 slotach",  # Duże
    ]

    print("\n⏱️  Comparing latency (adaptive_steps=False vs True):\n")

    for problem in test_problems:
        # Stary sposób
        result_old = await old_gen.generate(problem)
        latency_old = result_old.latency_ms

        # Nowy sposób
        result_new = await new_gen.generate(problem)
        latency_new = result_new.latency_ms

        speedup = latency_old / latency_new if latency_new > 0 else 0

        print(f"Problem: {problem}")
        print(f"  Old (fixed steps):     {latency_old:>8.1f}ms")
        print(f"  New (adaptive steps):  {latency_new:>8.1f}ms")
        print(f"  Speedup:               {speedup:>8.1f}x")
        print()


async def main():
    """Główna funkcja demonstracyjna."""
    print("=" * 60)
    print("NLP2CMD Generation Module - IMPROVED Demo")
    print("=" * 60)
    print()
    print("This demo shows the improvements made to the thermodynamic")
    print("generator including:")
    print("  1. Better routing (optimization keywords)")
    print("  2. Correct resource/consumer parsing")
    print("  3. Adaptive Langevin steps for faster execution")
    print("  4. Proper Polish UTF-8 keyword support")
    print()

    await demo_hybrid()
    await demo_thermodynamic_improved()
    await demo_hybrid_thermodynamic_improved()
    await benchmark_latency()

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())