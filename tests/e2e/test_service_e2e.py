#!/usr/bin/env python3
"""
End-to-End Tests for NLP2CMD Service Mode

Tests cover:
1. Service startup and configuration
2. API endpoints functionality
3. Query processing with different DSLs
4. Configuration management
5. Error handling
6. Polish language support
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pytest
import requests
from requests.exceptions import RequestException


class NLP2CMDServiceManager:
    """Manages NLP2CMD service lifecycle for testing."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.process: Optional[subprocess.Popen] = None
        self.env_file = Path("test_e2e.env")
        
    def setup_test_env(self, **overrides):
        """Create test environment configuration."""
        config = {
            "NLP2CMD_HOST": self.host,
            "NLP2CMD_PORT": str(self.port),
            "NLP2CMD_DEBUG": "true",
            "NLP2CMD_LOG_LEVEL": "debug",
            "NLP2CMD_CORS_ORIGINS": "*",
            "NLP2CMD_MAX_WORKERS": "2",
            "NLP2CMD_AUTO_EXECUTE": "false",
            "NLP2CMD_SESSION_TIMEOUT": "3600",
        }
        config.update(overrides)
        
        with open(self.env_file, 'w') as f:
            f.write("# Test E2E Environment\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        return config
    
    def start_service(self, **kwargs) -> subprocess.Popen:
        """Start NLP2CMD service for testing."""
        cmd = [
            sys.executable, "-m", "nlp2cmd", "service",
            "--host", self.host,
            "--port", str(self.port),
            "--debug",
            "--log-level", "debug"
        ]
        
        # Add any additional arguments
        for key, value in kwargs.items():
            if key.startswith("--"):
                cmd.extend([key, str(value)])
        
        # Set environment with test config and PYTHONPATH
        env = os.environ.copy()
        if self.env_file.exists():
            env["NLP2CMD_HOST"] = self.host
            env["NLP2CMD_PORT"] = str(self.port)
        
        # Add src to PYTHONPATH
        src_path = str(Path(__file__).parent.parent.parent / "src")
        env["PYTHONPATH"] = src_path + ":" + env.get("PYTHONPATH", "")
        
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return self.process
    
    def stop_service(self):
        """Stop the service."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
    
    def wait_for_ready(self, timeout: int = 30) -> bool:
        """Wait for service to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except RequestException:
                pass
            time.sleep(0.5)
        return False
    
    def cleanup(self):
        """Clean up test resources."""
        self.stop_service()
        if self.env_file.exists():
            self.env_file.unlink()


@pytest.fixture(scope="function")
def service_manager():
    """Fixture for managing service lifecycle."""
    manager = NLP2CMDServiceManager()
    manager.setup_test_env()
    
    try:
        yield manager
    finally:
        manager.cleanup()


@pytest.fixture(scope="function")
def running_service(service_manager):
    """Fixture that provides a running service."""
    process = service_manager.start_service()
    
    # Wait for service to be ready
    if not service_manager.wait_for_ready():
        service_manager.stop_service()
        pytest.fail("Service failed to start within timeout")
    
    try:
        yield service_manager
    finally:
        service_manager.stop_service()


@pytest.mark.service
@pytest.mark.e2e
class TestServiceE2E:
    """End-to-end tests for NLP2CMD service."""
    
    def test_service_startup_and_health(self, running_service):
        """Test that service starts successfully and responds to health checks."""
        response = requests.get(f"{running_service.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "nlp2cmd"
    
    def test_service_info_endpoint(self, running_service):
        """Test service information endpoint."""
        response = requests.get(f"{running_service.base_url}/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "config" in data
        
        assert data["service"] == "NLP2CMD API"
        assert data["status"] == "running"
        
        # Check configuration
        config = data["config"]
        assert config["host"] == running_service.host
        assert config["port"] == running_service.port
        assert config["debug"] is True
    
    def test_basic_query_processing(self, running_service):
        """Test basic query processing functionality."""
        payload = {
            "query": "list files in current directory",
            "dsl": "shell"
        }
        
        response = requests.post(
            f"{running_service.base_url}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["command"] is not None
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 1
        assert data["domain"] == "shell"
        assert data["intent"] is not None
        assert isinstance(data["entities"], dict)
        assert data["errors"] is None or len(data["errors"]) == 0
        
        # Verify command makes sense
        command = data["command"].lower()
        assert any(cmd in command for cmd in ["ls", "dir", "list"])
    
    def test_polish_language_support(self, running_service):
        """Test Polish language query processing."""
        test_cases = [
            {
                "query": "znajdź pliki większe niż 100MB",
                "dsl": "shell",
                "expected_keywords": ["find", "size", "100"]
            },
            {
                "query": "uruchom usługę nginx",
                "dsl": "shell", 
                "expected_keywords": ["systemctl", "start", "nginx"]
            },
            {
                "query": "pokaż wszystkie procesy",
                "dsl": "shell",
                "expected_keywords": ["ps", "process"]
            }
        ]
        
        for case in test_cases:
            payload = {
                "query": case["query"],
                "dsl": case["dsl"]
            }
            
            response = requests.post(
                f"{running_service.base_url}/query",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["command"] is not None
            
            command = data["command"].lower()
            # Check if expected keywords are present
            found_keywords = sum(1 for kw in case["expected_keywords"] if kw in command)
            assert found_keywords > 0, f"No expected keywords found in command: {command}"
    
    def test_query_with_explanation(self, running_service):
        """Test query processing with explanation."""
        payload = {
            "query": "find all python files",
            "dsl": "shell",
            "explain": True
        }
        
        response = requests.post(
            f"{running_service.base_url}/query",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["explanation"] is not None
        assert "RuleBasedPipeline" in data["explanation"]
        assert "confidence" in data["explanation"]
    
    def test_different_dsl_support(self, running_service):
        """Test support for different DSL types."""
        test_cases = [
            {"query": "show all containers", "dsl": "docker"},
            {"query": "list pods", "dsl": "kubernetes"},
            {"query": "SELECT * FROM users", "dsl": "sql"},
            {"query": "list files", "dsl": "shell"}
        ]
        
        for case in test_cases:
            payload = {
                "query": case["query"],
                "dsl": case["dsl"]
            }
            
            response = requests.post(
                f"{running_service.base_url}/query",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should succeed for most cases
            if data["success"]:
                assert data["command"] is not None
                assert data["domain"] == case["dsl"]
    
    def test_configuration_management(self, running_service):
        """Test configuration get and update endpoints."""
        # Get current configuration
        response = requests.get(f"{running_service.base_url}/config")
        assert response.status_code == 200
        
        original_config = response.json()
        assert "host" in original_config
        assert "port" in original_config
        assert "log_level" in original_config
        
        # Update configuration
        update_payload = {"log_level": "warning"}
        response = requests.post(
            f"{running_service.base_url}/config",
            json=update_payload
        )
        
        assert response.status_code == 200
        update_result = response.json()
        
        assert "message" in update_result
        assert "config" in update_result
        assert update_result["config"]["log_level"] == "warning"
    
    def test_config_save_endpoint(self, running_service):
        """Test configuration save endpoint."""
        test_env_file = "test_save.env"
        
        try:
            # The config/save endpoint doesn't take env_file parameter in the request
            # It uses the default .env file or environment variable
            response = requests.post(
                f"{running_service.base_url}/config/save",
                json={}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "message" in result
            assert "Configuration saved" in result["message"]
            
            # Verify .env file was created (default behavior)
            assert Path(".env").exists()
            
            # Check content
            with open(".env", 'r') as f:
                content = f.read()
                assert "NLP2CMD_HOST" in content
                assert "NLP2CMD_PORT" in content
        
        finally:
            # Cleanup
            if Path(".env").exists():
                Path(".env").unlink()
            if Path(test_env_file).exists():
                Path(test_env_file).unlink()
    
    def test_error_handling(self, running_service):
        """Test error handling for invalid requests."""
        # Test invalid JSON
        response = requests.post(
            f"{running_service.base_url}/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code >= 400
        
        # Test missing required fields
        response = requests.post(
            f"{running_service.base_url}/query",
            json={"dsl": "shell"}  # Missing query
        )
        assert response.status_code >= 400
        
        # Test invalid DSL
        response = requests.post(
            f"{running_service.base_url}/query",
            json={"query": "test", "dsl": "invalid_dsl"}
        )
        # Should handle gracefully (either succeed with fallback or fail gracefully)
        assert response.status_code in [200, 400, 422]
    
    def test_concurrent_requests(self, running_service):
        """Test handling of concurrent requests."""
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = requests.post(
                    f"{running_service.base_url}/query",
                    json={"query": "list files", "dsl": "shell"},
                    timeout=10
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(status == 200 for status in results)
    
    def test_service_restart(self, service_manager):
        """Test service restart functionality."""
        # Start service
        process1 = service_manager.start_service()
        assert service_manager.wait_for_ready()
        
        # Make a request
        response = requests.get(f"{service_manager.base_url}/health")
        assert response.status_code == 200
        
        # Stop service
        service_manager.stop_service()
        
        # Start again
        process2 = service_manager.start_service()
        assert service_manager.wait_for_ready()
        
        # Make another request
        response = requests.get(f"{service_manager.base_url}/health")
        assert response.status_code == 200
        
        service_manager.stop_service()


@pytest.mark.integration
@pytest.mark.e2e
class TestServiceIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_complex_workflow(self, running_service):
        """Test a complete workflow with multiple steps."""
        base_url = running_service.base_url
        
        # Step 1: Check service health
        health_response = requests.get(f"{base_url}/health")
        assert health_response.status_code == 200
        
        # Step 2: Get configuration
        config_response = requests.get(f"{base_url}/config")
        assert config_response.status_code == 200
        
        # Step 3: Process multiple queries
        queries = [
            {"query": "list files", "dsl": "shell"},
            {"query": "show processes", "dsl": "shell"},
            {"query": "find large files", "dsl": "shell", "explain": True}
        ]
        
        for query_payload in queries:
            response = requests.post(f"{base_url}/query", json=query_payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["command"] is not None
        
        # Step 4: Update configuration
        update_response = requests.post(
            f"{base_url}/config",
            json={"log_level": "debug"}
        )
        assert update_response.status_code == 200
        
        # Step 5: Verify update took effect
        config_response = requests.get(f"{base_url}/config")
        assert config_response.json()["log_level"] == "debug"
    
    def test_polish_end_to_end_scenario(self, running_service):
        """Test Polish language scenario end-to-end."""
        base_url = running_service.base_url
        
        # Polish workflow
        polish_queries = [
            "znajdź pliki .log większe niż 10MB",
            "pokaż procesy zużywające najwięcej CPU",
            "uruchom usługę apache2",
            "sprawdź status systemu"
        ]
        
        results = []
        for query in polish_queries:
            response = requests.post(
                f"{base_url}/query",
                json={"query": query, "dsl": "shell", "explain": True}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["command"] is not None
            assert data["explanation"] is not None
            
            results.append({
                "query": query,
                "command": data["command"],
                "confidence": data["confidence"],
                "domain": data["domain"]
            })
        
        # Verify we got reasonable commands
        assert len(results) == len(polish_queries)
        
        # Check that commands make sense for Polish queries
        for result in results:
            command = result["command"].lower()
            assert len(command) > 0
            # Should contain relevant keywords
            assert any(keyword in command for keyword in ["find", "ps", "systemctl", "ls", "cat", "grep"])


if __name__ == "__main__":
    """Run tests directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run E2E tests for NLP2CMD service")
    parser.add_argument("--port", type=int, default=8001, help="Port for test service")
    parser.add_argument("--host", default="127.0.0.1", help="Host for test service")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Configure pytest
    pytest_args = [
        "tests/e2e/test_service_e2e.py",
        "-v" if args.verbose else "-q",
        "--tb=short",
        f"--base-url=http://{args.host}:{args.port}"
    ]
    
    # Run tests
    sys.exit(pytest.main(pytest_args))
