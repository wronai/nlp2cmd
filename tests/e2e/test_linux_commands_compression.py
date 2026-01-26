"""
E2E tests for Linux compression commands.
Tests: gzip, gunzip, bzip2, xz, 7z, rar, rsync, dd, tar, zip
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestCompressionCommands:
    """Test compression commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== GZIP =====
    def test_gzip_basic(self, detector):
        result = detector.detect_command("gzip largefile.txt")
        assert result[0].command == "gzip"

    def test_gzip_compress(self, detector):
        result = detector.detect_command("compress file with gzip")
        assert any(r.command == "gzip" for r in result)

    def test_gzip_polish(self, detector):
        result = detector.detect_command("kompresuj plik gzip")
        assert any(r.command == "gzip" for r in result)

    # ===== GUNZIP =====
    def test_gunzip_basic(self, detector):
        result = detector.detect_command("gunzip file.gz")
        assert result[0].command == "gunzip"

    def test_gunzip_extract(self, detector):
        result = detector.detect_command("extract gz file")
        assert any(r.command == "gunzip" for r in result)

    def test_gunzip_decompress(self, detector):
        result = detector.detect_command("decompress gzip file")
        assert any(r.command == "gunzip" for r in result)

    # ===== BZIP2 =====
    def test_bzip2_basic(self, detector):
        result = detector.detect_command("bzip2 data.txt")
        assert result[0].command == "bzip2"

    def test_bzip2_compress(self, detector):
        result = detector.detect_command("compress with bzip")
        assert any(r.command == "bzip2" for r in result)

    # ===== XZ =====
    def test_xz_basic(self, detector):
        result = detector.detect_command("xz archive.tar")
        assert result[0].command == "xz"

    def test_xz_compress(self, detector):
        result = detector.detect_command("compress xz format")
        assert any(r.command == "xz" for r in result)

    def test_xz_lzma(self, detector):
        result = detector.detect_command("lzma compression")
        assert any(r.command == "xz" for r in result)

    # ===== 7Z =====
    def test_7z_basic(self, detector):
        result = detector.detect_command("7z a archive.7z files")
        assert result[0].command == "7z"

    def test_7z_compress(self, detector):
        result = detector.detect_command("compress with 7zip")
        assert any(r.command == "7z" for r in result)

    # ===== RAR =====
    def test_rar_basic(self, detector):
        result = detector.detect_command("rar a archive.rar files")
        assert result[0].command == "rar"

    def test_unrar_basic(self, detector):
        result = detector.detect_command("unrar x archive.rar")
        assert any(r.command == "rar" for r in result)

    # ===== RSYNC =====
    def test_rsync_basic(self, detector):
        result = detector.detect_command("rsync -av source/ dest/")
        assert result[0].command == "rsync"

    def test_rsync_sync(self, detector):
        result = detector.detect_command("sync folders")
        assert any(r.command == "rsync" for r in result)

    def test_rsync_backup(self, detector):
        result = detector.detect_command("backup directory with rsync")
        assert any(r.command == "rsync" for r in result)

    def test_rsync_polish(self, detector):
        result = detector.detect_command("synchronizuj katalogi")
        assert any(r.command == "rsync" for r in result)

    # ===== DD =====
    def test_dd_basic(self, detector):
        result = detector.detect_command("dd if=/dev/sda of=disk.img")
        assert result[0].command == "dd"

    def test_dd_disk_image(self, detector):
        result = detector.detect_command("create disk image")
        assert any(r.command == "dd" for r in result)

    def test_dd_clone(self, detector):
        result = detector.detect_command("clone disk")
        assert any(r.command == "dd" for r in result)

    # ===== TAR =====
    def test_tar_basic(self, detector):
        result = detector.detect_command("tar -czvf archive.tar.gz files/")
        assert result[0].command == "tar"

    def test_tar_compress(self, detector):
        result = detector.detect_command("create tar archive")
        assert any(r.command == "tar" for r in result)

    def test_tar_extract(self, detector):
        result = detector.detect_command("extract tar file")
        assert any(r.command == "tar" for r in result)

    # ===== ZIP =====
    def test_zip_basic(self, detector):
        result = detector.detect_command("zip archive.zip files")
        assert result[0].command == "zip"

    def test_zip_compress(self, detector):
        result = detector.detect_command("create zip archive")
        assert any(r.command == "zip" for r in result)

    def test_unzip_basic(self, detector):
        result = detector.detect_command("unzip archive.zip")
        assert result[0].command == "unzip"
