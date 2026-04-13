# Second Brain Research L3 — 자기참조/영속 메모리 에이전트 실사례 조사

조사일: 2026-04-13
조사자: Researcher L3 (Agentis Second Brain)
대상: 2025–2026 실제 프로덕션/주요 OSS에서 돌아가는 메모리 에이전트
목적: 로컬 LLM(Gemma4) + 폐쇄망 + OpenCode/OmO 기반 환경에서 도입 가능성 평가

---

## 1. 상용 사례

### 1.1 Claude Code — Auto Memory + CLAUDE.md (지금 이 대화가 돌아가는 시스템)

- **메모리 구조 (4레이어)**:
  1. `CLAUDE.md` — 사용자가 수동 작성하는 지시서 (프로젝트/개인/조직 스코프)
  2. Auto Memory — Claude가 세션별로 자동 기록하는 노트 (user/feedback/project/reference 카테고리)
  3. Session Memory — 대화 연속성
  4. Auto Dream — 주기적 consolidation (24h + 5세션 축적 시 트리거)
- **인덱스 구조**: `MEMORY.md`가 엔트리포인트, 각 라인이 150자 이하 라벨 + 상세파일 포인터
- **배포 규모**: Claude Code 사용자 전원 (수십만 이상 추정)
- **실측 성능/관찰**:
  - 한 관찰 사례에서 Auto Dream이 913 세션을 9분 내에 consolidation
  - `CLAUDE.md`는 길이 상관없이 전체 로딩되지만, 짧은 게 adherence가 더 좋음
- **한계/알려진 이슈**:
  - **MEMORY.md 로딩 한계**: 처음 200 라인 또는 25KB 중 먼저 도달하는 것까지만 세션 시작 시 로딩. 그 이상은 무시됨
  - **시맨틱 서치 없음**: 포인터 모델이라 도메인을 알고 있을 땐 OK, 의미 기반 탐색 불가
  - **"왜(why)"를 저장하지 못함**: 사실은 저장하지만 그 맥락/이유는 빠짐
  - **멀티 에이전트 레이스 컨디션**: 같은 프로젝트에 Claude Code 여러 인스턴스 돌리면 메모리 파일 쓰기 충돌
  - Auto Memory는 "학습"이 아니라 "메모"일 뿐이라는 비판 존재
- **출처**:
  - https://code.claude.com/docs/en/memory
  - https://milvus.io/blog/claude-code-memory-memsearch.md
  - https://claudefa.st/blog/guide/mechanics/auto-memory
  - https://claudefa.st/blog/guide/mechanics/auto-dream
  - https://www.mindstudio.ai/blog/claude-code-source-leak-memory-architecture
  - https://medium.com/@brentwpeterson/automatic-memory-is-not-learning-4191f548df4c
  - https://giuseppegurgone.com/claude-memory

### 1.2 Letta (구 MemGPT)

- **메모리 구조**: LLM-as-OS 패러다임. Core memory (항상 컨텍스트) + Archival memory (벡터 저장) + Recall memory (대화 검색). 에이전트가 직접 메모리 편집
- **배포**: Docker로 서버 배포 → 수천 유저 스케일 지원. Letta Code (git-backed memory + skills + subagents) 최근 런칭
- **2025 업데이트**: GPT-5, Claude 4.5 Sonnet용 Letta V1 아키텍처로 재설계. $10M 시드펀딩 공개
- **한계**: 구 MemGPT 아키텍처는 최신 reasoning 모델에서 비효율적이라 자체적으로 재설계. 구조가 복잡해 learning curve 높음
- **출처**:
  - https://www.letta.com/blog/memgpt-and-letta
  - https://www.letta.com/blog/letta-v1-agent
  - https://www.letta.com/blog/introducing-the-letta-code-app
  - https://docs.letta.com/concepts/memgpt/

### 1.3 Cursor — Memories + Rules

