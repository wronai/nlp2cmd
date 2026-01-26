"""
E2E tests for Linux system monitoring commands.
Tests: vmstat, iostat, sar, mpstat, dmesg, journalctl, systemctl, crontab, at, watch
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestSystemMonitoringCommands:
    """Test system monitoring commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== VMSTAT =====
    def test_vmstat_basic(self, detector):
        result = detector.detect_command("vmstat 1")
        assert result[0].command == "vmstat"

    def test_vmstat_memory(self, detector):
        result = detector.detect_command("virtual memory statistics")
        assert any(r.command == "vmstat" for r in result)

    def test_vmstat_polish(self, detector):
        result = detector.detect_command("statystyki pamięci wirtualnej")
        assert any(r.command == "vmstat" for r in result)

    # ===== IOSTAT =====
    def test_iostat_basic(self, detector):
        result = detector.detect_command("iostat -x 1")
        assert result[0].command == "iostat"

    def test_iostat_io(self, detector):
        result = detector.detect_command("io statistics")
        assert any(r.command == "iostat" for r in result)

    def test_iostat_disk_io(self, detector):
        result = detector.detect_command("disk io performance")
        assert any(r.command == "iostat" for r in result)

    # ===== SAR =====
    def test_sar_basic(self, detector):
        result = detector.detect_command("sar 1 5")
        assert result[0].command == "sar"

    def test_sar_activity(self, detector):
        result = detector.detect_command("system activity report")
        assert any(r.command == "sar" for r in result)

    def test_sar_polish(self, detector):
        result = detector.detect_command("raport aktywności systemu")
        assert any(r.command == "sar" for r in result)

    # ===== MPSTAT =====
    def test_mpstat_basic(self, detector):
        result = detector.detect_command("mpstat -P ALL 1")
        assert result[0].command == "mpstat"

    def test_mpstat_cpu(self, detector):
        result = detector.detect_command("cpu statistics per processor")
        assert any(r.command == "mpstat" for r in result)

    def test_mpstat_polish(self, detector):
        result = detector.detect_command("statystyki cpu")
        assert any(r.command == "mpstat" for r in result)

    # ===== DMESG =====
    def test_dmesg_basic(self, detector):
        result = detector.detect_command("dmesg")
        assert result[0].command == "dmesg"

    def test_dmesg_kernel(self, detector):
        result = detector.detect_command("kernel messages")
        assert any(r.command == "dmesg" for r in result)

    def test_dmesg_polish(self, detector):
        result = detector.detect_command("logi kernela")
        assert any(r.command == "dmesg" for r in result)

    # ===== JOURNALCTL =====
    def test_journalctl_basic(self, detector):
        result = detector.detect_command("journalctl -f")
        assert result[0].command == "journalctl"

    def test_journalctl_systemd(self, detector):
        result = detector.detect_command("systemd logs")
        assert any(r.command == "journalctl" for r in result)

    def test_journalctl_polish(self, detector):
        result = detector.detect_command("logi systemd")
        assert any(r.command == "journalctl" for r in result)

    # ===== SYSTEMCTL =====
    def test_systemctl_basic(self, detector):
        result = detector.detect_command("systemctl status nginx")
        assert result[0].command == "systemctl"

    def test_systemctl_service(self, detector):
        result = detector.detect_command("manage systemd service")
        assert any(r.command == "systemctl" for r in result)

    def test_systemctl_polish(self, detector):
        result = detector.detect_command("zarządzaj usługami systemowymi")
        assert any(r.command == "systemctl" for r in result)

    # ===== CRONTAB =====
    def test_crontab_basic(self, detector):
        result = detector.detect_command("crontab -l")
        assert result[0].command == "crontab"

    def test_crontab_schedule(self, detector):
        result = detector.detect_command("scheduled cron tasks")
        assert any(r.command == "crontab" for r in result)

    def test_crontab_polish(self, detector):
        result = detector.detect_command("harmonogram zadań cron")
        assert any(r.command == "crontab" for r in result)

    # ===== AT =====
    def test_at_basic(self, detector):
        result = detector.detect_command("at 10:00")
        assert result[0].command == "at"

    def test_at_schedule_once(self, detector):
        result = detector.detect_command("schedule command once")
        assert any(r.command == "at" for r in result)

    def test_at_polish(self, detector):
        result = detector.detect_command("zaplanuj jednorazowo")
        assert any(r.command == "at" for r in result)

    # ===== WATCH =====
    def test_watch_basic(self, detector):
        result = detector.detect_command("watch -n 2 'df -h'")
        assert result[0].command == "watch"

    def test_watch_monitor(self, detector):
        result = detector.detect_command("monitor command output")
        assert any(r.command == "watch" for r in result)

    def test_watch_polish(self, detector):
        result = detector.detect_command("obserwuj wynik komendy")
        assert any(r.command == "watch" for r in result)
