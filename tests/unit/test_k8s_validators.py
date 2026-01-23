"""
Test Kubernetes command validation functionality.

This module tests kubectl syntax validation, safety checks,
and comprehensive validation rules for Kubernetes commands.
"""

import pytest
from nlp2cmd.validators import (
    BaseValidator,
    ValidationResult,
    KubernetesValidator,
)


class TestKubernetesValidator:
    """Test Kubernetes validator functionality."""
    
    @pytest.fixture
    def validator(self) -> KubernetesValidator:
        return KubernetesValidator()
    
    def test_valid_get_pods(self, validator):
        """Test valid kubectl get pods."""
        result = validator.validate("kubectl get pods")
        assert result.is_valid
        assert not result.errors
    
    def test_non_kubectl_command(self, validator):
        """Test non-kubectl command rejected."""
        result = validator.validate("ls -la")
        assert not result.is_valid
        assert any("kubectl" in error.lower() for error in result.errors)
    
    def test_delete_in_kube_system(self, validator):
        """Test delete in kube-system blocked."""
        result = validator.validate("kubectl delete pod some-pod -n kube-system")
        assert not result.is_valid
        assert any("kube-system" in error.lower() or "system namespace" in error.lower() 
                   for error in result.errors)
    
    def test_delete_default_namespace_warning(self, validator):
        """Test delete in default namespace warning."""
        result = validator.validate("kubectl delete pod some-pod")
        assert result.is_valid  # Valid but with warning
        assert any("default namespace" in warning.lower() or "production" in warning.lower() 
                   for warning in result.warnings)
    
    def test_force_delete_warning(self, validator):
        """Test force delete warning."""
        result = validator.validate("kubectl delete pod some-pod --force --grace-period=0")
        assert result.is_valid  # Valid but with warning
        assert any("force delete" in warning.lower() or "grace period" in warning.lower() 
                   for warning in result.warnings)
    
    def test_cluster_admin_operations_warning(self, validator):
        """Test cluster admin operations warning."""
        result = validator.validate("kubectl create clusterrolebinding admin-binding")
        assert result.is_valid  # Valid but with warning
        assert any("cluster" in warning.lower() and "admin" in warning.lower() 
                   for warning in result.warnings)
    
    def test_invalid_resource_type(self, validator):
        """Test invalid resource type."""
        result = validator.validate("kubectl get invalid_resource")
        assert not result.is_valid
        assert any("resource type" in error.lower() or "invalid" in error.lower() 
                   for error in result.errors)
    
    def test_apply_with_yaml_validation(self, validator):
        """Test apply with YAML validation."""
        result = validator.validate("kubectl apply -f deployment.yaml")
        assert result.is_valid
    
    def test_apply_with_invalid_file(self, validator):
        """Test apply with invalid file."""
        result = validator.validate("kubectl apply -f nonexistent.yaml")
        assert result.is_valid  # Valid but with warning
        assert any("file" in warning.lower() and "not found" in warning.lower() 
                   for warning in result.warnings)
    
    def test_exec_command_validation(self, validator):
        """Test exec command validation."""
        result = validator.validate("kubectl exec pod-name -- ls -la")
        assert result.is_valid
    
    def test_port_forward_security(self, validator):
        """Test port forward security."""
        result = validator.validate("kubectl port-forward pod-name 8080:80")
        assert result.is_valid  # Valid but with warning
        assert any("port forward" in warning.lower() for warning in result.warnings)
    
    def test_logs_with_all_namespaces_warning(self, validator):
        """Test logs with all namespaces warning."""
        result = validator.validate("kubectl logs --all-namespaces deployment/name")
        assert result.is_valid  # Valid but with warning
        assert any("all namespaces" in warning.lower() for warning in result.warnings)
    
    def test_scale_operation_validation(self, validator):
        """Test scale operation validation."""
        result = validator.validate("kubectl scale deployment myapp --replicas=3")
        assert result.is_valid
    
    def test_invalid_replica_count(self, validator):
        """Test invalid replica count."""
        result = validator.validate("kubectl scale deployment myapp --replicas=-1")
        assert not result.is_valid
        assert any("replica count" in error.lower() or "negative" in error.lower() 
                   for error in result.errors)
    
    def test_label_selector_validation(self, validator):
        """Test label selector validation."""
        result = validator.validate("kubectl get pods -l app=web")
        assert result.is_valid
    
    def test_field_selector_validation(self, validator):
        """Test field selector validation."""
        result = validator.validate("kubectl get pods --field-selector=status.phase=Running")
        assert result.is_valid
    
    def test_custom_resource_validation(self, validator):
        """Test custom resource validation."""
        result = validator.validate("kubectl get crds")
        assert result.is_valid
    
    def test_dry_run_validation(self, validator):
        """Test dry-run validation."""
        result = validator.validate("kubectl create deployment test --image=nginx --dry-run=client")
        assert result.is_valid
    
    def test_output_format_validation(self, validator):
        """Test output format validation."""
        result = validator.validate("kubectl get pods -o yaml")
        assert result.is_valid
        
        result2 = validator.validate("kubectl get pods -o json")
        assert result2.is_valid
    
    def test_watch_operation_warning(self, validator):
        """Test watch operation warning."""
        result = validator.validate("kubectl get pods --watch")
        assert result.is_valid  # Valid but with warning
        assert any("watch" in warning.lower() for warning in result.warnings)