- **메모리 구조**: `.cursor/rules/*.mdc` (수동 규칙) + Memories (자동 기록, Rules → Generate Memories 토글)
- **배포 규모**: Cursor 유저 전체 (100만+)
- **실측**: 유저들은 MCPs + Rules + Memories + Auto-run을 프로젝트 시작 시 함께 세팅하는 게 표준 패턴. 1.0에서 안정화
- **한계**: 자동 생성 메모리의 품질 편차, 메모리가 어디 저장됐는지 투명하지 않다는 불만
- **출처**:
  - https://forum.cursor.com/t/about-cursors-memory-record-feature/107355
  - https://cursor.com/changelog/2-0
  - https://medium.com/@hilalkara.dev/cursor-ai-complete-guide-2025-real-experiences-pro-tips-mcps-rules-context-engineering-6de1a776a8af

### 1.4 ChatGPT Memory

- **메모리 구조**: 유저별 글로벌 메모리 풀 (high-level preferences)
- **배포 규모**: ChatGPT 유저 전체 (수억)
- **실측 실패 사례**:
  - **2025-02-05 메모리 크래시**: 백엔드 업데이트 후 사일런트로 장기메모리 붕괴. 수년치 context 소실. 공지/롤백/메모리 뷰어/로그 다운로드 전부 없음
  - **토큰 한계로 인한 망각**: 긴 대화에서 이전 디테일 망각. 코딩 세션에서 20메시지 전에 고친 버그 재발
  - 한 MIT 연구에서 메모리 실패율 83% 리포트 (진위는 추가 확인 필요)
- **한계**: 정확한 템플릿/대용량 verbatim 텍스트 저장에 부적합 (OpenAI 공식 안내)
- **출처**:
  - https://www.webpronews.com/chatgpts-fading-recall-inside-the-2025-memory-wipe-crisis/
  - https://community.openai.com/t/critical-chatgpt-data-loss-engineering-fix-urgently-needed/1360675
  - https://community.openai.com/t/bug-gpt-4o-memory-regression-context-loss-across-chats-and-inside-threads/1310926
  - https://help.openai.com/en/articles/8590148-memory-faq
  - https://openai.com/index/memory-and-new-controls-for-chatgpt/

### 1.5 Devin (Cognition Labs)

- **메모리 구조**: **장기 메모리 없음**. 세션 내 context window 안에서만 추론. "amnesiac contractor"
- **배포**: 2026-03 기준 수천 개 회사에서 수십만 PR 머지. PR merge rate 34% → 67%로 YoY 상승
- **Claude Sonnet 4.5 재빌드 시 발견**: 모델이 컨텍스트 윈도우에 대해 "불안(anxious)"을 느끼고, 파일 시스템을 메모리로 사용하기 시작함. 요약/노트를 자발적으로 씀. 그러나 **모델 자체 요약만으로는 프로덕션 부족 → 성능 저하와 지식 공백**
- **교훈**: 모델이 자가 요약하게 두는 것은 불충분. 외부 메모리 스캐폴드가 필수
- **출처**:
  - https://www.sitepoint.com/devin-ai-engineers-production-realities/
  - https://inkeep.com/blog/context-anxiety
  - https://cognition.ai/blog/introducing-devin

### 1.6 Replit Agent

- **메모리 구조 (멀티티어)**: 프롬프트 내 short-term + DB 내 medium-term summaries + 벡터스토어 내 long-term + 그래프 구조
- **실측**: 한 세션이 수십 스텝, 수 시간 지속. LLM으로 메모리 압축/truncate하여 관리. 체크포인팅으로 롤백 지원
- **한계**: 수동 파일 편집이 들어가면 agent 메모리와 실제 코드가 out-of-sync. fresh chat 필요
- **출처**:
  - https://www.langchain.com/breakoutagents/replit
  - https://docs.replit.com/replitai/agent
  - https://www.zenml.io/llmops-database/building-a-production-ready-multi-agent-coding-assistant

### 1.7 LangChain Agent Builder (LangMem)

- **핵심 운영 교훈 (LangChain 공식 블로그)**:
  - **"프롬프팅이 가장 어려운 부분"**. 한 팀은 메모리 프롬프팅만 full-time으로 한 사람이 담당
  - **Consolidation 실패 사례**: 이메일 어시스턴트가 "cold outreach 벤더 리스트"를 무한 추가. "모든 cold outreach 무시"로 compact하지 못함 → 메모리가 계속 부풀음
  - **수동 개입 필요**: 에이전트가 세션 끝에 reflect/compact 하도록 유저가 명시적으로 프롬프트
  - **스키마 검증**: 에이전트가 메모리 파일 스키마를 잊고 invalid 파일 생성 → validation step을 강제하고 실패 시 LLM에 에러 반환
  - **Human-in-the-loop**: 메모리 업데이트마다 사람 승인
