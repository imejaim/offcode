# Second Brain — 울트라플랜

> 자기참조·장기기억·지식축적 에이전트 연구 → OFFCODE 이식.
> 2026-04-13 작성.

---

## Phase 0 — 원천 분석 (병렬 리서치)

3개 레인을 병렬 서브에이전트로 dispatch. 각 레인은 독립 파일에 산출물 저장.

| 레인 | 담당 | 산출 파일 | 초점 |
|------|------|-----------|------|
| **L1** | Karpathy gist 원문 분석 | `research/karpathy_gist_analysis.md` | 전체 개요, 핵심 개념, 제시 구조, OFFCODE 이식 시 고려점 |
| **L2** | 2025–2026 최신 방법론 | `research/latest_methods_2026.md` | MemGPT/Letta, A-MEM, Mem0, MIRIX, Claude Code auto memory 등 프레임워크별 비교 |
| **L3** | 실제 적용 사례 | `research/application_cases.md` | 상용/오픈소스 배포 사례, 성능·비용·한계, 로컬 LLM 적용성 |

**완료 조건**: 각 파일이 존재하고, 각 레인 요약(300자 내)이 본 문서 하단에 링크됨.

---

## Phase 1 — 종합 및 비교

- [ ] 방법론 비교표 작성 (축: 자기참조 깊이 / 저장구조 / 재인덱싱 / 세션 지속성 / 로컬 구현 난이도)
- [ ] Karpathy 방식 vs 기존 프레임워크 장단점
- [ ] 핵심 개념 용어집 (self-reference / episodic memory / procedural memory / semantic memory / reflection / consolidation)
- [ ] 산출: `apply/comparison.md`

---

## Phase 2 — OFFCODE 적용 설계

- [ ] OpenCode + OmO의 현재 메모리 구조 파악 (notepad, skill-loader, continuation hooks, project-memory.json)
- [ ] Claude Code auto memory (현재 사용 중인 MEMORY.md 시스템)와 비교
- [ ] **"에이전트별 자기참조" 구현안 설계** — 시지푸스·프로메테우스·아틀라스가 각자 자기 역할·히스토리·능력을 인식하는 구조
- [ ] 최소 스키마 정의 (agent_id, identity, skills, history_pointer, last_reflected_at 등)
- [ ] 산출: `apply/offcode_design.md`

---

## Phase 3 — PoC

- [ ] 1개 에이전트(후보: 오드리 Dr. Oh 또는 소규모 시지푸스 클론)에 자기참조 적용
- [ ] 세션 재시작 후 자기 상태 복원 테스트
- [ ] 파일 기반 시작 → 필요 시 SQLite/sqlite-vec로 확장
- [ ] 회고(reflection) 루프 추가: 세션 종료 시 자기 기억 요약·재기록
- [ ] 산출: `apply/poc_report.md` + 실제 코드

---

## Phase 4 — 전파

- [ ] OFFCODE 본체 통합 (OmO 훅 또는 Claude Code auto memory 확장)
- [ ] 오드리(Dr. Oh) 체크리스트에 "자기참조 메모리 상태" 항목 추가
- [ ] 다른 에이전트(시지푸스·아틀라스)로 확대
- [ ] 배포 패키지 포함

---

## 팀 편성 (Phase 0)

병렬 서브에이전트 3개로 구성:

- **L1 researcher** — Karpathy gist 원문 Fetch + 분석
- **L2 researcher** — WebSearch로 2025–2026 최신 프레임워크 스캔
- **L3 researcher** — WebSearch로 실제 적용 사례 스캔

각 에이전트는 백그라운드에서 실행되며, 완료 시 `research/` 아래 파일로 결과물 배치.

---

## 리서치 결과 요약 (2026-04-13 Phase 0 완료)

### L1 — Karpathy gist 분석 → `research/karpathy_gist_analysis.md`

