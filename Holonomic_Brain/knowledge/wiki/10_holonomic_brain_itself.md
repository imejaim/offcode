# 10. Holonomic Brain — 본 시스템 자체

> 자기참조(self-reference). 이 문서는 Holonomic Brain이 자기 자신을 설명한다.

## 정체

**Holonomic Brain**은 Agentis 프로젝트의 **Layer 3 지식 인프라**의 현재 구현체다. Karpathy LLM Wiki 패턴을 폐쇄망 + 로컬 LLM 제약 하에 적용한 것.

이름의 의미:
- **Holonomic** (홀로노믹) — 그리스어 *holos*(전체) + *nomos*(법칙). 전체가 부분에, 부분이 전체에 반영되는 구조
- 단일 진실(single source of truth)로서 세션·에이전트 경계를 넘어 지식이 축적됨

Second Brain(리서치 페이즈)의 실행 단계. Second_Brain/은 원본 연구로 보존.

## Karpathy 3-레이어 매핑

| Karpathy | Holonomic Brain 구현 |
|----------|----------------------|
| Schema (CLAUDE.md) | `CLAUDE.md` + 본 `10_holonomic_brain_itself.md` |
| Wiki (markdown graph) | `Holonomic_Brain/knowledge/wiki/*.md` (11개) + `visual/brain_graph.html` |
| Raw sources | `Holonomic_Brain/knowledge/raw/MANIFEST.md` (소스 인벤토리) |

## 3-연산 구현

| 연산 | 구현 방식 | 트리거 |
|------|-----------|--------|
| **Ingest** | 코부장이 세션 중 새 결론·결정·마일스톤을 해당 wiki 파일 또는 신규 파일에 추가 | 사건 발생 직후 |
| **Query** | 새 세션이 `00_index.md`를 먼저 읽고 관련 wiki로 진입 | 세션 시작 시 |
| **Lint** | 주 1회(또는 큰 변경 후) 전체 wiki 스캔 → 깨진 링크·중복·Superseded 갱신 | 수동, `log.md`에 기록 |

## 2-특수 파일

- **`00_index.md`** — 최상위 카테고리 + 각 wiki 링크 (본 디렉터리의 엔트리)
- **`../log.md`** — 변경 이력. 한 줄 + 날짜 + 변경자 + 변경 범위

## 파일 구조

```
Holonomic_Brain/
├── README.md                        ← 서브프로젝트 개요
├── SYSTEM_PROMPT.md                 ← Task 3: Agent Evolution Protocol 본문
├── knowledge/
│   ├── raw/
│   │   └── MANIFEST.md              ← 원본 소스 인벤토리 (경로+마지막 컴파일 시점)
│   ├── wiki/
│   │   ├── 00_index.md              ← 진입점
│   │   ├── 01~11_*.md               ← 주제별 지식 문서
│   ├── visual/
│   │   └── brain_graph.html         ← vis-network 인터랙티브 그래프
│   ├── lint/                        ← 린트 결과/보고서 (현재 비어있음)
│   └── log.md                       ← 변경 이력
└── scripts/                         ← (예정) ingest/query/lint 자동화
```

## 유지보수 규칙 (자기참조 계약)

1. **Source 필수**: 모든 wiki 엔트리는 끝에 `## Source` 섹션을 두고 원본 파일/메모리/URL을 명시
2. **Superseded 금지 삭제**: 낡은 정보는 `**Superseded**` 표기로 남겨둔다 (역사 보존)
3. **크기 제한**: 개별 wiki 파일 8KB 초과 시 분할 검토
4. **log.md 중복 쓰기**: 중요 변경은 git 커밋 메시지 + log.md 양쪽 기록
5. **lint 주기**: 최소 주 1회 또는 카테고리 신설 시
6. **시각화 동기화**: wiki 노드 추가/삭제 시 `brain_graph.html`의 nodes/edges 배열도 업데이트

## 코부장 메모리와의 분리

- **Claude Code Auto Memory** (`~/.claude/projects/.../memory/*.md`) → **개인 맥락**: 회장님 역할, 피드백 규칙, 관계 맥락
- **Holonomic Brain** (`Holonomic_Brain/knowledge/wiki/*.md`) → **프로젝트 맥락**: 객관적 기술·아키텍처·마일스톤·결정

둘은 **상호 참조하되 섞이지 않는다**. 메모리가 "회장님은 빈칸 없는 명령을 원한다"를 저장하면, Holonomic Brain은 "오드리 v3.1은 7카테고리를 갖는다"를 저장한다.

## 관련 노드

- [06. Karpathy Wiki 패턴](06_karpathy_wiki_pattern.md) — 본 시스템의 원전
- [07. 메모리 수렴선](07_memory_convergence_2026.md) — 다른 가능성들과 비교
- [08. 실제 적용 사례](08_production_cases.md) — 운영 규율의 근거
- [11. Agent Evolution Protocol](11_agent_evolution_protocol.md) — 본 지식을 새 세션이 어떻게 수용하는가

## Source

- 본 문서는 1차 원전 (primary source). 다른 문서의 요약이 아님.
- 영감: Karpathy LLM Wiki gist (`06_karpathy_wiki_pattern.md`)
