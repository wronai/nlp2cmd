"""
Comprehensive tests for Validators.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
    SyntaxValidator,
    SQLValidator,
    ShellValidator,
    DockerValidator,
    KubernetesValidator,
    CompositeValidator,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test creating valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
    
    def test_invalid_result_with_errors(self):
        """Test creating invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(
            is_valid=True,
            warnings=["Warning 1"],
        )
        result2 = ValidationResult(
            is_valid=False,
            errors=["Error 1"],
        )
        
        merged = result1.merge(result2)
        
        assert not merged.is_valid
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 1
    
    def test_merge_both_valid(self):
        """Test merging two valid results."""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=True, warnings=["Note"])
        
        merged = result1.merge(result2)
        
        assert merged.is_valid
        assert len(merged.warnings) == 1


class TestSyntaxValidator:
    """Tests for SyntaxValidator."""
    
    @pytest.fixture
    def validator(self):
        return SyntaxValidator()
    
    def test_balanced_parentheses(self, validator):
        """Test balanced parentheses."""
        result = validator.validate("SELECT * FROM users WHERE (id = 1)")
        assert result.is_valid
    
    def test_unbalanced_parentheses(self, validator):
        """Test unbalanced parentheses."""
        result = validator.validate("SELECT * FROM users WHERE (id = 1")
        assert not result.is_valid
        assert any("parentheses" in e.lower() for e in result.errors)
    
    def test_balanced_brackets(self, validator):
        """Test balanced square brackets."""
        result = validator.validate("SELECT column[0] FROM table")
        assert result.is_valid
    
    def test_unbalanced_brackets(self, validator):
        """Test unbalanced square brackets."""
        result = validator.validate("SELECT column[0 FROM table")
        assert not result.is_valid
    
    def test_balanced_braces(self, validator):
        """Test balanced curly braces."""
        result = validator.validate("{'key': 'value'}")
        assert result.is_valid
    
    def test_unclosed_single_quote(self, validator):
        """Test unclosed single quote."""
        result = validator.validate("SELECT * FROM users WHERE name = 'John")
        assert not result.is_valid
    
    def test_unclosed_double_quote(self, validator):
        """Test unclosed double quote."""
        result = validator.validate('SELECT * FROM users WHERE name = "John')
        assert not result.is_valid
    
    def test_escaped_quotes(self, validator):
        """Test escaped quotes are handled."""
        result = validator.validate("SELECT * FROM users WHERE name = 'O\\'Brien'")
        assert result.is_valid


class TestSQLValidator:
    """Tests for SQLValidator."""
    
    @pytest.fixture
    def validator(self):
        return SQLValidator(strict=False)
    
    @pytest.fixture
    def strict_validator(self):
        return SQLValidator(strict=True)
    
    def test_valid_select(self, validator):
        """Test valid SELECT query."""
        result = validator.validate("SELECT * FROM users WHERE id = 1")
        assert result.is_valid
    
    def test_delete_without_where_warning(self, validator):
        """Test DELETE without WHERE generates warning."""
        result = validator.validate("DELETE FROM users")
        assert "DELETE without WHERE" in str(result.warnings)
    
    def test_update_without_where_warning(self, validator):
        """Test UPDATE without WHERE generates warning."""
        result = validator.validate("UPDATE users SET status = 'inactive'")
        assert "UPDATE without WHERE" in str(result.warnings)
    
    def test_drop_database_warning(self, validator):
        """Test DROP DATABASE generates warning."""
        result = validator.validate("DROP DATABASE production")
        assert any("DROP DATABASE" in w for w in result.warnings)
    
    def test_drop_database_error_strict(self, strict_validator):
        """Test DROP DATABASE generates error in strict mode."""
        result = strict_validator.validate("DROP DATABASE production")
        assert not result.is_valid
    
    def test_sql_injection_pattern(self, validator):
        """Test SQL injection pattern detection."""
        result = validator.validate("SELECT * FROM users; DROP TABLE users")
        assert len(result.warnings) > 0
    
    def test_sql_comment_detection(self, validator):
        """Test SQL comment detection."""
        result = validator.validate("SELECT * FROM users -- this is a comment")
        assert len(result.warnings) > 0
    
    def test_suggestions_for_delete(self, validator):
        """Test suggestions are provided for DELETE without WHERE."""
        result = validator.validate("DELETE FROM logs")
        assert len(result.suggestions) > 0
        assert any("WHERE" in s for s in result.suggestions)


