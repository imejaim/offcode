# 오드리 v3.0 — 테스트 시나리오

> 병렬 작성: Tester 레인
> 계약 기준: `audrey_v3.0/DESIGN.md` (§6 체크 ID 맵, §7 judge)
> 본 문서는 **Python 테스트 코드가 아니라 시나리오 명세**다. Builder가 이 명세를 바탕으로 `test_*.py`를 작성한다.

## 읽는 법

- 각 시나리오는 **사전 상태 → 예상 CheckResult → AGENTIS_READY → 재현 방법** 순서.
- 체크 ID는 `ENV1~F4` (DESIGN.md §6).
- 예상 결과는 `id: STATUS (detail 내 기대 문자열)` 축약 기법을 사용한다. 예: `A1: PASS ("ollama")`.
- 상태가 명시되지 않은 체크 ID는 **해당 시나리오에서 판정에 영향 없음**(기본 PASS 또는 irrelevant).

---

## 환경 시나리오 (4개)

### S1. VDI (10.44.33.205, 사내망 도달 불가)

**환경 설명**: 코부장 상시 작업 환경. 외부망 접근 가능, 사내 10.88.* 대역은 절대 도달 불가. Ollama/vLLM 모두 없음. OpenCode/OmO는 설치는 되어 있을 수 있으나 로컬 LLM 엔드포인트 없음.

**사전 상태**
- hostname: `VDI-xxxxx`
- IP 대역: `10.44.33.*`
- `10.88.22.29:11434` 도달 불가 (타임아웃)
- `~/.config/opencode/opencode.json` 있음, providers 비어있거나 원격 Ollama 설정되어 있음(도달 불가)
- `oh-my-openagent.jsonc` 설치됨
- Ollama 로컬 프로세스 없음, vLLM 없음
- config: `fixtures/opencode.json.ollama_remote.json` 복제본 사용, environment_hint="auto"

**예상 체크 결과**
| ID | 상태 | 기대 detail 조건 |
|----|------|------------------|
| ENV1 | PASS | `kind == "vdi"`, reasoning에 `"10.44"` 또는 `"VDI"` 포함 |
| ENV2 | WARN | 사내 base_url 도달 실패가 나열되되, VDI 컨텍스트이므로 FAIL 아닌 WARN |
| A1 | SKIP | detail에 `"VDI 환경: 사내 프로바이더 건너뜀"` |
| A2 | SKIP | 동일 |
| A3 | SKIP | 동일 |
| A4 | SKIP | `actual_provider == None` |
| B1 | PASS | Node 설치되어 있음 (VDI 표준) |
| B2 | PASS 또는 WARN | opencode 설치 여부에 따라 |
| B3 | PASS | opencode.json 존재 |
| B4 | PASS | provider 선언 존재 (도달성은 따지지 않음) |
| B5 | SKIP | VDI에서는 baseURL 교차검증 SKIP |
| C1~C5 | PASS | 파일/경로 정상 |
| C6 | PASS 또는 WARN | OmO 버전 확인만 |
| C7 | SKIP | 살아있는 프로바이더 없음 → SKIP |
| D1~D3 | PASS 또는 SKIP | 로그 부재 허용 |
| E1 | SKIP | 프로바이더 없음 |
| E2 | PASS | 외부 API 없음 |
| F1~F4 | SKIP | E2E VDI SKIP 규칙 |

**예상 AGENTIS_READY**: **false**
**예상 verdict.reasons**: `["VDI 환경 — 사내 프로바이더 도달 불가로 E2E 건너뜀"]` (NOT READY지만 오진이 아닌 상황 설명)
**예상 verdict.warnings**: ENV2 내용

**검증 방법**
1. `env.detect_environment` 모킹: hostname/IP를 강제 주입하거나 `environment_hint="vdi"` 사용
2. `discover_providers`가 즉시 `alive=False`를 반환하도록 http.py 레벨에서 소켓 실패 유도 (또는 존재하지 않는 IP `10.88.22.29` 사용 + 짧은 timeout)
3. 픽스처: `fixtures/opencode.json.ollama_remote.json`를 임시 디렉터리에 복사 후 `opencode_config_dir` 지정

---

### S2. 사내 데스크탑 (10.88.21.*, Gemma4 31B Ollama 정상)

**환경 설명**: 회장님의 현재 주요 실사용 환경 — gist #6095074 기준. 원격 블랙웰 서버의 Ollama가 Gemma4 시지푸스를 서빙 중. vLLM은 내려가 있음.

