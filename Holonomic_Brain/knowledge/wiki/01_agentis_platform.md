# 01. Agentis 플랫폼

## 정체

**Agentis** — 사내 로컬 LLM 기반 에이전트 플랫폼(브랜드). 2026-04-13 OFFCODE에서 리브랜딩. 줄임말 없음(구 "오프코드/옵코"는 Superseded).

## 4서브브랜드 구조

```
Agentis              ← 전체 플랫폼 (브랜드)
 ├── Agentium        ← 실행 엔진 (core runtime)
 ├── AgentMesh       ← 에이전트 네트워크
 ├── AgentHub        ← UI / dashboard
 └── AgentSDK        ← 개발용 툴킷
```

| 컴포넌트 | 역할 | 현재 구현 |
|---|---|---|
| **Agentium** | 프로바이더→LLM→도구→응답 런타임 | OpenCode + OmO(oh-my-openagent) + Ollama |
| **AgentMesh** | 에이전트 간 통신·위임·오케스트레이션 | OmO 서브에이전트(시지푸스→헤파이스토스→…) |
| **AgentHub** | UI / 대시보드 / 작업 큐 | 미구현 (장기) |
| **AgentSDK** | 에이전트·도구·스킬 빌더 툴킷 | OmO plugin SDK, PydanticAI |

## 3레이어 아키텍처 (논리)

- **Layer 1 빌더** (Agentium) — 에이전트 코드를 작성/테스트/디버깅. 도구·MCP·CLI·훅·서브에이전트 제공.
- **Layer 2 런타임** — 만들어진 에이전트가 실제 업무 수행. PydanticAI + Ollama + MCP 서버.
- **Layer 3 지식 인프라** — 벡터DB + 문맥 강화 인덱싱 + 멀티모달 문서 처리 (장기).

## 핵심 원칙

1. **로컬 우선** — 외부 API 의존 금지. 사내망 완결.
2. **단계적 배포** — zip/폴더 → 단일 바이너리 → 컨테이너 순으로 성숙.
3. **사용자 주도 진화** — 초기 환경과 첫 에이전트 제공 후 사용자가 커스터마이징.
4. **단순 RAG 금지** — 반드시 LLM 문맥 강화 + 하이브리드 검색 + 리랭킹.
5. **OFFCODE는 빌더, 실행은 별도 런타임** — 하네스로 만들되 돌아가는 건 PydanticAI/API 서버.

## 오드리(Dr. Oh) 포지셔닝

오드리는 **Agentium 헬스체크 에이전트**다. AgentHub(대시보드) 도입 전까지 CLI 기반 진단이 오드리 역할이며, v3.1부터 "시지푸스가 대답하면 READY"를 제1 진실로 삼는다.

## 이전 세대와의 차이

| 항목 | 구 OFFCODE v1 | Agentis v1 |
|---|---|---|
| LLM 서빙 | vLLM + Qwen3.5 | **Ollama + Gemma4 31B/26B/E4B** (vLLM 백업) |
| 헬스체크 | 오드리 v2.31 (vLLM 하드코딩) | **오드리 v3.1** (프로바이더 중립 + E2E 우선) |
| 기억 구조 | 개별 세션 MEMORY.md | **Holonomic Brain**(본 시스템) + 세션 메모리 |

## 관련 노드

- [02. 환경 토폴로지](02_environments.md) — Agentis가 배포되는 곳
- [03. Gemma4 Ollama 서빙](03_gemma4_ollama.md) — Agentium의 LLM 레이어
- [05. 오드리 v3.1](05_audrey_v31.md) — Agentium 헬스체크
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md) — Layer 3 지식 인프라의 현재 구현

## Source

- `docs/AGENTIS_ARCHITECTURE.md`
- `CLAUDE.md`
- memory `project_offcode.md` (Agentis 플랫폼 개요)
