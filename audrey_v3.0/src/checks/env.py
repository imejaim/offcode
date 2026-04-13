"""ENV1/ENV2 environment checks."""
from __future__ import annotations

from ..config import Config
from ..context import CheckContext
from ..http import http_get
from ..result import (
    CATEGORY_ENV,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
)


def check_env1_self_aware(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        env = ctx.env
        detail = f"{env.kind} | {env.hostname} | {env.os}"
        status = STATUS_PASS if env.kind != "unknown" else STATUS_WARN
        return CheckResult(
            id="ENV1",
            name="환경 자각",
            status=status,
            detail=detail,
            category=CATEGORY_ENV,
            meta={
                "ip_hints": env.ip_hints,
                "gpu_hint": env.gpu_hint,
                "reasoning": env.reasoning,
            },
        )
    except Exception as exc:
        return CheckResult("ENV1", "환경 자각", STATUS_FAIL, str(exc), CATEGORY_ENV)


def check_env2_network(cfg: Config, ctx: CheckContext) -> CheckResult:
    """Probe first provider's base_url root as a reachability smoke test."""
    try:
        if not cfg.providers:
            return CheckResult(
                "ENV2",
                "네트워크 가용성",
                STATUS_WARN,
                "provider 없음",
                CATEGORY_ENV,
            )
        any_alive = any(s.alive for s in ctx.provider_statuses)
        if any_alive:
            alive_names = [s.provider.name for s in ctx.provider_statuses if s.alive]
            return CheckResult(
                "ENV2",
                "네트워크 가용성",
                STATUS_PASS,
                f"alive: {', '.join(alive_names)}",
                CATEGORY_ENV,
            )
        # fall back to a raw GET just to differentiate network vs server-down
        url = cfg.providers[0].base_url
        code, body, _ = http_get(url, timeout=3.0)
        if code > 0:
            return CheckResult(
                "ENV2",
                "네트워크 가용성",
                STATUS_WARN,
                f"네트워크는 닿지만 프로바이더 응답 실패 (HTTP {code})",
                CATEGORY_ENV,
            )
        return CheckResult(
            "ENV2",
            "네트워크 가용성",
            STATUS_FAIL,
            f"{url}: {body[:120]}",
            CATEGORY_ENV,
        )
    except Exception as exc:
        return CheckResult("ENV2", "네트워크 가용성", STATUS_FAIL, str(exc), CATEGORY_ENV)
