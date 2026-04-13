# 오드리(Dr. Oh) v3.0 업그레이드 울트라플랜

> 작성일: 2026-04-13
> 작성자: 코부장 @ VDI(10.44.33.205)
> 상태: **계획(PLAN)** — 구현 미착수

---

## 0. 왜 업그레이드가 필요한가 — 실전 오진 사례

2026-04-13 오드리(v2.31)가 다음과 같이 진단:

```
❌ vLLM 서버 ········· 연결 실패 (FAIL)
❌ opencode.json ···· missing (FAIL)
❌ OmO 플러그인 ····· 설정 없음 (FAIL)
⚠️  OmO 버전 ········ 업데이트 필요 (WARN)
⚠️  모델 유효성 ····· 미검증 (WARN)
종합: NOT_READY (4 FAIL, 2 WARN)
```

그러나 **실제로는 같은 시점에 사내 데스크탑에서 Gemma4 31B 시지푸스가 정상 응답**(gist #6095074). 즉 **오드리의 판정은 완전 오진**이었다. 오진 원인:

1. **vLLM 단일 프로바이더 전제** — 오드리는 vLLM이 살아있어야 OK라고 본다. 실제로는 **Ollama로 전환** 완료, vLLM은 백업.
2. **환경 혼동** — 오드리가 돌아간 환경과 시지푸스가 동작하는 환경이 다를 수 있음. 현재 구조는 "1 환경 = 1 오드리 실행" 전제라 이 구분이 없다.
3. **"동작 = OK"를 확인하지 않음** — 오드리는 설정 파일 존재/파싱만 본다. 실제 에이전트가 응답하는지 end-to-end 검증이 없다.

**결론**: 현재 오드리는 *설정의 문법 검사기*이지 *환경의 건강 진단기*가 아니다. v3.0에서 이 철학을 뒤집는다.

---

## 1. 설계 원칙 (v3.0)

1. **프로바이더 중립**: vLLM / Ollama / (향후) TGI, llama.cpp 무엇이든 OpenAI-호환 API면 동일하게 취급. 하드코딩 없음.
2. **"되면 OK"**: 한 경로가 되면 통과. "vLLM이 죽었어도 Ollama로 시지푸스가 응답하면 PASS" 판정 가능.
3. **End-to-end 우선**: 설정 파일 파싱보다 **실제 호출**이 상위 권한. 불일치 시 실제 호출 결과를 기준으로 설정 경고.
4. **환경 자각(self-aware)**: 오드리는 자기가 어느 환경(VDI/데스크탑/노트북/블랙웰)에서 실행되고 있는지 스스로 판단하고 결과에 기록.
5. **멀티 프로바이더 가시화**: 살아있는 프로바이더, 죽은 프로바이더, 현재 사용 중인 프로바이더를 **동시에** 보여준다.
6. **확장 가능한 스키마**: 새 프로바이더 추가 시 코드 변경 없이 config만으로 가능.
7. **후방 호환성**: v2.31 config.json은 읽기 가능해야 함 (마이그레이션 자동).

---

## 2. 현재(v2.31) 구조 요약

```
doctor_oh_check.py (1114 lines)
├── config.json          # vllm_url + vllm_model 단일 키
├── CATEGORY_INFRA       # A1/A2 — vLLM 전용
├── CATEGORY_OPENCODE    # B1~B4 — 설치·설정 존재 확인
├── CATEGORY_OMO         # C1~C5 — 플러그인 경로·jsonc 파싱
├── CATEGORY_LOGS        # D1~D3 — 로그 파싱
└── CATEGORY_MODEL       # E1/E2 — 모델 유효성(vllm_models 세트만)
```

**문제 지점**:
- `config.json` 스키마: 프로바이더 1개만 표현 가능
- `check_a1_vllm_endpoint`: vLLM 고정
- `check_a2_vllm_response`: payload가 Qwen/OpenAI 스타일
- `check_e1_configured_models`: `provider in ("localvllm", "vllm", "local")` 하드코딩
- `check_e2_local_model_only`: ollama는 제외군에도 없음 (경고 없이 통과하나, 인식은 못함)
- `check_b4_provider_config`: "provider 키 존재 = PASS" 수준. **타겟팅(vllm vs ollama)** 구분 없음.

---

## 3. v3.0 목표 구조

### 3.1 config.json (신 스키마, v3)

```jsonc
{
  "schema_version": 3,
  "providers": [
    {
      "name": "ollama",           // 임의 식별자
      "kind": "openai_compatible", // curl /v1/models 방식
      "base_url": "http://10.88.22.29:11434",
      "priority": 1,              // 낮을수록 우선. 2개 이상 살면 "actual" 결정에 사용
      "required": false,          // true면 죽었을 때 FAIL, false면 WARN
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
  "environment_hint": "auto",   // auto | vdi | desktop | laptop | blackwell
  "e2e": {
    "enabled": true,
    "agents": ["sisyphus", "hephaestus", "oracle"],  // 실제로 불러볼 에이전트
    "prompt": "ping",
    "timeout_sec": 60
  }
}
```

### 3.2 v2 → v3 자동 마이그레이션

v2.31 config.json(`vllm_url`/`vllm_model`)을 읽으면 자동으로 providers 배열 1개짜리로 변환하여 내부 사용. config 파일 자체는 건드리지 않음(사용자가 --migrate-config 플래그 줘야 디스크에 저장).

### 3.3 새 카테고리/체크 맵

```
CATEGORY_ENV         # v3 신설
  ENV1  환경 자각 (현재 호스트가 어느 환경인지 판정)
  ENV2  네트워크 가용성 (providers[].base_url 도달성)

CATEGORY_INFRA       # 재구성
  A1    프로바이더 디스커버리 (살아있는 프로바이더 1개+ = PASS)
  A2    프로바이더별 /v1/models 응답
  A3    프로바이더별 /v1/chat/completions 응답 (최소 1개 모델)
  A4    "actual provider" 결정 (가장 우선순위 높은 살아있는 프로바이더)

CATEGORY_OPENCODE    # 유지 + B5 추가
  B1    Node.js
  B2    OpenCode 설치
  B3    opencode.json 존재
  B4    provider 선언 (**v3**: opencode.json의 provider가 실제 살아있는 프로바이더를 가리키는지 교차검증)
  B5    **baseURL 도달성 교차 확인** (opencode.json의 baseURL이 실제 응답하는지. localhost 함정 방지)

CATEGORY_OMO         # 유지 + C5 보강
  C1~C5 (기존)
  C6    **OmO 버전 + 자동 업데이트** (이미 v2.31에 있음, 유지)
  C7    **각 에이전트의 model이 살아있는 프로바이더에 존재**하는지

CATEGORY_LOGS        # 유지
  D1~D3

CATEGORY_MODEL       # 재구성
  E1    설정된 모든 (provider, model) 쌍이 실제 서빙되는지
  E2    외부 API 프로바이더 탐지 (경고)
  E3    **모델 용량 합계 vs GPU 메모리** (힌트 레벨, 선택)

CATEGORY_E2E         # **v3 신설 — 핵심**
  F1    OpenCode 헤드리스(`opencode run` 또는 API) 로 "ping" 전송
  F2    시지푸스 응답 확인 (--agent sisyphus)
  F3    서브에이전트 응답 (헤파이스토스·오라클 선택)
  F4    응답 시간 계측 (첫 토큰, 전체 완료)
```

### 3.4 판정 로직 (종합)

기존: FAIL 1개 있으면 `NOT_READY`.
v3: **"OFFCODE_READY"** 로직:

```
OFFCODE_READY = (
  살아있는 프로바이더 ≥ 1 AND
  opencode.json 존재 AND
  baseURL 도달 가능 AND
  OmO 플러그인 로드 가능 AND
  E2E 시지푸스 응답 성공
)
```

이 5개 중 하나라도 실패하면 NOT_READY. 나머지(WARN/권고 사항)는 READY 판정에 영향 주지 않음. **"시지푸스가 대답하면 READY"가 제1 진실**.

---

## 4. 환경 자각 (ENV1) 설계

오드리가 자기가 어느 환경에서 돌고 있는지 판정하는 규칙:

| 환경 | 판정 규칙 (AND 조건) |
|------|---------------------|
| **VDI** | hostname starts with `VDI` OR 사내 IP 대역(`10.88.*`) 도달 불가 OR 외부망 접근 가능 |
| **블랙웰** | Linux + `nvidia-smi` 에 `RTX PRO 6000 Blackwell` 2장 |
| **사내 데스크탑** | Windows + IP `10.88.21.*` + 10.88.22.29 도달 가능 + GT 1030 (선택) |
| **사내 노트북** | Windows + IP `10.88.22.208` OR `RTX 4070` 감지 |
| **unknown** | 위 어느 것에도 해당 안 됨 |

판정 결과는 JSON 출력 최상단에 `environment` 필드로 기록. 환경에 따라 일부 체크의 **기본값**이 달라짐 (예: VDI에서는 블랙웰 도달 불가가 FAIL 아니라 SKIP).

---

## 5. Phase 구분 (울트라플랜)

### Phase 0 — 현상 파악 및 계약 고정 (0.5일)
- [x] v2.31 오진 사례 수집 (gist #6095097)
- [ ] v3 config 스키마 확정 (본 문서 §3.1)
- [ ] 판정 로직 명세 확정 (본 문서 §3.4)
- [ ] 회장님 리뷰 + 승인
- **산출**: `UPGRADE_PLAN_v3.md` (본 문서), 리뷰 댓글

### Phase 1 — 기반 리팩토링 (1일)
- [ ] `config.json` 스키마 v2/v3 로더 (+ 마이그레이션)
- [ ] 프로바이더 추상화(`Provider` dataclass) + 디스커버리 함수
- [ ] `http_get`/`http_post_json`에 per-provider base_url 주입
- [ ] 기존 A1/A2를 신 구조 위에 래핑 (후방 호환 유지)
- **게이트**: v2.31 config로 실행해도 결과가 바뀌지 않아야 함 (회귀 없음)

### Phase 2 — 신규 체크 구현 (1.5일)
- [ ] A1/A2/A3/A4 (프로바이더 디스커버리·응답·우선순위)
- [ ] B5 (baseURL 도달성 교차 확인) — **localhost 함정 방지**
- [ ] C7 (에이전트 model이 살아있는 프로바이더에 존재)
- [ ] ENV1/ENV2 (환경 자각)
- [ ] E1 재작성 (멀티 프로바이더 대응)
- **게이트**: 실제 데스크탑에서 돌렸을 때 "시지푸스 동작 중"이면 READY가 나와야 함

### Phase 3 — E2E 체크 (F1~F4) (1일)
- [ ] OpenCode 헤드리스 호출 방식 조사 (`opencode run` CLI 또는 4096 API)
- [ ] F1 최소 구현 (ping 프롬프트 전송 + 응답 수신)
- [ ] F2 시지푸스 직접 호출
- [ ] F3 헤파이스토스·오라클 호출
- [ ] F4 첫토큰/완료 시간 계측
- **게이트**: gist #6095074 수준의 응답을 F2가 포착 (실제 Gemma4 31B 응답)

### Phase 4 — 판정 로직 교체 + 출력 재디자인 (0.5일)
- [ ] `OFFCODE_READY` 5축 판정 구현
- [ ] ASCII 진단서에 environment + actual provider + e2e 결과 3개 섹션 추가
- [ ] JSON 출력 스키마 v3 정식화
- **게이트**: 오진 재현 시 PASS 나오는지 검증

### Phase 5 — auto-fix 확장 (0.5일)
- [ ] **localhost → 실제 서버 IP** 치환 (baseURL) — 오늘 발생한 실제 문제
- [ ] Qwen 모델 → Gemma4 치환 매핑
- [ ] 프로바이더 2개 선언되어 있을 때 priority 재정렬 제안
- [ ] `--dry-run` 플래그

### Phase 6 — 테스트 매트릭스 + 배포 (0.5일)
- [ ] 3환경 회귀 테스트 시나리오 작성 (VDI / 데스크탑 / 블랙웰)
  - [ ] VDI: 사내 접속 불가 → ENV만 PASS, 나머지 SKIP
  - [ ] 데스크탑: Gemma4 Ollama 시지푸스 → ALL PASS
  - [ ] 블랙웰: localhost Ollama → ALL PASS
  - [ ] 데스크탑 (고장 시나리오): baseURL localhost → B5 FAIL + auto-fix 제안
- [ ] README / SKILL.md / audrey_prompt.md 업데이트
- [ ] gist에 새 버전 공지

**총 예상 공수**: ~5일 (코부장 집중 작업 기준, 병렬 에이전트 활용 시 단축 가능)

---

## 6. 리스크 및 완화책

| 리스크 | 영향 | 완화책 |
|--------|------|--------|
| OpenCode 헤드리스 호출 방법 불명확 | F1~F4 막힘 | Phase 3 초반에 5분 스파이크로 확인. 안 되면 `opencode run -p` 또는 `bun dev serve` API 경로로 우회 |
| 환경 자각 오판정 (ENV1) | 다른 체크들 기본값 오염 | `--env` 플래그로 강제 지정 가능. auto 실패 시 unknown으로 안전하게 fallback |
| 멀티 프로바이더 디스커버리 타임아웃 | 체크 전체 느려짐 | 병렬 실행 + 각 3초 타임아웃 캡 |
| v2 config 유저 혼란 | 기존 스크립트 실패 | 자동 마이그레이션 + deprecation 경고 + `--config-v2` 호환 모드 |
| E2E가 31B 로드 시간 때문에 실패 | F 카테고리 전체 FAIL | 첫 호출은 warmup 허용(120s), 두 번째부터 타임아웃 엄격 |

---

## 7. 비-목표 (v3.0에서 하지 않는 것)

- GUI 대시보드 (CLI만 유지)
- 원격 오드리 (SSH로 다른 호스트 점검) — v3.1 이후
- 자기 참조 기억(Second_Brain 연계) — 별도 트랙
- 성능 벤치마크 풀 (F4의 응답시간 계측만, 비교 분석 없음)

---

## 8. 팀 편성 (병렬 에이전트 활용)

| 레인 | 담당 | 병렬 dispatch 가능? |
|------|------|---------------------|
| L-SpecReview | 본 계획 리뷰 + 스키마 v3 확정 | 단독 (회장님 피드백 대기) |
| L-Refactor | Phase 1 기반 리팩토링 | 단독 |
| L-NewChecks | Phase 2 신규 체크 구현 | Phase 1 완료 후 |
| L-E2EResearch | OpenCode 헤드리스 호출 조사 | **Phase 1과 병렬 가능** |
| L-TestMatrix | Phase 6 테스트 시나리오 준비 | **Phase 2와 병렬 가능** |

Phase 1 시작할 때 L-E2EResearch를 백그라운드로 먼저 dispatch. Phase 2 들어갈 때 L-TestMatrix도 백그라운드.

---

## 9. 수용 기준 (v3.0 done = READY)

1. 현재(2026-04-13) 사내 데스크탑 환경(Ollama Gemma4 31B 시지푸스 동작 중)에서 `python doctor_oh_check.py` 결과가 **OFFCODE_READY = TRUE**.
2. vLLM을 일부러 내려도(`systemctl stop vllm`) 결과가 유지됨.
3. baseURL을 localhost로 바꾸면 B5 FAIL + 자동수정 제안이 나옴.
4. VDI에서 돌렸을 때 FAIL 없이 ENV=vdi + 관련 체크 SKIP으로 떨어짐 (자기 환경을 안다).
5. 블랙웰에서 돌렸을 때도 같은 로직으로 ALL PASS.
6. 기존 v2.31 config.json으로 돌려도 회귀 없이 동작.

---

## 10. 다음 액션 (본 플랜 승인 후)

1. 회장님 리뷰 + 승인 (본 문서 gist 공유 or 구두)
2. `audrey/` 하위에 `v3/` 디렉터리 분기 (`doctor_oh_check.py` 대신 `doctor_v3.py` 병행 개발)
3. Phase 1 착수 — config 스키마 + 프로바이더 추상화
4. L-E2EResearch 병렬 dispatch
5. v3.0 완성 후 기존 `doctor_oh_check.py`는 `legacy/`로 이동, `v3`을 정식화

---

*본 문서는 오드리 업그레이드의 **계획**입니다. 구현은 승인 후 착수합니다.*
