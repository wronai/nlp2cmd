"""
Tests for Action Registry.
"""

import pytest
from nlp2cmd.registry import (
    ActionRegistry,
    ActionSchema,
    ActionResult,
    ActionHandler,
    ParamSchema,
    ParamType,
    get_registry,
)


class TestParamType:
    """Tests for ParamType enum."""
    
    def test_all_types_exist(self):
        """Test all parameter types are defined."""
        assert ParamType.STRING.value == "string"
        assert ParamType.INTEGER.value == "integer"
        assert ParamType.FLOAT.value == "float"
        assert ParamType.BOOLEAN.value == "boolean"
        assert ParamType.LIST.value == "list"
        assert ParamType.DICT.value == "dict"
        assert ParamType.ANY.value == "any"
        assert ParamType.FILE_PATH.value == "file_path"
        assert ParamType.SQL_IDENTIFIER.value == "sql_identifier"
        assert ParamType.K8S_RESOURCE.value == "k8s_resource"


class TestParamSchema:
    """Tests for ParamSchema dataclass."""
    
    def test_basic_param(self):
        """Test creating a basic parameter schema."""
        param = ParamSchema(
            name="table",
            type=ParamType.STRING,
        )
        assert param.name == "table"
        assert param.type == ParamType.STRING
        assert param.required is True
        assert param.default is None
    
    def test_optional_param(self):
        """Test optional parameter."""
        param = ParamSchema(
            name="limit",
            type=ParamType.INTEGER,
            required=False,
            default=10,
            min_value=1,
            max_value=1000,
        )
        assert param.required is False
        assert param.default == 10
        assert param.min_value == 1
        assert param.max_value == 1000
    
    def test_param_with_allowed_values(self):
        """Test parameter with allowed values."""
        param = ParamSchema(
            name="format",
            type=ParamType.STRING,
            allowed_values=["json", "yaml", "xml"],
        )
        assert param.allowed_values == ["json", "yaml", "xml"]


class TestActionSchema:
    """Tests for ActionSchema dataclass."""
    
    def test_basic_schema(self):
        """Test creating a basic action schema."""
        schema = ActionSchema(
            name="sql_select",
            description="Execute SELECT query",
            domain="sql",
        )
        assert schema.name == "sql_select"
        assert schema.domain == "sql"
        assert schema.params == []
        assert schema.is_destructive is False
    
    def test_schema_with_params(self):
        """Test schema with parameters."""
        schema = ActionSchema(
            name="sql_insert",
            description="Insert data",
            domain="sql",
            params=[
                ParamSchema(name="table", type=ParamType.STRING),
                ParamSchema(name="values", type=ParamType.DICT),
            ],
            is_destructive=True,
            requires_confirmation=True,
        )
        assert len(schema.params) == 2
        assert schema.is_destructive is True
        assert schema.requires_confirmation is True
    
    def test_get_required_params(self):
        """Test getting required parameters."""
        schema = ActionSchema(
            name="test",
            description="Test",
            domain="test",
            params=[
                ParamSchema(name="required1", type=ParamType.STRING),
                ParamSchema(name="optional1", type=ParamType.STRING, required=False),
                ParamSchema(name="required2", type=ParamType.INTEGER),
            ],
        )
        required = schema.get_required_params()
        assert required == ["required1", "required2"]
    
    def test_get_optional_params(self):
        """Test getting optional parameters."""
        schema = ActionSchema(
            name="test",
            description="Test",
            domain="test",
            params=[
                ParamSchema(name="required1", type=ParamType.STRING),
                ParamSchema(name="optional1", type=ParamType.STRING, required=False),
                ParamSchema(name="optional2", type=ParamType.INTEGER, required=False),
            ],
        )
        optional = schema.get_optional_params()
        assert optional == ["optional1", "optional2"]
    
    def test_get_param(self):
        """Test getting a specific parameter."""
        schema = ActionSchema(
            name="test",
            description="Test",
            domain="test",
            params=[
                ParamSchema(name="param1", type=ParamType.STRING),
                ParamSchema(name="param2", type=ParamType.INTEGER),
            ],
        )
        param = schema.get_param("param2")
        assert param is not None
        assert param.type == ParamType.INTEGER
        
        assert schema.get_param("nonexistent") is None


class TestActionResult:
    """Tests for ActionResult dataclass."""
    
    def test_success_result(self):
        """Test creating success result."""
        result = ActionResult.ok(data={"count": 42}, rows=10)
        assert result.success is True
        assert result.data == {"count": 42}
        assert result.error is None
        assert result.metadata["rows"] == 10
    
    def test_failure_result(self):
        """Test creating failure result."""
        result = ActionResult.fail(error="Table not found", table="users")
        assert result.success is False
        assert result.error == "Table not found"
        assert result.data is None
        assert result.metadata["table"] == "users"


