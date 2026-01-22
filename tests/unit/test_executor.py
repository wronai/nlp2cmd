"""
Tests for Plan Executor.
"""

import pytest
from nlp2cmd.executor import (
    PlanExecutor,
    PlanValidator,
    ExecutionPlan,
    ExecutionContext,
    ExecutionResult,
    PlanStep,
    StepResult,
    StepStatus,
)
from nlp2cmd.registry import ActionRegistry


class TestStepStatus:
    """Tests for StepStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test all step statuses are defined."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.SUCCESS.value == "success"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"


class TestPlanStep:
    """Tests for PlanStep dataclass."""
    
    def test_basic_step(self):
        """Test creating a basic step."""
        step = PlanStep(action="sql_select")
        assert step.action == "sql_select"
        assert step.params == {}
        assert step.foreach is None
        assert step.on_error == "stop"
        assert step.store_as == "sql_select_result"  # Auto-generated
    
    def test_step_with_params(self):
        """Test step with parameters."""
        step = PlanStep(
            action="sql_select",
            params={"table": "users", "columns": ["id", "name"]},
            store_as="users",
        )
        assert step.params["table"] == "users"
        assert step.store_as == "users"
    
    def test_step_with_foreach(self):
        """Test step with foreach."""
        step = PlanStep(
            action="shell_count_pattern",
            foreach="log_files",
            params={"file": "$item", "pattern": "ERROR"},
        )
        assert step.foreach == "log_files"
        assert step.params["file"] == "$item"
    
    def test_step_with_all_options(self):
        """Test step with all options."""
        step = PlanStep(
            action="test",
            params={"key": "value"},
            foreach="items",
            condition="$count > 0",
            store_as="result",
            on_error="continue",
            timeout=30.0,
            retry=3,
        )
        assert step.condition == "$count > 0"
        assert step.on_error == "continue"
        assert step.timeout == 30.0
        assert step.retry == 3


class TestExecutionPlan:
    """Tests for ExecutionPlan dataclass."""
    
    def test_basic_plan(self):
        """Test creating a basic plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        assert len(plan.steps) == 1
    
    def test_from_dict(self):
        """Test creating plan from dictionary."""
        plan_dict = {
            "steps": [
                {
                    "action": "shell_find",
                    "params": {"glob": "*.log"},
                    "store_as": "files",
                },
                {
                    "action": "shell_count_pattern",
                    "foreach": "files",
                    "params": {"file": "$item", "pattern": "ERROR"},
                },
            ],
            "metadata": {"created_by": "test"},
        }
        
        plan = ExecutionPlan.from_dict(plan_dict)
        
        assert len(plan.steps) == 2
        assert plan.steps[0].action == "shell_find"
        assert plan.steps[1].foreach == "files"
        assert plan.metadata["created_by"] == "test"
    
    def test_to_dict(self):
        """Test converting plan to dictionary."""
        plan = ExecutionPlan(
            steps=[
                PlanStep(action="test", params={"key": "value"}),
            ],
            metadata={"version": 1},
        )
        
        result = plan.to_dict()
        
        assert "steps" in result
        assert result["steps"][0]["action"] == "test"
        assert result["metadata"]["version"] == 1


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""
    
    def test_basic_context(self):
        """Test creating basic context."""
        ctx = ExecutionContext()
        assert len(ctx.trace_id) == 8
        assert ctx.variables == {}
        assert ctx.results == []
        assert ctx.current_step == 0
        assert ctx.dry_run is False
    
    def test_set_get_variable(self):
        """Test setting and getting variables."""
        ctx = ExecutionContext()
        ctx.set("users", [{"id": 1}, {"id": 2}])
        
        assert ctx.get("users") == [{"id": 1}, {"id": 2}]
        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", "default") == "default"
    
    def test_resolve_simple_reference(self):
        """Test resolving simple variable reference."""
        ctx = ExecutionContext()
        ctx.set("count", 42)
        
        assert ctx.resolve_reference("$count") == 42
    
    def test_resolve_nested_reference(self):
        """Test resolving nested reference."""
        ctx = ExecutionContext()
        ctx.set("user", {"name": "Alice", "age": 30})
        
        assert ctx.resolve_reference("$user.name") == "Alice"
        assert ctx.resolve_reference("$user.age") == 30
    
    def test_resolve_list_index(self):
        """Test resolving list index reference."""
        ctx = ExecutionContext()
        ctx.set("items", ["a", "b", "c"])
        
        assert ctx.resolve_reference("$items.0") == "a"
        assert ctx.resolve_reference("$items.2") == "c"
    
    def test_resolve_unknown_variable(self):
        """Test resolving unknown variable raises error."""
        ctx = ExecutionContext()
        
        with pytest.raises(ValueError, match="Unknown variable"):
            ctx.resolve_reference("$unknown")
    
    def test_non_reference_passthrough(self):
        """Test non-reference strings pass through."""
        ctx = ExecutionContext()
        
        assert ctx.resolve_reference("hello") == "hello"