**사전 상태**
- hostname: `DESKTOP-XXXX`, OS Windows
- IP: `10.88.21.*`
- `http://10.88.22.29:11434/v1/models` → `gemma4:31b`, `gemma4:26b`, `gemma4:e4b` 응답 (fixtures/provider_responses/ollama_models.json)
- `http://10.88.22.29:8000/v1/models` → 연결 거부 (vLLM down)
- `~/.config/opencode/opencode.json`: provider=ollama, baseURL=`http://10.88.22.29:11434/v1`
- `oh-my-openagent.jsonc`: sisyphus → `ollama/gemma4:31b`
- config: `config.example.v3.json` 기본값

**예상 체크 결과**
| ID | 상태 | 기대 detail 조건 |
|----|------|------------------|
| ENV1 | PASS | `kind == "desktop"` |
| ENV2 | PASS | 10.88.22.29 도달 |
| A1 | PASS | `"ollama"` 포함, `"vllm"` 포함 but `alive=False` (meta에 두 프로바이더 모두 기록) |
| A2 | PASS | detail에 `gemma4:31b` 포함 |
| A3 | PASS | chat/completions 200 OK |
| A4 | PASS | `actual_provider == "ollama"` (priority=1) |
| B1 | PASS | Node 설치 |
| B2 | PASS | OpenCode 설치 |
| B3 | PASS | opencode.json 존재 |
| B4 | PASS | provider=ollama 선언 일치 |
| B5 | PASS | baseURL → 실제 응답 일치 |
| C1 | PASS | file:// 경로 |
| C2 | PASS | 플러그인 파일 존재 |
| C3 | PASS | jsonc 파일 존재 |
| C4 | PASS | sisyphus model=gemma4:31b |
| C5 | PASS | sisyphus disabled 아님 |
| C6 | PASS 또는 WARN | 버전 확인 (업데이트 있으면 WARN) |
| C7 | PASS | `gemma4:31b` ∈ served_models |
| D1~D3 | PASS | 로그 확인 |
| E1 | PASS | 모든 (provider,model) 쌍 서빙 확인 |
| E2 | PASS | 외부 API 없음 |
| F1 | PASS | 헤드리스 ping 응답 |
| F2 | PASS | 시지푸스 응답, detail에 `"Gemma4"` 또는 `"31b"` 포함 |
| F3 | PASS | 헤파이스토스 응답 |
| F4 | PASS | latency_ms 기록 |

**예상 AGENTIS_READY**: **true**
**예상 verdict.warnings**: `["vllm 프로바이더 응답 없음 (priority=2, 필수 아님)"]`

**검증 방법**
1. `http.http_get/http_post_json`를 모킹해서 10.88.22.29:11434는 fixture 응답, 10.88.22.29:8000은 `ConnectionRefused` 유도
2. `tempfile.TemporaryDirectory`에 `opencode.json.ollama_remote.json`, `oh-my-openagent.jsonc.gemma4_tiered.json` 배치
3. 또는 `tests/fixtures/provider_server.py`(Builder가 작성)를 `http.server`로 띄워 11434 포트 대신 임의 포트 + monkey-patched base_url
4. **이 시나리오는 수용 기준 #1** — 반드시 PASS해야 함

---

### S3. 사내 노트북 (4070, 원격 Ollama, 테스트베드)

**환경 설명**: 본인 노트북, RTX 4070, 주로 코드 작성/테스트. Ollama는 로컬에도 설치되어 있으나 주로 10.88.22.29 원격 사용.

**사전 상태**
- hostname: `LAPTOP-XXXX`, OS Windows
- IP: `10.88.22.208`
- `nvidia-smi`에 `RTX 4070` 표시
- 원격 Ollama `10.88.22.29:11434` 도달
- 로컬 `127.0.0.1:11434` Ollama도 살아있을 수 있으나 config 상으로는 원격 사용
- vLLM 원격(`:8000`) 사망
- opencode.json: 원격 Ollama 설정

**예상 체크 결과**
| ID | 상태 | 기대 detail 조건 |
|----|------|------------------|
| ENV1 | PASS | `kind == "laptop"`, reasoning에 `"4070"` 또는 `"10.88.22.208"` 포함 |
| ENV2~F4 | S2와 동일 (PASS) | |

**예상 AGENTIS_READY**: **true**
(S2와 동일한 판정이지만 ENV1 자각 결과가 다르다는 점을 회귀 포인트로 잡음)

**검증 방법**
- S2와 동일하되, `detect_environment` 스텁에서 hostname/IP/GPU 힌트를 노트북으로 주입.
- 목적: ENV1 분기가 actual_provider 결정/F2 판정에 악영향을 주지 않음을 검증.

---

### S4. 블랙웰 서버 (Linux, localhost Ollama)

