"""
Data Science & ML - Optymalizacja procesów ML

Demonstruje użycie NLP2CMD do optymalizacji hiperparametrów,
planowania eksperymentów i wyboru cech.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import (
    ThermodynamicGenerator,
    OptimizationProblem,
)


async def demo_hyperparameter_optimization():
    """Optymalizacja hiperparametrów modelu ML."""
    print("=" * 70)
    print("  Data Science - Hyperparameter Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Problem optymalizacji hiperparametrów
    problem = OptimizationProblem(
        problem_type="hyperparameter",
        variables=["learning_rate", "batch_size", "num_layers", "dropout"],
        constraints=[
            {"type": "range", "var": "learning_rate", "min": 0.0001, "max": 0.1},
            {"type": "range", "var": "batch_size", "min": 16, "max": 256},
            {"type": "range", "var": "num_layers", "min": 2, "max": 10},
            {"type": "range", "var": "dropout", "min": 0.0, "max": 0.5},
        ],
        objective="minimize",  # minimize validation loss
        objective_field="val_loss",
    )
    
    result = await thermo.generate(
        "Znajdź optymalne hiperparametry dla modelu LSTM",
        problem=problem
    )
    
    print("\n✅ Optimal hyperparameters:")
    print(f"  Learning rate: {result.solution.get('learning_rate', 'N/A')}")
    print(f"  Batch size: {result.solution.get('batch_size', 'N/A')}")
    print(f"  Num layers: {result.solution.get('num_layers', 'N/A')}")
    print(f"  Dropout: {result.solution.get('dropout', 'N/A')}")
    print(f"  Energy: {result.energy:.4f}")
    print(f"  Converged: {result.converged}")


async def demo_feature_selection():
    """Optymalizacja wyboru cech dla modelu ML."""
    print("\n" + "=" * 70)
    print("  Data Science - Feature Selection")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    start_time = time.time()
    # Optymalizacja wyboru cech
    result = await thermo.generate("""
        Wybierz 10 najważniejszych cech z 50 dostępnych
        dla modelu predykcji churnu.
        Maksymalizuj AUC-ROC przy minimalnej korelacji między cechami.
    """)
    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"\n📊 Feature selection result:")
    print(f"   {result.decoded_output}")
    print(f"   Energy: {result.energy:.4f}")
    print(f"   Solution quality: {result.solution_quality.explanation}")
    print(f"   ⚡ Latency: {elapsed:.1f}ms")


async def demo_experiment_scheduling():
    """Planowanie eksperymentów ML na klastrze GPU."""
    print("\n" + "=" * 70)
    print("  Data Science - Experiment Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    start_time = time.time()
    # Planowanie eksperymentów ML
    result = await thermo.generate("""
        Zaplanuj 20 eksperymentów ML na 4 GPU:
        - GPU A100: najszybsze, 2 dostępne
        - GPU V100: średnie, 2 dostępne
        
        Eksperymenty:
        - 5x large models (wymagają A100, 4h każdy)
        - 10x medium models (dowolne GPU, 2h każdy)
        - 5x small models (dowolne GPU, 1h każdy)
        
        Minimalizuj całkowity czas i koszt.
    """)
    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"\n🧪 Experiment schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")
    print(f"   Sampler steps: {result.sampler_steps}")
    print(f"   ⚡ Latency: {elapsed:.1f}ms")


async def demo_model_ensemble_optimization():
    """Optymalizacja ensemble modeli."""
    print("\n" + "=" * 70)
    print("  Data Science - Model Ensemble Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    start_time = time.time()
    # Optymalizacja wag ensemble
    result = await thermo.generate("""
        Zoptymalizuj wagi dla ensemble 5 modeli:
        - Random Forest: accuracy 0.85, fast inference
        - XGBoost: accuracy 0.87, medium inference  
        - Neural Network: accuracy 0.89, slow inference
        - SVM: accuracy 0.84, medium inference
        - Logistic Regression: accuracy 0.82, very fast
        
        Maksymalizuj accuracy przy ograniczeniu:
        - Całkowity czas inference < 100ms
        - Max waga dla jednego modelu: 40%
    """)
    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    print(f"\n🤖 Ensemble weights:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")
    print(f"   ⚡ Latency: {elapsed:.1f}ms")


async def main():
    """Uruchom wszystkie demonstracje Data Science."""
    await demo_hyperparameter_optimization()
    await demo_feature_selection()
    await demo_experiment_scheduling()
    await demo_model_ensemble_optimization()
    
    print("\n" + "=" * 70)
    print("  Data Science demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
