"""
Hyperparameter optimization using thermodynamic approach.

This module implements a hyperparameter optimizer that uses
thermodynamic principles to find optimal hyperparameters for machine learning models.
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import random

from termo2.base_solver import BaseSolver


@dataclass
class HyperparameterSpace:
    """Definition of hyperparameter search space."""
    
    learning_rate: Tuple[float, float] = (0.001, 0.1)
    batch_size: Tuple[int, int] = (16, 256)
    epochs: Tuple[int, int] = (10, 200)
    dropout: Tuple[float, float] = (0.0, 0.5)
    weight_decay: Tuple[float, float] = (0.0, 0.01)
    momentum: Tuple[float, float] = (0.0, 0.99)
    
    def sample(self) -> Dict[str, Any]:
        """Sample random hyperparameters from the space."""
        return {
            'learning_rate': np.random.uniform(*self.learning_rate),
            'batch_size': np.random.randint(*self.batch_size),
            'epochs': np.random.randint(*self.epochs),
            'dropout': np.random.uniform(*self.dropout),
            'weight_decay': np.random.uniform(*self.weight_decay),
            'momentum': np.random.uniform(*self.momentum),
        }
    
    def decode(self, z: np.ndarray) -> Dict[str, Any]:
        """Decode vector z to hyperparameters."""
        # Normalize to [0, 1] range
        z_norm = (z - z.min()) / (z.max() - z.min() + 1e-8)
        
        # Map to parameter ranges
        idx = 0
        params = {}
        
        # learning_rate
        if idx < len(z_norm):
            params['learning_rate'] = z_norm[idx] * (self.learning_rate[1] - self.learning_rate[0]) + self.learning_rate[0]
            idx += 1
        
        # batch_size
        if idx < len(z_norm):
            params['batch_size'] = int(z_norm[idx] * (self.batch_size[1] - self.batch_size[0]) + self.batch_size[0])
            idx += 1
        
        # epochs
        if idx < len(z_norm):
            params['epochs'] = int(z_norm[idx] * (self.epochs[1] - self.epochs[0]) + self.epochs[0])
            idx += 1
        
        # dropout
        if idx < len(z_norm):
            params['dropout'] = z_norm[idx] * (self.dropout[1] - self.dropout[0]) + self.dropout[0]
            idx += 1
        
        # weight_decay
        if idx < len(z_norm):
            params['weight_decay'] = z_norm[idx] * (self.weight_decay[1] - self.weight_decay[0]) + self.weight_decay[0]
            idx += 1
        
        # momentum
        if idx < len(z_norm):
            params['momentum'] = z_norm[idx] * (self.momentum[1] - self.momentum[0]) + self.momentum[0]
        
        return params


@dataclass
class HyperparameterResult:
    """Result of hyperparameter optimization."""
    
    params: Dict[str, Any]
    score: float
    validation_loss: float
    training_time: float
    energy_estimate: float
    
    def is_better_than(self, other: 'HyperparameterResult') -> bool:
        """Check if this result is better than another."""
        return self.score > other.score


class HyperparameterOptimizer(BaseSolver):
    """Hyperparameter optimizer using thermodynamic approach."""
    
    def __init__(self, space: HyperparameterSpace, n_samples: int = 20):
        self.space = space
        self.n_samples = n_samples
        self.best_result = None
        self.history = []
    
    def optimize(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray) -> HyperparameterResult:
        """Optimize hyperparameters."""
        # Generate initial samples
        samples = self._generate_samples()
        
        # Evaluate all samples
        results = []
        for sample in samples:
            result = self._evaluate_hyperparameters(sample, X_train, y_train, X_val, y_val)
            results.append(result)
            
            if self.best_result is None or result.is_better_than(self.best_result):
                self.best_result = result
        
        # Sort results by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Return best result
        return results[0] if results else None
    
    def _generate_samples(self) -> List[Dict[str, Any]]:
        """Generate initial hyperparameter samples."""
        samples = []
        
        # Random sampling
        for _ in range(self.n_samples):
            sample = self.space.sample()
            samples.append(sample)
        
        return samples
    
    def _evaluate_hyperparameters(self, params: Dict[str, Any], 
                                X_train: np.ndarray, y_train: np.ndarray,
                                X_val: np.ndarray, y_val: np.ndarray) -> HyperparameterResult:
        """Evaluate hyperparameters on validation set."""
        # Simulate training (in real implementation, this would train a model)
        training_time = self._simulate_training_time(params)
        validation_loss = self._simulate_validation_loss(params, X_val, y_val)
        score = -validation_loss  # Higher score = better (lower loss)
        
        # Energy estimate based on parameter complexity
        energy = self._calculate_energy(params)
        
        return HyperparameterResult(
            params=params,
            score=score,
            validation_loss=validation_loss,
            training_time=training_time,
            energy_estimate=energy
        )
    
    def _simulate_training_time(self, params: Dict[str, Any]) -> float:
        """Simulate training time based on hyperparameters."""
        base_time = 100.0  # Base time in seconds
        
        # Adjust based on parameters
        time_multiplier = 1.0
        
        # More epochs = more time
        time_multiplier *= params['epochs'] / 50.0
        
        # Larger batch size = less epochs needed but more memory
        time_multiplier *= (256.0 / params['batch_size']) ** 0.5
        
        # Lower learning rate = slower convergence
        time_multiplier *= (0.01 / params['learning_rate']) ** 0.5
        
        return base_time * time_multiplier
    
    def _simulate_validation_loss(self, params: Dict[str, Any], 
                                 X_val: np.ndarray, y_val: np.ndarray) -> float:
        """Simulate validation loss based on hyperparameters."""
        # Simulate loss landscape
        base_loss = 1.0
        
        # Learning rate affects final loss
        lr_factor = params['learning_rate'] / 0.01
        lr_loss = base_loss * (1.0 + np.exp(-10 * lr_factor))
        
        # Overfitting factor (high dropout, low regularization)
        overfitting_factor = params['dropout'] * 10.0 / (params['weight_decay'] + 0.001)
        
        # Batch size affects generalization
        batch_factor = 64.0 / params['batch_size']
        
        final_loss = lr_loss * (1.0 + overfitting_factor * batch_factor)
        
        # Add some noise
        noise = np.random.normal(0, 0.1)
        final_loss += noise
        
        return max(0.01, final_loss)  # Ensure positive loss
    
    def _calculate_energy(self, params: Dict[str, Any]) -> float:
        """Calculate energy estimate for hyperparameters."""
        energy = 0.0
        
        # Penalize extreme values
        if params['learning_rate'] < 0.001 or params['learning_rate'] > 0.1:
            energy += 10.0
        
        if params['batch_size'] < 16 or params['batch_size'] > 256:
            energy += 5.0
        
        if params['dropout'] > 0.5:
            energy += 3.0
        
        if params['weight_decay'] > 0.01:
            energy += 2.0
        
        return energy


def demo_hyperparameter_optimization():
    """Demonstrate hyperparameter optimization."""
    print("=== Hyperparameter Optimization Demo ===")
    
    # Create search space
    space = HyperparameterSpace(
        learning_rate=(0.001, 0.1),
        batch_size=(16, 128),
        epochs=(20, 100),
        dropout=(0.0, 0.3),
        weight_decay=(0.0, 0.01),
        momentum=(0.8, 0.99)
    )
    
    # Create optimizer
    optimizer = HyperparameterOptimizer(space, n_samples=15)
    
    # Generate dummy data
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)
    y_train = np.random.randint(0, 2, (1000,))
    X_val = np.random.randn(200, 10)
    y_val = np.random.randint(0, 2, (200,))
    
    # Optimize
    print("Optimizing hyperparameters...")
    best_result = optimizer.optimize(X_train, y_train, X_val, y_val)
    
    if best_result:
        print(f"\nBest hyperparameters:")
        for param, value in best_result.params.items():
            print(f"  {param}: {value}")
        
        print(f"\nValidation loss: {best_result.validation_loss:.4f}")
        print(f"Training time: {best_result.training_time:.1f}s")
        print(f"Energy estimate: {best_result.energy_estimate:.2f}")
        print(f"Score: {best_result.score:.4f}")
    else:
        print("No valid results found")


if __name__ == "__main__":
    demo_hyperparameter_optimization()
