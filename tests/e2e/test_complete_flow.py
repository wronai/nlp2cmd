"""
End-to-End Tests: Complete Flow.

Tests the full pipeline from query to result:
User Query → Router → Planner → Validator → Executor → Aggregator → Output
"""

import pytest
from nlp2cmd import (
    DecisionRouter,
    RoutingDecision,
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    LLMPlanner,
    ResultAggregator,
    OutputFormat,
    StepStatus,
)


class TestCompleteFlow:
    """Tests for complete end-to-end flow."""
    
    def test_simple_query_direct_execution(
        self,
        decision_router,
        plan_executor,
        result_aggregator,
    ):
        """Test simple query goes through direct execution path."""
        # Step 1: Route query
        routing = decision_router.route(
            intent="select",
            entities={"table": "users"},
            text="show users",
            confidence=0.95,
        )
        
        assert routing.decision == RoutingDecision.DIRECT
        
        # Step 2: Create simple plan
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        # Step 3: Execute
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.SUCCESS
        assert len(result.final_result) == 5  # 5 mock users
        
        # Step 4: Aggregate
        output = result_aggregator.aggregate(result, format=OutputFormat.TABLE)
        
        assert output.success is True
        assert "Alice" in output.data
        assert "Bob" in output.data
    
    def test_complex_query_llm_planner(
        self,
        decision_router,
        llm_planner,
        plan_executor,
        result_aggregator,
    ):
        """Test complex query goes through LLM planner."""
        # Step 1: Route query - should go to LLM
        routing = decision_router.route(
            intent="analyze",
            entities={"table": "logs", "pattern": "ERROR"},
            text="analyze error patterns across all log files",
            confidence=0.85,
        )
        
        assert routing.decision == RoutingDecision.LLM_PLANNER
        
        # Step 2: For E2E test, we use a manually crafted plan
        # In production, LLM would generate this
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
                store_as="files",
            ),
            PlanStep(
                action="shell_count_pattern",
                foreach="files",
                params={"file": "$item", "pattern": "ERROR"},
                store_as="counts",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$counts"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 3
        
        # Verify foreach worked
        foreach_step = result.steps[1]
        assert foreach_step.iterations == 3  # 3 log files
        assert foreach_step.result == [15, 127, 3]  # ERROR counts
        
        # Step 4: Aggregate
        output = result_aggregator.aggregate(result)
        
        assert output.success is True
        assert output.step_count == 3
    
    def test_filtered_query_with_parameters(
        self,
        plan_executor,
        result_aggregator,
    ):
        """Test query with filter parameters."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "users",
                    "filters": ["status = 'active'"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        # Only active users should be returned
        assert len(result.final_result) == 3  # Alice, Bob, Diana
        assert all(u["status"] == "active" for u in result.final_result)
    
    def test_multi_domain_workflow(
        self,
        plan_executor,
        result_aggregator,
    ):
        """Test workflow spanning multiple domains."""
        plan = ExecutionPlan(steps=[
            # Step 1: Get database users
            PlanStep(
                action="sql_select",
                params={"table": "users", "filters": ["status = 'active'"]},
                store_as="active_users",
            ),
            # Step 2: Get running containers
            PlanStep(
                action="docker_ps",
                params={"all": False},
                store_as="containers",
            ),
            # Step 3: Get k8s pods
            PlanStep(
                action="k8s_get",
                params={"resource": "pods"},
                store_as="pods",
            ),
            # Step 4: Summarize
            PlanStep(
                action="summarize_results",
                params={"data": "$pods"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 4
        assert all(s.status == StepStatus.SUCCESS for s in result.steps)


class TestOutputFormats:
    """Tests for different output formats."""
    
    def test_text_format(self, plan_executor, result_aggregator):
        """Test text output format."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.TEXT)
        
        assert output.format == OutputFormat.TEXT
        assert isinstance(output.data, str)
    
    def test_table_format(self, plan_executor, result_aggregator):
        """Test table output format."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "products"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.TABLE)
        
        assert output.format == OutputFormat.TABLE
        assert "|" in output.data or "-" in output.data  # Table formatting
        assert "Laptop" in output.data
    
    def test_json_format(self, plan_executor, result_aggregator):
        """Test JSON output format."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "orders"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.JSON)
        
        assert output.format == OutputFormat.JSON
        # Data should be list of dicts
        assert isinstance(output.data, list)
    
    def test_markdown_format(self, plan_executor, result_aggregator):
        """Test markdown output format."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="docker_ps", params={}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.MARKDOWN)
        
        assert output.format == OutputFormat.MARKDOWN
        assert "|" in output.data  # Markdown table
    
    def test_summary_format(self, plan_executor, result_aggregator):
        """Test summary output format."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="k8s_get", params={"resource": "pods"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.SUMMARY)
        
        assert output.format == OutputFormat.SUMMARY
        assert "items" in output.data.lower()


class TestErrorHandling:
    """Tests for error handling in E2E flow."""
    
    def test_unknown_action_rejected(self, plan_executor):
        """Test that unknown actions are rejected."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="unknown_action", params={}),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is False
        assert "validation failed" in result.error.lower()
    
    def test_missing_required_param_rejected(self, plan_executor):
        """Test that missing required params are rejected."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={}),  # Missing 'table'
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is False
        assert "table" in result.error.lower()
    
    def test_low_confidence_triggers_clarification(self, decision_router):
        """Test that low confidence triggers clarification."""
        routing = decision_router.route(
            intent="unknown",
            entities={},
            text="do something unclear",
            confidence=0.4,
        )
        
        assert routing.decision == RoutingDecision.CLARIFICATION
    
    def test_very_low_confidence_rejected(self, decision_router):
        """Test that very low confidence is rejected."""
        routing = decision_router.route(
            intent="unknown",
            entities={},
            text="asdfghjkl",
            confidence=0.1,
        )
        
        assert routing.decision == RoutingDecision.REJECT


class TestTracingAndObservability:
    """Tests for tracing and observability features."""
    
    def test_trace_id_assigned(self, plan_executor):
        """Test that trace ID is assigned to execution."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.trace_id is not None
        assert len(result.trace_id) > 0
    
    def test_duration_tracked(self, plan_executor):
        """Test that duration is tracked."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.total_duration_ms >= 0
        assert result.steps[0].duration_ms >= 0
    
    def test_step_details_in_aggregated_result(self, plan_executor, result_aggregator):
        """Test that step details are included in aggregated result."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}, store_as="users"),
            PlanStep(action="summarize_results", params={"data": "$users"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, include_details=True)
        
        assert len(output.details) == 2
        assert output.details[0]["action"] == "sql_select"
        assert output.details[1]["action"] == "summarize_results"
    
    def test_trace_id_in_summary(self, plan_executor, result_aggregator):
        """Test that trace ID appears in summary."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result)
        
        assert result.trace_id in output.summary


class TestDryRunMode:
    """Tests for dry run mode."""
    
    def test_dry_run_validates_without_executing(self, plan_executor):
        """Test dry run mode validates but doesn't execute."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan, dry_run=True)
        
        assert result.success is True
        assert result.metadata.get("dry_run") is True
        # Steps should be marked as dry run
        assert result.steps[0].metadata.get("dry_run") is True
    
    def test_dry_run_catches_invalid_plan(self, plan_executor):
        """Test dry run catches invalid plans."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="invalid_action", params={}),
        ])
        
        result = plan_executor.execute(plan, dry_run=True)
        
        assert result.success is False


