"""
Termodynamiczny generator - przykład użycia

Demonstruje integrację hybrydowego i termodynamicznego podejścia.
"""

import asyncio
from nlp2cmd.generation import (
    create_hybrid_generator,
    create_thermodynamic_generator,
    HybridThermodynamicGenerator,
)


async def demo_hybrid():
    """Demonstracja generatora hybrydowego."""
    print("=== Hybrid Generator Demo ===")
    
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
        print(f"Query: {query}")
        print(f"Source: {result.source}")
        print(f"Command: {result.command}")
        print(f"Latency: {result.latency_ms:.1f}ms")
        print()
    
    # Statystyki
    stats = hybrid.get_stats()
    print(f"Rule hit rate: {stats.rule_hit_rate:.1%}")
    print(f"Cost savings: {stats.cost_savings_percent:.1f}%")
    print()


async def demo_thermodynamic():
    """Demonstracja generatora termodynamicznego."""
    print("=== Thermodynamic Generator Demo ===")
    
    # Termodynamiczny dla optymalizacji
    thermo = create_thermodynamic_generator(n_samples=5, n_steps=200)
    
    problems = [
        "Zaplanuj 5 zadań w 10 slotach",
        "Przydziel 3 zasoby do 4 konsumentów",
        "Zaplanuj 3 zadania, zadanie 2 przed slotem 5",
    ]
    
    for problem in problems:
        result = await thermo.generate(problem)
        print(f"Problem: {problem}")
        print(f"Type: {result.problem.problem_type}")
        print(f"Energy: {result.energy:.2f}")
        print(f"Converged: {result.converged}")
        print(f"Latency: {result.latency_ms:.1f}ms")
        print(f"Solution:\n{result.decoded_output}")
        
        if result.energy_estimate:
            savings = result.energy_estimate['savings_digital_percent']
            print(f"Energy savings: {savings:.1f}%")
        print()


async def demo_complete_hybrid():
    """Demonstracja pełnego generatora hybrydowego."""
    print("=== Complete HybridThermodynamic Generator Demo ===")
    
    generator = HybridThermodynamicGenerator()
    
    mixed_queries = [
        "Pokaż użytkowników z tabeli users",           # DSL
        "docker ps -a",                                 # DSL
        "Zaplanuj 4 zadania w 8 slotach",                # Thermodynamic
        "kubectl get pods -n default",                  # DSL
        "Przydziel 2 zasoby do 3 konsumentów",          # Thermodynamic
    ]
    
    for query in mixed_queries:
        result = await generator.generate(query)
        print(f"Query: {query}")
        print(f"Source: {result['source']}")
        print(f"Complexity: {result['complexity']:.2f}")
        
        if result['source'] == 'dsl':
            print(f"Command: {result['result'].command}")
            print(f"Latency: {result['result'].latency_ms:.1f}ms")
        else:
            print(f"Solution:\n{result['result'].decoded_output}")
            print(f"Energy: {result['result'].energy:.2f}")
            print(f"Latency: {result['result'].latency_ms:.1f}ms")
        print()


async def main():
    """Główna funkcja demonstracyjna."""
    print("NLP2CMD Generation Module - Complete Demo")
    print("=" * 50)
    print()
    
    await demo_hybrid()
    await demo_thermodynamic()
    await demo_complete_hybrid()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
