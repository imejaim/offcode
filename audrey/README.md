# 오드리 (Dr. Oh) - OFFCODE 환경 검사 v1.0

사내 폐쇄망 OFFCODE 환경(vLLM + OpenCode + OmO 플러그인)의 상태를 자동 진단하는 도구입니다.

## 요구사항

- Python 3.9+
- 외부 패키지 불필요 (stdlib only)
- Windows / Linux 모두 지원

## 파일 구조

```
audrey/
├── doctor_oh_check.py     # 메인 체크 스크립트
├── README.md              # 이 파일
└── config.json            # 체크 대상 설정 (vLLM URL, 경로 등)
```

## 사용법

```bash
# 전체 체크
python doctor_oh_check.py

# JSON 형식 출력
python doctor_oh_check.py --json

# 카테고리별 실행
python doctor_oh_check.py --category infra      # 인프라만
python doctor_oh_check.py --category opencode   # OpenCode만
python doctor_oh_check.py --category omo        # OmO 플러그인만
python doctor_oh_check.py --category logs       # 로그 & 캐시만

# 별도 config 경로 지정
python doctor_oh_check.py --config /path/to/config.json
```

## 체크 항목 (14개)

### A. 인프라 (2개)

| ID | 항목 | 설명 |
|----|------|------|
| A1 | vLLM 엔드포인트 | `GET /v1/models` 응답 확인 (HTTP 200) |
| A2 | 모델 응답 | `POST /v1/chat/completions` 정상 토큰 생성 확인 |

### B. OpenCode (4개)

| ID | 항목 | 설명 |
|----|------|------|
| B1 | Node.js | `node --version` 실행 가능 여부 |
| B2 | OpenCode 설치 | `opencode --version` 또는 `npm ls -g opencode-ai` |
| B3 | opencode.json | `~/.config/opencode/opencode.json` 존재 여부 |
| B4 | 프로바이더 설정 | opencode.json에 provider(localvllm 등) 설정 확인 |

### C. OmO 플러그인 (5개)

| ID | 항목 | 설명 |
|----|------|------|
| C1 | plugin file:// 경로 | plugin이 `file://` 로컬 경로인지 (npm이면 WARN) |
| C2 | dist/index.js 존재 | plugin 경로의 dist/index.js 실제 존재 여부 |
| C3 | oh-my-openagent.jsonc | OmO 설정 파일 존재 확인 |
| C4 | sisyphus 모델 설정 | `agents.sisyphus.model` 값 확인 |
| C5 | sisyphus 비활성화 없음 | `disabled_agents`에 sisyphus 미포함 확인 |

### D. 로그 & 캐시 (3개)

| ID | 항목 | 설명 |
|----|------|------|
| D1 | OmO 로그 | `%TEMP%/oh-my-opencode.log` (또는 `/tmp/`) 에러 확인 |
| D2 | OpenCode 로그 | `~/.local/share/opencode/log/` plugin 에러 확인 |
| D3 | 프록시 에러 | `proxy.url must be a non-empty string` 감지 |

## 결과 상태

| 상태 | 의미 |
|------|------|
| PASS | 정상 |
| FAIL | 실패 (환경 문제) |
| WARN | 경고 (동작은 하지만 권장하지 않음) |
| SKIP | 건너뜀 (선행 조건 미충족) |

## config.json 설정

```json
{
  "vllm_url": "http://10.88.22.29:8000",
  "vllm_model": "Qwen3.5-35B-A3B",
  "opencode_config_dir": "~/.config/opencode",
  "expected_plugin": "oh-my-openagent"
}
```

| 키 | 설명 | 기본값 |
|----|------|--------|
| `vllm_url` | vLLM 서버 URL | `http://10.88.22.29:8000` |
| `vllm_model` | 테스트할 모델명 | `Qwen3.5-35B-A3B` |
| `opencode_config_dir` | OpenCode 설정 디렉터리 | `~/.config/opencode` |
| `expected_plugin` | 기대하는 플러그인 이름 | `oh-my-openagent` |

## 종료 코드

- `0`: 모든 체크 통과 (WARN은 허용)
- `1`: 하나 이상의 FAIL 존재
