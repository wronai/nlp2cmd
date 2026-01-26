"""
E2E tests for Linux network commands.
Tests: ip, ifconfig, iptables, ufw, traceroute, nslookup, dig, nmap, tcpdump, arp
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestNetworkCommands:
    """Test network commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== IP =====
    def test_ip_basic(self, detector):
        result = detector.detect_command("ip addr")
        assert result[0].command == "ip"

    def test_ip_address(self, detector):
        result = detector.detect_command("show ip address")
        assert any(r.command == "ip" for r in result)

    def test_ip_polish(self, detector):
        result = detector.detect_command("pokaż adres ip")
        assert any(r.command == "ip" for r in result)

    # ===== IFCONFIG =====
    def test_ifconfig_basic(self, detector):
        result = detector.detect_command("ifconfig")
        assert result[0].command == "ifconfig"

    def test_ifconfig_interface(self, detector):
        result = detector.detect_command("interface configuration")
        assert any(r.command == "ifconfig" for r in result)

    def test_ifconfig_polish(self, detector):
        result = detector.detect_command("konfiguracja interfejsu sieciowego")
        assert any(r.command == "ifconfig" for r in result)

    # ===== IPTABLES =====
    def test_iptables_basic(self, detector):
        result = detector.detect_command("iptables -L")
        assert result[0].command == "iptables"

    def test_iptables_firewall(self, detector):
        result = detector.detect_command("firewall rules iptables")
        assert any(r.command == "iptables" for r in result)

    def test_iptables_polish(self, detector):
        result = detector.detect_command("reguły zapory iptables")
        assert any(r.command == "iptables" for r in result)

    # ===== UFW =====
    def test_ufw_basic(self, detector):
        result = detector.detect_command("ufw status")
        assert result[0].command == "ufw"

    def test_ufw_firewall(self, detector):
        result = detector.detect_command("uncomplicated firewall")
        assert any(r.command == "ufw" for r in result)

    def test_ufw_polish(self, detector):
        result = detector.detect_command("prosty firewall ufw")
        assert any(r.command == "ufw" for r in result)

    # ===== TRACEROUTE =====
    def test_traceroute_basic(self, detector):
        result = detector.detect_command("traceroute google.com")
        assert result[0].command == "traceroute"

    def test_traceroute_path(self, detector):
        result = detector.detect_command("trace network path")
        assert any(r.command == "traceroute" for r in result)

    def test_traceroute_polish(self, detector):
        result = detector.detect_command("śledź trasę sieciową")
        assert any(r.command == "traceroute" for r in result)

    # ===== NSLOOKUP =====
    def test_nslookup_basic(self, detector):
        result = detector.detect_command("nslookup example.com")
        assert result[0].command == "nslookup"

    def test_nslookup_dns(self, detector):
        result = detector.detect_command("dns lookup nslookup")
        assert any(r.command == "nslookup" for r in result)

    def test_nslookup_resolve(self, detector):
        result = detector.detect_command("resolve domain name")
        assert any(r.command == "nslookup" for r in result)

    # ===== DIG =====
    def test_dig_basic(self, detector):
        result = detector.detect_command("dig example.com")
        assert result[0].command == "dig"

    def test_dig_dns_query(self, detector):
        result = detector.detect_command("dns query dig")
        assert any(r.command == "dig" for r in result)

    def test_dig_polish(self, detector):
        result = detector.detect_command("zapytanie dns dig")
        assert any(r.command == "dig" for r in result)

    # ===== NMAP =====
    def test_nmap_basic(self, detector):
        result = detector.detect_command("nmap 192.168.1.1")
        assert result[0].command == "nmap"

    def test_nmap_scan(self, detector):
        result = detector.detect_command("port scanner nmap")
        assert any(r.command == "nmap" for r in result)

    def test_nmap_polish(self, detector):
        result = detector.detect_command("skanuj porty nmap")
        assert any(r.command == "nmap" for r in result)

    # ===== TCPDUMP =====
    def test_tcpdump_basic(self, detector):
        result = detector.detect_command("tcpdump -i eth0")
        assert result[0].command == "tcpdump"

    def test_tcpdump_capture(self, detector):
        result = detector.detect_command("packet capture tcpdump")
        assert any(r.command == "tcpdump" for r in result)

    def test_tcpdump_polish(self, detector):
        result = detector.detect_command("przechwytuj pakiety tcpdump")
        assert any(r.command == "tcpdump" for r in result)

    # ===== ARP =====
    def test_arp_basic(self, detector):
        result = detector.detect_command("arp -a")
        assert result[0].command == "arp"

    def test_arp_table(self, detector):
        result = detector.detect_command("arp table")
        assert any(r.command == "arp" for r in result)

    def test_arp_polish(self, detector):
        result = detector.detect_command("tablica arp")
        assert any(r.command == "arp" for r in result)
