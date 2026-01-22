"""
Shell DSL Adapter for NLP2CMD.

Supports Bash, Zsh, Fish, and PowerShell.
"""

from __future__ import annotations

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
            "patterns": ["znajdź plik", "szukaj", "find", "search", "locate", "show files", "list files"],
            "required_entities": ["target"],
            "optional_entities": ["filters", "scope"],
        },
        "file_operation": {
            "patterns": ["kopiuj", "przenieś", "usuń", "utwórz", "copy", "move", "delete", "create", "remove", "compress"],
            "required_entities": ["operation", "target"],
            "optional_entities": ["destination"],
        },
        "process_management": {
            "patterns": ["proces", "uruchom", "zatrzymaj", "kill", "start", "stop", "process", "show processes", "top processes"],
            "required_entities": ["action"],
            "optional_entities": ["process_name", "pid"],
        },
        "process_monitoring": {
            "patterns": ["pokaż procesy", "top", "htop", "ps", "monitoruj", "show top", "memory usage", "cpu usage"],
            "required_entities": [],
            "optional_entities": ["metric", "limit", "filters"],
        },
        "network": {
            "patterns": ["ping", "curl", "wget", "port", "sieć", "network", "network status"],
            "required_entities": ["action"],
            "optional_entities": ["host", "port"],
        },
        "disk": {
            "patterns": ["dysk", "miejsce", "disk", "space", "df", "du", "disk usage", "show disk"],
            "required_entities": ["action"],
            "optional_entities": ["path"],
        },
        "archive": {
            "patterns": ["spakuj", "rozpakuj", "zip", "tar", "compress", "extract", "archive"],
            "required_entities": ["action", "target"],
            "optional_entities": ["destination", "format"],
        },
        "text_processing": {
            "patterns": ["grep", "sed", "awk", "filtruj", "wyszukaj tekst", "search text", "find text"],
            "required_entities": ["action", "pattern"],
            "optional_entities": ["file", "options"],
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
            distro=ctx.get("distro", "ubuntu"),
            shell=ctx.get("shell", self.shell_type),
            available_tools=ctx.get("available_tools", []),
            environment_variables=ctx.get("environment_variables", {}),
        )

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate shell command from execution plan."""
        intent = plan.get("intent", "")
        entities = plan.get("entities", {})

        generators = {
            "file_search": self._generate_file_search,
            "file_operation": self._generate_file_operation,
            "process_management": self._generate_process_management,
            "process_monitoring": self._generate_process_monitoring,
            "network": self._generate_network,
            "disk": self._generate_disk,
            "archive": self._generate_archive,
            "text_processing": self._generate_text_processing,
            "git": self._generate_git,
            "docker": self._generate_docker,
            "container_management": self._generate_docker,  # alias
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
        scope = entities.get("scope", ".")

        # Determine if searching for files or directories
        type_flag = "-type f" if target == "files" else "-type d" if target == "directories" else ""

        cmd_parts = ["find", scope, type_flag]

        for f in filters:
            attr = f.get("attribute", "")
            op = f.get("operator", "=")
            value = f.get("value", "")

            if attr == "size":
                size_op = "+" if op in [">", ">="] else "-" if op in ["<", "<="] else ""
                cmd_parts.append(f"-size {size_op}{value}")
            elif attr == "mtime":
                # Convert days
                if isinstance(value, str) and "_days" in value:
                    days = value.replace("_days", "")
                    cmd_parts.append(f"-mtime -{days}")
                else:
                    cmd_parts.append(f"-mtime -{value}")
            elif attr == "name":
                cmd_parts.append(f'-name "{value}"')
            elif attr == "extension":
                cmd_parts.append(f'-name "*.{value}"')

        # Add useful output
        cmd_parts.append(r"-exec ls -lh {} \;")

        return " ".join(filter(None, cmd_parts))

    def _generate_file_operation(self, entities: dict[str, Any]) -> str:
        """Generate file operation command."""
        operation = entities.get("operation", "")
        target = entities.get("target", "")
        destination = entities.get("destination", "")

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

    def _generate_generic(self, entities: dict[str, Any]) -> str:
        """Generate generic command from entities."""
        command = entities.get("command", "")
        args = entities.get("args", [])

        if command:
            return f"{command} {' '.join(args)}"

        return "# Could not generate command"

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
        for blocked_dir in policy.blocked_directories:
            # Check if command operates on blocked directory
            if f" {blocked_dir}" in command or f"={blocked_dir}" in command:
                if blocked_dir == "/" and command.count("/") > 1:
                    continue  # Allow subdirectories
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
