"""
Display utilities for NLP2CMD CLI output formatting.

This module provides centralized display functions for consistent formatting
across all CLI commands and modes with optimized syntax highlighting.
"""

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box
from typing import Any, Optional, Dict, List
import yaml

# Import syntax cache for performance optimization
from .syntax_cache import get_cached_syntax

console = Console()


def display_command_result(
    command: str,
    metadata: Optional[Dict[str, Any]] = None,
    metrics_str: Optional[str] = None,
    show_yaml: bool = True,
    title: Optional[str] = None
) -> None:
    """
    Display command result with simple YAML format and bash markdown.
    
    Args:
        command: Generated command to display
        metadata: Optional metadata about the generation process
        metrics_str: Optional resource metrics string
        show_yaml: Whether to show YAML format
        title: Optional title for the display
    """
    # Display command as bash markdown with syntax highlighting
    if command and command.strip():
        print(f"```bash")
        # Use cached syntax highlighting for better performance
        syntax = get_cached_syntax(command.strip(), "bash", theme="monokai", line_numbers=False)
        console.print(syntax)
        print(f"```")
        print()
    
    # Show metadata if provided and YAML format requested
    if metadata and show_yaml:
        meta = dict(metadata)
        meta.setdefault("resource_metrics", None)
        meta.setdefault("resource_metrics_parsed", None)
        meta.setdefault("token_estimate", None)
        # Format as YAML with syntax highlighting
        yaml_text = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
        print(f"```yaml")
        yaml_syntax = get_cached_syntax(yaml_text.rstrip(), "yaml", theme="monokai", line_numbers=False)
        console.print(yaml_syntax)
        print(f"```")
    
    # Show metrics separately if not in YAML
    elif metrics_str and not show_yaml:
        print(f"\n📊 {metrics_str}")


def display_table(
    data: List[List[str]],
    title: str,
    headers: Optional[List[str]] = None,
    show_headers: bool = True,
    box_style: str = "round"
) -> None:
    """Display data in a formatted table."""
    table = Table(title=title, box=box_style)
    
    if headers and show_headers:
        table.add_column(headers)
    
    for row in data:
        table.add_row(row)
    
    console.print(table)


def display_panel(
    content: str,
    title: str,
    border_style: str = "cyan",
    padding: Optional[tuple[int, int]] = None
) -> None:
    """Display content in a formatted panel."""
    console.print(
        Panel(
            content,
            title=title,
            border_style=border_style,
            padding=padding
        )
    )


def display_info(
    message: str,
    style: str = "cyan"
) -> None:
    """Display informational message."""
    console.print(f"[{style}]{message}[/{style}]")


def display_success(message: str) -> None:
    """Display success message."""
    console.print(f"[green]✓ {message}[/green]")


def display_error(message: str) -> None:
    """Display error message."""
    console.print(f"[red]✗ {message}[/red]")


def display_warning(message: str) -> None:
    """Display warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def display_debug(message: str) -> None:
    """Display debug message."""
    console.print(f"[dim]🔍 {message}[/dim]")


def display_progress(
    message: str,
    spinner: bool = False
) -> None:
    """Display progress message."""
    if spinner:
        console.print(f"[cyan]⏳ {message}[/cyan]")
    else:
        console.print(f"[cyan]📋 {message}[/cyan]")


def display_section(title: str, content: Optional[str] = None) -> None:
    """Display section with title and optional content."""
    console.print(f"\n[bold blue]{title}[/bold blue]")
    if content:
        console.print(content)


def display_list(
    items: List[str],
    title: Optional[str] = None,
    bullet: str = "•"
) -> None:
    """Display list of items."""
    if title:
        console.print(f"\n[bold yellow]{title}[/bold yellow]")
    
    for item in items:
        console.print(f"{bullet} {item}")


def display_kv_pairs(
    data: Dict[str, Any],
    title: Optional[str] = None,
    indent: str = "  "
) -> None:
    """Display key-value pairs."""
    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
    
    for key, value in data.items():
        console.print(f"{indent}[bold]{key}:[/bold] {value}")
