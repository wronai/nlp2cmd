"""
Iteration 3: Template-Based Generation & Pipeline Tests.

Test template generation and the complete rule-based pipeline.
"""

import pytest
import time

from nlp2cmd.generation.templates import TemplateGenerator, TemplateResult
from nlp2cmd.generation.pipeline import (
    RuleBasedPipeline,
    PipelineResult,
    PipelineMetrics,
    create_pipeline,
)


class TestTemplateGenerator:
    """Test template-based DSL generation."""
    
    @pytest.fixture
    def generator(self) -> TemplateGenerator:
        return TemplateGenerator()
    
    # ==================== SQL Templates ====================
    
    def test_sql_select_basic(self, generator):
        """Test basic SQL SELECT generation."""
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={'table': 'users', 'columns': ['id', 'name']}
        )
        
        assert result.success
        assert 'SELECT' in result.command
        assert 'id' in result.command
        assert 'name' in result.command
        assert 'FROM users' in result.command
    
    def test_sql_select_all_columns(self, generator):
        """Test SQL SELECT with all columns."""
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={'table': 'orders'}
        )
        
        assert result.success
        assert 'SELECT *' in result.command or 'SELECT' in result.command
        assert 'orders' in result.command
    
    def test_sql_select_with_where(self, generator):
        """Test SQL SELECT with WHERE clause."""
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={
                'table': 'users',
                'columns': ['*'],
                'filters': [{'field': 'status', 'operator': '=', 'value': 'active'}]
            }
        )
        
        assert result.success
        assert 'WHERE' in result.command
        assert 'status' in result.command
    
    def test_sql_select_with_limit(self, generator):
        """Test SQL SELECT with LIMIT."""
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={'table': 'products', 'limit': 10}
        )
        
        assert result.success
        assert 'LIMIT 10' in result.command
    
    def test_sql_select_with_order(self, generator):
        """Test SQL SELECT with ORDER BY."""
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={
                'table': 'orders',
                'ordering': [{'field': 'created_at', 'direction': 'DESC'}]
            }
        )
        
        assert result.success
        assert 'ORDER BY' in result.command
        assert 'created_at' in result.command
    
    def test_sql_aggregate(self, generator):
        """Test SQL aggregate query."""
        result = generator.generate(
            domain='sql',
            intent='aggregate',
            entities={
                'table': 'orders',
                'aggregations': [{'function': 'COUNT', 'field': '*'}],
                'grouping': ['status']
            }
        )
        
        assert result.success
        assert 'COUNT' in result.command
        assert 'GROUP BY' in result.command
    
    # ==================== Shell Templates ====================
    
    def test_shell_find(self, generator):
        """Test shell find command."""
        result = generator.generate(
            domain='shell',
            intent='find',
            entities={'path': '/home/user', 'pattern': '*.py'}
        )
        
        assert result.success
        assert 'find' in result.command
        assert '/home/user' in result.command
    
    def test_shell_list(self, generator):
        """Test shell list command."""
        result = generator.generate(
            domain='shell',
            intent='list',
            entities={'path': '/var/log'}
        )
        
        assert result.success
        assert 'ls' in result.command
        assert '/var/log' in result.command
    
    def test_shell_grep(self, generator):
        """Test shell grep command."""
        result = generator.generate(
            domain='shell',
            intent='grep',
            entities={'pattern': 'error', 'path': '/var/log'}
        )
        
        assert result.success
        assert 'grep' in result.command
        assert 'error' in result.command
    
    # ==================== Docker Templates ====================
    
    def test_docker_list(self, generator):
        """Test docker list command."""
        result = generator.generate(
            domain='docker',
            intent='list',
            entities={}
        )
        
        assert result.success
        assert 'docker' in result.command
        assert 'ps' in result.command
    
    def test_docker_logs(self, generator):
        """Test docker logs command."""
        result = generator.generate(
            domain='docker',
            intent='logs_tail',
            entities={'container': 'myapp', 'limit': 100}
        )
        
        assert result.success
        assert 'docker' in result.command
        assert 'logs' in result.command
        assert 'myapp' in result.command
    
    def test_docker_exec(self, generator):
        """Test docker exec command."""
        result = generator.generate(
            domain='docker',
            intent='exec_bash',
            entities={'container': 'webapp'}
        )
        
        assert result.success
        assert 'docker' in result.command
        assert 'exec' in result.command
    
    # ==================== Kubernetes Templates ====================
    
    def test_k8s_get(self, generator):
        """Test kubectl get command."""
        result = generator.generate(
            domain='kubernetes',
            intent='get',
            entities={'resource': 'pods', 'namespace': 'default'}
        )
        
        assert result.success
        assert 'kubectl' in result.command
        assert 'get' in result.command
        assert 'pods' in result.command
    
    def test_k8s_scale(self, generator):
        """Test kubectl scale command."""
        result = generator.generate(
            domain='kubernetes',
            intent='scale',
            entities={'resource': 'deployment', 'name': 'myapp', 'replicas': 5}
        )
        
        assert result.success
        assert 'kubectl' in result.command
        assert 'scale' in result.command
        assert '5' in result.command
    
    def test_k8s_logs(self, generator):
        """Test kubectl logs command."""
        result = generator.generate(
            domain='kubernetes',
            intent='logs_simple',
            entities={'pod': 'myapp-123', 'tail': 100}
        )
        
        assert result.success
        assert 'kubectl' in result.command
        assert 'logs' in result.command


