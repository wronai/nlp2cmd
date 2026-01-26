"""
E2E tests for Linux miscellaneous commands.
Tests: screen, tmux, nano, vim, sed, jq, md5sum, sha256sum, base64, gdb
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestMiscellaneousCommands:
    """Test miscellaneous commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== SCREEN =====
    def test_screen_basic(self, detector):
        result = detector.detect_command("screen -S session")
        assert result[0].command == "screen"

    def test_screen_session(self, detector):
        result = detector.detect_command("screen session terminal")
        assert any(r.command == "screen" for r in result)

    def test_screen_polish(self, detector):
        result = detector.detect_command("nowa sesja screen")
        assert any(r.command == "screen" for r in result)

    # ===== TMUX =====
    def test_tmux_basic(self, detector):
        result = detector.detect_command("tmux new -s dev")
        assert result[0].command == "tmux"

    def test_tmux_session(self, detector):
        result = detector.detect_command("tmux session terminal")
        assert any(r.command == "tmux" for r in result)

    def test_tmux_polish(self, detector):
        result = detector.detect_command("sesja tmux")
        assert any(r.command == "tmux" for r in result)

    # ===== NANO =====
    def test_nano_basic(self, detector):
        result = detector.detect_command("nano file.txt")
        assert result[0].command == "nano"

    def test_nano_editor(self, detector):
        result = detector.detect_command("nano text editor")
        assert any(r.command == "nano" for r in result)

    def test_nano_polish(self, detector):
        result = detector.detect_command("edytor nano")
        assert any(r.command == "nano" for r in result)

    # ===== VIM =====
    def test_vim_basic(self, detector):
        result = detector.detect_command("vim config.py")
        assert result[0].command == "vim"

    def test_vim_editor(self, detector):
        result = detector.detect_command("vim editor")
        assert any(r.command == "vim" for r in result)

    def test_vim_polish(self, detector):
        result = detector.detect_command("edytor vim")
        assert any(r.command == "vim" for r in result)

    # ===== SED =====
    def test_sed_basic(self, detector):
        result = detector.detect_command("sed 's/old/new/g' file")
        assert result[0].command == "sed"

    def test_sed_replace(self, detector):
        result = detector.detect_command("sed replace text")
        assert any(r.command == "sed" for r in result)

    def test_sed_polish(self, detector):
        result = detector.detect_command("zamień tekst sed")
        assert any(r.command == "sed" for r in result)

    # ===== JQ =====
    def test_jq_basic(self, detector):
        result = detector.detect_command("jq '.key' file.json")
        assert result[0].command == "jq"

    def test_jq_parse(self, detector):
        result = detector.detect_command("jq parse json")
        assert any(r.command == "jq" for r in result)

    def test_jq_polish(self, detector):
        result = detector.detect_command("parsuj json jq")
        assert any(r.command == "jq" for r in result)

    # ===== MD5SUM =====
    def test_md5sum_basic(self, detector):
        result = detector.detect_command("md5sum file.iso")
        assert result[0].command == "md5sum"

    def test_md5sum_checksum(self, detector):
        result = detector.detect_command("md5 checksum")
        assert any(r.command == "md5sum" for r in result)

    def test_md5sum_polish(self, detector):
        result = detector.detect_command("suma kontrolna md5")
        assert any(r.command == "md5sum" for r in result)

    # ===== SHA256SUM =====
    def test_sha256sum_basic(self, detector):
        result = detector.detect_command("sha256sum file.iso")
        assert result[0].command == "sha256sum"

    def test_sha256sum_hash(self, detector):
        result = detector.detect_command("sha256 hash checksum")
        assert any(r.command == "sha256sum" for r in result)

    # ===== BASE64 =====
    def test_base64_basic(self, detector):
        result = detector.detect_command("base64 file.txt")
        assert result[0].command == "base64"

    def test_base64_encode(self, detector):
        result = detector.detect_command("base64 encode")
        assert any(r.command == "base64" for r in result)

    def test_base64_polish(self, detector):
        result = detector.detect_command("koduj base64")
        assert any(r.command == "base64" for r in result)

    # ===== GDB =====
    def test_gdb_basic(self, detector):
        result = detector.detect_command("gdb program")
        assert result[0].command == "gdb"

    def test_gdb_debugger(self, detector):
        result = detector.detect_command("gdb debugger")
        assert any(r.command == "gdb" for r in result)

    def test_gdb_polish(self, detector):
        result = detector.detect_command("debuguj gdb")
        assert any(r.command == "gdb" for r in result)
