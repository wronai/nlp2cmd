"""
Bioinformatyka - Pipeline genomowy i symulacje białkowe

Demonstruje użycie NLP2CMD do optymalizacji pipeline'ów
analitycznych w bioinformatyce.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_genomic_pipeline():
    start_time = time.time()
    """Optymalizacja pipeline'u analizy genomowej."""
    print("=" * 70)
    print("  Bioinformatyka - Genomic Pipeline Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja pipeline'u genomowego
    result = await thermo.generate("""
        Zaplanuj analizę 100 próbek DNA:
        - FastQC (5 min/próbka)
        - Trimming (10 min/próbka)
        - Alignment BWA (30 min/próbka)
        - Variant calling (45 min/próbka)
        - Annotation (15 min/próbka)
        
        Dostępne zasoby: 16 CPU cores, 64GB RAM
        Alignment wymaga 8GB RAM per job
        
        Minimalizuj czas przy zachowaniu kolejności kroków.
    """)
    
    print(result.decoded_output)
    print(f"\n📊 Pipeline metrics:")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Converged: {result.converged}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def demo_protein_folding():
    start_time = time.time()
    """Alokacja zasobów dla symulacji foldingu białek."""
    print("\n" + "=" * 70)
    print("  Bioinformatyka - Protein Folding Resource Allocation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Alokacja zasobów dla foldingu białek
    result = await thermo.generate("""
        Przydziel zasoby obliczeniowe dla 50 symulacji foldingu:
        - 10 dużych białek (>500 aminokwasów): wymagają GPU
        - 25 średnich (200-500 aa): GPU lub CPU cluster
        - 15 małych (<200 aa): tylko CPU
        
        Dostępne zasoby:
        - 4x NVIDIA A100 (100 TFLOPS każdy)
        - 128 CPU cores (łącznie 10 TFLOPS)
        
        Maksymalizuj wykorzystanie GPU, minimalizuj czas.
    """)
    
    print(f"\n🧬 Protein folding allocation:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_crispr_optimization():
    start_time = time.time()
    """Optymalizacja sekwencji guide RNA."""
    print("\n" + "=" * 70)
    print("  Bioinformatyka - CRISPR Guide RNA Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja CRISPR guide RNA
    result = await thermo.generate("""
        Zaprojektuj 5 guide RNA dla genu BRCA1:
        - Minimalizuj off-target effects
        - Maksymalizuj on-target efficiency
        - Unikaj sekwencji z więcej niż 4 T z rzędu
        - GC content między 40-60%
    """)
    
    print(f"\n🧬 CRISPR guide RNA design:")
    print(f"   {result.decoded_output}")
    print(f"   Energy estimate: {result.energy_estimate}")


async def demo_proteomics_analysis():
    start_time = time.time()
    """Planowanie analizy proteomicznej."""
    print("\n" + "=" * 70)
    print("  Bioinformatyka - Proteomics Analysis Pipeline")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Pipeline analizy proteomicznej
    result = await thermo.generate("""
        Zaplanuj analizę proteomiczną 200 próbek:
        - Sample prep (30 min/próbka)
        - Digestion trypsyną (2h, batch 20 próbek)
        - LC-MS/MS (1h/próbka, 2 instrumenty)
        - Database search (15 min/próbka)
        - Quantification (10 min/próbka)
        - Statistical analysis (2h total)
        
        Minimalizuj całkowity czas, optymalizuj użycie instrumentów.
    """)
    
    print(f"\n🔬 Proteomics pipeline:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_drug_discovery():
    start_time = time.time()
    """Optymalizacja procesu odkrywania leków."""
    print("\n" + "=" * 70)
    print("  Bioinformatyka - Drug Discovery Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja screeningu leków
    result = await thermo.generate("""
        Zoptymalizuj screening 10000 związków chemicznych:
        - Faza 1: In silico docking (1 min/związek, 100 CPU cores)
        - Faza 2: ADME/Tox prediction (30s/związek, 50 cores)
        - Faza 3: In vitro assay (4h/batch 100 związków, 5 robotów)
        - Faza 4: In vivo testing (tydzień/batch 10 związków)
        
        Wybierz top 100 kandydatów, minimalizuj czas i koszt.
    """)
    
    print(f"\n💊 Drug discovery pipeline:")
    print(f"   {result.decoded_output}")
    start_time = time.time()
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def main():
    """Uruchom wszystkie demonstracje bioinformatyki."""
    await demo_genomic_pipeline()
    await demo_protein_folding()
    await demo_crispr_optimization()
    await demo_proteomics_analysis()
    await demo_drug_discovery()
    
    print("\n" + "=" * 70)
    print("  Bioinformatics demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