class TestTemplateCustomization:
    """Test template customization."""
    
    def test_add_custom_template(self):
        """Test adding custom templates."""
        generator = TemplateGenerator()
        
        generator.add_template('custom', 'deploy', 'deploy {app} to {env}')
        
        result = generator.generate(
            domain='custom',
            intent='deploy',
            entities={'app': 'myapp', 'env': 'production'}
        )
        
        assert result.success
        assert 'deploy myapp to production' in result.command
    
    def test_custom_templates_dict(self):
        """Test initializing with custom templates dict."""
        custom = {
            'myapp': {
                'start': 'start-myapp --config {config}',
                'stop': 'stop-myapp --force',
            }
        }
        
        generator = TemplateGenerator(custom_templates=custom)
        
        result = generator.generate('myapp', 'start', {'config': 'prod.yml'})
        assert 'start-myapp --config prod.yml' in result.command
    
    def test_list_templates(self):
        """Test listing available templates."""
        generator = TemplateGenerator()
        
        sql_templates = generator.list_templates('sql')
        assert 'select' in sql_templates
        assert 'insert' in sql_templates
        
        docker_templates = generator.list_templates('docker')
        assert 'run' in docker_templates
        assert 'logs' in docker_templates


class TestRuleBasedPipeline:
    """Test complete rule-based pipeline."""
    
    @pytest.fixture
    def pipeline(self) -> RuleBasedPipeline:
        return RuleBasedPipeline()
    
    # ==================== SQL Pipeline ====================
    
    def test_pipeline_sql_select(self, pipeline):
        """Test pipeline for SQL SELECT."""
        result = pipeline.process("Pokaż wszystkich użytkowników z tabeli users")
        
        assert result.domain == 'sql'
        assert result.success
        assert 'SELECT' in result.command
        assert 'users' in result.command
    
    def test_pipeline_sql_with_filter(self, pipeline):
        """Test pipeline for SQL with filter."""
        result = pipeline.process("Pokaż użytkowników z tabeli users gdzie status = active")
        
        assert result.domain == 'sql'
        assert 'users' in result.command
    
    def test_pipeline_sql_with_limit(self, pipeline):
        """Test pipeline for SQL with limit."""
        result = pipeline.process("Pokaż 10 rekordów z tabeli orders")
        
        assert result.domain == 'sql'
        assert 'orders' in result.command
    
    # ==================== Shell Pipeline ====================
    
    def test_pipeline_shell_find(self, pipeline):
        """Test pipeline for shell find."""
        result = pipeline.process("Znajdź pliki .py w katalogu /home/user")
        
        assert result.domain == 'shell'
        assert result.success
        assert 'find' in result.command
    
    def test_pipeline_shell_process(self, pipeline):
        """Test pipeline for shell process."""
        result = pipeline.process("ps aux pokaż procesy systemowe")
        
        assert result.domain == 'shell'
    
    # ==================== Docker Pipeline ====================
    
    def test_pipeline_docker_list(self, pipeline):
        """Test pipeline for docker list."""
        result = pipeline.process("Pokaż uruchomione kontenery")
        
        assert result.domain == 'docker'
        assert result.success
        assert 'docker' in result.command
    
    def test_pipeline_docker_logs(self, pipeline):
        """Test pipeline for docker logs."""
        result = pipeline.process("Pokaż logi kontenera myapp")
        
        assert result.domain == 'docker'
        assert 'docker' in result.command
    
    # ==================== Kubernetes Pipeline ====================
    
    def test_pipeline_k8s_get(self, pipeline):
        """Test pipeline for kubectl get."""
        result = pipeline.process("Pokaż wszystkie pody w namespace default")
        
        assert result.domain == 'kubernetes'
        assert result.success
        assert 'kubectl' in result.command
    
    def test_pipeline_k8s_scale(self, pipeline):
        """Test pipeline for kubectl scale."""
        result = pipeline.process("Skaluj deployment myapp do 5 replik")
        
        assert result.domain == 'kubernetes'
        assert 'kubectl' in result.command
    
    # ==================== Edge Cases ====================
    
    def test_pipeline_unknown_input(self, pipeline):
        """Test pipeline with unknown input."""
        result = pipeline.process("xyzqwerty abcdef")
        
        assert result.domain == 'unknown'
        assert not result.success
        assert len(result.errors) > 0
    
    def test_pipeline_empty_input(self, pipeline):
        """Test pipeline with empty input."""
        result = pipeline.process("")
        
        assert result.domain == 'unknown'
        assert not result.success


