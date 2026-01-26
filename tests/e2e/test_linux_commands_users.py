"""
E2E tests for Linux user management commands.
Tests: whoami, who, w, last, id, groups, useradd, userdel, passwd, sudo
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestUserManagementCommands:
    """Test user management commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== WHOAMI =====
    def test_whoami_basic(self, detector):
        result = detector.detect_command("whoami")
        assert result[0].command == "whoami"

    def test_whoami_current_user(self, detector):
        result = detector.detect_command("who am i")
        assert any(r.command == "whoami" for r in result)

    def test_whoami_polish(self, detector):
        result = detector.detect_command("kim jestem")
        assert any(r.command == "whoami" for r in result)

    # ===== WHO =====
    def test_who_basic(self, detector):
        result = detector.detect_command("who")
        assert result[0].command == "who"

    def test_who_logged(self, detector):
        result = detector.detect_command("logged in users")
        assert any(r.command == "who" for r in result)

    def test_who_polish(self, detector):
        result = detector.detect_command("zalogowani użytkownicy")
        assert any(r.command == "who" for r in result)

    # ===== W =====
    def test_w_basic(self, detector):
        result = detector.detect_command("w command")
        assert result[0].command == "w"

    def test_w_activity(self, detector):
        result = detector.detect_command("user activity status")
        assert any(r.command == "w" for r in result)

    def test_w_polish(self, detector):
        result = detector.detect_command("co robią użytkownicy")
        assert any(r.command == "w" for r in result)

    # ===== LAST =====
    def test_last_basic(self, detector):
        result = detector.detect_command("last")
        assert result[0].command == "last"

    def test_last_login_history(self, detector):
        result = detector.detect_command("login history")
        assert any(r.command == "last" for r in result)

    def test_last_polish(self, detector):
        result = detector.detect_command("historia logowań")
        assert any(r.command == "last" for r in result)

    # ===== ID =====
    def test_id_basic(self, detector):
        result = detector.detect_command("id")
        assert result[0].command == "id"

    def test_id_user(self, detector):
        result = detector.detect_command("user id and groups")
        assert any(r.command == "id" for r in result)

    def test_id_polish(self, detector):
        result = detector.detect_command("identyfikator użytkownika")
        assert any(r.command == "id" for r in result)

    # ===== GROUPS =====
    def test_groups_basic(self, detector):
        result = detector.detect_command("groups")
        assert result[0].command == "groups"

    def test_groups_user(self, detector):
        result = detector.detect_command("user groups")
        assert any(r.command == "groups" for r in result)

    def test_groups_polish(self, detector):
        result = detector.detect_command("grupy użytkownika")
        assert any(r.command == "groups" for r in result)

    # ===== USERADD =====
    def test_useradd_basic(self, detector):
        result = detector.detect_command("useradd newuser")
        assert result[0].command == "useradd"

    def test_useradd_create(self, detector):
        result = detector.detect_command("create new user account")
        assert any(r.command == "useradd" for r in result)

    def test_useradd_polish(self, detector):
        result = detector.detect_command("dodaj użytkownika")
        assert any(r.command == "useradd" for r in result)

    # ===== USERDEL =====
    def test_userdel_basic(self, detector):
        result = detector.detect_command("userdel olduser")
        assert result[0].command == "userdel"

    def test_userdel_delete(self, detector):
        result = detector.detect_command("delete user account")
        assert any(r.command == "userdel" for r in result)

    def test_userdel_polish(self, detector):
        result = detector.detect_command("usuń użytkownika")
        assert any(r.command == "userdel" for r in result)

    # ===== PASSWD =====
    def test_passwd_basic(self, detector):
        result = detector.detect_command("passwd")
        assert result[0].command == "passwd"

    def test_passwd_change(self, detector):
        result = detector.detect_command("change user password")
        assert any(r.command == "passwd" for r in result)

    def test_passwd_polish(self, detector):
        result = detector.detect_command("zmień hasło użytkownika")
        assert any(r.command == "passwd" for r in result)

    # ===== SUDO =====
    def test_sudo_basic(self, detector):
        result = detector.detect_command("sudo command")
        assert result[0].command == "sudo"

    def test_sudo_root(self, detector):
        result = detector.detect_command("run as superuser")
        assert any(r.command == "sudo" for r in result)

    def test_sudo_polish(self, detector):
        result = detector.detect_command("uruchom jako administrator")
        assert any(r.command == "sudo" for r in result)
