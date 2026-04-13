"""C1~C7 — OmO plugin, config, version check, agent model cross-check."""
from __future__ import annotations

import json
import platform
import urllib.request
from pathlib import Path
from typing import Optional

from ..config import Config, expand_path, read_jsonc
from ..context import CheckContext, run_command
from ..result import (
    CATEGORY_OMO,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIP,
    STATUS_WARN,
)


def _get_plugin_path(data: Optional[dict]) -> Optional[str]:
    if data is None:
        return None
    plugins = data.get("plugins") or data.get("plugin")
    if isinstance(plugins, list):
        for p in plugins:
            if isinstance(p, str):
                return p
            if isinstance(p, dict):
                return p.get("path") or p.get("url") or p.get("source")
    if isinstance(plugins, str):
        return plugins
    if isinstance(plugins, dict):
        return plugins.get("path") or plugins.get("url") or plugins.get("source")
    return None


def _find_omo_config() -> Optional[Path]:
    """OmO 설정 파일 탐색.

    upstream OpenCode `paths.ts:39` 패턴에 맞춰 `.jsonc`와 `.json` 확장자를
    모두 허용한다. `oh-my-openagent`(dual publish)와 `oh-my-opencode`
    이름을 모두 본다.
    """
    roots = [
        Path.cwd(),
        Path.cwd() / ".opencode",
        expand_path("~/.config/opencode"),
        expand_path("~/.config/oh-my-openagent"),
    ]
    names = ("oh-my-openagent", "oh-my-opencode")
    exts = (".jsonc", ".json")
    for root in roots:
        for name in names:
            for ext in exts:
                candidate = root / f"{name}{ext}"
                if candidate.exists():
                    return candidate
    return None


def _load_omo(ctx: CheckContext) -> Optional[dict]:
    if ctx.omo_config is not None:
        return ctx.omo_config
    path = _find_omo_config()
    if path is None:
        return None
    data = read_jsonc(path)
    if data is not None:
        ctx.omo_config = data
    return data


