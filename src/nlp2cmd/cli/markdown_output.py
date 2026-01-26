"""Utilities for printing CLI output as Markdown code blocks."""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console


def _render_to_text(renderable: Any) -> str:
    """Render any Rich renderable or string to plain text."""
    if renderable is None:
        return ""
    if isinstance(renderable, str):
        return renderable.rstrip()
    capture_console = Console(record=True, force_terminal=False, color_system=None)
    capture_console.print(renderable)
    return capture_console.export_text().rstrip()


def print_markdown_block(
    renderable: Any,
    *,
    language: str = "text",
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Print a renderable or string wrapped in a Markdown code block."""
    console = console or Console()
    body = _render_to_text(renderable)
    lines = [f"```{language}"]
    if title:
        lines.append(title.rstrip())
    if body:
        lines.append(body)
    lines.append("```")
    console.print("\n".join(lines), markup=False)
