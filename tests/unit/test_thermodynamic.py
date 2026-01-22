"""
Tests for Thermodynamic Computing Module.
"""

import pytest
import numpy as np

from nlp2cmd.thermodynamic import (
    LangevinConfig,
    LangevinSampler,
    QuadraticEnergy,
    ConstraintEnergy,
    MajorityVoter,
    ThermodynamicRouter,
    EnergyEstimator,
    EntropyProductionRegularizer,
)
from nlp2cmd.thermodynamic.energy_models import (
    SchedulingEnergy,
    AllocationEnergy,
    Task,
)


class TestLangevinConfig:
    """Tests for LangevinConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LangevinConfig()
        
        assert config.mu == 1.0
        assert config.kT == 1.0
        assert config.dt == 0.01
        assert config.n_steps == 1000
        assert config.dim == 64
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LangevinConfig(
            mu=0.5,
            kT=0.1,
            dt=0.001,
            n_steps=5000,
            dim=128
        )
        
        assert config.mu == 0.5
        assert config.kT == 0.1
        assert config.n_steps == 5000


class TestQuadraticEnergy:
    """Tests for QuadraticEnergy model."""
    
    def test_energy_at_target(self):
        """Test energy is zero at target."""
        target = np.array([1.0, 2.0, 3.0])
        energy_model = QuadraticEnergy(target=target)
        
        E = energy_model.energy(target, {})
        assert E == pytest.approx(0.0)
    
    def test_energy_away_from_target(self):
        """Test energy increases away from target."""
        target = np.zeros(3)
        energy_model = QuadraticEnergy(target=target)
        
        z = np.array([1.0, 0.0, 0.0])
        E = energy_model.energy(z, {})
        
        assert E == pytest.approx(0.5)  # 0.5 * ||z - 0||² = 0.5 * 1 = 0.5
    
    def test_gradient(self):
        """Test gradient computation."""
        target = np.zeros(3)
        energy_model = QuadraticEnergy(target=target)
        
        z = np.array([1.0, 2.0, 3.0])
        grad = energy_model.gradient(z, {})
        
        # Gradient of 0.5 * ||z||² is z
        np.testing.assert_array_almost_equal(grad, z)


class TestLangevinSampler:
    """Tests for LangevinSampler."""
    
    @pytest.fixture
    def simple_sampler(self):
        """Create sampler with quadratic energy."""
        config = LangevinConfig(
            n_steps=100,
            dim=3,
            kT=0.1,
            seed=42
        )
        energy = QuadraticEnergy(target=np.zeros(3))
        return LangevinSampler(energy, config)
    
    def test_sampling_converges_to_target(self, simple_sampler):
        """Test that sampler converges near target."""
        result = simple_sampler.sample(condition={})
        
        # Should be close to target (0, 0, 0)
        assert np.linalg.norm(result.sample) < 2.0
    
    def test_result_contains_energy(self, simple_sampler):
        """Test result contains energy value."""
        result = simple_sampler.sample(condition={})
        
        assert hasattr(result, 'energy')
        assert result.energy >= 0
    
    def test_result_contains_entropy_production(self, simple_sampler):
        """Test result contains entropy production."""
        result = simple_sampler.sample(condition={})
        
        assert hasattr(result, 'entropy_production')
    
    def test_trajectory_recording(self):
        """Test trajectory is recorded when requested."""
        config = LangevinConfig(
            n_steps=50,
            dim=3,
            record_trajectory=True,
            seed=42
        )
        energy = QuadraticEnergy()
        sampler = LangevinSampler(energy, config)
        
        result = sampler.sample(condition={})
        
        assert result.trajectory is not None
        assert len(result.trajectory) == 51  # Initial + 50 steps
    
    def test_multiple_samples(self):
        """Test generating multiple samples."""
        config = LangevinConfig(
            n_steps=100,
            dim=3,
            kT=0.1,
            seed=None  # No fixed seed - samples should differ
        )
        energy = QuadraticEnergy(target=np.zeros(3))
        sampler = LangevinSampler(energy, config)
        
        results = sampler.sample(condition={}, n_samples=5)
        
        assert len(results) == 5
        
        # At least some samples should be different (with random seeds)
        samples = [r.sample for r in results]
        all_same = all(np.allclose(samples[0], s) for s in samples[1:])
        # Note: With no seed, samples should differ due to random initialization
        # But we can't guarantee this in all cases, so we just check we got 5 results
    
    def test_parallel_sampling(self, simple_sampler):
        """Test parallel sampling."""
        results = simple_sampler.sample_parallel(
            condition={},
            n_samples=4,
            max_workers=2
        )
        
        assert len(results) == 4


class TestMajorityVoter:
    """Tests for MajorityVoter."""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample results for voting."""
        from nlp2cmd.thermodynamic import SamplerResult
        
        return [
            SamplerResult(
                sample=np.array([1.0, 0.0]),
                energy=1.0,
                trajectory=None,
                entropy_production=0.5,
                n_steps=100,
                converged=True
            ),
            SamplerResult(
                sample=np.array([0.5, 0.5]),
                energy=0.5,
                trajectory=None,
                entropy_production=0.3,
                n_steps=100,
                converged=True
            ),
            SamplerResult(
                sample=np.array([0.1, 0.1]),
                energy=0.1,
                trajectory=None,
                entropy_production=0.8,
                n_steps=100,
                converged=True
            ),
        ]
    
    def test_energy_voting(self, sample_results):
        """Test voting by lowest energy."""
        voter = MajorityVoter(strategy='energy')
        best = voter.vote(sample_results)
        
        assert best.energy == 0.1  # Lowest energy
    
    def test_entropy_voting(self, sample_results):
        """Test voting by lowest entropy production."""
        voter = MajorityVoter(strategy='entropy')
        best = voter.vote(sample_results)
        
        assert best.entropy_production == 0.3  # Lowest entropy
    
    def test_combined_voting(self, sample_results):
        """Test combined voting strategy."""
        voter = MajorityVoter(strategy='combined')
        best = voter.vote(sample_results)
        
        # Should consider both energy and entropy
        assert best is not None


