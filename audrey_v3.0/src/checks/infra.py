"""A1~A4 — provider discovery infra checks."""
from __future__ import annotations

from ..config import Config
from ..context import CheckContext
from ..http import http_post_json
from ..result import (
    CATEGORY_INFRA,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_WARN,
)


def check_a1_discovery(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        statuses = ctx.provider_statuses
        alive = [s for s in statuses if s.alive]
        dead_required = [s for s in statuses if not s.alive and s.provider.required]
        summary = ", ".join(
            f"{s.provider.name}={'OK' if s.alive else 'DOWN'}" for s in statuses
        )
        if not statuses:
            return CheckResult("A1", "프로바이더 디스커버리", STATUS_FAIL, "providers 비어있음", CATEGORY_INFRA)
        if dead_required:
            return CheckResult(
                "A1",
                "프로바이더 디스커버리",
                STATUS_FAIL,
                f"필수 프로바이더 DOWN: {', '.join(s.provider.name for s in dead_required)} | {summary}",
                CATEGORY_INFRA,
            )
        if not alive:
            return CheckResult(
                "A1",
                "프로바이더 디스커버리",
                STATUS_WARN,
                f"살아있는 프로바이더 없음 | {summary}",
                CATEGORY_INFRA,
            )
        return CheckResult(
            "A1",
            "프로바이더 디스커버리",
            STATUS_PASS,
            summary,
            CATEGORY_INFRA,
            meta={"alive": [s.provider.name for s in alive]},
        )
    except Exception as exc:
        return CheckResult("A1", "프로바이더 디스커버리", STATUS_FAIL, str(exc), CATEGORY_INFRA)


def check_a2_models_listing(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        lines: list = []
        any_ok = False
        for s in ctx.provider_statuses:
            if s.alive:
                any_ok = True
                lines.append(f"{s.provider.name}={len(s.served_models)}개")
            else:
                lines.append(f"{s.provider.name}=DOWN")
        if not lines:
            return CheckResult("A2", "/v1/models", STATUS_SKIP, "프로바이더 없음", CATEGORY_INFRA)
        status = STATUS_PASS if any_ok else STATUS_WARN
        return CheckResult("A2", "/v1/models", status, " | ".join(lines), CATEGORY_INFRA)
    except Exception as exc:
        return CheckResult("A2", "/v1/models", STATUS_FAIL, str(exc), CATEGORY_INFRA)


def check_a3_chat_completion(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        actual = ctx.actual_provider
        if actual is None:
            return CheckResult("A3", "chat 응답", STATUS_SKIP, "실사용 프로바이더 없음", CATEGORY_INFRA)
        model = actual.served_models[0] if actual.served_models else (
            actual.provider.expected_models[0] if actual.provider.expected_models else ""
        )
        if not model:
            return CheckResult(
                "A3",
                "chat 응답",
                STATUS_WARN,
                f"{actual.provider.name}에 테스트할 모델이 없음",
                CATEGORY_INFRA,
            )
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 4,
        }
        code, body, latency = http_post_json(actual.provider.chat_url, payload, timeout=15.0)
        if code == 200:
            return CheckResult(
                "A3",
                "chat 응답",
                STATUS_PASS,
                f"{actual.provider.name} {model} ({latency}ms)",
                CATEGORY_INFRA,
                meta={"latency_ms": latency, "model": model},
            )
        return CheckResult(
            "A3",
            "chat 응답",
            STATUS_FAIL,
            f"HTTP {code}: {body[:120]}",
            CATEGORY_INFRA,
        )
    except Exception as exc:
        return CheckResult("A3", "chat 응답", STATUS_FAIL, str(exc), CATEGORY_INFRA)


def check_a4_actual_provider(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        actual = ctx.actual_provider
        if actual is None:
            return CheckResult(
                "A4",
                "actual provider",
                STATUS_FAIL,
                "살아있는 프로바이더 없음",
                CATEGORY_INFRA,
            )
        return CheckResult(
            "A4",
            "actual provider",
            STATUS_PASS,
            f"{actual.provider.name} @ {actual.provider.base_url}",
            CATEGORY_INFRA,
            meta={"name": actual.provider.name, "base_url": actual.provider.base_url},
        )
    except Exception as exc:
        return CheckResult("A4", "actual provider", STATUS_FAIL, str(exc), CATEGORY_INFRA)
