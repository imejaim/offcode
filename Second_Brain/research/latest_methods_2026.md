# 최신 에이전트 메모리 / 자기참조 아키텍처 서베이 (2025 Q3 – 2026 Q2)

> 작성: Agentis Second Brain 서브프로젝트, Researcher L2
> 목적: 로컬 LLM(Gemma4 31B/26B/E4B, Ollama) + 폐쇄망 환경에 이식 가능한 최신 에이전트 메모리 패턴 정리
> 기준 시점: 2026-04

---

## 1. 서론 — 2025–2026 에이전트 메모리 연구의 큰 흐름

2023년 Reflexion / Generative Agents의 "reflection + episodic buffer" 시대가 지나간 뒤, 2025년부터 에이전트 메모리는 다음 네 축으로 재정의되었다.

1. **상태 보존(stateful) 런타임의 제품화** — MemGPT는 Letta로 합병(2024 말)되며 "메모리 블록(memory blocks)"이라는 추상화를 제품 표준으로 굳혔고, 2025-10 재아키텍처에서 Claude Code / ReAct의 교훈을 결합한 Letta V1 에이전트 루프를 공개했다([Letta blog](https://www.letta.com/blog/letta-v1-agent)).
2. **자기조직화 메모리(agentic memory)** — A-MEM(NeurIPS 2025)은 Zettelkasten 원리를 LLM에 이식하여 메모리가 스스로 링크·태그·재색인되는 "살아있는 네트워크"로 진화시켰다([arXiv 2502.12110](https://arxiv.org/abs/2502.12110)).
3. **서비스 레이어로서의 메모리** — Mem0(v1.0, 2025-10, Apache-2.0)는 vector + graph + KV 3종 저장소를 묶어 "LLM 앞단 미들웨어"로 포지셔닝. LOCOMO에서 OpenAI Memory 대비 +26% 정확도, -91% 지연, -90% 토큰을 기록([arXiv 2504.19413](https://arxiv.org/abs/2504.19413)).
4. **다중 메모리 타입의 재도입(인지과학 리바이벌)** — MIRIX(2025-07), LangMem(2025), 그리고 12월 서베이 "Memory in the Age of AI Agents"([arXiv 2512.13564](https://arxiv.org/abs/2512.13564))는 모두 **Core / Episodic / Semantic / Procedural / Resource / Knowledge Vault** 같은 인지 아키텍처(Soar, ACT-R 계보) 분류를 LLM 에이전트에 다시 적용한다.

제품 현장(Claude Code Auto Memory, Windsurf Cascade Memories, Gemini Personal Context, ChatGPT Memory)도 2025년을 기점으로 "사용자가 쓰는 규칙 파일" + "에이전트가 스스로 적는 노트" + "주기적 consolidation(dream)" 3층 구조로 수렴 중이다.

---

## 2. 주요 프레임워크/접근법

### 2.1 Letta (구 MemGPT)

- URL: https://github.com/letta-ai/letta, https://docs.letta.com
- 발표 시점: MemGPT 논문 2023-10 → Letta로 브랜딩 2024 → **Letta V1 에이전트 루프 2025-10**
- 핵심 아이디어: LLM이 **tool call로 자기 컨텍스트를 직접 편집**. 컨텍스트 윈도우를 OS 페이지처럼 취급.
- 메모리 구조(3-tier):
  - **Core Memory** (RAM, in-context): `human` 블록 + `persona` 블록, 에이전트가 read/write, 문자 상한 존재
  - **Recall Memory** (disk cache): 검색 가능한 대화 히스토리
  - **Archival Memory** (cold storage): 벡터 DB, tool call로 질의
- 분류: **Semantic + Episodic**(Archival), **Procedural**(Persona 블록의 행동 규칙)
- 자기참조 수준: **높음**. 에이전트가 자기 core memory를 편집하는 것이 기본 동작. V1부터는 Sonnet 4.5의 memory tool을 네이티브로 드라이브함.
- 강점: 개념이 단순, 로컬 Ollama 지원([docs](https://docs.letta.com/guides/server/providers/ollama/)), Docker 한 줄로 자가호스팅, Postgres + pgvector로 영속화
- 약점: Postgres 의존성, 작은 로컬 모델에서는 tool-call 신뢰도가 떨어져 블록 편집 실패가 잦음

### 2.2 A-MEM (Agentic Memory)

- URL: https://arxiv.org/abs/2502.12110 · https://github.com/agiresearch/A-mem
- 발표 시점: arXiv 2025-02, **NeurIPS 2025 accepted**
- 핵심 아이디어: Zettelkasten. 새 메모리가 들어오면 (1) 구조화된 노트 생성(컨텍스트/키워드/태그) → (2) 과거 메모리 탐색 후 의미 있는 링크 형성 → (3) 기존 메모리의 attribute 갱신(**memory evolution**).
- 메모리 구조: 단일 레이어, 그러나 각 노트가 semantic(태그)+episodic(원문 context)+relational(링크) 혼합
- 자기참조 수준: **매우 높음**. 추가 쓰기마다 과거 노트를 다시 읽고 갱신하는 self-referential update가 본질.
- 강점: 6개 foundation model에서 SOTA, 메모리가 시간이 갈수록 "조직화"되는 유일한 오픈 구현체
- 약점: 쓰기 한 번당 LLM 호출 여러 번 → 토큰/지연 비용 큼. 로컬 소형 모델에서 링크 품질 급락 가능.

### 2.3 Mem0

- URL: https://github.com/mem0ai/mem0 · https://arxiv.org/abs/2504.19413
- 발표 시점: 논문 2025-04, **v1.0.0 2025-10**, $24M 시리즈 A
- 핵심 아이디어: LLM과 앱 사이에 "메모리 레이어"를 꽂는 미들웨어. 대화에서 사실을 자동 추출 → 저장 → 필요 시 인출.
- 메모리 구조: **Vector store(semantic) + Graph DB(relational) + KV store(fast facts)** 3중 하이브리드
- 분류: 주로 **Semantic + Factual**, Episodic은 raw history를 별도 보관
- 자기참조 수준: **중간**. ADD/UPDATE/DELETE/NOOP 결정은 LLM이 내리지만 스키마 자체는 고정.
- 강점: Apache-2.0, Ollama 네이티브, LOCOMO에서 OpenAI Memory 대비 +26% / -91% 지연 / -90% 토큰, Netflix·Lemonade 채택 사례
- 약점: Graph DB(Neptune/Neo4j) 세팅 복잡도, 폐쇄망에서 graph backend 선택지가 제한적

### 2.4 MIRIX

- URL: https://github.com/Mirix-AI/MIRIX · https://arxiv.org/abs/2507.07957 · https://mirix.io
- 발표 시점: 2025-07
- 핵심 아이디어: "개인 비서"용으로 화면 스크린샷까지 먹고, **6종 메모리 타입**을 **다중 에이전트**가 분업 관리.
- 메모리 구조(6-type):
  - **Core** (persona + human)
  - **Episodic** (time-stamped events: event_type, summary, actors, timestamp)
  - **Semantic** (concepts, knowledge graph, entities)
  - **Procedural** (workflow JSON steps)
  - **Resource Memory** (원본 자료 참조)
  - **Knowledge Vault** (구조화 팩트 저장)
- 자기참조 수준: **높음**. 각 메모리 타입마다 담당 서브에이전트가 있고, 상위 오케스트레이터가 업데이트 조정.
- 강점: LOCOMO 85.4% SOTA, ScreenshotVQA에서 RAG 대비 +35% 정확도 + 저장 공간 **99.9% 감소**
- 약점: React-Electron + Uvicorn 풀스택, 설치 복잡. 6개 에이전트 풀이 로컬 소형 LLM에선 과부하.

### 2.5 Claude Code Auto Memory + Auto Dream (Anthropic)

- URL: https://code.claude.com/docs/en/memory · https://claudefa.st/blog/guide/mechanics/auto-dream
- 발표 시점: Auto Memory 2025-후반(v2.1.59+), Auto Dream 2026-03 단계 롤아웃
- 핵심 아이디어: **4-layer 메모리**
  1. `CLAUDE.md` (사용자 작성, 버전 관리)
  2. **Auto Memory** (`MEMORY.md`, 에이전트 자동 기록)
  3. Session Memory (대화 내부)
  4. **Auto Dream** (24h + 5회 대화 경과 시 서브에이전트가 백그라운드에서 노트 정리·통합·모순 해결)
- 분류: CLAUDE.md=**Procedural/Declarative**, MEMORY.md=**Episodic+Semantic**, Dream=**Consolidation loop**
- 자기참조 수준: **높음**. 특히 Dream이 "에이전트가 자기 과거 노트를 다시 읽고 재구성"하는 sleep-time consolidation에 가까움.
- 강점: 파일 기반(Git 친화적), 폐쇄망 이식성 최상(그냥 markdown), 사용자 인스펙션 완전 투명
- 약점: Anthropic 전용 런타임. 그러나 **아이디어 자체는 프레임워크-무관**하게 OpenCode/Gemma4 환경에도 그대로 복제 가능.

### 2.6 Windsurf Cascade Memories + Rules

- URL: https://docs.windsurf.com/windsurf/cascade/memories
- 발표 시점: 2025 전반
- 핵심 아이디어: **Memories**(자동, 로컬 전용) vs **Rules**(수동, `.windsurf/rules/` + `AGENTS.md`, 버전관리)
- 분류: Memories=Episodic, Rules=Procedural
- 자기참조: 중간. Cascade가 대화 중 자동 생성하지만 "팀 공유 + 영속"을 원하면 Rules로 승격 권장.
- 강점: 2-tier(ephemeral vs durable) 설계가 명확
- 약점: 글로벌 규칙 6,000자 / 워크스페이스 12,000자 상한. 폐쇄망 이식성은 AGENTS.md 패턴만 차용 가능.

### 2.7 LangGraph / LangMem

- URL: https://docs.langchain.com/oss/python/langgraph/memory · https://blog.langchain.com/langmem-sdk-launch/
- 발표 시점: LangMem SDK 2025
- 핵심 아이디어: LangGraph store(namespace 기반 영속 KV) + **LangMem SDK**가 semantic/episodic/procedural 3종 메모리 추출·관리 툴 제공. Postgres + pgvector 프로덕션 권장.
- 분류: 인지과학 3-tier(semantic=facts/preferences, episodic=few-shot examples, procedural=system prompts)
- 자기참조 수준: 중간. 에이전트가 `manage_memory` 툴로 직접 편집 가능하나 자동 consolidation 루프는 사용자 설계 몫.
- 강점: 오픈소스, 벡터 스토어 교체 자유, 폐쇄망에서 Postgres만 있으면 완전 자가호스팅
- 약점: "프레임워크"라 boilerplate 많음, 메모리 스키마를 직접 설계해야 함

### 2.8 CrewAI 통합 Memory (v0.28+)

- URL: https://docs.crewai.com/en/concepts/memory
- 발표 시점: 2025-12 (v0.28)
- 핵심 아이디어: 기존 short-term / long-term / entity / external 4종을 **단일 `Memory` 클래스**로 통합. LLM이 저장 시점에 scope·category·importance를 추론, recall 시 semantic+recency+importance 복합 스코어링.
- 분류: 자체 명칭(short/long/entity)이지만 내부적으로 episodic + semantic 혼합
- 자기참조 수준: 중간. "adaptive-depth recall"로 상황에 따라 얼마나 깊이 돌아볼지 자기 결정.
- 강점: API 단순화, 멀티에이전트 "Crew"가 공유 메모리 접근
- 약점: 여전히 클라우드 LLM 가정이 강함

### 2.9 Reflexion 계열 후속 (MAR, Agent-R)

- URL: https://arxiv.org/abs/2501.11425 (Agent-R), https://arxiv.org/html/2512.20845v1 (MAR)
- 발표 시점: Agent-R 2025-01, MAR 2025-12
- 핵심 아이디어:
  - **Agent-R**: MCTS로 "잘못된 trajectory → 교정된 trajectory" 쌍을 스스로 생성해 iterative self-training
  - **MAR**: 단일 Reflexion 에이전트의 confirmation bias 문제를 다중 페르소나 + judge 모델로 분해. HotPotQA +3pt, HumanEval 76.4→82.6
- 분류: **Episodic reflection buffer**, 그러나 MAR은 메모리 쓰기 전에 critique 단계가 명시적
- 자기참조 수준: **매우 높음** (본질상 self-reflection)
- 강점: 학습이 아닌 추론-시 기법, 소형 모델도 일부 이득
- 약점: 반성 루프 자체의 토큰 소모가 크고, 로컬 모델에선 judge 품질이 병목

### 2.10 Karpathy LLM Wiki (참조용)

- URL: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- 발표 시점: 2025 (gist)
- 핵심 아이디어: RAG를 버리고 **LLM이 유지하는 영속 wiki(markdown)** 를 도입. 원본 소스는 불변, wiki는 LLM이 계속 편집(cross-reference, 모순 flag, summary). 스키마가 wiki의 진화 규칙을 정의.
- 분류: **Semantic 위주, Procedural(schema)**. Episodic은 의도적으로 배제.
- 자기참조 수준: **높음**. "compounding artifact"라는 표현 자체가 자기참조 consolidation을 뜻함.
- 강점: 극단적 단순성(파일+규칙), 폐쇄망 이식성 최고, 인간이 inspect 가능
- 약점: benchmark 없음, consolidation 트리거/충돌 해결을 구현자가 설계해야 함

### 2.11 Memory in the Age of AI Agents (Survey, 2025-12)

- URL: https://arxiv.org/abs/2512.13564 · https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- 핵심: "forms-functions-dynamics" 3축 taxonomy
  - **Forms**: token-level / parametric / latent
  - **Functions**: factual / experiential / working
  - **Dynamics**: formation / evolution / retrieval
- Agentis 설계 시 **용어 통일용 레퍼런스**로 사용 권장.

### 2.12 인지 아키텍처 리바이벌 (Soar / ACT-R + LLM)

- URL: https://arxiv.org/html/2505.07087v2 (Cognitive Design Patterns for LLM Agents)
- 2025년에 Soar/ACT-R 커뮤니티가 LLM과 상호번역·상호운용 연구를 재개. "observe-decide-act" 공통 모델로 LLM 에이전트를 매핑.
- 현재 실용 구현체는 거의 없으나, MIRIX의 6-type 분류, LangMem의 3-type 분류가 모두 이 계보의 직접 후손.

---

## 3. 비교표

| 접근법 | 저장 방식 | 재인덱싱(link/evolve) | 회고(consolidation) 루프 | 로컬 구현 난이도 | 폐쇄망 호환성 |
|---|---|---|---|---|---|
| **Letta / MemGPT** | Postgres + pgvector, core blocks in-context | 수동(에이전트 tool call) | 없음(에이전트가 직접) | 중 (Docker 한 줄) | 상 (Ollama 공식 지원) |
| **A-MEM** | 벡터 DB + 노트 그래프 | **자동**(쓰기마다 링크+evolve) | 묵시적(evolve가 대체) | 중-상 | 중 (LLM 호출량 많음) |
| **Mem0** | Vector + Graph + KV 3종 | LLM 기반 ADD/UPDATE/DELETE | 없음 | 중 (Graph DB 셋업) | 중 (Neptune/Neo4j 필요) |
| **MIRIX** | 6-type 스키마 + 다중 DB | 서브에이전트별 자동 | 부분(타입별 update rule) | **상** (풀스택) | 중 (로컬 모델 과부하) |
| **Claude Auto Memory + Dream** | Markdown 파일(`MEMORY.md`) | Dream이 주기적 재작성 | **명시적**(24h/5회 트리거) | **하** (파일만) | **상** (Anthropic 런타임은 불가, 아이디어 복제는 즉시) |
| **LangGraph + LangMem** | Namespace store(Postgres) | manage_memory 툴 | 사용자 구현 | 중 | 상 |
| **Karpathy Wiki** | Markdown + schema.md | LLM이 매 편집마다 | 구현자 정의 | **하** | **상** |
| **Reflexion / MAR** | episodic text buffer | N/A | **매 시도마다** | 하-중 | 상 |

---

## 4. Karpathy 접근법의 위치

Karpathy의 wiki gist는 위 스펙트럼에서 **"극단적으로 단순한 쪽 끝"** 에 위치한다. 그 이유와 의미를 정리하면:

1. **형태(Form)**: Token-level, 그것도 **파일시스템 markdown**. Letta(DB 블록), A-MEM(벡터 노트), Mem0(3-hybrid), MIRIX(6-type DB) 스펙트럼에서 가장 "낮은 기술 스택".
2. **기능(Function)**: 거의 전적으로 **semantic + factual**. Karpathy는 episodic(대화 로그)은 의도적으로 버리고, "소스 → wiki → 응답"의 단방향 컴파일을 강조. 이 점에서 Mem0보다 Claude Code의 `CLAUDE.md` 철학에 가깝다.
3. **동역학(Dynamics)**: Formation/Evolution/Retrieval이 **모두 같은 wiki 편집 행위 하나**로 통합. A-MEM의 "memory evolution"과 철학이 일치하지만, A-MEM은 벡터 DB에서 자동 수행하는 반면 Karpathy는 사람이 읽을 수 있는 파일을 고수한다.
4. **자기참조 수준**: Claude Auto Dream과 매우 유사한 **sleep-time consolidation** 패턴. Dream이 "노트를 정리하는 서브에이전트"라면 Karpathy는 "에이전트가 자기 wiki를 계속 다듬는 것"이 본체.
5. **차별점**: Karpathy는 **schema.md**(wiki 진화 규칙) 개념을 전면에 내세우는데, 이는 Soar의 production rule / ACT-R의 procedural memory와 철학적으로 동형이다. 즉 "에이전트 행동 규칙을 메모리 안에 메타데이터로 박는" 인지아키텍처 계보의 2026년판 최소 구현.

**결론적 포지셔닝**: Karpathy gist = "Claude Auto Memory + A-MEM evolution + LangMem procedural rules"를 **DB 없이** 구현하는 극미니멀 레퍼런스. 벤치마크는 없지만 폐쇄망/로컬 LLM 환경에서의 **이식성은 최고**.

---

## 5. Agentis 추천 기술 3가지

제약: Gemma4 31B/26B/E4B(Ollama) + 폐쇄망 + Windows 사내망/VDI + Docker 및 Postgres는 가능하지만 외부 DB/그래프 서비스는 불가.

### 추천 1: **Karpathy Wiki 패턴 + Claude Code Auto Dream 트리거 규칙** (메인 엔진)

- **왜**: 폐쇄망 호환성 최고, Git으로 이력·감사 추적 무료, Gemma4 E4B(작은 모델) 수준에서도 "파일 편집"만 요구되므로 tool-call 실패율 낮음.
- **구체화**: `.offcode/memory/` 아래 `facts.md`, `procedures.md`, `episodes.md`, `schema.md`. 세션마다 오드리/오벤저스가 markdown을 직접 patch. 24시간 + N회 대화 경과 시 별도 subagent(예: "꿈꾸는 오드리")가 consolidation 패스 실행 — Claude Code Auto Dream의 트리거를 그대로 차용.
- **참조**: [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), [Claude Auto Dream](https://claudefa.st/blog/guide/mechanics/auto-dream), [Claude Code memory docs](https://code.claude.com/docs/en/memory).

### 추천 2: **Letta 자가호스팅 + Ollama 백엔드** (상태 보존 런타임이 필요한 에이전트용)

- **왜**: 에이전트가 자기 core/persona 블록을 편집하는 패턴이 필요한 특정 봇(예: 장기 페르소나를 가진 "뀨리")에만 선택적으로. Docker 한 줄 + Ollama 공식 지원이라 폐쇄망에서도 설치 리스크 낮음.
- **구체화**: Letta 서버 Docker 컨테이너 내부에서 Postgres+pgvector로 영속화, `OLLAMA_BASE_URL=http://host:11434/v1` 환경변수로 Gemma4 31B에 연결. **소형 모델로는 tool-call 신뢰도 확보를 위해 31B를 기본값으로 권장**, E4B는 핫패스에서 배제.
- **참조**: [Letta self-hosting](https://docs.letta.com/guides/selfhosting/), [Letta + Ollama](https://docs.letta.com/guides/server/providers/ollama/), [Letta V1 agent loop](https://www.letta.com/blog/letta-v1-agent).

### 추천 3: **A-MEM의 Zettelkasten evolution 알고리즘을 Karpathy wiki 위에 오버레이**

- **왜**: Karpathy wiki의 약점은 "노트 사이 링크가 자동으로 안 생긴다"는 점. A-MEM의 핵심 알고리즘(노트 생성 시 과거 노트 탐색 → 링크 → 관련 노트 attribute 갱신)을 **DB 없이 markdown 파일 수준에서 모사**하면 폐쇄망 제약을 유지하면서 자기조직화 품질을 얻는다.
- **구체화**: `facts.md` 신규 엔트리 작성 시 31B 모델이 (a) 관련 키워드 추출, (b) 기존 엔트리 semantic grep, (c) 양방향 `[[wikilink]]` 삽입, (d) 영향 받은 기존 엔트리의 summary 라인 수정. 이를 consolidation 패스에서 배치로 수행하면 추론 비용을 집중시킬 수 있다.
- **참조**: [A-MEM paper](https://arxiv.org/abs/2502.12110), [A-MEM GitHub](https://github.com/agiresearch/A-mem).

### 제외한 후보와 이유

- **Mem0**: 훌륭하지만 Graph DB 의존(Neo4j/Neptune) → 폐쇄망 운영 부담
- **MIRIX**: 6에이전트 풀 + Electron 스택 → Gemma4 E4B 레벨에서 운용 불가
- **LangGraph/LangMem**: 좋은 옵션이나 framework lock-in. OpenCode/OMO 위에 얹기에는 중복 레이어
- **CrewAI v0.28**: 멀티에이전트 orchestration 축이 다름, Agentis는 OMO가 그 역할
- **Reflexion/MAR**: 메모리 "저장소"라기보단 "추론 패턴". 메인 엔진 위에 optional layer로 얹는 건 가능

---

## 부록: 참고 서베이 용어 정리 (Memory in the Age of AI Agents, 2025-12)

추후 Agentis 내부 문서에서 용어를 통일할 때 이 taxonomy를 사용한다:

- **Forms**: token-level(인컨텍스트·파일) / parametric(파인튜닝) / latent(hidden state persistence)
- **Functions**: factual(사실) / experiential(에피소드) / working(단기)
- **Dynamics**: formation(생성) / evolution(갱신·통합) / retrieval(인출)

Agentis 추천 스택의 분류:
- 추천 1(Wiki+Dream) = token-level / factual+experiential / formation+evolution+retrieval 전부 커버
- 추천 2(Letta) = token-level / factual+experiential / retrieval 중심
- 추천 3(A-MEM overlay) = token-level / factual / evolution 강화

---

## 참고 URL 전체 목록

- Letta: https://github.com/letta-ai/letta · https://docs.letta.com · https://www.letta.com/blog/memory-blocks · https://www.letta.com/blog/letta-v1-agent · https://docs.letta.com/guides/server/providers/ollama/ · https://docs.letta.com/guides/selfhosting/
- A-MEM: https://arxiv.org/abs/2502.12110 · https://github.com/agiresearch/A-mem · https://neurips.cc/virtual/2025/poster/119020
- Mem0: https://github.com/mem0ai/mem0 · https://arxiv.org/abs/2504.19413 · https://mem0.ai/
- MIRIX: https://github.com/Mirix-AI/MIRIX · https://arxiv.org/abs/2507.07957 · https://mirix.io
- Claude Code memory: https://code.claude.com/docs/en/memory · https://claudefa.st/blog/guide/mechanics/auto-dream · https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Windsurf: https://docs.windsurf.com/windsurf/cascade/memories
- LangGraph/LangMem: https://docs.langchain.com/oss/python/langgraph/memory · https://blog.langchain.com/langmem-sdk-launch/
- CrewAI: https://docs.crewai.com/en/concepts/memory
- Reflexion 계열: https://arxiv.org/abs/2303.11366 · https://arxiv.org/abs/2501.11425 · https://arxiv.org/html/2512.20845v1
- Cognitive architectures: https://arxiv.org/html/2505.07087v2
- Survey: https://arxiv.org/abs/2512.13564 · https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- Karpathy: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
