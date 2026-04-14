# 05. 오드리 (Dr. Oh) v3.1 — Agentium 헬스체크

## 재설계 트리거

2026-04-13 v2.31이 사내 데스크탑에서 **시지푸스가 Gemma4 31B로 정상 동작 중인데** "vLLM 연결 실패 / opencode.json missing / OmO 설정 없음"으로 오진. 근본 원인: **vLLM 단일 프로바이더 하드코딩**, 설정 파싱만 하고 실제 동작 무시.

이 사건이 v3.0 재설계의 직접 계기이며, 설계 철학을 **"설정 문법 검사기" → "환경 건강 진단기"** 로 전환.

## 7가지 설계 원칙

1. **프로바이더 중립** — vLLM/Ollama/TGI 동등, 하드코딩 없음
2. **"되면 OK"** — 한 경로가 되면 통과. 나머지는 WARN
3. **End-to-end 우선** — 설정 파싱보다 실제 호출이 상위 권한
4. **환경 자각** — VDI/데스크탑/노트북/블랙웰 자체 판정
5. **멀티 프로바이더 가시화** — 살아있음/죽음/실사용 동시 표시
6. **확장 가능** — 새 프로바이더는 config만 추가
7. **후방 호환** — v2.31 config.json 자동 마이그레이션

## AGENTIS_READY 5축 판정

```
READY = 살아있는 프로바이더 ≥ 1   (A1 PASS)
        AND opencode.json/jsonc 존재 (B3 PASS)
        AND baseURL 실제 도달 가능  (B5 PASS)
        AND OmO 플러그인 로드      (C2 PASS)
        AND 시지푸스 F2 PASS       (← 제1 진실)
```

이 5개 중 하나라도 FAIL이면 NOT READY. 나머지는 warnings로 분리.

## 체크 ID 맵 (7 카테고리)

| 카테고리 | IDs | 요약 |
|----------|-----|------|
| ENV  | ENV1, ENV2 | 환경 자각 + 네트워크 가용성 |
| INFRA | A1, A2, A3, A4 | 프로바이더 디스커버리/응답/우선순위 |
| OPENCODE | B1, B2, B3, B4, B5 | Node/OpenCode/jsonc/provider/**baseURL 교차** |
| OMO | C1, C2, C3, C4, C5, C6, C7 | 플러그인/jsonc/모델 교차확인 |
| LOGS | D1, D2, D3 | OmO/OpenCode/proxy 에러 스캔 |
| MODEL | E1, E2 | 멀티 프로바이더 유효성 + 외부 API 탐지 |
| E2E | F1, F2, F3, F4 | **헤드리스 ping / 시지푸스 / 서브에이전트 / 응답시간** |

## 핵심 체크 몇 개

### B5 — baseURL 도달성 교차 확인 (신설)
`opencode.json/jsonc`의 provider baseURL을 **실제로 probe**한다. localhost인데 alive non-local 프로바이더가 존재하면 FAIL + autofix 제안.
`/v1`로 끝나는 URL은 `/models`만 덧붙여 이중 `/v1/v1` 방지 (v3.1 패치).

### F1/F2 — E2E 헤드리스 ping (Scout 확정 전략)
`opencode run --format json --agent sisyphus "ping"` 서브프로세스. NDJSON stdout 파싱, `type:"text"` 이벤트를 수집. 2026-04-13 블랙웰에서 15.7~18.1초로 실검증 완료.
폴백: `opencode serve` HTTP API (4096) → `opencode --headless --prompt`.

### ENV1 — 환경 자각
IP + hostname + nvidia-smi 기반. VDI(10.44.*), 블랙웰(Ubuntu+RTX PRO 6000), 데스크탑(10.88.21.*), 노트북(10.88.22.208 or RTX 4070) 규칙.

## v3.0 → v3.1 패치

- **B3 `.jsonc` 지원** — OpenCode upstream `config.ts:1071`은 `opencode.jsonc > opencode.json > config.json` 순 공식 지원. v3.0은 `.json`만 보고 false FAIL.
- **B5 probe 정규화** — baseURL이 이미 `/v1`로 끝나면 중복 제거.
- **OmO 설정 탐색 매트릭스** — `{oh-my-openagent, oh-my-opencode} × {.jsonc, .json} × 4루트`.

## 파일 구조

- `audrey_v3.0/src/` — Python 3.9+ stdlib only, 16파일 ~1800줄
- `audrey_v3.0/DESIGN.md` — 인터페이스 계약 (모든 dataclass·함수 시그니처 고정)
- `audrey_v3.0/tests/scenarios.md` — 4환경 + 4회귀 시나리오
- `audrey_v3.0/docs/headless_opencode.md` — Scout 정적 분석 보고서
- `audrey_v3.0/scripts/audrey3.{sh,bat}` — 디렉터리명의 `.`로 `python -m audrey_v3.0` 불가 → src/ 래퍼

## 검증 이력

| 날짜 | 환경 | 결과 |
|---|---|---|
| 2026-04-13 VDI | 코부장 자체 스모크 | ENV1 `vdi` 판정, 블랙웰 Ollama 118ms alive, AGENTIS_READY=FALSE (VDI는 OpenCode 미설치 = 정답) |
| 2026-04-13 블랙웰 | 회장님 실행 | **AGENTIS_READY=TRUE**, F2 18.1s |

## 관련 노드

- [04. 시지푸스 마일스톤](04_sisyphus_milestones.md) — baseURL 함정 사건(R2)
- [07. 메모리 수렴선](07_memory_convergence_2026.md) — "regression before readiness" 원칙
- [11. Agent Evolution Protocol](11_agent_evolution_protocol.md) — 오드리 체크 항목이 프로토콜 체크리스트로 올라감

## Source

- `audrey_v3.0/README.md`, `DESIGN.md`, `docs/headless_opencode.md`, `tests/scenarios.md`
- `audrey/UPGRADE_PLAN_v3.md`
- memory `project_audrey_v23.md`
- `_archive/gist_comment_20260413_audrey_v31.md`
