"""
E2E tests for Linux hardware info commands.
Tests: lscpu, lspci, lsusb, lshw, dmidecode, hdparm, smartctl, lsblk, blkid, fdisk
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestHardwareInfoCommands:
    """Test hardware info commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== LSCPU =====
    def test_lscpu_basic(self, detector):
        result = detector.detect_command("lscpu")
        assert result[0].command == "lscpu"

    def test_lscpu_cpu_info(self, detector):
        result = detector.detect_command("cpu info lscpu")
        assert any(r.command == "lscpu" for r in result)

    def test_lscpu_polish(self, detector):
        result = detector.detect_command("info o procesorze lscpu")
        assert any(r.command == "lscpu" for r in result)

    # ===== LSPCI =====
    def test_lspci_basic(self, detector):
        result = detector.detect_command("lspci")
        assert result[0].command == "lspci"

    def test_lspci_pci(self, detector):
        result = detector.detect_command("pci devices lspci")
        assert any(r.command == "lspci" for r in result)

    def test_lspci_polish(self, detector):
        result = detector.detect_command("urządzenia pci lspci")
        assert any(r.command == "lspci" for r in result)

    # ===== LSUSB =====
    def test_lsusb_basic(self, detector):
        result = detector.detect_command("lsusb")
        assert result[0].command == "lsusb"

    def test_lsusb_usb(self, detector):
        result = detector.detect_command("usb devices lsusb")
        assert any(r.command == "lsusb" for r in result)

    def test_lsusb_polish(self, detector):
        result = detector.detect_command("urządzenia usb lsusb")
        assert any(r.command == "lsusb" for r in result)

    # ===== LSHW =====
    def test_lshw_basic(self, detector):
        result = detector.detect_command("lshw")
        assert result[0].command == "lshw"

    def test_lshw_hardware(self, detector):
        result = detector.detect_command("hardware info lshw")
        assert any(r.command == "lshw" for r in result)

    def test_lshw_polish(self, detector):
        result = detector.detect_command("info o sprzęcie lshw")
        assert any(r.command == "lshw" for r in result)

    # ===== DMIDECODE =====
    def test_dmidecode_basic(self, detector):
        result = detector.detect_command("dmidecode")
        assert result[0].command == "dmidecode"

    def test_dmidecode_bios(self, detector):
        result = detector.detect_command("bios info dmidecode")
        assert any(r.command == "dmidecode" for r in result)

    def test_dmidecode_dmi(self, detector):
        result = detector.detect_command("dmi table dmidecode")
        assert any(r.command == "dmidecode" for r in result)

    # ===== HDPARM =====
    def test_hdparm_basic(self, detector):
        result = detector.detect_command("hdparm -I /dev/sda")
        assert result[0].command == "hdparm"

    def test_hdparm_disk(self, detector):
        result = detector.detect_command("disk parameters hdparm")
        assert any(r.command == "hdparm" for r in result)

    def test_hdparm_polish(self, detector):
        result = detector.detect_command("parametry dysku hdparm")
        assert any(r.command == "hdparm" for r in result)

    # ===== SMARTCTL =====
    def test_smartctl_basic(self, detector):
        result = detector.detect_command("smartctl -a /dev/sda")
        assert result[0].command == "smartctl"

    def test_smartctl_health(self, detector):
        result = detector.detect_command("disk health smartctl")
        assert any(r.command == "smartctl" for r in result)

    def test_smartctl_polish(self, detector):
        result = detector.detect_command("zdrowie dysku smart")
        assert any(r.command == "smartctl" for r in result)

    # ===== LSBLK =====
    def test_lsblk_basic(self, detector):
        result = detector.detect_command("lsblk")
        assert result[0].command == "lsblk"

    def test_lsblk_disks(self, detector):
        result = detector.detect_command("list disks lsblk")
        assert any(r.command == "lsblk" for r in result)

    def test_lsblk_polish(self, detector):
        result = detector.detect_command("lista dysków lsblk")
        assert any(r.command == "lsblk" for r in result)

    # ===== BLKID =====
    def test_blkid_basic(self, detector):
        result = detector.detect_command("blkid")
        assert result[0].command == "blkid"

    def test_blkid_uuid(self, detector):
        result = detector.detect_command("disk uuid blkid")
        assert any(r.command == "blkid" for r in result)

    # ===== FDISK =====
    def test_fdisk_basic(self, detector):
        result = detector.detect_command("fdisk -l")
        assert result[0].command == "fdisk"

    def test_fdisk_partition(self, detector):
        result = detector.detect_command("partition table fdisk")
        assert any(r.command == "fdisk" for r in result)

    def test_fdisk_polish(self, detector):
        result = detector.detect_command("partycje dysku fdisk")
        assert any(r.command == "fdisk" for r in result)
