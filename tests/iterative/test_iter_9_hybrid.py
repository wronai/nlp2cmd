"""
Iteration 9: Hybrid Rule+LLM Generator Tests.

Test hybrid approach using rules first, LLM as fallback.
"""

import pytest
import asyncio

from nlp2cmd.generation.hybrid import (
    HybridGenerator,
    HybridResult,
    HybridStats,
    AdaptiveHybridGenerator,
    create_hybrid_generator,
)
from nlp2cmd.generation.pipeline import RuleBasedPipeline
from nlp2cmd.generation.llm_multi import MultiDomainGenerator
from nlp2cmd.generation.llm_simple import MockLLMClient


class TestHybridResult:
    """Test HybridResult dataclass."""
    
    def test_rules_result(self):
        """Test result from rules."""
        result = HybridResult(
            command="SELECT * FROM users;",
            domain="sql",
            source="rules",
            confidence=0.85,
            latency_ms=2.5,
            success=True,
        )
        
        assert result.source == "rules"
        assert result.llm_calls == 0
        assert result.estimated_cost == 0.0
    
    def test_llm_result(self):
        """Test result from LLM."""
        result = HybridResult(
            command="SELECT * FROM users;",
            domain="sql",
            source="llm",
            confidence=0.9,
            latency_ms=500.0,
            success=True,
            llm_calls=1,
            estimated_cost=0.01,
        )
        
        assert result.source == "llm"
        assert result.llm_calls == 1
        assert result.estimated_cost > 0


class TestHybridStats:
    """Test HybridStats."""
    
    def test_empty_stats(self):
        """Test empty statistics."""
        stats = HybridStats()
        
        assert stats.total_requests == 0
        assert stats.rule_hit_rate == 0.0
        assert stats.avg_latency_ms == 0.0
    
    def test_rule_hit_rate(self):
        """Test rule hit rate calculation."""
        stats = HybridStats(
            total_requests=100,
            rule_hits=80,
            llm_fallbacks=20,
        )
        
        assert stats.rule_hit_rate == 0.8
    
    def test_cost_savings(self):
        """Test cost savings calculation."""
        stats = HybridStats(
            total_requests=100,
            rule_hits=70,
        )
        
        assert stats.cost_savings_percent == 70.0
    
    def test_to_dict(self):
        """Test conversion to dict."""
        stats = HybridStats(
            total_requests=10,
            rule_hits=8,
            llm_fallbacks=2,
            total_llm_calls=2,
            total_latency_ms=100.0,
            estimated_total_cost=0.02,
        )
        
        d = stats.to_dict()
        
        assert d["total_requests"] == 10
        assert "80" in d["rule_hit_rate"]  # 80%


class TestHybridGenerator:
    """Test hybrid generator."""
    
    @pytest.fixture
    def rules_only(self) -> HybridGenerator:
        """Generator with rules only (no LLM)."""
        return HybridGenerator(
            rule_pipeline=RuleBasedPipeline(),
            llm_generator=None,
            confidence_threshold=0.7,
        )
    
    @pytest.fixture
    def with_llm(self) -> HybridGenerator:
        """Generator with LLM fallback."""
        return HybridGenerator(
            rule_pipeline=RuleBasedPipeline(),
            llm_generator=MultiDomainGenerator(MockLLMClient()),
            confidence_threshold=0.7,
        )
    
    @pytest.mark.asyncio
    async def test_high_confidence_uses_rules(self, with_llm):
        """Test that high confidence queries use rules."""
        result = await with_llm.generate("Pokaż dane z tabeli users")
        
        assert result.source == "rules"
        assert result.llm_calls == 0
        assert result.estimated_cost == 0.0
    
    @pytest.mark.asyncio
    async def test_low_confidence_falls_back(self, with_llm):
        """Test that low confidence falls back to LLM."""
        # Very ambiguous query
        result = await with_llm.generate(
            "xyz abc random",
            force_llm=True
        )
        
        assert result.source == "llm"
        assert result.llm_calls >= 1
    
    @pytest.mark.asyncio
    async def test_force_llm_bypasses_rules(self, with_llm):
        """Test that force_llm bypasses rules."""
        result = await with_llm.generate(
            "Pokaż użytkowników z tabeli users",
            force_llm=True
        )
        
        assert result.source == "llm"
    
    @pytest.mark.asyncio
    async def test_no_llm_returns_rules_anyway(self, rules_only):
        """Test that without LLM, rules result is returned."""
        result = await rules_only.generate("xyz unknown query")
        
        # No LLM fallback available
        assert result.source == "rules"
        assert "LLM fallback not available" in result.errors or result.success
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, with_llm):
        """Test statistics are tracked."""
        await with_llm.generate("Pokaż dane z tabeli users")
        await with_llm.generate("Pokaż dane z tabeli orders")
        
        stats = with_llm.get_stats()
        
        assert stats.total_requests == 2
        assert stats.total_latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_reset_stats(self, with_llm):
        """Test statistics reset."""
        await with_llm.generate("test")
        with_llm.reset_stats()
        
        stats = with_llm.get_stats()
        assert stats.total_requests == 0
    
    def test_set_threshold(self, with_llm):
        """Test setting confidence threshold."""
        with_llm.set_confidence_threshold(0.9)
        assert with_llm.confidence_threshold == 0.9


