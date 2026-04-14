# 11. Agent Evolution Protocol

> Task 3: 새로운 에이전트 세션이 시작될 때마다 Holonomic Brain을 **인덱싱**하여 이전 결정 사항을 재설명할 필요 없이 즉시 이어서 작업할 수 있도록 하는 규약.

## 원칙

1. **재설명 금지**: 이미 wiki에 있는 결정을 사용자에게 다시 설명해 달라고 하면 안 된다. 읽어라.
2. **index 우선**: 세션 시작 후 최초 도구 호출은 `knowledge/wiki/00_index.md` 또는 관련 wiki 파일을 읽는 것이어야 한다.
3. **Wiki가 틀리면 고쳐라**: 실제 상태와 wiki가 다르면 wiki를 갱신한 뒤 작업한다.
4. **Source를 의심하지 마라(먼저)**: wiki에 Source가 명시돼 있으면 그대로 믿되, 작업 직전 "before recommending from memory" 규칙대로 현재 상태 1회 검증.

## 부트스트랩 순서 (새 세션용)

매 신규 세션 시작 시 코부장(또는 다른 에이전트)은 아래 순서를 따른다:

### Step 1 — 환경 자각
```
Holonomic_Brain/knowledge/wiki/02_environments.md 읽기
→ 내가 어느 환경에서 돌고 있는가? (VDI/데스크탑/노트북/블랙웰)
→ 확인 방법: hostname, IP, 환경 변수
```

### Step 2 — 플랫폼 맥락
```
Holonomic_Brain/knowledge/wiki/01_agentis_platform.md 읽기
→ Agentis 4서브브랜드 구조
→ 내가 다루는 컴포넌트(Agentium / AgentMesh / ...)가 무엇인가
```

### Step 3 — 카테고리 진입
사용자 요청 키워드 → 해당 wiki 파일로 분기:

| 키워드 | 진입 파일 |
|--------|-----------|
| "시지푸스", "에이전트 안 보임", "baseURL" | `04_sisyphus_milestones.md` |
| "오드리", "헬스체크", "진단", "AGENTIS_READY" | `05_audrey_v31.md` |
| "Gemma4", "Ollama", "모델 배분" | `03_gemma4_ollama.md` |
| "기억", "메모리", "자기참조", "wiki" | `06~08_*.md` + `10_holonomic_brain_itself.md` |
| "제약", "안 되는 것", "함정" | `09_constraints_blackwell.md` |

### Step 4 — 그래프 확인(선택)
복잡한 의존성이 얽힌 작업이면 `visual/brain_graph.html`을 열어 관계를 한 눈에 파악.

### Step 5 — 작업 + 기록
작업 종료 시점에 새 결정·마일스톤·교훈이 생겼다면:
1. 해당 wiki 파일 편집 (Source 섹션 유지)
2. `knowledge/log.md`에 한 줄 추가: `YYYY-MM-DD | 변경자 | wiki 파일 | 한 줄 요약`
3. git 커밋 메시지에 wiki 변경 명시

## CLAUDE.md 연동

프로젝트 `CLAUDE.md`의 "세션 시작 시" 섹션에 본 프로토콜 링크를 박는다. 이미 박힌 상태라면 이 wiki는 그 계약의 본문.

현재 CLAUDE.md 예상 추가 라인:
```markdown
## 세션 시작 시
- `Holonomic_Brain/knowledge/wiki/00_index.md`를 읽고 이전 결정 사항 파악
- ...
```

## 사용자(회장님)에게 미치는 효과

- 새 세션에서 "저번에 우리 VDI 얘기 했잖아, 그거 다시 설명할게" 같은 비용이 사라진다
- 오드리 v3.1이 어떻게 동작하는지 매번 재설명할 필요가 없다
- 블랙웰 제약사항은 항상 `09_constraints_blackwell.md`에서 1회 조회로 끝난다

## 오남용 방지

- 본 프로토콜은 **지식 주입**이지 **의견 주입**이 아니다. 사용자 선호·스타일·피드백은 여전히 Claude Code memory에 머무른다
- wiki가 거대해질 수 있다 → `10_holonomic_brain_itself.md`의 8KB 제한 + lint 주기 엄격 준수
- 잘못된 wiki가 에이전트를 오도할 수 있다 → Source 없는 주장 금지 + human-in-the-loop 승인

## 관련 노드

- [00. Index](00_index.md)
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md)
- [08. 실제 적용 사례 — Claude Code 4레이어](08_production_cases.md)

## Source

- 본 문서가 1차 원전. Task 3 요구사항(홀로노믹 브레인 요구서, 2026-04-14)의 직접 반영.
