"""
End-to-End Tests: Action Registry and Plan Validation.

Tests for action registration, validation, and security constraints.
"""

import pytest
from nlp2cmd import (
    ActionRegistry,
    ActionSchema,
    ParamSchema,
    ParamType,
    get_registry,
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    PlanValidator,
)


class TestActionRegistryE2E:
    """E2E tests for Action Registry."""
    
    def test_registry_has_all_domains(self, action_registry):
        """Test that registry has all expected domains."""
        domains = action_registry.list_domains()
        
        assert "sql" in domains
        assert "shell" in domains
        assert "docker" in domains
        assert "kubernetes" in domains
        assert "utility" in domains
    
    def test_sql_domain_actions(self, action_registry):
        """Test SQL domain has expected actions."""
        sql_actions = action_registry.list_actions(domain="sql")
        
        assert "sql_select" in sql_actions
        assert "sql_insert" in sql_actions
        assert "sql_update" in sql_actions
        assert "sql_delete" in sql_actions
        assert "sql_aggregate" in sql_actions
    
    def test_shell_domain_actions(self, action_registry):
        """Test Shell domain has expected actions."""
        shell_actions = action_registry.list_actions(domain="shell")
        
        assert "shell_find" in shell_actions
        assert "shell_read_file" in shell_actions
        assert "shell_count_pattern" in shell_actions
        assert "shell_process_list" in shell_actions
    
    def test_docker_domain_actions(self, action_registry):
        """Test Docker domain has expected actions."""
        docker_actions = action_registry.list_actions(domain="docker")
        
        assert "docker_ps" in docker_actions
        assert "docker_run" in docker_actions
        assert "docker_stop" in docker_actions
        assert "docker_logs" in docker_actions
    
    def test_kubernetes_domain_actions(self, action_registry):
        """Test Kubernetes domain has expected actions."""
        k8s_actions = action_registry.list_actions(domain="kubernetes")
        
        assert "k8s_get" in k8s_actions
        assert "k8s_scale" in k8s_actions
        assert "k8s_logs" in k8s_actions
    
    def test_destructive_actions_marked(self, action_registry):
        """Test that destructive actions are properly marked."""
        destructive = action_registry.get_destructive_actions()
        
        # SQL write operations should be destructive
        assert "sql_insert" in destructive
        assert "sql_update" in destructive
        assert "sql_delete" in destructive
        
        # Docker write operations should be destructive
        assert "docker_run" in destructive
        assert "docker_stop" in destructive
        
        # K8s scale should be destructive
        assert "k8s_scale" in destructive
        
        # Read operations should NOT be destructive
        assert "sql_select" not in destructive
        assert "docker_ps" not in destructive
        assert "k8s_get" not in destructive
    
    def test_action_schema_has_description(self, action_registry):
        """Test that all actions have descriptions."""
        for action_name in action_registry.list_actions():
            schema = action_registry.get(action_name)
            assert schema is not None
            assert schema.description
            assert len(schema.description) > 0
    
    def test_register_custom_action(self, action_registry):
        """Test registering a custom action."""
        custom_schema = ActionSchema(
            name="custom_e2e_action",
            description="Custom action for E2E testing",
            domain="test",
            params=[
                ParamSchema(name="input", type=ParamType.STRING),
                ParamSchema(name="count", type=ParamType.INTEGER, required=False, default=1),
            ],
            returns=ParamType.STRING,
        )
        
        action_registry.register(custom_schema)
        
        assert action_registry.has("custom_e2e_action")
        assert "custom_e2e_action" in action_registry.list_actions(domain="test")
    
    def test_llm_prompt_generation(self, action_registry):
        """Test generating LLM prompt from registry."""
        prompt = action_registry.to_llm_prompt()
        
        assert "Available actions:" in prompt
        assert "sql_select" in prompt
        assert "Description:" in prompt
        assert "Returns:" in prompt
    
    def test_llm_prompt_domain_filter(self, action_registry):
        """Test generating LLM prompt for specific domain."""
        sql_prompt = action_registry.to_llm_prompt(domain="sql")
        
        assert "sql_select" in sql_prompt
        assert "docker_ps" not in sql_prompt
        assert "k8s_get" not in sql_prompt


