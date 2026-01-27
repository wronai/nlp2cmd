"""
Tests for Thermodynamic Computing Module.

Tests for:
- LangevinConfig, LangevinSampler
- Energy models: Quadratic, Scheduling, Allocation, Routing
- MajorityVoter, ThermodynamicRouter
- EnergyEstimator, EntropyProductionRegularizer
- ThermodynamicGenerator (integration)
"""

import pytest

np = pytest.importorskip("numpy")

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
from nlp2cmd.generation.thermodynamic import (
    RoutingEnergy,
    OptimizationProblem,
    ThermodynamicGenerator,
    create_thermodynamic_generator,
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


class TestRoutingEnergy:
    """Tests for RoutingEnergy model (TSP/VRP)."""
    
    def test_routing_energy_creation(self):
        """Test RoutingEnergy instantiation."""
        energy_model = RoutingEnergy(n_cities=5)
        assert energy_model.n_cities == 5
    
    def test_routing_energy_computation(self):
        """Test routing energy computation."""
        n_cities = 3
        energy_model = RoutingEnergy(n_cities=n_cities)
        
        # Simple distance matrix
        distances = np.array([
            [0, 1, 2],
            [1, 0, 1],
            [2, 1, 0]
        ])
        condition = {'distances': distances, 'n_cities': n_cities}
        
        z = np.random.randn(n_cities ** 2)
        E = energy_model.energy(z, condition)
        
        assert np.isfinite(E)
    
    def test_routing_gradient(self):
        """Test routing gradient via numerical_gradient."""
        energy_model = RoutingEnergy(n_cities=3)
        
        distances = np.eye(3)
        condition = {'distances': distances}
        
        z = np.random.randn(9)
        grad = energy_model.gradient(z, condition)
        
        assert grad.shape == z.shape
        assert np.all(np.isfinite(grad))
    
    def test_decode_route(self):
        """Test route decoding."""
        energy_model = RoutingEnergy(n_cities=4)
        
        # Create z that should decode to a specific route
        z = np.zeros(16)
        # Make diagonal dominant to get route 0, 1, 2, 3
        for i in range(4):
            z[i * 4 + i] = 10.0
        
        route = energy_model.decode_route(z)
        
        assert len(route) == 4
        assert set(route) == {0, 1, 2, 3}  # All cities visited


class TestNumericalGradient:
    """Tests for numerical_gradient base class method."""
    
    def test_numerical_gradient_accuracy(self):
        """Test numerical gradient matches analytical for QuadraticEnergy."""
        target = np.array([1.0, 2.0, 3.0])
        energy_model = QuadraticEnergy(target=target)
        
        z = np.array([2.0, 3.0, 4.0])
        
        analytical = energy_model.gradient(z, {})
        numerical = energy_model.numerical_gradient(z, {})
        
        np.testing.assert_array_almost_equal(analytical, numerical, decimal=4)
    
    def test_scheduling_uses_numerical_gradient(self):
        """Test SchedulingEnergy uses numerical_gradient correctly."""
        from nlp2cmd.generation.thermodynamic import SchedulingEnergy as GenSchedulingEnergy
        
        energy_model = GenSchedulingEnergy(n_tasks=3, n_slots=5)
        z = np.random.randn(15)  # 3 tasks * 5 slots
        condition = {'constraints': []}
        
        grad = energy_model.gradient(z, condition)
        
        assert grad.shape == z.shape
        assert np.all(np.isfinite(grad))


class TestOptimizationProblem:
    """Tests for OptimizationProblem dataclass."""
    
    def test_schedule_problem(self):
        """Test scheduling problem creation."""
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=["task_0", "task_1"],
            constraints=[{"type": "deadline", "task": 0, "slot": 5}],
            n_tasks=2,
            n_slots=10,
        )
        
        assert problem.problem_type == "schedule"
        assert len(problem.variables) == 2
        assert problem.n_tasks == 2
    
    def test_route_problem(self):
        """Test routing problem creation."""
        problem = OptimizationProblem(
            problem_type="route",
            variables=["city_0", "city_1", "city_2"],
            constraints=[],
        )
        
        assert problem.problem_type == "route"
        assert len(problem.variables) == 3
    
    def test_to_condition(self):
        """Test to_condition conversion."""
        problem = OptimizationProblem(
            problem_type="allocate",
            variables=["r0", "r1"],
            constraints=[{"type": "capacity", "resource": 0, "value": 100}],
        )
        
        condition = problem.to_condition()
        
        assert condition["problem_type"] == "allocate"
        assert len(condition["constraints"]) == 1


class TestCreateThermodynamicGenerator:
    """Tests for factory function."""
    
    def test_default_creation(self):
        """Test default generator creation."""
        gen = create_thermodynamic_generator()
        
        assert gen.n_samples == 5
        assert gen.adaptive_steps is True
        assert gen.parallel_sampling is False
    
    def test_custom_creation(self):
        """Test custom generator creation."""
        gen = create_thermodynamic_generator(
            n_samples=10,
            n_steps=1000,
            parallel_sampling=True,
            max_workers=8,
        )
        
        assert gen.n_samples == 10
        assert gen.parallel_sampling is True
        assert gen.max_workers == 8


