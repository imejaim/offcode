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

## 리서치 결과 요약 (완료 후 채움)

### L1 — Karpathy gist 분석
*(에이전트 완료 후 본 위치에 300자 요약)*

### L2 — 최신 방법론
*(에이전트 완료 후 본 위치에 300자 요약)*

### L3 — 적용 사례
*(에이전트 완료 후 본 위치에 300자 요약)*

---

*문서 작성: 2026-04-13 (VDI 세션)*
