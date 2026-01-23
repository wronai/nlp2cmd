"""
Test Docker command validation functionality.

This module tests Docker syntax validation, safety checks,
and comprehensive validation rules for Docker commands.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
    DockerValidator,
)


class TestDockerValidator:
    """Test Docker validator functionality."""
    
    @pytest.fixture
    def validator(self) -> DockerValidator:
        return DockerValidator()
    
    def test_valid_docker_ps(self, validator):
        """Test valid docker ps."""
        result = validator.validate("docker ps")
        assert result.is_valid
        assert not result.errors
    
    def test_non_docker_command(self, validator):
        """Test non-docker command rejected."""
        result = validator.validate("ls -la")
        assert not result.is_valid
        assert any("docker" in error.lower() for error in result.errors)
    
    def test_privileged_warning(self, validator):
        """Test privileged mode warning."""
        result = validator.validate("docker run --privileged nginx")
        assert result.is_valid  # Still valid but with warning
        assert any("privileged" in warning.lower() for warning in result.warnings)
    
    def test_docker_socket_mount_warning(self, validator):
        """Test Docker socket mount warning."""
        result = validator.validate("docker run -v /var/run/docker.sock:/var/run/docker.sock nginx")
        assert result.is_valid  # Valid but with warning
        assert any("docker socket" in warning.lower() or "socket" in warning.lower() 
                   for warning in result.warnings)
    
    def test_root_user_warning(self, validator):
        """Test root user warning."""
        result = validator.validate("docker run --user root nginx")
        assert result.is_valid  # Valid but with warning
        assert any("root" in warning.lower() for warning in result.warnings)
    
    def test_host_network_warning(self, validator):
        """Test host network warning."""
        result = validator.validate("docker run --network host nginx")
        assert result.is_valid  # Valid but with warning
        assert any("host network" in warning.lower() for warning in result.warnings)
    
    def test_docker_rm_force_warning(self, validator):
        """Test docker rm -f warning."""
        result = validator.validate("docker rm -f container")
        assert result.is_valid  # Valid but with warning
        assert any("force" in warning.lower() or "-f" in warning 
                   for warning in result.warnings)
    
    def test_docker_kill_warning(self, validator):
        """Test docker kill warning."""
        result = validator.validate("docker kill container")
        assert result.is_valid  # Valid but with warning
        assert any("kill" in warning.lower() for warning in result.warnings)
    
    def test_invalid_image_name(self, validator):
        """Test invalid image name."""
        result = validator.validate("docker run invalid@image:name")
        assert not result.is_valid
        assert any("image name" in error.lower() or "invalid" in error.lower() 
                   for error in result.errors)
    
    def test_docker_build_context_warning(self, validator):
        """Test Docker build context warning."""
        result = validator.validate("docker build /")
        assert result.is_valid  # Valid but with warning
        assert any("build context" in warning.lower() or "root directory" in warning.lower() 
                   for warning in result.warnings)
    
    def test_docker_compose_validation(self, validator):
        """Test docker compose validation."""
        result = validator.validate("docker-compose up")
        assert result.is_valid
    
    def test_docker_volume_mount_validation(self, validator):
        """Test Docker volume mount validation."""
        result = validator.validate("docker run -v /host/path:/container/path nginx")
        assert result.is_valid
    
    def test_docker_port_validation(self, validator):
        """Test Docker port validation."""
        result = validator.validate("docker run -p 8080:80 nginx")
        assert result.is_valid
        
        # Test invalid port
        result2 = validator.validate("docker run -p 99999:80 nginx")
        assert not result2.is_valid
        assert any("port" in error.lower() and "invalid" in error.lower() 
                   for error in result2.errors)
    
    def test_docker_environment_variable_validation(self, validator):
        """Test Docker environment variable validation."""
        result = validator.validate("docker run -e ENV_VAR=value nginx")
        assert result.is_valid
    
    def test_docker_resource_limits(self, validator):
        """Test Docker resource limits."""
        result = validator.validate("docker run --memory=512m --cpus=0.5 nginx")
        assert result.is_valid
    
    def test_docker_entrypoint_validation(self, validator):
        """Test Docker entrypoint validation."""
        result = validator.validate("docker run --entrypoint /bin/sh nginx")
        assert result.is_valid
    
    def test_docker_security_options(self, validator):
        """Test Docker security options."""
        result = validator.validate("docker run --security-opt=no-new-privileges nginx")
        assert result.is_valid
    
    def test_docker_label_validation(self, validator):
        """Test Docker label validation."""
        result = validator.validate("docker run --label=app=web nginx")
        assert result.is_valid