- **출처**:
  - https://blog.langchain.com/how-we-built-agent-builders-memory-system/
  - https://blog.langchain.com/memory-for-agents/
  - https://blog.langchain.com/langmem-sdk-launch/

### 1.8 CrewAI / AutoGen 프로덕션 메모리

- **CrewAI**: short-term / long-term / entity / contextual 4종 빌트인 메모리. 82% task success, 1.8s latency. 단, **장기 크루는 컨텍스트 누적으로 성능 저하 → 수동 cleanup 필수**
- **AutoGen**: 대화 히스토리 + 외부 벡터스토어. 3.1s latency. 한 클라이언트는 **24/7 모니터링 시스템에서 100 교환 후 메시지 프루닝으로 600MB 메모리 유지**
- **비용**: 프레임워크 자체는 무료지만 토큰비용이 엔지니어당 월 $200~$2,000+
- **출처**:
  - https://www.secondtalent.com/resources/crewai-vs-autogen-usage-performance-features-and-popularity-in/
  - https://docs.crewai.com/en/concepts/memory
  - https://latenode.com/blog/platform-comparisons-alternatives/automation-platform-comparisons/langgraph-vs-autogen-vs-crewai-complete-ai-agent-framework-comparison-architecture-analysis-2025

---

## 2. 오픈소스 사례 (GitHub 1k+ stars)

### 2.1 Mem0 — mem0ai/mem0

- **스타**: **41,000+** (2025-10 기준), Python 패키지 다운로드 1,300만+
- **메모리 구조**: user/session/agent 멀티레벨, selective memory 파이프라인
- **벤치마크**: OpenAI Memory 대비 LOCOMO +26%, 응답 91% 빠름, 토큰 90% 절감
- **상업**: $24M 투자 (YC, Peak XV, Basis Set). **2025-05 AWS Agent SDK의 exclusive memory provider로 채택**
- **동향**: 활발한 PR/이슈. v1.0 릴리즈로 API/vector store/GCP 통합 개선
- **출처**:
  - https://github.com/mem0ai/mem0
  - https://arxiv.org/abs/2504.19413
  - https://techcrunch.com/2025/10/28/mem0-raises-24m-from-yc-peak-xv-and-basis-set-to-build-the-memory-layer-for-ai-apps/

### 2.2 Graphiti — getzep/graphiti

- **스타**: **20,000+** (2025-11 기준). 이전 14k → 20k로 급증
- **메모리 구조**: 시간 인식(temporal) 지식 그래프. 시맨틱 임베딩 + BM25 키워드 + 그래프 traversal 하이브리드. **LLM 요약에 의존 안 함**
- **동향**: Graphiti MCP Server 1.0 릴리즈. FalkorDB 지원 추가
- **벤치마크**: Deep Memory Retrieval(DMR)에서 MemGPT 상회
- **출처**:
  - https://github.com/getzep/graphiti
  - https://blog.getzep.com/graphiti-hits-20k-stars-mcp-server-1-0/
  - https://arxiv.org/abs/2501.13956

### 2.3 Letta (구 MemGPT) — letta-ai/letta

- **스타**: 수만 대 (MemGPT 시절부터 축적)
- **동향**: V1 아키텍처 재설계로 활발

### 2.4 LangMem — langchain-ai/langmem

- **포지션**: LangChain 생태계의 메모리 SDK. Agent Builder의 프로덕션 운영 경험이 그대로 반영
- **출처**: https://github.com/langchain-ai/langmem

---

## 3. 벤치마크 결과 (2025–2026)

### 3.1 LoCoMo (Long Conversations Memory)

- **구성**: 10개 장기 대화, 평균 27.2 세션 / 588 턴 / 198 질문. 4종 질문(Single-hop, Multi-hop, Temporal, Open-domain)
- **최근 상위**:
  - **MemMachine v0.2**: LoCoMo 0.9169 (gpt-4.1-mini). Mem0/Zep/Memobase/LangMem/OpenAI baseline 모두 상회
  - **Mem0**: OpenAI Memory 대비 +26%
