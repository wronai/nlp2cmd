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


class MarkdownConsoleProxy:
    """Proxy that forces all console.print output into markdown code blocks."""

    def __init__(self, console: Console, *, language: str = "text") -> None:
        self._console = console
        self._language = language

    def print(self, renderable: Any, *args, **kwargs) -> None:  # type: ignore[override]
        # Ignore extra args/kwargs for simplicity and rely on markdown blocks
        print_markdown_block(renderable, language=self._language, console=self._console)

    def input(self, *args, **kwargs):  # type: ignore[override]
        return self._console.input(*args, **kwargs)

    def __getattr__(self, item: str):
        return getattr(self._console, item)


class MarkdownBlockStream:
    """Context manager that streams multiple prints inside a single Markdown block."""

    def __init__(
        self,
        console: Optional[Console] = None,
        *,
        language: str = "text",
        title: Optional[str] = None,
    ) -> None:
        self._console = console or Console()
        self._language = language
        self._title = title.rstrip() if isinstance(title, str) else None
        self._open = False

    def __enter__(self) -> "MarkdownBlockStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if not self._open:
            self._console.print(f"```{self._language}", markup=False)
            if self._title:
                self._console.print(self._title, markup=False)
            self._open = True

    def print(self, renderable: Any) -> None:
        body = _render_to_text(renderable)
        self._ensure_open()
        if body:
            self._console.print(body, markup=False)
        else:
            self._console.print("", markup=False)

    def close(self) -> None:
        if self._open:
            self._console.print("```", markup=False)
            self._open = False