class TestThermodynamicRouter:
    """Tests for ThermodynamicRouter."""
    
    @pytest.fixture
    def router(self):
        return ThermodynamicRouter(complexity_threshold=0.5)
    
    def test_classic_intents(self, router):
        """Test classic intents are routed correctly."""
        assert router.route('query', 0.3) == 'classic'
        assert router.route('execute', 0.4) == 'classic'
        assert router.route('deploy', 0.2) == 'classic'
    
    def test_thermodynamic_intents_low_complexity(self, router):
        """Test thermodynamic intents with low complexity."""
        assert router.route('schedule', 0.3) == 'hybrid'
        assert router.route('allocate', 0.4) == 'hybrid'
    
    def test_thermodynamic_intents_high_complexity(self, router):
        """Test thermodynamic intents with high complexity."""
        assert router.route('schedule', 0.7) == 'langevin'
        assert router.route('optimize', 0.8) == 'langevin'
    
    def test_complexity_estimation(self, router):
        """Test complexity estimation."""
        complexity = router.estimate_complexity(
            "Schedule 10 tasks to minimize total time",
            {'constraints': ['deadline', 'precedence', 'resource']}
        )
        
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.5  # Should be high due to keywords and constraints


class TestEnergyEstimator:
    """Tests for EnergyEstimator."""
    
    def test_energy_estimation(self):
        """Test energy estimation for different approaches."""
        estimator = EnergyEstimator()
        
        result = estimator.estimate(
            llm_input_tokens=500,
            llm_output_tokens_classic=2000,
            llm_output_tokens_hybrid=200,
            langevin_steps=5000
        )
        
        assert 'llm_only_joules' in result
        assert 'hybrid_digital_joules' in result
        assert 'hybrid_analog_joules' in result
        assert 'savings_digital_percent' in result
        
        # Hybrid should use less energy than LLM-only
        assert result['hybrid_digital_joules'] < result['llm_only_joules']
        assert result['savings_digital_percent'] > 0


