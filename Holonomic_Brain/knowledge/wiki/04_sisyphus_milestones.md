# 04. 시지푸스 마일스톤

Agentis Layer 1 빌더의 첫 번째 시험대 = 시지푸스 에이전트가 각 환경에서 응답하는가.

## 마일스톤 타임라인

| 날짜 | 환경 | 결과 | 검증 방법 |
|---|---|---|---|
| 2026-04-08 | 초기 셋업 디버깅 | 플러그인 로드 3중 문제 발견 | 오타 + 프록시 + file:// 경로 |
| 2026-04-10 16:33 | **블랙웰 서버 (localhost)** | ✅ Gemma4 31B 첫 응답 | `opencode` TUI에서 "하이, 넌 누구니?" → 34.2s 응답 |
| 2026-04-13 04:20 | **사내 데스크탑 (원격)** | ✅ Gemma4 31B 원격 응답 | baseURL `localhost`→`10.88.22.29` 1줄 치환 후 |
| 2026-04-13 07:44 | **블랙웰 (오드리 v3.1 F2)** | ✅ cli_run 18.1s | `opencode run --format json` NDJSON |
| — | 사내 노트북 | ⏳ 미검증 | 자체 Gemma4 + 블랙웰 없이 독립 |
| — | VDI | 해당 없음 (GPU 없음) | — |

## 공통 장애 패턴 (누적 기록)

### 시지푸스가 에이전트 목록에 안 뜸
**원인**: OmO의 `meetsSisyphusAnyModelRequirement` 체크가 폴백 체인(claude-opus-4-6→kimi→gpt-5.4→glm-5)에 로컬 모델이 없으면 `return undefined` → 에이전트 생성 자체가 안 됨.
**해결**: `oh-my-openagent.jsonc`에서 `agents.sisyphus.model`을 로컬 모델로 오버라이드.
**코드**: `oh-my-openagent-dev/src/agents/builtin-agents/sisyphus-agent.ts:52`, `src/shared/model-requirements.ts:21-46`.

### 플러그인이 로드 안 됨
**원인**: npm 레지스트리 로딩 버그 (`oh-my-opencode@3.15.3`).
**해결**: `file://` 로컬 경로로 참조. 예: `file:///home/dongho.yoon/.nvm/.../oh-my-opencode/dist/index.js` (Linux), `file://C:/Users/dongho.yoon/.config/opencode/node_modules/oh-my-openagent` (Windows).

### "Cannot connect to API: socket connection was closed unexpectedly"
**원인**: `opencode.json`의 `baseURL`이 `http://localhost:11434/v1`인데 클라이언트 호스트에 로컬 Ollama가 없음.
**해결**: 블랙웰 서버 IP로 치환 — `http://10.88.22.29:11434/v1`.
**재발 방지**: 오드리 v3.1 B5 체크(baseURL 도달성 교차 확인)가 이 함정을 탐지한다.

## 수정 라운드 표준 절차 (gist 소통 채널 기반)

1. 진단 4단계 댓글(curl / opencode.json / plugin 경로 + jsonc / version + 시지푸스 표시)로 현재 상태 요약
2. 원인 가설 → 1줄 치환 명령 제안
3. 재실행 → 응답 스크린샷/문자로 확인
4. 성공 시 wiki(`04`, `05`)에 기록 + 메모리 업데이트

## 관련 노드

- [02. 환경 토폴로지](02_environments.md) — 환경별 증상
- [03. Gemma4 Ollama 서빙](03_gemma4_ollama.md) — 무엇이 응답하는가
- [05. 오드리 v3.1](05_audrey_v31.md) — 회귀 시나리오 R2(localhost 함정)

## Source

- memory `project_sisyphus_fix.md`
- `_archive/gist_comments_20260410.txt`
- `_archive/gist_comment_20260413_win_sisyphus_diag.md`, `_fix1.md`
