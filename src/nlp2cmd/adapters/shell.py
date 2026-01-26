"""
Shell DSL Adapter for NLP2CMD.

Supports Bash, Zsh, Fish, and PowerShell.
"""

from __future__ import annotations

import re
import shlex
import shutil
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy


@dataclass
class ShellSafetyPolicy(SafetyPolicy):
    """Shell-specific safety policy."""

    blocked_commands: list[str] = field(
        default_factory=lambda: [
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            ":(){:|:&};:",  # fork bomb
            "chmod -R 777 /",
            "chown -R",
        ]
    )
    require_confirmation_for: list[str] = field(
        default_factory=lambda: [
            "rm",
            "rmdir",
            "kill",
            "killall",
            "shutdown",
            "reboot",
            "systemctl stop",
            "docker rm",
            "docker rmi",
        ]
    )
    allow_sudo: bool = False
    allow_pipe_to_shell: bool = False
    max_pipe_depth: int = 5
    sandbox_mode: bool = True
    allowed_directories: list[str] = field(default_factory=list)
    blocked_directories: list[str] = field(
        default_factory=lambda: ["/", "/etc", "/boot", "/root", "/sys", "/proc"]
    )


@dataclass
class EnvironmentContext:
    """System environment context."""

    os: str = "linux"
    distro: str = "ubuntu"
    shell: str = "bash"
    available_tools: list[str] = field(default_factory=list)
    environment_variables: dict[str, str] = field(default_factory=dict)