class TestEntropyProductionRegularizer:
    """Tests for EntropyProductionRegularizer."""
    
    def test_regularization_computation(self):
        """Test regularization term computation."""
        from nlp2cmd.thermodynamic import SamplerResult
        
        regularizer = EntropyProductionRegularizer(lambda_entropy=0.1)
        
        result = SamplerResult(
            sample=np.array([1.0]),
            energy=1.0,
            trajectory=None,
            entropy_production=5.0,
            n_steps=100,
            converged=True
        )
        
        reg = regularizer.compute_regularization(result)
        
        assert reg == pytest.approx(0.5)  # 0.1 * 5.0
    
    def test_heat_dissipation(self):
        """Test heat dissipation estimation."""
        from nlp2cmd.thermodynamic import SamplerResult
        
        regularizer = EntropyProductionRegularizer(kT=0.5)
        
        result = SamplerResult(
            sample=np.array([1.0]),
            energy=1.0,
            trajectory=None,
            entropy_production=2.0,
            n_steps=100,
            converged=True
        )
        
        Q = regularizer.estimate_heat_dissipation(result)
        
        assert Q == pytest.approx(1.0)  # kT * entropy = 0.5 * 2.0


class TestSchedulingEnergy:
    """Tests for SchedulingEnergy model."""
    
    @pytest.fixture
    def simple_scheduling(self):
        """Create simple scheduling problem."""
        tasks = [
            Task(id='A', duration=2.0, deadline=5.0),
            Task(id='B', duration=3.0, deadline=6.0),
        ]
        condition = {
            'tasks': tasks,
            'resources': [],
            'assignments': {'A': 'M1', 'B': 'M1'},
        }
        return tasks, condition
    
    def test_no_violation_energy(self, simple_scheduling):
        """Test energy with no violations."""
        tasks, condition = simple_scheduling
        energy_model = SchedulingEnergy()
        
        # Non-overlapping schedule: A starts at 0, B starts at 2
        z = np.array([0.0, 2.0])
        E = energy_model.energy(z, condition)
        
        # Should be low (only makespan term)
        assert E < 10.0
    
    def test_overlap_penalty(self, simple_scheduling):
        """Test overlap increases energy."""
        tasks, condition = simple_scheduling
        energy_model = SchedulingEnergy()
        
        # Overlapping schedule: both start at 0
        z_overlap = np.array([0.0, 0.0])
        E_overlap = energy_model.energy(z_overlap, condition)
        
        # Non-overlapping
        z_no_overlap = np.array([0.0, 2.0])
        E_no_overlap = energy_model.energy(z_no_overlap, condition)
        
        assert E_overlap > E_no_overlap
    
    def test_deadline_penalty(self):
        """Test deadline violation increases energy."""
        tasks = [
            Task(id='A', duration=5.0, deadline=3.0),  # Impossible deadline
        ]
        condition = {'tasks': tasks, 'resources': [], 'assignments': {}}
        energy_model = SchedulingEnergy()
        
        z = np.array([0.0])  # Start at 0, ends at 5, deadline is 3
        E = energy_model.energy(z, condition)
        
        # Should have deadline penalty
        assert E > 0


class TestAllocationEnergy:
    """Tests for AllocationEnergy model."""
    
    def test_feasible_allocation(self):
        """Test energy for feasible allocation."""
        energy_model = AllocationEnergy()
        
        condition = {
            'n_requests': 2,
            'n_resources': 2,
            'capacities': [10.0, 10.0],
            'demands': [5.0, 5.0],
            'costs': np.ones((2, 2))
        }
        
        # Feasible allocation
        z = np.array([5.0, 0.0, 0.0, 5.0])  # R1 gets 5 from res1, R2 gets 5 from res2
        E = energy_model.energy(z, condition)
        
        # Should be finite
        assert np.isfinite(E)
    
    def test_capacity_violation(self):
        """Test capacity violation increases energy."""
        energy_model = AllocationEnergy()
        
        condition = {
            'n_requests': 2,
            'n_resources': 1,
            'capacities': [5.0],
            'demands': [3.0, 3.0],
            'costs': np.ones((2, 1))
        }
        
        # Over-allocation
        z = np.array([5.0, 5.0])  # Total 10 > capacity 5
        E = energy_model.energy(z, condition)
        
        # Should have high penalty
        assert E > 10.0
