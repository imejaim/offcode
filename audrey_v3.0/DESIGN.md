# 오드리 v3.0 — 인터페이스 계약 (DESIGN CONTRACT)

> 병렬 작업 시 **모든 에이전트/구현자가 이 문서의 타입을 정확히 지켜야 한다.**
> 변경은 본 문서부터. 코드 쪽에서 임의로 바꾸면 통합 시 회귀.

---

## 0. Python 공통 규칙

- Python 3.9+, **stdlib only** (v2.31과 동일 제약)
- 모든 체크는 **네트워크/파일 부재에도 예외 없이 CheckResult 반환**
- 타입힌트 필수 (`from __future__ import annotations`)
- 외부 프로세스 호출은 `run_command()` 공용 함수 사용(30초 타임아웃 + shell 폴백, v2.31에서 이식)

---

## 1. `result.py` — CheckResult

```python
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"

CATEGORY_ENV      = "env"
CATEGORY_INFRA    = "infra"
CATEGORY_OPENCODE = "opencode"
CATEGORY_OMO      = "omo"
CATEGORY_LOGS     = "logs"
CATEGORY_MODEL    = "model"
CATEGORY_E2E      = "e2e"

@dataclass
class CheckResult:
    id: str                    # "A1", "ENV1", "F2" 등
    name: str                  # 사람이 읽는 이름
    status: str                # STATUS_*
    detail: str                # 한 줄 설명/값
    category: str              # CATEGORY_*
    fix: Optional[str] = None  # 자동수정 가능한 경우 제안 텍스트
    meta: dict[str, Any] = field(default_factory=dict)  # 확장 정보

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

**불변식**: `status`는 반드시 4개 상수 중 하나. `category`도 상수 중 하나.

---

## 2. `provider.py` — Provider 추상화

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Provider:
    name: str                          # 임의 식별자 ("ollama", "vllm" 등)
    kind: str                          # "openai_compatible" (현재 유일)
    base_url: str                      # "http://10.88.22.29:11434"
    priority: int = 1                  # 낮을수록 우선
    required: bool = False             # True면 죽었을 때 FAIL
    expected_models: list[str] = field(default_factory=list)

    @property
    def models_url(self) -> str:
        return self.base_url.rstrip("/") + "/v1/models"

    @property
    def chat_url(self) -> str:
        return self.base_url.rstrip("/") + "/v1/chat/completions"


@dataclass
class ProviderStatus:
    provider: Provider
    alive: bool
    served_models: list[str]   # 실제 서빙 중인 모델 ID
    latency_ms: Optional[int] = None
    error: Optional[str] = None


def discover_providers(providers: list[Provider], timeout: float = 3.0) -> list[ProviderStatus]:
    """병렬로 각 프로바이더에 GET /v1/models. 결과 리스트 반환. 예외 삼킴."""
    ...


def pick_actual_provider(statuses: list[ProviderStatus]) -> Optional[ProviderStatus]:
    """alive=True 중 priority 오름차순으로 첫 번째 선택."""
    ...
```

---

## 3. `config.py` — v2/v3 로더

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class E2EConfig:
    enabled: bool = True
    agents: list[str] = field(default_factory=lambda: ["sisyphus"])
    prompt: str = "ping"
    timeout_sec: int = 60

@dataclass
class Config:
    schema_version: int
    providers: list[Provider]
    opencode_config_dir: Path
    expected_plugin: str
    environment_hint: str      # "auto" | "vdi" | "desktop" | "laptop" | "blackwell"
    e2e: E2EConfig


def load_config(path: Path) -> Config:
    """JSON 파일을 읽어 Config 반환.

    - schema_version=3이면 그대로 파싱
    - schema_version 없음 + vllm_url 존재 → v2로 간주 → v3로 내부 마이그레이션
    - 잘못된 스키마 → 명확한 예외 (ValueError)
    """
    ...


def migrate_v2_to_v3(v2_data: dict) -> dict:
    """v2 dict → v3 dict 변환. 디스크 쓰기 없음."""
    ...
