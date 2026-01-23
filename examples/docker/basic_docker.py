#!/usr/bin/env python3
"""
NLP2CMD Docker Example

Demonstrates natural language to Docker command transformation
with safety policies and compose file generation.
"""

from pathlib import Path

from app2schema import extract_schema_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
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

    # app2schema -> build dynamic schema export for docker CLI
    export_path = Path("./generated_docker_dynamic_schema.json")
    try:
        extract_schema_to_file("docker", export_path, source_type="shell", merge=True)
    except Exception as e:
        print(f"Failed to extract schema for docker: {e}")
        return

    adapter = DynamicAdapter(
        config={"custom_options": {"load_common_commands": False}},
        safety_policy=safety_policy,
    )
    adapter.register_schema_source(str(export_path), source_type="auto")

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

    print("=" * 60)
    print("NLP2CMD Docker Examples")
    print("=" * 60)

    for cmd in commands:
        print(f"\n📝 Request: {cmd}")
        print("-" * 40)

        result = nlp.transform(cmd)

        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"\nGenerated command:")
        print(f"   {result.command}")

        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

    # Safety policy demo
    print("\n" + "=" * 60)
    print("Safety Policy Demo")
    print("=" * 60)

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
