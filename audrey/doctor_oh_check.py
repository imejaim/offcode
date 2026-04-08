#!/usr/bin/env python3
"""
오드리 (Dr. Oh) - OFFCODE 환경 검사 v1.0

사내 폐쇄망 OFFCODE 환경(vLLM + OpenCode + OmO)의 상태를 진단합니다.
Python 3.9+ stdlib만 사용하며, pip install 없이 동작합니다.

사용법:
    python doctor_oh_check.py              # 전체 체크
    python doctor_oh_check.py --json       # JSON 출력
    python doctor_oh_check.py --category infra   # 인프라만
    python doctor_oh_check.py --category opencode
    python doctor_oh_check.py --category omo
    python doctor_oh_check.py --category logs
"""

import argparse
import io
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

VERSION = "1.0"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARN = "WARN"
STATUS_SKIP = "SKIP"

ICON = {
    STATUS_PASS: "\u2705",
    STATUS_FAIL: "\u274c",
    STATUS_WARN: "\u26a0\ufe0f",
    STATUS_SKIP: "\u23ed\ufe0f",
}

CATEGORY_INFRA = "infra"
CATEGORY_OPENCODE = "opencode"
CATEGORY_OMO = "omo"
CATEGORY_LOGS = "logs"

CATEGORIES = [CATEGORY_INFRA, CATEGORY_OPENCODE, CATEGORY_OMO, CATEGORY_LOGS]

CATEGORY_LABELS = {
    CATEGORY_INFRA: "인프라",
    CATEGORY_OPENCODE: "OpenCode",
    CATEGORY_OMO: "OmO 플러그인",
    CATEGORY_LOGS: "로그 & 캐시",
}

# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------


def load_config(script_dir: Path) -> Dict[str, Any]:
    config_path = script_dir / "config.json"
    defaults = {
        "vllm_url": "http://10.88.22.29:8000",
        "vllm_model": "Qwen3.5-35B-A3B",
        "opencode_config_dir": "~/.config/opencode",
        "expected_plugin": "oh-my-openagent",
    }
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        defaults.update(user_cfg)
    return defaults


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p)))


def run_command(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """명령 실행 후 (returncode, stdout, stderr) 반환."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=(platform.system() == "Windows"),
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return -1, "", "command not found"
    except subprocess.TimeoutExpired:
        return -2, "", "timeout"
    except Exception as exc:
        return -3, "", str(exc)


def http_get(url: str, timeout: int = 10) -> Tuple[int, str]:
    """HTTP GET 후 (status_code, body) 반환. 실패시 (-1, error_msg)."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:
        return -1, str(exc)


def http_post_json(url: str, payload: Dict[str, Any], timeout: int = 30) -> Tuple[int, str]:
    """HTTP POST JSON 후 (status_code, body) 반환."""
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:
        return -1, str(exc)


def read_jsonc(path: Path) -> Optional[Dict[str, Any]]:
    """JSONC(주석 포함 JSON) 파일을 읽어 dict로 반환. 실패시 None."""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        # 한줄 주석 제거 (// ...)
        text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
        # 블록 주석 제거 (/* ... */)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        # trailing comma 제거
        text = re.sub(r",\s*([}\]])", r"\1", text)
        return json.loads(text)
    except Exception:
        return None


def tail_lines(path: Path, n: int = 200) -> List[str]:
    """파일 마지막 n줄 반환."""
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 결과 객체
# ---------------------------------------------------------------------------


class CheckResult:
    def __init__(
        self,
        check_id: str,
        label: str,
        status: str,
        detail: str = "",
        category: str = "",
    ):
        self.check_id = check_id
        self.label = label
        self.status = status
        self.detail = detail
        self.category = category

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.check_id,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
            "category": self.category,
        }

    def display_line(self) -> str:
        icon = ICON.get(self.status, "?")
        detail_part = f" ({self.detail})" if self.detail else ""
        return f"  {icon} {self.check_id}. {self.label:<20s} {self.status}{detail_part}"


# ---------------------------------------------------------------------------
# A. 인프라 체크
# ---------------------------------------------------------------------------


def check_a1_vllm_endpoint(cfg: Dict[str, Any]) -> CheckResult:
    """A1: vLLM 엔드포인트 접근 (GET /v1/models)"""
    url = cfg["vllm_url"].rstrip("/") + "/v1/models"
    status, body = http_get(url, timeout=10)
    if status == 200:
        return CheckResult("A1", "vLLM 엔드포인트", STATUS_PASS, cfg["vllm_url"], CATEGORY_INFRA)
    return CheckResult("A1", "vLLM 엔드포인트", STATUS_FAIL, f"HTTP {status}: {body[:80]}", CATEGORY_INFRA)