- **출처**:
  - https://snap-research.github.io/locomo/
  - https://arxiv.org/pdf/2410.10813
  - https://memmachine.ai/blog/2025/12/memmachine-v0.2-delivers-top-scores-and-efficiency-on-locomo-benchmark/

### 3.2 LongMemEval

- **구성**: 500개 질문, 세션당 평균 50.2 세션/115K 토큰. 5가지 능력 평가 (정보 추출, 멀티세션 추론, 시간 추론, 지식 업데이트, abstention)
- **최근 상위**:
  - **OMEGA**: 95.4% (466/500) — 현재 최고
  - **LiCoMemory** (Huang et al., 2025-11): 73.8% accuracy / 76.6% recall (GPT-4o-mini backbone) — 그래프/fact-extraction 베이스라인 전부 상회
- **출처**:
  - https://openreview.net/forum?id=pZiyCaVuti
  - https://omegamax.co/benchmarks
  - https://www.emergentmind.com/topics/locomo-and-longmemeval-_s-benchmarks

### 3.3 MEMTRACK (2025-10)

- 장기 메모리 + 상태 추적 평가. 상세는 https://arxiv.org/pdf/2510.01353

---

## 4. 실패/한계 실측

### 4.1 토큰 비용 폭발

- **POC → 프로덕션 비용 점프**: POC 테스트 시 $50 토큰이 프로덕션에서 **$2.5M/월**로 비화된 사례
- **실제 배포 케이스**: 월 API 청구 **$500 → $847K**로 스케일업 중 폭등
- **3,000명 × 10회/일**: 일 3만 대화 → 일 $4.2K / 월 $126K
- **full-context의 벽**: 100K+ 토큰 윈도우를 매 요청에 풀로 전송하면 p95 latency **17초**, 토큰 비용 14배
- **메모리 레이어 효과**: Mem0 파이프라인 기준 토큰 ~90% 절감, p95 latency ~91% 절감
- **출처**:
  - https://medium.com/@klaushofenbitzer/token-cost-trap-why-your-ai-agents-roi-breaks-at-scale-and-how-to-fix-it-4e4a9f6f5b9a
  - https://thenewstack.io/memory-for-ai-agents-a-new-paradigm-of-context-engineering/
  - https://mem0.ai/blog/state-of-ai-agent-memory-2026

### 4.2 Consolidation 실패 (LangChain 사례)

- 이메일 에이전트가 "cold outreach 무시할 벤더"를 끝없이 리스트업. **일반화 패턴(모든 cold outreach 무시)**으로 compact하지 못함 → 메모리 무한 증식
- 교훈: 에이전트가 스스로 "추상화 레벨 올리기"를 잘 못함. 주기적 사람 개입 필수

### 4.3 ChatGPT 2025-02 메모리 붕괴

- 백엔드 업데이트가 **사일런트로** 장기메모리 파괴. 유저 공지 0, 복구 0. 창작/개발 워크플로우 붕괴 보고 다수
- 교훈: 벤더 락인된 메모리는 고위험. **로컬 파일 기반 메모리가 회복력 관점에서 우월**

### 4.4 Devin 컨텍스트 불안(Context Anxiety)

- Claude Sonnet 4.5 기반 Devin이 "컨텍스트 윈도우 고갈 인식" → 숏컷. 이 현상을 관리하려고 자발적 노트 작성 시작. 그러나 모델 자체 요약은 프로덕션 불충분
- 교훈: 모델에게 self-summarize를 맡기면 gap 발생. **외부 스캐폴드(스키마/검증)가 필수**

### 4.5 CrewAI 장기 크루 성능 저하

- 장기 실행 크루는 컨텍스트 축적으로 느려짐. 수동 cleanup 전략 구현 필요
- AutoGen 24/7 프로덕션에서는 100 교환 후 프루닝으로 600MB 유지

---

## 5. Agentis 적용성 평가

전제: 로컬 LLM(Gemma4 31B 분석 + 26B-A4B 시지푸스), 폐쇄망, OpenCode + OmO 플러그인, GPU 96GB × 2 블랙웰 서버

