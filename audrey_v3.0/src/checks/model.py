"""E1/E2 — multi-provider model validity + external-API detector."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..config import Config, expand_path, read_jsonc
from ..context import CheckContext
from ..result import (
    CATEGORY_MODEL,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
)


_EXTERNAL_PROVIDERS = frozenset({
    "openai", "anthropic", "google", "opencode", "azure",
    "deepseek", "groq", "mistral", "cohere", "fireworks",
    "together", "perplexity", "anyscale",
})


def _collect_models(value, prefix: str = "", out: Optional[list] = None) -> list:
    if out is None:
        out = []
    if isinstance(value, dict):
        for k, v in value.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if k == "model" and isinstance(v, str):
                out.append((prefix or "root", v))
            _collect_models(v, path, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _collect_models(v, f"{prefix}[{i}]", out)
    return out


def _config_files(cfg: Config) -> list:
    d = cfg.opencode_config_dir
    return [
        d / "opencode.json",
        d / "opencode.jsonc",
        d / "oh-my-openagent.jsonc",
        d / "oh-my-opencode.jsonc",
        Path.cwd() / "opencode.json",
        Path.cwd() / "opencode.jsonc",
        Path.cwd() / ".opencode" / "oh-my-openagent.jsonc",
        Path.cwd() / ".opencode" / "oh-my-opencode.jsonc",
    ]


def _gather(cfg: Config) -> list:
    entries: list = []
    seen: set = set()
    for p in _config_files(cfg):
        try:
            resolved = p.resolve()
        except Exception:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        data = read_jsonc(p)
        if data is None:
            continue
        for scope, model in _collect_models(data):
            entries.append((p, scope, model))
    return entries


def check_e1_multi_provider_models(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        entries = _gather(cfg)
        if not entries:
            return CheckResult(
                "E1",
                "멀티 프로바이더 모델",
                STATUS_WARN,
                "설정 파일에서 model 값 미발견",
                CATEGORY_MODEL,
            )
        # Build a set of (provider_name, model_id) from alive providers
        alive: dict = {}
        for s in ctx.provider_statuses:
            if s.alive:
                alive[s.provider.name] = set(s.served_models)

        invalid: list = []
        for path, scope, model in entries:
            if "/" not in model:
                continue
            prov, model_id = model.split("/", 1)
            prov_lc = prov.lower()
            if prov_lc in _EXTERNAL_PROVIDERS:
                continue
            # match by provider name, or alias like "localvllm"/"local"/"vllm"
            matched_set: Optional[set] = None
            if prov in alive:
                matched_set = alive[prov]
            else:
                for n, served in alive.items():
                    if prov_lc in n.lower() or n.lower() in prov_lc:
                        matched_set = served
                        break
            if matched_set is None:
                invalid.append((path.name, scope, model, "매칭되는 살아있는 프로바이더 없음"))
                continue
            if model_id not in matched_set:
                invalid.append(
                    (path.name, scope, model, f"{prov}에 {model_id} 없음, 서빙: {sorted(matched_set)[:3]}")
                )
        if invalid:
            detail = "; ".join(f"{s}={m}" for _, s, m, _ in invalid[:3])
            return CheckResult(
                "E1",
                "멀티 프로바이더 모델",
                STATUS_FAIL,
                f"{len(invalid)}개 불일치: {detail[:140]}",
                CATEGORY_MODEL,
                meta={"invalid": [(str(p), s, m, r) for p, s, m, r in invalid]},
            )
        return CheckResult(
            "E1",
            "멀티 프로바이더 모델",
            STATUS_PASS,
            f"{len(entries)}개 모델 설정 모두 유효",
            CATEGORY_MODEL,
        )
    except Exception as exc:
        return CheckResult("E1", "멀티 프로바이더 모델", STATUS_FAIL, str(exc), CATEGORY_MODEL)


def check_e2_external_providers(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        entries = _gather(cfg)
        external: list = []
        for _, scope, model in entries:
            if "/" not in model:
                continue
            prov = model.split("/", 1)[0].lower()
            if prov in _EXTERNAL_PROVIDERS:
                external.append((scope, model))
        if external:
            ext_list = ", ".join(m for _, m in external[:5])
            return CheckResult(
                "E2",
                "외부 API 탐지",
                STATUS_WARN,
                f"외부 API 모델: {ext_list[:160]}",
                CATEGORY_MODEL,
                fix="사내 폐쇄망에서는 외부 API 불가. 로컬 프로바이더로 교체",
            )
        return CheckResult("E2", "외부 API 탐지", STATUS_PASS, "외부 API 미참조", CATEGORY_MODEL)
    except Exception as exc:
        return CheckResult("E2", "외부 API 탐지", STATUS_FAIL, str(exc), CATEGORY_MODEL)