class TestPipelineResult:
    """Test PipelineResult methods."""
    
    def test_to_plan(self):
        """Test conversion to execution plan."""
        result = PipelineResult(
            input_text="test",
            domain="sql",
            intent="select",
            detection_confidence=0.85,
            entities={"table": "users"},
            command="SELECT * FROM users;",
            template_used="test",
            success=True,
        )
        
        plan = result.to_plan()
        
        assert plan["intent"] == "select"
        assert plan["entities"]["table"] == "users"
        assert plan["confidence"] == 0.85


class TestPipelineMetrics:
    """Test pipeline metrics tracking."""
    
    def test_metrics_recording(self):
        """Test recording pipeline results."""
        metrics = PipelineMetrics()
        
        # Record some results
        result1 = PipelineResult(
            input_text="test1",
            domain="sql",
            intent="select",
            detection_confidence=0.9,
            entities={},
            command="SELECT *",
            template_used="",
            success=True,
            latency_ms=5.0,
        )
        
        result2 = PipelineResult(
            input_text="test2",
            domain="docker",
            intent="list",
            detection_confidence=0.8,
            entities={},
            command="docker ps",
            template_used="",
            success=True,
            latency_ms=3.0,
        )
        
        result3 = PipelineResult(
            input_text="test3",
            domain="unknown",
            intent="unknown",
            detection_confidence=0.0,
            entities={},
            command="",
            template_used="",
            success=False,
            latency_ms=1.0,
            errors=["Unknown domain"],
        )
        
        metrics.record(result1)
        metrics.record(result2)
        metrics.record(result3)
        
        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.success_rate == 2/3
        assert metrics.avg_latency_ms == 3.0
    
    def test_metrics_report(self):
        """Test generating metrics report."""
        metrics = PipelineMetrics()
        
        result = PipelineResult(
            input_text="test",
            domain="sql",
            intent="select",
            detection_confidence=0.9,
            entities={},
            command="SELECT *",
            template_used="",
            success=True,
            latency_ms=5.0,
        )
        metrics.record(result)
        
        report = metrics.report()
        
        assert "total_requests" in report
        assert "success_rate" in report
        assert "avg_latency_ms" in report
        assert report["total_requests"] == 1


class TestPipelineFactory:
    """Test pipeline factory function."""
    
    def test_create_pipeline_default(self):
        """Test creating default pipeline."""
        pipeline = create_pipeline()
        
        assert isinstance(pipeline, RuleBasedPipeline)
        
        result = pipeline.process("Pokaż użytkowników z tabeli users")
        assert result.domain == 'sql'
    
    def test_create_pipeline_custom_threshold(self):
        """Test creating pipeline with custom threshold."""
        pipeline = create_pipeline(confidence_threshold=0.9)
        
        assert pipeline.confidence_threshold == 0.9
    
    def test_create_pipeline_custom_patterns(self):
        """Test creating pipeline with custom patterns."""
        custom_patterns = {
            'myapp': {
                'deploy': ['myapp-deploy-xyz', 'release-myapp-xyz'],
            }
        }
        
        pipeline = create_pipeline(custom_patterns=custom_patterns)
        
        result = pipeline.process("myapp-deploy-xyz now")
        assert result.domain == 'myapp'


