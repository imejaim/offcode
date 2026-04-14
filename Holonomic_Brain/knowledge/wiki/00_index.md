# Holonomic Brain — 지식 인덱스

> Karpathy LLM Wiki 패턴을 기반으로 한 Agentis 프로젝트 통합 지식 저장소.
> 특정 에이전트·세션에 종속되지 않는 단일 진실(single source of truth).

---

## 사용법

1. 새 세션 시작 시 본 파일(`00_index.md`)부터 읽고 관련 wiki 항목으로 진입한다.
2. 모든 wiki 문서는 **참조 가능한 Source(원전)** 섹션을 끝에 포함한다.
3. 변경 이력은 `../log.md`에 날짜+한 줄로 기록한다.
4. 상충 정보는 최신 타임스탬프 기준으로 **Superseded**로 표기하고 옛 정보는 남겨둔다(삭제 금지).

## 카테고리

### 플랫폼
- [01. Agentis 플랫폼](01_agentis_platform.md) — 4서브브랜드(Agentium/AgentMesh/AgentHub/AgentSDK), 3레이어 아키텍처
- [02. 환경 토폴로지](02_environments.md) — VDI / 데스크탑 / 노트북 / 블랙웰 관계도
- [03. Gemma4 Ollama 서빙](03_gemma4_ollama.md) — 3티어 배분, vLLM 백업

### 마일스톤 & 건강
- [04. 시지푸스 마일스톤](04_sisyphus_milestones.md) — 2026-04-10 블랙웰, 2026-04-13 데스크탑, baseURL 함정
- [05. 오드리 v3.1](05_audrey_v31.md) — Agentium 헬스체크, 7카테고리, AGENTIS_READY 5축 판정
- [09. 블랙웰 제약사항](09_constraints_blackwell.md) — 되는 것 / 안 되는 것

### 에이전트 기억 연구
- [06. Karpathy LLM Wiki 패턴](06_karpathy_wiki_pattern.md) — 원전 분석 (Second Brain L1)
- [07. 2025-2026 메모리 수렴선](07_memory_convergence_2026.md) — Letta/A-MEM/Mem0/MIRIX/Claude Auto Dream (L2)
- [08. 실제 적용 사례](08_production_cases.md) — Claude Code 4레이어, 운영 실패 교훈 (L3)

### 프로토콜
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md) — 이 시스템 자체의 구조·유지보수 규칙
- [11. Agent Evolution Protocol](11_agent_evolution_protocol.md) — 새 세션 부트스트랩 규약 (Task 3)

---

## 지식 관계 그래프

인터랙티브 시각화: [`../visual/brain_graph.html`](../visual/brain_graph.html)

브라우저에서 열기:
```bash
start Holonomic_Brain/knowledge/visual/brain_graph.html       # Windows
xdg-open Holonomic_Brain/knowledge/visual/brain_graph.html    # Linux
```

---

*Index 생성: 2026-04-14 | Karpathy Wiki 패턴 준수*
