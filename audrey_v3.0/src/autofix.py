"""Auto-fix utilities.

Supported fixes:
  1. B5 localhost trap → replace baseURL with alive provider IP
  2. Qwen → Gemma4 model name replacement
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .config import Config
from .context import CheckContext
from .result import STATUS_PASS, STATUS_WARN, CheckResult

QWEN_TO_GEMMA4_REPLACEMENTS = {
    "Qwen3.5-35B-A3B": "gemma4:31b",
    "localvllm/Qwen3.5-35B-A3B": "ollama/gemma4:31b",
    "vllm/Qwen3.5-35B-A3B": "ollama/gemma4:31b",
}


def _replace_in_file(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


def _pick_alive_baseurl(ctx: CheckContext) -> str | None:
    for s in ctx.provider_statuses:
        if not s.alive:
            continue
        url = s.provider.base_url
        host = (urlparse(url).hostname or "").lower()
        if host not in ("localhost", "127.0.0.1", "::1"):
            return url
    return None


def apply(cfg: Config, ctx: CheckContext, results: list) -> list:
    """Run auto-fixes based on result IDs. Returns new CheckResult entries."""
    if not ctx.auto_fix:
        return []
    fixes: list = []
    by_id = {r.id: r for r in results}

    # Fix 1: B5 localhost trap
    b5 = by_id.get("B5")
    if b5 and b5.status != STATUS_PASS and "localhost" in (b5.detail or ""):
        alive_url = _pick_alive_baseurl(ctx)
        oc_path = cfg.opencode_config_dir / "opencode.json"
        if alive_url and oc_path.exists():
            try:
                text = oc_path.read_text(encoding="utf-8", errors="ignore")
                changed = False
                for needle in ("http://localhost", "http://127.0.0.1"):
                    if needle in text:
                        host_base = alive_url.rstrip("/")
                        # replace hostname part only (keep port if any)
                        import re
                        text_new = re.sub(
                            r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                            host_base,
                            text,
                        )
                        if text_new != text:
                            text = text_new
                            changed = True
                if changed:
                    oc_path.write_text(text, encoding="utf-8")
                    fixes.append(
                        CheckResult(
                            id="FIX-B5",
                            name="B5 localhost 치환",
                            status=STATUS_PASS,
                            detail=f"opencode.json baseURL → {alive_url}",
                            category="infra",
                        )
                    )
            except Exception as exc:
                fixes.append(
                    CheckResult(
                        id="FIX-B5",
                        name="B5 localhost 치환",
                        status=STATUS_WARN,
                        detail=str(exc),
                        category="infra",
                    )
                )

    # Fix 2: Qwen → Gemma4
    changed_files: list = []
    for candidate in (
        cfg.opencode_config_dir / "opencode.json",
        cfg.opencode_config_dir / "oh-my-openagent.jsonc",
        cfg.opencode_config_dir / "oh-my-opencode.jsonc",
        Path.cwd() / "opencode.json",
        Path.cwd() / ".opencode" / "oh-my-openagent.jsonc",
    ):
        for old, new in QWEN_TO_GEMMA4_REPLACEMENTS.items():
            if _replace_in_file(candidate, old, new):
                changed_files.append(f"{candidate.name}: {old}→{new}")
    if changed_files:
        fixes.append(
            CheckResult(
                id="FIX-MODEL",
                name="Qwen→Gemma4 치환",
                status=STATUS_PASS,
                detail="; ".join(changed_files[:5]),
                category="model",
            )
        )

    return fixes
