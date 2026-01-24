"""
Command Line Interface for NLP2CMD.

Provides interactive REPL mode, file operations, and environment analysis.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
import select
import asyncio
import shlex
from pathlib import Path
from typing import Any, Optional

try:
    import click
except Exception:  # pragma: no cover
    class _ClickStub:
        class Group:
            def parse_args(self, ctx, args):
                return args

            def get_command(self, ctx, name):
                return None

        class Context:
            pass

        class Choice:
            def __init__(self, choices):
                self.choices = choices

        class Path:
            def __init__(
                self,
                exists: bool = False,
                dir_okay: bool = True,
                file_okay: bool = True,
                path_type=None,
            ):
                self.exists = exists
                self.dir_okay = dir_okay
                self.file_okay = file_okay
                self.path_type = path_type

        @staticmethod
        def _decorator(*_args, **_kwargs):
            def _wrap(func):
                return func

            return _wrap

        group = _decorator
        option = _decorator
        argument = _decorator
        command = _decorator

        @staticmethod
        def pass_context(func):
            return func

    click = _ClickStub()

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.syntax import Syntax
except Exception:  # pragma: no cover
    class Console:  # type: ignore
        def print(self, *args, **kwargs):
            try:
                builtins_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
                builtins_print(*args)
            except Exception:
                return

        def input(self, *args, **kwargs):
            return ""

    class Panel:  # type: ignore
        def __init__(self, renderable, *args, **kwargs):
            self.renderable = renderable

    class Table:  # type: ignore
        def __init__(self, *args, **kwargs):
            return

    class Text(str):  # type: ignore
        pass

    class Syntax:  # type: ignore
        def __init__(self, code, *args, **kwargs):
            self.code = code
from nlp2cmd.utils.yaml_compat import yaml

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import (
    DockerAdapter,
    DQLAdapter,
    KubernetesAdapter,
    ShellAdapter,
    SQLAdapter,
    AppSpecAdapter,
    BrowserAdapter,
)
from nlp2cmd.pipeline_runner import PipelineRunner
from nlp2cmd.execution import ExecutionRunner, open_url
from nlp2cmd.environment import EnvironmentAnalyzer
from nlp2cmd.feedback import FeedbackAnalyzer, FeedbackResult, FeedbackType
from nlp2cmd.schemas import SchemaRegistry
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator
from nlp2cmd.monitoring import measure_resources, format_last_metrics, estimate_token_cost, format_token_estimate
from nlp2cmd.web_schema.form_data_loader import FormDataLoader


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


def _system_beep() -> None:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        return


def _timed_default_yes(
    *,
    timed_prompt: str,
    full_prompt: str,
    timeout_s: float = 1.0,
) -> str:
    if not sys.stdin.isatty():
        return "y"

    console.print(timed_prompt, end="")
    _system_beep()
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout_s)
    except Exception:
        ready = []

    if not ready:
        console.print("y")
        return "y"

    try:
        line = sys.stdin.readline()
    except Exception:
        line = ""

    resp = (line or "").strip().lower()
    if resp:
        return resp

    resp = console.input(full_prompt).strip().lower()
    return resp or "y"


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
        "browser": lambda: BrowserAdapter(),
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

        self.context["last_plan"] = result.plan.model_dump() if hasattr(result.plan, "model_dump") else {}
        self.context["transform_status"] = result.status.value if hasattr(result.status, "value") else str(result.status)
        prev = self.context.get("previous_commands")
        if not isinstance(prev, list):
            prev = []
        prev.append(result.command)
        self.context["previous_commands"] = prev

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
        out: dict[str, Any] = {
            "dsl": getattr(self, "dsl", None),
            "query": feedback.original_input,
            "status": feedback.type.value,
            "confidence": float(feedback.confidence),
            "generated_command": (feedback.generated_output or "").strip() or None,
            "errors": list(feedback.errors or []),
            "warnings": list(feedback.warnings or []),
            "suggestions": list(feedback.suggestions or []),
            "clarification_questions": list(feedback.clarification_questions or []),
        }

        if feedback.auto_corrections:
            out["auto_corrections"] = dict(feedback.auto_corrections)

        metrics_str = format_last_metrics()
        if metrics_str:
            out["resource_metrics"] = metrics_str
            try:
                from nlp2cmd.monitoring.token_costs import parse_metrics_string

                metrics = parse_metrics_string(metrics_str)
                if metrics:
                    out["resource_metrics_parsed"] = metrics

                if (
                    metrics.get("time_ms") is not None
                    and metrics.get("cpu_percent") is not None
                    and metrics.get("memory_mb") is not None
                ):
                    token_estimate = estimate_token_cost(
                        metrics["time_ms"],
                        metrics["cpu_percent"],
                        metrics["memory_mb"],
                        metrics.get("energy_mj"),
                    )
                    out["token_estimate"] = {
                        "total": int(token_estimate.total_tokens_estimate),
                        "input": int(token_estimate.input_tokens_estimate),
                        "output": int(token_estimate.output_tokens_estimate),
                        "cost_usd": float(token_estimate.estimated_cost_usd),
                        "model_tier": token_estimate.equivalent_model_tier,
                        "tokens_per_ms": float(token_estimate.tokens_per_millisecond),
                        "tokens_per_mj": float(token_estimate.tokens_per_mj),
                    }
            except Exception:
                pass

        yaml_text = yaml.safe_dump(out, sort_keys=False, allow_unicode=True)
        console.print("```yaml")
        console.print(Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False))
        console.print("```")

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
            answers: list[str] = []
            questions = list(feedback.clarification_questions or [])
            if not questions:
                questions = ["Please clarify the request."]

            max_questions = 5
            for q in questions[:max_questions]:
                response = console.input(f"\n[yellow]{q}[/yellow] ").strip()
                if response:
                    answers.append(response)

            if answers:
                combined = " ".join(answers)
                self.context["user_clarification"] = combined
                new_feedback = self.process(f"{feedback.original_input}. {combined}")
                self.display_feedback(new_feedback)
                if new_feedback.type != FeedbackType.SUCCESS:
                    if new_feedback.requires_user_input:
                        self._correction_loop(new_feedback)
                return

        elif feedback.can_auto_fix and self.auto_repair:
            console.print("\n[cyan]Apply auto-corrections? [y/N]:[/cyan] ", end="")
            if console.input().strip().lower() == "y":
                for original, fixed in feedback.auto_corrections.items():
                    console.print(f"Applied: {fixed[:60]}...")

        missing_tool = feedback.metadata.get("missing_tool") if isinstance(feedback.metadata, dict) else None
        if isinstance(missing_tool, str) and missing_tool:
            console.print(f"\n[yellow]Missing tool detected:[/yellow] {missing_tool}")
            console.print("[cyan]Show installation hints? [y/N]:[/cyan] ", end="")
            if console.input().strip().lower() == "y":
                console.print("Which package manager do you use? (apt/dnf/yum/pacman/brew/other)")
                pm = console.input("[bold green]pm>[/bold green] ").strip().lower()
                hints = {
                    "apt": f"sudo apt-get update && sudo apt-get install -y {missing_tool}",
                    "dnf": f"sudo dnf install -y {missing_tool}",
                    "yum": f"sudo yum install -y {missing_tool}",
                    "pacman": f"sudo pacman -S {missing_tool}",
                    "brew": f"brew install {missing_tool}",
                }
                cmd = hints.get(pm)
                if cmd:
                    console.print(Panel(Syntax(cmd, "bash", theme="monokai", line_numbers=False), border_style="yellow"))
                else:
                    console.print(f"Install '{missing_tool}' using your system package manager or official docs.")


def _looks_like_log_input(text: str) -> bool:
    if not text:
        return False

    if "\n" not in text:
        return False

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 3:
        return False

    score = 0
    for ln in lines[:40]:
        ll = ln.lower()

        if "traceback (most recent call last)" in ll:
            score += 4
        if re.search(r"file \".+\", line \d+", ln):
            score += 3
        if re.search(r"\b(exception|error|fatal|stack trace)\b", ll):
            score += 1
        if re.search(r"^\d{4}-\d{2}-\d{2}[ t]\d{2}:\d{2}:\d{2}", ln):
            score += 1
        if re.search(r"^\[(info|warn|warning|error|debug|trace)\]", ll):
            score += 1
        if "command not found" in ll:
            score += 2

    return score >= 4


def _interactive_followup(session: InteractiveSession, feedback: FeedbackResult) -> FeedbackResult:
    if not feedback.requires_user_input:
        return feedback

    questions = list(feedback.clarification_questions or [])
    if not questions:
        questions = ["Please clarify the request."]

    answers: list[str] = []
    for q in questions[:5]:
        response = console.input(f"\n[yellow]{q}[/yellow] ").strip()
        if response:
            answers.append(response)

    if not answers:
        return feedback

    combined = " ".join(answers)
    return session.process(f"{feedback.original_input}. {combined}")


def _handle_run_query(
    query: str,
    dsl: str,
    appspec: Optional[Path],
    auto_confirm: bool,
    execute_web: bool,
    auto_install: bool,
    auto_repair: bool,
):
    """
    Handle --run option: generate and execute command with error recovery.
    
    Features:
    - Generate command from natural language
    - Execute with real-time output
    - Detect errors and suggest recovery
    - Interactive retry loop with LLM assistance
    - Context-aware disambiguation from history
    """
    from nlp2cmd.generation.pipeline import RuleBasedPipeline
    
    console.print(Panel(
        f"[bold]{query}[/bold]",
        title="[cyan]🚀 Run Mode[/cyan]",
        border_style="cyan",
    ))
    
    # Step 0: Check for similar queries in history (disambiguation)
    if not auto_confirm:
        try:
            from nlp2cmd.context.disambiguator import CommandDisambiguator
            
            disambiguator = CommandDisambiguator(console=console)
            result = disambiguator.disambiguate(query, auto_select=False)
            
            if result.from_history and result.selected_command:
                console.print(f"\n[dim]Using previous command from history[/dim]")
                query = result.selected_query
                # Could directly use result.selected_command here
        except Exception:
            pass
    
    # Step 1: Generate command
    console.print("\n[dim]Generating command...[/dim]")
    
    adapter_map = {
        "sql": lambda: SQLAdapter(),
        "shell": lambda: ShellAdapter(),
        "docker": lambda: DockerAdapter(),
        "kubernetes": lambda: KubernetesAdapter(),
        "dql": lambda: DQLAdapter(),
        "appspec": lambda: AppSpecAdapter(appspec_path=str(appspec) if appspec else None),
        "browser": lambda: BrowserAdapter(),
    }
    
    if dsl == "auto":
        pipeline = RuleBasedPipeline()
        used_generated_command = False
        result = pipeline.process(query)

        if (not _looks_like_log_input(query)) and (not result.success) and auto_repair:
            try:
                from nlp2cmd.generation.llm_simple import LiteLLMClient

                llm = LiteLLMClient()
                result = pipeline.process_with_llm_repair(
                    query,
                    llm_client=llm,
                    persist=True,
                    max_repairs=1,
                )
            except Exception:
                pass

        if not _looks_like_log_input(query):
            steps = pipeline.process_steps(query)
            if len(steps) > 1:
                console.print("\n[cyan]Multi-step plan detected:[/cyan]")
                executable_indices: list[int] = []
                for i, step in enumerate(steps, 1):
                    cmd = (step.command or "").strip()
                    ok = bool(cmd) and not cmd.startswith("#") and step.domain != "sql"
                    if ok:
                        executable_indices.append(i)
                    console.print(f"  {i}. [{step.domain}/{step.intent}] {cmd}")

                if not executable_indices:
                    if any(s.domain == "sql" for s in steps):
                        console.print(
                            "[yellow]Only SQL steps were generated. Run Mode executes shell commands and will not execute SQL.[/yellow]"
                        )
                    else:
                        console.print("[red]✗ No executable steps could be derived[/red]")
                    return

                selected: list[int] = []
                if auto_confirm:
                    selected = list(executable_indices)
                else:
                    resp = console.input(
                        "[yellow]Execute steps? [s(elect)/a(ll)/n]: [/yellow]"
                    ).strip().lower()
                    if resp in {"n", "no", "nie"}:
                        console.print("[yellow]Cancelled by user[/yellow]")
                        return
                    if resp in {"a", "all"}:
                        selected = list(executable_indices)
                    else:
                        raw = console.input(
                            "[yellow]Enter step numbers (e.g. 1,3) or press Enter for 1st step: [/yellow]"
                        ).strip()
                        if not raw:
                            selected = [executable_indices[0]]
                        else:
                            parts = [p.strip() for p in raw.split(",") if p.strip()]
                            for p in parts:
                                if p.isdigit():
                                    n = int(p)
                                    if n in executable_indices and n not in selected:
                                        selected.append(n)

                if not selected:
                    console.print("[yellow]No steps selected[/yellow]")
                    return

                runner = ExecutionRunner(
                    console=console,
                    auto_confirm=auto_confirm,
                    max_retries=3,
                )

                for n in selected:
                    step = steps[n - 1]
                    cmd = (step.command or "").strip()
                    if not cmd or cmd.startswith("#"):
                        continue
                    console.print(Panel(
                        f"[bold]{cmd}[/bold]",
                        title=f"[cyan]Step {n}/{len(steps)}: {step.domain}/{step.intent}[/cyan]",
                        border_style="cyan",
                    ))
                    exec_result = runner.run_with_recovery(cmd, query)
                    if not exec_result.success and not auto_confirm:
                        cont = console.input("[yellow]Continue to next step? [y/N]: [/yellow]").strip().lower()
                        if cont not in {"y", "yes", "tak"}:
                            return

                return

        if _looks_like_log_input(query):
            console.print("[yellow]Detected log-like input. Falling back to interactive nlp2cmd analysis.[/yellow]")
            session = InteractiveSession(dsl="shell", auto_repair=False)
            feedback = session.process(query)
            session.display_feedback(feedback)
            feedback = _interactive_followup(session, feedback)
            session.display_feedback(feedback)

            cmd = (feedback.generated_output or "").strip()
            if cmd and not cmd.startswith("#"):
                command = cmd
                detected_domain = "shell"
                detected_intent = "log_fallback"
                used_generated_command = True
            else:
                console.print("[red]✗ Could not derive an executable command from logs[/red]")
                return
        elif not result.success:
            console.print(f"[red]✗ Could not generate command with rule-based pipeline: {result.command}[/red]")
            
            # Try different fallback strategies
            fallback_success = False
            
            # Strategy 1: Try LiteLLM with Ollama
            console.print("[yellow]Attempting LLM fallback via LiteLLM...[/yellow]")
            try:
                from nlp2cmd.generation.llm_simple import LiteLLMClient
                import asyncio

                llm = LiteLLMClient()

                system_prompt = """You are a command-line expert. Convert the user's natural language request into a valid shell command.