def check_a2_vllm_response(cfg: Dict[str, Any]) -> CheckResult:
    """A2: 모델 응답 테스트 (POST /v1/chat/completions)"""
    url = cfg["vllm_url"].rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": cfg["vllm_model"],
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 8,
    }
    t0 = time.time()
    status, body = http_post_json(url, payload, timeout=30)
    elapsed = time.time() - t0
    if status == 200:
        return CheckResult(
            "A2", "모델 응답", STATUS_PASS,
            f"{cfg['vllm_model']}, {elapsed:.1f}s", CATEGORY_INFRA,
        )
    return CheckResult("A2", "모델 응답", STATUS_FAIL, f"HTTP {status}: {body[:80]}", CATEGORY_INFRA)


# ---------------------------------------------------------------------------
# B. OpenCode 체크
# ---------------------------------------------------------------------------


def check_b1_nodejs(cfg: Dict[str, Any]) -> CheckResult:
    """B1: Node.js 설치 확인"""
    rc, out, err = run_command(["node", "--version"])
    if rc == 0 and out:
        return CheckResult("B1", "Node.js", STATUS_PASS, out, CATEGORY_OPENCODE)
    return CheckResult("B1", "Node.js", STATUS_FAIL, err or "not found", CATEGORY_OPENCODE)


def check_b2_opencode_install(cfg: Dict[str, Any]) -> CheckResult:
    """B2: OpenCode 설치 확인"""
    # opencode --version 시도
    rc, out, err = run_command(["opencode", "--version"])
    if rc == 0 and out:
        return CheckResult("B2", "OpenCode 설치", STATUS_PASS, out.splitlines()[0], CATEGORY_OPENCODE)
    # npm ls -g 시도
    rc2, out2, err2 = run_command(["npm", "ls", "-g", "opencode-ai", "--depth=0"])
    if rc2 == 0 and "opencode-ai" in out2:
        ver = out2.strip().splitlines()[-1].strip()
        return CheckResult("B2", "OpenCode 설치", STATUS_PASS, ver, CATEGORY_OPENCODE)
    return CheckResult("B2", "OpenCode 설치", STATUS_FAIL, "not found", CATEGORY_OPENCODE)


def check_b3_opencode_json(cfg: Dict[str, Any]) -> CheckResult:
    """B3: opencode.json 존재 확인"""
    config_dir = expand_path(cfg["opencode_config_dir"])
    oc_json = config_dir / "opencode.json"
    if oc_json.exists():
        return CheckResult("B3", "opencode.json", STATUS_PASS, str(oc_json), CATEGORY_OPENCODE)
    return CheckResult("B3", "opencode.json", STATUS_FAIL, f"not found: {oc_json}", CATEGORY_OPENCODE)


def check_b4_provider_config(cfg: Dict[str, Any]) -> CheckResult:
    """B4: opencode.json에 provider 설정 확인"""
    config_dir = expand_path(cfg["opencode_config_dir"])
    oc_json = config_dir / "opencode.json"
    data = read_jsonc(oc_json)
    if data is None:
        return CheckResult("B4", "프로바이더 설정", STATUS_SKIP, "opencode.json 없음", CATEGORY_OPENCODE)

    # provider 키 탐색 (다양한 위치)
    providers = data.get("provider") or data.get("providers") or {}
    if providers:
        # dict이면 키 목록, str이면 그대로
        if isinstance(providers, dict):
            names = list(providers.keys())
            return CheckResult("B4", "프로바이더 설정", STATUS_PASS, ", ".join(names), CATEGORY_OPENCODE)
        return CheckResult("B4", "프로바이더 설정", STATUS_PASS, str(providers), CATEGORY_OPENCODE)

    # model 키에서 provider 추론
    model = data.get("model", {})
    if isinstance(model, dict) and model:
        return CheckResult("B4", "프로바이더 설정", STATUS_PASS, str(model), CATEGORY_OPENCODE)

    return CheckResult("B4", "프로바이더 설정", STATUS_WARN, "provider 키 없음", CATEGORY_OPENCODE)


# ---------------------------------------------------------------------------
# C. OmO 플러그인 체크
# ---------------------------------------------------------------------------