| 사례 | 적용 가능성 | 이유 |
|------|:-:|------|
| **Claude Code 4레이어 (MEMORY.md + Auto Memory + Auto Dream)** | **바로 도입 가능 (개념)** | 구조 자체는 파일 시스템 + 프롬프트 규약. 시맨틱 서치 없이도 동작. **Agentis에 가장 적합한 레퍼런스**. 단 실제 Claude Code 구현은 독점이므로 **설계 모방 + OmO 훅으로 재구현** 필요 |
| **Mem0** | **개조 필요** | Python 패키지, 벡터스토어(Qdrant/Chroma 등 로컬 가능) 사용 가능. 다만 **LLM 호출이 내부에서 일어나는 부분을 Gemma4로 교체** 필요. OpenAI API hard-code 제거 필수. 라이선스 Apache 2.0 (OK) |
| **Graphiti / Zep** | **개조 필요** | Neo4j 또는 FalkorDB 필요 (로컬 배포 가능). LLM 요약 의존 낮음 → 작은 모델에 우호적. **시간 인식 그래프는 코드 히스토리와 잘 맞음**. MCP 서버 있어 OpenCode/OmO 연동 쉬움. 폐쇄망 그래프DB 구축 비용이 관건 |
| **Letta (MemGPT V1)** | **개조 필요, 난이도 高** | Docker 배포 가능, 로컬 LLM 지원. 그러나 Letta는 최신 reasoning 모델(Claude 4.5/GPT-5) 기준으로 재설계 중이라 **Gemma4 26B 수준에서 동일 품질 재현이 리스크**. 시도해볼 만하지만 1차 선택은 아님 |
| **LangMem (LangChain)** | **개조 필요** | LangChain 스택 도입 필요 → OpenCode/OmO 기조와 충돌. 다만 **운영 교훈(프롬프팅 full-time, consolidation 실패, 스키마 검증, human-in-the-loop)은 그대로 차용**해야 함 |
| **CrewAI/AutoGen 메모리** | **불가(직접 도입)** / 교훈만 | 별도 프레임워크. Agentis는 OpenCode+OmO 기반이므로 도입 시 스택 중복. 단 "100 교환 프루닝", "장기 크루 cleanup" 패턴은 OmO 훅으로 이식 가능 |
| **Cursor Rules + Memories** | **바로 도입 가능 (개념)** | `.cursor/rules/*.mdc` 패턴은 OpenCode의 `AGENTS.md`/`CLAUDE.md`와 동일 철학. 그대로 쓸 수 있음 |
| **Replit 멀티티어 (prompt+DB+vector+graph)** | **바로 도입 가능 (개념)** | 아키텍처 패턴 자체를 OmO에 적용 가능. 단 각 계층 구현은 로컬 대체품 필요 (Postgres + Chroma/Qdrant + FalkorDB) |
| **Devin "장기메모리 없음"** | **반면교사** | 장기메모리 없이 가면 onboarding 비용 영구화. Agentis는 반드시 장기메모리를 가져야 한다는 근거 |
| **ChatGPT 메모리 붕괴 사례** | **반면교사** | 벤더 락인 금지. **로컬 파일 기반 + git-backed 메모리**가 회복력의 답 (Letta Code의 git-backed 설계와 일치) |
| **LoCoMo/LongMemEval 벤치마크** | **평가 프레임으로 도입** | Agentis Second Brain 구축 후 자체 평가에 LoCoMo 또는 LongMemEval의 축소판을 한국어로 번역/적응하여 회귀 테스트에 쓰는 게 유효 |

### 최종 권고 (스택 후보)

1. **1차 추천**: **Claude Code 4레이어 설계를 OmO로 재구현** (파일 기반, MEMORY.md 인덱스, Auto Dream consolidation 훅). 이유: 폐쇄망/로컬LLM에서 가장 단순하고 벤더 락인 없음. 시맨틱 서치 부재 문제는 2차로 Mem0 또는 Graphiti를 **검색 레이어**로만 얹어 해결
2. **2차 추천**: **Graphiti (FalkorDB 로컬)**를 "코드 히스토리 + 의사결정 그래프" 전용으로 활용. LLM 요약 의존이 낮아 Gemma4 26B로도 안정적
3. **반드시 적용할 운영 규율 (LangChain 교훈 기반)**:
   - 메모리 스키마 validation 강제 + 실패 시 LLM에 에러 반환
   - 세션 종료 시 reflect/compact 프롬프트 강제
   - 중요한 메모리 업데이트는 human-in-the-loop (회장님 승인)
   - Consolidation 실패 감시: 메모리 파일 크기/항목 수 모니터링
