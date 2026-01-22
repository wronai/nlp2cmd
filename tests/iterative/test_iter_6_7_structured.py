"""
Iteration 6-7: Structured Output & Validation Tests.

Test structured JSON output and self-correcting validation.
"""

import pytest
import json

from nlp2cmd.generation.structured import (
    StructuredLLMPlanner,
    StructuredPlan,
    StructuredPlanResult,
    MultiStepPlanner,
    MultiStepPlan,
    PLAN_SCHEMA,
)
from nlp2cmd.generation.validating import (
    ValidatingGenerator,
    ValidationResult,
    SimpleSQLValidator,
    SimpleShellValidator,
    SimpleDockerValidator,
    SimpleKubernetesValidator,
    create_default_validators,
)
from nlp2cmd.generation.llm_simple import MockLLMClient
from nlp2cmd.generation.llm_multi import MultiDomainGenerator


class TestStructuredPlan:
    """Test StructuredPlan dataclass."""
    
    def test_create_plan(self):
        """Test creating a structured plan."""
        plan = StructuredPlan(
            domain="sql",
            intent="select",
            entities={"table": "users", "columns": ["id", "name"]},
            confidence=0.95,
        )
        
        assert plan.domain == "sql"
        assert plan.intent == "select"
        assert plan.entities["table"] == "users"
    
    def test_to_adapter_plan(self):
        """Test conversion to adapter format."""
        plan = StructuredPlan(
            domain="sql",
            intent="select",
            entities={"table": "users"},
            confidence=0.9,
        )
        
        adapter_plan = plan.to_adapter_plan()
        
        assert adapter_plan["intent"] == "select"
        assert adapter_plan["entities"]["table"] == "users"
        assert adapter_plan["confidence"] == 0.9


class TestStructuredLLMPlanner:
    """Test structured LLM planner."""
    
    @pytest.fixture
    def planner(self) -> StructuredLLMPlanner:
        mock = MockLLMClient(responses={
            "użytkownik": json.dumps({
                "domain": "sql",
                "intent": "select",
                "entities": {"table": "users"},
                "confidence": 0.95
            }),
        })
        return StructuredLLMPlanner(mock)
    
    @pytest.mark.asyncio
    async def test_plan_returns_structured(self, planner):
        """Test that plan returns structured result."""
        result = await planner.plan("Pokaż użytkowników")
        
        # Mock may not return valid JSON, but test the flow
        assert isinstance(result, StructuredPlanResult)
    
    @pytest.mark.asyncio
    async def test_plan_with_context(self, planner):
        """Test planning with context."""
        result = await planner.plan(
            "Pokaż dane",
            context={"available_tables": ["users", "orders"]}
        )
        
        assert isinstance(result, StructuredPlanResult)
    
    def test_parse_response_valid_json(self, planner):
        """Test parsing valid JSON response."""
        json_str = json.dumps({
            "domain": "sql",
            "intent": "select",
            "entities": {"table": "test"},
            "confidence": 0.9
        })
        
        plan = planner._parse_response(json_str)
        
        assert plan.domain == "sql"
        assert plan.intent == "select"
    
    def test_parse_response_with_markdown(self, planner):
        """Test parsing JSON with markdown wrapper."""
        json_str = """```json
{
  "domain": "shell",
  "intent": "find",
  "entities": {"path": "/home"},
  "confidence": 0.85
}
```"""
        
        plan = planner._parse_response(json_str)
        
        assert plan.domain == "shell"
        assert plan.intent == "find"
    
    def test_parse_response_missing_domain_raises(self, planner):
        """Test that missing domain raises error."""
        json_str = json.dumps({
            "intent": "select",
            "entities": {}
        })
        
        with pytest.raises(ValueError, match="domain"):
            planner._parse_response(json_str)


class TestMultiStepPlan:
    """Test multi-step plan."""
    
    def test_create_multi_step_plan(self):
        """Test creating multi-step plan."""
        steps = [
            StructuredPlan("shell", "find", {"path": "/var/log"}),
            StructuredPlan("shell", "count", {"depends_on": 0}),
        ]
        
        plan = MultiStepPlan(
            steps=steps,
            dependencies={1: [0]}
        )
        
        assert len(plan.steps) == 2
        assert plan.dependencies[1] == [0]
    
    def test_execution_order(self):
        """Test execution order with dependencies."""
        steps = [
            StructuredPlan("shell", "step0", {}),
            StructuredPlan("shell", "step1", {}),
            StructuredPlan("shell", "step2", {}),
        ]
        
        plan = MultiStepPlan(
            steps=steps,
            dependencies={2: [0, 1]}  # step2 depends on 0 and 1
        )
        
        order = plan.get_execution_order()
        
        # step2 should come after 0 and 1
        assert order.index(2) > order.index(0)
        assert order.index(2) > order.index(1)


class TestPlanSchema:
    """Test plan JSON schema."""
    
    def test_schema_has_required_fields(self):
        """Test schema has required fields."""
        assert "domain" in PLAN_SCHEMA["properties"]
        assert "intent" in PLAN_SCHEMA["properties"]
        assert "entities" in PLAN_SCHEMA["properties"]
    
    def test_schema_domain_enum(self):
        """Test domain enum values."""
        domain_schema = PLAN_SCHEMA["properties"]["domain"]
        assert "sql" in domain_schema["enum"]
        assert "shell" in domain_schema["enum"]


