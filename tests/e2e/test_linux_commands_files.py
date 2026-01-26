"""
E2E tests for Linux file operation commands.
Tests: touch, ln, stat, chmod, chown, tree, rmdir, which, whereis, locate
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestFileOperationCommands:
    """Test file operation commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== TOUCH =====
    def test_touch_basic(self, detector):
        result = detector.detect_command("touch newfile.txt")
        assert result[0].command == "touch"

    def test_touch_create_file(self, detector):
        result = detector.detect_command("create new file")
        assert any(r.command == "touch" for r in result)

    def test_touch_polish(self, detector):
        result = detector.detect_command("utwórz nowy plik")
        assert any(r.command == "touch" for r in result)

    # ===== LN =====
    def test_ln_basic(self, detector):
        result = detector.detect_command("ln -s source target")
        assert result[0].command == "ln"

    def test_ln_symlink(self, detector):
        result = detector.detect_command("create symbolic link")
        assert any(r.command == "ln" for r in result)

    def test_ln_polish(self, detector):
        result = detector.detect_command("utwórz dowiązanie symboliczne")
        assert any(r.command == "ln" for r in result)

    # ===== STAT =====
    def test_stat_basic(self, detector):
        result = detector.detect_command("stat file.txt")
        assert result[0].command == "stat"

    def test_stat_file_info(self, detector):
        result = detector.detect_command("show file info")
        assert any(r.command == "stat" for r in result)

    def test_stat_metadata(self, detector):
        result = detector.detect_command("file metadata details")
        assert any(r.command == "stat" for r in result)

    # ===== CHMOD =====
    def test_chmod_basic(self, detector):
        result = detector.detect_command("chmod 755 script.sh")
        assert result[0].command == "chmod"

    def test_chmod_permissions(self, detector):
        result = detector.detect_command("change file permissions")
        assert any(r.command == "chmod" for r in result)

    def test_chmod_executable(self, detector):
        result = detector.detect_command("make file executable")
        assert any(r.command == "chmod" for r in result)

    def test_chmod_polish(self, detector):
        result = detector.detect_command("zmień uprawnienia pliku")
        assert any(r.command == "chmod" for r in result)

    # ===== CHOWN =====
    def test_chown_basic(self, detector):
        result = detector.detect_command("chown user:group file")
        assert result[0].command == "chown"

    def test_chown_owner(self, detector):
        result = detector.detect_command("change file owner")
        assert any(r.command == "chown" for r in result)

    def test_chown_polish(self, detector):
        result = detector.detect_command("zmień właściciela pliku")
        assert any(r.command == "chown" for r in result)

    # ===== TREE =====
    def test_tree_basic(self, detector):
        result = detector.detect_command("tree /home")
        assert result[0].command == "tree"

    def test_tree_directory(self, detector):
        result = detector.detect_command("show directory tree")
        assert any(r.command == "tree" for r in result)

    def test_tree_polish(self, detector):
        result = detector.detect_command("pokaż drzewo katalogów")
        assert any(r.command == "tree" for r in result)

    # ===== RMDIR =====
    def test_rmdir_basic(self, detector):
        result = detector.detect_command("rmdir empty_folder")
        assert result[0].command == "rmdir"

    def test_rmdir_remove(self, detector):
        result = detector.detect_command("remove empty directory")
        assert any(r.command == "rmdir" for r in result)

    def test_rmdir_polish(self, detector):
        result = detector.detect_command("usuń pusty katalog")
        assert any(r.command == "rmdir" for r in result)

    # ===== WHICH =====
    def test_which_basic(self, detector):
        result = detector.detect_command("which python")
        assert result[0].command == "which"

    def test_which_locate_command(self, detector):
        result = detector.detect_command("locate command path")
        assert any(r.command == "which" for r in result)

    def test_which_polish(self, detector):
        result = detector.detect_command("znajdź ścieżkę komendy")
        assert any(r.command == "which" for r in result)

    # ===== WHEREIS =====
    def test_whereis_basic(self, detector):
        result = detector.detect_command("whereis bash")
        assert result[0].command == "whereis"

    def test_whereis_binary(self, detector):
        result = detector.detect_command("locate binary and man page")
        assert any(r.command == "whereis" for r in result)

    def test_whereis_polish(self, detector):
        result = detector.detect_command("znajdź program")
        assert any(r.command == "whereis" for r in result)

    # ===== LOCATE =====
    def test_locate_basic(self, detector):
        result = detector.detect_command("locate config.conf")
        assert result[0].command == "locate"

    def test_locate_find_fast(self, detector):
        result = detector.detect_command("find file fast using database")
        assert any(r.command == "locate" for r in result)

    def test_locate_polish(self, detector):
        result = detector.detect_command("szybkie szukanie pliku")
        assert any(r.command == "locate" for r in result)