**환경 설명**: Gemma4 serving 실서버. Linux, `nvidia-smi`에 Blackwell 2장. Ollama는 localhost:11434에서 돌고 있음.

**사전 상태**
- hostname: `blackwell-01` (또는 `svc-gpu-*`)
- OS Linux
- `nvidia-smi` 문자열에 `Blackwell`
- `http://127.0.0.1:11434/v1/models` → Gemma4 3종 응답
- vLLM 없음
- opencode.json: providers[0].base_url = `http://127.0.0.1:11434` (**localhost가 정답**인 유일한 환경)
- oh-my-openagent.jsonc: sisyphus → `ollama/gemma4:31b`

**예상 체크 결과**
| ID | 상태 | 기대 detail 조건 |
|----|------|------------------|
| ENV1 | PASS | `kind == "blackwell"`, reasoning에 `"Blackwell"` 포함 |
| ENV2 | PASS | localhost 도달 |
| A1~A4 | PASS | actual_provider="ollama" (localhost) |
| B5 | **PASS** | localhost baseURL이 실제 응답하므로 이 환경에서는 함정 아님 |
| 그 외 | PASS | S2와 동일 |
| F1~F4 | PASS | localhost 응답 |

**예상 AGENTIS_READY**: **true**

**검증 방법**
1. `detect_environment` 스텁에 Linux + Blackwell 힌트 주입
2. base_url=`http://127.0.0.1:<임시포트>`로 `http.server` 기반 가짜 Ollama를 띄워 A1~A3 통과
3. **중요**: 이 시나리오는 "localhost baseURL이 항상 FAIL이 아님"을 보증. R2와 구별되는 지점.

---

## 회귀 시나리오 (4개)

### R1. v2.31 config.json 그대로 실행 (후방 호환)

**사전 상태**
- `--config fixtures/config.v2.json`
- 나머지 환경은 S2 (사내 데스크탑, Ollama 살아있음)

**예상 동작**
- `config.load_config`가 `schema_version` 없음 + `vllm_url` 존재 감지 → `migrate_v2_to_v3()` 내부 호출
- 변환된 Config는 providers 1개 (`vllm`, base_url=`http://10.88.22.29:8000`)
- 디스크에는 쓰기 없음

**예상 체크 결과**
- ENV1 PASS
- A1 FAIL 또는 WARN: `vllm` 프로바이더 alive=False (vLLM 내려가 있음)
- A4: `actual_provider == None`
- AGENTIS_READY: **false** (프로바이더 0개)
- **그러나** — v2.31 시절 같은 config로 돌렸을 때도 `NOT_READY`였으므로 **회귀 없음**이 성립
- detail에 `"v2 config detected; migrated to v3 in-memory"` 로그

**검증 방법**
- `fixtures/config.v2.json` 로드 + tmp 환경
- `config.migrate_v2_to_v3` 단위 테스트 병행 (입력 dict → 출력 dict 동치)
- 회귀 기준: v2.31 `doctor_oh_check.py`를 같은 환경에서 돌렸을 때의 결과와 5축 판정이 **동일**해야 함

---

### R2. baseURL localhost 함정 (오늘 발생한 실제 버그)

**사전 상태**
- 사내 데스크탑 S2 환경
- **BUT** `opencode.json`의 `baseURL = "http://localhost:11434/v1"` (fixtures/opencode.json.localhost_trap.json)
- 실제 Ollama는 원격 10.88.22.29에 있음, 로컬 127.0.0.1:11434에는 아무것도 없음

**예상 체크 결과**
| ID | 상태 | detail 기대 |
|----|------|------------|
| A1 | PASS | discover_providers는 config.providers를 보므로 10.88.22.29 alive |
| B3 | PASS | 파일 존재 |
| B4 | WARN | opencode.json provider는 선언됨 |
| **B5** | **FAIL** | detail에 `"localhost:11434 도달 불가"` + `"실제 프로바이더는 10.88.22.29"` |
| B5.fix | **not None** | `"baseURL을 http://10.88.22.29:11434/v1 로 치환 제안"` |
| C7 | WARN 또는 FAIL | 에이전트가 가리키는 provider가 실제로는 죽은 localhost |
| F1 | FAIL | 헤드리스 호출 시 OpenCode가 localhost로 찌름 → 실패 |
| F2 | FAIL | 시지푸스 응답 없음 |

**예상 AGENTIS_READY**: **false**
**예상 verdict.reasons**: `["B5 FAIL — baseURL localhost 함정", "F2 FAIL — 시지푸스 무응답"]`
**예상 autofix 후보**: B5.fix

