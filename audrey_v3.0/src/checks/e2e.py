"""F1~F4 — end-to-end smoke tests against OpenCode + sisyphus.

Strategy priority (Scout confirmed by static analysis of opencode-dev src):

1. `opencode run --format json <prompt>` — primary. NDJSON events on stdout,
   no server to manage, fully non-interactive. (run.ts:221-305, 544-556)
2. `POST http://127.0.0.1:4096/session/:id/message` — fallback if an existing
   `opencode serve` is running locally. (server/routes/session.ts)
3. `opencode --headless --prompt <prompt>` — defensive fallback in case a
   future CLI exposes this form.

Each strategy gracefully falls through. Returns the first strategy that
actually produces non-empty text.
"""
from __future__ import annotations

import json as _json
import shutil
import subprocess
import time
from pathlib import Path

from ..config import Config
from ..context import CheckContext, run_command
from ..http import http_get, http_post_json
from ..result import (
    CATEGORY_E2E,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_WARN,
)


def _resolve_bin(name: str = "opencode") -> str | None:
    """Windows-safe `opencode` resolver.

    `shutil.which('opencode')` on Windows sometimes misses the `.cmd` wrapper
    installed by npm global. We try the name verbatim, then explicit suffixes.
    """
    found = shutil.which(name)
    if found:
        return found
    for suffix in (".cmd", ".exe", ".bat", ".ps1"):
        found = shutil.which(name + suffix)
        if found:
            return found
    return None


def _extract_text(body: str) -> str:
    """Best-effort non-empty text extraction from HTTP JSON response bodies."""
    try:
        data = _json.loads(body)
    except Exception:
        return body.strip()
    if isinstance(data, dict):
        if isinstance(data.get("content"), str):
            return data["content"]
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                return msg["content"]
        if isinstance(data.get("message"), str):
            return data["message"]
        if isinstance(data.get("text"), str):
            return data["text"]
    return body.strip()


def _strategy_cli_run(agent: str, prompt: str, timeout: int, model: str | None = None, cwd: str | None = None) -> tuple:
    """Strategy 1 (PRIMARY): `opencode run --format json --agent <a> <prompt>`.

    Parses NDJSON events from stdout. Per Scout analysis:
    - `type == "text"` → accumulate part.text
    - `type == "error"` → failure
    - stream end = process exit
    """
    bin_path = _resolve_bin("opencode")
    if not bin_path:
        return False, "cli_run", "opencode not in PATH"

    cmd = [bin_path, "run", "--format", "json", "--agent", agent]
    if model:
        cmd.extend(["--model", model])
    if cwd:
        cmd.extend(["--dir", str(Path(cwd).as_posix())])
    cmd.append(prompt)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return False, "cli_run", f"timeout after {timeout}s"
    except Exception as exc:
        return False, "cli_run", f"launch failed: {exc}"

    texts: list[str] = []
    errors: list[str] = []
    event_count = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            evt = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        event_count += 1
        t = evt.get("type") if isinstance(evt, dict) else None
        if t == "text":
            part = evt.get("part") or {}
            txt = part.get("text") if isinstance(part, dict) else None
            if isinstance(txt, str) and txt:
                texts.append(txt)
        elif t == "error":
            err = evt.get("error") or evt.get("message") or "unknown"
            errors.append(str(err))

    if proc.returncode == 0 and not errors and texts:
        return True, "cli_run", "\n".join(texts)

    if errors:
        return False, "cli_run", f"events={event_count} errors={errors[0][:120]}"
    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "").strip()[-200:]
        return False, "cli_run", f"rc={proc.returncode} stderr={stderr_tail}"
    return False, "cli_run", f"events={event_count} no text parts"


def _strategy_headless_flag(agent: str, prompt: str, timeout: int) -> tuple:
    """Strategy 3: `opencode --headless --prompt <prompt>` (if flag exists)."""
    rc, out, err = run_command(
        ["opencode", "--headless", "--prompt", prompt, "--agent", agent],
        timeout=timeout,
    )
    if rc == 0 and out.strip():
        return True, "headless_flag", out.strip()
    return False, "headless_flag", (err or out or f"rc={rc}")[:200]


def _strategy_api(agent: str, prompt: str, timeout: int) -> tuple:
    """Strategy 2: POST to already-running `opencode serve` on :4096."""
    base = "http://127.0.0.1:4096"
    code, _, _ = http_get(f"{base}/app", timeout=2.0)
    if code < 0:
        return False, "api", "server not running"
    # Try /session/chat (exact endpoint name is uncertain across versions)
    for path in ("/session/chat", "/chat", "/v1/chat"):
        c, body, _ = http_post_json(
            f"{base}{path}",
            {"agent": agent, "prompt": prompt, "input": prompt},
            timeout=timeout,
        )
        if c == 200:
            txt = _extract_text(body)
            if txt:
                return True, f"api:{path}", txt
    return False, "api", "no endpoint accepted request"


