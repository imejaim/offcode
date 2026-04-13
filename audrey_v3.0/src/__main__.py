"""CLI entry point for Dr. Oh v3.0."""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Optional

from . import autofix
from .checks import env as chk_env
from .checks import e2e as chk_e2e
from .checks import infra as chk_infra
from .checks import logs as chk_logs
from .checks import model as chk_model
from .checks import omo as chk_omo
from .checks import opencode as chk_opencode
from .config import Config, default_config, load_config
from .context import CheckContext
from .env import detect_environment
from .judge import judge
from .provider import discover_providers, pick_actual_provider
from .report import emit
from .result import (
    CATEGORIES,
    CATEGORY_E2E,
    CATEGORY_ENV,
    CATEGORY_INFRA,
    CATEGORY_LOGS,
    CATEGORY_MODEL,
    CATEGORY_OMO,
    CATEGORY_OPENCODE,
    CheckResult,
    STATUS_FAIL,
)


def _fix_stdout_encoding() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


CATEGORY_CHECKS: dict = {
    CATEGORY_ENV: [chk_env.check_env1_self_aware, chk_env.check_env2_network],
    CATEGORY_INFRA: [
        chk_infra.check_a1_discovery,
        chk_infra.check_a2_models_listing,
        chk_infra.check_a3_chat_completion,
        chk_infra.check_a4_actual_provider,
    ],
    CATEGORY_OPENCODE: [
        chk_opencode.check_b1_node,
        chk_opencode.check_b2_opencode,
        chk_opencode.check_b3_opencode_json,
        chk_opencode.check_b4_provider_declared,
        chk_opencode.check_b5_baseurl_reachable,
    ],
    CATEGORY_OMO: [
        chk_omo.check_c1_plugin_file,
        chk_omo.check_c2_plugin_exists,
        chk_omo.check_c3_omo_config,
        chk_omo.check_c4_sisyphus_model,
        chk_omo.check_c5_sisyphus_enabled,
        chk_omo.check_c6_omo_version,
        chk_omo.check_c7_agent_models_alive,
    ],
    CATEGORY_LOGS: [
        chk_logs.check_d1_omo_log,
        chk_logs.check_d2_opencode_log,
        chk_logs.check_d3_proxy_error,
    ],
    CATEGORY_MODEL: [
        chk_model.check_e1_multi_provider_models,
        chk_model.check_e2_external_providers,
    ],
    CATEGORY_E2E: [
        chk_e2e.check_f1_headless_ping,
        chk_e2e.check_f2_sisyphus,
        chk_e2e.check_f3_subagents,
        chk_e2e.check_f4_latency,
    ],
}


def _run_checks(cfg: Config, ctx: CheckContext, categories: list) -> list:
    results: list = []
    latencies: list = []
    for cat in categories:
        for fn in CATEGORY_CHECKS.get(cat, []):
            try:
                r = fn(cfg, ctx)
            except Exception as exc:
                r = CheckResult(
                    id="??",
                    name=fn.__name__,
                    status=STATUS_FAIL,
                    detail=f"예외: {exc}",
                    category=cat,
                )
            if isinstance(r, list):
                for item in r:
                    results.append(item)
                    if item.meta.get("latency_ms"):
                        latencies.append(item.meta["latency_ms"])
            else:
                results.append(r)
                if r.meta.get("latency_ms"):
                    latencies.append(r.meta["latency_ms"])
    # Stash latencies on ctx so F4 can consume them
    ctx.__dict__["_e2e_latencies"] = latencies
    return results


def main(argv: Optional[list] = None) -> int:
    _fix_stdout_encoding()
    parser = argparse.ArgumentParser(
        prog="python -m audrey_v3.0",
        description="Dr. Oh v3.0 — Agentium 환경 진단",
    )
    parser.add_argument("--config", type=Path, help="v3 또는 v2 config.json 경로")
    parser.add_argument(
        "--category",
        choices=CATEGORIES,
        action="append",
        help="특정 카테고리만 실행 (반복 가능)",
    )
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--auto-fix", action="store_true", help="자동 수정 시도")
    parser.add_argument("--env", help="환경 힌트 강제 지정 (vdi|desktop|laptop|blackwell)")
    args = parser.parse_args(argv)

    if args.config:
        try:
            cfg = load_config(args.config)
        except Exception as exc:
            print(f"[ERROR] config load failed: {exc}", file=sys.stderr)
            return 2
    else:
        cfg = default_config()

    env_hint = args.env or cfg.environment_hint or "auto"
    env_info = detect_environment(env_hint)

    statuses = discover_providers(cfg.providers, timeout=3.0)
    actual = pick_actual_provider(statuses)

    ctx = CheckContext(
        env=env_info,
        provider_statuses=statuses,
        actual_provider=actual,
        auto_fix=bool(args.auto_fix),
    )

    categories = args.category or CATEGORIES
    # Run twice if auto-fix to re-verify after fixes
    results = _run_checks(cfg, ctx, categories)

    if args.auto_fix:
        fix_results = autofix.apply(cfg, ctx, results)
        if fix_results:
            # Re-run affected categories (infra + opencode + model are cheap)
            ctx.opencode_json = None
            ctx.omo_config = None
            results = _run_checks(cfg, ctx, categories)
            results = fix_results + results

    verdict = judge(results)
    output = emit(cfg, ctx, results, verdict, as_json=args.json)
    print(output)

    return 0 if verdict.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