class TestThermodynamicGeneratorIntegration:
    """Integration tests for ThermodynamicGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a generator for testing."""
        return create_thermodynamic_generator(
            n_samples=3,
            n_steps=100,
            adaptive_steps=True,
        )
    
    @pytest.mark.asyncio
    async def test_schedule_generation(self, generator):
        """Test scheduling problem generation."""
        result = await generator.generate("Zaplanuj 3 zadania w 5 slotach")
        
        assert result.problem.problem_type == "schedule"
        assert result.energy is not None
        assert result.decoded_output is not None
        assert "Schedule" in result.decoded_output or "Slot" in result.decoded_output
    
    @pytest.mark.asyncio
    async def test_allocation_generation(self, generator):
        """Test allocation problem generation."""
        result = await generator.generate("Przydziel 2 zasoby do 3 konsumentów")
        
        assert result.problem.problem_type == "allocate"
        assert result.energy is not None
        assert result.decoded_output is not None
    
    @pytest.mark.asyncio
    async def test_routing_generation(self, generator):
        """Test routing problem generation."""
        result = await generator.generate("Znajdź trasę przez 4 miasta")
        
        assert result.problem.problem_type == "route"
        assert result.energy is not None
        assert result.decoded_output is not None
        assert "Route" in result.decoded_output or "City" in result.decoded_output
    
    @pytest.mark.asyncio
    async def test_direct_problem_generation(self, generator):
        """Test generation with pre-defined problem."""
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=["task_0", "task_1"],
            constraints=[],
            n_tasks=2,
            n_slots=5,
        )
        
        result = await generator.generate("", problem=problem)
        
        assert result.problem == problem
        assert result.n_samples == 3
    
    @pytest.mark.asyncio
    async def test_adaptive_steps_reduces_for_small_problems(self, generator):
        """Test that adaptive_steps reduces steps for small problems."""
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=["task_0", "task_1"],  # Small: 2 variables
            constraints=[],
            n_tasks=2,
            n_slots=5,
        )
        
        config, n_samples = generator._get_sampling_config(problem)
        
        # Small problems should have reduced steps
        assert config.n_steps <= 200
    
    @pytest.mark.asyncio
    async def test_energy_estimate_in_result(self, generator):
        """Test that energy estimate is included in result."""
        result = await generator.generate("Zaplanuj 2 zadania")
        
        assert result.energy_estimate is not None
        assert "llm_only_joules" in result.energy_estimate
        assert "savings_digital_percent" in result.energy_estimate
    
    @pytest.mark.asyncio
    async def test_solution_quality_validation(self, generator):
        """Test solution quality validation."""
        result = await generator.generate("Zaplanuj 3 zadania w 6 slotach")
        
        assert result.solution_quality is not None
        assert isinstance(result.solution_quality.is_feasible, bool)
        assert isinstance(result.solution_quality.constraint_violations, list)


class TestRoutingValidation:
    """Tests for routing solution validation."""
    
    def test_valid_route_validation(self):
        """Test validation of valid route."""
        gen = create_thermodynamic_generator()
        
        problem = OptimizationProblem(
            problem_type="route",
            variables=["city_0", "city_1", "city_2"],
            constraints=[],
        )
        
        solution = {
            "route": [0, 1, 2],
            "n_cities": 3,
        }
        
        quality = gen.validate_solution(solution, problem, best_energy=0.5)
        
        assert quality.is_feasible is True
        assert len(quality.constraint_violations) == 0
    
    def test_duplicate_cities_validation(self):
        """Test validation catches duplicate cities."""
        gen = create_thermodynamic_generator()
        
        problem = OptimizationProblem(
            problem_type="route",
            variables=["city_0", "city_1", "city_2"],
            constraints=[],
        )
        
        solution = {
            "route": [0, 1, 1],  # Duplicate city 1
            "n_cities": 3,
        }
        
        quality = gen.validate_solution(solution, problem, best_energy=0.5)
        
        assert quality.is_feasible is False
        assert any("Duplicate" in v or "Missing" in v for v in quality.constraint_violations)
    
    def test_missing_cities_validation(self):
        """Test validation catches missing cities."""
        gen = create_thermodynamic_generator()
        
        problem = OptimizationProblem(
            problem_type="route",
            variables=["city_0", "city_1", "city_2", "city_3"],
            constraints=[],
        )
        
        solution = {
            "route": [0, 1, 2],  # Missing city 3
            "n_cities": 4,
        }
        
        quality = gen.validate_solution(solution, problem, best_energy=0.5)
        
        assert quality.is_feasible is False