4. **회피할 것**: 모델 자가 요약 단독 의존(Devin 교훈), full-context 전송(비용 폭탄), 벤더 락인 메모리(ChatGPT 2025-02 교훈)

---

## 출처 전체 목록

### 상용 사례
- https://code.claude.com/docs/en/memory
- https://milvus.io/blog/claude-code-memory-memsearch.md
- https://claudefa.st/blog/guide/mechanics/auto-memory
- https://claudefa.st/blog/guide/mechanics/auto-dream
- https://www.mindstudio.ai/blog/claude-code-source-leak-memory-architecture
- https://www.mindstudio.ai/blog/what-is-claude-code-auto-memory
- https://medium.com/@brentwpeterson/automatic-memory-is-not-learning-4191f548df4c
- https://giuseppegurgone.com/claude-memory
- https://www.letta.com/blog/memgpt-and-letta
- https://www.letta.com/blog/letta-v1-agent
- https://www.letta.com/blog/introducing-the-letta-code-app
- https://docs.letta.com/concepts/memgpt/
- https://forum.cursor.com/t/about-cursors-memory-record-feature/107355
- https://cursor.com/changelog/2-0
- https://medium.com/@hilalkara.dev/cursor-ai-complete-guide-2025-real-experiences-pro-tips-mcps-rules-context-engineering-6de1a776a8af
- https://www.webpronews.com/chatgpts-fading-recall-inside-the-2025-memory-wipe-crisis/
- https://community.openai.com/t/critical-chatgpt-data-loss-engineering-fix-urgently-needed/1360675
- https://community.openai.com/t/bug-gpt-4o-memory-regression-context-loss-across-chats-and-inside-threads/1310926
- https://help.openai.com/en/articles/8590148-memory-faq
- https://openai.com/index/memory-and-new-controls-for-chatgpt/
- https://www.sitepoint.com/devin-ai-engineers-production-realities/
- https://inkeep.com/blog/context-anxiety
- https://cognition.ai/blog/introducing-devin
- https://www.langchain.com/breakoutagents/replit
- https://docs.replit.com/replitai/agent
- https://www.zenml.io/llmops-database/building-a-production-ready-multi-agent-coding-assistant
- https://blog.langchain.com/how-we-built-agent-builders-memory-system/
- https://blog.langchain.com/memory-for-agents/
- https://blog.langchain.com/langmem-sdk-launch/
- https://www.secondtalent.com/resources/crewai-vs-autogen-usage-performance-features-and-popularity-in/
- https://docs.crewai.com/en/concepts/memory

### 오픈소스
- https://github.com/mem0ai/mem0
- https://arxiv.org/abs/2504.19413
- https://techcrunch.com/2025/10/28/mem0-raises-24m-from-yc-peak-xv-and-basis-set-to-build-the-memory-layer-for-ai-apps/
- https://github.com/getzep/graphiti
- https://blog.getzep.com/graphiti-hits-20k-stars-mcp-server-1-0/
- https://arxiv.org/abs/2501.13956
- https://github.com/langchain-ai/langmem

### 벤치마크
- https://snap-research.github.io/locomo/
- https://arxiv.org/pdf/2410.10813
- https://openreview.net/forum?id=pZiyCaVuti
- https://omegamax.co/benchmarks
- https://www.emergentmind.com/topics/locomo-and-longmemeval-_s-benchmarks
- https://memmachine.ai/blog/2025/12/memmachine-v0.2-delivers-top-scores-and-efficiency-on-locomo-benchmark/
- https://arxiv.org/pdf/2510.01353

### 비용/실패
- https://medium.com/@klaushofenbitzer/token-cost-trap-why-your-ai-agents-roi-breaks-at-scale-and-how-to-fix-it-4e4a9f6f5b9a
- https://thenewstack.io/memory-for-ai-agents-a-new-paradigm-of-context-engineering/
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://blogs.oracle.com/developers/agent-memory-why-your-ai-has-amnesia-and-how-to-fix-it