def _load_opencode_data(cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    config_dir = expand_path(cfg["opencode_config_dir"])
    return read_jsonc(config_dir / "opencode.json")


def _get_plugin_path(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """opencode.json에서 plugin 경로 문자열 추출."""
    if data is None:
        return None
    # plugins 배열 또는 plugin 문자열
    plugins = data.get("plugins") or data.get("plugin")
    if isinstance(plugins, list):
        for p in plugins:
            if isinstance(p, str):
                return p
            if isinstance(p, dict):
                return p.get("path") or p.get("url") or p.get("source")
        return None
    if isinstance(plugins, str):
        return plugins
    if isinstance(plugins, dict):
        return plugins.get("path") or plugins.get("url") or plugins.get("source")
    return None


def check_c1_plugin_file_path(cfg: Dict[str, Any]) -> CheckResult:
    """C1: plugin이 file:// 로컬 경로인지"""
    data = _load_opencode_data(cfg)
    plugin_path = _get_plugin_path(data)
    if plugin_path is None:
        return CheckResult("C1", "plugin file:// 경로", STATUS_FAIL, "plugin 설정 없음", CATEGORY_OMO)
    if plugin_path.startswith("file://"):
        return CheckResult("C1", "plugin file:// 경로", STATUS_PASS, "", CATEGORY_OMO)
    if plugin_path.startswith("/") or plugin_path.startswith("C:") or plugin_path.startswith("D:"):
        return CheckResult("C1", "plugin file:// 경로", STATUS_WARN, f"file:// 프리픽스 없음: {plugin_path[:60]}", CATEGORY_OMO)
    return CheckResult("C1", "plugin file:// 경로", STATUS_WARN, f"npm 레지스트리 방식?: {plugin_path[:60]}", CATEGORY_OMO)


def check_c2_dist_index_js(cfg: Dict[str, Any]) -> CheckResult:
    """C2: plugin 경로의 dist/index.js 존재"""
    data = _load_opencode_data(cfg)
    plugin_path = _get_plugin_path(data)
    if plugin_path is None:
        return CheckResult("C2", "dist/index.js 존재", STATUS_SKIP, "plugin 경로 없음", CATEGORY_OMO)

    # file:// 접두사 제거
    raw = plugin_path
    if raw.startswith("file://"):
        raw = raw[7:]

    # dist/index.js로 끝나면 그 파일 직접 확인
    check_path = expand_path(raw)
    if check_path.name == "index.js":
        target = check_path
    else:
        target = check_path / "dist" / "index.js"

    if target.exists():
        return CheckResult("C2", "dist/index.js 존재", STATUS_PASS, str(target), CATEGORY_OMO)
    return CheckResult("C2", "dist/index.js 존재", STATUS_FAIL, f"not found: {target}", CATEGORY_OMO)


def _find_omo_config() -> Optional[Path]:
    """oh-my-openagent.jsonc 경로 탐색 (여러 후보)."""
    candidates = [
        Path.cwd() / "oh-my-openagent.jsonc",
        Path.cwd() / ".opencode" / "oh-my-openagent.jsonc",
        expand_path("~/.config/opencode/oh-my-openagent.jsonc"),
        expand_path("~/.config/oh-my-openagent/oh-my-openagent.jsonc"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def check_c3_omo_config_exists(cfg: Dict[str, Any]) -> CheckResult:
    """C3: oh-my-openagent.jsonc 존재 확인"""
    found = _find_omo_config()
    if found:
        return CheckResult("C3", "oh-my-openagent.jsonc", STATUS_PASS, str(found), CATEGORY_OMO)
    return CheckResult("C3", "oh-my-openagent.jsonc", STATUS_FAIL, "not found", CATEGORY_OMO)


def check_c4_sisyphus_model(cfg: Dict[str, Any]) -> CheckResult:
    """C4: agents.sisyphus.model 설정 확인"""
    found = _find_omo_config()
    if not found:
        return CheckResult("C4", "sisyphus 모델 설정", STATUS_SKIP, "config 없음", CATEGORY_OMO)
    data = read_jsonc(found)
    if data is None:
        return CheckResult("C4", "sisyphus 모델 설정", STATUS_FAIL, "파싱 실패", CATEGORY_OMO)

    agents = data.get("agents", {})
    sisyphus = agents.get("sisyphus", {})
    model = sisyphus.get("model")
    if model:
        return CheckResult("C4", "sisyphus 모델 설정", STATUS_PASS, str(model), CATEGORY_OMO)
    return CheckResult("C4", "sisyphus 모델 설정", STATUS_WARN, "model 미설정", CATEGORY_OMO)


def check_c5_sisyphus_not_disabled(cfg: Dict[str, Any]) -> CheckResult:
    """C5: disabled_agents에 sisyphus가 없는지"""
    found = _find_omo_config()
    if not found:
        return CheckResult("C5", "sisyphus 비활성화 없음", STATUS_SKIP, "config 없음", CATEGORY_OMO)
    data = read_jsonc(found)
    if data is None:
        return CheckResult("C5", "sisyphus 비활성화 없음", STATUS_FAIL, "파싱 실패", CATEGORY_OMO)

    disabled = data.get("disabled_agents", [])
    if isinstance(disabled, list) and "sisyphus" in disabled:
        return CheckResult("C5", "sisyphus 비활성화 없음", STATUS_FAIL, "disabled_agents에 sisyphus 포함", CATEGORY_OMO)
    return CheckResult("C5", "sisyphus 비활성화 없음", STATUS_PASS, "", CATEGORY_OMO)


# ---------------------------------------------------------------------------
# D. 로그 & 캐시 체크
# ---------------------------------------------------------------------------


def _omo_log_path() -> Path:
    """OmO 로그 파일 경로 (OS별)."""
    if platform.system() == "Windows":
        tmp = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
        return Path(tmp) / "oh-my-opencode.log"
    return Path("/tmp/oh-my-opencode.log")


def _opencode_log_dir() -> Path:
    """OpenCode 로그 디렉터리."""
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA", expand_path("~/AppData/Local"))
        return Path(local) / "opencode" / "log"
    return expand_path("~/.local/share/opencode/log")


def check_d1_omo_log(cfg: Dict[str, Any]) -> CheckResult:
    """D1: OmO 로그 파일 존재 및 최근 에러 확인"""
    log_path = _omo_log_path()
    if not log_path.exists():
        return CheckResult("D1", "OmO 로그", STATUS_WARN, f"로그 없음: {log_path}", CATEGORY_LOGS)
    lines = tail_lines(log_path, 200)
    errors = [ln for ln in lines if re.search(r"\bERROR\b|\bError\b|\bFATAL\b", ln)]
    if errors:
        last_err = errors[-1][:80]
        return CheckResult("D1", "OmO 로그", STATUS_WARN, f"{len(errors)}개 에러, 최근: {last_err}", CATEGORY_LOGS)
    return CheckResult("D1", "OmO 로그", STATUS_PASS, "에러 없음", CATEGORY_LOGS)


def check_d2_opencode_log(cfg: Dict[str, Any]) -> CheckResult:
    """D2: OpenCode 로그에서 plugin 관련 에러 확인"""
    log_dir = _opencode_log_dir()
    if not log_dir.exists():
        return CheckResult("D2", "OpenCode 로그", STATUS_WARN, f"로그 디렉터리 없음: {log_dir}", CATEGORY_LOGS)
    # 최신 로그 파일 찾기
    log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        log_files = sorted(log_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        return CheckResult("D2", "OpenCode 로그", STATUS_WARN, "로그 파일 없음", CATEGORY_LOGS)
    latest = log_files[0]
    lines = tail_lines(latest, 300)
    plugin_errors = [
        ln for ln in lines
        if re.search(r"plugin", ln, re.IGNORECASE) and re.search(r"error|fail|exception", ln, re.IGNORECASE)
    ]
    if plugin_errors:
        last_err = plugin_errors[-1][:80]
        return CheckResult("D2", "OpenCode 로그", STATUS_WARN, f"{len(plugin_errors)}개 plugin 에러: {last_err}", CATEGORY_LOGS)
    return CheckResult("D2", "OpenCode 로그", STATUS_PASS, "에러 없음", CATEGORY_LOGS)


def check_d3_proxy_error(cfg: Dict[str, Any]) -> CheckResult:
    """D3: 프록시 에러 감지 (proxy.url must be a non-empty string)"""
    PROXY_PATTERN = r"proxy\.url must be a non-empty string"
    paths_to_check = [_omo_log_path()]
    log_dir = _opencode_log_dir()
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if log_files:
            paths_to_check.append(log_files[0])

    for log_path in paths_to_check:
        if not log_path.exists():
            continue
        lines = tail_lines(log_path, 300)
        hits = [ln for ln in lines if re.search(PROXY_PATTERN, ln)]
        if hits:
            return CheckResult("D3", "프록시 에러 없음", STATUS_FAIL, f"발견: {hits[-1][:80]}", CATEGORY_LOGS)

    return CheckResult("D3", "프록시 에러 없음", STATUS_PASS, "", CATEGORY_LOGS)


# ---------------------------------------------------------------------------
# 체크 레지스트리
# ---------------------------------------------------------------------------

CHECK_REGISTRY: Dict[str, List] = {
    CATEGORY_INFRA: [check_a1_vllm_endpoint, check_a2_vllm_response],
    CATEGORY_OPENCODE: [check_b1_nodejs, check_b2_opencode_install, check_b3_opencode_json, check_b4_provider_config],
    CATEGORY_OMO: [check_c1_plugin_file_path, check_c2_dist_index_js, check_c3_omo_config_exists, check_c4_sisyphus_model, check_c5_sisyphus_not_disabled],
    CATEGORY_LOGS: [check_d1_omo_log, check_d2_opencode_log, check_d3_proxy_error],
}


# ---------------------------------------------------------------------------
# 실행 엔진
# ---------------------------------------------------------------------------


def run_checks(categories: Optional[List[str]] = None, cfg: Optional[Dict[str, Any]] = None) -> List[CheckResult]:
    if cfg is None:
        cfg = load_config(Path(__file__).parent)
    if categories is None:
        categories = CATEGORIES

    results: List[CheckResult] = []
    for cat in categories:
        if cat not in CHECK_REGISTRY:
            continue
        for fn in CHECK_REGISTRY[cat]:
            try:
                result = fn(cfg)
            except Exception as exc:
                check_id = fn.__doc__.split(":")[0].strip() if fn.__doc__ else "??"
                result = CheckResult(check_id, fn.__name__, STATUS_FAIL, f"예외: {exc}", cat)
            if not result.category:
                result.category = cat
            results.append(result)
    return results


def print_banner() -> None:
    print()
    print("\u2554" + "\u2550" * 48 + "\u2557")
    print("\u2551  \uc624\ub4dc\ub9ac (Dr. Oh) - OFFCODE \ud658\uacbd \uac80\uc0ac v" + VERSION + "    \u2551")
    print("\u255a" + "\u2550" * 48 + "\u255d")
    print()


def print_results(results: List[CheckResult]) -> None:
    current_cat = ""
    for r in results:
        if r.category != current_cat:
            current_cat = r.category
            label = CATEGORY_LABELS.get(current_cat, current_cat)
            print(f"[{label}]")
        print(r.display_line())
    print()

    pass_count = sum(1 for r in results if r.status == STATUS_PASS)
    fail_count = sum(1 for r in results if r.status == STATUS_FAIL)
    warn_count = sum(1 for r in results if r.status == STATUS_WARN)
    skip_count = sum(1 for r in results if r.status == STATUS_SKIP)
    total = len(results)

    parts = [f"{pass_count}/{total} \ud1b5\uacfc"]
    if fail_count:
        parts.append(f"{fail_count} \uc2e4\ud328")
    else:
        parts.append("0 \uc2e4\ud328")
    if warn_count:
        parts.append(f"{warn_count} \uacbd\uace0")
    else:
        parts.append("0 \uacbd\uace0")
    if skip_count:
        parts.append(f"{skip_count} \uac74\ub108\ub6f0")

    print(f"\uacb0\uacfc: {' | '.join(parts)}")


def print_json(results: List[CheckResult]) -> None:
    output = {
        "version": VERSION,
        "checks": [r.to_dict() for r in results],
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r.status == STATUS_PASS),
            "fail": sum(1 for r in results if r.status == STATUS_FAIL),
            "warn": sum(1 for r in results if r.status == STATUS_WARN),
            "skip": sum(1 for r in results if r.status == STATUS_SKIP),
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _ensure_utf8_stdio() -> None:
    """Windows cp949 등 비-UTF8 콘솔에서 유니코드 출력을 보장."""
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main() -> None:
    _ensure_utf8_stdio()

    parser = argparse.ArgumentParser(
        description="\uc624\ub4dc\ub9ac (Dr. Oh) - OFFCODE \ud658\uacbd \uac80\uc0ac",
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON \ud615\uc2dd\uc73c\ub85c \ucd9c\ub825",
    )
    parser.add_argument(
        "--category",
        choices=CATEGORIES,
        help="\ud2b9\uc815 \uce74\ud14c\uace0\ub9ac\ub9cc \uac80\uc0ac (infra, opencode, omo, logs)",
    )
    parser.add_argument(
        "--config",
        help="config.json \uacbd\ub85c (\uae30\ubcf8: \uc2a4\ud06c\ub9bd\ud2b8 \ub514\ub809\ud130\ub9ac)",
    )
    args = parser.parse_args()

    # 설정 로드
    if args.config:
        cfg_dir = Path(args.config).parent
    else:
        cfg_dir = Path(__file__).parent
    cfg = load_config(cfg_dir)

    # 카테고리 결정
    categories = [args.category] if args.category else None

    # 체크 실행
    results = run_checks(categories, cfg)

    # 출력
    if args.json:
        print_json(results)
    else:
        print_banner()
        print_results(results)

    # 종료 코드: 실패가 있으면 1
    has_fail = any(r.status == STATUS_FAIL for r in results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
