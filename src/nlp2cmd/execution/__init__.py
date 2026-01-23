"""
Execution module for NLP2CMD.

Contains executors for different DSL types:
- Shell commands
- Browser automation (Playwright)
- Keyboard shortcuts
- Interactive runner with error recovery
"""

from nlp2cmd.execution.browser import BrowserExecutor, open_url, search_web
from nlp2cmd.execution.runner import ExecutionRunner, ExecutionResult, RecoveryContext

__all__ = [
    "BrowserExecutor",
    "open_url",
    "search_web",
    "ExecutionRunner",
    "ExecutionResult",
    "RecoveryContext",
]
