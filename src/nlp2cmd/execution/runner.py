"""
Execution runner with interactive error handling and LLM-assisted recovery.

Provides:
- Command execution with real-time logging
- Error detection and context extraction
- LLM integration for suggesting fix commands
- Automatic app2schema discovery for new commands
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
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

    class Text(str):  # type: ignore
        pass

    class Live:  # type: ignore
        def __init__(self, *args, **kwargs):
            return

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update(self, *args, **kwargs):
            return


@dataclass
class ExecutionResult:
    """Result of command execution."""
    success: bool
    command: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    error_context: Optional[str] = None


@dataclass
class RecoveryContext:
    """Context for LLM-assisted error recovery."""
    original_query: str
    executed_command: str
    error_output: str
    exit_code: int
    previous_attempts: list[str] = field(default_factory=list)
    environment_info: dict[str, Any] = field(default_factory=dict)


class ExecutionRunner:
    """
    Execute commands with logging, error handling, and LLM-assisted recovery.
    
    Features:
    - Real-time output streaming
    - Error detection and classification
    - LLM integration for suggesting recovery commands
    - Interactive confirmation before execution
    """
    
    def __init__(
        self,
        console: Optional[Console] = None,
        auto_confirm: bool = False,
        max_retries: int = 3,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize execution runner.
        
        Args:
            console: Rich console for output (creates new if None)
            auto_confirm: Skip confirmation prompts
            max_retries: Maximum number of retry attempts
            llm_client: Optional LLM client for error recovery suggestions
        """
        self.console = console or Console()
        self.auto_confirm = auto_confirm
        self.max_retries = max_retries
        self.llm_client = llm_client
        self.execution_history: list[ExecutionResult] = []
        
        # Initialize global command history
        self._cmd_history = None
        try:
            from nlp2cmd.history.tracker import get_global_history
            self._cmd_history = get_global_history()
        except Exception:
            pass
    
    def run_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        stream_output: bool = True,
    ) -> ExecutionResult:
        """
        Execute a shell command with real-time output.
        
        Args:
            command: Shell command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            stream_output: Stream output in real-time
        
        Returns:
            ExecutionResult with output and status
        """
        start_time = time.time()
        
        self.console.print(f"\n[bold cyan]$ {command}[/bold cyan]")
        
        try:
            if stream_output:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd,
                    env=env,
                )
                
                stdout_lines = []
                stderr_lines = []
                
                import select
                import os
                
                if hasattr(select, 'poll'):
                    poller = select.poll()
                    poller.register(process.stdout, select.POLLIN)
                    poller.register(process.stderr, select.POLLIN)
                    
                    while process.poll() is None:
                        events = poller.poll(100)
                        for fd, event in events:
                            if fd == process.stdout.fileno():
                                line = process.stdout.readline()
                                if line:
                                    stdout_lines.append(line)
                                    self.console.print(f"  {line.rstrip()}")
                            elif fd == process.stderr.fileno():
                                line = process.stderr.readline()
                                if line:
                                    stderr_lines.append(line)
                                    self.console.print(f"  [red]{line.rstrip()}[/red]")
                else:
                    stdout, stderr = process.communicate(timeout=timeout)
                    stdout_lines = stdout.splitlines(keepends=True)
                    stderr_lines = stderr.splitlines(keepends=True)
                    for line in stdout_lines:
                        self.console.print(f"  {line.rstrip()}")
                    for line in stderr_lines:
                        self.console.print(f"  [red]{line.rstrip()}[/red]")
                
                remaining_stdout, remaining_stderr = process.communicate()
                if remaining_stdout:
                    stdout_lines.append(remaining_stdout)
                    for line in remaining_stdout.splitlines():
                        self.console.print(f"  {line}")
                if remaining_stderr:
                    stderr_lines.append(remaining_stderr)
                    for line in remaining_stderr.splitlines():
                        self.console.print(f"  [red]{line}[/red]")
                
                exit_code = process.returncode
                stdout = ''.join(stdout_lines)
                stderr = ''.join(stderr_lines)
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                )
                exit_code = result.returncode
                stdout = result.stdout
                stderr = result.stderr
                
                if stdout:
                    self.console.print(stdout)
                if stderr:
                    self.console.print(f"[red]{stderr}[/red]")
            
            duration_ms = (time.time() - start_time) * 1000
            success = exit_code == 0
            
            result = ExecutionResult(
                success=success,
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                error_context=stderr if not success else None,
            )
            
            self.execution_history.append(result)
            
            # Record in global command history
            if self._cmd_history:
                try:
                    self._cmd_history.record(
                        query=command,  # For shell commands, the command is the query
                        dsl="shell",
                        command=command,
                        success=success,
                        exit_code=exit_code,
                        duration_ms=duration_ms,
                        error=stderr if not success else None,
                    )
                except Exception:
                    pass
            
            if success:
                self.console.print(f"[green]✓ Command completed in {duration_ms:.1f}ms[/green]")
            else:
                self.console.print(f"[red]✗ Command failed with exit code {exit_code}[/red]")
            
            return result
            
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            result = ExecutionResult(
                success=False,
                command=command,
                exit_code=-1,
                stderr="Command timed out",
                duration_ms=duration_ms,
                error_context="Timeout",
            )
            self.execution_history.append(result)
            self.console.print(f"[red]✗ Command timed out after {timeout}s[/red]")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = ExecutionResult(
                success=False,
                command=command,
                exit_code=-1,
                stderr=str(e),
                duration_ms=duration_ms,
                error_context=str(e),
            )
            self.execution_history.append(result)
            self.console.print(f"[red]✗ Execution error: {e}[/red]")
            return result
    
    def confirm_execution(self, command: str) -> bool:
        """
        Ask user to confirm command execution.
        
        Args:
            command: Command to be executed
        
        Returns:
            True if user confirms, False otherwise
        """
        if self.auto_confirm:
            return True
        
        self.console.print(Panel(
            f"[bold]{command}[/bold]",
            title="[yellow]Command to execute[/yellow]",
            border_style="yellow",
        ))
        
        response = self.console.input("[yellow]Execute this command? [Y/n/e(dit)]: [/yellow]").strip().lower()
        
        if response in ("", "y", "yes", "tak"):
            return True
        elif response in ("n", "no", "nie"):
            return False
        elif response in ("e", "edit", "edytuj"):
            new_command = self.console.input("[cyan]Enter modified command: [/cyan]").strip()
            if new_command:
                return self.confirm_execution(new_command)
            return False
        else:
            return False
    
    def get_recovery_suggestion(self, context: RecoveryContext) -> Optional[str]:
        """
        Get LLM-assisted recovery suggestion based on error context.
        
        Args:
            context: Recovery context with error information
        
        Returns:
            Suggested recovery command or None
        """
        if not self.llm_client:
            return self._get_heuristic_suggestion(context)
        
        try:
            prompt = self._build_recovery_prompt(context)
            response = self.llm_client.generate(prompt)
            return self._parse_recovery_response(response)
        except Exception as e:
            self.console.print(f"[yellow]LLM recovery failed: {e}[/yellow]")
            return self._get_heuristic_suggestion(context)
    
    def _build_recovery_prompt(self, context: RecoveryContext) -> str:
        """Build prompt for LLM recovery suggestion."""
        return f"""You are a command-line assistant. The user tried to execute a command that failed.

Original user query: {context.original_query}
Executed command: {context.executed_command}
Exit code: {context.exit_code}
Error output:
{context.error_output}

Previous attempts: {context.previous_attempts}

Suggest a single command to fix this issue or an alternative approach.
Respond with ONLY the command, no explanation.
If the issue requires installing a package, suggest the installation command.
If the command syntax was wrong, provide the corrected command.
"""
    
    def _parse_recovery_response(self, response: str) -> Optional[str]:
        """Parse LLM response to extract command."""
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('```'):
                    continue
                return line
        return None
    
    def _get_heuristic_suggestion(self, context: RecoveryContext) -> Optional[str]:
        """Get heuristic-based recovery suggestion."""
        error = context.error_output.lower()
        
        if "command not found" in error or "not found" in error:
            cmd_parts = context.executed_command.split()
            if cmd_parts:
                tool = cmd_parts[0]
                return f"# Install '{tool}' using your package manager (apt, brew, etc.)"
        
        if "permission denied" in error:
            return f"sudo {context.executed_command}"
        
        if "no such file or directory" in error:
            return "# Check if the file/directory exists"
        
        if "connection refused" in error or "could not connect" in error:
            return "# Check if the service is running"
        
        if "playwright" in error.lower():
            return "playwright install"
        
        return None
    
    def run_with_recovery(
        self,
        command: str,
        original_query: str,
        on_suggestion: Optional[Callable[[str], bool]] = None,
    ) -> ExecutionResult:
        """
        Execute command with automatic error recovery.
        
        Args:
            command: Command to execute
            original_query: Original user query
            on_suggestion: Callback when recovery suggestion is made
        
        Returns:
            Final ExecutionResult
        """
        attempts = []
        current_command = command
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self.console.print(f"\n[yellow]Retry attempt {attempt}/{self.max_retries}[/yellow]")
            
            if not self.confirm_execution(current_command):
                return ExecutionResult(
                    success=False,
                    command=current_command,
                    exit_code=-1,
                    error_context="User cancelled",
                )
            
            result = self.run_command(current_command)
            
            if result.success:
                return result
            
            attempts.append(current_command)
            
            if attempt < self.max_retries:
                context = RecoveryContext(
                    original_query=original_query,
                    executed_command=current_command,
                    error_output=result.stderr or result.stdout,
                    exit_code=result.exit_code,
                    previous_attempts=attempts,
                )
                
                suggestion = self.get_recovery_suggestion(context)
                
                if suggestion:
                    self.console.print(Panel(
                        f"[cyan]{suggestion}[/cyan]",
                        title="[yellow]💡 Suggested recovery[/yellow]",
                        border_style="yellow",
                    ))
                    
                    if on_suggestion:
                        if on_suggestion(suggestion):
                            current_command = suggestion
                            continue
                    else:
                        response = self.console.input(
                            "[yellow]Try this suggestion? [Y/n/c(ustom)]: [/yellow]"
                        ).strip().lower()
                        
                        if response in ("", "y", "yes", "tak"):
                            current_command = suggestion
                            continue
                        elif response in ("c", "custom", "własne"):
                            custom = self.console.input("[cyan]Enter custom command: [/cyan]").strip()
                            if custom:
                                current_command = custom
                                continue
                
                response = self.console.input(
                    "[yellow]Retry with modified command? [y/N]: [/yellow]"
                ).strip().lower()
                
                if response in ("y", "yes", "tak"):
                    custom = self.console.input("[cyan]Enter command: [/cyan]").strip()
                    if custom:
                        current_command = custom
                        continue
            
            break
        
        return result
