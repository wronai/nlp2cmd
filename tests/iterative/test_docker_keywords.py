"""
Test Docker keyword intent detection.

This module tests keyword-based intent detection for Docker domain
including container management, image operations, and Docker Compose.
"""

import pytest

from nlp2cmd.generation.keywords import KeywordIntentDetector, DetectionResult


class TestDockerKeywords:
    """Test Docker keyword intent detection."""
    
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()
    
    def test_docker_list_polish(self, detector):
        """Test docker list detection in Polish."""
        result = detector.detect("Pokaż kontenery Docker")
        assert result.domain == 'docker'
        assert result.intent == 'list'
    
    def test_docker_list_english(self, detector):
        """Test docker list detection in English."""
        result = detector.detect("List docker containers")
        assert result.domain == 'docker'
        assert result.intent == 'list'
    
    def test_docker_run(self, detector):
        """Test docker run detection."""
        result = detector.detect("Uruchom kontener nginx")
        assert result.domain == 'docker'
        assert result.intent == 'run'
    
    def test_docker_logs(self, detector):
        """Test docker logs detection."""
        result = detector.detect("Pokaż logi kontenera")
        assert result.domain == 'docker'
        assert result.intent == 'logs'
    
    def test_docker_compose(self, detector):
        """Test docker compose detection."""
        result = detector.detect("Uruchom docker compose")
        assert result.domain == 'docker'
        assert result.intent == 'compose_up'
    
    def test_docker_stop(self, detector):
        """Test docker stop detection."""
        result = detector.detect("Zatrzymaj kontener")
        assert result.domain == 'docker'
        assert result.intent == 'stop'
    
    def test_docker_start(self, detector):
        """Test docker start detection."""
        result = detector.detect("Uruchom zatrzymany kontener")
        assert result.domain == 'docker'
        assert result.intent == 'start'
    
    def test_docker_remove(self, detector):
        """Test docker remove detection."""
        result = detector.detect("Usuń kontener")
        assert result.domain == 'docker'
        assert result.intent == 'remove'
    
    def test_docker_build(self, detector):
        """Test docker build detection."""
        result = detector.detect("Zbuduj obraz Docker")
        assert result.domain == 'docker'
        assert result.intent == 'build'
    
    def test_docker_pull(self, detector):
        """Test docker pull detection."""
        result = detector.detect("Pobierz obraz z repozytorium")
        assert result.domain == 'docker'
        assert result.intent == 'pull'
    
    def test_docker_push(self, detector):
        """Test docker push detection."""
        result = detector.detect("Wypchnij obraz do repozytorium")
        assert result.domain == 'docker'
        assert result.intent == 'push'
    
    def test_docker_exec(self, detector):
        """Test docker exec detection."""
        result = detector.detect("Wykonaj komendę w kontenerze")
        assert result.domain == 'docker'
        assert result.intent == 'exec'