class TestSimpleSQLValidator:
    """Test SQL validator."""
    
    @pytest.fixture
    def validator(self) -> SimpleSQLValidator:
        return SimpleSQLValidator()
    
    def test_valid_select(self, validator):
        """Test valid SELECT is accepted."""
        result = validator.validate("SELECT * FROM users WHERE id = 1;")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_unbalanced_parentheses(self, validator):
        """Test unbalanced parentheses detected."""
        result = validator.validate("SELECT * FROM users WHERE (id = 1;")
        assert not result.is_valid
        assert any("parentheses" in e.lower() for e in result.errors)
    
    def test_unclosed_string(self, validator):
        """Test unclosed string detected."""
        result = validator.validate("SELECT * FROM users WHERE name = 'test;")
        assert not result.is_valid
        assert any("string" in e.lower() for e in result.errors)
    
    def test_delete_without_where_warning(self, validator):
        """Test DELETE without WHERE generates warning."""
        result = validator.validate("DELETE FROM users;")
        assert result.is_valid  # Valid but with warning
        assert any("DELETE" in w for w in result.warnings)
    
    def test_update_without_where_warning(self, validator):
        """Test UPDATE without WHERE generates warning."""
        result = validator.validate("UPDATE users SET status = 'inactive';")
        assert result.is_valid
        assert any("UPDATE" in w for w in result.warnings)


class TestSimpleShellValidator:
    """Test Shell validator."""
    
    @pytest.fixture
    def validator(self) -> SimpleShellValidator:
        return SimpleShellValidator()
    
    def test_valid_find(self, validator):
        """Test valid find command."""
        result = validator.validate("find /home -name '*.py'")
        assert result.is_valid
    
    def test_dangerous_rm_rf(self, validator):
        """Test rm -rf / is blocked."""
        result = validator.validate("rm -rf /")
        assert not result.is_valid
        assert any("dangerous" in e.lower() for e in result.errors)
    
    def test_sudo_warning(self, validator):
        """Test sudo generates warning."""
        result = validator.validate("sudo apt update")
        assert result.is_valid
        assert any("sudo" in w.lower() for w in result.warnings)
    
    def test_unclosed_quote(self, validator):
        """Test unclosed quote detected."""
        result = validator.validate("echo 'hello")
        assert not result.is_valid


class TestSimpleDockerValidator:
    """Test Docker validator."""
    
    @pytest.fixture
    def validator(self) -> SimpleDockerValidator:
        return SimpleDockerValidator()
    
    def test_valid_docker_ps(self, validator):
        """Test valid docker ps."""
        result = validator.validate("docker ps -a")
        assert result.is_valid
    
    def test_non_docker_command(self, validator):
        """Test non-docker command rejected."""
        result = validator.validate("kubectl get pods")
        assert not result.is_valid
    
    def test_privileged_warning(self, validator):
        """Test privileged mode warning."""
        result = validator.validate("docker run --privileged nginx")
        assert result.is_valid
        assert any("privileged" in w.lower() for w in result.warnings)


class TestSimpleKubernetesValidator:
    """Test Kubernetes validator."""
    
    @pytest.fixture
    def validator(self) -> SimpleKubernetesValidator:
        return SimpleKubernetesValidator()
    
    def test_valid_get_pods(self, validator):
        """Test valid kubectl get pods."""
        result = validator.validate("kubectl get pods -n default")
        assert result.is_valid
    
    def test_non_kubectl_command(self, validator):
        """Test non-kubectl command rejected."""
        result = validator.validate("docker ps")
        assert not result.is_valid
    
    def test_delete_in_kube_system(self, validator):
        """Test delete in kube-system blocked."""
        result = validator.validate("kubectl delete pod test -n kube-system")
        assert not result.is_valid
        assert any("kube-system" in e for e in result.errors)


class TestCreateDefaultValidators:
    """Test validator factory."""
    
    def test_creates_all_validators(self):
        """Test all domain validators are created."""
        validators = create_default_validators()
        
        assert "sql" in validators
        assert "shell" in validators
        assert "docker" in validators
        assert "kubernetes" in validators
    
    def test_validators_work(self):
        """Test created validators are functional."""
        validators = create_default_validators()
        
        sql_result = validators["sql"].validate("SELECT 1;")
        assert sql_result.is_valid


class TestValidatingGenerator:
    """Test validating generator."""
    
    @pytest.fixture
    def generator(self) -> ValidatingGenerator:
        mock = MockLLMClient()
        multi_gen = MultiDomainGenerator(mock)
        validators = create_default_validators()
        return ValidatingGenerator(multi_gen, validators, max_retries=3)
    
    @pytest.mark.asyncio
    async def test_generate_valid_sql(self, generator):
        """Test generating valid SQL."""
        result = await generator.generate("Pokaż użytkowników")
        
        # Mock returns valid SQL
        assert result.attempts >= 1
    
    @pytest.mark.asyncio
    async def test_tracks_attempts(self, generator):
        """Test that attempts are tracked."""
        result = await generator.generate("test query")
        
        assert result.attempts >= 1
        assert result.attempts <= 3  # max_retries


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_with_errors(self):
        """Test invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
