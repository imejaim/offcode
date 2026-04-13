#!/usr/bin/env python3
"""
오드리 (Dr. Oh) - Agentis 환경 검사 v2.3

사내 폐쇄망 Agentis 환경(vLLM + OpenCode + OmO)의 상태를 진단합니다.
Python 3.9+ stdlib만 사용하며, pip install 없이 동작합니다.

사용법:
    python doctor_oh_check.py                        # 전체 체크
    python doctor_oh_check.py --json                 # JSON 출력
    python doctor_oh_check.py --category infra       # 인프라만
    python doctor_oh_check.py --category model       # 모델 검증만
    python doctor_oh_check.py --auto-fix --json      # 자동 수정 + JSON
    python doctor_oh_check.py --project "C:\\myproj"  # 프로젝트 지정

v2.3 변경사항 (v1.0 대비):
    - JSONC 파서 강화: BOM, 인라인 코멘트(문자열 내부 인식), 트레일링 콤마
    - subprocess 타임아웃 30초 + shell=True 폴백
    - 모델 유효성 검증 (E1): 설정된 모델이 vLLM에 실제 존재하는지 확인
    - 외부 API 모델 감지 (E2): 사내 폐쇄망에서 외부 프로바이더 경고
    - --auto-fix: 안전한 모델 자동 교체 (SAFE_MODEL_REPLACEMENTS)
    - --project: 프로젝트 디렉터리 지정
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Windows stdout encoding fix
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

VERSION = "2.31"

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
CATEGORY_MODEL = "model"

CATEGORIES = [CATEGORY_INFRA, CATEGORY_OPENCODE, CATEGORY_OMO, CATEGORY_LOGS, CATEGORY_MODEL]

CATEGORY_LABELS = {
    CATEGORY_INFRA: "인프라",
    CATEGORY_OPENCODE: "OpenCode",
    CATEGORY_OMO: "OmO 플러그인",
    CATEGORY_LOGS: "로그 & 캐시",
    CATEGORY_MODEL: "모델 검증",
}

# ---------------------------------------------------------------------------
# 안전한 모델 교체 맵 (--auto-fix 시 사용)
# ---------------------------------------------------------------------------
SAFE_MODEL_REPLACEMENTS: Dict[str, str] = {
    "opencode/glm-4.7-free": "opencode/gpt-5-nano",
}

# 외부 (사내망 밖) 프로바이더 목록
_EXTERNAL_PROVIDERS = frozenset({
    "openai", "anthropic", "google", "opencode", "azure",
    "deepseek", "groq", "mistral", "cohere", "fireworks",
    "together", "perplexity", "anyscale",
})

# ---------------------------------------------------------------------------
# subprocess 타임아웃
# ---------------------------------------------------------------------------
_DEFAULT_TIMEOUT = 30  # seconds — v2.21에서 이식, 무한 대기 방지


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


def run_command(cmd: List[str], timeout: int = _DEFAULT_TIMEOUT) -> Tuple[int, str, str]:
    """명령 실행 후 (returncode, stdout, stderr) 반환.

    v2.3: shell=True 폴백 + 30초 기본 타임아웃 (v2.21 이식).
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -2, "", f"TIMEOUT after {timeout}s: {' '.join(str(a) for a in cmd)}"
    except FileNotFoundError:
        # shell=True 폴백 (Windows에서 .cmd/.bat 확장자 문제 우회)
        cmdline = " ".join(shlex.quote(str(x)) for x in cmd)
        try:
            proc = subprocess.run(
                cmdline,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                shell=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return -2, "", f"TIMEOUT after {timeout}s: {cmdline}"
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
    """JSONC(주석 포함 JSON) 파일을 읽어 dict로 반환.

    v2.3 강화 (v2.21 이식):
    - utf-8-sig로 BOM 자동 처리
    - 문자열 내부의 // 는 주석으로 취급하지 않음 (char-by-char 파싱)
    - 트레일링 콤마 제거
    """
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            # 전체 줄 주석
            if stripped.startswith("//"):
                continue
            # 인라인 주석 제거 (문자열 내부 인식)
            in_string = False
            escape = False
            result_chars: List[str] = []
            i = 0
            while i < len(line):
                ch = line[i]
                if escape:
                    result_chars.append(ch)
                    escape = False
                    i += 1
                    continue
                if ch == '\\' and in_string:
                    result_chars.append(ch)
                    escape = True
                    i += 1
                    continue
                if ch == '"':
                    in_string = not in_string
                    result_chars.append(ch)
                    i += 1
                    continue
                if not in_string and ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                    break
                result_chars.append(ch)
                i += 1
            lines.append("".join(result_chars))
        cleaned = "\n".join(lines)
        # 블록 주석 제거 (/* ... */)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        # 트레일링 콤마 제거
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        loaded = json.loads(cleaned)
        return loaded if isinstance(loaded, dict) else None
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
# 모델 헬퍼 (v2.21 이식)
# ---------------------------------------------------------------------------


def _collect_configured_models(
    value: object,
    prefix: str = "",
    out: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple[str, str]]:
    """설정 딕셔너리에서 모든 model 값을 재귀적으로 수집. [(scope, model_id), ...]"""
    if out is None:
        out = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key == "model" and isinstance(item, str):
                out.append((prefix or "root", item))
            _collect_configured_models(item, path, out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            _collect_configured_models(item, path, out)
    return out


def _replace_model_value(path: Path, old: str, new: str) -> bool:
    """파일에서 모델 ID 문자열을 안전하게 교체."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    before = text
    text = text.replace(f'"{old}"', f'"{new}"')
    if text == before:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _find_all_config_files(cfg: Dict[str, Any]) -> List[Path]:
    """모델 설정이 들어있을 수 있는 모든 설정 파일 경로 후보."""
    config_dir = expand_path(cfg["opencode_config_dir"])
    candidates = [
        config_dir / "opencode.json",
        config_dir / "opencode.jsonc",
        config_dir / "oh-my-openagent.jsonc",
        config_dir / "oh-my-openagent.json",
        config_dir / "oh-my-opencode.jsonc",
        config_dir / "oh-my-opencode.json",
        Path.cwd() / "opencode.json",
        Path.cwd() / "opencode.jsonc",
        Path.cwd() / ".opencode" / "oh-my-openagent.jsonc",
        Path.cwd() / ".opencode" / "oh-my-opencode.jsonc",
    ]
    return candidates


def _gather_all_configured_models(cfg: Dict[str, Any]) -> List[Tuple[Path, str, str]]:
    """모든 설정 파일에서 (파일경로, scope, model_id) 수집."""
    entries: List[Tuple[Path, str, str]] = []
    seen_paths: set = set()
    for path in _find_all_config_files(cfg):
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        data = read_jsonc(path)
        if data is None:
            continue
        for scope, model in _collect_configured_models(data):
            entries.append((path, scope, model))
    return entries


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
        fix: Optional[str] = None,
    ):
        self.check_id = check_id
        self.label = label
        self.status = status
        self.detail = detail
        self.category = category
        self.fix = fix

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.check_id,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
            "category": self.category,
        }
        if self.fix:
            d["fix"] = self.fix
        return d

    def display_line(self) -> str:
        icon = ICON.get(self.status, "?")
        detail_part = f" ({self.detail})" if self.detail else ""
        fix_part = f"\n       fix: {self.fix}" if self.fix else ""
        return f"  {icon} {self.check_id}. {self.label:<20s} {self.status}{detail_part}{fix_part}"


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

    providers = data.get("provider") or data.get("providers") or {}
    if providers:
        if isinstance(providers, dict):
            names = list(providers.keys())
            return CheckResult("B4", "프로바이더 설정", STATUS_PASS, ", ".join(names), CATEGORY_OPENCODE)
        return CheckResult("B4", "프로바이더 설정", STATUS_PASS, str(providers), CATEGORY_OPENCODE)

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

    raw = plugin_path
    if raw.startswith("file://"):
        raw = raw[7:]

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
        # oh-my-opencode 이름도 탐색 (dual publish)
        Path.cwd() / ".opencode" / "oh-my-opencode.jsonc",
        expand_path("~/.config/opencode/oh-my-opencode.jsonc"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def check_c3_omo_config_exists(cfg: Dict[str, Any]) -> CheckResult:
    """C3: oh-my-openagent.jsonc 존재 확인"""
    found = _find_omo_config()
    if found:
        return CheckResult("C3", "OmO 설정 파일", STATUS_PASS, str(found), CATEGORY_OMO)
    return CheckResult("C3", "OmO 설정 파일", STATUS_FAIL, "not found", CATEGORY_OMO)


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


def _detect_omo_install() -> Tuple[Optional[str], Optional[Path], str]:
    """OmO 설치 정보 자동 감지. (패키지명, 설치경로, 업데이트 명령어) 반환.

    플랫폼별 자동 판단:
    - 윈도우: ~/.config/opencode/node_modules/oh-my-openagent (로컬 설치)
    - 리눅스: $(npm root -g)/oh-my-opencode (글로벌 설치)
    """
    is_win = platform.system() == "Windows"

    # 로컬 설치 탐색 (윈도우 우선)
    local_candidates = [
        ("oh-my-openagent", expand_path("~/.config/opencode/node_modules/oh-my-openagent")),
        ("oh-my-opencode", expand_path("~/.config/opencode/node_modules/oh-my-opencode")),
    ]
    for pkg_name, pkg_path in local_candidates:
        pkg_json = pkg_path / "package.json"
        if pkg_json.exists():
            update_cmd = f"cd {pkg_path.parent.parent} && npm update {pkg_name}"
            return pkg_name, pkg_path, update_cmd

    # 글로벌 설치 탐색 (리눅스 우선)
    rc, out, _ = run_command(["npm", "root", "-g"], timeout=10)
    if rc == 0 and out:
        global_root = Path(out.strip())
        global_candidates = [
            ("oh-my-opencode", global_root / "oh-my-opencode"),
            ("oh-my-openagent", global_root / "oh-my-openagent"),
        ]
        for pkg_name, pkg_path in global_candidates:
            pkg_json = pkg_path / "package.json"
            if pkg_json.exists():
                update_cmd = f"npm update -g {pkg_name}"
                return pkg_name, pkg_path, update_cmd

    return None, None, ""


def _get_installed_omo_version(pkg_path: Path) -> Optional[str]:
    """설치된 OmO 패키지의 버전을 package.json에서 읽기."""
    pkg_json = pkg_path / "package.json"
    if not pkg_json.exists():
        return None
    try:
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        return data.get("version")
    except Exception:
        return None


def _get_latest_omo_version(pkg_name: str) -> Optional[str]:
    """npm 레지스트리에서 최신 버전 조회."""
    url = f"https://registry.npmjs.org/{pkg_name}/latest"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("version")
    except Exception:
        return None


def check_c6_omo_version(cfg: Dict[str, Any], auto_fix: bool = False) -> List[CheckResult]:
    """C6: OmO 버전 확인 및 업데이트 안내.

    - 설치된 버전 확인 (package.json)
    - npm 레지스트리에서 최신 버전 조회
    - 업데이트 필요 시 플랫폼별 명령어 안내
    - --auto-fix 시 자동 업데이트 실행
    """
    results: List[CheckResult] = []
    pkg_name, pkg_path, update_cmd = _detect_omo_install()

    if pkg_name is None or pkg_path is None:
        results.append(CheckResult(
            "C6", "OmO 버전", STATUS_WARN,
            "OmO 설치 경로를 찾지 못함", CATEGORY_OMO,
        ))
        return results

    installed = _get_installed_omo_version(pkg_path)
    if not installed:
        results.append(CheckResult(
            "C6", "OmO 버전", STATUS_WARN,
            f"버전 읽기 실패: {pkg_path}", CATEGORY_OMO,
        ))
        return results

    latest = _get_latest_omo_version(pkg_name)
    if not latest:
        results.append(CheckResult(
            "C6", "OmO 버전", STATUS_PASS,
            f"{pkg_name}@{installed} (최신 버전 조회 실패 — 네트워크 문제?)", CATEGORY_OMO,
        ))
        return results

    if installed == latest:
        results.append(CheckResult(
            "C6", "OmO 버전", STATUS_PASS,
            f"{pkg_name}@{installed} (최신)", CATEGORY_OMO,
        ))
        return results

    # 업데이트 필요
    if auto_fix:
        rc, out, err = run_command(update_cmd.split(), timeout=60)
        if rc == 0:
            new_ver = _get_installed_omo_version(pkg_path) or "?"
            results.append(CheckResult(
                "C6", "OmO 버전", STATUS_PASS,
                f"{pkg_name} 업데이트 완료: {installed} → {new_ver}", CATEGORY_OMO,
            ))
        else:
            results.append(CheckResult(
                "C6", "OmO 버전", STATUS_WARN,
                f"{pkg_name}@{installed} → {latest} 업데이트 실패: {err[:80]}", CATEGORY_OMO,
                fix=update_cmd,
            ))
    else:
        results.append(CheckResult(
            "C6", "OmO 버전", STATUS_WARN,
            f"{pkg_name}@{installed} → {latest} 업데이트 가능", CATEGORY_OMO,
            fix=update_cmd,
        ))

    return results


# ---------------------------------------------------------------------------
# D. 로그 & 캐시 체크
# ---------------------------------------------------------------------------


def _omo_log_path() -> Path:
    if platform.system() == "Windows":
        tmp = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
        return Path(tmp) / "oh-my-opencode.log"
    return Path("/tmp/oh-my-opencode.log")


def _opencode_log_dir() -> Path:
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
# E. 모델 검증 (v2.3 신규 — v2.21 이식)
# ---------------------------------------------------------------------------


def check_e1_configured_models(cfg: Dict[str, Any], auto_fix: bool = False) -> List[CheckResult]:
    """E1: 설정된 모델 유효성 검증 (vLLM 모델 목록 대조).

    - 모든 설정 파일에서 model 값 수집
    - vLLM /v1/models 에서 실제 서빙 모델 확인
    - 불일치 모델 탐지, --auto-fix 시 SAFE_MODEL_REPLACEMENTS 적용
    """
    results: List[CheckResult] = []
    entries = _gather_all_configured_models(cfg)

    if not entries:
        results.append(CheckResult(
            "E1", "모델 설정 수집", STATUS_WARN,
            "설정 파일에서 model 값을 찾지 못함", CATEGORY_MODEL,
        ))
        return results

    results.append(CheckResult(
        "E1", "모델 설정 수집", STATUS_PASS,
        f"{len(entries)}개 모델 설정 발견", CATEGORY_MODEL,
    ))

    # vLLM에서 실제 서빙 중인 모델 가져오기
    vllm_url = cfg["vllm_url"].rstrip("/") + "/v1/models"
    vllm_models: set = set()
    status, body = http_get(vllm_url, timeout=10)
    if status == 200:
        try:
            data = json.loads(body)
            for m in data.get("data", []):
                if isinstance(m, dict) and "id" in m:
                    vllm_models.add(m["id"])
        except Exception:
            pass

    # 각 설정 모델 검증
    invalid: List[Tuple[Path, str, str, str]] = []
    for path, scope, model in entries:
        if "/" not in model:
            continue
        provider, model_id = model.split("/", 1)

        # vLLM 로컬 프로바이더인 경우 실제 모델 존재 확인
        if provider in ("localvllm", "vllm", "local") and vllm_models:
            if model_id not in vllm_models:
                invalid.append((path, scope, model, f"vLLM에 {model_id} 없음, 서빙 중: {', '.join(sorted(vllm_models))}"))

    if invalid:
        detail_parts = [f"{scope}={model} ({reason[:60]})" for _, scope, model, reason in invalid[:3]]
        detail_str = "; ".join(detail_parts)
        fix_text = "opencode.json 또는 oh-my-openagent.jsonc의 model 값을 vLLM 서빙 모델에 맞게 수정"

        if auto_fix:
            changed_items: List[str] = []
            fixed_models: set = set()
            for file_path, scope, model, reason in invalid:
                replacement = SAFE_MODEL_REPLACEMENTS.get(model)
                if not replacement:
                    continue
                if _replace_model_value(file_path, model, replacement):
                    changed_items.append(f"{file_path.name}: {model} → {replacement}")
                    fixed_models.add(model)

            if changed_items:
                results.append(CheckResult(
                    "E1-fix", "모델 자동 수정", STATUS_PASS,
                    f"{len(changed_items)}개 수정: {'; '.join(changed_items[:3])}", CATEGORY_MODEL,
                ))
                # 수정 후 남은 invalid 확인
                remaining = [i for i in invalid if i[2] not in fixed_models]
                if remaining:
                    results.append(CheckResult(
                        "E1-val", "모델 유효성", STATUS_FAIL,
                        f"미해결 {len(remaining)}개: {detail_str[:140]}", CATEGORY_MODEL,
                        fix=fix_text,
                    ))
                else:
                    results.append(CheckResult(
                        "E1-val", "모델 유효성", STATUS_WARN,
                        "자동 수정 완료, 재검사 권장", CATEGORY_MODEL,
                    ))
                return results
            else:
                results.append(CheckResult(
                    "E1-fix", "모델 자동 수정", STATUS_WARN,
                    "안전 교체 매핑 없음 (SAFE_MODEL_REPLACEMENTS)", CATEGORY_MODEL,
                ))

        results.append(CheckResult(
            "E1-val", "모델 유효성", STATUS_FAIL,
            detail_str[:160], CATEGORY_MODEL,
            fix=fix_text,
        ))
    else:
        if vllm_models:
            results.append(CheckResult(
                "E1-val", "모델 유효성", STATUS_PASS,
                f"vLLM 서빙 모델: {', '.join(sorted(vllm_models))}", CATEGORY_MODEL,
            ))
        else:
            results.append(CheckResult(
                "E1-val", "모델 유효성", STATUS_WARN,
                "vLLM 모델 목록 조회 실패, 모델 유효성 미검증", CATEGORY_MODEL,
            ))

    return results


def check_e2_local_model_only(cfg: Dict[str, Any]) -> CheckResult:
    """E2: 외부 API 모델 감지 (사내 폐쇄망 경고).

    설정 파일에서 openai/, anthropic/ 등 외부 프로바이더 모델이
    있으면 경고한다. 폐쇄망에서는 접근 불가이므로.
    """
    entries = _gather_all_configured_models(cfg)
    external: List[Tuple[str, str]] = []

    for _, scope, model in entries:
        if "/" not in model:
            continue
        provider = model.split("/", 1)[0].lower()
        if provider in _EXTERNAL_PROVIDERS:
            external.append((scope, model))

    if external:
        ext_list = ", ".join(f"{model}" for _, model in external[:5])
        return CheckResult(
            "E2", "로컬 모델 전용", STATUS_WARN,
            f"외부 API 모델 감지: {ext_list[:160]}", CATEGORY_MODEL,
            fix="사내 폐쇄망에서는 외부 API 접근 불가. localvllm/ollama 등 로컬 프로바이더 사용 권장",
        )
    return CheckResult(
        "E2", "로컬 모델 전용", STATUS_PASS,
        "외부 API 모델 미참조", CATEGORY_MODEL,
    )


# ---------------------------------------------------------------------------
# 체크 레지스트리
# ---------------------------------------------------------------------------

CHECK_REGISTRY: Dict[str, List] = {
    CATEGORY_INFRA: [check_a1_vllm_endpoint, check_a2_vllm_response],
    CATEGORY_OPENCODE: [check_b1_nodejs, check_b2_opencode_install, check_b3_opencode_json, check_b4_provider_config],
    CATEGORY_OMO: [check_c1_plugin_file_path, check_c2_dist_index_js, check_c3_omo_config_exists, check_c4_sisyphus_model, check_c5_sisyphus_not_disabled],
    CATEGORY_LOGS: [check_d1_omo_log, check_d2_opencode_log, check_d3_proxy_error],
    # C6, E 카테고리는 run_checks에서 별도 처리 (auto_fix 파라미터 필요)
}


# ---------------------------------------------------------------------------
# 실행 엔진
# ---------------------------------------------------------------------------


def run_checks(
    categories: Optional[List[str]] = None,
    cfg: Optional[Dict[str, Any]] = None,
    auto_fix: bool = False,
) -> List[CheckResult]:
    if cfg is None:
        cfg = load_config(Path(__file__).parent)
    if categories is None:
        categories = CATEGORIES

    results: List[CheckResult] = []
    for cat in categories:
        if cat == CATEGORY_MODEL:
            # E 카테고리는 별도 처리
            results.extend(check_e1_configured_models(cfg, auto_fix=auto_fix))
            try:
                results.append(check_e2_local_model_only(cfg))
            except Exception as exc:
                results.append(CheckResult("E2", "로컬 모델 전용", STATUS_FAIL, f"예외: {exc}", CATEGORY_MODEL))
            continue

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

        # C6: OmO 버전 체크 (C 카테고리 끝에 추가, auto_fix 필요)
        if cat == CATEGORY_OMO:
            try:
                results.extend(check_c6_omo_version(cfg, auto_fix=auto_fix))
            except Exception as exc:
                results.append(CheckResult("C6", "OmO 버전", STATUS_FAIL, f"예외: {exc}", CATEGORY_OMO))

    return results


def print_banner() -> None:
    print()
    print("\u2554" + "\u2550" * 48 + "\u2557")
    print("\u2551  \uc624\ub4dc\ub9ac (Dr. Oh) - Agentis \ud658\uacbd \uac80\uc0ac v" + VERSION + "   \u2551")
    print("\u255a" + "\u2550" * 48 + "\u255d")
    print()


def print_results(results: List[CheckResult]) -> None:
    current_cat = ""
    for r in results:
        if r.category != current_cat:
            current_cat = r.category
            label = CATEGORY_LABELS.get(current_cat, current_cat)
            print(f"\n[{label}]")
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

    verdict = "READY" if fail_count == 0 else "NOT_READY"
    print(f"\uacb0\uacfc: {' | '.join(parts)}")
    print(f"\ud310\uc815: {verdict}")


def print_json(results: List[CheckResult]) -> None:
    fail_count = sum(1 for r in results if r.status == STATUS_FAIL)
    output = {
        "version": VERSION,
        "checks": [r.to_dict() for r in results],
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r.status == STATUS_PASS),
            "fail": fail_count,
            "warn": sum(1 for r in results if r.status == STATUS_WARN),
            "skip": sum(1 for r in results if r.status == STATUS_SKIP),
            "verdict": "ready" if fail_count == 0 else "not-ready",
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="\uc624\ub4dc\ub9ac (Dr. Oh) - Agentis \ud658\uacbd \uac80\uc0ac v" + VERSION,
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON \ud615\uc2dd\uc73c\ub85c \ucd9c\ub825",
    )
    parser.add_argument(
        "--category",
        choices=CATEGORIES,
        help="\ud2b9\uc815 \uce74\ud14c\uace0\ub9ac\ub9cc \uac80\uc0ac (infra, opencode, omo, logs, model)",
    )
    parser.add_argument(
        "--config",
        help="config.json \uacbd\ub85c (\uae30\ubcf8: \uc2a4\ud06c\ub9bd\ud2b8 \ub514\ub809\ud130\ub9ac)",
    )
    parser.add_argument(
        "--project", default=".",
        help="\ud504\ub85c\uc81d\ud2b8 \ub514\ub809\ud130\ub9ac (\uae30\ubcf8: \ud604\uc7ac \ub514\ub809\ud130\ub9ac)",
    )
    parser.add_argument(
        "--auto-fix", action="store_true",
        help="\uc548\uc804\ud55c \uc790\ub3d9 \uc218\uc815 \uc2dc\ub3c4 (\ubaa8\ub378 \uad50\uccb4 \ub4f1)",
    )
    args = parser.parse_args()

    # 프로젝트 디렉터리로 이동
    project = Path(args.project).resolve()
    os.chdir(project)

    # 설정 로드
    if args.config:
        cfg_dir = Path(args.config).parent
    else:
        cfg_dir = Path(__file__).parent
    cfg = load_config(cfg_dir)

    # 카테고리 결정
    categories = [args.category] if args.category else None

    # 체크 실행
    results = run_checks(categories, cfg, auto_fix=args.auto_fix)

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