Rules:
- Respond ONLY with the command, no explanation
- Use standard shell commands
- For "uruchom docker" or similar requests, use appropriate docker commands
- Keep commands simple and executable"""

                async def get_llm_response():
                    return await llm.complete(
                        user=query,
                        system=system_prompt,
                        max_tokens=200,
                        temperature=0.1
                    )

                response = asyncio.run(get_llm_response())
                command = response.strip()

                if command and not command.startswith("#") and not command.lower().startswith(("i'm sorry", "sorry", "i cannot", "cannot")):
                    detected_domain = "shell"
                    detected_intent = "llm_fallback"
                    console.print(f"[green]✓ LLM fallback succeeded[/green]")
                    fallback_success = True
                    used_generated_command = True
            except ImportError as e:
                if "litellm" in str(e):
                    console.print("[yellow]LiteLLM not installed. Attempting auto-install...[/yellow]")
                    if auto_install:
                        try:
                            import subprocess
                            console.print("[dim]Installing litellm...[/dim]")
                            subprocess.run(
                                [sys.executable, "-m", "pip", "install", "litellm"],
                                check=True,
                                capture_output=True,
                            )
                            console.print("[green]✓ litellm installed successfully. Retrying LLM fallback...[/green]")
                            # Retry after installation
                            from nlp2cmd.generation.llm_simple import LiteLLMClient
                            import asyncio
                            
                            llm = LiteLLMClient()
                            system_prompt = """You are a command-line expert. Convert the user's natural language request into a valid shell command.
                            
