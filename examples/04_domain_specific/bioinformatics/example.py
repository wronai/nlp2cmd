"""
Bioinformatyka - Pipeline genomowy i symulacje białkowe

Demonstruje użycie NLP2CMD do optymalizacji pipeline'ów
analitycznych w bioinformatyce.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo


async def demo_genomic_pipeline():
    """Optymalizacja pipeline'u analizy genomowej."""
    # Optymalizacja pipeline'u genomowego
    result = await run_thermo_demo(
        "Bioinformatyka - Genomic Pipeline Scheduling",
        """
        Zaplanuj analizę 100 próbek DNA:
        - FastQC (5 min/próbka)
        - Trimming (10 min/próbka)
        - Alignment BWA (30 min/próbka)
        - Variant calling (45 min/próbka)
        - Annotation (15 min/próbka)
        
        Dostępne zasoby: 16 CPU cores, 64GB RAM
        Alignment wymaga 8GB RAM per job
        
        Minimalizuj czas przy zachowaniu kolejności kroków.
    """,
    )
    
    print(result.decoded_output)
    print(f"\n📊 Pipeline metrics:")
    print_metrics(result, energy=True, converged=True, solution_quality=True)


async def demo_protein_folding():
    """Alokacja zasobów dla symulacji foldingu białek."""
    # Alokacja zasobów dla foldingu białek
    result = await run_thermo_demo(
        "Bioinformatyka - Protein Folding Resource Allocation",
        """
        Przydziel zasoby obliczeniowe dla 50 symulacji foldingu:
        - 10 dużych białek (>500 aminokwasów): wymagają GPU
        - 25 średnich (200-500 aa): GPU lub CPU cluster
        - 15 małych (<200 aa): tylko CPU
        
        Dostępne zasoby:
        - 4x NVIDIA A100 (100 TFLOPS każdy)
        - 128 CPU cores (łącznie 10 TFLOPS)
        
        Maksymalizuj wykorzystanie GPU, minimalizuj czas.
    """,
        leading_newline=True,
    )
    
    print(f"\n🧬 Protein folding allocation:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_crispr_optimization():
    """Optymalizacja sekwencji guide RNA."""
    # Optymalizacja CRISPR guide RNA
    result = await run_thermo_demo(
        "Bioinformatyka - CRISPR Guide RNA Optimization",
        """
        Zaprojektuj 5 guide RNA dla genu BRCA1:
        - Minimalizuj off-target effects
        - Maksymalizuj on-target efficiency
        - Unikaj sekwencji z więcej niż 4 T z rzędu
        - GC content między 40-60%
    """,
        leading_newline=True,
    )
    
    print(f"\n🧬 CRISPR guide RNA design:")
    print(f"   {result.decoded_output}")
    print(f"   Energy estimate: {result.energy_estimate}")


async def demo_proteomics_analysis():
    """Planowanie analizy proteomicznej."""
    # Pipeline analizy proteomicznej
    result = await run_thermo_demo(
        "Bioinformatyka - Proteomics Analysis Pipeline",
        """
        Zaplanuj analizę proteomiczną 200 próbek:
        - Sample prep (30 min/próbka)
        - Digestion trypsyną (2h, batch 20 próbek)
        - LC-MS/MS (1h/próbka, 2 instrumenty)
        - Database search (15 min/próbka)
        - Quantification (10 min/próbka)
        - Statistical analysis (2h total)
        
        Minimalizuj całkowity czas, optymalizuj użycie instrumentów.
    """,
        leading_newline=True,
    )
    
    print(f"\n🔬 Proteomics pipeline:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_drug_discovery():
    """Optymalizacja procesu odkrywania leków."""
    # Optymalizacja screeningu leków
    result = await run_thermo_demo(
        "Bioinformatyka - Drug Discovery Optimization",
        """
        Zoptymalizuj screening 10000 związków chemicznych:
        - Faza 1: In silico docking (1 min/związek, 100 CPU cores)
        - Faza 2: ADME/Tox prediction (30s/związek, 50 cores)
        - Faza 3: In vitro assay (4h/batch 100 związków, 5 robotów)
        - Faza 4: In vivo testing (tydzień/batch 10 związków)
        
        Wybierz top 100 kandydatów, minimalizuj czas i koszt.
    """,
        leading_newline=True,
    )
    
    print(f"\n💊 Drug discovery pipeline:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def main():
    """Uruchom wszystkie demonstracje bioinformatyki."""
    await demo_genomic_pipeline()
    await demo_protein_folding()
    await demo_crispr_optimization()
    await demo_proteomics_analysis()
    await demo_drug_discovery()

    print_separator("Bioinformatics demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
