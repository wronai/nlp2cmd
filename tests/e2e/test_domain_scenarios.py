"""
End-to-End Tests: Domain-Specific Scenarios.

Tests for SQL, Shell, Docker, and Kubernetes specific workflows.
"""

import pytest
from nlp2cmd import (
    PlanExecutor,
    ExecutionPlan,
    PlanStep,
    ResultAggregator,
    OutputFormat,
    StepStatus,
)


class TestSQLScenarios:
    """E2E tests for SQL-specific scenarios."""
    
    def test_select_all_users(self, plan_executor, result_aggregator):
        """Test selecting all users."""
        plan = ExecutionPlan(steps=[
            PlanStep(action="sql_select", params={"table": "users"}),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.TABLE)
        
        assert result.success is True
        assert len(result.final_result) == 5
        assert "Alice" in output.data
        assert "Bob" in output.data
    
    def test_select_with_city_filter(self, plan_executor):
        """Test selecting users by city."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "users",
                    "filters": ["city = 'warsaw'"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 2  # Alice and Charlie
        assert all(u["city"] == "Warsaw" for u in result.final_result)
    
    def test_select_specific_columns(self, plan_executor):
        """Test selecting specific columns."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "users",
                    "columns": ["name", "email"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        # Should only have name and email columns
        first_user = result.final_result[0]
        assert "name" in first_user
        assert "email" in first_user
        assert "status" not in first_user
    
    def test_aggregate_users_by_status(self, plan_executor):
        """Test aggregating users by status."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_aggregate",
                params={
                    "table": "users",
                    "aggregations": [{"function": "COUNT", "field": "*"}],
                    "grouping": ["status"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        # Should have groups for active, inactive, pending
        assert len(result.final_result) >= 2
    
    def test_products_by_category(self, plan_executor):
        """Test filtering products by category."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "products",
                    "filters": ["category = 'electronics'"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert all(p["category"] == "Electronics" for p in result.final_result)
    
    def test_completed_orders(self, plan_executor):
        """Test filtering completed orders."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="sql_select",
                params={
                    "table": "orders",
                    "filters": ["status = 'completed'"],
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert all(o["status"] == "completed" for o in result.final_result)


class TestShellScenarios:
    """E2E tests for Shell-specific scenarios."""
    
    def test_find_log_files(self, plan_executor):
        """Test finding log files."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 3
        assert all(".log" in f for f in result.final_result)
    
    def test_find_python_files(self, plan_executor):
        """Test finding Python files."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.py"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert all(".py" in f for f in result.final_result)
    
    def test_count_errors_in_single_file(self, plan_executor):
        """Test counting errors in a single file."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_count_pattern",
                params={
                    "file": "/var/log/error.log",
                    "pattern": "ERROR",
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert result.final_result == 127
    
    def test_count_errors_across_all_logs(self, plan_executor):
        """Test counting errors across all log files."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
                store_as="logs",
            ),
            PlanStep(
                action="shell_count_pattern",
                foreach="logs",
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
        assert result.steps[1].result == [15, 127, 3]  # Counts for each file
        total_errors = sum(result.steps[1].result)
        assert total_errors == 145
    
    def test_list_processes(self, plan_executor):
        """Test listing processes."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_process_list",
                params={"limit": 5},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 5
    
    def test_list_processes_sorted_by_cpu(self, plan_executor):
        """Test listing processes sorted by CPU."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="shell_process_list",
                params={"sort_by": "cpu", "limit": 3},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        # Should be sorted by CPU descending
        cpus = [p["cpu"] for p in result.final_result]
        assert cpus == sorted(cpus, reverse=True)


class TestDockerScenarios:
    """E2E tests for Docker-specific scenarios."""
    
    def test_list_running_containers(self, plan_executor):
        """Test listing running containers."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="docker_ps",
                params={"all": False},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 3
        assert all(c["status"] == "running" for c in result.final_result)
    
    def test_list_all_containers(self, plan_executor):
        """Test listing all containers."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="docker_ps",
                params={"all": True},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
    
    def test_filter_containers_by_name(self, plan_executor):
        """Test filtering containers by name."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="docker_ps",
                params={"filter": "api"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert all("api" in c["name"] for c in result.final_result)
    
    def test_get_container_logs(self, plan_executor):
        """Test getting container logs."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="docker_logs",
                params={"container": "api-1", "tail": 50},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert "api-1" in result.final_result
    
    def test_container_status_workflow(self, plan_executor, result_aggregator):
        """Test complete container status workflow."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="docker_ps",
                params={},
                store_as="containers",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$containers"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result)
        
        assert result.success is True
        assert "3 items" in output.summary or "3" in str(result.steps[0].result)


class TestKubernetesScenarios:
    """E2E tests for Kubernetes-specific scenarios."""
    
    def test_get_pods(self, plan_executor):
        """Test getting pods."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_get",
                params={"resource": "pods"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 3
    
    def test_get_pods_by_name(self, plan_executor):
        """Test getting pods by name filter."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_get",
                params={"resource": "pods", "name": "api-server"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert all("api-server" in p["name"] for p in result.final_result)
    
    def test_get_deployments(self, plan_executor):
        """Test getting deployments."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_get",
                params={"resource": "deployments"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 2
    
    def test_get_services(self, plan_executor):
        """Test getting services."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_get",
                params={"resource": "services"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.final_result) == 2
    
    def test_scale_deployment(self, plan_executor):
        """Test scaling a deployment."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_scale",
                params={
                    "deployment": "api-server",
                    "replicas": 5,
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert result.final_result is True
    
    def test_get_pod_logs(self, plan_executor):
        """Test getting pod logs."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_logs",
                params={
                    "pod": "api-server-abc123",
                    "tail": 100,
                },
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert "api-server" in result.final_result
    
    def test_k8s_status_workflow(self, plan_executor, result_aggregator):
        """Test complete K8s status workflow."""
        plan = ExecutionPlan(steps=[
            PlanStep(
                action="k8s_get",
                params={"resource": "pods"},
                store_as="pods",
            ),
            PlanStep(
                action="k8s_get",
                params={"resource": "deployments"},
                store_as="deployments",
            ),
            PlanStep(
                action="summarize_results",
                params={"data": "$deployments"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        output = result_aggregator.aggregate(result, format=OutputFormat.TEXT)
        
        assert result.success is True
        assert len(result.steps) == 3


class TestCrossDomainScenarios:
    """E2E tests for cross-domain workflows."""
    
    def test_infrastructure_health_check(self, plan_executor, result_aggregator):
        """Test infrastructure health check across domains."""
        plan = ExecutionPlan(steps=[
            # Check Docker containers
            PlanStep(
                action="docker_ps",
                params={},
                store_as="containers",
            ),
            # Check K8s pods
            PlanStep(
                action="k8s_get",
                params={"resource": "pods"},
                store_as="pods",
            ),
            # Check processes
            PlanStep(
                action="shell_process_list",
                params={"limit": 10},
                store_as="processes",
            ),
            # Summarize
            PlanStep(
                action="summarize_results",
                params={"data": "$processes"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 4
        assert all(s.status == StepStatus.SUCCESS for s in result.steps)
    
    def test_user_and_order_analysis(self, plan_executor):
        """Test analyzing users and their orders."""
        plan = ExecutionPlan(steps=[
            # Get active users
            PlanStep(
                action="sql_select",
                params={
                    "table": "users",
                    "filters": ["status = 'active'"],
                },
                store_as="active_users",
            ),
            # Get completed orders
            PlanStep(
                action="sql_select",
                params={
                    "table": "orders",
                    "filters": ["status = 'completed'"],
                },
                store_as="completed_orders",
            ),
            # Summarize
            PlanStep(
                action="summarize_results",
                params={"data": "$completed_orders"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 3
    
    def test_log_analysis_pipeline(self, plan_executor):
        """Test complete log analysis pipeline."""
        plan = ExecutionPlan(steps=[
            # Find all logs
            PlanStep(
                action="shell_find",
                params={"glob": "*.log"},
                store_as="log_files",
            ),
            # Count errors in each
            PlanStep(
                action="shell_count_pattern",
                foreach="log_files",
                params={"file": "$item", "pattern": "ERROR"},
                store_as="error_counts",
            ),
            # Count warnings in each
            PlanStep(
                action="shell_count_pattern",
                foreach="log_files",
                params={"file": "$item", "pattern": "WARNING"},
                store_as="warning_counts",
            ),
            # Summarize errors
            PlanStep(
                action="summarize_results",
                params={"data": "$error_counts"},
            ),
        ])
        
        result = plan_executor.execute(plan)
        
        assert result.success is True
        assert len(result.steps) == 4
        
        # Verify foreach iterations
        assert result.steps[1].iterations == 3
        assert result.steps[2].iterations == 3
