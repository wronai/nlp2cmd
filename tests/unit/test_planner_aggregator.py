"""
Tests for LLM Planner and Result Aggregator.
"""

import json
import pytest
from nlp2cmd.planner import (
    LLMPlanner,
    PlannerConfig,
    PlanningResult,
)
from nlp2cmd.aggregator import (
    ResultAggregator,
    AggregatedResult,
    OutputFormat,
)
from nlp2cmd.executor import (
    ExecutionResult,
    StepResult,
    StepStatus,
)
from nlp2cmd.registry import ActionRegistry


# =============================================================================
# LLM Planner Tests
# =============================================================================

class TestPlannerConfig:
    """Tests for PlannerConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PlannerConfig()
        assert config.max_steps == 10
        assert config.require_confirmation_for_destructive is True
        assert config.include_examples is True
        assert config.temperature == 0.2
        assert config.max_tokens == 2000
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PlannerConfig(
            max_steps=5,
            temperature=0.5,
            include_examples=False,
        )
        assert config.max_steps == 5
        assert config.temperature == 0.5
        assert config.include_examples is False


class TestPlanningResult:
    """Tests for PlanningResult."""
    
    def test_success_result(self):
        """Test successful planning result."""
        from nlp2cmd.executor import ExecutionPlan, PlanStep
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = PlanningResult(
            success=True,
            plan=plan,
            confidence=0.95,
        )
        
        assert result.success is True
        assert result.plan is not None
        assert result.error is None
        assert result.confidence == 0.95
    
    def test_failure_result(self):
        """Test failed planning result."""
        result = PlanningResult(
            success=False,
            error="Could not parse response",
            raw_response="invalid json",
        )
        
        assert result.success is False
        assert result.plan is None
        assert result.error == "Could not parse response"


class TestLLMPlanner:
    """Tests for LLMPlanner."""
    
    @pytest.fixture
    def planner(self):
        """Create planner without LLM client (uses rule-based fallback)."""
        return LLMPlanner()
    
    def test_rule_based_plan_sql(self, planner):
        """Test rule-based planning for SQL."""
        result = planner.plan(
            intent="select",
            entities={"table": "users", "columns": ["id", "name"]},
            text="show all users",
        )
        
        assert result.success is True
        assert result.plan is not None
        assert len(result.plan.steps) >= 1
        assert result.plan.steps[0].action == "sql_select"
    
    def test_rule_based_plan_shell(self, planner):
        """Test rule-based planning for shell."""
        result = planner.plan(
            intent="file_search",
            entities={"glob": "*.log"},
            text="find all log files",
        )
        
        assert result.success is True
        assert "shell_find" in result.plan.steps[0].action
    
    def test_rule_based_plan_with_context(self, planner):
        """Test planning with context."""
        result = planner.plan(
            intent="select",
            entities={"table": "orders"},
            text="get orders",
            context={"database": "production"},
        )
        
        assert result.success is True
    
    def test_rule_based_plan_with_domain(self, planner):
        """Test planning with domain filter."""
        result = planner.plan(
            intent="get",
            entities={"resource": "pods"},
            text="show all pods",
            domain="kubernetes",
        )
        
        assert result.success is True
    
    def test_get_action_catalog(self, planner):
        """Test getting action catalog."""
        catalog = planner.get_action_catalog()
        
        assert "Available actions:" in catalog
        assert "sql_select" in catalog
    
    def test_get_action_catalog_by_domain(self, planner):
        """Test getting action catalog by domain."""
        catalog = planner.get_action_catalog(domain="docker")
        
        assert "docker_ps" in catalog
        assert "sql_select" not in catalog
    
    def test_parse_json_response(self, planner):
        """Test parsing JSON response."""
        response = '{"steps": [{"action": "test", "params": {}}]}'
        result = planner._parse_response(response)
        
        assert result is not None
        assert "steps" in result
    
    def test_parse_json_with_markdown(self, planner):
        """Test parsing JSON wrapped in markdown."""
        response = '''```json
{"steps": [{"action": "test", "params": {}}]}
```'''
        result = planner._parse_response(response)
        
        assert result is not None
        assert "steps" in result
    
    def test_parse_invalid_json(self, planner):
        """Test parsing invalid JSON returns None."""
        result = planner._parse_response("not json at all")
        assert result is None
    
    def test_plan_validation_failure(self, planner):
        """Test plan that fails validation."""
        # Create planner with mock that returns invalid plan
        class MockLLM:
            def messages(self):
                pass
        
        # Manually test validation
        from nlp2cmd.executor import ExecutionPlan, PlanStep
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="nonexistent_action"),
        ])
        
        is_valid, errors = planner.validator.validate(plan)
        assert is_valid is False


class TestLLMPlannerExamples:
    """Tests for LLM Planner examples."""
    
    def test_examples_have_valid_structure(self):
        """Test that built-in examples have valid structure."""
        planner = LLMPlanner()
        
        for example in planner.EXAMPLES:
            plan_dict = example["plan"]
            
            # Check basic structure
            assert "steps" in plan_dict
            assert len(plan_dict["steps"]) > 0
            
            for step in plan_dict["steps"]:
                assert "action" in step
                # Params may contain $references which are validated at runtime


# =============================================================================
# Result Aggregator Tests
# =============================================================================

class TestOutputFormat:
    """Tests for OutputFormat enum."""
    
    def test_all_formats_exist(self):
        """Test all output formats are defined."""
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.SUMMARY.value == "summary"


class TestResultAggregator:
    """Tests for ResultAggregator."""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()
    
    @pytest.fixture
    def sample_execution_result(self):
        """Create sample execution result."""
        return ExecutionResult(
            trace_id="abc123",
            success=True,
            steps=[
                StepResult(
                    step_index=0,
                    action="sql_select",
                    status=StepStatus.SUCCESS,
                    result=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
                    duration_ms=15.5,
                ),
                StepResult(
                    step_index=1,
                    action="summarize_results",
                    status=StepStatus.SUCCESS,
                    result="2 users found",
                    duration_ms=5.2,
                ),
            ],
            final_result="2 users found",
            total_duration_ms=20.7,
        )
    
    def test_aggregate_basic(self, aggregator, sample_execution_result):
        """Test basic aggregation."""
        result = aggregator.aggregate(sample_execution_result)
        
        assert isinstance(result, AggregatedResult)
        assert result.success is True
        assert result.step_count == 2
        assert result.trace_id == "abc123"
    
    def test_aggregate_with_details(self, aggregator, sample_execution_result):
        """Test aggregation with step details."""
        result = aggregator.aggregate(
            sample_execution_result,
            include_details=True,
        )
        
        assert len(result.details) == 2
        assert result.details[0]["action"] == "sql_select"
        assert result.details[0]["status"] == "success"
    
    def test_aggregate_json_format(self, aggregator, sample_execution_result):
        """Test JSON format output."""
        result = aggregator.aggregate(
            sample_execution_result,
            format=OutputFormat.JSON,
        )
        
        assert result.format == OutputFormat.JSON
        # Data should be returned as-is for JSON
        assert result.data == "2 users found"
    
    def test_aggregate_text_format(self, aggregator, sample_execution_result):
        """Test text format output."""
        result = aggregator.aggregate(
            sample_execution_result,
            format=OutputFormat.TEXT,
        )
        
        assert result.format == OutputFormat.TEXT
        assert isinstance(result.data, str)
    
    def test_aggregate_table_format(self, aggregator):
        """Test table format output."""
        execution_result = ExecutionResult(
            trace_id="test",
            success=True,
            steps=[
                StepResult(
                    step_index=0,
                    action="sql_select",
                    status=StepStatus.SUCCESS,
                    result=[
                        {"id": 1, "name": "Alice", "age": 30},
                        {"id": 2, "name": "Bob", "age": 25},
                    ],
                    duration_ms=10.0,
                ),
            ],
            final_result=[
                {"id": 1, "name": "Alice", "age": 30},
                {"id": 2, "name": "Bob", "age": 25},
            ],
            total_duration_ms=10.0,
        )
        
        result = aggregator.aggregate(
            execution_result,
            format=OutputFormat.TABLE,
        )
        
        assert result.format == OutputFormat.TABLE
        assert "id" in result.data
        assert "name" in result.data
        assert "|" in result.data or "-" in result.data  # Table formatting
    
    def test_aggregate_markdown_format(self, aggregator):
        """Test markdown format output."""
        execution_result = ExecutionResult(
            trace_id="test",
            success=True,
            steps=[],
            final_result=[
                {"col1": "a", "col2": "b"},
            ],
            total_duration_ms=5.0,
        )
        
        result = aggregator.aggregate(
            execution_result,
            format=OutputFormat.MARKDOWN,
        )
        
        assert result.format == OutputFormat.MARKDOWN
        assert "|" in result.data  # Markdown table
    
    def test_aggregate_summary_format(self, aggregator):
        """Test summary format output."""
        execution_result = ExecutionResult(
            trace_id="test",
            success=True,
            steps=[],
            final_result=[
                {"value": 10},
                {"value": 20},
                {"value": 30},
            ],
            total_duration_ms=5.0,
        )
        
        result = aggregator.aggregate(
            execution_result,
            format=OutputFormat.SUMMARY,
        )
        
        assert result.format == OutputFormat.SUMMARY
        assert "3 items" in result.data
    
    def test_aggregate_failed_execution(self, aggregator):
        """Test aggregating failed execution."""
        execution_result = ExecutionResult(
            trace_id="failed",
            success=False,
            steps=[
                StepResult(
                    step_index=0,
                    action="sql_select",
                    status=StepStatus.FAILED,
                    error="Table not found",
                    duration_ms=5.0,
                ),
            ],
            error="Execution failed",
            total_duration_ms=5.0,
        )
        
        result = aggregator.aggregate(execution_result)
        
        assert result.success is False
        assert "failed" in result.summary.lower()
        assert "Table not found" in result.summary
    
    def test_generate_summary(self, aggregator, sample_execution_result):
        """Test summary generation."""
        result = aggregator.aggregate(sample_execution_result)
        
        assert "✅" in result.summary  # Success emoji
        assert "completed" in result.summary.lower()
        assert "abc123" in result.summary  # Trace ID
    
    def test_to_llm_context(self, aggregator, sample_execution_result):
        """Test generating LLM context."""
        aggregated = aggregator.aggregate(sample_execution_result)
        context = aggregator.to_llm_context(aggregated)
        
        assert "Execution Result:" in context
        assert "Success" in context
        assert "2 users found" in context
    
    def test_to_llm_context_truncation(self, aggregator):
        """Test LLM context truncation for large results."""
        # Create large result
        large_data = [{"id": i, "data": "x" * 100} for i in range(100)]
        
        execution_result = ExecutionResult(
            trace_id="large",
            success=True,
            steps=[],
            final_result=large_data,
            total_duration_ms=100.0,
        )
        
        aggregated = aggregator.aggregate(execution_result)
        context = aggregator.to_llm_context(aggregated, max_tokens=100)
        
        # Should be truncated
        assert "truncated" in context.lower() or len(context) < 10000


class TestResultAggregatorEdgeCases:
    """Edge case tests for ResultAggregator."""
    
    @pytest.fixture
    def aggregator(self):
        return ResultAggregator()
    
    def test_aggregate_no_final_result(self, aggregator):
        """Test aggregating with no final result."""
        execution_result = ExecutionResult(
            trace_id="test",
            success=True,
            steps=[
                StepResult(
                    step_index=0,
                    action="test",
                    status=StepStatus.SUCCESS,
                    result=None,
                    duration_ms=5.0,
                ),
            ],
            final_result=None,
            total_duration_ms=5.0,
        )
        
        result = aggregator.aggregate(execution_result)
        
        assert result.success is True
        assert result.data is None or result.data == "None"
    
    def test_aggregate_empty_list_result(self, aggregator):
        """Test aggregating empty list result."""
        execution_result = ExecutionResult(
            trace_id="test",
            success=True,
            steps=[],
            final_result=[],
            total_duration_ms=5.0,
        )
        
        result = aggregator.aggregate(execution_result)
        
        assert "empty" in result.data.lower() or "no results" in result.data.lower()
    
    def test_aggregate_mixed_step_status(self, aggregator):
        """Test aggregating with mixed step statuses."""
        execution_result = ExecutionResult(
            trace_id="mixed",
            success=False,
            steps=[
                StepResult(step_index=0, action="step1", status=StepStatus.SUCCESS, duration_ms=5.0),
                StepResult(step_index=1, action="step2", status=StepStatus.FAILED, error="Error", duration_ms=3.0),
                StepResult(step_index=2, action="step3", status=StepStatus.SKIPPED, duration_ms=0.0),
            ],
            total_duration_ms=8.0,
        )
        
        result = aggregator.aggregate(execution_result, include_details=True)
        
        assert "1 succeeded" in result.summary
        assert "1 failed" in result.summary
        assert "1 skipped" in result.summary
    
    def test_format_step_detail_with_large_result(self, aggregator):
        """Test step detail formatting with large result."""
        large_result = [{"id": i} for i in range(1000)]
        
        step = StepResult(
            step_index=0,
            action="test",
            status=StepStatus.SUCCESS,
            result=large_result,
            duration_ms=10.0,
        )
        
        detail = aggregator._format_step_detail(step)
        
        # Should have preview, not full result
        assert "result_preview" in detail or "result_size" in detail
