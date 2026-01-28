"""
IT & DevOps - Automatyzacja infrastruktury

Demonstruje użycie NLP2CMD do automatyzacji zadań DevOps
i zarządzania infrastrukturą Kubernetes.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_separator, print_simple_result
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator


async def demo_devops_commands():
    """Podstawowe komendy DevOps."""
    print_separator("IT & DevOps - Podstawowe komendy")
    
    generator = HybridThermodynamicGenerator()
    
    # Naturalny język → komendy DevOps
    queries = [
        "kubectl get pods -n production",  # Direct kubectl command
        "kubectl scale deployment api-server --replicas=5",  # Direct kubectl command
        "kubectl logs -l app=api --since=1h | grep -i error",  # Direct kubectl command
        "pg_dump mydb | aws s3 cp - s3://backups/db-$(date +%Y%m%d).sql",  # Direct shell command
    ]
    
    for query in queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
        print_simple_result(query, result, elapsed)


async def demo_ci_cd_optimization():
    """Optymalizacja CI/CD Pipeline."""
    print_separator("IT & DevOps - Optymalizacja CI/CD Pipeline", leading_newline=True)
    
    from nlp2cmd.generation import create_thermodynamic_generator
    
    thermo = create_thermodynamic_generator(n_samples=10)
    
    start_time = time.time()
    # Problem: Optymalizacja kolejności jobów w pipeline
    result = await thermo.generate("""
        Zaplanuj 8 jobów CI/CD:
        - build (5 min)
        - unit-tests (3 min, po build)
        - integration-tests (10 min, po build)
        - security-scan (4 min, po build)
        - docker-build (3 min, po unit-tests)
        - deploy-staging (2 min, po docker-build i integration-tests)
        - e2e-tests (15 min, po deploy-staging)
        - deploy-prod (2 min, po e2e-tests i security-scan)
        
        Minimalizuj całkowity czas wykonania.
    """)
    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(result.decoded_output)
    print(f"\n⚡ Latency: {elapsed:.1f}ms")


async def demo_incident_response():
    """Automatyczna analiza i response na incydenty."""
    print_separator("IT & DevOps - Incident Response Automation", leading_newline=True)
    
    generator = HybridThermodynamicGenerator()
    
    incident_query = """
    High CPU on node-3. Check pods, drain node, and notify team.
    Commands needed: kubectl top pods, kubectl cordon, kubectl drain
    """
    
    start_time = time.time()
    result = await generator.generate(incident_query)
    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"\n🚨 Incident: High CPU on node-3")
    print(f"Generated response plan:")
    print(f"   {result['result'].command}")
    print(f"   ⚡ Latency: {elapsed:.1f}ms")


async def main():
    """Uruchom wszystkie demonstracje DevOps."""
    await demo_devops_commands()
    await demo_ci_cd_optimization()
    await demo_incident_response()
    
    print_separator("DevOps demos completed!", leading_newline=True)


if __name__ == "__main__":
    asyncio.run(main())
