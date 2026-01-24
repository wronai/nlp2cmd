"""
Utility modules for NLP2CMD.
"""

try:
    from nlp2cmd.utils.playwright_installer import (
        ensure_playwright_installed,
        is_playwright_installed,
        is_playwright_browsers_installed,
    )
except Exception:  # pragma: no cover
    ensure_playwright_installed = None  # type: ignore
    is_playwright_installed = None  # type: ignore
    is_playwright_browsers_installed = None  # type: ignore

__all__ = [
    "ensure_playwright_installed",
    "is_playwright_installed",
    "is_playwright_browsers_installed",
]
