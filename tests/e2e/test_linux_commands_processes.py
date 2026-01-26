"""
E2E tests for Linux process management commands.
Tests: htop, pgrep, pkill, killall, nice, renice, nohup, bg, fg, jobs
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestProcessManagementCommands:
    """Test process management commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== HTOP =====
    def test_htop_basic(self, detector):
        result = detector.detect_command("htop")
        assert result[0].command == "htop"

    def test_htop_interactive(self, detector):
        result = detector.detect_command("interactive process viewer")
        assert any(r.command == "htop" for r in result)

    def test_htop_polish(self, detector):
        result = detector.detect_command("monitor procesów")
        assert any(r.command == "htop" for r in result)

    # ===== PGREP =====
    def test_pgrep_basic(self, detector):
        result = detector.detect_command("pgrep python")
        assert result[0].command == "pgrep"

    def test_pgrep_find_process(self, detector):
        result = detector.detect_command("find process by name")
        assert any(r.command == "pgrep" for r in result)

    def test_pgrep_polish(self, detector):
        result = detector.detect_command("znajdź proces")
        assert any(r.command == "pgrep" for r in result)

    # ===== PKILL =====
    def test_pkill_basic(self, detector):
        result = detector.detect_command("pkill firefox")
        assert result[0].command == "pkill"

    def test_pkill_by_name(self, detector):
        result = detector.detect_command("kill process by name")
        assert any(r.command == "pkill" for r in result)

    def test_pkill_polish(self, detector):
        result = detector.detect_command("zabij proces po nazwie")
        assert any(r.command == "pkill" for r in result)

    # ===== KILLALL =====
    def test_killall_basic(self, detector):
        result = detector.detect_command("killall chrome")
        assert result[0].command == "killall"

    def test_killall_all_processes(self, detector):
        result = detector.detect_command("kill all processes named")
        assert any(r.command == "killall" for r in result)

    def test_killall_polish(self, detector):
        result = detector.detect_command("zabij wszystkie procesy")
        assert any(r.command == "killall" for r in result)

    # ===== NICE =====
    def test_nice_basic(self, detector):
        result = detector.detect_command("nice -n 10 command")
        assert result[0].command == "nice"

    def test_nice_priority(self, detector):
        result = detector.detect_command("run with low priority")
        assert any(r.command == "nice" for r in result)

    def test_nice_polish(self, detector):
        result = detector.detect_command("uruchom z priorytetem")
        assert any(r.command == "nice" for r in result)

    # ===== RENICE =====
    def test_renice_basic(self, detector):
        result = detector.detect_command("renice -n 5 -p 1234")
        assert result[0].command == "renice"

    def test_renice_change_priority(self, detector):
        result = detector.detect_command("change process priority")
        assert any(r.command == "renice" for r in result)

    def test_renice_polish(self, detector):
        result = detector.detect_command("zmień priorytet procesu")
        assert any(r.command == "renice" for r in result)

    # ===== NOHUP =====
    def test_nohup_basic(self, detector):
        result = detector.detect_command("nohup script.sh &")
        assert result[0].command == "nohup"

    def test_nohup_background(self, detector):
        result = detector.detect_command("run in background ignore hangup")
        assert any(r.command == "nohup" for r in result)

    def test_nohup_polish(self, detector):
        result = detector.detect_command("uruchom w tle")
        assert any(r.command == "nohup" for r in result)

    # ===== BG =====
    def test_bg_basic(self, detector):
        result = detector.detect_command("bg %1")
        assert result[0].command == "bg"

    def test_bg_background_job(self, detector):
        result = detector.detect_command("resume job in background")
        assert any(r.command == "bg" for r in result)

    # ===== FG =====
    def test_fg_basic(self, detector):
        result = detector.detect_command("fg %1")
        assert result[0].command == "fg"

    def test_fg_foreground_job(self, detector):
        result = detector.detect_command("bring job to foreground")
        assert any(r.command == "fg" for r in result)

    def test_fg_polish(self, detector):
        result = detector.detect_command("przenieś na pierwszy plan")
        assert any(r.command == "fg" for r in result)

    # ===== JOBS =====
    def test_jobs_basic(self, detector):
        result = detector.detect_command("jobs")
        assert result[0].command == "jobs"

    def test_jobs_list(self, detector):
        result = detector.detect_command("list background jobs")
        assert any(r.command == "jobs" for r in result)

    def test_jobs_polish(self, detector):
        result = detector.detect_command("pokaż zadania w tle")
        assert any(r.command == "jobs" for r in result)