class TestPipelinePerformance:
    """Test pipeline performance."""
    
    @pytest.fixture
    def pipeline(self) -> RuleBasedPipeline:
        return RuleBasedPipeline()
    
    def test_pipeline_latency(self, pipeline):
        """Test that pipeline latency is reasonable (<50ms)."""
        test_inputs = [
            "Pokaż użytkowników z tabeli users",
            "Znajdź pliki .py w /home",
            "Pokaż kontenery docker",
            "Kubectl get pods",
        ]
        
        for text in test_inputs:
            result = pipeline.process(text)
            
            # Latency should be <50ms
            assert result.latency_ms < 50, \
                f"Pipeline too slow: {result.latency_ms:.2f}ms for '{text}'"
    
    def test_pipeline_throughput(self, pipeline):
        """Test pipeline throughput."""
        test_inputs = [
            "Pokaż użytkowników",
            "Find files",
            "Docker ps",
            "Get pods",
        ] * 25  # 100 inputs
        
        start = time.time()
        results = pipeline.process_batch(test_inputs)
        elapsed = time.time() - start
        
        throughput = len(test_inputs) / elapsed
        
        # Should handle at least 100 requests per second
        assert throughput > 100, f"Throughput too low: {throughput:.0f}/s"
        
        print(f"\n=== Pipeline Throughput ===")
        print(f"  Throughput: {throughput:.0f} requests/second")


# End-to-end evaluation dataset
E2E_EVAL_DATASET = [
    # SQL
    ("Pokaż wszystkich użytkowników z tabeli users", "sql", ["SELECT", "users"]),
    ("Wyświetl 10 ostatnich zamówień z tabeli orders", "sql", ["SELECT", "orders"]),
    
    # Shell
    ("Znajdź pliki .py w katalogu /home", "shell", ["find", "/home"]),
    ("Pokaż uruchomione procesy", "shell", ["ps"]),
    
    # Docker
    ("Pokaż uruchomione kontenery", "docker", ["docker", "ps"]),
    ("Logi kontenera webapp", "docker", ["docker", "logs"]),
    
    # Kubernetes
    ("kubectl get pody w namespace production", "kubernetes", ["kubectl", "get", "pods"]),
    ("Skaluj deployment do 3 replik", "kubernetes", ["kubectl", "scale"]),
]


class TestPipelineAccuracy:
    """Measure end-to-end pipeline accuracy."""
    
    @pytest.fixture
    def pipeline(self) -> RuleBasedPipeline:
        return RuleBasedPipeline()
    
    @pytest.mark.parametrize("text,expected_domain,expected_contains", E2E_EVAL_DATASET)
    def test_eval_case(self, pipeline, text, expected_domain, expected_contains):
        """Test individual evaluation case."""
        result = pipeline.process(text)
        
        assert result.domain == expected_domain, \
            f"Domain mismatch for '{text}': expected {expected_domain}, got {result.domain}"
        
        for expected in expected_contains:
            assert expected.lower() in result.command.lower(), \
                f"Expected '{expected}' in command: {result.command}"
    
    def test_overall_accuracy(self, pipeline):
        """Calculate overall end-to-end accuracy."""
        correct_domain = 0
        correct_command = 0
        total = len(E2E_EVAL_DATASET)
        
        for text, expected_domain, expected_contains in E2E_EVAL_DATASET:
            result = pipeline.process(text)
            
            if result.domain == expected_domain:
                correct_domain += 1
                
                cmd_lower = result.command.lower()
                all_present = all(e.lower() in cmd_lower for e in expected_contains)
                if all_present:
                    correct_command += 1
        
        domain_accuracy = correct_domain / total
        command_accuracy = correct_command / total
        
        print(f"\n=== End-to-End Pipeline Accuracy ===")
        print(f"  Domain accuracy: {domain_accuracy:.1%} ({correct_domain}/{total})")
        print(f"  Command accuracy: {command_accuracy:.1%} ({correct_command}/{total})")
        
        # Target: >50% end-to-end accuracy
        assert domain_accuracy >= 0.50, f"Domain accuracy too low: {domain_accuracy:.1%}"