class TestPlanValidator:
    """Tests for PlanValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator with fresh registry."""
        return PlanValidator(ActionRegistry())
    
    def test_validate_valid_plan(self, validator):
        """Test validating a valid plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={"table": "users"},
                store_as="users",
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_empty_plan(self, validator):
        """Test validating empty plan fails."""
        plan = ExecutionPlan(steps=[])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is False
        assert any("at least one" in e for e in errors)
    
    def test_validate_unknown_action(self, validator):
        """Test validating unknown action fails."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="nonexistent_action"),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is False
        assert any("Unknown action" in e for e in errors)
    
    def test_validate_missing_params(self, validator):
        """Test validating missing required params fails."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={},  # Missing 'table'
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is False
        assert any("Missing required" in e for e in errors)
    
    def test_validate_foreach_reference(self, validator):
        """Test validating foreach reference."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
                store_as="files",
            ),
            PlanStep(
                action="shell_count_pattern",
                foreach="files",  # References previous step
                params={"file": "$item", "pattern": "ERROR"},
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is True
    
    def test_validate_undefined_reference(self, validator):
        """Test validating undefined reference fails."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_count_pattern",
                foreach="undefined_var",  # Not defined
                params={"file": "$item", "pattern": "ERROR"},
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is False
        assert any("undefined" in e for e in errors)
    
    def test_validate_param_reference(self, validator):
        """Test validating parameter references."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={"table": "users"},
                store_as="users",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$users"},  # Valid reference
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        assert is_valid is True


class TestPlanExecutor:
    """Tests for PlanExecutor."""
    
    @pytest.fixture
    def executor(self):
        """Create executor with mock handlers."""
        exec = PlanExecutor()
        
        # Register mock handlers
        exec.register_handler("sql_select", lambda table, **kw: [{"id": 1}, {"id": 2}])
        exec.register_handler("shell_find", lambda **kw: ["a.log", "b.log"])
        exec.register_handler("shell_count_pattern", lambda file, pattern, **kw: 5)
        
        return exec
    
    def test_execute_simple_plan(self, executor):
        """Test executing a simple plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={"table": "users"},
            ),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.SUCCESS
        assert result.final_result == [{"id": 1}, {"id": 2}]
    
    def test_execute_multi_step_plan(self, executor):
        """Test executing multi-step plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
                store_as="files",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$files"},
            ),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 2
    
    def test_execute_foreach(self, executor):
        """Test executing foreach loop."""
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
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        # The foreach step should have iterations
        assert result.steps[1].iterations == 2  # a.log, b.log
        assert result.steps[1].result == [5, 5]
    
    def test_execute_with_initial_context(self, executor):
        """Test executing with initial context."""
        from nlp2cmd.registry import ActionSchema, ParamSchema, ParamType
        
        # Register custom actions
        executor.registry.register(ActionSchema(
            name="provide_data",
            description="Provide data",
            domain="test",
        ))
        executor.registry.register(ActionSchema(
            name="use_data",
            description="Use data",
            domain="test",
            params=[ParamSchema(name="data", type=ParamType.ANY)],
        ))
        
        executor.register_handler("provide_data", lambda: [1, 2, 3])
        executor.register_handler("use_data", lambda data: f"Got {len(data)} items")
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="provide_data", params={}, store_as="input_data"),
            PlanStep(action="use_data", params={"data": "$input_data"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        assert "3 items" in result.final_result
    
    def test_execute_dry_run(self, executor):
        """Test dry run mode."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = executor.execute(plan, dry_run=True)
        
        assert result.success is True
        assert result.metadata["dry_run"] is True
        # Steps should be validated but not executed
        assert result.steps[0].metadata.get("dry_run") is True
    
    def test_execute_step_callback(self, executor):
        """Test step completion callback."""
        completed_steps = []
        
        def on_complete(step_result):
            completed_steps.append(step_result.action)
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*"}),
            PlanStep(action="summarize_results", params={"data": "$shell_find_result"}),
        ])
        
        executor.execute(plan, on_step_complete=on_complete)
        
        assert len(completed_steps) == 2
        assert "shell_find" in completed_steps
    
    def test_execute_error_stop(self, executor):
        """Test error handling - stop mode."""
        from nlp2cmd.registry import ActionSchema, ParamType
        
        # Register the failing action
        executor.registry.register(ActionSchema(
            name="failing_action",
            description="Always fails",
            domain="test",
        ))
        executor.register_handler("failing_action", lambda **kw: (_ for _ in ()).throw(RuntimeError("Failed")))
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*"}),
            PlanStep(action="failing_action", params={}, on_error="stop"),
            PlanStep(action="summarize_results", params={"data": "$shell_find_result"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is False
        assert len(result.steps) == 2  # Third step not executed
        assert result.steps[1].status == StepStatus.FAILED
    
    def test_execute_error_continue(self, executor):
        """Test error handling - continue mode."""
        from nlp2cmd.registry import ActionSchema, ParamType
        
        # Register the failing action
        executor.registry.register(ActionSchema(
            name="failing_action_cont",
            description="Always fails",
            domain="test",
        ))
        executor.register_handler("failing_action_cont", lambda **kw: (_ for _ in ()).throw(RuntimeError("Failed")))
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*"}, store_as="files"),
            PlanStep(action="failing_action_cont", params={}, on_error="continue"),
            PlanStep(action="summarize_results", params={"data": "$files"}),
        ])
        
        result = executor.execute(plan)
        
        # All steps executed despite error
        assert len(result.steps) == 3
        assert result.steps[1].status == StepStatus.FAILED
        assert result.steps[2].status == StepStatus.SUCCESS
    
    def test_execute_condition(self, executor):
        """Test conditional execution."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={"table": "users"},
                store_as="count",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$count"},
                condition="len($count) > 0",
            ),
        ])
        
        result = executor.execute(plan)
        assert result.success is True
    
    def test_execute_invalid_plan(self, executor):
        """Test executing invalid plan fails."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="nonexistent"),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is False
        assert "validation failed" in result.error.lower()
    
    def test_trace_id_assigned(self, executor):
        """Test trace ID is assigned."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.trace_id is not None
        assert len(result.trace_id) > 0
    
    def test_duration_tracked(self, executor):
        """Test duration is tracked."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.total_duration_ms > 0
        assert result.steps[0].duration_ms > 0


class TestPlanExecutorEdgeCases:
    """Edge case tests for PlanExecutor."""
    
    @pytest.fixture
    def executor(self):
        return PlanExecutor()
    
    def test_empty_foreach_iterable(self, executor):
        """Test foreach with empty iterable."""
        from nlp2cmd.registry import ActionSchema, ParamSchema, ParamType
        
        # Register custom actions
        executor.registry.register(ActionSchema(
            name="get_empty",
            description="Returns empty list",
            domain="test",
        ))
        executor.registry.register(ActionSchema(
            name="process_item",
            description="Process item",
            domain="test",
            params=[ParamSchema(name="item", type=ParamType.ANY)],
        ))
        
        executor.register_handler("get_empty", lambda: [])
        executor.register_handler("process_item", lambda item: item)
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="get_empty", params={}, store_as="items"),
            PlanStep(action="process_item", foreach="items", params={"item": "$item"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        assert result.steps[1].iterations == 0
        assert result.steps[1].result == []
    
    def test_nested_param_resolution(self, executor):
        """Test nested parameter resolution."""
        from nlp2cmd.registry import ActionSchema, ParamSchema, ParamType
        
        # Register custom actions
        executor.registry.register(ActionSchema(
            name="get_config",
            description="Get config",
            domain="test",
        ))
        executor.registry.register(ActionSchema(
            name="use_config",
            description="Use config",
            domain="test",
            params=[ParamSchema(name="host", type=ParamType.STRING)],
        ))
        
        executor.register_handler("get_config", lambda: {"db": {"host": "localhost"}})
        executor.register_handler("use_config", lambda host: f"connected to {host}")
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="get_config", params={}, store_as="config"),
            PlanStep(action="use_config", params={"host": "$config.db.host"}),
        ])
        
        result = executor.execute(plan)
        
        assert result.success is True
        assert "localhost" in result.final_result
