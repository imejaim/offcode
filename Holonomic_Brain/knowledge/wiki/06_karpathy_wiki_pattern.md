# 06. Karpathy LLM Wiki 패턴 (원전 분석)

> 원문: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
> Second Brain Researcher L1 분석 결과를 바탕으로 재컴파일.

## 핵심 주장

Karpathy의 gist는 *자기참조 에세이*가 아니라 **"LLM Wiki"** 라는 개인 지식 베이스 패턴 문서다. 제목 그대로 *A pattern for building personal knowledge bases using LLMs*.

### RAG와의 근본 차이

- **RAG**: 매 질문마다 원본 소스에서 지식을 **재발견**(retrieval) → 비용·지연 누적
- **LLM Wiki**: **인제스트 타임에 지식을 컴파일**해 마크다운 그래프로 누적 → 조회는 그냥 읽기

### LLM의 역할

LLM은 질문자가 아니라 **wiki의 유지보수자(maintainer)** 다. Vannevar Bush의 Memex가 풀지 못했던 "누가 링크를 유지하느냐" 문제를 LLM이 해결한다.

## 아키텍처 (3-레이어 × 3-연산 × 2-특수파일)

### 3 레이어

```
[Raw sources]        ← 원본 문서, 대화, 코드, 티켓…
      │ ingest
      ▼
[Wiki (markdown)]    ← 컴파일된 지식. 사람도 LLM도 읽을 수 있는 형태
      │ query
      ▼
[Schema (CLAUDE.md)] ← 위키의 모양/규칙. 메타 지식
```

### 3 연산

1. **Ingest** — raw → wiki에 새 엔트리 추가 + 기존 링크 업데이트
2. **Query** — 사용자 질문 → wiki 그래프 탐색 → 답
3. **Lint** — 깨진 링크, 중복, Superseded 대체 검증 (reflection pass)

### 2 특수 파일

- **`index.md`** — 최상위 진입점. 수동 또는 자동 업데이트. 임베딩 DB 없이 이 파일만으로 ~100 sources 규모 관리 가능
- **`log.md`** — 변경 로그. 인간 가독. git과 이중 기록 권장

## 멘탈 모델

- "메모리 = 벡터"가 아니라 **"메모리 = 사람이 읽을 수 있는 git 버전 관리 마크다운"**
- **self-reference = wiki 읽기**
- **reflection = lint 패스**
- **consolidation = 정기 ingest + 링크 재정리**

## 강점

1. 임베딩 DB·벡터스토어 불필요 → 폐쇄망/로컬 LLM에 매우 적합
2. git diff로 변경 이력 추적 → 롤백·블레임 자연스러움
3. 스키마가 CLAUDE.md에 있어 LLM이 스스로 구조를 이해
4. 인덱스·log.md가 사람 협업에도 투명

## 약점과 완화

- ~100 sources 초과 시 index.md가 비대해진다 → 카테고리별 sub-index 필요
- 일관된 ingest는 LLM 품질에 의존 → Gemma4처럼 instruction following이 약한 모델에선 단계별 파이프라인 필요
- lint 주기 설정이 자의적 → log.md에 lint 일시 강제 기록

## Agentis 적용 고려사항

1. **Gemma4 한계 대응**: ingest를 단일 프롬프트 대신 (1) 소스 요약 → (2) 관련 wiki 찾기 → (3) 링크 제안 → (4) 병합 쓰기 **4단계 파이프라인**으로 분해
2. **Obsidian GUI 없음**: CLI 기반 그래프 덤프 스크립트 또는 mkdocs 정적 빌드로 대체. 본 프로젝트는 **vis-network HTML**로 구현 → [`../visual/brain_graph.html`](../visual/brain_graph.html)
3. **임베딩 없이 검색**: ripgrep + BM25 스코어링으로 충분. 벡터 검색은 ~200 sources 이후 도입 검토
4. **Schema in CLAUDE.md**: Agentis의 `CLAUDE.md`가 이미 이 역할 → Holonomic Brain의 Layer 0

## 관련 노드

- [07. 2025-2026 메모리 수렴선](07_memory_convergence_2026.md) — Karpathy Wiki는 이 스펙트럼의 극미니멀 끝
- [08. 실제 적용 사례](08_production_cases.md) — Claude Code 4레이어가 같은 계보
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md) — **본 시스템 자체가 이 패턴의 구현체**

## Source

- `Second_Brain/research/karpathy_gist_analysis.md` (L1 원전 분석)
- <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