class ShellAdapter(BaseDSLAdapter):
    """
    Shell adapter supporting multiple shell types.

    Transforms natural language into shell commands with
    safety checks and environment awareness.
    """

    DSL_NAME = "shell"
    DSL_VERSION = "1.0"

    SHELL_TYPES = ["bash", "zsh", "fish", "powershell"]

    INTENTS = {
        "file_search": {
            "patterns": [
                "znajdź plik", "znajdź", "znajdz", "szukaj", "find", "search", "locate", 
                "show files", "list files", "pokaż pliki", "wyszukaj pliki", "listuj pliki",
                "znajdź pliki z rozszerzeniem", "znajdź pliki większe niż", "znajdź pliki zmodyfikowane",
                "pokaż zawartość pliku", "wyświetl plik", "cat plik", "odczytaj plik",
                "pokaż ostatnie linii pliku", "tail plik", "koniec pliku"
            ],
            "required_entities": ["target"],
            "optional_entities": ["filters", "scope"],
        },
        "file_operation": {
            "patterns": [
                "kopiuj", "przenieś", "usuń", "utwórz", "copy", "move", "delete", "create", "remove", "compress",
                "skopiuj plik", "przenieś plik", "usuń plik", "usuń wszystkie pliki", "utwórz katalog",
                "zmień nazwę pliku", "mv plik", "rename plik", "zmień nazwę", "zmień nazwę pliku na",
                "sprawdź rozmiar pliku", "rozmiar pliku", "du plik", "wielkość pliku"
            ],
            "required_entities": ["operation", "target"],
            "optional_entities": ["destination"],
        },
        "process_management": {
            "patterns": [
                "proces", "uruchom", "zatrzymaj", "kill", "start", "stop", "process", "show processes", "top processes",
                "zabij proces", "uruchom proces", "zatrzymaj proces", "restartuj proces", "uruchom ponownie",
                "uruchom w tle", "uruchom skrypt", "zatrzymaj usługę", "uruchom usługę", "status usługi",
                "sprawdź status", "monitor systemowy", "htop", "top",
                # Specific services
                "apache", "apache2", "httpd", "nginx", "mysql", "mariadb", "postgresql", "postgres",
                "docker", "redis", "mongodb", "mongod", "serwer apache", "serwer nginx", "serwer mysql"
            ],
            "required_entities": ["action"],
            "optional_entities": ["process_name", "pid"],
        },
        "process_monitoring": {
            "patterns": [
                "pokaż procesy", "top", "htop", "ps", "monitoruj", "show top", "memory usage", "cpu usage",
                "sprawdź procesy", "działające procesy", "procesy zużywające pamięć", "procesy zużywające cpu",
                "znajdź procesy", "procesy użytkownika", "zombie procesy", "drzewo procesów"
            ],
            "required_entities": [],
            "optional_entities": ["metric", "limit", "filters"],
        },
        "network": {
            "patterns": [
                "ping", "curl", "wget", "port", "sieć", "network", "network status",
                "sprawdź połączenie", "testuj łączność", "pinguj", "sprawdź ping",
                "pokaż adres ip", "adres ip", "ip address", "konfiguracja sieciowa",
                "znajdź porty", "otwarte porty", "porty nasłuchujące", "aktywne połączenia",
                "znajdź urządzenia", "skanuj sieć", "nmap", "prędkość internetu"
            ],
            "required_entities": ["action"],
            "optional_entities": ["host", "port"],
        },
        "disk": {
            "patterns": [
                "dysk", "miejsce", "disk", "space", "df", "du", "disk usage", "show disk",
                "pokaż dysk", "użycie dysku", "miejsce na dysku", "sprawdź miejsce na dysku",
                "sprawdź dysk twardy", "dysk twardy", "zdrowie dysku", "defragmentacja"
            ],
            "required_entities": ["action"],
            "optional_entities": ["path"],
        },
        "archive": {
            "patterns": [
                "spakuj", "rozpakuj", "zip", "tar", "compress", "extract", "archive",
                "utwórz backup", "skompresuj", "archiwum", "backup", "kopia zapasowa",
                "skopiuj backup", "odtwórz z backupu", "integralność backupu", "status backupu",
                "usuń stare backupi", "rozmiar backupu", "harmonogram backup"
            ],
            "required_entities": ["action", "target"],
            "optional_entities": ["destination", "format"],
        },
        "text_processing": {
            "patterns": [
                "grep", "sed", "awk", "filtruj", "wyszukaj tekst", "search text", "find text",
                "znajdź błędy", "wyszukaj błędy", "grep error", "filtruj logi", "przeglądaj logi"
            ],
            "required_entities": ["action", "pattern"],
            "optional_entities": ["file", "options"],
        },
        "system_maintenance": {
            "patterns": [
                "aktualizacja", "upgrade", "czyszczenie", "maintenance", "update", "clean",
                "czyść cache", "aktualizuj system", "uruchom aktualizację", "czyszczenie systemowe",
                "sprawdź logi", "logi systemowe", "oczyszczanie plików tymczasowych", "usuń stare pliki",
                "sprawdź cron", "status cron", "uruchom defragmentację"
            ],
            "required_entities": ["action"],
            "optional_entities": ["target"],
        },
        "development": {
            "patterns": [
                "test", "build", "compile", "run", "debug", "lint", "version", "install",
                "uruchom testy", "testy jednostkowe", "zbuduj projekt", "maven", "npm install",
                "serwer deweloperski", "uruchom serwer", "debugger", "linter", "analiza kodu",
                "logi aplikacji", "czyszczenie cache", "generuj dokumentację", "wersja node"
            ],
            "required_entities": ["action"],
            "optional_entities": ["target", "tool"],
        },
        "security": {
            "patterns": [
                "bezpieczeństwo", "security", "who", "last", "ssh", "permissions", "firewall",
                "kto jest zalogowany", "historia logowań", "sesje ssh", "uprawnienia pliku",
                "pliki suid", "firewall rules", "logi bezpieczeństwa", "podejrzane procesy",
                "zainstalowane pakiety", "użytkownicy systemu"
            ],
            "required_entities": ["action"],
            "optional_entities": ["target"],
        },
        "git": {
            "patterns": ["git", "commit", "push", "pull", "branch", "merge", "show commits", "git status"],
            "required_entities": ["action"],
            "optional_entities": ["branch", "message", "remote"],
        },
        "docker": {
            "patterns": ["docker", "kontener", "obraz", "container", "image", "docker ps"],
            "required_entities": ["action"],
            "optional_entities": ["container_name", "image_name", "options"],
        },
        "user_management": {
            "patterns": [
                "użytkownik", "user", "grupa", "group", "whoami", "who", "last", "id",
                "dodaj użytkownika", "usuń użytkownika", "zmień hasło", "passwd",
                "useradd", "userdel", "usermod", "groupadd", "kim jestem"
            ],
            "required_entities": ["action"],
            "optional_entities": ["username", "group"],
        },
        "hardware_info": {
            "patterns": [
                "cpu", "procesor", "pamięć", "ram", "hardware", "sprzęt", "lscpu", "lspci",
                "lsusb", "lshw", "urządzenia", "devices", "info o cpu", "info o sprzęcie"
            ],
            "required_entities": ["action"],
            "optional_entities": ["device"],
        },
        "disk_management": {
            "patterns": [
                "mount", "umount", "zamontuj", "odmontuj", "partycja", "partition",
                "fdisk", "mkfs", "fsck", "blkid", "lsblk", "dyski", "disks"
            ],
            "required_entities": ["action"],
            "optional_entities": ["device", "mountpoint"],
        },
        "package_management": {
            "patterns": [
                "apt", "apt-get", "dpkg", "yum", "dnf", "pacman", "snap", "flatpak",
                "zainstaluj", "odinstaluj", "aktualizuj pakiety", "install package"
            ],
            "required_entities": ["action"],
            "optional_entities": ["package"],
        },
        "service_management": {
            "patterns": [
                "systemctl", "service", "usługa", "daemon", "cron", "crontab",
                "uruchom usługę", "zatrzymaj usługę", "status usługi", "journalctl"
            ],
            "required_entities": ["action"],
            "optional_entities": ["service_name"],
        },
        "text_file_ops": {
            "patterns": [
                "cat", "head", "tail", "less", "more", "wc", "sort", "uniq", "cut", "tr",
                "pokaż plik", "wyświetl plik", "pierwsze linie", "ostatnie linie",
                "policz linie", "sortuj", "unikalne", "śledź log"
            ],
            "required_entities": ["action"],
            "optional_entities": ["file", "lines"],
        },
        "checksum": {
            "patterns": [
                "md5", "sha256", "sha1", "checksum", "suma kontrolna", "hash",
                "base64", "koduj", "dekoduj", "encode", "decode"
            ],
            "required_entities": ["action"],
            "optional_entities": ["file"],
        },
        "terminal_session": {
            "patterns": [
                "screen", "tmux", "byobu", "sesja", "session", "multiplexer",
                "nowa sesja", "lista sesji", "dołącz do sesji"
            ],
            "required_entities": ["action"],
            "optional_entities": ["session_name"],
        },
    }

    def __init__(
        self,
        shell_type: str = "bash",
        environment_context: Optional[dict[str, Any]] = None,
        safety_policy: Optional[ShellSafetyPolicy] = None,
        config: Optional[AdapterConfig] = None,
    ):
        """
        Initialize Shell adapter.

        Args:
            shell_type: Target shell (bash, zsh, fish, powershell)
            environment_context: System environment information
            safety_policy: Shell-specific safety policy
            config: Adapter configuration
        """
        super().__init__(config, safety_policy or ShellSafetyPolicy())

        if shell_type not in self.SHELL_TYPES:
            raise ValueError(f"Unsupported shell: {shell_type}. Use one of: {self.SHELL_TYPES}")

        self.shell_type = shell_type
        self.env = self._parse_environment_context(environment_context or {})

    def _parse_environment_context(self, ctx: dict[str, Any]) -> EnvironmentContext:
        """Parse environment context."""
        return EnvironmentContext(
            os=ctx.get("os", "linux"),
            distro=ctx.get("distr", "ubuntu"),
            shell=ctx.get("shell", self.shell_type),
            available_tools=ctx.get("available_tools", []),
            environment_variables=ctx.get("environment_variables", {}),
        )

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate shell command from execution plan."""
        intent = plan.get("intent", "")
        entities = plan.get("entities", {})
        
        # Store full text for fallback processing
        if "_full_text" not in entities:
            # Try multiple sources for the full text
            full_text = plan.get("text", "") or plan.get("query", "") or plan.get("input", "") or ""
            entities["_full_text"] = full_text
        
        # Add fallback service detection
        if not entities.get("process_name"):
            full_text = str(entities.get("_full_text", ""))
            for service in ["apache", "apache2", "httpd", "nginx", "mysql", "mariadb", "postgresql", "postgres", "docker", "redis", "mongodb"]:
                if service in full_text.lower():
                    entities["process_name"] = service
                    break
        
        # Add fallback action detection
        if not entities.get("action"):
            full_text = str(entities.get("_full_text", "")).lower()
            if "uruchom" in full_text or "start" in full_text:
                entities["action"] = "uruchom"
            elif "zatrzymaj" in full_text or "stop" in full_text:
                entities["action"] = "zatrzymaj"
            elif "zabij" in full_text or "kill" in full_text:
                entities["action"] = "zabij"
            elif "restartuj" in full_text or "restart" in full_text:
                entities["action"] = "restartuj"

        generators = {
            "file_search": self._generate_file_search,
            "find": self._generate_find,
            "list": self._generate_list,
            "list_dirs": self._generate_list_dirs,
            "file_operation": self._generate_file_operation,
            "process_management": self._generate_process_management,
            "process_monitoring": self._generate_process_monitoring,
            "network": self._generate_network,
            "disk": self._generate_disk,
            "archive": self._generate_archive,
            "text_processing": self._generate_text_processing,
            "search": self._generate_text_processing,  # grep alias
            "grep": self._generate_text_processing,  # grep alias
            "system_maintenance": self._generate_system_maintenance,
            "development": self._generate_development,
            "security": self._generate_security,
            "git": self._generate_git,
            "docker": self._generate_docker,
            "container_management": self._generate_docker,  # alias
            "user_management": self._generate_user_management,
            "hardware_info": self._generate_hardware_info,
            "disk_management": self._generate_disk_management,
            "package_management": self._generate_package_management,
            "service_management": self._generate_service_management,
            "text_file_ops": self._generate_text_file_ops,
            "checksum": self._generate_checksum,
            "terminal_session": self._generate_terminal_session,
            "cat": self._generate_cat,
            "head": self._generate_head_tail,
            "tail": self._generate_head_tail,
            "wc": self._generate_wc,
        }

        generator = generators.get(intent)
        if generator:
            return generator(entities)

        # Fallback: try to construct command from entities
        return self._generate_generic(entities)

    def _generate_file_search(self, entities: dict[str, Any]) -> str:
        """Generate find command."""
        target = entities.get("target", "files")
        filters = entities.get("filters", [])
        scope = entities.get("path", entities.get("scope", "."))
        mtime_filtered = False
        
        # Build find command with entities
        cmd_parts = ["find", scope]
        
        # Add type filter
        if target == "files" or "plik" in str(target).lower():
            cmd_parts.append("-type f")
        elif target == "directories" or "katalog" in str(target).lower():
            cmd_parts.append("-type d")
        
        # Add name pattern
        if "filename" in entities:
            cmd_parts.extend(["-name", f'"{entities["filename"]}"'])
        elif "file_pattern" in entities:
            cmd_parts.extend(["-name", f'"{entities["file_pattern"]}"'])
        
        # Process filters list
        for filter_item in filters:
            if isinstance(filter_item, dict):
                attr = filter_item.get("attribute")
                operator = filter_item.get("operator", ">")
                value = filter_item.get("value")
                
                if attr == "size" and value:
                    # Handle size filter
                    if isinstance(value, str):
                        # Parse string like "100M"
                        m = re.match(r"^(\d+)\s*([a-zA-Z]+)$", value.strip())
                        if m:
                            num = m.group(1)
                            unit = m.group(2).upper()
                            # Convert MB->M, GB->G, KB->k, etc.
                            if unit.startswith('M') and len(unit) > 1:
                                unit = 'M'
                            elif unit.startswith('G') and len(unit) > 1:
                                unit = 'G'
                            elif unit.startswith('K') and len(unit) > 1:
                                unit = 'k'
                            elif unit.startswith('T') and len(unit) > 1:
                                unit = 'T'
                            cmd_parts.append(f"-size +{num}{unit}")
                        else:
                            cmd_parts.append(f"-size +{value}")
                
                elif attr == "mtime" and value:
                    # Handle modification time filter
                    m = re.search(r"(\d+)", str(value))
                    days = m.group(1) if m else str(value)
                    cmd_parts.append(f"-mtime -{days}")
                    mtime_filtered = True
                
                elif attr == "age" and value:
                    # Handle age filter
                    m = re.search(r"(\d+)", str(value))
                    days = m.group(1) if m else str(value)
                    cmd_parts.append(f"-mtime -{days}")
                    mtime_filtered = True
        # Add name pattern
        if "file_pattern" in entities:
            cmd_parts.extend(["-name", f'"*.{entities["file_pattern"]}"'])
        
        # Add size filter
        if "size" in entities and isinstance(entities["size"], dict):
            size_info = entities["size"]
            if "value" in size_info and "unit" in size_info:
                unit = size_info['unit']
                # Convert MB->M, GB->G, KB->k, etc.
                if unit.startswith('M') and len(unit) > 1:
                    unit = 'M'
                elif unit.startswith('G') and len(unit) > 1:
                    unit = 'G'
                elif unit.startswith('K') and len(unit) > 1:
                    unit = 'k'
                elif unit.startswith('T') and len(unit) > 1:
                    unit = 'T'
                cmd_parts.append(f"-size +{size_info['value']}{unit}")
        elif "size" in entities:
            size_str = entities["size"]
            # Parse string like "10MB" and convert
            m = re.match(r"^(\d+)\s*([a-zA-Z]+)$", size_str.strip())
            if m:
                value = m.group(1)
                unit = m.group(2).upper()
                # Convert MB->M, GB->G, KB->k, etc.
                if unit.startswith('M') and len(unit) > 1:
                    unit = 'M'
                elif unit.startswith('G') and len(unit) > 1:
                    unit = 'G'
                elif unit.startswith('K') and len(unit) > 1:
                    unit = 'k'
                elif unit.startswith('T') and len(unit) > 1:
                    unit = 'T'
                cmd_parts.append(f"-size +{value}{unit}")
            else:
                cmd_parts.append(f"-size +{entities['size']}")
        
        # Add age/time filter
        if "age" in entities and isinstance(entities["age"], dict):
            age_info = entities["age"]
            if "value" in age_info and "unit" in age_info:
                unit_map = {"days": "mtime", "hours": "mmin", "minutes": "mmin"}
                time_unit = unit_map.get(age_info["unit"].lower(), "mtime")
                cmd_parts.append(f"-{time_unit} -{age_info['value']}")
                if time_unit == "mtime":
                    mtime_filtered = True
        
        # Handle specific Polish patterns from natural language (fallback)
        elif "rozszerzeniem" in str(target) or "extension" in str(target):
            extension = entities.get("extension", "py")
            cmd_parts.extend(["-name", f"*.{extension}"])
        elif "większe niż" in str(target) or "size" in str(target):
            size = entities.get("size", "100M")
            cmd_parts.append(f"-size +{size}")
        elif "zmodyfikowane" in str(target) or "mtime" in str(target):
            days = entities.get("days", "7")
            m = re.search(r"(\d+)", str(days))
            days = m.group(1) if m else str(days)
            cmd_parts.append(f"-mtime -{days}")
            mtime_filtered = True
        
        if mtime_filtered:
            printf_format = "'%T@\\t%TY-%Tm-%Td %TH:%TM:%TS\\t%s\\t%p\\n'"
            find_cmd = " ".join(cmd_parts + ["-printf", printf_format])
            return f"{find_cmd} | sort -nr | cut -f2-"

        return " ".join(cmd_parts)

    def _generate_find(self, entities: dict[str, Any]) -> str:
        """Generate find command using entities."""
        scope = entities.get("path", entities.get("scope", "."))
        cmd_parts = ["find", scope]
        mtime_filtered = False
        
        # Add type filter
        target = entities.get("target", "files")
        if target == "files" or "plik" in str(target).lower():
            cmd_parts.append("-type f")
        elif target == "directories" or "katalog" in str(target).lower():
            cmd_parts.append("-type d")
        
        # Add name pattern
        if "filename" in entities:
            cmd_parts.extend(["-name", f'"{entities["filename"]}"'])
        elif "file_pattern" in entities:
            cmd_parts.extend(["-name", f"*.{entities['file_pattern']}"])
        
        # Process filters list
        filters = entities.get("filters", [])
        for filter_item in filters:
            if isinstance(filter_item, dict):
                attr = filter_item.get("attribute")
                operator = filter_item.get("operator", ">")
                value = filter_item.get("value")
                
                if attr == "size" and value:
                    # Handle size filter
                    if isinstance(value, str):
                        # Parse string like "100M"
                        m = re.match(r"^(\d+)\s*([a-zA-Z]+)$", value.strip())
                        if m:
                            num = m.group(1)
                            unit = m.group(2).upper()
                            # Convert MB->M, GB->G, KB->k, etc.
                            if unit.startswith('M') and len(unit) > 1:
                                unit = 'M'
                            elif unit.startswith('G') and len(unit) > 1:
                                unit = 'G'
                            elif unit.startswith('K') and len(unit) > 1:
                                unit = 'k'
                            elif unit.startswith('T') and len(unit) > 1:
                                unit = 'T'
                            cmd_parts.append(f"-size +{num}{unit}")
                        else:
                            cmd_parts.append(f"-size +{value}")
                    else:
                        cmd_parts.append(f"-size +{value}")
                
                elif attr == "mtime" and value:
                    # Handle modification time filter
                    m = re.search(r"(\d+)", str(value))
                    days = m.group(1) if m else str(value)
                    cmd_parts.append(f"-mtime -{days}")
                    mtime_filtered = True
                
                elif attr == "age" and value:
                    # Handle age filter
                    m = re.search(r"(\d+)", str(value))
                    days = m.group(1) if m else str(value)
                    cmd_parts.append(f"-mtime -{days}")
                    mtime_filtered = True
        
        # Add size filter
        if "size" in entities and isinstance(entities["size"], dict):
            size_info = entities["size"]
            if "value" in size_info and "unit" in size_info:
                unit = size_info['unit']
                # Convert MB->M, GB->G, KB->k, etc.
                if unit.startswith('M') and len(unit) > 1:
                    unit = 'M'
                elif unit.startswith('G') and len(unit) > 1:
                    unit = 'G'
                elif unit.startswith('K') and len(unit) > 1:
                    unit = 'k'
                elif unit.startswith('T') and len(unit) > 1:
                    unit = 'T'
                cmd_parts.append(f"-size +{size_info['value']}{unit}")
        
        # Handle string size (e.g., "10MB")
        elif "size" in entities and isinstance(entities["size"], str):
            size_str = entities["size"]
            # Parse string like "10MB" and convert
            m = re.match(r"^(\d+)\s*([a-zA-Z]+)$", size_str.strip())
            if m:
                value = m.group(1)
                unit = m.group(2).upper()
                # Convert MB->M, GB->G, KB->k, etc.
                if unit.startswith('M') and len(unit) > 1:
                    unit = 'M'
                elif unit.startswith('G') and len(unit) > 1:
                    unit = 'G'
                elif unit.startswith('K') and len(unit) > 1:
                    unit = 'k'
                elif unit.startswith('T') and len(unit) > 1:
                    unit = 'T'
                cmd_parts.append(f"-size +{value}{unit}")
        
        # Add age/time filter
        if "age" in entities and isinstance(entities["age"], dict):
            age_info = entities["age"]
            if "value" in age_info and "unit" in age_info:
                unit_map = {"days": "mtime", "hours": "mmin", "minutes": "mmin"}
                time_unit = unit_map.get(age_info["unit"].lower(), "mtime")
                cmd_parts.append(f"-{time_unit} -{age_info['value']}")
                if time_unit == "mtime":
                    mtime_filtered = True
        
        # Handle specific Polish patterns from natural language (fallback)
        full_text = str(entities.get("_full_text", "")).lower()
        if "zmodyfikowane" in full_text or "mtime" in str(target).lower():
            days = entities.get("days", "7")
            m = re.search(r"(\d+)", str(days))
            days = m.group(1) if m else str(days)
            cmd_parts.append(f"-mtime -{days}")
            mtime_filtered = True

        if mtime_filtered:
            printf_format = "'%T@\\t%TY-%Tm-%Td %TH:%TM:%TS\\t%s\\t%p\\n'"
            find_cmd = " ".join(cmd_parts + ["-printf", printf_format])
            return f"{find_cmd} | sort -nr | cut -f2-"
        
        return " ".join(cmd_parts)

    @staticmethod
    def _normalize_find_size_value(value: Any) -> str:
        """Normalize values like '10KB'/'1MB' into GNU find -size suffixes (k/M/G/T/c)."""
        s = str(value or "").strip()
        if not s:
            return ""

        m = re.match(r"^(\d+)(?:\s*)([a-zA-Z]+)?$", s)
        if not m:
            return s

        num = m.group(1)
        unit = (m.group(2) or "").strip().upper()

        if unit in {"KB", "K"}:
            return f"{num}k"
        if unit in {"MB", "M"}:
            return f"{num}M"
        if unit in {"GB", "G"}:
            return f"{num}G"
        if unit in {"TB", "T"}:
            return f"{num}T"
        if unit in {"B", "BYTE", "BYTES", "C"}:
            return f"{num}c"

        return s

    def _generate_file_operation(self, entities: dict[str, Any]) -> str:
        """Generate file operation command."""
        operation = entities.get("operation", "")
        target = entities.get("target", "")
        destination = entities.get("destination", "")
        
        # Extract operation from matched keyword if not in entities
        if not operation and "matched_keyword" in entities:
            matched = entities["matched_keyword"]
            if any(kw in matched for kw in ["zainstaluj", "install", "apt install", "apt-get install"]):
                operation = "install"
            elif any(kw in matched for kw in ["dodaj", "pobierz", "wget", "curl"]):
                operation = "download"
        
        # Handle install operations
        if "zainstaluj" in operation or "install" in operation or "apt install" in operation or "apt-get install" in operation:
            package = entities.get("package", target)
            if package:
                return f"sudo apt-get install {package}"
            else:
                return "sudo apt-get install"
        elif "dodaj" in operation or "pobierz" in operation or "wget" in operation or "curl" in operation:
            if target:
                return f"wget {target}"
            else:
                return "wget"
        
        # Handle specific Polish patterns
        if "kopiuj" in operation or "copy" in operation:
            if destination:
                return f"cp {target} {destination}"
            else:
                return f"cp {target} ."
        elif "przenieś" in operation or "move" in operation:
            if destination:
                return f"mv {target} {destination}"
            else:
                return f"mv {target} ."
        elif "usuń" in operation or "delete" in operation or "remove" in operation:
            if "wszystkie" in str(target) or "all" in str(target):
                extension = entities.get("extension", "tmp")
                return f"find . -name '*.{extension}' -delete"
            else:
                return f"rm {target}"
        elif "utwórz" in operation or "create" in operation:
            if "katalog" in str(target) or "directory" in str(target):
                return f"mkdir {target}"
            else:
                return f"touch {target}"
        elif "zmień nazwę" in operation or "rename" in operation or "mv" in operation:
            if "na" in str(target):
                parts = str(target).split(" na ")
                if len(parts) == 2:
                    old_name = parts[0].replace("zmień nazwę pliku", "").strip()
                    new_name = parts[1].strip()
                    return f"mv {old_name} {new_name}"
            return f"mv {target} {destination}"
        elif "rozmiar" in str(target) or "du" in str(target):
            return f"du -h {target}"

        operations = {
            "copy": f"cp -r {shlex.quote(target)} {shlex.quote(destination)}",
            "move": f"mv {shlex.quote(target)} {shlex.quote(destination)}",
            "delete": f"rm -rf {shlex.quote(target)}",
            "create": f"touch {shlex.quote(target)}",
            "mkdir": f"mkdir -p {shlex.quote(target)}",
        }

        return operations.get(operation, f"# Unknown operation: {operation}")

    def _generate_process_management(self, entities: dict[str, Any]) -> str:
        """Generate process management command."""
        action = entities.get("action", "")
        process_name = entities.get("process_name", "")
        pid = entities.get("pid", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Direct ps command detection
        if "ps aux" in full_text or "ps " in full_text:
            return "ps aux"
        if full_text.strip() == "ps":
            return "ps aux"
        
        # If no entities extracted, use full text parsing
        if not action and not process_name:
            
            # Detect action
            if "uruchom" in full_text or "start" in full_text:
                action = "uruchom"
            elif "zatrzymaj" in full_text or "stop" in full_text:
                action = "zatrzymaj"
            elif "zabij" in full_text or "kill" in full_text:
                action = "zabij"
            elif "restartuj" in full_text or "restart" in full_text:
                action = "restartuj"
            
            # Detect service name
            for service in ["apache", "apache2", "httpd", "nginx", "mysql", "mariadb", "postgresql", "postgres", "docker", "redis", "mongodb"]:
                if service in full_text:
                    process_name = service
                    break
        
        # Common service mappings
        service_mappings = {
            "apache": "apache2",
            "apache2": "apache2", 
            "httpd": "httpd",
            "nginx": "nginx",
            "mysql": "mysql",
            "mariadb": "mariadb",
            "postgresql": "postgresql",
            "postgres": "postgresql",
            "docker": "docker",
            "redis": "redis",
            "mongodb": "mongod"
        }
        
        # Map common service names
        if process_name.lower() in service_mappings:
            service_name = service_mappings[process_name.lower()]
            is_service = True
        else:
            service_name = process_name
            is_service = False
        
        # Handle specific Polish patterns
        if "zabij" in action or "kill" in action:
            if pid:
                return f"kill -9 {pid}"
            elif process_name:
                return f"pkill -f {process_name}"
            else:
                return "kill -9 PID"
        elif "uruchom" in action or "start" in action:
            if "w tle" in str(action) or "background" in str(action):
                if process_name:
                    return f"nohup {process_name} &"
                else:
                    return "nohup python script.py &"
            elif "skrypt" in str(process_name) or "script" in str(process_name):
                return f"./{process_name}"
            elif "usługę" in str(action) or "service" in str(action) or is_service or "serwer" in str(process_name):
                return f"systemctl start {service_name}"
            else:
                # Fallback: if no process_name but action suggests service start
                if not process_name and ("serwer" in str(action) or "usługę" in str(action)):
                    return "systemctl start"
                elif process_name:
                    return f"{process_name}"
                else:
                    return "# Process action"
        elif "zatrzymaj" in action or "stop" in action:
            if "usługę" in str(action) or "service" in str(action) or is_service or "serwer" in str(process_name):
                return f"systemctl stop {service_name}"
            elif process_name:
                return f"pkill -f {process_name}"
            else:
                return "stop"
        elif "restartuj" in action or "restart" in action or "ponownie" in action:
            if "serwer" in str(process_name) or "server" in str(process_name):
                service_name = entities.get("service_name", "apache2")
                return f"systemctl restart {service_name}"
            elif "usługę" in str(action) or "service" in str(action):
                service_name = entities.get("service_name", process_name)
                return f"systemctl restart {service_name}"
            else:
                return f"restart {process_name}"
        elif "status" in action:
            if "usługi" in str(action) or "service" in str(action):
                service_name = entities.get("service_name", process_name)
                return f"systemctl status {service_name}"
            else:
                return f"status {process_name}"

        if action in ["kill", "stop"]:
            if pid:
                return f"kill {pid}"
            elif process_name:
                return f"pkill {shlex.quote(process_name)}"
        elif action == "start":
            return f"{process_name} &"

        return f"# Process action: {action}"

    def _generate_process_monitoring(self, entities: dict[str, Any]) -> str:
        """Generate process monitoring command."""
        metric = entities.get("metric", "cpu")
        limit = entities.get("limit", 10)
        projection = entities.get("projection", [])
        metric_lower = str(metric).lower()
        
        # Handle specific Polish patterns
        if "cpu" in metric_lower and "memory" not in metric_lower and "pamię" not in metric_lower:
            return "top -n 1"
        elif "procesy" in str(metric) or "działające" in str(metric):
            return "ps aux"
        elif "zużywające" in str(metric):
            if "pamięć" in str(metric) or "memory" in str(metric):
                return "ps aux --sort=-%mem | head -10"
            elif "cpu" in str(metric):
                return "ps aux --sort=-%cpu | head -10"
            else:
                return "ps aux | head -10"
        elif "użytkownika" in str(metric):
            user = entities.get("user", "tom")
            return f"ps aux | grep {user}"
        elif "zombie" in str(metric):
            return "ps aux | awk '{print $8}' | grep -v '^\\[' | sort | uniq -c"
        elif "drzewo" in str(metric) or "tree" in str(metric):
            return "pstree"
        elif "monitor" in str(metric) or "htop" in str(metric):
            return "htop"

        if metric == "memory_usage" or metric == "memory":
            sort_flag = "-%mem"
        else:
            sort_flag = "-%cpu"

        # Build command with pipeline
        cmd = f"ps aux --sort={sort_flag} | head -{limit + 1}"

        if projection:
            # Add awk to filter columns
            if "process_name" in projection and "memory_percent" in projection:
                cmd += " | tail -{} | awk '{{print $11, $4\"%\"}}'".format(limit)
            elif "process_name" in projection:
                cmd += " | tail -{} | awk '{{print $11}}'".format(limit)

        return cmd

    def _generate_network(self, entities: dict[str, Any]) -> str:
        """Generate network command."""
        action = entities.get("action", "")
        host = entities.get("host", "")
        port = entities.get("port", "")
        
        # Handle specific Polish patterns
        if "połączenie" in str(action) or "ping" in action:
            if host:
                return f"ping -c 4 {host}"
            else:
                return "ping -c 4 google.com"
        elif "port" in str(action) or "porty" in action:
            if "otwarte" in str(action) or "nasłuchujące" in str(action):
                return "netstat -tuln | grep LISTEN"
            elif port:
                return f"lsof -i :{port}"
            else:
                return "netstat -tuln"
        elif "adres" in str(action) or "ip" in action:
            return "ip addr show"
        elif "konfiguracja" in str(action) or "config" in action:
            return "ifconfig -a"
        elif "urządzenia" in str(action) or "nmap" in action:
            return "nmap -sn 192.168.1.0/24"
        elif "prędkość" in str(action) or "speed" in action:
            return "curl -o /dev/null -s -w '%{time_total}' http://speedtest.net"
        elif "aktywne" in str(action) or "connections" in action:
            return "ss -tulpn"

        if action == "ping":
            return f"ping -c 4 {shlex.quote(host)}"
        elif action == "check_port":
            return f"nc -zv {shlex.quote(host)} {port}"
        elif action == "curl":
            return f"curl -s {shlex.quote(host)}"
        elif action == "wget":
            return f"wget {shlex.quote(host)}"
        elif action == "ports":
            return "netstat -tuln"

        return f"# Network action: {action}"

    def _generate_disk(self, entities: dict[str, Any]) -> str:
        """Generate disk command."""
        action = entities.get("action", "usage")
        path = entities.get("path", ".")
        
        # Handle specific Polish patterns
        if "dysk" in str(action) or "miejsce" in str(action) or "usage" in str(action):
            return "df -h"
        elif "zdrowie" in str(action) or "health" in str(action):
            return "fsck -n /dev/sda1"
        elif "defragmentacja" in str(action) or "defrag" in action:
            return "defrag /dev/sda1"

        if action == "usage":
            return f"df -h {path}"
        elif action == "size":
            return f"du -sh {path}"
        elif action == "tree":
            return f"tree -L 2 {path}"

        return f"df -h {path}"

    def _generate_archive(self, entities: dict[str, Any]) -> str:
        """Generate archive command."""
        action = entities.get("action", "")
        target = entities.get("target", "")
        destination = entities.get("destination", "")
        fmt = entities.get("format", "tar.gz")
        
        # Handle specific Polish patterns
        if "backup" in str(action) or "kopia" in str(action):
            if "utwórz" in str(action) or "create" in str(action):
                if "katalogu" in str(target) or "directory" in str(target):
                    return f"tar -czf backup.tar.gz {target}"
                else:
                    return f"tar -czf backup.tar.gz {target}"
            elif "skopiuj" in str(action) or "copy" in str(action):
                return f"rsync -av {target} {destination}"
            elif "odtwórz" in str(action) or "restore" in str(action):
                return f"tar -xzf backup.tar.gz {target}"
            elif "integralność" in str(action) or "integrity" in str(action):
                return f"md5sum {target}"
            elif "status" in str(action):
                return f"ls -la {destination}"
            elif "stare" in str(action) and "backupi" in str(target):
                return f"find {destination} -mtime +7 -delete"
            elif "rozmiar" in str(target) or "size" in str(target):
                return f"du -sh {target}"
            elif "harmonogram" in str(action) or "schedule" in str(action):
                return "crontab -l"
        elif "skompresuj" in str(action) or "compress" in action:
            return f"tar -czf archive.tar.gz {target}"
        elif "spakuj" in str(action) or "pack" in action:
            return f"tar -czf {fmt} {target}"

        if action in ["compress", "pack", "spakuj"]:
            if fmt == "zip":
                return f"zip -r {shlex.quote(destination or target + '.zip')} {shlex.quote(target)}"
            else:
                return f"tar -czvf {shlex.quote(destination or target + '.tar.gz')} {shlex.quote(target)}"
        elif action in ["extract", "unpack", "rozpakuj"]:
            if target.endswith(".zip"):
                return f"unzip {shlex.quote(target)}"
            else:
                return f"tar -xzvf {shlex.quote(target)}"

        return f"# Archive action: {action}"

    def _generate_text_processing(self, entities: dict[str, Any]) -> str:
        """Generate text processing command."""
        action = entities.get("action", "grep")
        pattern = entities.get("pattern", "")
        file = entities.get("file", "")

        if action == "grep" or action == "search":
            return f"grep -r {shlex.quote(pattern)} {shlex.quote(file) if file else '.'}"
        elif action == "count":
            return f"grep -c {shlex.quote(pattern)} {shlex.quote(file)}"
        elif action == "replace":
            replacement = entities.get("replacement", "")
            return f"sed -i 's/{pattern}/{replacement}/g' {shlex.quote(file)}"

        return f"grep {shlex.quote(pattern)} {shlex.quote(file)}"

    def _generate_git(self, entities: dict[str, Any]) -> str:
        """Generate git command."""
        action = entities.get("action", "")
        branch = entities.get("branch", "")
        message = entities.get("message", "")
        remote = entities.get("remote", "origin")

        commands = {
            "status": "git status",
            "pull": f"git pull {remote} {branch}" if branch else f"git pull {remote}",
            "push": f"git push {remote} {branch}" if branch else f"git push {remote}",
            "commit": f"git commit -m {shlex.quote(message)}" if message else "git commit",
            "add": "git add .",
            "branch": f"git checkout -b {branch}" if branch else "git branch",
            "checkout": f"git checkout {branch}",
            "log": "git log --oneline -10",
            "diff": "git diff",
            "stash": "git stash",
        }

        return commands.get(action, f"git {action}")

    def _generate_system_maintenance(self, entities: dict[str, Any]) -> str:
        """Generate system maintenance command."""
        action = entities.get("action", "")
        target = entities.get("target", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Fallback: extract action from full text if not in entities
        if not action and full_text:
            if "aktualizuj" in full_text or "update" in full_text or "aktualizacja" in full_text:
                action = "aktualizuj"
            elif "czyść" in full_text or "clean" in full_text:
                action = "czyść"
            elif "sprawdź" in full_text:
                action = "sprawdź"
        
        # Fallback: extract target from full text if not in entities
        if not target and full_text:
            if "system" in full_text or "systemu" in full_text:
                target = "system"
            elif "cache" in full_text:
                target = "cache"
            elif "logi" in full_text:
                target = "logi"
            elif "cron" in full_text:
                target = "cron"
        
        if "aktualizuj" in action or "update" in action or "aktualizacja" in full_text:
            # Try non-sudo check first, fall back to sudo if needed
            return "apt list --upgradable 2>/dev/null | grep -v 'WARNING:' || sudo apt update && sudo apt upgrade -y"
        elif "czyść" in action or "clean" in action:
            if "cache" in target:
                return "apt clean && apt autoclean"
            elif "tmp" in target:
                return "rm -rf /tmp/*"
            else:
                return "apt autoremove"
        elif "logi" in target:
            return "tail -n 50 /var/log/syslog"
        elif "cron" in target:
            return "systemctl status cron"
        elif "defragmentacja" in action:
            return "defrag /dev/sda1"
        
        return f"# System maintenance: {action}"

    def _generate_development(self, entities: dict[str, Any]) -> str:
        """Generate development command."""
        action = entities.get("action", "")
        target = entities.get("target", "")
        tool = entities.get("tool", "")
        
        if "test" in action:
            if "pytest" in tool or "python" in tool:
                return "pytest tests/"
            elif "maven" in tool:
                return "mvn test"
            else:
                return "python -m pytest"
        elif "build" in action:
            if "maven" in tool:
                return "mvn clean install"
            elif "npm" in tool:
                return "npm run build"
            else:
                return "make build"
        elif "install" in action:
            if "npm" in tool:
                return "npm install"
            elif "pip" in tool:
                return "pip install -r requirements.txt"
            else:
                return "apt install"
        elif "run" in action or "serwer" in target:
            if "django" in tool:
                return "python manage.py runserver"
            elif "flask" in tool:
                return "flask run"
            else:
                return "python main.py"
        elif "debug" in action:
            return "python -m pdb script.py"
        elif "lint" in action:
            if "python" in tool:
                return "pylint src/"
            elif "javascript" in tool:
                return "eslint ."
            else:
                return "lint"
        elif "version" in action:
            if "node" in tool:
                return "node --version"
            elif "python" in tool:
                return "python --version"
            else:
                return "version"
        elif "logi" in target:
            return "tail -f app.log"
        elif "cache" in target:
            return "rm -rf __pycache__"
        elif "dokumentacja" in target:
            return "sphinx-build -b html docs/"
        
        return f"# Development: {action}"

    def _generate_security(self, entities: dict[str, Any]) -> str:
        """Generate security command."""
        action = entities.get("action", "")
        target = entities.get("target", "")
        
        if "zalogowany" in target or "who" in action:
            return "who"
        elif "historia" in target or "logowań" in target:
            return "last -n 10"
        elif "uprawnienia" in target:
            file_path = entities.get("file_path", "config.conf")
            return f"ls -la {file_path}"
        elif "suid" in target:
            return "find / -perm -4000 -type f"
        elif "firewall" in target:
            return "iptables -L"
        elif "bezpieczeństwa" in target:
            return "tail -n 100 /var/log/auth.log"
        elif "podejrzane" in target:
            return "ps aux | grep -v '\\['"
        elif "pakiety" in target:
            return "dpkg -l | grep -i security"
        elif "użytkownicy" in target:
            return "cat /etc/passwd"
        
        return f"# Security: {action}"

    def _generate_docker(self, entities: dict[str, Any]) -> str:
        """Generate docker command."""
        action = entities.get("action", "")
        actions = entities.get("actions", [action] if action else [])
        container_name = entities.get("container_name", "")
        image_name = entities.get("image_name", "")
        filters = entities.get("filters", [])

        # Handle complex multi-action scenarios
        if len(actions) > 1:
            return self._generate_docker_script(actions, entities)

        action = actions[0] if actions else "ps"

        commands = {
            "ps": "docker ps",
            "images": "docker images",
            "run": f"docker run -d {shlex.quote(image_name)}",
            "stop": f"docker stop {shlex.quote(container_name)}",
            "start": f"docker start {shlex.quote(container_name)}",
            "restart": f"docker restart {shlex.quote(container_name)}",
            "rm": f"docker rm {shlex.quote(container_name)}",
            "rmi": f"docker rmi {shlex.quote(image_name)}",
            "logs": f"docker logs -f {shlex.quote(container_name)} --tail=100",
            "exec": f"docker exec -it {shlex.quote(container_name)} /bin/bash",
            "build": f"docker build -t {shlex.quote(image_name)} .",
            "pull": f"docker pull {shlex.quote(image_name)}",
            "prune": "docker system prune -f",
        }

        return commands.get(action, f"docker {action}")

    def _generate_docker_script(
        self, actions: list[str], entities: dict[str, Any]
    ) -> str:
        """Generate multi-step docker script."""
        filters = entities.get("filters", [])
        
        script_lines = ["#!/bin/bash", "# WARNING: Review before executing", ""]

        # Build filter condition
        filter_condition = ""
        for f in filters:
            if f.get("attribute") == "running_time":
                # Complex filtering for running time
                filter_condition = "running > 24h"

        if "stop_containers" in actions:
            script_lines.extend([
                "# Find and stop old containers",
                'OLD_CONTAINERS=$(docker ps --filter "status=running" --format "{{.ID}}")',
                "",
                'if [ -n "$OLD_CONTAINERS" ]; then',
                '    echo "Stopping containers..."',
                "    docker stop $OLD_CONTAINERS",
            ])

            if "remove_images" in actions:
                script_lines.extend([
                    "",
                    "    # Get images from stopped containers",
                    "    IMAGES=$(docker inspect --format='{{.Image}}' $OLD_CONTAINERS 2>/dev/null)",
                    '    if [ -n "$IMAGES" ]; then',
                    "        docker rmi $IMAGES 2>/dev/null",
                    "    fi",
                ])

            script_lines.extend([
                "else",
                '    echo "No containers found matching criteria"',
                "fi",
            ])

        return "\n".join(script_lines)

    def _generate_list(self, entities: dict[str, Any]) -> str:
        """Generate list command."""
        path = entities.get("path", ".")
        username = entities.get("username", "")
        target = entities.get("target", "")
        full_text = entities.get("_full_text", "")
        
        # Extract path from full text if not already found
        if path == "." and full_text:
            # Match paths like /app/test_data, /home/user, etc.
            path_match = re.search(r'(/[\w./-]+)', full_text)
            if path_match:
                path = path_match.group(1)
        
        # Check if listing directories/folders specifically
        is_listing_folders = (
            "folder" in target.lower() or 
            "katalog" in target.lower() or 
            "directories" in target.lower() or
            "folder" in full_text.lower()
        )
        
        if is_listing_folders:
            # Clean path by removing 'folders' if present
            if path.endswith("folders"):
                path = path[:-7].strip()
                if not path:
                    path = "~"
            
            # Handle user-specific paths
            if "user" in str(path).lower():
                path = "~"
            
            return f"find {path} -maxdepth 1 -type d"
        
        # Handle user home directory explicitly
        if path == "~" or path == "~/":
            return "ls -la ~"
        
        # Handle user-specific paths
        if username:
            # Check for user-related keywords
            user_keywords = ["użytkownika", "usera", "user", "użytkownik"]
            if any(keyword in username.lower() for keyword in user_keywords):
                # Default to current user home directory for generic user references
                if username.lower() in ["użytkownika", "usera", "user", "użytkownik", "folders"]:
                    return "ls -la ~"
                else:
                    # Try to extract actual username
                    m = re.search(r'(?:użytkownika|usera|user)\s+([a-zA-Z0-9_-]+)', username, re.IGNORECASE)
                    if m:
                        user = m.group(1)
                        return f"ls -la ~{user}"
                    else:
                        return "ls -la ~"
        
        # Default list command
        if "folders" in path.lower():
            clean_path = path.lower().replace("folders", "").strip()
            if not clean_path or clean_path == "~":
                clean_path = "~"
            return f"ls -la {clean_path} | grep '^d'"
        
        # Check if we're listing folders based on target or full text
        text = entities.get("text", "")
        if (target and "folder" in target.lower()) or (full_text and "folder" in full_text.lower()) or "folders" in str(full_text).lower() or "folders" in str(text).lower():
            return f"find {path} -maxdepth 1 -type d"
        
        return f"ls -la {path}"

    def _generate_list_dirs(self, entities: dict[str, Any]) -> str:
        """Generate list directories command."""
        path = entities.get("path", "~")
        full_text = entities.get("_full_text", "")
        
        # Clean path for user folders
        if "user" in str(path).lower() and "folders" in str(path).lower():
            path = "~"
        elif path.endswith("folders"):
            path = path[:-7].strip()
            if not path:
                path = "~"
        
        # Handle user-specific paths
        if "user" in full_text.lower():
            path = "~"
        
        return f"find {path} -maxdepth 1 -type d"

    def _generate_generic(self, entities: dict[str, Any]) -> str:
        """Generate generic command from entities."""
        command = entities.get("command", "")
        args = entities.get("args", [])

        if command:
            return f"{command} {' '.join(args)}"
        
        # Fallback logic for process management when intent is not detected
        full_text = str(entities.get("_full_text", "")).lower()
        action = entities.get("action", "")
        process_name = entities.get("process_name", "")
        
        # Detect action if not set
        if not action:
            if "uruchom" in full_text or "start" in full_text:
                action = "uruchom"
            elif "zatrzymaj" in full_text or "stop" in full_text:
                action = "zatrzymaj"
            elif "zabij" in full_text or "kill" in full_text:
                action = "zabij"
            elif "restartuj" in full_text or "restart" in full_text:
                action = "restartuj"
        
        # Detect service name if not set
        if not process_name:
            for service in ["apache", "apache2", "httpd", "nginx", "mysql", "mariadb", "postgresql", "postgres", "docker", "redis", "mongodb"]:
                if service in full_text:
                    process_name = service
                    break
        
        # Generate command if we have action and/or process_name
        if action and process_name:
            if "uruchom" in action or "start" in action:
                return f"systemctl start {process_name}"
            elif "zatrzymaj" in action or "stop" in action:
                return f"systemctl stop {process_name}"
            elif "restartuj" in action or "restart" in action:
                return f"systemctl restart {process_name}"
            elif "zabij" in action or "kill" in action:
                return f"pkill -f {process_name}"
        elif action:
            if "uruchom" in action or "start" in action:
                return "systemctl start"
            elif "zatrzymaj" in action or "stop" in action:
                return "systemctl stop"
            elif "restartuj" in action or "restart" in action:
                return "systemctl restart"
            elif "zabij" in action or "kill" in action:
                return "kill -9 PID"

        return "# Could not generate command"

    def _generate_user_management(self, entities: dict[str, Any]) -> str:
        """Generate user management command."""
        action = entities.get("action", "")
        username = entities.get("username", "")
        group = entities.get("group", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        if "whoami" in full_text or "kim jestem" in full_text:
            return "whoami"
        elif "who" in action or "zalogowani" in full_text:
            return "who"
        elif "last" in action or "historia logowań" in full_text:
            return "last -n 10"
        elif "id" in action or "identyfikator" in full_text:
            if username:
                return f"id {username}"
            return "id"
        elif "groups" in action or "grupy" in full_text:
            if username:
                return f"groups {username}"
            return "groups"
        elif "dodaj" in action or "useradd" in action or "add user" in full_text:
            if username:
                return f"sudo useradd -m {username}"
            return "sudo useradd -m USERNAME"
        elif "usuń" in action or "userdel" in action or "delete user" in full_text:
            if username:
                return f"sudo userdel -r {username}"
            return "sudo userdel -r USERNAME"
        elif "modyfikuj" in action or "usermod" in action:
            if username and group:
                return f"sudo usermod -aG {group} {username}"
            return "sudo usermod -aG GROUP USERNAME"
        elif "groupadd" in action or "dodaj grupę" in full_text:
            if group:
                return f"sudo groupadd {group}"
            return "sudo groupadd GROUP"
        elif "passwd" in action or "hasło" in full_text:
            if username:
                return f"sudo passwd {username}"
            return "passwd"
        elif "su" in action or "przełącz" in full_text:
            if username:
                return f"su - {username}"
            return "su -"
        
        return "whoami"

    def _generate_hardware_info(self, entities: dict[str, Any]) -> str:
        """Generate hardware info command."""
        action = entities.get("action", "")
        device = entities.get("device", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        if "lscpu" in full_text or "cpu" in action or "procesor" in full_text:
            return "lscpu"
        elif "lspci" in full_text or "pci" in action:
            return "lspci"
        elif "lsusb" in full_text or "usb" in action:
            return "lsusb"
        elif "lshw" in full_text or "hardware" in action or "sprzęt" in full_text:
            return "sudo lshw -short"
        elif "dmidecode" in full_text or "bios" in action:
            return "sudo dmidecode -t system"
        elif "pamięć" in full_text or "ram" in full_text or "memory" in action:
            return "free -h"
        elif "hdparm" in full_text or "dysk twardy" in full_text:
            if device:
                return f"sudo hdparm -I {device}"
            return "sudo hdparm -I /dev/sda"
        elif "smartctl" in full_text or "smart" in action or "zdrowie" in full_text:
            if device:
                return f"sudo smartctl -a {device}"
            return "sudo smartctl -a /dev/sda"
        
        return "lscpu"

    def _generate_disk_management(self, entities: dict[str, Any]) -> str:
        """Generate disk management command."""
        action = entities.get("action", "")
        device = entities.get("device", "")
        mountpoint = entities.get("mountpoint", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        if "lsblk" in full_text or "lista dysków" in full_text or "list disks" in action:
            return "lsblk -f"
        elif "blkid" in full_text or "uuid" in full_text:
            return "blkid"
        elif "mount" in action and "umount" not in action:
            if device and mountpoint:
                return f"sudo mount {device} {mountpoint}"
            return "mount"
        elif "umount" in action or "odmontuj" in full_text:
            if mountpoint:
                return f"sudo umount {mountpoint}"
            elif device:
                return f"sudo umount {device}"
            return "sudo umount /mnt"
        elif "fdisk" in full_text or "partycja" in full_text:
            if device:
                return f"sudo fdisk -l {device}"
            return "sudo fdisk -l"
        elif "mkfs" in full_text or "formatuj" in full_text:
            if device:
                return f"sudo mkfs.ext4 {device}"
            return "sudo mkfs.ext4 /dev/sdX"
        elif "fsck" in full_text or "sprawdź" in full_text:
            if device:
                return f"sudo fsck {device}"
            return "sudo fsck /dev/sda1"
        
        return "lsblk"

    def _generate_package_management(self, entities: dict[str, Any]) -> str:
        """Generate package management command."""
        action = entities.get("action", "")
        package = entities.get("package", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Detect package manager from context
        if "yum" in full_text:
            pm = "yum"
        elif "dnf" in full_text:
            pm = "dnf"
        elif "pacman" in full_text:
            pm = "pacman"
        elif "snap" in full_text:
            pm = "snap"
        elif "flatpak" in full_text:
            pm = "flatpak"
        elif "pip" in full_text:
            pm = "pip"
        else:
            pm = "apt"
        
        if "zainstaluj" in action or "install" in action:
            if pm == "apt":
                return f"sudo apt install -y {package}" if package else "sudo apt install -y PACKAGE"
            elif pm == "yum":
                return f"sudo yum install -y {package}" if package else "sudo yum install -y PACKAGE"
            elif pm == "dnf":
                return f"sudo dnf install -y {package}" if package else "sudo dnf install -y PACKAGE"
            elif pm == "pacman":
                return f"sudo pacman -S {package}" if package else "sudo pacman -S PACKAGE"
            elif pm == "snap":
                return f"sudo snap install {package}" if package else "sudo snap install PACKAGE"
            elif pm == "pip":
                return f"pip install {package}" if package else "pip install PACKAGE"
        elif "odinstaluj" in action or "remove" in action or "usuń" in action:
            if pm == "apt":
                return f"sudo apt remove {package}" if package else "sudo apt remove PACKAGE"
            elif pm == "pip":
                return f"pip uninstall {package}" if package else "pip uninstall PACKAGE"
        elif "aktualizuj" in action or "update" in action or "upgrade" in action:
            if pm == "apt":
                return "sudo apt update && sudo apt upgrade -y"
            elif pm == "yum":
                return "sudo yum update -y"
            elif pm == "dnf":
                return "sudo dnf update -y"
            elif pm == "pacman":
                return "sudo pacman -Syu"
        elif "szukaj" in action or "search" in action:
            if pm == "apt":
                return f"apt search {package}" if package else "apt search PATTERN"
        elif "lista" in action or "list" in action:
            if pm == "apt":
                return "apt list --installed"
            elif pm == "pip":
                return "pip list"
        
        return "sudo apt update"

    def _generate_service_management(self, entities: dict[str, Any]) -> str:
        """Generate service management command."""
        action = entities.get("action", "")
        service_name = entities.get("service_name", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Detect service from text
        if not service_name:
            for svc in ["nginx", "apache2", "mysql", "postgresql", "docker", "ssh", "redis"]:
                if svc in full_text:
                    service_name = svc
                    break
        
        if "status" in action or "status" in full_text:
            if service_name:
                return f"systemctl status {service_name}"
            return "systemctl status"
        elif "uruchom" in action or "start" in action:
            if service_name:
                return f"sudo systemctl start {service_name}"
            return "sudo systemctl start SERVICE"
        elif "zatrzymaj" in action or "stop" in action:
            if service_name:
                return f"sudo systemctl stop {service_name}"
            return "sudo systemctl stop SERVICE"
        elif "restart" in action or "restartuj" in full_text:
            if service_name:
                return f"sudo systemctl restart {service_name}"
            return "sudo systemctl restart SERVICE"
        elif "enable" in action or "włącz" in full_text:
            if service_name:
                return f"sudo systemctl enable {service_name}"
            return "sudo systemctl enable SERVICE"
        elif "disable" in action or "wyłącz" in full_text:
            if service_name:
                return f"sudo systemctl disable {service_name}"
            return "sudo systemctl disable SERVICE"
        elif "lista" in action or "list" in action:
            return "systemctl list-units --type=service"
        elif "journalctl" in full_text or "logi" in full_text:
            if service_name:
                return f"journalctl -u {service_name} -f"
            return "journalctl -f"
        elif "crontab" in full_text or "cron" in action:
            if "edytuj" in full_text or "edit" in action:
                return "crontab -e"
            return "crontab -l"
        
        return "systemctl list-units --type=service"

    def _generate_text_file_ops(self, entities: dict[str, Any]) -> str:
        """Generate text file operations command."""
        action = entities.get("action", "")
        file = entities.get("file", "")
        lines = entities.get("lines", "10")
        full_text = str(entities.get("_full_text", "")).lower()
        
        if "cat" in action or "pokaż plik" in full_text or "wyświetl plik" in full_text:
            if file:
                return f"cat {file}"
            return "cat FILE"
        elif "head" in action or "pierwsze linie" in full_text:
            if file:
                return f"head -n {lines} {file}"
            return f"head -n {lines} FILE"
        elif "tail" in action or "ostatnie linie" in full_text:
            if "śledź" in full_text or "follow" in action:
                if file:
                    return f"tail -f {file}"
                return "tail -f FILE"
            if file:
                return f"tail -n {lines} {file}"
            return f"tail -n {lines} FILE"
        elif "less" in action:
            if file:
                return f"less {file}"
            return "less FILE"
        elif "wc" in action or "policz" in full_text:
            if "linie" in full_text or "lines" in action:
                if file:
                    return f"wc -l {file}"
                return "wc -l FILE"
            if file:
                return f"wc {file}"
            return "wc FILE"
        elif "sort" in action or "sortuj" in full_text:
            if file:
                return f"sort {file}"
            return "sort FILE"
        elif "uniq" in action or "unikalne" in full_text:
            if file:
                return f"sort {file} | uniq"
            return "sort FILE | uniq"
        elif "cut" in action:
            if file:
                return f"cut -d',' -f1 {file}"
            return "cut -d',' -f1 FILE"
        elif "tr" in action:
            return "tr '[:lower:]' '[:upper:]'"
        
        return "cat FILE"

    def _generate_checksum(self, entities: dict[str, Any]) -> str:
        """Generate checksum/encoding command."""
        action = entities.get("action", "")
        file = entities.get("file", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        if "md5" in action or "md5" in full_text:
            if file:
                return f"md5sum {file}"
            return "md5sum FILE"
        elif "sha256" in action or "sha256" in full_text:
            if file:
                return f"sha256sum {file}"
            return "sha256sum FILE"
        elif "sha1" in action or "sha1" in full_text:
            if file:
                return f"sha1sum {file}"
            return "sha1sum FILE"
        elif "base64" in action or "base64" in full_text:
            if "dekoduj" in full_text or "decode" in action:
                if file:
                    return f"base64 -d {file}"
                return "base64 -d FILE"
            if file:
                return f"base64 {file}"
            return "base64 FILE"
        elif "xxd" in action or "hex" in full_text:
            if file:
                return f"xxd {file}"
            return "xxd FILE"
        
        return "md5sum FILE"

    def _generate_terminal_session(self, entities: dict[str, Any]) -> str:
        """Generate terminal multiplexer command."""
        action = entities.get("action", "")
        session_name = entities.get("session_name", "")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Detect tool
        if "screen" in full_text:
            tool = "screen"
        elif "byobu" in full_text:
            tool = "byobu"
        else:
            tool = "tmux"
        
        if "nowa" in action or "new" in action or "utwórz" in full_text:
            if tool == "tmux":
                if session_name:
                    return f"tmux new -s {session_name}"
                return "tmux new -s session"
            elif tool == "screen":
                if session_name:
                    return f"screen -S {session_name}"
                return "screen -S session"
        elif "lista" in action or "list" in action:
            if tool == "tmux":
                return "tmux ls"
            elif tool == "screen":
                return "screen -ls"
        elif "dołącz" in action or "attach" in action:
            if tool == "tmux":
                if session_name:
                    return f"tmux attach -t {session_name}"
                return "tmux attach"
            elif tool == "screen":
                if session_name:
                    return f"screen -r {session_name}"
                return "screen -r"
        elif "zamknij" in action or "kill" in action:
            if tool == "tmux":
                if session_name:
                    return f"tmux kill-session -t {session_name}"
                return "tmux kill-session"
        
        return "tmux ls"

    def validate_syntax(self, command: str) -> dict[str, Any]:
        """Validate shell command syntax."""
        errors = []
        warnings = []

        # Check for unclosed quotes
        single_quotes = command.count("'")
        double_quotes = command.count('"')
        if single_quotes % 2 != 0:
            errors.append("Unclosed single quote")
        if double_quotes % 2 != 0:
            errors.append("Unclosed double quote")

        # Check for unclosed parentheses/braces
        if command.count("(") != command.count(")"):
            errors.append("Unbalanced parentheses")
        if command.count("{") != command.count("}"):
            errors.append("Unbalanced braces")
        if command.count("[") != command.count("]"):
            errors.append("Unbalanced brackets")

        # Check pipe depth
        pipe_count = command.count("|")
        policy: ShellSafetyPolicy = self.config.safety_policy  # type: ignore
        if pipe_count > policy.max_pipe_depth:
            warnings.append(f"Deep pipe chain ({pipe_count} pipes)")

        # Check for common mistakes
        if "rm -rf *" in command:
            warnings.append("Dangerous: rm -rf with wildcard")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check_safety(self, command: str) -> dict[str, Any]:
        """Check shell command against safety policy."""
        policy: ShellSafetyPolicy = self.config.safety_policy  # type: ignore

        # Check blocked commands
        command_lower = command.lower()
        for blocked in policy.blocked_commands:
            if blocked.lower() in command_lower:
                return {
                    "allowed": False,
                    "reason": f"Command contains blocked pattern: {blocked}",
                }

        # Check sudo
        if not policy.allow_sudo and command.strip().startswith("sudo"):
            return {
                "allowed": False,
                "reason": "sudo is not allowed by safety policy",
            }

        # Check pipe to shell
        if not policy.allow_pipe_to_shell:
            dangerous_pipes = ["| sh", "| bash", "| zsh", "|sh", "|bash"]
            for dp in dangerous_pipes:
                if dp in command:
                    return {
                        "allowed": False,
                        "reason": "Piping to shell is not allowed",
                    }

        # Check blocked directories
        try:
            argv = shlex.split(command)
        except ValueError:
            argv = command.split()

        for blocked_dir in policy.blocked_directories:
            for arg in argv:
                value = arg
                if "=" in arg:
                    value = arg.split("=", 1)[1]

                if blocked_dir == "/":
                    if value == "/":
                        return {
                            "allowed": False,
                            "reason": f"Operations on {blocked_dir} are not allowed",
                        }
                    continue

                if value == blocked_dir or value.startswith(blocked_dir + "/"):
                    return {
                        "allowed": False,
                        "reason": f"Operations on {blocked_dir} are not allowed",
                    }

        # Check commands requiring confirmation
        requires_confirmation = False
        for pattern in policy.require_confirmation_for:
            if pattern.lower() in command_lower:
                requires_confirmation = True
                break

        return {
            "allowed": True,
            "requires_confirmation": requires_confirmation,
        }

    def _generate_cat(self, entities: dict[str, Any]) -> str:
        """Generate cat command for viewing file contents."""
        file = entities.get("file", entities.get("path", entities.get("filename", "")))
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Extract file path from full text if not in entities
        if not file and full_text:
            import re
            # Match common file patterns
            match = re.search(r'([/\w.-]+\.\w+)', full_text)
            if match:
                file = match.group(1)
        
        if file:
            return f"cat {shlex.quote(file)}"
        return "cat"

    def _generate_head_tail(self, entities: dict[str, Any]) -> str:
        """Generate head or tail command."""
        action = entities.get("action", "head")
        file = entities.get("file", entities.get("path", ""))
        lines = entities.get("lines", entities.get("count", "10"))
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Determine head or tail from full text
        if "tail" in full_text or "ostatni" in full_text or "końc" in full_text:
            cmd = "tail"
        elif "head" in full_text or "pierwsz" in full_text or "począt" in full_text:
            cmd = "head"
        else:
            cmd = action if action in ("head", "tail") else "head"
        
        # Extract file from full text if not in entities
        if not file and full_text:
            import re
            match = re.search(r'([/\w.-]+\.\w+)', full_text)
            if match:
                file = match.group(1)
        
        # Extract line count from full text
        if full_text:
            import re
            match = re.search(r'(\d+)\s*(lini|line)', full_text)
            if match:
                lines = match.group(1)
        
        if file:
            return f"{cmd} -n {lines} {shlex.quote(file)}"
        return f"{cmd} -n {lines}"

    def _generate_wc(self, entities: dict[str, Any]) -> str:
        """Generate wc command for counting lines/words/chars."""
        file = entities.get("file", entities.get("path", ""))
        mode = entities.get("mode", "lines")
        full_text = str(entities.get("_full_text", "")).lower()
        
        # Extract file from full text if not in entities
        if not file and full_text:
            import re
            match = re.search(r'([/\w.-]+\.\w+)', full_text)
            if match:
                file = match.group(1)
        
        # Determine counting mode
        flag = "-l"  # default: lines
        if "słow" in full_text or "word" in full_text:
            flag = "-w"
        elif "znak" in full_text or "char" in full_text or "byte" in full_text:
            flag = "-c"
        
        if file:
            return f"wc {flag} {shlex.quote(file)}"
        return f"wc {flag}"

    def check_tool_availability(self, command: str) -> dict[str, Any]:
        """Check if required tools are available."""
        # Extract first command from pipeline
        first_cmd = command.split("|")[0].strip().split()[0]

        # Check if tool exists
        if shutil.which(first_cmd):
            return {"available": True, "tool": first_cmd}
        else:
            return {
                "available": False,
                "tool": first_cmd,
                "suggestion": f"Install {first_cmd} or check PATH",
            }
