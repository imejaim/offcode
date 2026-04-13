# 오드리 v3.1 (Dr. Oh) — Agentium 헬스체크 에이전트

> 폴더명은 `audrey_v3.0`(최초 스캐폴딩 당시)이지만 현재 **v3.1**. 폴더 rename은 차기에.

## v3.1 변경사항 (2026-04-13, v3.0 대비 패치)

- **B3 `opencode.jsonc` 지원** — OpenCode upstream은 `opencode.jsonc > opencode.json > config.json` 순으로 공식 지원(`opencode-dev/packages/opencode/src/config/config.ts:1071`). v3.0은 `.json`만 봐서 `.jsonc` 사용자에게 false FAIL. v3.1은 3개 후보 모두 탐색.
- **OmO 설정 탐색 확장** — `oh-my-openagent.jsonc/json` + `oh-my-opencode.jsonc/json`. 여러 루트 디렉터리 × 이름 × 확장자 매트릭스.
- **B5 baseURL probe 정규화** — baseURL이 이미 `/v1`으로 끝나면 `/models`만 붙여서 이중 `/v1` 방지 (Ollama 404 버그 수정).
- **버전 문자열** — `3.0.0` → `3.1.0`, 진단서 헤더도 v3.1.
- `ctx.opencode_json_path` 사이드 채널로 실제 선택된 파일 경로 보존 (omo.py 호환 유지).


> **Agentis 플랫폼**의 실행 엔진인 **Agentium**(OpenCode + OmO + 로컬 LLM)의 건강 상태를
> 진단하는 에이전트. v2.31의 "설정 문법 검사기"에서 "환경 건강 진단기"로 재설계.

## v2.31 → v3.0 핵심 변화

| 항목 | v2.31 | v3.0 |
|------|-------|------|
| 프로바이더 | vLLM 하드코딩 | **중립**(Ollama/vLLM/TGI/…) |
| 판정 기준 | 설정 파싱 | **"시지푸스가 대답하면 READY"** E2E 우선 |
| 환경 자각 | 없음 | VDI/데스크탑/노트북/블랙웰 자체 판정 |
| 멀티 프로바이더 | 불가능 | 살아있는/죽은/실사용 프로바이더 동시 가시화 |
| baseURL 검증 | 없음 | **도달성 교차 확인**(localhost 함정 방지) |
| Config 스키마 | v2(`vllm_url` 단일) | v3(`providers[]` 배열) + v2 자동 마이그레이션 |

## 구조

```
audrey_v3.0/
├── README.md              ← 본 문서
├── DESIGN.md              ← 인터페이스 계약 (Python 타입으로 고정)
├── PLAN.md                ← Phase 0~6 울트라플랜 (audrey/UPGRADE_PLAN_v3.md 사본)
├── config.example.v3.json ← v3 스키마 예시
├── src/
│   ├── __init__.py
│   ├── __main__.py        ← CLI 진입점
│   ├── config.py          ← v2/v3 로더 + 마이그레이션
│   ├── provider.py        ← Provider 추상화 + 디스커버리
│   ├── http.py            ← stdlib HTTP 래퍼
│   ├── env.py             ← 환경 자각(VDI/데스크탑/...)
│   ├── result.py          ← CheckResult + 상태 상수
│   ├── judge.py           ← AGENTIS_READY 5축 판정
│   ├── report.py          ← ASCII 진단서 + JSON 출력
│   ├── autofix.py         ← localhost 치환 등 자동 수정
│   └── checks/
│       ├── __init__.py
│       ├── env.py         ← ENV1/ENV2
│       ├── infra.py       ← A1~A4 프로바이더 디스커버리
│       ├── opencode.py    ← B1~B5
│       ├── omo.py         ← C1~C7
│       ├── logs.py        ← D1~D3
│       ├── model.py       ← E1/E2
│       └── e2e.py         ← F1~F4 End-to-end
├── tests/
│   ├── fixtures/          ← 시뮬레이션용 가짜 응답·설정 파일
│   └── scenarios.md       ← 3환경 회귀 테스트 시나리오
├── docs/
│   └── headless_opencode.md  ← OpenCode 헤드리스 호출 조사 결과
└── scripts/
    └── install_opencode_local.sh  ← opencode-dev 기반 로컬 설치
```

## 실행

```bash
# 전체 체크
python -m audrey_v3.0 --config config.example.v3.json

# JSON 출력
python -m audrey_v3.0 --json

# 카테고리별
python -m audrey_v3.0 --category e2e

# v2 config 자동 마이그레이션 (읽기 전용)
python -m audrey_v3.0 --config ../audrey/config.json

# auto-fix
python -m audrey_v3.0 --auto-fix
```

## 수용 기준

1. 현재(2026-04-13) 사내 데스크탑(Ollama Gemma4 31B 시지푸스 동작)에서 **AGENTIS_READY=TRUE**
2. vLLM을 내려도 결과 유지
3. baseURL을 localhost로 바꾸면 B5 FAIL + auto-fix 제안
4. VDI에서는 ENV=vdi 자기 판정 + 관련 체크 SKIP
5. 블랙웰에서 localhost Ollama 동일 로직으로 PASS
6. v2.31 config.json으로 실행해도 회귀 없음