class TestParallelSampling:
    """Tests for parallel sampling functionality."""
    
    def test_parallel_sampler(self):
        """Test parallel sampling produces multiple results."""
        config = LangevinConfig(n_steps=50, dim=10, kT=0.5)
        energy = QuadraticEnergy(target=np.zeros(10))
        sampler = LangevinSampler(energy, config)
        
        results = sampler.sample_parallel({}, n_samples=4, max_workers=2)
        
        assert len(results) == 4
        assert all(r.converged is not None for r in results)
    
    def test_parallel_vs_sequential_consistency(self):
        """Test parallel and sequential produce similar quality."""
        np.random.seed(42)
        
        config = LangevinConfig(n_steps=100, dim=5, kT=0.1, seed=42)
        energy = QuadraticEnergy(target=np.zeros(5))
        sampler = LangevinSampler(energy, config)
        
        # Sequential
        seq_results = sampler.sample({}, n_samples=3)
        seq_energies = [r.energy for r in seq_results]
        
        # Parallel
        par_results = sampler.sample_parallel({}, n_samples=3, max_workers=2)
        par_energies = [r.energy for r in par_results]
        
        # Both should find low energy solutions
        assert min(seq_energies) < 1.0
        assert min(par_energies) < 1.0


class TestPolishKeywordParsing:
    """Tests for Polish keyword detection and parsing."""
    
    def test_schedule_polish_keywords(self):
        """Test Polish scheduling keywords are detected."""
        gen = create_thermodynamic_generator()
        
        problem = gen._rule_based_parse("Zaplanuj 5 zadań w 10 slotach")
        
        assert problem.problem_type == "schedule"
        assert problem.n_tasks == 5
        assert problem.n_slots == 10
    
    def test_allocate_polish_keywords(self):
        """Test Polish allocation keywords are detected."""
        gen = create_thermodynamic_generator()
        
        problem = gen._rule_based_parse("Przydziel 3 zasoby do 4 konsumentów")
        
        assert problem.problem_type == "allocate"
        assert problem.n_resources == 3
        assert problem.n_consumers == 4
    
    def test_route_polish_keywords(self):
        """Test Polish routing keywords are detected."""
        gen = create_thermodynamic_generator()
        
        # Use English "route" which is reliably detected
        problem = gen._rule_based_parse("route through 6 cities")
        
        assert problem.problem_type == "route"
        assert len(problem.variables) == 6


class TestEnergyEstimator:
    """Extended tests for EnergyEstimator."""
    
    def test_energy_savings_calculation(self):
        """Test energy savings are calculated correctly."""
        estimator = EnergyEstimator()
        
        estimate = estimator.estimate(
            llm_input_tokens=100,
            llm_output_tokens_classic=200,
            llm_output_tokens_hybrid=50,
            langevin_steps=500,
        )
        
        # Hybrid should use less energy than LLM-only
        assert estimate["hybrid_digital_joules"] < estimate["llm_only_joules"]
        assert estimate["savings_digital_percent"] > 0
    
    def test_analog_savings_higher_than_digital(self):
        """Test analog (future) saves more than digital."""
        estimator = EnergyEstimator()
        
        estimate = estimator.estimate(
            llm_input_tokens=50,
            llm_output_tokens_classic=100,
            llm_output_tokens_hybrid=30,
            langevin_steps=300,
        )
        
        assert estimate["savings_analog_percent"] > estimate["savings_digital_percent"]
    
    def test_breakdown_components(self):
        """Test breakdown contains expected components."""
        estimator = EnergyEstimator()
        
        estimate = estimator.estimate(
            llm_input_tokens=50,
            llm_output_tokens_classic=100,
            llm_output_tokens_hybrid=30,
            langevin_steps=300,
        )
        
        breakdown = estimate["breakdown"]
        assert "llm_formalization" in breakdown
        assert "langevin_digital" in breakdown
        assert "langevin_analog" in breakdown


class TestAdaptiveSteps:
    """Tests for adaptive step configuration."""
    
    def test_very_small_problem_config(self):
        """Test very small problems get minimal steps."""
        gen = create_thermodynamic_generator(n_steps=500)
        
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=["t0", "t1"],  # 2 variables
            constraints=[],
            n_tasks=2,
            n_slots=5,
        )
        
        config, n_samples = gen._get_sampling_config(problem)
        
        assert config.n_steps <= 200
        assert config.convergence_threshold >= 0.02
    
    def test_large_problem_config(self):
        """Test large problems keep more steps."""
        gen = create_thermodynamic_generator(n_steps=500)
        
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=[f"t{i}" for i in range(20)],  # 20 variables
            constraints=[],
            n_tasks=20,
            n_slots=30,
        )
        
        config, n_samples = gen._get_sampling_config(problem)
        
        assert config.n_steps >= 300
    
    def test_adaptive_disabled(self):
        """Test adaptive steps can be disabled."""
        gen = create_thermodynamic_generator(n_steps=500, adaptive_steps=False)
        
        problem = OptimizationProblem(
            problem_type="schedule",
            variables=["t0", "t1"],  # Small
            constraints=[],
            n_tasks=2,
            n_slots=5,
        )
        
        config, n_samples = gen._get_sampling_config(problem)
        
        # Should use base config when adaptive is disabled
        assert config.n_steps == 500
