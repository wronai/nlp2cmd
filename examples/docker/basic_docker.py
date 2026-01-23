#!/usr/bin/env python3
"""
NLP2CMD Docker Example

Demonstrates natural language to Docker command transformation
with safety policies and compose file generation.
"""

from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.adapters.docker import DockerSafetyPolicy


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
    appspec_path = Path("./generated_docker_appspec.json")
    extract_appspec_to_file("docker", appspec_path, source_type="shell", merge=True)

    adapter = AppSpecAdapter(appspec_path=appspec_path, safety_policy=safety_policy)
    nlp = NLP2CMD(adapter=adapter)

    # Example commands
    commands = [
        "Run nginx on port 8080",
        "List all running containers",
        "Show logs for web container",
        "Stop all containers",
        "Remove unused images",
        "Build image from current directory tagged as myapp",
    ]

    print("=" * 60)
    print("NLP2CMD Docker Examples")
    print("=" * 60)

    for cmd in commands:
        print(f"\n📝 Request: {cmd}")
        print("-" * 40)

        ir = nlp.transform_ir(cmd)

        print(f"Action: {ir.action_id}")
        print(f"\nGenerated command:")
        print(f"   {ir.dsl}")

        if ir.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in ir.warnings:
                print(f"   - {warning}")

    # Safety policy demo
    print("\n" + "=" * 60)
    print("Safety Policy Demo")
    print("=" * 60)

    dangerous_commands = [
        "Run container with privileged mode",
        "Mount root filesystem",
    ]

    for cmd in dangerous_commands:
        print(f"\n📝 Request: {cmd}")
        try:
            ir = nlp.transform_ir(cmd)
            print(f"Generated: {ir.dsl}")
        except Exception as e:
            print(f"❌ Blocked: {e}")


if __name__ == "__main__":
    main()