Rules:
- Respond ONLY with the command, no explanation
- Use standard shell commands
- For "uruchom docker" or similar requests, use appropriate docker commands
- Keep commands simple and executable"""
                            
                            async def get_llm_response():
                                return await llm.complete(
                                    user=query,
                                    system=system_prompt,
                                    max_tokens=200,
                                    temperature=0.1
                                )
                            
                            response = asyncio.run(get_llm_response())
                            command = response.strip()
                            
                            if command and not command.startswith("#") and not command.lower().startswith(("i'm sorry", "sorry", "i cannot", "cannot")):
                                detected_domain = "shell"
                                detected_intent = "llm_fallback"
                                console.print(f"[green]✓ LLM fallback succeeded after auto-install[/green]")
                                fallback_success = True
                                used_generated_command = True
                        except Exception as install_error:
                            console.print(f"[red]✗ Auto-install failed: {str(install_error)}[/red]")
                    else:
                        console.print("[yellow]Use --auto-install to automatically install missing dependencies[/yellow]")
                else:
                    console.print(f"[red]✗ Import error: {str(e)}[/red]")
            except Exception as e:
                error_msg = str(e)
                if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                    console.print("[yellow]Could not connect to Ollama. Attempting to start Ollama...[/yellow]")
                    if auto_install:
                        try:
                            import subprocess
                            console.print("[dim]Starting Ollama with Docker...[/dim]")
                            subprocess.run(["docker", "run", "-d", "-p", "11434:11434", "ollama/ollama"], check=True, capture_output=True)
                            console.print("[green]✓ Ollama started. Retrying LLM fallback...[/green]")
                            # Give it a moment to start
                            import time
                            time.sleep(3)
                            
                            # Retry the LLM call
                            from nlp2cmd.generation.llm_simple import LiteLLMClient
                            import asyncio
                            
                            llm = LiteLLMClient()
                            system_prompt = """You are a command-line expert. Convert the user's natural language request into a valid shell command.
                            