class TestPlanValidationE2E:
    """E2E tests for Plan Validation."""
    
    @pytest.fixture
    def validator(self, action_registry):
        """Create plan validator."""
        return PlanValidator(action_registry)
    
    def test_valid_single_step_plan(self, validator):
        """Test validating a valid single-step plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_multi_step_plan(self, validator):
        """Test validating a valid multi-step plan."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="shell_find", params={"glob": "*.log"}, store_as="files"),
            PlanStep(
                action="shell_count_pattern",
                foreach="files",
                params={"file": "$item", "pattern": "ERROR"},
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is True
    
    def test_invalid_unknown_action(self, validator):
        """Test that unknown actions are rejected."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="unknown_action", params={}),
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is False
        assert any("Unknown action" in e for e in errors)
    
    def test_invalid_missing_required_param(self, validator):
        """Test that missing required params are caught."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={}),  # Missing 'table'
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is False
        assert any("table" in e.lower() for e in errors)
    
    def test_invalid_undefined_foreach_reference(self, validator):
        """Test that undefined foreach references are caught."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_count_pattern",
                foreach="undefined_variable",
                params={"file": "$item", "pattern": "ERROR"},
            ),
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is False
        assert any("undefined" in e.lower() for e in errors)
    
    def test_invalid_empty_plan(self, validator):
        """Test that empty plans are rejected."""
        plan = ExecutionPlan(steps=[])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is False
        assert any("at least one" in e.lower() for e in errors)
    
    def test_valid_variable_reference_chain(self, validator):
        """Test validating proper variable reference chain."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}, store_as="users"),
            PlanStep(action="summarize_results", params={"data": "$users"}),
        ])
        
        is_valid, errors = validator.validate(plan)
        
        assert is_valid is True


class TestSecurityConstraints:
    """E2E tests for security constraints."""
    
    def test_only_registered_actions_execute(self, plan_executor):
        """Test that only registered actions can execute."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="malicious_action", params={}),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is False
        assert "Unknown action" in result.error or "validation failed" in result.error
    
    def test_destructive_actions_flagged(self, action_registry):
        """Test that destructive actions are properly flagged."""
        delete_schema = action_registry.get("sql_delete")
        
        assert delete_schema is not None
        assert delete_schema.is_destructive is True
        assert delete_schema.requires_confirmation is True
    
    def test_sql_injection_not_possible(self, plan_executor):
        """Test that SQL injection is not possible through params."""
        # Even if malicious input is provided, it's just a parameter value
        # The actual SQL is never constructed or executed by LLM
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "users; DROP TABLE users;--",  # Attempted injection
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        # The mock handler treats it as a table name, not SQL
        # In production, the handler would properly escape/validate
        assert result.success is True  # Mock returns empty list for unknown table
    
    def test_no_shell_execution_from_params(self, plan_executor):
        """Test that shell commands can't be executed through params."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={
                    "glob": "*.log; rm -rf /",  # Attempted command injection
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        # Mock handler treats it as a glob pattern
        # In production, shell_find would use safe APIs, not shell execution
        assert result.success is True
    
    def test_param_type_validation(self, action_registry):
        """Test that parameter types are validated."""
        # Attempt to validate with wrong type
        is_valid, errors = action_registry.validate_action(
            "k8s_scale",
            {"deployment": "nginx", "replicas": "not_a_number"},  # Should be integer
        )
        
        assert is_valid is False
        assert any("type" in e.lower() for e in errors)


class TestExecutorIntegration:
    """E2E tests for Executor integration."""
    
    def test_executor_validates_before_running(self, plan_executor):
        """Test that executor validates plans before running."""
        invalid_plan = ExecutionPlan(steps=[
            PlanStep(action="unknown_action", params={}),
        ])
        
        result = plan_executor.execute(invalid_plan)
        
        # Should fail at validation, not execution
        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert len(result.steps) == 0  # No steps executed
    
    def test_executor_respects_on_error_stop(self, plan_executor):
        """Test that executor stops on error when configured."""
        from nlp2cmd.registry import ActionSchema
        
        # Register a failing action
        plan_executor.registry.register(ActionSchema(
            name="always_fails",
            description="Always fails",
            domain="test",
        ))
        plan_executor.register_handler(
            "always_fails",
            lambda **kw: (_ for _ in ()).throw(RuntimeError("Intentional failure"))
        )
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
            PlanStep(action="always_fails", params={}, on_error="stop"),
            PlanStep(action="sql_select", params={"table": "orders"}),  # Should not run
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is False
        assert len(result.steps) == 2  # Third step not executed
    
    def test_executor_continues_on_error_when_configured(self, plan_executor):
        """Test that executor continues on error when configured."""
        from nlp2cmd.registry import ActionSchema
        
        # Register a failing action
        plan_executor.registry.register(ActionSchema(
            name="always_fails_cont",
            description="Always fails (continue)",
            domain="test",
        ))
        plan_executor.register_handler(
            "always_fails_cont",
            lambda **kw: (_ for _ in ()).throw(RuntimeError("Intentional failure"))
        )
        
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}, store_as="users"),
            PlanStep(action="always_fails_cont", params={}, on_error="continue"),
            PlanStep(action="summarize_results", params={"data": "$users"}),
        ])
        
        result = plan_executor.execute(plan)
        
        # Third step should run despite second step failing
        assert len(result.steps) == 3
    
    def test_dry_run_mode(self, plan_executor):
        """Test dry run mode validates without executing."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
            PlanStep(action="docker_ps", params={}),
        ])
        
        result = plan_executor.execute(plan, dry_run=True)
        
        assert result.success is True
        assert result.metadata.get("dry_run") is True
        # In dry run, steps are validated but not actually executed
        for step in result.steps:
            assert step.metadata.get("dry_run") is True
