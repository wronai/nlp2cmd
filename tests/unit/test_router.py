"""
Tests for Decision Router.
"""

import pytest
from nlp2cmd.router import (
    DecisionRouter,
    RoutingDecision,
    RoutingResult,
    RouterConfig,
)


class TestRoutingDecision:
    """Tests for RoutingDecision enum."""
    
    def test_all_decisions_exist(self):
        """Test all routing decisions are defined."""
        assert RoutingDecision.DIRECT.value == "direct"
        assert RoutingDecision.LLM_PLANNER.value == "llm_planner"
        assert RoutingDecision.CLARIFICATION.value == "clarification"
        assert RoutingDecision.REJECT.value == "reject"


class TestRoutingResult:
    """Tests for RoutingResult dataclass."""
    
    def test_basic_result(self):
        """Test creating a basic routing result."""
        result = RoutingResult(
            decision=RoutingDecision.DIRECT,
            reason="Simple query",
        )
        assert result.decision == RoutingDecision.DIRECT
        assert result.reason == "Simple query"
        assert result.confidence == 1.0
        assert result.suggested_actions == []
    
    def test_result_with_all_fields(self):
        """Test result with all fields."""
        result = RoutingResult(
            decision=RoutingDecision.LLM_PLANNER,
            reason="Complex multi-step",
            confidence=0.85,
            suggested_actions=["sql_select", "summarize"],
            metadata={"multi_step": True},
        )
        assert result.confidence == 0.85
        assert len(result.suggested_actions) == 2
        assert result.metadata["multi_step"] is True


class TestRouterConfig:
    """Tests for RouterConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RouterConfig()
        
        assert "select" in config.simple_intents
        assert "analyze" in config.complex_intents
        assert config.entity_threshold == 5
        assert config.confidence_threshold == 0.6
        assert "then" in config.multi_step_keywords
        assert "analyze" in config.complex_keywords
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RouterConfig(
            simple_intents=["get", "list"],
            complex_intents=["migrate"],
            entity_threshold=3,
            confidence_threshold=0.8,
        )
        assert config.simple_intents == ["get", "list"]
        assert config.entity_threshold == 3


class TestDecisionRouter:
    """Tests for DecisionRouter."""
    
    @pytest.fixture
    def router(self):
        """Create router instance."""
        return DecisionRouter()
    
    def test_simple_intent_direct(self, router):
        """Test simple intent routes to direct execution."""
        result = router.route(
            intent="select",
            entities={"table": "users"},
            text="show users",  # No multi-step keywords
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.DIRECT
        assert "simple" in result.reason.lower()
    
    def test_complex_intent_llm(self, router):
        """Test complex intent routes to LLM planner."""
        result = router.route(
            intent="analyze",
            entities={"table": "logs", "timerange": "last week"},
            text="analyze error patterns in logs",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
    
    def test_low_confidence_clarification(self, router):
        """Test low confidence triggers clarification."""
        result = router.route(
            intent="unknown",
            entities={},
            text="do something with data",
            confidence=0.4,
        )
        assert result.decision == RoutingDecision.CLARIFICATION
    
    def test_very_low_confidence_reject(self, router):
        """Test very low confidence triggers rejection."""
        result = router.route(
            intent="unknown",
            entities={},
            text="asdfghjkl",
            confidence=0.1,
        )
        assert result.decision == RoutingDecision.REJECT
    
    def test_multi_step_keywords_llm(self, router):
        """Test multi-step keywords route to LLM."""
        result = router.route(
            intent="select",
            entities={"table": "users"},
            text="get users and then count by status",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
        assert result.metadata.get("multi_step") is True
    
    def test_complex_keywords_llm(self, router):
        """Test complex analysis keywords route to LLM."""
        result = router.route(
            intent="select",
            entities={"table": "sales"},
            text="compare sales trends between regions",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
        assert result.metadata.get("complex_analysis") is True
    
    def test_high_entity_count_llm(self, router):
        """Test high entity count routes to LLM."""
        result = router.route(
            intent="select",
            entities={
                "table": "orders",
                "columns": ["id", "total"],
                "filter1": "status = active",
                "filter2": "amount > 100",
                "join": "users",
                "groupby": "user_id",
            },
            text="complex query with many parameters",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
    
    def test_joins_entity_llm(self, router):
        """Test joins in entities routes to LLM."""
        result = router.route(
            intent="select",
            entities={"table": "orders", "joins": ["users", "products"]},
            text="get orders with user info",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
    
    def test_foreach_keyword_llm(self, router):
        """Test foreach keyword routes to LLM."""
        result = router.route(
            intent="file_search",
            entities={"pattern": "*.log"},
            text="for each log file count errors",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
    
    def test_register_intent_mapping(self, router):
        """Test registering custom intent mapping."""
        router.register_intent_mapping("custom_intent", "custom_action")
        router.add_simple_intent("custom_intent")
        
        result = router.route(
            intent="custom_intent",
            entities={"param": "value"},
            text="do custom thing",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.DIRECT
        assert "custom_action" in result.suggested_actions
    
    def test_add_complex_intent(self, router):
        """Test adding a complex intent."""
        router.add_complex_intent("new_complex")
        
        result = router.route(
            intent="new_complex",
            entities={},
            text="run new complex operation",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.LLM_PLANNER
    
    def test_context_handling(self, router):
        """Test context is passed through."""
        result = router.route(
            intent="select",
            entities={"table": "users"},
            text="show users",
            confidence=0.9,
            context={"database": "production"},
        )
        # Context doesn't change routing, just passed through
        assert result.decision == RoutingDecision.DIRECT


class TestRouterEdgeCases:
    """Edge case tests for Decision Router."""
    
    @pytest.fixture
    def router(self):
        return DecisionRouter()
    
    def test_empty_text(self, router):
        """Test handling empty text."""
        result = router.route(
            intent="select",
            entities={"table": "users"},
            text="",
            confidence=0.9,
        )
        assert result.decision == RoutingDecision.DIRECT
    
    def test_empty_entities(self, router):
        """Test handling empty entities."""
        result = router.route(
            intent="help",
            entities={},
            text="help me",
            confidence=0.9,
        )
        assert result.decision in (RoutingDecision.DIRECT, RoutingDecision.LLM_PLANNER)
    
    def test_special_characters_in_text(self, router):
        """Test handling special characters."""
        result = router.route(
            intent="select",
            entities={"filter": "name = 'O\\'Brien'"},
            text="find user O'Brien",
            confidence=0.9,
        )
        # Should not crash
        assert result.decision in (RoutingDecision.DIRECT, RoutingDecision.LLM_PLANNER)
    
    def test_unicode_in_text(self, router):
        """Test handling unicode."""
        result = router.route(
            intent="select",
            entities={"name": "日本語"},
            text="find 日本語 entries",
            confidence=0.9,
        )
        assert result.decision in (RoutingDecision.DIRECT, RoutingDecision.LLM_PLANNER)
    
    def test_custom_config(self):
        """Test router with custom config."""
        config = RouterConfig(
            simple_intents=["simple_only"],
            complex_intents=[],
            entity_threshold=2,
            confidence_threshold=0.9,
        )
        router = DecisionRouter(config=config)
        
        # Only "simple_only" is simple now
        result = router.route(
            intent="select",
            entities={"a": 1, "b": 2, "c": 3},
            text="something",
            confidence=0.95,
        )
        # High entity count should trigger LLM
        assert result.decision == RoutingDecision.LLM_PLANNER