Rules:
- Respond ONLY with the command, no explanation
- Use standard shell commands
- For "uruchom docker" or similar requests, use appropriate docker commands
- Keep commands simple and executable"""
                            
                            async def get_llm_response():
                                return await llm.complete(
                                    user=query,
                                    system=system_prompt,
                                    max_tokens=200,
                                    temperature=0.1
                                )
                            
                            response = asyncio.run(get_llm_response())
                            command = response.strip()
                            
                            if command and not command.startswith("#") and not command.lower().startswith(("i'm sorry", "sorry", "i cannot", "cannot")):
                                detected_domain = "shell"
                                detected_intent = "llm_fallback"
                                console.print(f"[green]✓ LLM fallback succeeded after starting Ollama[/green]")
                                fallback_success = True
                                used_generated_command = True
                        except Exception as docker_error:
                            console.print(f"[red]✗ Failed to start Ollama: {str(docker_error)}[/red]")
                    else:
                        console.print("[yellow]Use --auto-install to automatically start Ollama[/yellow]")
                else:
                    console.print(f"[red]✗ LLM fallback failed with error: {str(e)}[/red]")
            
            # Strategy 2: Simple pattern matching as last resort
            if not fallback_success:
                console.print("[yellow]Attempting pattern-based fallback...[/yellow]")
                query_lower = query.lower()
                
                # Simple pattern matching for common commands
                if "docker" in query_lower:
                    if any(word in query_lower for word in ["uruchom", "start", "run", "uruchomić"]):
                        command = "docker run -it ubuntu bash"
                        detected_domain = "docker"
                        detected_intent = "pattern_fallback"
                        console.print("[green]✓ Pattern fallback succeeded[/green]")
                        fallback_success = True
                        used_generated_command = True
                elif "git" in query_lower:
                    if any(word in query_lower for word in ["klonuj", "clone"]):
                        command = "git clone <repository_url>"
                        detected_domain = "shell"
                        detected_intent = "pattern_fallback"
                        console.print("[green]✓ Pattern fallback succeeded[/green]")
                        fallback_success = True
                        used_generated_command = True
            
            if not fallback_success:
                console.print("[red]✗ All fallback strategies failed[/red]")
                return

        if (not used_generated_command) and result.success:
            command = result.command
            detected_domain = result.domain
            detected_intent = result.intent
        
        console.print(f"[dim]Detected: {detected_domain}/{detected_intent}[/dim]")
    else:
        adapter = adapter_map.get(dsl, lambda: ShellAdapter())()
        nlp = NLP2CMD(adapter=adapter)
        transform_result = nlp.transform(query)
        command = transform_result.command

        detected_domain = dsl
        detected_intent = getattr(getattr(transform_result, "plan", None), "intent", "unknown")
        console.print(f"[dim]Detected: {detected_domain}/{detected_intent}[/dim]")

    if detected_domain == "sql":
        try:
            console.print(
                Panel(
                    Syntax(command, "sql"),
                    title="[yellow]SQL query[/yellow]",
                    border_style="yellow",
                )
            )
        except Exception:
            console.print(
                Panel(
                    f"[bold]{command}[/bold]",
                    title="[yellow]SQL query[/yellow]",
                    border_style="yellow",
                )
            )
        console.print(
            "[yellow]Run Mode executes shell commands; SQL is not executed automatically. Run this query in your database client (psql/mysql/sqlite3) or use --dsl sql without --run.[/yellow]"
        )
        return
    
    # Step 2: Check if it's a browser command and detect typing actions
    is_browser_command = False
    detected_has_typing = False
    
    # Check if query contains typing/clicking/form actions
    loader = FormDataLoader()
    typing_keywords = loader.get_nlp_keywords("typing")
    clicking_keywords = loader.get_nlp_keywords("clicking")
    form_keywords = FormDataLoader.dedupe_selectors([
        *loader.get_nlp_keywords("form"),
        *loader.get_nlp_keywords("submit"),
        *loader.get_nlp_keywords("fill_form_phrases"),
        *loader.get_nlp_keywords("press_enter"),
    ])
    
    query_lower = query.lower()
    has_typing = any(kw in query_lower for kw in typing_keywords)
    has_clicking = any(kw in query_lower for kw in clicking_keywords)
    has_form = any(kw in query_lower for kw in form_keywords)
    
    if dsl == "auto":
        if detected_domain == "shell" and detected_intent in ("open_url", "search_web"):
            is_browser_command = True
            detected_has_typing = has_typing or has_clicking or has_form
            
            # Auto-enable execute_web if typing/clicking detected
            if detected_has_typing and not execute_web:
                console.print("[dim]Auto-enabling browser automation (detected typing/clicking action)[/dim]")
                execute_web = True
    elif dsl == "browser":
        is_browser_command = True
        detected_has_typing = True
        if not execute_web:
            execute_web = True
    
    # Step 3: Execute with recovery
    runner = ExecutionRunner(
        console=console,
        auto_confirm=auto_confirm,
        max_retries=3,
    )
    
    if is_browser_command and execute_web and detected_has_typing:
        # Use PipelineRunner for complex browser automation (typing, clicking, etc.)
        console.print("\n[cyan]Using Playwright for browser automation...[/cyan]")
        
        # Check and install Playwright if needed
        from nlp2cmd.utils.playwright_installer import ensure_playwright_installed
        
        if not ensure_playwright_installed(console=console, auto_install=auto_install):
            console.print("[yellow]Browser automation skipped - Playwright not available[/yellow]")
            _fallback_open_url_from_query(query)
            return
        
        try:
            # Generate ActionIR using BrowserAdapter for multi-step actions
            browser_adapter = BrowserAdapter()
            nlp_browser = NLP2CMD(adapter=browser_adapter)
            ir = nlp_browser.transform_ir(query)
            
            console.print(f"[dim]Actions: {ir.explanation}[/dim]\n")
            
            # Execute with PipelineRunner
            from nlp2cmd.pipeline_runner import PipelineRunner
            pw_runner = PipelineRunner(headless=False)
            result = pw_runner.run(ir, dry_run=False, confirm=auto_confirm)

            if (not result.success) and isinstance(result.data, dict) and result.data.get("requires_confirmation"):
                reason = str(result.data.get("confirmation_reason") or "unknown")
                url_for_confirm = str(result.data.get("url") or "")
                loader_for_confirm = FormDataLoader(site=url_for_confirm) if url_for_confirm else FormDataLoader()

                approved = False
                if reason in {"submit", "press_enter"}:
                    approved = loader_for_confirm.get_site_approval(reason)

                if not approved and not auto_confirm:
                    if reason == "submit":
                        timed_prompt = "\n[yellow]This action will submit a form. Proceed? (auto-Y in 1s; Enter=choose):[/yellow] "
                        full_prompt = "\n[yellow]This action will submit a form. Proceed? [[y/N/a(always for this site)]]:[/yellow] "
                        resp = _timed_default_yes(timed_prompt=timed_prompt, full_prompt=full_prompt)
                    elif reason == "press_enter":
                        timed_prompt = "\n[yellow]This action will press Enter (may submit a form). Proceed? (auto-Y in 1s; Enter=choose):[/yellow] "
                        full_prompt = "\n[yellow]This action will press Enter (may submit a form). Proceed? [[y/N/a(always for this site)]]:[/yellow] "
                        resp = _timed_default_yes(timed_prompt=timed_prompt, full_prompt=full_prompt)
                    else:
                        prompt = "\n[yellow]This action requires confirmation. Proceed? [[y/N]]:[/yellow] "
                        console.print(prompt, end="")
                        resp = console.input().strip().lower()

                    if resp in {"a", "always"} and reason in {"submit", "press_enter"}:
                        loader_for_confirm.set_site_approval(reason, True)
                        approved = True
                    elif resp in {"y", "yes", "tak"}:
                        approved = True

                if not approved and not auto_confirm:
                    console.print("[yellow]Cancelled by user[/yellow]")
                    return

                result = pw_runner.run(ir, dry_run=False, confirm=True)

            if result.success:
                console.print(f"\n[green]✅ Browser automation completed successfully[/green]")
                console.print(f"[dim]Executed {result.data.get('actions_executed', 0)} actions in {result.duration_ms:.1f}ms[/dim]")
                return

            console.print(f"\n[red]❌ Browser automation failed: {result.error}[/red]")
            _fallback_open_url(ir)
            return
        except Exception as e:
            console.print(f"[red]Playwright error: {e}[/red]")
            _fallback_open_url_from_query(query)
            return
    else:
        # Execute shell command with recovery
        exec_result = runner.run_with_recovery(command, query)
        
        if not exec_result.success and exec_result.error_context:
            console.print("\n[yellow]Command failed. Analyzing error...[/yellow]")
            
            # Try to suggest next steps based on error
            _suggest_next_steps(query, command, exec_result, runner)


def _suggest_next_steps(
    original_query: str,
    command: str,
    result,
    runner: ExecutionRunner,
):
    """Suggest next steps based on error context."""
    error = (result.stderr or result.stdout or "").lower()
    
    suggestions = []
    
    if "command not found" in error:
        cmd_parts = command.split()
        if cmd_parts:
            tool = cmd_parts[0]
            suggestions.append(f"Install missing tool: {tool}")
            suggestions.append("Check if the tool is in your PATH")
    
    if "permission denied" in error:
        suggestions.append(f"Try with sudo: sudo {command}")
    
    if "connection refused" in error or "could not connect" in error:
        suggestions.append("Check if the target service is running")
        suggestions.append("Verify the hostname/port is correct")
    
    if "no such file" in error:
        suggestions.append("Verify the file/directory path exists")
    
    if "playwright" in error:
        suggestions.append("Install Playwright: pip install playwright && playwright install")
    
    if suggestions:
        console.print("\n[yellow]💡 Suggestions:[/yellow]")
        for i, s in enumerate(suggestions, 1):
            console.print(f"  {i}. {s}")
        
        console.print("\n[cyan]Would you like to try another command? [y/N]:[/cyan] ", end="")
        response = console.input().strip().lower()
        
        if response in ("y", "yes", "tak"):
            new_query = console.input("[bold green]Enter new query or command: [/bold green]").strip()
            if new_query:
                if new_query.startswith("!"):
                    # Direct command execution
                    runner.run_with_recovery(new_query[1:].strip(), original_query)
                else:
                    # Generate new command from query
                    from nlp2cmd.generation.pipeline import RuleBasedPipeline
                    pipeline = RuleBasedPipeline()
                    new_result = pipeline.process(new_query)
                    if new_result.success:
                        runner.run_with_recovery(new_result.command, new_query)
                    else:
                        console.print(f"[red]Could not generate command from: {new_query}[/red]")


def _is_playwright_error(msg: str) -> bool:
    m = (msg or "").lower()
    if not m:
        return False
    return (
        "no module named 'playwright'" in m
        or "playwright not available" in m
        or "looks like playwright" in m
        or "playwright install" in m
        or "browsertype.launch" in m
        or "executable doesn't exist" in m
        or "executable doesn't exist" in m
    )


def _maybe_install_playwright(msg: str, runner: ExecutionRunner, *, auto_install: bool) -> bool:
    if not _is_playwright_error(msg):
        return False

    if not auto_install:
        console.print("\n[yellow]Playwright is required for browser automation. Install it now? [y/N][/yellow] ", end="")
        if console.input().strip().lower() not in {"y", "yes", "tak"}:
            return False

    py = shlex.quote(sys.executable)
    pip_cmd = f"{py} -m pip install -U playwright"
    install_cmd = f"{py} -m playwright install chromium"

    if not auto_install:
        if not runner.confirm_execution(pip_cmd):
            return False

    res1 = runner.run_command(pip_cmd, stream_output=True)
    if not res1.success:
        return False

    if not auto_install:
        if not runner.confirm_execution(install_cmd):
            return False

    res2 = runner.run_command(install_cmd, stream_output=True)
    return bool(res2.success)


def _fallback_open_url(ir) -> None:
    url = None
    type_text = None

    try:
        params = getattr(ir, "params", None)
        if isinstance(params, dict):
            url = params.get("url")
            type_text = params.get("type_text")
    except Exception:
        url = None

    if isinstance(url, str) and url:
        res = open_url(url, use_webbrowser=False)
        if res.success:
            console.print(f"\n[yellow]Opened URL without Playwright: {url}[/yellow]")
            if isinstance(type_text, str) and type_text:
                console.print(f"[yellow]Type manually: {type_text}[/yellow]")


def _fallback_open_url_from_query(query: str) -> None:
    try:
        url = BrowserAdapter._extract_url(query)
    except Exception:
        url = None
    if isinstance(url, str) and url:
        res = open_url(url, use_webbrowser=False)
        if res.success:
            console.print(f"\n[yellow]Opened URL without Playwright: {url}[/yellow]")


from nlp2cmd.cli.web_schema import web_schema_group
from nlp2cmd.cli.history import history_group


@click.group(cls=NLP2CMDGroup, invoke_without_command=True)
@click.option("-i", "--interactive", is_flag=True, help="Start interactive mode")
@click.option(
    "-d", "--dsl",
    type=click.Choice(["auto", "sql", "shell", "docker", "kubernetes", "dql", "appspec", "browser"]),
    default="auto",
    help="DSL type"
)
@click.option(
    "--appspec",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to an app2schema.appspec JSON file (required for --dsl appspec)",
)
@click.option("-q", "--query", help="Single query to process")
@click.option("-r", "--run", "run_query", help="Execute query immediately with interactive error recovery")
@click.option("--auto-repair", is_flag=True, help="Auto-apply repairs")
@click.option("--explain", is_flag=True, help="Explain how the result was produced")
@click.option("--execute-web", is_flag=True, help="Execute dom_dql.v1 actions via Playwright (requires playwright)")
@click.option("--auto-confirm", is_flag=True, help="Skip confirmation prompts when using --run")
@click.option("--auto-install", is_flag=True, help="Auto-install missing Python deps/tools when using --run (e.g. playwright)")
@click.pass_context
def main(
    ctx,
    interactive: bool,
    dsl: str,
    appspec: Optional[Path],
    query: Optional[str],
    run_query: Optional[str],
    auto_repair: bool,
    explain: bool,
    execute_web: bool,
    auto_confirm: bool,
    auto_install: bool,
):
    """NLP2CMD - Natural Language to Domain-Specific Commands."""
    if load_dotenv is not None:
        try:
            load_dotenv()
        except Exception:
            pass
    ctx.ensure_object(dict)
    ctx.obj["dsl"] = dsl
    ctx.obj["auto_repair"] = auto_repair

    if ctx.invoked_subcommand is None:
        if run_query:
            _handle_run_query(
                run_query,
                dsl=dsl,
                appspec=appspec,
                auto_confirm=auto_confirm,
                execute_web=execute_web,
                auto_install=auto_install,
                auto_repair=auto_repair,
            )
        elif query:
            if dsl == "appspec":
                session = InteractiveSession(
                    dsl=dsl,
                    auto_repair=auto_repair,
                    appspec=str(appspec) if appspec else None,
                )
                feedback = session.process(query)
                session.display_feedback(feedback)
                if execute_web:
                    try:
                        ir = NLP2CMD(adapter=AppSpecAdapter(appspec_path=str(appspec))).transform_ir(query)
                        runner = PipelineRunner(headless=False)
                        res = runner.run(ir, dry_run=False, confirm=True)
                        if res.success:
                            console.print(f"\n✅ Executed web action in {res.duration_ms:.1f}ms")
                        else:
                            console.print(f"\n❌ Web execution failed: {res.error}")
                    except Exception as e:
                        console.print(f"\n❌ Web execution error: {e}")
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
                if execute_web and dsl == "browser":
                    try:
                        adapter = BrowserAdapter()
                        nlp = NLP2CMD(adapter=adapter)
                        ir = nlp.transform_ir(query, context=session.context)
                        runner = PipelineRunner(headless=False)
                        res = runner.run(ir, dry_run=False, confirm=True)
                        if res.success:
                            console.print(f"\n✅ Opened URL via Playwright in {res.duration_ms:.1f}ms")
                        else:
                            console.print(f"\n❌ Playwright execution failed: {res.error}")
                    except Exception as e:
                        console.print(f"\n❌ Playwright execution error: {e}")
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


# Register subcommands
main.add_command(web_schema_group)
main.add_command(history_group)


if __name__ == "__main__":
    main()