```

**v3 예시 파일**: `config.example.v3.json`

```json
{
  "schema_version": 3,
  "providers": [
    {
      "name": "ollama",
      "kind": "openai_compatible",
      "base_url": "http://10.88.22.29:11434",
      "priority": 1,
      "required": false,
      "expected_models": ["gemma4:31b", "gemma4:26b", "gemma4:e4b"]
    },
    {
      "name": "vllm",
      "kind": "openai_compatible",
      "base_url": "http://10.88.22.29:8000",
      "priority": 2,
      "required": false,
      "expected_models": []
    }
  ],
  "opencode_config_dir": "~/.config/opencode",
  "expected_plugin": "oh-my-openagent",
  "environment_hint": "auto",
  "e2e": {
    "enabled": true,
    "agents": ["sisyphus", "hephaestus", "oracle"],
    "prompt": "ping",
    "timeout_sec": 60
  }
}
```

---

## 4. `env.py` — 환경 자각

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class EnvironmentInfo:
    kind: str                 # "vdi" | "desktop" | "laptop" | "blackwell" | "unknown"
    hostname: str
    os: str                   # "Windows" | "Linux" | ...
    ip_hints: list[str]
    gpu_hint: Optional[str]   # "RTX PRO 6000 Blackwell" 등
    reasoning: str            # 왜 이렇게 판정했는지 한 줄


def detect_environment(hint: str = "auto") -> EnvironmentInfo:
    """hint가 'auto'면 규칙 기반 판정, 아니면 강제 지정."""
    ...
```

**판정 규칙**:
- VDI: hostname에 `VDI` 포함 OR IP `10.44.*` OR 외부망 reachable
- 블랙웰: Linux + `nvidia-smi` 에 `Blackwell` 문자열
- 사내 데스크탑: Windows + IP `10.88.21.*` + `10.88.22.29:11434` 도달
- 사내 노트북: Windows + `RTX 4070` 또는 IP `10.88.22.208`
- 위 어느 것도 아니면 `unknown`

---

## 5. `checks/*.py` — 체크 함수 시그니처

모든 체크 함수는:

```python
def check_<id>_<short>(cfg: Config, ctx: CheckContext) -> CheckResult:
    ...
```

또는 다중 결과 반환이 필요한 경우:

```python
def check_<id>_<short>(cfg: Config, ctx: CheckContext) -> list[CheckResult]:
    ...
```

**CheckContext**: 이전 체크 결과를 공유하는 객체 (Provider 디스커버리 결과 등 재사용).

```python
@dataclass
class CheckContext:
    env: EnvironmentInfo
    provider_statuses: list[ProviderStatus]
    actual_provider: Optional[ProviderStatus]
    opencode_json: Optional[dict]       # 파싱된 opencode.json
    omo_config: Optional[dict]          # 파싱된 oh-my-openagent.jsonc
    auto_fix: bool = False
```

---

## 6. 체크 ID 맵 (고정)

| ID | 이름 | 카테고리 | 파일 |
|----|------|----------|------|
| ENV1 | 환경 자각 | env | `checks/env.py` |
| ENV2 | 네트워크 가용성 | env | `checks/env.py` |
| A1 | 프로바이더 디스커버리 | infra | `checks/infra.py` |
| A2 | 프로바이더 /v1/models 응답 (N개) | infra | `checks/infra.py` |
| A3 | 프로바이더 /v1/chat/completions 응답 | infra | `checks/infra.py` |
| A4 | actual provider 결정 | infra | `checks/infra.py` |
| B1 | Node.js | opencode | `checks/opencode.py` |
| B2 | OpenCode 설치 | opencode | `checks/opencode.py` |
| B3 | opencode.json 존재 | opencode | `checks/opencode.py` |
| B4 | provider 선언 | opencode | `checks/opencode.py` |
| B5 | **baseURL 도달성 교차 확인** | opencode | `checks/opencode.py` |
| C1 | plugin file:// 경로 | omo | `checks/omo.py` |
| C2 | plugin 파일 존재 | omo | `checks/omo.py` |
| C3 | OmO 설정 파일 존재 | omo | `checks/omo.py` |
| C4 | sisyphus 모델 설정 | omo | `checks/omo.py` |
| C5 | sisyphus 비활성화 없음 | omo | `checks/omo.py` |
| C6 | OmO 버전 + 업데이트 | omo | `checks/omo.py` |
| C7 | 에이전트 model이 살아있는 프로바이더에 존재 | omo | `checks/omo.py` |
| D1 | OmO 로그 | logs | `checks/logs.py` |
| D2 | OpenCode 로그 | logs | `checks/logs.py` |
| D3 | 프록시 에러 | logs | `checks/logs.py` |
| E1 | 멀티 프로바이더 모델 유효성 | model | `checks/model.py` |
| E2 | 외부 API 프로바이더 탐지 | model | `checks/model.py` |
| F1 | OpenCode 헤드리스 ping | e2e | `checks/e2e.py` |
| F2 | 시지푸스 응답 | e2e | `checks/e2e.py` |
| F3 | 서브에이전트 응답 | e2e | `checks/e2e.py` |
| F4 | 응답시간 계측 | e2e | `checks/e2e.py` |

