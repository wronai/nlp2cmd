"""
Command Line Interface for NLP2CMD.

Provides interactive REPL mode, file operations, and environment analysis.
"""

from __future__ import annotations

import json
import sys
import asyncio
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import (
    DockerAdapter,
    DQLAdapter,
    KubernetesAdapter,
    ShellAdapter,
    SQLAdapter,
    AppSpecAdapter,
)
from nlp2cmd.environment import EnvironmentAnalyzer
from nlp2cmd.feedback import FeedbackAnalyzer, FeedbackResult, FeedbackType
from nlp2cmd.schemas import SchemaRegistry
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator
from nlp2cmd.monitoring import measure_resources, format_last_metrics, estimate_token_cost, format_token_estimate


console = Console()


class NLP2CMDGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]):
        if args:
            first = args[0]
            if not first.startswith("-") and self.get_command(ctx, first) is None:
                text_parts: list[str] = []
                option_parts: list[str] = []
                seen_option = False
                for a in args:
                    if not seen_option and a.startswith("-"):
                        seen_option = True
                    if seen_option:
                        option_parts.append(a)
                    else:
                        text_parts.append(a)

                query_text = " ".join(text_parts).strip()

                rewritten: list[str] = []
                rewritten.extend(option_parts)
                if query_text:
                    rewritten.extend(["--query", query_text])
                args = rewritten

        return super().parse_args(ctx, args)


def _shell_env_context(context: dict[str, Any]) -> dict[str, Any]:
    os_info = context.get("os") or {}
    shell_info = context.get("shell") or {}
    env_vars = context.get("env_vars") or {}

    os_name = os_info.get("system")
    if isinstance(os_name, str):
        os_name = os_name.lower()
    else:
        os_name = "linux"

    return {
        "os": os_name,
        "distro": os_info.get("release", ""),
        "shell": shell_info.get("name", "bash"),
        "available_tools": [],
        "environment_variables": env_vars,
    }


def get_adapter(dsl: str, context: dict[str, Any]):
    """Get the appropriate adapter for the DSL type."""
    adapters = {
        "sql": lambda: SQLAdapter(dialect="postgresql"),
        "shell": lambda: ShellAdapter(environment_context=_shell_env_context(context)),
        "docker": lambda: DockerAdapter(),
        "kubernetes": lambda: KubernetesAdapter(),
        "dql": lambda: DQLAdapter(),
        "appspec": lambda: AppSpecAdapter(),
    }

    if dsl == "auto":
        # Default to shell for auto mode
        return ShellAdapter(environment_context=_shell_env_context(context))

    factory = adapters.get(dsl)
    if factory:
        return factory()

    raise ValueError(f"Unknown DSL: {dsl}")