def _run_ping(agent: str, prompt: str, timeout: int) -> tuple:
    """Try strategies in order. Returns (ok, strategy, text_or_err, latency_ms)."""
    strategies = (_strategy_cli_run, _strategy_api, _strategy_headless_flag)
    last_err = ""
    last_strategy = ""
    t0 = time.time()
    for fn in strategies:
        ok, name, payload = fn(agent, prompt, timeout)
        if ok:
            return True, name, payload, int((time.time() - t0) * 1000)
        last_err = payload
        last_strategy = name
    return False, last_strategy, last_err, int((time.time() - t0) * 1000)


def check_f1_headless_ping(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        if not cfg.e2e.enabled:
            return CheckResult("F1", "헤드리스 ping", STATUS_SKIP, "e2e.enabled=false", CATEGORY_E2E)
        agent = cfg.e2e.agents[0] if cfg.e2e.agents else "sisyphus"
        ok, strat, payload, latency = _run_ping(agent, cfg.e2e.prompt, cfg.e2e.timeout_sec)
        meta = {"strategy": strat, "latency_ms": latency}
        if ok:
            return CheckResult(
                "F1",
                "헤드리스 ping",
                STATUS_PASS,
                f"{strat} ({latency}ms)",
                CATEGORY_E2E,
                meta=meta,
            )
        return CheckResult(
            "F1",
            "헤드리스 ping",
            STATUS_FAIL,
            f"all strategies failed. last={strat}: {payload[:120]}",
            CATEGORY_E2E,
            meta=meta,
        )
    except Exception as exc:
        return CheckResult("F1", "헤드리스 ping", STATUS_FAIL, str(exc), CATEGORY_E2E)


def check_f2_sisyphus(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        if not cfg.e2e.enabled:
            return CheckResult("F2", "시지푸스 응답", STATUS_SKIP, "e2e.enabled=false", CATEGORY_E2E)
        ok, strat, payload, latency = _run_ping("sisyphus", cfg.e2e.prompt, cfg.e2e.timeout_sec)
        meta = {"strategy": strat, "latency_ms": latency}
        if ok and payload.strip():
            return CheckResult(
                "F2",
                "시지푸스 응답",
                STATUS_PASS,
                f"{latency}ms via {strat}",
                CATEGORY_E2E,
                meta=meta,
            )
        return CheckResult(
            "F2",
            "시지푸스 응답",
            STATUS_FAIL,
            f"{strat}: {payload[:120]}",
            CATEGORY_E2E,
            meta=meta,
        )
    except Exception as exc:
        return CheckResult("F2", "시지푸스 응답", STATUS_FAIL, str(exc), CATEGORY_E2E)


def check_f3_subagents(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        if not cfg.e2e.enabled:
            return CheckResult("F3", "서브에이전트 응답", STATUS_SKIP, "e2e.enabled=false", CATEGORY_E2E)
        subs = [a for a in cfg.e2e.agents if a != "sisyphus"]
        if not subs:
            return CheckResult("F3", "서브에이전트 응답", STATUS_SKIP, "서브에이전트 없음", CATEGORY_E2E)
        results: list = []
        ok_count = 0
        for agent in subs:
            ok, strat, payload, latency = _run_ping(agent, cfg.e2e.prompt, cfg.e2e.timeout_sec)
            results.append((agent, ok, latency, strat))
            if ok:
                ok_count += 1
        if ok_count == len(subs):
            return CheckResult(
                "F3",
                "서브에이전트 응답",
                STATUS_PASS,
                f"{ok_count}/{len(subs)} 응답",
                CATEGORY_E2E,
                meta={"results": results},
            )
        if ok_count > 0:
            return CheckResult(
                "F3",
                "서브에이전트 응답",
                STATUS_WARN,
                f"{ok_count}/{len(subs)} 응답",
                CATEGORY_E2E,
                meta={"results": results},
            )
        return CheckResult(
            "F3",
            "서브에이전트 응답",
            STATUS_FAIL,
            f"0/{len(subs)} 응답",
            CATEGORY_E2E,
            meta={"results": results},
        )
    except Exception as exc:
        return CheckResult("F3", "서브에이전트 응답", STATUS_FAIL, str(exc), CATEGORY_E2E)


def check_f4_latency(cfg: Config, ctx: CheckContext) -> CheckResult:
    """Derive from F1/F2 meta; this is a summary check only."""
    try:
        # Grab previously recorded latencies via ctx (if runner populated them)
        latencies = ctx.__dict__.get("_e2e_latencies") or []
        if not latencies:
            return CheckResult(
                "F4",
                "응답시간 계측",
                STATUS_SKIP,
                "F1/F2 결과 없음",
                CATEGORY_E2E,
            )
        avg = sum(latencies) / len(latencies)
        status = STATUS_PASS if avg < 30000 else STATUS_WARN
        return CheckResult(
            "F4",
            "응답시간 계측",
            status,
            f"avg={avg:.0f}ms ({len(latencies)}건)",
            CATEGORY_E2E,
            meta={"latencies": latencies},
        )
    except Exception as exc:
        return CheckResult("F4", "응답시간 계측", STATUS_FAIL, str(exc), CATEGORY_E2E)
