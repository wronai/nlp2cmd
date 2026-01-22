#!/usr/bin/env python3
"""
NLP2CMD Docker Example

Demonstrates natural language to Docker command transformation
with safety policies and compose file generation.
"""

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import DockerAdapter, DockerSafetyPolicy


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

    # Create adapter
    adapter = DockerAdapter(safety_policy=safety_policy)
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

        result = nlp.transform(cmd)

        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"\nGenerated command:")
        print(f"   {result.command}")

        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

    # Docker Compose file generation
    print("\n" + "=" * 60)
    print("Docker Compose Generation")
    print("=" * 60)

    spec = {
        "version": "3.8",
        "services": {
            "web": {
                "image": "nginx:alpine",
                "ports": ["8080:80"],
                "volumes": ["./html:/usr/share/nginx/html:ro"],
                "restart": "unless-stopped",
            },
            "api": {
                "build": ".",
                "ports": ["3000:3000"],
                "environment": {
                    "NODE_ENV": "production",
                    "DATABASE_URL": "postgres://db:5432/app",
                },
                "depends_on": ["db"],
            },
            "db": {
                "image": "postgres:15",
                "volumes": ["pgdata:/var/lib/postgresql/data"],
                "environment": {
                    "POSTGRES_PASSWORD": "secret",
                    "POSTGRES_DB": "app",
                },
            },
        },
        "volumes": {"pgdata": {}},
    }

    compose_yaml = adapter.generate_compose_file(spec)
    print("\nGenerated docker-compose.yml:")
    print("-" * 40)
    print(compose_yaml)

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
        result = nlp.transform(cmd)
        print(f"Status: {result.status.value}")

        if result.errors:
            print(f"❌ Blocked: {result.errors[0]}")


if __name__ == "__main__":
    main()