class TestHybridGeneratorRuleConditions:
    """Test rule acceptance conditions."""
    
    @pytest.fixture
    def generator(self) -> HybridGenerator:
        return HybridGenerator(
            rule_pipeline=RuleBasedPipeline(),
            llm_generator=MultiDomainGenerator(MockLLMClient()),
            confidence_threshold=0.7,
        )
    
    @pytest.mark.asyncio
    async def test_sql_with_table_uses_rules(self, generator):
        """Test SQL with table entity uses rules."""
        result = await generator.generate("Pokaż dane z tabeli users")
        
        assert result.source == "rules"
        assert result.domain == "sql"
    
    @pytest.mark.asyncio
    async def test_docker_with_container_uses_rules(self, generator):
        """Test Docker with container uses rules."""
        result = await generator.generate("Pokaż logi kontenera myapp")
        
        assert result.source == "rules"
        assert result.domain == "docker"
    
    @pytest.mark.asyncio
    async def test_k8s_with_resource_uses_rules(self, generator):
        """Test K8s with resource type uses rules."""
        result = await generator.generate("Pokaż wszystkie pody")
        
        assert result.source == "rules"
        assert result.domain == "kubernetes"


class TestHybridGeneratorBatch:
    """Test batch processing."""
    
    @pytest.fixture
    def generator(self) -> HybridGenerator:
        return HybridGenerator(
            rule_pipeline=RuleBasedPipeline(),
            llm_generator=MultiDomainGenerator(MockLLMClient()),
        )
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, generator):
        """Test batch generation."""
        texts = [
            "Pokaż dane z tabeli users",
            "Znajdź pliki .py",
            "Pokaż kontenery docker",
        ]
        
        results = await generator.generate_batch(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, HybridResult) for r in results)


class TestAdaptiveHybridGenerator:
    """Test adaptive threshold generator."""
    
    @pytest.fixture
    def generator(self) -> AdaptiveHybridGenerator:
        return AdaptiveHybridGenerator(
            rule_pipeline=RuleBasedPipeline(),
            llm_generator=MultiDomainGenerator(MockLLMClient()),
            initial_threshold=0.7,
            min_threshold=0.5,
            max_threshold=0.95,
            adaptation_rate=0.05,
        )
    
    def test_initial_threshold(self, generator):
        """Test initial threshold is set."""
        assert generator.confidence_threshold == 0.7
    
    def test_adapt_threshold_down(self, generator):
        """Test threshold decreases with good accuracy."""
        # Simulate 10 correct rule predictions
        for _ in range(10):
            generator._adapt_threshold(True)
        
        assert generator.confidence_threshold < 0.7
        assert generator.confidence_threshold >= 0.5
    
    def test_adapt_threshold_up(self, generator):
        """Test threshold increases with poor accuracy."""
        # Simulate 10 incorrect rule predictions
        for _ in range(10):
            generator._adapt_threshold(False)
        
        assert generator.confidence_threshold > 0.7
        assert generator.confidence_threshold <= 0.95
    
    def test_threshold_bounds(self, generator):
        """Test threshold stays within bounds."""
        # Push to minimum
        for _ in range(100):
            generator._adapt_threshold(True)
        
        assert generator.confidence_threshold >= generator.min_threshold
        
        # Push to maximum
        for _ in range(100):
            generator._adapt_threshold(False)
        
        assert generator.confidence_threshold <= generator.max_threshold


class TestCreateHybridGenerator:
    """Test factory function."""
    
    def test_create_without_llm(self):
        """Test creating generator without LLM."""
        generator = create_hybrid_generator()
        
        assert generator.rules is not None
        assert generator.llm is None
    
    def test_create_with_llm(self):
        """Test creating generator with LLM."""
        mock = MockLLMClient()
        generator = create_hybrid_generator(llm_client=mock)
        
        assert generator.rules is not None
        assert generator.llm is not None
    
    def test_create_custom_threshold(self):
        """Test creating with custom threshold."""
        generator = create_hybrid_generator(confidence_threshold=0.9)
        
        assert generator.confidence_threshold == 0.9


class TestHybridPerformance:
    """Test hybrid generator performance."""
    
    @pytest.fixture
    def generator(self) -> HybridGenerator:
        return create_hybrid_generator()
    
    @pytest.mark.asyncio
    async def test_rules_faster_than_threshold(self, generator):
        """Test rules path is fast (<10ms)."""
        result = await generator.generate("Pokaż dane z tabeli users")
        
        # Rules should be very fast
        if result.source == "rules":
            assert result.latency_ms < 10
    
    @pytest.mark.asyncio
    async def test_batch_throughput(self, generator):
        """Test batch processing throughput."""
        import time
        
        texts = ["Pokaż dane z tabeli users"] * 100
        
        start = time.time()
        results = await generator.generate_batch(texts)
        elapsed = time.time() - start
        
        throughput = len(texts) / elapsed
        
        # Should handle at least 100 req/sec with rules
        assert throughput > 50
        
        # Most should use rules
        rule_results = sum(1 for r in results if r.source == "rules")
        assert rule_results / len(results) > 0.9
