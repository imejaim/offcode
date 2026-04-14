# 07. 2025-2026 에이전트 메모리 수렴선

> Second Brain Researcher L2 서베이 기반. 2025 Q3 – 2026 Q2 연구/제품 흐름.

## 네 방향 수렴

2025-2026년 에이전트 메모리 연구는 대략 네 갈래로 수렴했다.

### 1. 표준화 — Letta (구 MemGPT)

- **2025-10 V1** 에이전트 루프 재설계와 함께 제품화
- 메모리 블록 3종: `core` / `recall` / `archival`
- 업계 디폴트 어휘로 자리잡음
- 약점: 외부 서버 운영 부담. Agentis 폐쇄망엔 자가호스팅+Ollama 조합 가능하지만 E4B는 핫패스 배제 필요

### 2. 자기조직화 — A-MEM (NeurIPS 2025)

- Zettelkasten 원리 적용 — 메모리가 쓰기마다 스스로 **링크·재색인·evolve**
- 특별한 DB 불필요, 로직이 알고리즘에 있음
- 장점: Karpathy Wiki 위에 얹어서 자동 양방향 링크/요약 갱신으로 쓸 수 있음

### 3. 미들웨어 — Mem0 v1.0

- Apache-2.0, $24M 투자, 41k⭐
- vector + graph + KV 하이브리드를 미들웨어로 패키징
- **LOCOMO 벤치마크에서 OpenAI Memory 대비 +26% 품질 / -91% 지연**
- 약점: graph DB 의존. 폐쇄망에서는 인프라 부담

### 4. SOTA — MIRIX 6-type

- 2025-07, 메모리를 6 종류로 분류: Core / Episodic / Semantic / Procedural / Resource / KnowledgeVault
- 멀티에이전트 구성
- **LOCOMO 85.4% SOTA**
- 약점: 풀스택 복잡도. 초기 도입 비용 큼

## 제품 현장 (상용)

제품 레벨에서는 다음 3층 구조로 수렴:

```
규칙 파일 (사용자가 쓰는)       ← Claude Code CLAUDE.md, Windsurf Rules, Cursor Rules
      +
자동 노트 (에이전트가 쓰는)     ← Claude Auto Memory, Windsurf Memories, Gemini Personal Context
      +
주기적 consolidation           ← Claude Auto Dream, Mem0 update()
```

- **Claude Code Auto Memory + Auto Dream** — 지금 이 세션에서 돌아가는 바로 그 시스템
- **Windsurf Memories + Rules** — 같은 계보
- **Gemini Personal Context** — 구조화 덜 됐지만 같은 개념

## 정리 문서

- **"Memory in the Age of AI Agents"** (arXiv 2512.13564, 2025-12) — forms / functions / dynamics 분류로 위 전부를 taxonomy화

## Karpathy Wiki의 위치

```
    스펙트럼  ← 미니멀                              풀스택 →

    Karpathy     Claude Code   Letta     A-MEM    Mem0    MIRIX
    LLM Wiki     4레이어
    (markdown)
```

- 극미니멀 끝 = Karpathy (markdown + schema만)
- 극풀스택 끝 = MIRIX (6 type + 멀티에이전트)
- **Claude Auto Dream의 consolidation 철학 + A-MEM의 evolution 철학**을 **DB 없이** 구현한 것이 Karpathy Wiki
- **Holonomic Brain은 이 지점을 골랐다** → Agentis 폐쇄망 제약 + 로컬 LLM 품질 현실에 최적

## Agentis 추천 3종 (L2 결론)

| 순위 | 기술 | 용도 |
|------|------|------|
| 1 | **Karpathy Wiki + Auto Dream 트리거** | 메인 엔진. Holonomic Brain 자체가 이 구현 |
| 2 | **Letta 자가호스팅 + Ollama 31B** | 장기 페르소나 봇 전용(E4B 핫패스 배제) |
| 3 | **A-MEM evolution 알고리즘** | Karpathy wiki 위에 오버레이해서 자동 링크 유지 |

**제외**: Mem0(graph DB 의존), MIRIX(풀스택 과부하), LangGraph memory(중복 레이어)

## 관련 노드

- [06. Karpathy Wiki 패턴](06_karpathy_wiki_pattern.md) — 원전 분석
- [08. 실제 적용 사례](08_production_cases.md) — L3 운영 실측
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md) — 어떤 선택을 했는가

## Source

- `Second_Brain/research/latest_methods_2026.md` (L2 서베이, 소스 URL 전문 포함)