---

## 7. `judge.py` — AGENTIS_READY 판정

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Verdict:
    ready: bool
    reasons: list[str]     # READY 아닌 경우 왜 아닌지
    warnings: list[str]    # READY여도 경고 남아있을 수 있음


def judge(results: list[CheckResult]) -> Verdict:
    """AGENTIS_READY 5축 판정.

    READY = (
        살아있는 프로바이더 ≥ 1 AND     # A1 PASS
        opencode.json 존재 AND         # B3 PASS
        baseURL 도달 가능 AND           # B5 PASS
        OmO 플러그인 로드 AND           # C2 PASS
        시지푸스 F2 PASS
    )

    이 5개 중 하나라도 FAIL이면 NOT READY.
    나머지는 warnings로.
    """
    ...
```

---

## 8. `report.py` — 출력

두 모드:

1. **ASCII 진단서** (기본)
2. **JSON** (`--json`)

ASCII 진단서 템플릿:

```
╔══════════════════════════════════════════════════════╗
║        Agentium 환경 진단서 — Dr. Oh v3.0            ║
╠══════════════════════════════════════════════════════╣
║  환경: {env.kind} ({env.hostname}, {env.os})         ║
║  일시: {iso_date}                                    ║
║  실사용 프로바이더: {actual.name} @ {actual.base_url}║
╠══════════════════════════════════════════════════════╣
║  [ENV]                                               ║
║  {PASS/WARN/FAIL} ENV1 환경 자각                     ║
║  ...                                                 ║
║  [INFRA]                                             ║
║  ...                                                 ║
║  [E2E]                                               ║
║  {✅/❌} F2 시지푸스 응답 (34.2s)                     ║
╠══════════════════════════════════════════════════════╣
║  AGENTIS_READY: TRUE                                 ║
║                                                      ║
║  경고: ...                                           ║
╚══════════════════════════════════════════════════════╝
```

JSON 포맷:

```json
{
  "schema_version": 3,
  "run_at": "2026-04-13T05:12:33Z",
  "environment": { ... EnvironmentInfo ... },
  "providers": [ ... ProviderStatus ... ],
  "actual_provider": "ollama",
  "results": [ ... CheckResult ... ],
  "verdict": {
    "ready": true,
    "reasons": [],
    "warnings": ["..."]
  }
}
```

---

## 9. 통합 포인트 (누가 누구를 부르는가)

```
__main__.py
  ├── load_config()            (config.py)
  ├── detect_environment()     (env.py)
  ├── discover_providers()     (provider.py)
  ├── pick_actual_provider()   (provider.py)
  ├── build CheckContext
  ├── run all checks (categories order: env → infra → opencode → omo → logs → model → e2e)
  ├── judge()                  (judge.py)
  ├── autofix.apply()          (autofix.py, --auto-fix 시)
  └── report.emit()            (report.py)
```

---

## 10. 금지사항

- `requests`, `httpx`, `pydantic` 등 외부 패키지 import 금지
- `print()` 직접 호출 금지 → `report.py`만 출력
- `exit()` 내부 금지 → `__main__.py`에서만 종료코드 결정
- 체크 함수에서 `raise` 금지 → 모두 `CheckResult(FAIL, detail=str(e))`로 포장
- 글로벌 상태 금지 → 모든 상태는 `Config`/`CheckContext`를 통해 흐름

---

*이 문서는 살아있는 계약(living contract)입니다. 병렬 작업 시 변경은 먼저 본 문서부터.*
