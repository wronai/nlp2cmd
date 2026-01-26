"""
E2E tests for Linux package management commands.
Tests: apt, dpkg, yum, dnf, pacman, snap, flatpak, pip, pip3, virtualenv
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestPackageManagementCommands:
    """Test package management commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== APT =====
    def test_apt_basic(self, detector):
        result = detector.detect_command("apt install nginx")
        assert result[0].command == "apt"

    def test_apt_update(self, detector):
        result = detector.detect_command("apt update packages")
        assert any(r.command == "apt" for r in result)

    def test_apt_polish(self, detector):
        result = detector.detect_command("zainstaluj pakiet apt")
        assert any(r.command == "apt" for r in result)

    # ===== DPKG =====
    def test_dpkg_basic(self, detector):
        result = detector.detect_command("dpkg -i package.deb")
        assert result[0].command == "dpkg"

    def test_dpkg_debian(self, detector):
        result = detector.detect_command("debian package dpkg")
        assert any(r.command == "dpkg" for r in result)

    def test_dpkg_polish(self, detector):
        result = detector.detect_command("zainstaluj pakiet deb")
        assert any(r.command == "dpkg" for r in result)

    # ===== YUM =====
    def test_yum_basic(self, detector):
        result = detector.detect_command("yum install httpd")
        assert result[0].command == "yum"

    def test_yum_rpm(self, detector):
        result = detector.detect_command("yum package manager")
        assert any(r.command == "yum" for r in result)

    # ===== DNF =====
    def test_dnf_basic(self, detector):
        result = detector.detect_command("dnf install vim")
        assert result[0].command == "dnf"

    def test_dnf_fedora(self, detector):
        result = detector.detect_command("dnf package fedora")
        assert any(r.command == "dnf" for r in result)

    # ===== PACMAN =====
    def test_pacman_basic(self, detector):
        result = detector.detect_command("pacman -S firefox")
        assert result[0].command == "pacman"

    def test_pacman_arch(self, detector):
        result = detector.detect_command("arch linux pacman")
        assert any(r.command == "pacman" for r in result)

    # ===== SNAP =====
    def test_snap_basic(self, detector):
        result = detector.detect_command("snap install vscode")
        assert result[0].command == "snap"

    def test_snap_install(self, detector):
        result = detector.detect_command("install snap package")
        assert any(r.command == "snap" for r in result)

    # ===== FLATPAK =====
    def test_flatpak_basic(self, detector):
        result = detector.detect_command("flatpak install gimp")
        assert result[0].command == "flatpak"

    def test_flatpak_install(self, detector):
        result = detector.detect_command("install flatpak app")
        assert any(r.command == "flatpak" for r in result)

    # ===== PIP =====
    def test_pip_basic(self, detector):
        result = detector.detect_command("pip install requests")
        assert result[0].command == "pip"

    def test_pip_python(self, detector):
        result = detector.detect_command("python pip package")
        assert any(r.command == "pip" for r in result)

    def test_pip_polish(self, detector):
        result = detector.detect_command("zainstaluj pakiet pip python")
        assert any(r.command == "pip" for r in result)

    # ===== PIP3 =====
    def test_pip3_basic(self, detector):
        result = detector.detect_command("pip3 install django")
        assert result[0].command == "pip3"

    def test_pip3_python3(self, detector):
        result = detector.detect_command("python3 pip3 package")
        assert any(r.command == "pip3" for r in result)

    # ===== VIRTUALENV =====
    def test_virtualenv_basic(self, detector):
        result = detector.detect_command("virtualenv venv")
        assert result[0].command == "virtualenv"

    def test_virtualenv_create(self, detector):
        result = detector.detect_command("create virtual environment python")
        assert any(r.command == "virtualenv" for r in result)

    def test_virtualenv_polish(self, detector):
        result = detector.detect_command("utwórz środowisko wirtualne")
        assert any(r.command == "virtualenv" for r in result)
