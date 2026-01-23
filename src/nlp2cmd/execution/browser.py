"""
Browser automation executor for NLP2CMD.

Provides functionality to execute browser automation commands using:
1. System commands (xdg-open, open, start) for simple URL opening
2. Playwright for advanced browser automation (type, click, navigate)
"""

from __future__ import annotations

import platform
import subprocess
import webbrowser
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote_plus


@dataclass
class BrowserResult:
    """Result of a browser automation action."""
    success: bool
    action: str
    url: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


def get_os_open_command() -> str:
    """Get the appropriate command to open URLs on current OS."""
    system = platform.system().lower()
    if system == "linux":
        return "xdg-open"
    elif system == "darwin":
        return "open"
    elif system == "windows":
        return "start"
    else:
        return "xdg-open"


def normalize_url(url: str) -> str:
    """Normalize a URL by adding protocol if missing."""
    url = url.strip()
    if not url.startswith(("http://", "https://", "file://")):
        url = "https://" + url
    return url


def open_url(url: str, use_webbrowser: bool = True) -> BrowserResult:
    """
    Open a URL in the default browser.
    
    Args:
        url: URL to open (will add https:// if no protocol)
        use_webbrowser: If True, use Python's webbrowser module (more portable)
                       If False, use system command (xdg-open/open/start)
    
    Returns:
        BrowserResult with success status
    """
    url = normalize_url(url)
    
    try:
        if use_webbrowser:
            webbrowser.open(url)
            return BrowserResult(
                success=True,
                action="open_url",
                url=url,
                message=f"Opened {url} in default browser",
            )
        else:
            cmd = get_os_open_command()
            subprocess.Popen(
                [cmd, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return BrowserResult(
                success=True,
                action="open_url",
                url=url,
                message=f"Opened {url} using {cmd}",
            )
    except Exception as e:
        return BrowserResult(
            success=False,
            action="open_url",
            url=url,
            error=str(e),
        )


def search_web(query: str, engine: str = "google") -> BrowserResult:
    """
    Search the web using the specified search engine.
    
    Args:
        query: Search query
        engine: Search engine to use (google, duckduckgo, bing, yahoo)
    
    Returns:
        BrowserResult with success status
    """
    search_urls = {
        "google": "https://www.google.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
        "bing": "https://www.bing.com/search?q=",
        "yahoo": "https://search.yahoo.com/search?p=",
    }
    
    base_url = search_urls.get(engine.lower(), search_urls["google"])
    url = base_url + quote_plus(query)
    
    result = open_url(url)
    result.action = "search_web"
    result.message = f"Searched for '{query}' using {engine}"
    return result


class BrowserExecutor:
    """
    Execute browser automation commands.
    
    Supports:
    - Simple URL opening (using webbrowser or system commands)
    - Advanced automation with Playwright (if installed)
    """
    
    def __init__(self, use_playwright: bool = False, headless: bool = False):
        """
        Initialize browser executor.
        
        Args:
            use_playwright: If True, use Playwright for advanced automation
            headless: If True, run browser in headless mode (Playwright only)
        """
        self.use_playwright = use_playwright
        self.headless = headless
        self._browser = None
        self._page = None
        self._playwright = None
    
    async def _ensure_playwright(self):
        """Initialize Playwright browser if not already done."""
        if self._browser is not None:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
            self._page = await self._browser.new_page()
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Install with: pip install playwright && playwright install"
            )
    
    async def close(self):
        """Close the browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    def execute_simple(self, action: str, params: dict[str, Any]) -> BrowserResult:
        """
        Execute a simple browser action (no Playwright required).
        
        Args:
            action: Action to execute (open_url, search_web)
            params: Action parameters
        
        Returns:
            BrowserResult
        """
        if action in ("open_url", "open_browser", "browse", "navigate"):
            url = params.get("url", "")
            if not url:
                return BrowserResult(
                    success=False,
                    action=action,
                    error="No URL provided",
                )
            return open_url(url)
        
        elif action == "search_web":
            query = params.get("query", "")
            engine = params.get("engine", "google")
            if not query:
                return BrowserResult(
                    success=False,
                    action=action,
                    error="No search query provided",
                )
            return search_web(query, engine)
        
        else:
            return BrowserResult(
                success=False,
                action=action,
                error=f"Unknown simple action: {action}",
            )
    
    async def execute(self, action: str, params: dict[str, Any]) -> BrowserResult:
        """
        Execute a browser automation action.
        
        For simple actions (open_url, search_web), Playwright is not required.
        For advanced actions (type, click, navigate), Playwright is used.
        
        Args:
            action: Action to execute
            params: Action parameters
        
        Returns:
            BrowserResult
        """
        # Simple actions don't need Playwright
        if action in ("open_url", "open_browser", "browse", "search_web"):
            return self.execute_simple(action, params)
        
        # Advanced actions need Playwright
        if not self.use_playwright:
            return BrowserResult(
                success=False,
                action=action,
                error="Advanced browser automation requires Playwright. Enable with use_playwright=True",
            )
        
        await self._ensure_playwright()
        
        try:
            if action == "navigate":
                url = normalize_url(params.get("url", ""))
                await self._page.goto(url)
                return BrowserResult(
                    success=True,
                    action=action,
                    url=url,
                    message=f"Navigated to {url}",
                )
            
            elif action == "type":
                text = params.get("text", "")
                selector = params.get("selector", "")
                
                if selector:
                    await self._page.fill(selector, text)
                else:
                    await self._page.keyboard.type(text)
                
                return BrowserResult(
                    success=True,
                    action=action,
                    message=f"Typed '{text}'" + (f" into {selector}" if selector else ""),
                )
            
            elif action == "click":
                selector = params.get("selector", "")
                if not selector:
                    return BrowserResult(
                        success=False,
                        action=action,
                        error="No selector provided for click",
                    )
                
                await self._page.click(selector)
                return BrowserResult(
                    success=True,
                    action=action,
                    message=f"Clicked on {selector}",
                )
            
            elif action == "press":
                key = params.get("key", "")
                if not key:
                    return BrowserResult(
                        success=False,
                        action=action,
                        error="No key provided for press",
                    )
                
                await self._page.keyboard.press(key)
                return BrowserResult(
                    success=True,
                    action=action,
                    message=f"Pressed key {key}",
                )
            
            elif action == "screenshot":
                path = params.get("path", "screenshot.png")
                await self._page.screenshot(path=path)
                return BrowserResult(
                    success=True,
                    action=action,
                    message=f"Screenshot saved to {path}",
                )
            
            else:
                return BrowserResult(
                    success=False,
                    action=action,
                    error=f"Unknown action: {action}",
                )
        
        except Exception as e:
            return BrowserResult(
                success=False,
                action=action,
                error=str(e),
            )


def generate_shell_command(action: str, params: dict[str, Any]) -> str:
    """
    Generate a shell command for browser actions.
    
    This is used when --dsl auto generates a shell command instead of
    using Playwright directly.
    
    Args:
        action: Browser action
        params: Action parameters
    
    Returns:
        Shell command string
    """
    cmd = get_os_open_command()
    
    if action in ("open_url", "open_browser", "browse", "navigate"):
        url = normalize_url(params.get("url", ""))
        return f"{cmd} '{url}'"
    
    elif action == "search_web":
        query = params.get("query", "")
        engine = params.get("engine", "google")
        search_urls = {
            "google": "https://www.google.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
            "bing": "https://www.bing.com/search?q=",
            "yahoo": "https://search.yahoo.com/search?p=",
        }
        base_url = search_urls.get(engine.lower(), search_urls["google"])
        url = base_url + quote_plus(query)
        return f"{cmd} '{url}'"
    
    else:
        return f"# Unknown browser action: {action}"