Karpathy gist는 자기참조 에세이가 아니라 **"LLM Wiki" 패턴 문서**. 핵심 주장: RAG가 매 질문마다 지식을 재발견하는 반면, LLM Wiki는 **인제스트 타임에 지식을 컴파일**해 마크다운 그래프로 누적하고 LLM이 wiki 유지보수자 역할. 아키텍처는 **3-레이어(Raw sources / Wiki / Schema=CLAUDE.md) + 3-연산(Ingest/Query/Lint) + 2개 특수 파일(`index.md`, `log.md`)**. 임베딩 DB 없이 `index.md`만으로 ~100 sources 운영 가능. 멘탈 모델: "메모리 = 사람이 읽을 수 있는 git 버전 관리 마크다운", self-reference=wiki 읽기, reflection=lint 패스. Vannevar Bush Memex의 유지보수 난제를 LLM이 해결한다는 프레임. **폐쇄망/로컬 LLM 적합성 매우 높음**.

### L2 — 2025–2026 최신 방법론 → `research/latest_methods_2026.md`

네 방향 수렴: (1) **Letta**(MemGPT 제품화, 2025-10 V1) — core/recall/archival 블록 업계 표준. (2) **A-MEM**(NeurIPS 2025) — Zettelkasten 자기조직화, 쓰기마다 링크·재색인 evolve. (3) **Mem0 v1.0**(41k⭐, Apache-2.0) — vector+graph+KV, LOCOMO에서 OpenAI Memory +26% / -91% 지연. (4) **MIRIX** 6-type 멀티에이전트 — LOCOMO 85.4% SOTA. 제품 현장(Claude Code Auto Memory + **Auto Dream**, Windsurf, Gemini)은 "규칙파일 + 자동노트 + 주기 consolidation" 3층으로 수렴. Karpathy Wiki는 이 스펙트럼의 **극미니멀 끝** — Auto Dream의 consolidation + A-MEM의 evolution을 DB 없이 markdown+schema로 구현. **OFFCODE 추천 3종**: (1) Karpathy Wiki + Auto Dream 트리거를 메인 엔진 (2) Letta 자가호스팅+Ollama(31B 전용) 서브 (3) A-MEM evolution을 markdown 위에 오버레이. 제외: Mem0(graph DB 의존), MIRIX(풀스택 과부하), LangGraph(중복).

### L3 — 실제 적용 사례 → `research/application_cases.md`

**Claude Code 4레이어(CLAUDE.md + Auto Memory + Session + Auto Dream)가 OFFCODE 최적 레퍼런스** — 파일 기반, 시맨틱 서치 불필요, 폐쇄망 친화. 보완 필요: MEMORY.md 25KB/200라인 한계, 멀티에이전트 레이스 컨디션, "왜"를 저장 못 하는 한계. OSS 1순위 **Mem0(41k⭐)**, 2순위 **Graphiti(20k⭐, FalkorDB 로컬 가능, Gemma4 26B 친화)** — 둘 다 로컬화 개조 필요. **운영 실패 교훈**: LangChain 이메일 에이전트 consolidation 실패(메모리 무한증식, 프롬프트 전담자 필요) / POC→프로덕션 월 $500→$847K, full-context 17초 latency / ChatGPT 2025-02 사일런트 메모리 붕괴 → **벤더 락인 금지, git-backed 로컬 메모리가 답** / Devin은 장기메모리 포기하고 세션 파일시스템 활용 — 반면교사. 벤치마크: LoCoMo MemMachine 0.9169, LongMemEval OMEGA 95.4%. **최종 권고**: Claude Code 4레이어를 OmO 훅으로 재구현 + Graphiti(FalkorDB) 의사결정 그래프 레이어 얹는 하이브리드. 규율: 스키마 validation 강제, 세션 종료 시 reflect/compact, 중요 업데이트 human-in-the-loop, 파일 크기 모니터링.

---

## Phase 0 종합 판단 (VDI 세션)

3레인이 **한 결론으로 수렴**: Karpathy Wiki 패턴 + Claude Code 4레이어 + A-MEM evolution 오버레이 = OFFCODE 최적 아키텍처. 벤더 락인/외부 DB 의존 없음. 이미 우리가 쓰고 있는 `MEMORY.md` 시스템이 이 계보의 최소 구현체 → **Phase 2 설계 난이도가 예상보다 낮음**.

Phase 1(비교표) 착수 조건 만족. 다음 세션에서 `apply/comparison.md` 작성 예정.

---

*문서 작성: 2026-04-13 (VDI 세션)*
*Phase 0 완료: 2026-04-13 (백그라운드 에이전트 3레인 병렬 실행)*
