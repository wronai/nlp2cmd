"""
Docker DSL Adapter for NLP2CMD.

Supports Docker CLI and Docker Compose operations.
"""

from __future__ import annotations

from nlp2cmd.utils.yaml_compat import yaml
from dataclasses import dataclass, field
from typing import Any, Optional

import re

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy

# Polish Language Support Integration
try:
    from ..polish_support import get_polish_support
    polish_support = get_polish_support()
    POLISH_SUPPORT_ENABLED = True
except ImportError:
    polish_support = None
    POLISH_SUPPORT_ENABLED = False



@dataclass
class DockerSafetyPolicy(SafetyPolicy):
    """Docker-specific safety policy."""

    allow_privileged: bool = False
    allow_host_network: bool = False
    allow_host_pid: bool = False
    allow_volume_mounts: list[str] = field(default_factory=list)
    blocked_images: list[str] = field(default_factory=list)
    require_image_tag: bool = True
    max_memory: str = "4g"
    max_cpus: float = 2.0

    def check_command(self, command: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Check Docker command against safety policy.

        Exposed for DynamicAdapter compatibility (it calls safety_policy.check_command if present).
        """
        # Check privileged mode
        if not self.allow_privileged and "--privileged" in command:
            return {
                "allowed": False,
                "reason": "Privileged mode is not allowed",
                "risk_level": "high",
            }

        # Check host network
        if not self.allow_host_network and "--network host" in command:
            return {
                "allowed": False,
                "reason": "Host network mode is not allowed",
                "risk_level": "high",
            }

        # Check host PID
        if not self.allow_host_pid and "--pid host" in command:
            return {
                "allowed": False,
                "reason": "Host PID mode is not allowed",
                "risk_level": "high",
            }

        # Check blocked images
        for blocked in self.blocked_images:
            if blocked in command:
                return {
                    "allowed": False,
                    "reason": f"Image '{blocked}' is blocked",
                    "risk_level": "high",
                }

        # Check for dangerous volume mounts
        dangerous_mounts = ["-v /:/", "-v /etc:/", "-v /var/run/docker.sock"]
        for mount in dangerous_mounts:
            if mount in command:
                return {
                    "allowed": False,
                    "reason": f"Dangerous volume mount detected: {mount}",
                    "risk_level": "high",
                }

        return {"allowed": True, "requires_confirmation": False, "risk_level": "low"}


@dataclass
class ComposeContext:
    """Docker Compose context."""

    services: dict[str, Any] = field(default_factory=dict)
    networks: dict[str, Any] = field(default_factory=dict)
    volumes: dict[str, Any] = field(default_factory=dict)
    version: str = "3.8"


class DockerAdapter(BaseDSLAdapter):
    """
    Docker adapter for CLI and Compose operations.

    Transforms natural language into Docker commands
    with support for both Docker CLI and Docker Compose.
    """

    DSL_NAME = "docker"
    DSL_VERSION = "1.0"

    INTENTS = {
        "container_run": {
            "patterns": ["uruchom kontener", "run container", "docker run", "start container", "run", "start"],
            "required_entities": ["image"],
            "optional_entities": ["name", "ports", "volumes", "environment", "network"],
        },
        "container_stop": {
            "patterns": ["zatrzymaj", "stop", "docker stop", "stop container"],
            "required_entities": ["container"],
        },
        "container_remove": {
            "patterns": ["usuń kontener", "remove container", "docker rm", "remove"],
            "required_entities": ["container"],
        },
        "image_build": {
            "patterns": ["zbuduj obraz", "build image", "docker build", "build"],
            "required_entities": ["tag"],
            "optional_entities": ["dockerfile", "context"],
        },
        "image_pull": {
            "patterns": ["pobierz obraz", "pull image", "docker pull"],
            "required_entities": ["image"],
        },
        "compose_up": {
            "patterns": ["docker-compose up", "compose up", "uruchom stack", "up"],
            "optional_entities": ["services", "detach", "build"],
        },
        "compose_down": {
            "patterns": ["docker-compose down", "compose down", "zatrzymaj stack", "down"],
            "optional_entities": ["volumes", "images"],
        },
        "logs": {
            "patterns": ["logi", "logs", "docker logs", "show logs", "log"],
            "required_entities": ["container"],
            "optional_entities": ["tail", "follow"],
        },
        "exec": {
            "patterns": ["exec", "execute", "wejdź do kontenera", "execute command"],
            "required_entities": ["container", "command"],
        },
        "list": {
            "patterns": ["pokaż", "list", "ls", "ps", "show", "show all", "list all"],
            "optional_entities": ["type", "all", "filter"],
        },
        "prune": {
            "patterns": ["wyczyść", "prune", "clean"],
            "optional_entities": ["type", "force"],
        },
    }

    def __init__(
        self,
        compose_context: Optional[dict[str, Any]] = None,
        safety_policy: Optional[DockerSafetyPolicy] = None,
        config: Optional[AdapterConfig] = None,
    ):
        """
        Initialize Docker adapter.

        Args:
            compose_context: Docker Compose context (services, networks, volumes)
            safety_policy: Docker-specific safety policy
            config: Adapter configuration
        """
        super().__init__(config, safety_policy or DockerSafetyPolicy())
        self.compose = self._parse_compose_context(compose_context or {})

    def _parse_compose_context(self, ctx: dict[str, Any]) -> ComposeContext:
        """Parse compose context."""
        return ComposeContext(
            services=ctx.get("services", {}),
            networks=ctx.get("networks", {}),
            volumes=ctx.get("volumes", {}),
            version=ctx.get("version", "3.8"),
        )

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate Docker command from execution plan."""
        intent = plan.get("intent", "")
        entities = plan.get("entities", {})

        generators = {
            "container_run": self._generate_run,
            "container_stop": self._generate_stop,
            "container_remove": self._generate_remove,
            "image_build": self._generate_build,
            "image_pull": self._generate_pull,
            "compose_up": self._generate_compose_up,
            "compose_down": self._generate_compose_down,
            "logs": self._generate_logs,
            "exec": self._generate_exec,
            "list": self._generate_list,
            "prune": self._generate_prune,
            "container_management": self._generate_container_management,
        }

        generator = generators.get(intent)
        if generator:
            return generator(entities)

        return f"# Unknown Docker intent: {intent}"

    def _generate_run(self, entities: dict[str, Any]) -> str:
        """Generate docker run command."""
        image = entities.get("image", "")
        name = entities.get("name", "")
        ports = entities.get("ports", [])
        volumes = entities.get("volumes", [])
        environment = entities.get("environment", {})
        network = entities.get("network", "")
        detach = entities.get("detach", True)
        command = entities.get("command", "")

        parts = ["docker run"]

        if detach:
            parts.append("-d")

        if name:
            parts.append(f"--name {name}")

        for port in ports:
            if isinstance(port, dict):
                parts.append(f"-p {port.get('host')}:{port.get('container')}")
            else:
                parts.append(f"-p {port}")

        for volume in volumes:
            if isinstance(volume, dict):
                parts.append(f"-v {volume.get('host')}:{volume.get('container')}")
            else:
                parts.append(f"-v {volume}")

        for key, value in environment.items():
            parts.append(f"-e {key}={value}")

        if network:
            parts.append(f"--network {network}")

        # Apply safety policy constraints
        policy: DockerSafetyPolicy = self.config.safety_policy  # type: ignore
        if policy.max_memory:
            parts.append(f"--memory={policy.max_memory}")
        if policy.max_cpus:
            parts.append(f"--cpus={policy.max_cpus}")

        # Add image (with tag if required)
        if policy.require_image_tag and ":" not in image:
            image = f"{image}:latest"
        parts.append(image)

        if command:
            parts.append(command)

        return " ".join(parts)

    def _generate_stop(self, entities: dict[str, Any]) -> str:
        """Generate docker stop command."""
        container = entities.get("container", "")
        timeout = entities.get("timeout", "")

        cmd = f"docker stop {container}"
        if timeout:
            cmd = f"docker stop -t {timeout} {container}"

        return cmd

    def _generate_remove(self, entities: dict[str, Any]) -> str:
        """Generate docker rm command."""
        container = entities.get("container", "")
        force = entities.get("force", False)
        volumes = entities.get("remove_volumes", False)

        parts = ["docker rm"]
        if force:
            parts.append("-f")
        if volumes:
            parts.append("-v")
        parts.append(container)

        return " ".join(parts)

    def _generate_build(self, entities: dict[str, Any]) -> str:
        """Generate docker build command."""
        tag = entities.get("tag", "myimage:latest")
        dockerfile = entities.get("dockerfile", "")
        context = entities.get("context", ".")
        no_cache = entities.get("no_cache", False)
        build_args = entities.get("build_args", {})

        parts = ["docker build"]

        parts.append(f"-t {tag}")

        if dockerfile:
            parts.append(f"-f {dockerfile}")

        if no_cache:
            parts.append("--no-cache")

        for key, value in build_args.items():
            parts.append(f"--build-arg {key}={value}")

        parts.append(context)

        return " ".join(parts)

    def _generate_pull(self, entities: dict[str, Any]) -> str:
        """Generate docker pull command."""
        image = entities.get("image", "")

        policy: DockerSafetyPolicy = self.config.safety_policy  # type: ignore
        if policy.require_image_tag and ":" not in image:
            image = f"{image}:latest"

        return f"docker pull {image}"

    def _generate_compose_up(self, entities: dict[str, Any]) -> str:
        """Generate docker-compose up command."""
        services = entities.get("services", [])
        detach = entities.get("detach", True)
        build = entities.get("build", False)
        file = entities.get("file", "")

        parts = ["docker-compose"]

        if file:
            parts.append(f"-f {file}")

        parts.append("up")

        if detach:
            parts.append("-d")

        if build:
            parts.append("--build")

        if services:
            parts.extend(services)

        return " ".join(parts)

    def _generate_compose_down(self, entities: dict[str, Any]) -> str:
        """Generate docker-compose down command."""
        volumes = entities.get("volumes", False)
        images = entities.get("images", "")
        file = entities.get("file", "")

        parts = ["docker-compose"]

        if file:
            parts.append(f"-f {file}")

        parts.append("down")

        if volumes:
            parts.append("-v")

        if images:
            parts.append(f"--rmi {images}")

        return " ".join(parts)

    def _generate_logs(self, entities: dict[str, Any]) -> str:
        """Generate docker logs command."""
        container = entities.get("container", "")
        tail = entities.get("tail", 100)
        follow = entities.get("follow", True)
        timestamps = entities.get("timestamps", False)

        parts = ["docker logs"]

        if follow:
            parts.append("-f")

        if timestamps:
            parts.append("-t")

        parts.append(f"--tail={tail}")
        parts.append(container)

        return " ".join(parts)

    def _generate_exec(self, entities: dict[str, Any]) -> str:
        """Generate docker exec command."""
        container = entities.get("container", "")
        command = entities.get("command", "/bin/bash")
        interactive = entities.get("interactive", True)
        user = entities.get("user", "")
        workdir = entities.get("workdir", "")

        parts = ["docker exec"]

        if interactive:
            parts.append("-it")

        if user:
            parts.append(f"-u {user}")

        if workdir:
            parts.append(f"-w {workdir}")

        parts.append(container)
        parts.append(command)

        return " ".join(parts)

    def _generate_list(self, entities: dict[str, Any]) -> str:
        """Generate docker list command."""
        list_type = entities.get("type", "containers")
        all_items = entities.get("all", False)
        filter_expr = entities.get("filter", "")
        format_str = entities.get("format", "")

        if list_type == "images":
            cmd = "docker images"
        elif list_type == "volumes":
            cmd = "docker volume ls"
        elif list_type == "networks":
            cmd = "docker network ls"
        else:
            cmd = "docker ps"

        if all_items and list_type == "containers":
            cmd += " -a"

        if filter_expr:
            cmd += f' --filter "{filter_expr}"'

        if format_str:
            cmd += f' --format "{format_str}"'

        return cmd

    def _generate_prune(self, entities: dict[str, Any]) -> str:
        """Generate docker prune command."""
        prune_type = entities.get("type", "system")
        force = entities.get("force", True)
        all_items = entities.get("all", False)

        types = {
            "system": "docker system prune",
            "containers": "docker container prune",
            "images": "docker image prune",
            "volumes": "docker volume prune",
            "networks": "docker network prune",
        }

        cmd = types.get(prune_type, "docker system prune")

        if force:
            cmd += " -f"

        if all_items and prune_type in ["images", "system"]:
            cmd += " -a"

        return cmd

    def _generate_container_management(self, entities: dict[str, Any]) -> str:
        """Generate complex container management script."""
        actions = entities.get("actions", [])
        filters = entities.get("filters", [])

        script_lines = [
            "#!/bin/bash",
            "# Container management script",
            "set -e",
            "",
        ]

        # Build filter for finding containers
        filter_parts = []
        for f in filters:
            attr = f.get("attribute", "")
            op = f.get("operator", "")
            value = f.get("value", "")

            if attr == "running_time":
                script_lines.extend([
                    f"# Filter: containers running > {value}",
                    f'CONTAINERS=$(docker ps --format "{{{{.ID}}}} {{{{.RunningFor}}}}" | \\',
                    f'    awk \'$2 ~ /hours|days/ {{ print $1 }}\')',
                    "",
                ])
            elif attr == "status":
                filter_parts.append(f'--filter "status={value}"')

        if "stop_containers" in actions:
            script_lines.extend([
                'if [ -n "$CONTAINERS" ]; then',
                '    echo "Stopping containers..."',
                "    echo $CONTAINERS | xargs docker stop",
            ])

        if "remove_images" in actions:
            script_lines.extend([
                "",
                '    echo "Removing associated images..."',
                "    for c in $CONTAINERS; do",
                '        img=$(docker inspect --format="{{.Image}}" $c 2>/dev/null)',
                '        [ -n "$img" ] && docker rmi $img 2>/dev/null || true',
                "    done",
            ])

        if "stop_containers" in actions:
            script_lines.extend([
                "else",
                '    echo "No containers matching criteria"',
                "fi",
            ])

        return "\n".join(script_lines)

    def generate_compose_file(self, spec: dict[str, Any]) -> str:
        """Generate docker-compose.yml content."""
        compose = {
            "version": spec.get("version", "3.8"),
            "services": {},
        }

        for service_name, service_config in spec.get("services", {}).items():
            service = {}

            if "image" in service_config:
                service["image"] = service_config["image"]
            elif "build" in service_config:
                service["build"] = service_config["build"]

            if "ports" in service_config:
                service["ports"] = [str(p) for p in service_config["ports"]]

            if "volumes" in service_config:
                service["volumes"] = service_config["volumes"]

            if "environment" in service_config:
                service["environment"] = service_config["environment"]

            if "depends_on" in service_config:
                service["depends_on"] = service_config["depends_on"]

            if "networks" in service_config:
                service["networks"] = service_config["networks"]

            if "restart" in service_config:
                service["restart"] = service_config["restart"]

            compose["services"][service_name] = service

        if spec.get("networks"):
            compose["networks"] = spec["networks"]

        if spec.get("volumes"):
            compose["volumes"] = spec["volumes"]

        return yaml.dump(compose, default_flow_style=False, sort_keys=False)

    def validate_syntax(self, command: str) -> dict[str, Any]:
        """Validate Docker command syntax."""
        errors = []
        warnings = []

        # Check for common issues
        if command.startswith("docker run"):
            if "--name" not in command:
                warnings.append("Consider adding --name for easier container management")

            if "-d" not in command and "--detach" not in command:
                warnings.append("Container will run in foreground (add -d for background)")

        if "docker build" in command:
            if "-t" not in command and "--tag" not in command:
                errors.append("docker build requires -t/--tag")

        # Check image tags
        policy: DockerSafetyPolicy = self.config.safety_policy  # type: ignore
        if policy.require_image_tag:
            # Simple check for image without tag in run/pull commands
            parts = command.split()
            for i, part in enumerate(parts):
                if part in ["run", "pull"] and i + 1 < len(parts):
                    image = parts[i + 1]
                    if not image.startswith("-") and ":" not in image:
                        warnings.append(f"Image '{image}' has no tag, will use :latest")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check_safety(self, command: str) -> dict[str, Any]:
        """Check Docker command against safety policy."""
        policy: DockerSafetyPolicy = self.config.safety_policy  # type: ignore

        # Check privileged mode
        if not policy.allow_privileged and "--privileged" in command:
            return {
                "allowed": False,
                "reason": "Privileged mode is not allowed",
            }

        # Check host network
        if not policy.allow_host_network and "--network host" in command:
            return {
                "allowed": False,
                "reason": "Host network mode is not allowed",
            }

        # Check host PID
        if not policy.allow_host_pid and "--pid host" in command:
            return {
                "allowed": False,
                "reason": "Host PID mode is not allowed",
            }

        # Check blocked images
        for blocked in policy.blocked_images:
            if blocked in command:
                return {
                    "allowed": False,
                    "reason": f"Image '{blocked}' is blocked",
                }

        # Check for dangerous volume mounts
        dangerous_mounts = ["-v /:/", "-v /etc:/", "-v /var/run/docker.sock"]
        for mount in dangerous_mounts:
            if mount in command:
                return {
                    "allowed": False,
                    "reason": f"Dangerous volume mount detected: {mount}",
                }

        return {"allowed": True}
