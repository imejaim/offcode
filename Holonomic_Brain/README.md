# Holonomic Brain

> **Agentis Layer 3 지식 인프라의 현재 구현체.**
> Karpathy LLM Wiki 패턴(markdown + schema + index + log + lint)을 폐쇄망 + 로컬 LLM 환경에 적용.

## 왜 존재하는가

- 매 세션마다 "저번에 VDI 얘기한 거 다시 설명할게"가 반복되는 비용 제거
- 프로젝트 결정·아키텍처·마일스톤을 **세션·에이전트에 종속되지 않는 단일 진실**로 저장
- 벡터 DB/외부 서비스 없이 git + markdown만으로 Agentium 내 어떤 에이전트든 접근 가능

## 3초 요약

```
knowledge/
├── raw/MANIFEST.md    ← 원본 소스 인벤토리 (물리 복제 없음)
├── wiki/00~11_*.md    ← 컴파일된 주제별 지식 (11개 문서)
├── visual/brain_graph.html  ← vis-network 인터랙티브 그래프
└── log.md             ← 변경 이력
```

## 빠르게 시작

### 1) 그래프 열기

**Windows (현재 VDI)**:
```powershell
start Holonomic_Brain/knowledge/visual/brain_graph.html
```

**Linux (블랙웰/WSL)**:
```bash
xdg-open Holonomic_Brain/knowledge/visual/brain_graph.html
```

노드를 클릭하면 우측 패널에 요약과 관련 wiki 링크가 뜬다.

### 2) 인덱스부터 읽기

```
Holonomic_Brain/knowledge/wiki/00_index.md
```

11개 wiki 문서에 카테고리별로 진입할 수 있다.

### 3) 새 세션에서 사용

[`11_agent_evolution_protocol.md`](knowledge/wiki/11_agent_evolution_protocol.md) 의 5단계 부트스트랩 순서를 따른다. `CLAUDE.md`의 "세션 시작 시" 섹션이 이를 강제한다.

## 구성 원칙 (Karpathy + Agentis 적응)

1. **Single source of truth** — 한 정보는 한 곳에만. 다른 곳에는 링크.
2. **Superseded 보존** — 낡은 결정은 삭제 대신 `**Superseded**` 표기로 남긴다.
3. **Source 필수** — 모든 wiki 엔트리 끝에 `## Source` 섹션.
4. **폐쇄망 제1원칙** — 외부 DB/벡터 서비스 금지. vis-network CDN도 오프라인 fallback 주석 포함.
5. **개인 메모리와 분리** — Claude Code auto memory(개인 맥락) vs Holonomic Brain(프로젝트 맥락).

## 유지보수

- **Ingest**: 세션 중 새 결정·마일스톤 발생 시 해당 wiki에 편집 반영 + `log.md`에 1줄
- **Lint**: 주 1회 권장. 깨진 링크/중복/Superseded 상태 점검
- **크기 제한**: 개별 wiki 파일 8KB 초과 시 분할 검토
- **그래프 동기화**: wiki 추가/삭제 시 `visual/brain_graph.html`의 nodes/edges 배열 업데이트

## 관련 문서

- [`../docs/AGENTIS_ARCHITECTURE.md`](../docs/AGENTIS_ARCHITECTURE.md) — 플랫폼 아키텍처 원본
- [`../Second_Brain/`](../Second_Brain/) — 리서치 페이즈(원전 보존, 본 시스템의 씨앗)
- [`../audrey_v3.0/`](../audrey_v3.0/) — Agentium 헬스체크 구현

---

*초기화: 2026-04-14 | Karpathy Wiki 패턴 v1*
