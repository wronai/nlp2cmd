"""
Test shell command validation functionality.

This module tests shell syntax validation, safety checks,
and comprehensive validation rules for shell commands.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
    ShellValidator,
)


class TestShellValidator:
    """Test shell validator functionality."""
    
    @pytest.fixture
    def validator(self) -> ShellValidator:
        return ShellValidator()
    
    def test_valid_find(self, validator):
        """Test valid find command."""
        result = validator.validate("find /home/user -name '*.py'")
        assert result.is_valid
        assert not result.errors
    
    def test_dangerous_rm_rf(self, validator):
        """Test rm -rf / is blocked."""
        result = validator.validate("rm -rf /")
        assert not result.is_valid
        assert any("dangerous" in error.lower() or "rm -rf /" in error.lower() 
                   for error in result.errors)
    
    def test_sudo_warning(self, validator):
        """Test sudo generates warning."""
        result = validator.validate("sudo apt-get update")
        assert result.is_valid  # Still valid but with warning
        assert any("sudo" in warning.lower() for warning in result.warnings)
    
    def test_unclosed_quote(self, validator):
        """Test unclosed quote detected."""
        result = validator.validate("echo 'unclosed string")
        assert not result.is_valid
        assert any("quote" in error.lower() for error in result.errors)
    
    def test_pipe_chaining_validation(self, validator):
        """Test pipe chaining validation."""
        result = validator.validate("cat file.txt | grep 'error' | wc -l")
        assert result.is_valid
    
    def test_command_substitution(self, validator):
        """Test command substitution validation."""
        result = validator.validate("echo $(date)")
        assert result.is_valid
    
    def test_process_killing_validation(self, validator):
        """Test process killing validation."""
        result = validator.validate("kill -9 1234")
        assert result.is_valid  # Valid but with warning
        assert any("kill -9" in warning or "SIGKILL" in warning 
                   for warning in result.warnings)
    
    def test_file_permission_changes(self, validator):
        """Test file permission change validation."""
        result = validator.validate("chmod 777 sensitive_file")
        assert result.is_valid  # Valid but with warning
        assert any("777" in warning and "permissions" in warning 
                   for warning in result.warnings)
    
    def test_system_file_modification(self, validator):
        """Test system file modification validation."""
        result = validator.validate("echo 'test' >> /etc/passwd")
        assert not result.is_valid
        assert any("system file" in error.lower() or "etc/passwd" in error.lower() 
                   for error in result.errors)
    
    def test_wildcard_expansion_safety(self, validator):
        """Test wildcard expansion safety."""
        result = validator.validate("rm *")
        assert not result.is_valid
        assert any("wildcard" in error.lower() or "all files" in error.lower() 
                   for error in result.errors)
    
    def test_eval_command_blocking(self, validator):
        """Test eval command blocking."""
        result = validator.validate("eval 'rm -rf /'")
        assert not result.is_valid
        assert any("eval" in error.lower() for error in result.errors)
    
    def test_background_job_safety(self, validator):
        """Test background job safety."""
        result = validator.validate("nohup rm -rf / &")
        assert not result.is_valid
        assert any("background" in error.lower() or "nohup" in error.lower() 
                   for error in result.errors)
    
    def test_redirect_validation(self, validator):
        """Test redirect validation."""
        result = validator.validate("ls > output.txt")
        assert result.is_valid
        
        result2 = validator.validate("ls >> output.txt")
        assert result2.is_valid
    
    def test_environment_variable_usage(self, validator):
        """Test environment variable usage."""
        result = validator.validate("echo $PATH")
        assert result.is_valid
    
    def test_command_injection_prevention(self, validator):
        """Test command injection prevention."""
        result = validator.validate("ls; rm -rf /")
        assert not result.is_valid
        assert any("injection" in error.lower() or "command separator" in error.lower() 
                   for error in result.errors)
    
    def test_path_traversal_prevention(self, validator):
        """Test path traversal prevention."""
        result = validator.validate("cat ../../../etc/passwd")
        assert not result.is_valid
        assert any("path traversal" in error.lower() or "directory traversal" in error.lower() 
                   for error in result.errors)