**검증 방법**
1. `fixtures/opencode.json.localhost_trap.json`을 tmp에 배치
2. http mock: 10.88.22.29 응답, 127.0.0.1 응답 없음
3. **핵심 검증**: `result.fix`가 None이 아니고, `--auto-fix` 모드에서 치환 후 재실행 시 PASS
4. 수용 기준 #3 대응 시나리오

---

### R3. provider=`localvllm` 구 Qwen 스타일인데 실제로는 Ollama 살아있음

**사전 상태**
- `opencode.json`: `provider="localvllm"`, `baseURL="http://10.88.22.29:8000/v1"`, `model="Qwen3.5-35B-A3B"` (fixtures/opencode.json.qwen_legacy.json)
- 실제로는 vLLM 다운, Ollama는 10.88.22.29:11434에서 Gemma4 서빙 중
- config.v3의 providers에는 ollama, vllm 둘 다 선언

**예상 체크 결과**
| ID | 상태 | detail 기대 |
|----|------|------------|
| A1 | PASS | ollama alive, vllm dead |
| A4 | PASS | actual=ollama |
| B4 | WARN | provider=localvllm인데 살아있는 프로바이더는 ollama |
| B5 | FAIL | vllm:8000 도달 불가 |
| **C7** | **WARN** | detail에 `"Qwen3.5-35B-A3B"`, `"프로바이더 vllm이 죽었음"`, 추천: `"ollama/gemma4:31b"` |
| E1 | WARN | 설정된 모델이 어떤 살아있는 프로바이더에도 없음 |

**예상 AGENTIS_READY**: **false**
**예상 autofix**: provider 블록을 ollama로 재작성하는 제안 (dry-run 텍스트)

**검증 방법**
- fixture + http mock
- `judge()`가 "프로바이더 있음 but 엔드포인트 불일치"를 구별하는지 확인 (단순히 A1만 보고 READY 치면 안 됨)

---

### R4. 멀티 프로바이더 동시 생존 (Ollama + vLLM 둘 다 alive)

**사전 상태**
- 10.88.22.29:11434 Ollama alive (Gemma4 3종)
- 10.88.22.29:8000 vLLM alive (Qwen3.5-35B-A3B)
- config.v3 providers: ollama(priority=1), vllm(priority=2)
- opencode.json: provider=ollama

**예상 체크 결과**
| ID | 상태 | detail 기대 |
|----|------|------------|
| A1 | PASS | detail에 `"2/2 alive"`, meta.provider_statuses 길이 2 둘 다 alive=True |
| A2 | PASS | 두 프로바이더 각각 /v1/models 응답 모델 리스트 기록 |
| A3 | PASS | 두 프로바이더 모두 chat 응답 |
| **A4** | **PASS** | `actual_provider == "ollama"` (priority=1 선택) |
| C7 | PASS | gemma4:31b ∈ ollama.served_models |
| E2 | PASS | 외부 API 없음 |
| F2 | PASS | 시지푸스 응답 (ollama 사용) |

**예상 AGENTIS_READY**: **true**
**예상 verdict.warnings**: `["vllm도 alive — priority=2로 대기 중"]` (정보성)

**검증 방법**
- 두 mock 서버 동시 기동 (또는 http mock에 양쪽 응답 세팅)
- `pick_actual_provider` 로직 검증: priority 오름차순, tie-breaker는 name 사전순
- **중요**: R4는 "정답" 시나리오 — 시스템이 잘 설계됐는지 확인하는 골든 케이스

---

## 시나리오 매트릭스 요약

| 시나리오 | ENV | 프로바이더 상태 | baseURL | READY | 주요 검증 포인트 |
|----------|-----|-----------------|---------|-------|------------------|
| S1 | vdi | 없음 | 원격(불가) | false | VDI 자각 + SKIP 분기 |
| S2 | desktop | ollama alive, vllm dead | 원격 정상 | **true** | 수용 기준 #1, 메인 골든 케이스 |
| S3 | laptop | ollama alive | 원격 정상 | true | ENV 분기가 판정 오염 안 함 |
| S4 | blackwell | localhost ollama alive | localhost(정답) | true | localhost가 항상 FAIL 아님 |
| R1 | desktop | vllm dead (v2 config) | - | false | v2→v3 마이그레이션 회귀 없음 |
| R2 | desktop | ollama alive | **localhost(함정)** | false | B5 FAIL + autofix |
| R3 | desktop | ollama alive, vllm dead | vllm(불일치) | false | provider/endpoint 불일치 탐지 |
| R4 | desktop | 둘 다 alive | 원격 정상 | **true** | priority 선택 로직 |