def check_c1_plugin_file(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        data = ctx.opencode_json
        plugin_path = _get_plugin_path(data)
        if plugin_path is None:
            return CheckResult("C1", "plugin file://", STATUS_FAIL, "plugin 설정 없음", CATEGORY_OMO)
        if plugin_path.startswith("file://"):
            return CheckResult("C1", "plugin file://", STATUS_PASS, plugin_path[:80], CATEGORY_OMO)
        if plugin_path.startswith("/") or len(plugin_path) > 2 and plugin_path[1] == ":":
            return CheckResult(
                "C1",
                "plugin file://",
                STATUS_WARN,
                f"file:// 프리픽스 없음: {plugin_path[:60]}",
                CATEGORY_OMO,
            )
        return CheckResult(
            "C1",
            "plugin file://",
            STATUS_WARN,
            f"npm 레지스트리 방식?: {plugin_path[:60]}",
            CATEGORY_OMO,
        )
    except Exception as exc:
        return CheckResult("C1", "plugin file://", STATUS_FAIL, str(exc), CATEGORY_OMO)


def check_c2_plugin_exists(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        data = ctx.opencode_json
        plugin_path = _get_plugin_path(data)
        if plugin_path is None:
            return CheckResult("C2", "plugin 파일", STATUS_SKIP, "plugin 경로 없음", CATEGORY_OMO)
        raw = plugin_path[7:] if plugin_path.startswith("file://") else plugin_path
        check = expand_path(raw)
        target = check if check.name == "index.js" else check / "dist" / "index.js"
        if target.exists():
            return CheckResult("C2", "plugin 파일", STATUS_PASS, str(target), CATEGORY_OMO)
        return CheckResult("C2", "plugin 파일", STATUS_FAIL, f"not found: {target}", CATEGORY_OMO)
    except Exception as exc:
        return CheckResult("C2", "plugin 파일", STATUS_FAIL, str(exc), CATEGORY_OMO)


def check_c3_omo_config(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        path = _find_omo_config()
        if path is None:
            return CheckResult("C3", "OmO 설정 파일", STATUS_FAIL, "not found", CATEGORY_OMO)
        _load_omo(ctx)
        return CheckResult("C3", "OmO 설정 파일", STATUS_PASS, str(path), CATEGORY_OMO)
    except Exception as exc:
        return CheckResult("C3", "OmO 설정 파일", STATUS_FAIL, str(exc), CATEGORY_OMO)


def check_c4_sisyphus_model(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        data = _load_omo(ctx)
        if data is None:
            return CheckResult("C4", "sisyphus 모델", STATUS_SKIP, "config 없음", CATEGORY_OMO)
        agents = data.get("agents", {}) or {}
        sisyphus = agents.get("sisyphus", {}) or {}
        model = sisyphus.get("model")
        if model:
            return CheckResult("C4", "sisyphus 모델", STATUS_PASS, str(model), CATEGORY_OMO)
        return CheckResult("C4", "sisyphus 모델", STATUS_WARN, "model 미설정", CATEGORY_OMO)
    except Exception as exc:
        return CheckResult("C4", "sisyphus 모델", STATUS_FAIL, str(exc), CATEGORY_OMO)


def check_c5_sisyphus_enabled(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        data = _load_omo(ctx)
        if data is None:
            return CheckResult("C5", "sisyphus 활성화", STATUS_SKIP, "config 없음", CATEGORY_OMO)
        disabled = data.get("disabled_agents", []) or []
        if isinstance(disabled, list) and "sisyphus" in disabled:
            return CheckResult(
                "C5",
                "sisyphus 활성화",
                STATUS_FAIL,
                "disabled_agents에 포함됨",
                CATEGORY_OMO,
                fix="oh-my-openagent.jsonc의 disabled_agents에서 'sisyphus' 제거",
            )
        return CheckResult("C5", "sisyphus 활성화", STATUS_PASS, "", CATEGORY_OMO)
    except Exception as exc:
        return CheckResult("C5", "sisyphus 활성화", STATUS_FAIL, str(exc), CATEGORY_OMO)


def _detect_omo_install() -> tuple:
    is_win = platform.system() == "Windows"
    local_candidates = [
        ("oh-my-openagent", expand_path("~/.config/opencode/node_modules/oh-my-openagent")),
        ("oh-my-opencode", expand_path("~/.config/opencode/node_modules/oh-my-opencode")),
    ]
    for pkg_name, pkg_path in local_candidates:
        if (pkg_path / "package.json").exists():
            return pkg_name, pkg_path, f"cd {pkg_path.parent.parent} && npm update {pkg_name}"
    rc, out, _ = run_command(["npm", "root", "-g"], timeout=10)
    if rc == 0 and out:
        root = Path(out.strip())
        for pkg_name in ("oh-my-opencode", "oh-my-openagent"):
            pkg_path = root / pkg_name
            if (pkg_path / "package.json").exists():
                return pkg_name, pkg_path, f"npm update -g {pkg_name}"
    return None, None, ""


def _read_installed_version(pkg_path: Path) -> Optional[str]:
    try:
        data = json.loads((pkg_path / "package.json").read_text(encoding="utf-8"))
        return data.get("version")
    except Exception:
        return None


def _read_latest_version(pkg_name: str) -> Optional[str]:
    url = f"https://registry.npmjs.org/{pkg_name}/latest"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return (json.loads(resp.read().decode("utf-8")) or {}).get("version")
    except Exception:
        return None


def check_c6_omo_version(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        pkg_name, pkg_path, update_cmd = _detect_omo_install()
        if pkg_name is None or pkg_path is None:
            return CheckResult("C6", "OmO 버전", STATUS_WARN, "설치 경로 미발견", CATEGORY_OMO)
        installed = _read_installed_version(pkg_path)
        if not installed:
            return CheckResult("C6", "OmO 버전", STATUS_WARN, f"버전 읽기 실패: {pkg_path}", CATEGORY_OMO)
        latest = _read_latest_version(pkg_name)
        if not latest:
            return CheckResult(
                "C6", "OmO 버전", STATUS_PASS,
                f"{pkg_name}@{installed} (latest 조회 실패)", CATEGORY_OMO,
            )
        if installed == latest:
            return CheckResult(
                "C6", "OmO 버전", STATUS_PASS, f"{pkg_name}@{installed} (최신)", CATEGORY_OMO,
            )
        if ctx.auto_fix:
            rc, _, err = run_command(update_cmd.split(), timeout=60)
            if rc == 0:
                new_ver = _read_installed_version(pkg_path) or "?"
                return CheckResult(
                    "C6", "OmO 버전", STATUS_PASS,
                    f"업데이트 완료: {installed} → {new_ver}", CATEGORY_OMO,
                )
            return CheckResult(
                "C6", "OmO 버전", STATUS_WARN,
                f"{pkg_name}@{installed} → {latest} 업데이트 실패: {err[:80]}", CATEGORY_OMO,
                fix=update_cmd,
            )
        return CheckResult(
            "C6", "OmO 버전", STATUS_WARN,
            f"{pkg_name}@{installed} → {latest} 업데이트 가능", CATEGORY_OMO,
            fix=update_cmd,
        )
    except Exception as exc:
        return CheckResult("C6", "OmO 버전", STATUS_FAIL, str(exc), CATEGORY_OMO)


def _collect_agent_models(data: dict) -> list:
    out: list = []
    agents = data.get("agents", {}) or {}
    if isinstance(agents, dict):
        for name, spec in agents.items():
            if isinstance(spec, dict):
                model = spec.get("model")
                if isinstance(model, str):
                    out.append((name, model))
    return out


def check_c7_agent_models_alive(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        data = _load_omo(ctx)
        if data is None:
            return CheckResult("C7", "agent 모델 교차확인", STATUS_SKIP, "config 없음", CATEGORY_OMO)
        entries = _collect_agent_models(data)
        if not entries:
            return CheckResult("C7", "agent 모델 교차확인", STATUS_WARN, "agent.model 없음", CATEGORY_OMO)
        alive_model_ids: set = set()
        for s in ctx.provider_statuses:
            if s.alive:
                for mid in s.served_models:
                    alive_model_ids.add(mid)
                    alive_model_ids.add(f"{s.provider.name}/{mid}")
        missing: list = []
        for agent, model in entries:
            if "/" in model:
                _, model_id = model.split("/", 1)
            else:
                model_id = model
            if model not in alive_model_ids and model_id not in alive_model_ids:
                missing.append((agent, model))
        if missing:
            detail = ", ".join(f"{a}={m}" for a, m in missing[:5])
            return CheckResult(
                "C7",
                "agent 모델 교차확인",
                STATUS_WARN,
                f"살아있는 프로바이더에 없는 모델: {detail}",
                CATEGORY_OMO,
                meta={"missing": missing},
            )
        return CheckResult(
            "C7",
            "agent 모델 교차확인",
            STATUS_PASS,
            f"{len(entries)}개 에이전트 모두 매칭",
            CATEGORY_OMO,
        )
    except Exception as exc:
        return CheckResult("C7", "agent 모델 교차확인", STATUS_FAIL, str(exc), CATEGORY_OMO)
