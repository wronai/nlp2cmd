#!/usr/bin/env python3
"""
NLP2CMD Docker Example

Demonstrates natural language to Docker command transformation
with safety policies and compose file generation.
"""

import sys
from pathlib import Path

from app2schema import extract_appspec_to_file

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_rule, print_separator
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.adapters.docker import DockerSafetyPolicy
from nlp2cmd.core import RuleBasedBackend


def main():
    # Configure safety policy
    safety_policy = DockerSafetyPolicy(
        allow_privileged=False,
        allow_host_network=False,
        allow_host_pid=False,
        blocked_images=["untrusted/*"],
        require_image_tag=True,
        max_memory="4g",
        max_cpus=2.0,
    )

    # app2schema -> build appspec for docker CLI
    commands_dir = Path("./command_schemas/commands")
    commands_dir.mkdir(parents=True, exist_ok=True)
    appspec_path = commands_dir / "docker.appspec.json"
    try:
        extract_appspec_to_file("docker", appspec_path, source_type="shell", merge=True)
    except Exception as e:
        print(f"Failed to extract AppSpec for docker: {e}")
        return

    adapter = AppSpecAdapter(appspec_path=appspec_path, safety_policy=safety_policy)

    nlp = NLP2CMD(
        adapter=adapter,
        nlp_backend=RuleBasedBackend(rules={}, config={"dsl": "docker"}),
    )

    # Example commands
    commands = [
        "Run nginx on port 8080",
        "List all running containers",
        "Show logs for web container",
        "Stop all containers",
        "Remove unused images",
        "Build image from current directory tagged as myapp",
    ]

    print_separator("NLP2CMD Docker Examples", width=60)

    for cmd in commands:
        print(f"\n📝 Request: {cmd}")
        print_rule(width=40)

        ir = nlp.transform_ir(cmd)

        print(f"Action: {ir.action_id}")
        print(f"\nGenerated command:")
        print(f"   {ir.dsl}")

    # Safety policy demo
    print_separator("Safety Policy Demo", leading_newline=True, width=60)

    dangerous_commands = [
        "docker run --privileged alpine:latest",
        "docker run --network host nginx:alpine",
        "docker run -v /:/mnt alpine:latest",
    ]

    for cmd in dangerous_commands:
        print(f"\n📝 Command: {cmd}")
        safety = adapter.check_safety(cmd)
        if not safety.get("allowed", True):
            print(f"❌ Blocked: {safety.get('reason', 'Blocked by safety policy')}")
        else:
            print("✅ Allowed")


if __name__ == "__main__":
    main()