class TestSamplePlans:
    """Tests using predefined sample plans."""
    
    def test_simple_select_plan(self, plan_executor, sample_plans):
        """Test simple select plan."""
        result = plan_executor.execute(sample_plans["simple_select"])
        
        assert result.success is True
        assert len(result.final_result) == 5
    
    def test_filtered_select_plan(self, plan_executor, sample_plans):
        """Test filtered select plan."""
        result = plan_executor.execute(sample_plans["filtered_select"])
        
        assert result.success is True
        assert len(result.final_result) == 3  # Only active users
    
    def test_multi_step_analysis_plan(self, plan_executor, sample_plans):
        """Test multi-step analysis plan."""
        result = plan_executor.execute(sample_plans["multi_step_analysis"])
        
        assert result.success is True
        assert len(result.steps) == 3
        assert result.steps[1].iterations == 3  # 3 log files
    
    def test_k8s_status_plan(self, plan_executor, sample_plans):
        """Test Kubernetes status plan."""
        result = plan_executor.execute(sample_plans["k8s_status"])
        
        assert result.success is True
        assert len(result.final_result) == 3  # 3 pods
    
    def test_docker_status_plan(self, plan_executor, sample_plans):
        """Test Docker status plan."""
        result = plan_executor.execute(sample_plans["docker_status"])
        
        assert result.success is True
        assert len(result.final_result) == 3  # 3 containers
