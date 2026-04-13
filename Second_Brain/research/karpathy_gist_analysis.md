# Karpathy "LLM Wiki" Gist 분석

> 원문: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
> Raw: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f/raw
> 제목: **LLM Wiki — A pattern for building personal knowledge bases using LLMs**

## 1. 개요

이 gist는 Andrej Karpathy가 작성한 "아이디어 문서(idea file)"로, 자기 자신의 LLM 에이전트(Claude Code, OpenAI Codex, OpenCode 등)에 복사-붙여넣기해서 쓰라고 의도된 **패턴 문서**다. 특정 구현이 아니라 **고수준 아이디어**를 전달하는 것이 목적이며, 에이전트가 사용자와 협업해 세부 사항을 채우도록 설계되어 있다.

해결하려는 문제는 명확하다. 기존 RAG 방식("업로드 → 청크 검색 → 답변")은 **매 질문마다 LLM이 지식을 처음부터 재발견**한다는 한계를 가진다. 누적(accumulation)이 없고, 종합(synthesis)이 없으며, 교차 참조도 매번 새로 만들어진다. Karpathy는 이를 "the LLM is rediscovering knowledge from scratch on every question"이라 표현한다.

## 2. 핵심 아이디어

**인용 1 — 영속적이고 복리(compounding)적인 아티팩트로서의 Wiki:**
> "the LLM **incrementally builds and maintains a persistent wiki** — a structured, interlinked collection of markdown files that sits between you and the raw sources."

RAG가 "쿼리 타임 검색"이라면, LLM Wiki는 **"인제스트 타임 컴파일"**이다. 새 소스가 들어오면 LLM은 그것을 읽고 요약한 뒤, 기존 wiki의 엔티티/컨셉 페이지를 수정하고, 모순을 표시하고, 교차 참조를 갱신한다. 지식은 한 번 컴파일되고 **계속 최신 상태로 유지된다**.

**인용 2 — 분업:**
> "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."

사람은 소스 큐레이션·탐색·질문을 담당하고, LLM은 요약·교차 참조·파일링·유지보수 같은 "지루한(bookkeeping)" 작업을 전담한다. 사람은 wiki를 **거의 쓰지 않는다** — LLM이 쓴다.

**인용 3 — 왜 작동하는가:**
> "Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored... The wiki stays maintained because the cost of maintenance is near zero."

Vannevar Bush의 Memex(1945) 비전에서 미해결이었던 "누가 유지보수하는가"라는 문제를 LLM이 해결한다는 것이 Karpathy의 핵심 주장이다.

## 3. 제시된 구조/프롬프트/코드

**3-레이어 아키텍처:**
1. **Raw sources** — 불변(immutable) 원본 문서. LLM은 읽기만 한다.
2. **The wiki** — LLM이 소유하는 마크다운 파일 디렉터리. 요약, 엔티티, 컨셉, 비교, 오버뷰, 합성 페이지.
3. **The schema** — `CLAUDE.md` 또는 `AGENTS.md`. wiki 구조·컨벤션·워크플로를 정의하는 **설정 파일**. 사용자와 LLM이 공진화(co-evolve)시킨다.

**3가지 핵심 연산:**
- **Ingest**: 소스 1개 → 요약 페이지 작성 → index 업데이트 → 10~15개 엔티티/컨셉 페이지 갱신 → log 추가
- **Query**: wiki 검색 → 종합 답변(마크다운, 비교 표, Marp 슬라이드, matplotlib 차트). **좋은 답변은 다시 wiki에 파일링**되어 복리 효과를 낸다.
- **Lint**: 주기적 건강 검사 — 모순, 낡은 주장, 고아 페이지, 누락된 교차 참조, 데이터 공백 탐지.

**2개의 특수 파일:**
- `index.md` — **콘텐츠 지향** 카탈로그. 임베딩 기반 RAG 없이 100 sources / 수백 페이지 규모까지 잘 작동.
- `log.md` — **시간순** append-only 기록. 일관된 접두사(`## [2026-04-02] ingest | Title`) 사용 시 `grep "^## \[" log.md | tail -5` 같은 unix 파이프로 파싱 가능.

