"""
Test Kubernetes keyword intent detection.

This module tests keyword-based intent detection for Kubernetes domain
including pod management, deployments, services, and cluster operations.
"""

import pytest

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult


class TestK8sKeywords:
    """Test Kubernetes keyword intent detection."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_k8s_get_pods_polish(self, detector):
        """Test k8s get pods detection in Polish."""
        result = detector.detect("Pokaż pody w klastrze")
        assert result.domain == 'kubernetes'
        assert result.intent == 'get'
    
    def test_k8s_get_pods_english(self, detector):
        """Test k8s get pods detection in English."""
        result = detector.detect("Get pods in cluster")
        assert result.domain == 'kubernetes'
        assert result.intent == 'get'
    
    def test_k8s_scale(self, detector):
        """Test k8s scale detection."""
        result = detector.detect("Skaluj deployment")
        assert result.domain == 'kubernetes'
        assert result.intent == 'scale'
    
    def test_k8s_logs(self, detector):
        """Test k8s logs detection."""
        result = detector.detect("Pokaż logi poda")
        assert result.domain == 'kubernetes'
        assert result.intent == 'logs'
    
    def test_k8s_describe(self, detector):
        """Test k8s describe detection."""
        result = detector.detect("Opisz deployment")
        assert result.domain == 'kubernetes'
        assert result.intent == 'describe'
    
    def test_k8s_create(self, detector):
        """Test k8s create detection."""
        result = detector.detect("Stwórz deployment")
        assert result.domain == 'kubernetes'
        assert result.intent == 'create'
    
    def test_k8s_delete(self, detector):
        """Test k8s delete detection."""
        result = detector.detect("Usuń pod")
        assert result.domain == 'kubernetes'
        assert result.intent == 'delete'
    
    def test_k8s_apply(self, detector):
        """Test k8s apply detection."""
        result = detector.detect("Zastosuj konfigurację")
        assert result.domain == 'kubernetes'
        assert result.intent == 'apply'
    
    def test_k8s_namespace(self, detector):
        """Test k8s namespace detection."""
        result = detector.detect("W namespace production")
        assert result.domain == 'kubernetes'
        assert 'namespace' in result.entities
    
    def test_k8s_service(self, detector):
        """Test k8s service detection."""
        result = detector.detect("Stwórz serwis")
        assert result.domain == 'kubernetes'
        assert result.intent == 'create_service'
    
    def test_k8s_configmap(self, detector):
        """Test k8s configmap detection."""
        result = detector.detect("Stwórz configmap")
        assert result.domain == 'kubernetes'
        assert result.intent == 'create_configmap'
    
    def test_k8s_secret(self, detector):
        """Test k8s secret detection."""
        result = detector.detect("Stwórz secret")
        assert result.domain == 'kubernetes'
        assert result.intent == 'create_secret'
    
    def test_k8s_ingress(self, detector):
        """Test k8s ingress detection."""
        result = detector.detect("Stwórz ingress")
        assert result.domain == 'kubernetes'
        assert result.intent == 'create_ingress'
