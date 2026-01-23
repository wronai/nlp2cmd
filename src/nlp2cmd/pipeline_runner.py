from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.adapters.base import SafetyPolicy
from nlp2cmd.ir import ActionIR


@dataclass
class ShellExecutionPolicy:
    allowlist: set[str] = field(default_factory=set)
    blocked_regex: list[str] = field(
        default_factory=lambda: [
            r"\brm\s+-rf\s+/\b",
            r"\brm\s+-rf\s+/\*\b",
            r"\bmkfs\b",
            r"\bdd\s+if=/dev/zero\b",
            r":\(\)\{:\|:&\};:",
        ]
    )
    require_confirm_regex: list[str] = field(
        default_factory=lambda: [
            r"\brm\b",
            r"\brmdir\b",
            r"\bkill\b",
            r"\bkillall\b",
            r"\bshutdown\b",
            r"\breboot\b",
            r"\bsystemctl\s+stop\b",
            r"\bdocker\s+rm\b",
            r"\bdocker\s+rmi\b",
        ]
    )
    allow_sudo: bool = False
    allow_pipes: bool = False


@dataclass
class RunnerResult:
    success: bool
    kind: str
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0


class PipelineRunner:
    def __init__(
        self,
        *,
        shell_policy: Optional[ShellExecutionPolicy] = None,
        safety_policy: Optional[SafetyPolicy] = None,
        headless: bool = True,
    ):
        self.shell_policy = shell_policy or ShellExecutionPolicy()
        self.safety_policy = safety_policy
        self.headless = headless

    def run(
        self,
        ir: ActionIR,
        *,
        cwd: Optional[str] = None,
        timeout_s: float = 15.0,
        dry_run: bool = True,
        confirm: bool = False,
        web_url: Optional[str] = None,
    ) -> RunnerResult:
        started = time.time()
        try:
            if ir.dsl_kind == "shell":
                res = self._run_shell(ir.dsl, cwd=cwd, timeout_s=timeout_s, dry_run=dry_run, confirm=confirm)
            elif ir.dsl_kind == "dom":
                res = self._run_dom_dql(ir.dsl, dry_run=dry_run, confirm=confirm, web_url=web_url)
            else:
                res = RunnerResult(
                    success=False,
                    kind=str(ir.dsl_kind),
                    error=f"Unsupported dsl_kind: {ir.dsl_kind}",
                )

            res.duration_ms = (time.time() - started) * 1000.0
            return res
        except Exception as e:
            return RunnerResult(
                success=False,
                kind=str(ir.dsl_kind),
                error=str(e),
                duration_ms=(time.time() - started) * 1000.0,
            )

    def _run_shell(
        self,
        command: str,
        *,
        cwd: Optional[str],
        timeout_s: float,
        dry_run: bool,
        confirm: bool,
    ) -> RunnerResult:
        cmd = str(command or "").strip()
        if not cmd:
            return RunnerResult(success=False, kind="shell", error="Empty command")

        if self.safety_policy is not None:
            chk = self._check_against_safety_policy(cmd, self.safety_policy)
            if not chk["allowed"]:
                return RunnerResult(success=False, kind="shell", error=str(chk.get("reason") or "Blocked"))
            if chk.get("requires_confirmation") and not confirm:
                return RunnerResult(
                    success=False,
                    kind="shell",
                    error="Command requires confirmation",
                    data={"requires_confirmation": True},
                )

        parsed = self._parse_shell_command(cmd)
        if not parsed["allowed"]:
            return RunnerResult(success=False, kind="shell", error=str(parsed.get("reason") or "Blocked"))

        if parsed.get("requires_confirmation") and not confirm:
            return RunnerResult(
                success=False,
                kind="shell",
                error="Command requires confirmation",
                data={"requires_confirmation": True},
            )

        argv = parsed.get("argv")
        if not isinstance(argv, list) or not argv:
            return RunnerResult(success=False, kind="shell", error="Failed to parse command")

        if dry_run:
            return RunnerResult(success=True, kind="shell", data={"argv": argv, "dry_run": True})

        cp = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout_s,
            check=False,
        )
        return RunnerResult(
            success=cp.returncode == 0,
            kind="shell",
            data={
                "argv": argv,
                "returncode": cp.returncode,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
            },
            error=None if cp.returncode == 0 else (cp.stderr.strip() or f"returncode={cp.returncode}"),
        )

    def _parse_shell_command(self, command: str) -> dict[str, Any]:
        cmd = command.strip()
        cmd_lower = cmd.lower()

        if not self.shell_policy.allow_sudo and re.search(r"(^|\s)sudo(\s|$)", cmd_lower):
            return {"allowed": False, "reason": "sudo is not allowed"}

        if not self.shell_policy.allow_pipes and any(op in cmd for op in ["|", ";", "&&", "||", ">", "<"]):
            return {"allowed": False, "reason": "Pipes/redirects/chaining are not allowed"}

        if any(x in cmd for x in ["$(`", "`", "$(", "${"]):
            return {"allowed": False, "reason": "Shell expansions are not allowed"}

        for pat in self.shell_policy.blocked_regex:
            if re.search(pat, cmd_lower):
                return {"allowed": False, "reason": f"Command blocked by pattern: {pat}"}

        requires = any(re.search(p, cmd_lower) for p in self.shell_policy.require_confirm_regex)

        try:
            argv = shlex.split(cmd)
        except Exception:
            argv = cmd.split()

        if not argv:
            return {"allowed": False, "reason": "Empty command"}

        base = argv[0]
        if self.shell_policy.allowlist and base not in self.shell_policy.allowlist:
            return {"allowed": False, "reason": f"Command not in allowlist: {base}"}

        return {"allowed": True, "argv": argv, "requires_confirmation": requires}

    @staticmethod
    def _check_against_safety_policy(command: str, policy: SafetyPolicy) -> dict[str, Any]:
        cmd_lower = (command or "").lower()

        if not policy.enabled:
            return {"allowed": True, "requires_confirmation": False}

        for pattern in policy.blocked_patterns:
            if str(pattern).lower() in cmd_lower:
                return {"allowed": False, "reason": f"Blocked pattern: {pattern}", "requires_confirmation": False}

        requires = False
        for pattern in policy.require_confirmation_for:
            if str(pattern).lower() in cmd_lower:
                requires = True
                break

        return {"allowed": True, "requires_confirmation": requires}

    def _run_dom_dql(
        self,
        dql_json: str,
        *,
        dry_run: bool,
        confirm: bool,
        web_url: Optional[str],
    ) -> RunnerResult:
        try:
            payload = json.loads(dql_json)
        except Exception as e:
            return RunnerResult(success=False, kind="dom", error=f"Invalid dom_dql.v1 JSON: {e}")

        if not isinstance(payload, dict) or payload.get("dsl") != "dom_dql.v1":
            return RunnerResult(success=False, kind="dom", error="Unsupported dom DQL payload")

        url = payload.get("url") or web_url
        action = str(payload.get("action") or "")
        target = payload.get("target") or {}
        selector = str((target or {}).get("value") or "")

        if not url:
            return RunnerResult(success=False, kind="dom", error="Missing url for dom action")
        if not action:
            return RunnerResult(success=False, kind="dom", error="Missing action")
        if not selector:
            return RunnerResult(success=False, kind="dom", error="Missing target selector")

        params = payload.get("params") or {}
        if dry_run:
            return RunnerResult(
                success=True,
                kind="dom",
                data={"dry_run": True, "url": url, "action": action, "selector": selector, "params": params},
            )

        if action in {"click", "type", "select"} and not confirm:
            pass

        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:
            return RunnerResult(success=False, kind="dom", error=f"Playwright not available: {e}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(str(url))
            page.wait_for_timeout(250)

            locator = page.locator(selector).first

            if action == "click":
                locator.click()
            elif action == "type":
                value = (params or {}).get("value")
                if value is None:
                    return RunnerResult(success=False, kind="dom", error="Missing params.value for type")
                locator.fill(str(value))
            elif action == "select":
                value = (params or {}).get("value")
                if value is None:
                    return RunnerResult(success=False, kind="dom", error="Missing params.value for select")
                locator.select_option(str(value))
            else:
                return RunnerResult(success=False, kind="dom", error=f"Unsupported dom action: {action}")

            browser.close()

        return RunnerResult(success=True, kind="dom", data={"url": url, "action": action, "selector": selector})