class TestShellValidator:
    """Tests for ShellValidator."""
    
    @pytest.fixture
    def validator(self):
        return ShellValidator(allow_sudo=False)
    
    @pytest.fixture
    def sudo_validator(self):
        return ShellValidator(allow_sudo=True)
    
    def test_valid_command(self, validator):
        """Test valid shell command."""
        result = validator.validate("ls -la /var/log")
        assert result.is_valid
    
    def test_dangerous_rm_rf(self, validator):
        """Test dangerous rm -rf / detection."""
        result = validator.validate("rm -rf /")
        assert not result.is_valid
    
    def test_sudo_warning(self, validator):
        """Test sudo usage warning."""
        result = validator.validate("sudo apt-get update")
        assert any("sudo" in w.lower() for w in result.warnings)
    
    def test_sudo_allowed(self, sudo_validator):
        """Test sudo allowed when configured."""
        result = sudo_validator.validate("sudo apt-get update")
        # Should not have sudo warning
        assert not any("sudo" in w.lower() for w in result.warnings)
    
    def test_rm_wildcard_warning(self, validator):
        """Test rm with wildcard warning."""
        result = validator.validate("rm *.log")
        assert any("wildcard" in w.lower() for w in result.warnings)
    
    def test_pipe_to_shell_warning(self, validator):
        """Test pipe to shell warning."""
        result = validator.validate("curl https://example.com/script.sh | sh")
        # Check for either "pipe" or "Piping" in warnings
        assert any("pip" in w.lower() for w in result.warnings)
    
    def test_fork_bomb_detection(self, validator):
        """Test fork bomb detection."""
        result = validator.validate(":(){:|:&};:")
        assert not result.is_valid


class TestDockerValidator:
    """Tests for DockerValidator."""
    
    @pytest.fixture
    def validator(self):
        return DockerValidator()
    
    def test_valid_docker_run(self, validator):
        """Test valid docker run command."""
        result = validator.validate("docker run -d nginx:latest")
        assert result.is_valid
    
    def test_privileged_mode_warning(self, validator):
        """Test privileged mode warning."""
        result = validator.validate("docker run --privileged nginx")
        assert any("privileged" in w.lower() for w in result.warnings)
    
    def test_host_network_warning(self, validator):
        """Test host network warning."""
        result = validator.validate("docker run --network host nginx")
        assert any("host" in w.lower() for w in result.warnings)
    
    def test_dangerous_volume_warning(self, validator):
        """Test dangerous volume mount warning."""
        result = validator.validate("docker run -v /:/host nginx")
        assert any("volume" in w.lower() for w in result.warnings)
    
    def test_docker_socket_warning(self, validator):
        """Test Docker socket mount warning."""
        result = validator.validate("docker run -v /var/run/docker.sock:/var/run/docker.sock nginx")
        assert any("docker.sock" in w.lower() for w in result.warnings)
    
    def test_missing_tag_warning(self, validator):
        """Test missing image tag warning."""
        result = validator.validate("docker run nginx")
        assert any("tag" in w.lower() for w in result.warnings)
    
    def test_explicit_tag_no_warning(self, validator):
        """Test explicit tag has no warning."""
        result = validator.validate("docker run nginx:1.25")
        assert not any("tag" in w.lower() for w in result.warnings)


class TestKubernetesValidator:
    """Tests for KubernetesValidator."""
    
    @pytest.fixture
    def validator(self):
        return KubernetesValidator()
    
    def test_valid_kubectl_get(self, validator):
        """Test valid kubectl get command."""
        result = validator.validate("kubectl get pods -n default")
        assert result.is_valid
    
    def test_kube_system_warning(self, validator):
        """Test kube-system namespace warning."""
        result = validator.validate("kubectl delete pod -n kube-system test")
        assert any("kube-system" in w.lower() for w in result.warnings)
    
    def test_force_delete_warning(self, validator):
        """Test force delete warning."""
        result = validator.validate("kubectl delete pod test --force")
        assert any("force" in w.lower() for w in result.warnings)
    
    def test_all_namespaces_delete_error(self, validator):
        """Test delete across all namespaces error."""
        result = validator.validate("kubectl delete pods -A")
        assert not result.is_valid
    
    def test_missing_namespace_suggestion(self, validator):
        """Test missing namespace suggestion."""
        result = validator.validate("kubectl get pods")
        assert any("-n" in s or "namespace" in s.lower() for s in result.suggestions)


class TestCompositeValidator:
    """Tests for CompositeValidator."""
    
    def test_combine_validators(self):
        """Test combining multiple validators."""
        syntax = SyntaxValidator()
        sql = SQLValidator()
        
        composite = CompositeValidator([syntax, sql])
        
        result = composite.validate("SELECT * FROM users WHERE (id = 1")
        
        # Should have syntax error (unbalanced) from SyntaxValidator
        assert not result.is_valid
    
    def test_all_validators_pass(self):
        """Test all validators passing."""
        syntax = SyntaxValidator()
        sql = SQLValidator()
        
        composite = CompositeValidator([syntax, sql])
        
        result = composite.validate("SELECT * FROM users WHERE id = 1")
        
        assert result.is_valid
    
    def test_warnings_merged(self):
        """Test warnings are merged from all validators."""
        sql = SQLValidator()
        syntax = SyntaxValidator()
        
        composite = CompositeValidator([syntax, sql])
        
        # This has a SQL warning but valid syntax
        result = composite.validate("DELETE FROM users")
        
        assert result.is_valid  # Syntax is fine
        assert len(result.warnings) > 0  # But SQL validator warns