**옵션 도구:** [qmd](https://github.com/tobi/qmd)(BM25+벡터 하이브리드 + LLM 재랭킹, on-device, CLI+MCP), Obsidian Web Clipper, Marp, Dataview, git.

## 4. Karpathy의 관점 — 멘탈 모델

Karpathy의 프레임은 **"RAG vs. Self-Reference/Reflection"**이 아니라 **"런타임 검색 vs. 컴파일된 지식"**이다. 그의 관심은 에이전트의 "자기 회고(self-reflection)" 같은 인지적 메타포가 아니라, **지식을 물질적 아티팩트(markdown 파일 그래프)로 외재화(externalize)**하는 데에 있다.

- **메모리 ≠ 벡터 DB**. 메모리는 사람이 읽을 수 있는 마크다운 파일이어야 하고, 사람이 브라우징/검증할 수 있어야 한다.
- **자기 참조 = wiki 자체**. 에이전트의 "기억"은 wiki를 읽는 것이고, "학습"은 wiki를 편집하는 것이다. 별도의 숨겨진 state가 없다.
- **Reflection = Lint 패스**. 모순 탐지, 고아 페이지 정리, 갭 분석 — 이것이 곧 반성(reflection)이다.
- **schema 파일(CLAUDE.md/AGENTS.md)의 위상이 매우 높다**. 이것이 에이전트를 "generic chatbot"에서 "disciplined wiki maintainer"로 바꾸는 핵심이라고 명시.
- **Obsidian graph view**를 "wiki의 shape을 보는 최고의 방법"으로 꼽는 점에서, 그의 모델은 **그래프 구조적(graph-structural)**이지 임베딩 공간적이지 않다.

## 5. OFFCODE 이식 고려사항

Karpathy가 **암묵적으로 가정하는 것들**과, Gemma4 기반 폐쇄망 환경에서 깨지는 지점:

**깨지지 않는 가정 (OFFCODE에 그대로 이식 가능):**
- 마크다운 파일 + git 저장소 = 인프라 불필요. 폐쇄망에 최적.
- 임베딩/벡터 DB 불필요 (index.md로 ~100 sources까지 커버) → **로컬 LLM의 약한 리트리벌 능력을 보완**.
- 10~15개 파일을 한 pass에 편집하는 "툴 루프" 패턴 → OpenCode+OmO의 agent+tool 구조와 자연스럽게 부합.

**주의할 가정:**
1. **컨텍스트 윈도우**: Claude Code/Codex는 수십 파일을 한 번에 읽고 일관되게 편집할 수 있다. Gemma4 (특히 26B-A4B)는 한 번에 touch 가능한 파일 수가 적을 수 있음 → **ingest를 "소스 1개 × 편집 k개"가 아닌 "단계별 파이프라인(요약 → 링크 추출 → 페이지별 업데이트)"로 분해** 필요.
2. **교차 참조 품질**: 고품질 cross-linking은 강한 instruction following을 요구. Gemma4에는 schema(CLAUDE.md 대응물)를 더 **엄격하고 예시 중심**으로 써야 함.
3. **qmd 같은 외부 도구**: github.com 의존 → 폐쇄망에서는 wget만 가능한 블랙웰 환경 제약 고려. **대안: ripgrep+BM25 Python 스크립트로 자체 구현**(OmO 툴로).
4. **Obsidian GUI 가정**: OFFCODE는 VDI/CLI 중심 → graph view 대신 **텍스트 기반 그래프 덤프**(예: `lint` 시 인접 리스트 출력)로 대체.
5. **"You read it; the LLM writes it"**: 회장님이 Obsidian처럼 실시간 브라우징할 수 있는 뷰어가 폐쇄망에 필요. 정적 HTML 빌더(예: mkdocs) 로컬 빌드 고려.
6. **자동 업데이트/배포 경로 부재**: Karpathy는 개인용. OFFCODE는 팀 공유 예정 → **git 기반 동기화 + 머지 정책** 추가 필요.

**주류 프레임워크 대비 포지션 (후속 연구 연결):**
- **MemGPT/Letta**: OS 메타포, 페이지 in/out. Karpathy는 "OS 필요 없다, git + markdown이면 충분"이라는 입장.
- **A-MEM / Mem0 / MIRIX**: 구조화된 메모리 노트/그래프. 방향은 유사하나, Karpathy는 **사람이 직접 읽는 아티팩트**를 명시적으로 강조.
- **Claude Code auto-memory**: 세션 간 사실 축적. Karpathy 방식은 세션이 아닌 **주제/엔티티 단위**로 축적.

## 6. 요약 한 줄

> **"메모리는 벡터가 아니라 git으로 버전 관리되는 마크다운 wiki이고, LLM은 그 wiki의 maintainer다."**
