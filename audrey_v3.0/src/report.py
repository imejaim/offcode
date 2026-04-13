"""Report emitters — ASCII diagnostic sheet + JSON."""
from __future__ import annotations

import datetime
import json
from typing import Optional

from .config import Config
from .context import CheckContext
from .env import EnvironmentInfo
from .judge import Verdict
from .result import (
    CATEGORY_LABELS,
    CATEGORIES,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_WARN,
)

ICON = {
    STATUS_PASS: "[PASS]",
    STATUS_WARN: "[WARN]",
    STATUS_FAIL: "[FAIL]",
    STATUS_SKIP: "[SKIP]",
}


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _fmt_line(result) -> str:
    icon = ICON.get(result.status, "[?]")
    detail = f" — {result.detail}" if result.detail else ""
    fix = f"\n         fix: {result.fix}" if result.fix else ""
    return f"  {icon} {result.id:<5s} {result.name}{detail}{fix}"


def emit_ascii(
    cfg: Config,
    ctx: CheckContext,
    results: list,
    verdict: Verdict,
) -> str:
    lines: list = []
    bar = "=" * 60
    lines.append(bar)
    lines.append("        Agentium 환경 진단서 — Dr. Oh v3.1")
    lines.append(bar)
    env = ctx.env
    lines.append(f"  환경: {env.kind} ({env.hostname}, {env.os})")
    lines.append(f"  일시: {_now_iso()}")
    if ctx.actual_provider:
        ap = ctx.actual_provider.provider
        lines.append(f"  실사용 프로바이더: {ap.name} @ {ap.base_url}")
    else:
        lines.append("  실사용 프로바이더: (없음)")
    lines.append(bar)

    by_cat: dict = {c: [] for c in CATEGORIES}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)

    for cat in CATEGORIES:
        items = by_cat.get(cat) or []
        if not items:
            continue
        lines.append(f"  [{CATEGORY_LABELS.get(cat, cat.upper())}]")
        for r in items:
            lines.append(_fmt_line(r))
        lines.append("")

    lines.append(bar)
    ready_str = "TRUE" if verdict.ready else "FALSE"
    lines.append(f"  AGENTIS_READY: {ready_str}")
    if verdict.reasons:
        lines.append("")
        lines.append("  실패 사유:")
        for reason in verdict.reasons:
            lines.append(f"    - {reason}")
    if verdict.warnings:
        lines.append("")
        lines.append("  경고:")
        for w in verdict.warnings[:10]:
            lines.append(f"    - {w}")
        if len(verdict.warnings) > 10:
            lines.append(f"    ... (+{len(verdict.warnings) - 10})")
    lines.append(bar)
    return "\n".join(lines)


def emit_json(
    cfg: Config,
    ctx: CheckContext,
    results: list,
    verdict: Verdict,
) -> str:
    payload = {
        "schema_version": 3,
        "run_at": _now_iso(),
        "environment": ctx.env.to_dict(),
        "providers": [s.to_dict() for s in ctx.provider_statuses],
        "actual_provider": ctx.actual_provider.provider.name if ctx.actual_provider else None,
        "results": [r.to_dict() for r in results],
        "verdict": verdict.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def emit(
    cfg: Config,
    ctx: CheckContext,
    results: list,
    verdict: Verdict,
    as_json: bool = False,
) -> str:
    if as_json:
        return emit_json(cfg, ctx, results, verdict)
    return emit_ascii(cfg, ctx, results, verdict)
