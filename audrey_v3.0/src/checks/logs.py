"""D1~D3 — log & cache checks (ported from v2.31)."""
from __future__ import annotations

import os
import platform
import re
from pathlib import Path

from ..config import Config, expand_path
from ..context import CheckContext
from ..result import (
    CATEGORY_LOGS,
    CheckResult,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
)


def _omo_log_path() -> Path:
    if platform.system() == "Windows":
        tmp = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
        return Path(tmp) / "oh-my-opencode.log"
    return Path("/tmp/oh-my-opencode.log")


def _opencode_log_dir() -> Path:
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA", str(expand_path("~/AppData/Local")))
        return Path(local) / "opencode" / "log"
    return expand_path("~/.local/share/opencode/log")


def _tail(path: Path, n: int = 200) -> list:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


def check_d1_omo_log(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        log = _omo_log_path()
        if not log.exists():
            return CheckResult("D1", "OmO 로그", STATUS_WARN, f"로그 없음: {log}", CATEGORY_LOGS)
        lines = _tail(log, 200)
        errors = [ln for ln in lines if re.search(r"\bERROR\b|\bError\b|\bFATAL\b", ln)]
        if errors:
            return CheckResult(
                "D1",
                "OmO 로그",
                STATUS_WARN,
                f"{len(errors)}개 에러, 최근: {errors[-1][:80]}",
                CATEGORY_LOGS,
            )
        return CheckResult("D1", "OmO 로그", STATUS_PASS, "에러 없음", CATEGORY_LOGS)
    except Exception as exc:
        return CheckResult("D1", "OmO 로그", STATUS_FAIL, str(exc), CATEGORY_LOGS)


def check_d2_opencode_log(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        log_dir = _opencode_log_dir()
        if not log_dir.exists():
            return CheckResult(
                "D2", "OpenCode 로그", STATUS_WARN, f"로그 디렉터리 없음: {log_dir}", CATEGORY_LOGS,
            )
        files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            files = sorted(log_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return CheckResult("D2", "OpenCode 로그", STATUS_WARN, "로그 파일 없음", CATEGORY_LOGS)
        lines = _tail(files[0], 300)
        plugin_errors = [
            ln for ln in lines
            if re.search(r"plugin", ln, re.IGNORECASE)
            and re.search(r"error|fail|exception", ln, re.IGNORECASE)
        ]
        if plugin_errors:
            return CheckResult(
                "D2",
                "OpenCode 로그",
                STATUS_WARN,
                f"{len(plugin_errors)}개 plugin 에러: {plugin_errors[-1][:80]}",
                CATEGORY_LOGS,
            )
        return CheckResult("D2", "OpenCode 로그", STATUS_PASS, "에러 없음", CATEGORY_LOGS)
    except Exception as exc:
        return CheckResult("D2", "OpenCode 로그", STATUS_FAIL, str(exc), CATEGORY_LOGS)


def check_d3_proxy_error(cfg: Config, ctx: CheckContext) -> CheckResult:
    try:
        pattern = r"proxy\.url must be a non-empty string"
        paths = [_omo_log_path()]
        log_dir = _opencode_log_dir()
        if log_dir.exists():
            files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                paths.append(files[0])
        for p in paths:
            if not p.exists():
                continue
            hits = [ln for ln in _tail(p, 300) if re.search(pattern, ln)]
            if hits:
                return CheckResult(
                    "D3",
                    "프록시 에러",
                    STATUS_FAIL,
                    f"발견: {hits[-1][:80]}",
                    CATEGORY_LOGS,
                )
        return CheckResult("D3", "프록시 에러", STATUS_PASS, "없음", CATEGORY_LOGS)
    except Exception as exc:
        return CheckResult("D3", "프록시 에러", STATUS_FAIL, str(exc), CATEGORY_LOGS)