class TestActionHandler:
    """Tests for ActionHandler."""
    
    @pytest.fixture
    def schema(self):
        """Create test schema."""
        return ActionSchema(
            name="test_action",
            description="Test action",
            domain="test",
            params=[
                ParamSchema(name="required_str", type=ParamType.STRING),
                ParamSchema(name="optional_int", type=ParamType.INTEGER, required=False, default=10),
                ParamSchema(name="limited", type=ParamType.INTEGER, min_value=1, max_value=100, required=False),
                ParamSchema(name="choices", type=ParamType.STRING, allowed_values=["a", "b", "c"], required=False),
            ],
        )
    
    def test_validate_valid_params(self, schema):
        """Test validating valid parameters."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "required_str": "hello",
            "optional_int": 20,
        })
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required(self, schema):
        """Test validation fails for missing required."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "optional_int": 20,
        })
        assert is_valid is False
        assert any("required_str" in e for e in errors)
    
    def test_validate_wrong_type(self, schema):
        """Test validation fails for wrong type."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "required_str": 123,  # Should be string
        })
        assert is_valid is False
        assert any("type" in e.lower() for e in errors)
    
    def test_validate_out_of_range(self, schema):
        """Test validation fails for out of range value."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "required_str": "test",
            "limited": 200,  # Max is 100
        })
        assert is_valid is False
        assert any("100" in e for e in errors)
    
    def test_validate_invalid_choice(self, schema):
        """Test validation fails for invalid choice."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "required_str": "test",
            "choices": "d",  # Not in allowed values
        })
        assert is_valid is False
        assert any("must be one of" in e for e in errors)
    
    def test_validate_unknown_param(self, schema):
        """Test validation fails for unknown parameter."""
        handler = ActionHandler(schema)
        is_valid, errors = handler.validate_params({
            "required_str": "test",
            "unknown_param": "value",
        })
        assert is_valid is False
        assert any("Unknown" in e for e in errors)


class TestActionRegistry:
    """Tests for ActionRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create fresh registry."""
        return ActionRegistry()
    
    def test_builtin_actions_registered(self, registry):
        """Test built-in actions are registered."""
        assert registry.has("sql_select")
        assert registry.has("sql_insert")
        assert registry.has("shell_find")
        assert registry.has("docker_ps")
        assert registry.has("k8s_get")
    
    def test_list_actions(self, registry):
        """Test listing all actions."""
        actions = registry.list_actions()
        assert len(actions) > 10
        assert "sql_select" in actions
    
    def test_list_actions_by_domain(self, registry):
        """Test listing actions by domain."""
        sql_actions = registry.list_actions(domain="sql")
        assert "sql_select" in sql_actions
        assert "docker_ps" not in sql_actions
    
    def test_list_domains(self, registry):
        """Test listing domains."""
        domains = registry.list_domains()
        assert "sql" in domains
        assert "shell" in domains
        assert "docker" in domains
        assert "kubernetes" in domains
    
    def test_get_action_schema(self, registry):
        """Test getting action schema."""
        schema = registry.get("sql_select")
        assert schema is not None
        assert schema.name == "sql_select"
        assert schema.domain == "sql"
    
    def test_get_nonexistent(self, registry):
        """Test getting nonexistent action."""
        assert registry.get("nonexistent") is None
    
    def test_register_custom_action(self, registry):
        """Test registering custom action."""
        schema = ActionSchema(
            name="custom_action",
            description="Custom action",
            domain="custom",
            params=[
                ParamSchema(name="input", type=ParamType.STRING),
            ],
        )
        registry.register(schema)
        
        assert registry.has("custom_action")
        assert "custom_action" in registry.list_actions(domain="custom")
    
    def test_validate_action(self, registry):
        """Test validating action parameters."""
        is_valid, errors = registry.validate_action(
            "sql_select",
            {"table": "users"}
        )
        assert is_valid is True
    
    def test_validate_unknown_action(self, registry):
        """Test validating unknown action."""
        is_valid, errors = registry.validate_action(
            "nonexistent",
            {}
        )
        assert is_valid is False
        assert any("Unknown" in e for e in errors)
    
    def test_get_by_tag(self, registry):
        """Test getting actions by tag."""
        read_actions = registry.get_by_tag("read")
        assert len(read_actions) > 0
        assert all("read" in a.tags for a in read_actions)
    
    def test_get_destructive_actions(self, registry):
        """Test getting destructive actions."""
        destructive = registry.get_destructive_actions()
        assert "sql_insert" in destructive
        assert "sql_delete" in destructive
        assert "docker_stop" in destructive
    
    def test_to_llm_prompt(self, registry):
        """Test generating LLM prompt."""
        prompt = registry.to_llm_prompt()
        assert "Available actions:" in prompt
        assert "sql_select" in prompt
        assert "Description:" in prompt
    
    def test_to_llm_prompt_with_domain(self, registry):
        """Test generating LLM prompt for specific domain."""
        prompt = registry.to_llm_prompt(domain="sql")
        assert "sql_select" in prompt
        assert "docker_ps" not in prompt


class TestGetRegistry:
    """Tests for get_registry function."""
    
    def test_singleton(self):
        """Test registry is singleton."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2
    
    def test_has_builtin_actions(self):
        """Test global registry has built-in actions."""
        registry = get_registry()
        assert registry.has("sql_select")


class TestRegistryEdgeCases:
    """Edge case tests for Action Registry."""
    
    def test_register_with_handler(self):
        """Test registering action with handler."""
        registry = ActionRegistry()
        schema = ActionSchema(
            name="with_handler",
            description="Action with handler",
            domain="test",
        )
        
        class TestHandler(ActionHandler):
            def execute(self, params):
                return ActionResult.ok(data="executed")
        
        handler = TestHandler(schema)
        registry.register(schema, handler)
        
        assert registry.get_handler("with_handler") is not None
    
    def test_param_with_custom_validator(self):
        """Test parameter with custom validator."""
        def is_even(value):
            return value % 2 == 0
        
        schema = ActionSchema(
            name="test",
            description="Test",
            domain="test",
            params=[
                ParamSchema(
                    name="even_number",
                    type=ParamType.INTEGER,
                    validators=[is_even],
                ),
            ],
        )
        
        handler = ActionHandler(schema)
        
        # Valid - even number
        is_valid, _ = handler.validate_params({"even_number": 4})
        assert is_valid is True
        
        # Invalid - odd number
        is_valid, errors = handler.validate_params({"even_number": 3})
        assert is_valid is False
        assert any("validation" in e.lower() for e in errors)
