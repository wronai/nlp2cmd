"""
Automatic Playwright installation helper.

Detects if Playwright is needed and installs it automatically with user confirmation.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

from rich.console import Console


def is_playwright_installed() -> bool:
    """Check if Playwright is installed."""
    try:
        import playwright
        return True
    except ImportError:
        return False


def is_playwright_browsers_installed() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to launch chromium to check if it's installed
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                return True
            except Exception:
                return False
    except Exception:
        return False


def install_playwright(console: Optional[Console] = None) -> bool:
    """
    Install Playwright package.
    
    Args:
        console: Rich console for output
    
    Returns:
        True if installation succeeded, False otherwise
    """
    if console is None:
        console = Console()
    
    console.print("\n[yellow]📦 Installing Playwright...[/yellow]")
    
    try:
        # Install playwright package
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "playwright", "-q"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            console.print("[green]✓ Playwright package installed[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to install Playwright: {result.stderr}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Installation error: {e}[/red]")
        return False


def install_playwright_browsers(console: Optional[Console] = None) -> bool:
    """
    Install Playwright browsers (chromium).
    
    Args:
        console: Rich console for output
    
    Returns:
        True if installation succeeded, False otherwise
    """
    if console is None:
        console = Console()
    
    console.print("\n[yellow]🌐 Installing Chromium browser...[/yellow]")
    console.print("[dim]This may take a few minutes (downloading ~170MB)...[/dim]")
    
    try:
        # Install chromium browser
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            console.print("[green]✓ Chromium browser installed[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to install browser: {result.stderr}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Installation error: {e}[/red]")
        return False


def ensure_playwright_installed(
    console: Optional[Console] = None,
    auto_install: bool = False,
) -> bool:
    """
    Ensure Playwright is installed, prompting user if needed.
    
    Args:
        console: Rich console for output
        auto_install: If True, install without asking
    
    Returns:
        True if Playwright is ready, False otherwise
    """
    if console is None:
        console = Console()
    
    # Check if package is installed
    if not is_playwright_installed():
        if not auto_install:
            console.print("\n[yellow]⚠️  Playwright is required for browser automation[/yellow]")
            response = console.input("[cyan]Install Playwright now? [Y/n]: [/cyan]").strip().lower()
            if response not in ("", "y", "yes", "tak"):
                console.print("[yellow]Skipping browser automation[/yellow]")
                return False
        
        if not install_playwright(console):
            return False
    
    # Check if browsers are installed
    if not is_playwright_browsers_installed():
        if not auto_install:
            console.print("\n[yellow]⚠️  Chromium browser is required for browser automation[/yellow]")
            response = console.input("[cyan]Install Chromium now? [Y/n]: [/cyan]").strip().lower()
            if response not in ("", "y", "yes", "tak"):
                console.print("[yellow]Skipping browser automation[/yellow]")
                return False
        
        if not install_playwright_browsers(console):
            return False
    
    console.print("[green]✓ Playwright is ready[/green]")
    return True
