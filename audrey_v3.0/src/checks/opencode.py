"""B1~B5 — OpenCode install + config + baseURL reachability cross-check."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from ..config import Config, expand_path, read_jsonc
from ..context import CheckContext, run_command
from ..http import http_get
from ..result import (
    CATEGORY_OPENCODE,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_WARN,
)


def check_b1_node(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        rc, out, err = run_command(["node", "--version"])
        if rc == 0 and out:
            return CheckResult("B1", "Node.js", STATUS_PASS, out, CATEGORY_OPENCODE)
        return CheckResult("B1", "Node.js", STATUS_FAIL, err or "not found", CATEGORY_OPENCODE)
    except Exception as exc:
        return CheckResult("B1", "Node.js", STATUS_FAIL, str(exc), CATEGORY_OPENCODE)


def check_b2_opencode(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        rc, out, err = run_command(["opencode", "--version"])
        if rc == 0 and out:
            return CheckResult("B2", "OpenCode 설치", STATUS_PASS, out.splitlines()[0], CATEGORY_OPENCODE)
        rc2, out2, _ = run_command(["npm", "ls", "-g", "opencode-ai", "--depth=0"])
        if rc2 == 0 and "opencode-ai" in out2:
            return CheckResult(
                "B2",
                "OpenCode 설치",
                STATUS_PASS,
                out2.strip().splitlines()[-1].strip(),
                CATEGORY_OPENCODE,
            )
        return CheckResult("B2", "OpenCode 설치", STATUS_FAIL, err or "not found", CATEGORY_OPENCODE)
    except Exception as exc:
        return CheckResult("B2", "OpenCode 설치", STATUS_FAIL, str(exc), CATEGORY_OPENCODE)


# OpenCode 공식 후보 순서 (upstream config.ts:1071):
#   opencode.jsonc > opencode.json > config.json
# jsonc가 1순위이므로 오드리도 동일한 우선순위로 탐색한다.
_OPENCODE_CONFIG_FILENAMES = ("opencode.jsonc", "opencode.json", "config.json")


def _load_opencode_json(cfg: Config, ctx: CheckContext) -> tuple:
    """Locate and parse the active OpenCode config file.

    Tries .jsonc, .json, config.json in upstream's own priority order.
    Returns (path_found_or_first_candidate, parsed_or_None).

    Caches the parsed dict on `ctx.opencode_json` (unchanged shape, for
    omo.py compatibility) and the resolved Path on `ctx.opencode_json_path`.
    """
    if ctx.opencode_json is not None:
        cached_path = getattr(ctx, "opencode_json_path", None)
        if cached_path:
            return Path(cached_path), ctx.opencode_json
        return cfg.opencode_config_dir / _OPENCODE_CONFIG_FILENAMES[0], ctx.opencode_json

    first_candidate = cfg.opencode_config_dir / _OPENCODE_CONFIG_FILENAMES[0]
    for filename in _OPENCODE_CONFIG_FILENAMES:
        candidate = cfg.opencode_config_dir / filename
        if not candidate.exists():
            continue
        data = read_jsonc(candidate)
        if data is not None:
            ctx.opencode_json = data
            # Stash resolved path in a side channel so B5/C7/etc. can tell
            # which file was actually used without mutating the main shape.
            setattr(ctx, "opencode_json_path", str(candidate))
            return candidate, data
    return first_candidate, None


def check_b3_opencode_json(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        path, data = _load_opencode_json(cfg, ctx)
        if data is None:
            tried = " / ".join(_OPENCODE_CONFIG_FILENAMES)
            return CheckResult(
                "B3",
                "opencode.json/jsonc",
                STATUS_FAIL,
                f"not found in {cfg.opencode_config_dir} (tried: {tried})",
                CATEGORY_OPENCODE,
                fix=f"opencode.jsonc 또는 opencode.json 파일을 {cfg.opencode_config_dir}에 생성",
            )
        return CheckResult(
            "B3",
            "opencode.json/jsonc",
            STATUS_PASS,
            f"{path.name} @ {path.parent}",
            CATEGORY_OPENCODE,
            meta={"path": str(path), "ext": path.suffix},
        )
    except Exception as exc:
        return CheckResult("B3", "opencode.json/jsonc", STATUS_FAIL, str(exc), CATEGORY_OPENCODE)


def _extract_provider_baseurls(data: dict) -> list:
    """Return list of (provider_name, base_url) from opencode.json."""
    out: list = []
    providers = data.get("provider") or data.get("providers") or {}
    if isinstance(providers, dict):
        for name, spec in providers.items():
            if isinstance(spec, dict):
                opts = spec.get("options") or {}
                url = opts.get("baseURL") or opts.get("base_url") or spec.get("baseURL")
                if isinstance(url, str):
                    out.append((name, url))
    return out


def check_b4_provider_declared(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        _, data = _load_opencode_json(cfg, ctx)
        if data is None:
            return CheckResult("B4", "provider 선언", STATUS_SKIP, "opencode.json 없음", CATEGORY_OPENCODE)
        providers = data.get("provider") or data.get("providers") or {}
        if isinstance(providers, dict) and providers:
            names = ", ".join(providers.keys())
            return CheckResult("B4", "provider 선언", STATUS_PASS, names, CATEGORY_OPENCODE)
        model = data.get("model")
        if isinstance(model, dict) and model:
            return CheckResult("B4", "provider 선언", STATUS_PASS, str(model)[:80], CATEGORY_OPENCODE)
        return CheckResult("B4", "provider 선언", STATUS_WARN, "provider 키 없음", CATEGORY_OPENCODE)
    except Exception as exc:
        return CheckResult("B4", "provider 선언", STATUS_FAIL, str(exc), CATEGORY_OPENCODE)


def check_b5_baseurl_reachable(cfg: Config, ctx: CheckContext) -> CheckResult:
    """B5 — baseURL trap detector. Compares opencode.json baseURL to the alive
    providers, and actually probes the URL from this host."""
    try:
        _, data = _load_opencode_json(cfg, ctx)
        if data is None:
            return CheckResult("B5", "baseURL 도달성", STATUS_SKIP, "opencode.json 없음", CATEGORY_OPENCODE)
        entries = _extract_provider_baseurls(data)
        if not entries:
            return CheckResult(
                "B5",
                "baseURL 도달성",
                STATUS_WARN,
                "opencode.json에 provider baseURL 선언 없음",
                CATEGORY_OPENCODE,
            )

        failures: list = []
        traps: list = []
        for name, url in entries:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if host in ("localhost", "127.0.0.1", "::1"):
                alive_non_local = [
                    s for s in ctx.provider_statuses
                    if s.alive and "127.0.0.1" not in s.provider.base_url
                    and "localhost" not in s.provider.base_url
                ]
                if alive_non_local:
                    traps.append((name, url, alive_non_local[0].provider.base_url))
            # Normalize: opencode.json's baseURL usually ends with "/v1"
            # (per OpenAI-compatible convention). Don't double-append /v1.
            probe = url.rstrip("/")
            if probe.endswith("/v1"):
                probe = probe + "/models"
            else:
                probe = probe + "/v1/models"
            code, body, _ = http_get(probe, timeout=3.0)
            if code != 200:
                failures.append((name, url, f"HTTP {code}: {body[:60]}"))

        if traps and failures:
            n, url, suggest = traps[0]
            return CheckResult(
                "B5",
                "baseURL 도달성",
                STATUS_FAIL,
                f"localhost 함정: provider={n} url={url}; 추천 → {suggest}",
                CATEGORY_OPENCODE,
                fix=f"opencode.json의 {n}.options.baseURL을 {suggest}로 교체",
                meta={"traps": traps, "failures": failures},
            )
        if failures:
            first = failures[0]
            return CheckResult(
                "B5",
                "baseURL 도달성",
                STATUS_FAIL,
                f"{first[0]}({first[1]}) 도달 실패: {first[2]}",
                CATEGORY_OPENCODE,
                meta={"failures": failures},
            )
        return CheckResult(
            "B5",
            "baseURL 도달성",
            STATUS_PASS,
            ", ".join(n for n, _ in entries),
            CATEGORY_OPENCODE,
        )
    except Exception as exc:
        return CheckResult("B5", "baseURL 도달성", STATUS_FAIL, str(exc), CATEGORY_OPENCODE)