class InteractiveSession:
    """Interactive REPL session with feedback loop."""

    def __init__(
        self,
        dsl: str = "auto",
        auto_repair: bool = False,
        appspec: Optional[str] = None,
    ):
        self.dsl = dsl
        self.auto_repair = auto_repair
        self.appspec = appspec

        # Initialize components
        self.env_analyzer = EnvironmentAnalyzer()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.schema_registry = SchemaRegistry()

        # Session state
        self.history: list[dict[str, Any]] = []
        self.context: dict[str, Any] = {}

        # Analyze environment
        self._analyze_environment()

    def _analyze_environment(self):
        """Analyze current environment."""
        self.context["environment"] = self.env_analyzer.analyze()

        # Detect tools
        tools = self.env_analyzer.detect_tools()
        self.context["available_tools"] = {
            name: info for name, info in tools.items() if info.available
        }

        # Find config files
        self.context["config_files"] = self.env_analyzer.find_config_files(Path.cwd())

        # Check services
        self.context["services"] = self.env_analyzer.check_services()

    def process(self, user_input: str) -> FeedbackResult:
        """Process user input and return feedback."""
        # Select adapter
        if self.dsl == "appspec":
            if not self.appspec:
                raise ValueError("--appspec is required when using --dsl appspec")
            adapter = AppSpecAdapter(appspec_path=self.appspec)
        else:
            adapter = get_adapter(self.dsl, self.context["environment"])
        nlp2cmd = NLP2CMD(adapter=adapter)

        # Transform with monitoring
        with measure_resources():
            result = nlp2cmd.transform(user_input, context=self.context)

        # Analyze feedback
        feedback = self.feedback_analyzer.analyze(
            original_input=user_input,
            generated_output=result.command,
            validation_errors=result.errors,
            validation_warnings=result.warnings,
            dsl_type=result.dsl_type,
            context=self.context,
        )

        # Store in history
        self.history.append({
            "input": user_input,
            "result": result,
            "feedback": feedback,
        })

        return feedback

    def display_feedback(self, feedback: FeedbackResult):
        """Display feedback result with formatting."""
        icons = {
            FeedbackType.SUCCESS: "✅",
            FeedbackType.SYNTAX_ERROR: "❌",
            FeedbackType.SCHEMA_MISMATCH: "⚠️",
            FeedbackType.RUNTIME_ERROR: "💥",
            FeedbackType.AMBIGUOUS_INPUT: "❓",
            FeedbackType.PARTIAL_SUCCESS: "🔶",
            FeedbackType.SECURITY_VIOLATION: "🛡️",
        }

        icon = icons.get(feedback.type, "ℹ️")

        console.print(f"\n{icon} Status: [bold]{feedback.type.value}[/bold]")
        console.print(f"📊 Confidence: {feedback.confidence:.0%}")

        if feedback.generated_output:
            console.print("\n📝 Generated command:")
            syntax = Syntax(
                feedback.generated_output,
                "bash",
                theme="monokai",
                line_numbers=False,
            )
            console.print(Panel(syntax, border_style="green"))

        if feedback.errors:
            console.print("\n[red]🔴 Errors:[/red]")
            for error in feedback.errors:
                console.print(f"   • {error}")

        if feedback.warnings:
            console.print("\n[yellow]⚠️ Warnings:[/yellow]")
            for warning in feedback.warnings:
                console.print(f"   • {warning}")

        if feedback.auto_corrections:
            console.print("\n[cyan]🔧 Auto-corrections available:[/cyan]")
            for original, fixed in feedback.auto_corrections.items():
                console.print(f"   • {original[:50]}... → {fixed[:50]}...")

        if feedback.suggestions:
            console.print("\n[blue]💡 Suggestions:[/blue]")
            for suggestion in feedback.suggestions:
                console.print(f"   {suggestion}")

        if feedback.clarification_questions:
            console.print("\n[magenta]❓ Clarification needed:[/magenta]")
            for i, question in enumerate(feedback.clarification_questions, 1):
                console.print(f"   {i}. {question}")
        
        # Always show resource metrics
        metrics_str = format_last_metrics()
        if metrics_str:
            console.print(f"\n📊 {metrics_str}")
            
            # Show token cost estimate
            try:
                from nlp2cmd.monitoring.token_costs import parse_metrics_string
                metrics = parse_metrics_string(metrics_str)
                
                if metrics.get("time_ms") is not None and metrics.get("cpu_percent") is not None and metrics.get("memory_mb") is not None:
                    token_estimate = estimate_token_cost(
                        metrics["time_ms"],
                        metrics["cpu_percent"], 
                        metrics["memory_mb"],
                        metrics.get("energy_mj")
                    )
                    token_str = format_token_estimate(token_estimate)
                    console.print(f"\n{token_str}")
            except Exception as e:
                console.print(f"\n[red]Token cost estimation failed: {e}[/red]")

    def run(self):
        """Run interactive REPL."""
        console.print(Panel.fit(
            "[bold blue]NLP2CMD Interactive Mode[/bold blue]\n"
            "Type 'help' for commands, 'exit' to quit",
            border_style="blue",
        ))

        # Show environment info
        env = self.context["environment"]
        tools = self.context["available_tools"]
        config_count = len(self.context["config_files"])

        console.print(f"\n🔍 Environment: {env['os']['system']} ({env['os'].get('release', '')})")
        console.print(f"🛠️  Tools: {', '.join(tools.keys()) or 'none detected'}")
        console.print(f"📁 Config files: {config_count}")
        console.print()

        while True:
            try:
                user_input = console.input("[bold green]nlp2cmd>[/bold green] ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    console.print("👋 Goodbye!")
                    break

                if user_input.lower() == "help":
                    self._show_help()
                    continue

                if user_input.startswith("!"):
                    self._handle_command(user_input[1:])
                    continue

                # Process input
                feedback = self.process(user_input)
                self.display_feedback(feedback)

                # Interactive correction loop
                if feedback.type != FeedbackType.SUCCESS:
                    self._correction_loop(feedback)

            except KeyboardInterrupt:
                console.print("\n👋 Interrupted. Type 'exit' to quit.")
            except EOFError:
                break

    def _show_help(self):
        """Display help information."""
        help_text = """
[bold]Commands:[/bold]
  !env          Show environment info
  !tools        List detected tools
  !files        List config files
  !history      Show command history
  !clear        Clear history

[bold]Examples:[/bold]
  Find files larger than 100MB
  Show all Docker containers
  Get users from database where city = 'Warsaw'
  Scale deployment nginx to 5 replicas
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))

    def _handle_command(self, cmd: str):
        """Handle special commands."""
        parts = cmd.split()
        command = parts[0] if parts else ""

        if command == "env":
            env = self.context["environment"]
            table = Table(title="Environment")
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("OS", f"{env['os']['system']} {env['os'].get('release', '')}")
            table.add_row("Shell", env['shell'].get('name', 'unknown'))
            table.add_row("User", env['user'].get('name', 'unknown'))
            table.add_row("CWD", env.get('cwd', ''))

            console.print(table)

        elif command == "tools":
            tools = self.context["available_tools"]
            table = Table(title="Available Tools")
            table.add_column("Tool", style="cyan")
            table.add_column("Version")
            table.add_column("Path")

            for name, info in tools.items():
                table.add_row(name, info.version or "?", info.path or "")

            console.print(table)

        elif command == "files":
            files = self.context["config_files"]
            table = Table(title="Config Files")
            table.add_column("File", style="cyan")
            table.add_column("Size")

            for f in files:
                size = f.get("size", 0)
                size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
                table.add_row(f.get("name", ""), size_str)

            console.print(table)

        elif command == "history":
            if not self.history:
                console.print("No history yet.")
            else:
                for i, item in enumerate(self.history[-10:], 1):
                    console.print(f"{i}. {item['input'][:50]}...")

        elif command == "clear":
            self.history.clear()
            console.print("History cleared.")

        else:
            console.print(f"Unknown command: {command}")

    def _correction_loop(self, feedback: FeedbackResult):
        """Interactive correction loop."""
        if feedback.type == FeedbackType.SUCCESS:
            return

        if feedback.requires_user_input:
            response = console.input("\n[yellow]Provide clarification or press Enter to skip:[/yellow] ").strip()

            if response:
                # Re-process with additional context
                self.context["user_clarification"] = response
                new_feedback = self.process(
                    f"{feedback.original_input}. {response}"
                )
                self.display_feedback(new_feedback)

        elif feedback.can_auto_fix and self.auto_repair:
            console.print("\n[cyan]Apply auto-corrections? [y/N]:[/cyan] ", end="")
            if console.input().strip().lower() == "y":
                for original, fixed in feedback.auto_corrections.items():
                    console.print(f"Applied: {fixed[:60]}...")


@click.group(cls=NLP2CMDGroup, invoke_without_command=True)
@click.option("-i", "--interactive", is_flag=True, help="Start interactive mode")
@click.option(
    "-d", "--dsl",
    type=click.Choice(["auto", "sql", "shell", "docker", "kubernetes", "dql", "appspec"]),
    default="auto",
    help="DSL type"
)
@click.option(
    "--appspec",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to an app2schema.appspec JSON file (required for --dsl appspec)",
)
@click.option("-q", "--query", help="Single query to process")
@click.option("--auto-repair", is_flag=True, help="Auto-apply repairs")
@click.option("--explain", is_flag=True, help="Explain how the result was produced")
@click.pass_context
def main(
    ctx,
    interactive: bool,
    dsl: str,
    appspec: Optional[Path],
    query: Optional[str],
    auto_repair: bool,
    explain: bool,
):
    """NLP2CMD - Natural Language to Domain-Specific Commands."""
    ctx.ensure_object(dict)
    ctx.obj["dsl"] = dsl
    ctx.obj["auto_repair"] = auto_repair

    if ctx.invoked_subcommand is None:
        if query:
            if dsl == "appspec":
                session = InteractiveSession(
                    dsl=dsl,
                    auto_repair=auto_repair,
                    appspec=str(appspec) if appspec else None,
                )
                feedback = session.process(query)
                session.display_feedback(feedback)
            elif dsl == "auto":
                with measure_resources():
                    result = asyncio.run(HybridThermodynamicGenerator().generate(query, context={}))
                    if result["source"] == "thermodynamic":
                        tr = result["result"]
                        console.print(tr.decoded_output or "")
                        if explain:
                            if tr.solution_quality:
                                console.print(f"\n✅ Feasible: {tr.solution_quality.is_feasible}")
                                if tr.solution_quality.constraint_violations:
                                    console.print("\nViolations:")
                                    for v in tr.solution_quality.constraint_violations:
                                        console.print(f"  - {v}")
                                console.print(f"\nExplanation: {tr.solution_quality.explanation}")
                                console.print(f"Optimality gap (heuristic): {tr.solution_quality.optimality_gap:.2f}")
                            console.print(f"\nEnergy: {tr.energy:.4f}")
                            console.print(f"Entropy production: {tr.entropy_production:.4f}")
                            if tr.sampler_steps is not None:
                                console.print(f"Sampler steps: {tr.sampler_steps}")
                            console.print(f"Samples: {tr.n_samples}")
                            console.print(f"Converged: {tr.converged}")
                            console.print(f"Latency: {tr.latency_ms:.1f}ms")
                    else:
                        hr = result["result"]
                        console.print(hr.command)
                        if explain:
                            console.print(f"\nSource: {hr.source}")
                            console.print(f"Domain: {hr.domain}")
                            console.print(f"Confidence: {hr.confidence:.2f}")
                            console.print(f"Latency: {hr.latency_ms:.1f}ms")
                
                # Show resource metrics for auto mode
                metrics_str = format_last_metrics()
                if metrics_str:
                    console.print(f"\n📊 {metrics_str}")
                    
                    # Show token cost estimate
                    try:
                        from nlp2cmd.monitoring.token_costs import parse_metrics_string
                        metrics = parse_metrics_string(metrics_str)
                        
                        if metrics.get("time_ms") is not None and metrics.get("cpu_percent") is not None and metrics.get("memory_mb") is not None:
                            token_estimate = estimate_token_cost(
                                metrics["time_ms"],
                                metrics["cpu_percent"], 
                                metrics["memory_mb"],
                                metrics.get("energy_mj")
                            )
                            token_str = format_token_estimate(token_estimate)
                            console.print(f"\n{token_str}")
                    except Exception as e:
                        console.print(f"\n[red]Token cost estimation failed: {e}[/red]")
            else:
                session = InteractiveSession(
                    dsl=dsl,
                    auto_repair=auto_repair,
                )
                feedback = session.process(query)
                session.display_feedback(feedback)
        elif interactive:
            session = InteractiveSession(
                dsl=dsl,
                auto_repair=auto_repair,
                appspec=str(appspec) if appspec else None,
            )
            session.run()
        else:
            console.print(ctx.get_help())


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--backup", is_flag=True, help="Create backup before repair")
@click.pass_context
def repair(ctx, file: str, backup: bool):
    """Repair a configuration file."""
    file_path = Path(file)
    registry = SchemaRegistry()

    # Detect format
    schema = registry.detect_format(file_path)
    if not schema:
        console.print(f"[red]Unknown file format: {file}[/red]")
        return

    console.print(f"🔍 Detected format: [cyan]{schema.name}[/cyan]")

    # Read content
    content = file_path.read_text()

    # Validate
    validation = registry.validate(content, schema.name.lower())

    if validation.get("errors"):
        console.print("\n[red]Errors found:[/red]")
        for error in validation["errors"]:
            console.print(f"  • {error}")

    if validation.get("warnings"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in validation["warnings"]:
            console.print(f"  • {warning}")

    # Repair
    result = registry.repair(content, schema.name.lower(), auto_fix=True)

    if result["changes"]:
        console.print("\n[cyan]Changes:[/cyan]")
        for change in result["changes"]:
            if change.get("type") == "fixed":
                console.print(f"  ✅ {change.get('reason', 'Fixed')}")
            else:
                console.print(f"  ⚠️  {change.get('reason', 'Warning')}")

        if result["repaired"]:
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                backup_path.write_text(content)
                console.print(f"\n💾 Backup: {backup_path}")

            file_path.write_text(result["content"])
            console.print(f"✅ Saved: {file}")
    else:
        console.print("\n✅ No issues found!")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, file: str):
    """Validate a configuration file."""
    file_path = Path(file)
    registry = SchemaRegistry()

    schema = registry.detect_format(file_path)
    if not schema:
        console.print(f"[red]Unknown file format: {file}[/red]")
        return

    console.print(f"🔍 Format: [cyan]{schema.name}[/cyan]")

    content = file_path.read_text()
    result = registry.validate(content, schema.name.lower())

    if result.get("valid"):
        console.print("✅ [green]Valid![/green]")
    else:
        console.print("❌ [red]Invalid[/red]")

    if result.get("errors"):
        for error in result["errors"]:
            console.print(f"  [red]• {error}[/red]")

    if result.get("warnings"):
        for warning in result["warnings"]:
            console.print(f"  [yellow]• {warning}[/yellow]")


@main.command("analyze-env")
@click.option("-o", "--output", type=click.Path(), help="Output file (JSON)")
@click.pass_context
def analyze_env(ctx, output: Optional[str]):
    """Analyze system environment."""
    analyzer = EnvironmentAnalyzer()
    report = analyzer.full_report()

    if output:
        # Convert to dict for JSON serialization
        report_dict = {
            "os": report.os_info,
            "tools": {
                name: {
                    "available": info.available,
                    "version": info.version,
                    "path": info.path,
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
            "config_files": report.config_files,
            "resources": report.resources,
            "recommendations": report.recommendations,
        }

        with open(output, "w") as f:
            json.dump(report_dict, f, indent=2)

        console.print(f"📄 Report saved: {output}")
    else:
        # Display in terminal
        console.print(Panel.fit(
            f"[bold]System:[/bold] {report.os_info['system']} {report.os_info.get('release', '')}",
            title="Environment Report",
        ))

        # Tools table
        table = Table(title="Tools")
        table.add_column("Tool")
        table.add_column("Version")
        table.add_column("Status")

        for name, info in report.tools.items():
            status = "✅" if info.available else "❌"
            table.add_row(name, info.version or "-", status)

        console.print(table)

        # Services table
        table = Table(title="Services")
        table.add_column("Service")
        table.add_column("Port")
        table.add_column("Status")

        for name, info in report.services.items():
            status = "🟢" if info.running else "🔴"
            port = str(info.port) if info.port else "-"
            table.add_row(name, port, status)

        console.print(table)

        if report.recommendations:
            console.print("\n[yellow]Recommendations:[/yellow]")
            for rec in report.recommendations:
                console.print(f"  • {rec}")


if __name__ == "__main__":
    main()
