#!/usr/bin/env python3
"""
NLP2CMD Shell Example

Demonstrates natural language to shell command transformation
with environment context and safety policies.

📚 Related Documentation:
- https://github.com/wronai/nlp2cmd/blob/main/docs/guides/user-guide.md
- https://github.com/wronai/nlp2cmd/blob/main/docs/api/README.md
- https://github.com/wronai/nlp2cmd/blob/main/THERMODYNAMIC_INTEGRATION.md

🚀 More Examples:
- https://github.com/wronai/nlp2cmd/tree/main/examples/use_cases
"""

from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.adapters.shell import ShellSafetyPolicy
from nlp2cmd.environment import EnvironmentAnalyzer


def main():
    # Analyze current environment
    env_analyzer = EnvironmentAnalyzer()
    env_info = env_analyzer.analyze()
    tools = env_analyzer.detect_tools(["docker", "git", "kubectl", "aws", "curl"])

    print("=" * 60)
    print("Environment Analysis")
    print("=" * 60)
    print(f"OS: {env_info['os']['system']} {env_info['os']['release']}")
    print(f"Shell: {env_info['shell']['name']}")
    print(f"Available tools: {[t for t, i in tools.items() if i.available]}")

    # Configure safety policy
    safety_policy = ShellSafetyPolicy(
        blocked_commands=[
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
        ],
        require_confirmation_for=[
            "rm",
            "kill",
            "shutdown",
        ],
        allow_sudo=False,
        max_pipe_depth=5,
        sandbox_mode=True,
    )

    # app2schema -> build a dynamic schema export for detected tools
    # (kept local to the example; no hardcoded keywords inside adapter)
    export_path = Path("./generated_shell_dynamic_schema.json")
    for tool_name, info in tools.items():
        if info.available:
            try:
                extract_appspec_to_file(tool_name, export_path, source_type="shell")
            except Exception:
                continue

    adapter = DynamicAdapter(
        config={"custom_options": {"load_common_commands": False}},
        safety_policy=safety_policy,
    )
    adapter.register_schema_source(str(export_path), source_type="auto")

    nlp = NLP2CMD(adapter=adapter)

    # Example commands
    commands = [
        "Find files larger than 100MB modified in the last week",
        "Show top 10 processes by memory usage",
        "List all running Docker containers",
        "Count lines of Python code in current directory",
        "Show disk usage sorted by size",
        "Find all TODO comments in source files",
        "Compress the logs directory",
        "Show git commits from last week by author",
    ]

    print("\n" + "=" * 60)
    print("NLP2CMD Shell Examples")
    print("=" * 60)

    for cmd in commands:
        print(f"\n📝 Request: {cmd}")
        print("-" * 40)

        result = nlp.transform(cmd)

        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"\nGenerated command:")
        print(f"   $ {result.command}")

        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

    # Safety policy demo
    print("\n" + "=" * 60)
    print("Safety Policy Demo")
    print("=" * 60)

    dangerous_commands = [
        "Delete everything in root directory",
        "Run command with sudo",
    ]

    for cmd in dangerous_commands:
        print(f"\n📝 Request: {cmd}")
        result = nlp.transform(cmd)
        print(f"Status: {result.status.value}")

        if not result.is_success:
            print(f"❌ Blocked: {result.errors[0] if result.errors else 'Safety violation'}")


if __name__ == "__main__":
    main()
