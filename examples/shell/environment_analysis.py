#!/usr/bin/env python3
"""
NLP2CMD Environment Analysis Example

Demonstrates environment analysis capabilities:
- OS and system information
- Tool detection
- Service status checking
- Configuration file discovery
- Resource monitoring
- Recommendations generation
"""

import json
from pathlib import Path

from nlp2cmd.environment import (
    EnvironmentAnalyzer,
    ToolInfo,
    ServiceInfo,
)


def format_size(gb: float) -> str:
    """Format size in human-readable format."""
    if gb >= 1000:
        return f"{gb/1000:.1f} TB"
    return f"{gb:.1f} GB"


def main():
    print("=" * 70)
    print("NLP2CMD Environment Analysis")
    print("=" * 70)

    analyzer = EnvironmentAnalyzer()

    # Section 1: Basic Environment Info
    print("\n" + "─" * 70)
    print("1. SYSTEM INFORMATION")
    print("─" * 70)

    env = analyzer.analyze()

    print(f"\n🖥️  Operating System:")
    print(f"   System:  {env['os']['system']}")
    print(f"   Release: {env['os']['release']}")
    print(f"   Machine: {env['os']['machine']}")
    print(f"   Python:  {env['os']['python_version']}")

    print(f"\n🐚 Shell:")
    print(f"   Name: {env['shell']['name']}")
    print(f"   Path: {env['shell']['path']}")

    print(f"\n👤 User:")
    print(f"   Name: {env['user']['name']}")
    print(f"   Home: {env['user']['home']}")
    print(f"   Root: {'Yes' if env['user']['is_root'] else 'No'}")

    print(f"\n📂 Working Directory:")
    print(f"   {env['cwd']}")

    # Section 2: Tool Detection
    print("\n" + "─" * 70)
    print("2. TOOL DETECTION")
    print("─" * 70)

    tools_to_check = [
        "docker", "docker-compose", "kubectl",
        "git", "python", "node",
        "psql", "mysql", "redis-cli",
        "terraform", "aws", "gcloud",
        "helm", "ansible"
    ]

    print("\n🔧 Checking available tools...")
    tools = analyzer.detect_tools(tools_to_check)

    # Group by availability
    available = []
    unavailable = []

    for name, info in tools.items():
        if info.available:
            available.append(info)
        else:
            unavailable.append(info)

    print("\n✅ Available tools:")
    for tool in available:
        version_str = f"v{tool.version}" if tool.version else "unknown version"
        config_str = f" (config: {len(tool.config_files)} files)" if tool.config_files else ""
        print(f"   • {tool.name}: {version_str}{config_str}")
        if tool.config_files:
            for cf in tool.config_files:
                print(f"     └─ {cf}")

    if unavailable:
        print("\n❌ Unavailable tools:")
        for tool in unavailable:
            print(f"   • {tool.name}")

    # Section 3: Service Status
    print("\n" + "─" * 70)
    print("3. SERVICE STATUS")
    print("─" * 70)

    print("\n🔌 Checking services...")
    services = analyzer.check_services()

    for name, info in services.items():
        status_icon = "🟢" if info.running else "🔴"
        port_str = f":{info.port}" if info.port else ""
        reachable_str = " (reachable)" if info.reachable else " (not reachable)" if info.port else ""

        print(f"   {status_icon} {name}{port_str}{reachable_str}")

    # Section 4: Configuration Files
    print("\n" + "─" * 70)
    print("4. CONFIGURATION FILES")
    print("─" * 70)

    print(f"\n📁 Scanning current directory: {Path.cwd()}")

    configs = analyzer.find_config_files(Path.cwd())

    if configs:
        print("\n📄 Found configuration files:")
        for config in configs:
            size = config.get("size", 0)
            size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            name = config.get("name", "unknown")
            fmt = config.get("format") or (Path(name).suffix.lstrip(".") or "unknown")
            print(f"   • {name}")
            print(f"     Format: {fmt}")
            print(f"     Size: {size_str}")
            print(f"     Path: {config.get('path', '')}")
    else:
        print("\n   No configuration files found in current directory")

    # Section 5: System Resources
    print("\n" + "─" * 70)
    print("5. SYSTEM RESOURCES")
    print("─" * 70)

    resources = analyzer._get_resources()
    disk = resources.get("disk", {})
    memory = resources.get("memory")

    print(f"\n💾 Disk Usage:")
    print(f"   Total:  {format_size(disk.get('total_gb', 0.0))}")
    print(f"   Used:   {format_size(disk.get('used_gb', 0.0))} ({disk.get('percent_used', 0.0):.1f}%)")
    print(f"   Free:   {format_size(disk.get('free_gb', 0.0))}")

    # Progress bar for disk
    bar_width = 30
    filled = int(disk.get("percent_used", 0.0) / 100 * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"   [{bar}]")

    if memory and memory.get("total_gb"):
        print(f"\n🧠 Memory:")
        print(f"   Total:     {format_size(memory.get('total_gb', 0.0))}")
        print(f"   Available: {format_size(memory.get('available_gb', 0.0))}")
        print(f"   Used:      {memory.get('percent_used', 0.0):.1f}%")

        # Progress bar for memory
        filled = int(memory.get("percent_used", 0.0) / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"   [{bar}]")

    # Section 6: Command Validation
    print("\n" + "─" * 70)
    print("6. COMMAND VALIDATION")
    print("─" * 70)

    commands_to_validate = [
        "docker ps",
        "kubectl get pods",
        "nonexistent-command --arg",
        "git status",
        "cd /tmp",  # Shell builtin
    ]

    print("\n🔍 Validating commands against environment:")
    for cmd in commands_to_validate:
        result = analyzer.validate_command(cmd, {"services": services})

        if result["valid"]:
            print(f"   ✅ {cmd}")
        else:
            print(f"   ⚠️  {cmd}")
            for warning in result["warnings"]:
                print(f"      └─ {warning}")

    # Section 7: Full Report
    print("\n" + "─" * 70)
    print("7. FULL ENVIRONMENT REPORT")
    print("─" * 70)

    report = analyzer.full_report()

    print("\n📊 Generating recommendations...")

    if report.recommendations:
        print("\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   • {rec}")
    else:
        print("\n   ✅ No recommendations - environment looks good!")

    # Section 8: Export Report
    print("\n" + "─" * 70)
    print("8. EXPORT REPORT")
    print("─" * 70)

    report_data = {
        "os": report.os_info,
        "tools": {
            name: {
                "available": info.available,
                "version": info.version,
                "path": info.path,
                "config_files": info.config_files,
            }
            for name, info in report.tools.items()
        },
        "services": {
            name: {
                "running": info.running,
                "port": info.port,
                "reachable": info.reachable,
            }
            for name, info in report.services.items()
        },
        "resources": report.resources,
        "config_files": [
            {
                "name": cf.get("name", "unknown"),
                "format": cf.get("format")
                or (Path(cf.get("name", "")).suffix.lstrip(".") or "unknown"),
                "path": cf.get("path", ""),
                "size": cf.get("size", 0),
            }
            for cf in report.config_files
        ],
        "recommendations": report.recommendations,
    }

    print("\n📝 Report JSON preview:")
    print("-" * 40)
    print(json.dumps(report_data, indent=2)[:500] + "...")

    print("\n💾 To save full report:")
    print("   nlp2cmd --analyze-env --output env-report.json")

    # Summary
    print("\n" + "=" * 70)
    print("ENVIRONMENT ANALYSIS SUMMARY")
    print("=" * 70)

    available_count = len([t for t in tools.values() if t.available])
    running_count = len([s for s in services.values() if s.running])
    disk_percent_used = disk.get("percent_used", 0.0)
    memory_percent_used = (memory or {}).get("percent_used", 0.0)

    print(f"""
📊 Analysis Results:

   System: {env['os']['system']} {env['os']['release']}
   Tools:  {available_count}/{len(tools)} available
   Services: {running_count}/{len(services)} running
   Disk: {disk_percent_used:.0f}% used
   Memory: {memory_percent_used:.0f}% used (if available)
   Config files: {len(configs)} found
   Recommendations: {len(report.recommendations)}

Usage in your code:
    from nlp2cmd import EnvironmentAnalyzer

    analyzer = EnvironmentAnalyzer()

    # Quick analysis
    env = analyzer.analyze()

    # Detect specific tools
    tools = analyzer.detect_tools(["docker", "kubectl"])

    # Check services
    services = analyzer.check_services()

    # Validate command
    result = analyzer.validate_command("docker ps")

    # Full report
    report = analyzer.full_report()
""")


if __name__ == "__main__":
    main()
