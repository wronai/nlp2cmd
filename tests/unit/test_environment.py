"""
Unit tests for NLP2CMD environment module.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from nlp2cmd.environment import (
    EnvironmentAnalyzer,
    EnvironmentReport,
    ToolInfo,
    ServiceInfo,
)


class TestToolInfo:
    """Tests for ToolInfo dataclass."""

    def test_available_tool(self):
        """Test available tool info."""
        info = ToolInfo(
            name="docker",
            available=True,
            version="24.0.5",
            path="/usr/bin/docker",
            config_files=["/home/user/.docker/config.json"],
        )

        assert info.available
        assert info.version == "24.0.5"
        assert len(info.config_files) == 1

    def test_unavailable_tool(self):
        """Test unavailable tool info."""
        info = ToolInfo(
            name="kubectl",
            available=False,
        )

        assert not info.available
        assert info.version is None

    def test_tool_info_defaults(self):
        """Test ToolInfo default values."""
        info = ToolInfo(name="test", available=False)
        
        assert info.version is None
        assert info.path is None
        assert info.config_files == []


class TestServiceInfo:
    """Tests for ServiceInfo dataclass."""

    def test_running_service(self):
        """Test running service info."""
        info = ServiceInfo(
            name="postgresql",
            running=True,
            port=5432,
            reachable=True,
        )

        assert info.running
        assert info.port == 5432
        assert info.reachable

    def test_stopped_service(self):
        """Test stopped service info."""
        info = ServiceInfo(
            name="mysql",
            running=False,
            port=3306,
        )

        assert not info.running
        assert not info.reachable


class TestEnvironmentAnalyzer:
    """Tests for EnvironmentAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return EnvironmentAnalyzer()

    def test_analyze_returns_dict(self, analyzer):
        """Test analyze returns dictionary."""
        result = analyzer.analyze()
        
        assert isinstance(result, dict)
        assert "os" in result
        assert "shell" in result
        assert "user" in result
        assert "cwd" in result

    def test_get_os_info(self, analyzer):
        """Test OS info detection."""
        os_info = analyzer._get_os_info()
        
        assert "system" in os_info
        assert "release" in os_info
        assert "machine" in os_info

    def test_get_shell_info(self, analyzer):
        """Test shell info detection."""
        shell_info = analyzer._get_shell_info()
        
        assert "path" in shell_info
        assert "name" in shell_info

    def test_get_user_info(self, analyzer):
        """Test user info detection."""
        user_info = analyzer._get_user_info()
        
        assert "name" in user_info
        assert "home" in user_info
        assert "is_root" in user_info

    def test_detect_tools(self, analyzer):
        """Test tool detection."""
        # Only check python which should be available
        tools = analyzer.detect_tools(["python"])
        
        assert "python" in tools
        assert tools["python"].available is True

    def test_detect_tools_unavailable(self, analyzer):
        """Test detection of unavailable tool."""
        tools = analyzer.detect_tools(["nonexistent_tool_xyz"])
        
        assert "nonexistent_tool_xyz" in tools
        assert tools["nonexistent_tool_xyz"].available is False

    def test_check_services(self, analyzer):
        """Test service check returns dict."""
        services = analyzer.check_services()
        
        assert isinstance(services, dict)
        # Should have docker_daemon at minimum
        assert "docker_daemon" in services

    def test_find_config_files(self, analyzer):
        """Test config file finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "docker-compose.yml").write_text("version: '3'")
            (Path(tmpdir) / "test.py").write_text("print('test')")
            
            files = analyzer.find_config_files(
                Path(tmpdir),
                patterns=["docker-compose*.yml", "*.py"]
            )
            
            assert len(files) >= 1
            assert any("docker-compose" in f["name"] for f in files)

    def test_validate_command_basic(self, analyzer):
        """Test basic command validation."""
        result = analyzer.validate_command("echo hello", context={})
        
        assert "valid" in result
        assert "warnings" in result

    def test_validate_command_shell_builtin(self, analyzer):
        """Test shell builtin validation."""
        result = analyzer.validate_command("cd /tmp", context={})
        
        assert result["valid"] is True

    def test_validate_command_with_context(self, analyzer):
        """Test command validation with context."""
        context = {
            "available_tools": {"ls": True},
            "services": {},
        }
        result = analyzer.validate_command("ls -la", context)
        
        assert result["valid"] is True

    def test_full_report(self, analyzer):
        """Test full report generation."""
        report = analyzer.full_report()
        
        assert isinstance(report, EnvironmentReport)
        assert report.os_info is not None
        assert isinstance(report.tools, dict)
        assert isinstance(report.services, dict)


class TestEnvironmentReport:
    """Tests for EnvironmentReport dataclass."""

    def test_report_creation(self):
        """Test creating environment report."""
        report = EnvironmentReport(
            os_info={"system": "Linux"},
            tools={"python": ToolInfo(name="python", available=True)},
            services={"docker": ServiceInfo(name="docker", running=True)},
            config_files=[],
            resources={"disk": {"total_gb": 100}},
            recommendations=["Install docker"],
        )

        assert report.os_info["system"] == "Linux"
        assert "python" in report.tools
        assert len(report.recommendations) == 1


class TestRecommendations:
    """Tests for recommendation generation."""

    @pytest.fixture
    def analyzer(self):
        return EnvironmentAnalyzer()

    def test_recommendations_for_missing_docker(self, analyzer):
        """Test recommendations when Docker is missing."""
        tools = {
            "docker": ToolInfo(name="docker", available=False),
            "git": ToolInfo(name="git", available=True),
        }
        services = {}
        
        recommendations = analyzer._generate_recommendations(tools, services)
        
        assert any("docker" in r.lower() for r in recommendations)

    def test_recommendations_for_outdated_docker(self, analyzer):
        """Test recommendations for outdated Docker."""
        tools = {
            "docker": ToolInfo(name="docker", available=True, version="19.0.0"),
        }
        services = {}
        
        recommendations = analyzer._generate_recommendations(tools, services)
        
        assert any("outdated" in r.lower() for r in recommendations)

    def test_recommendations_for_stopped_docker(self, analyzer):
        """Test recommendations when Docker daemon is stopped."""
        tools = {
            "docker": ToolInfo(name="docker", available=True, version="24.0.0"),
        }
        services = {
            "docker_daemon": ServiceInfo(name="docker_daemon", running=False),
        }
        
        recommendations = analyzer._generate_recommendations(tools, services)
        
        assert any("daemon" in r.lower() for r in recommendations)

    def test_no_recommendations_when_all_good(self, analyzer):
        """Test no recommendations when everything is configured."""
        tools = {
            "docker": ToolInfo(name="docker", available=True, version="24.0.0"),
            "git": ToolInfo(name="git", available=True, version="2.40.0"),
        }
        services = {
            "docker_daemon": ServiceInfo(name="docker_daemon", running=True),
        }
        
        recommendations = analyzer._generate_recommendations(tools, services)
        
        # Should have minimal or no recommendations
        assert len(recommendations) <= 1
