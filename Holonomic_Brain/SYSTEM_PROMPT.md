# Holonomic Brain — Agent System Prompt Addendum

> 새 에이전트 세션 시작 시 이 본문을 컨텍스트로 주입한다. (Task 3 Agent Evolution Protocol의 실제 프롬프트 본문)

---

You are working inside the **Agentis** project. Before asking the user about any prior decision, **consult the Holonomic Brain first**:

## Mandatory Bootstrap Order

1. **Read the entry index**:
   `Holonomic_Brain/knowledge/wiki/00_index.md`

2. **Identify your environment** (self-reference):
   `Holonomic_Brain/knowledge/wiki/02_environments.md`
   - Which of the 4 environments are you running in? (VDI / desktop / laptop / blackwell)
   - How do you know?

3. **Load the platform context**:
   `Holonomic_Brain/knowledge/wiki/01_agentis_platform.md`
   - Which Agentis sub-brand does the task touch? (Agentium / AgentMesh / AgentHub / AgentSDK)

4. **Jump to the relevant category** based on user keywords:
   - "시지푸스", "baseURL", "에이전트 안 보임" → `04_sisyphus_milestones.md`
   - "오드리", "AGENTIS_READY", "진단" → `05_audrey_v31.md`
   - "Gemma4", "Ollama", "모델 배분" → `03_gemma4_ollama.md`
   - "기억", "메모리", "wiki" → `06_*`, `07_*`, `08_*`, `10_*`
   - "제약", "안 되는 것", "함정" → `09_constraints_blackwell.md`

5. **For complex dependencies**, open the graph:
   `Holonomic_Brain/knowledge/visual/brain_graph.html`

## Rules

- **Never** re-ask the user to re-explain a decision that already exists in the wiki. **Read it.**
- **If reality contradicts the wiki**, update the wiki first, then proceed.
- **If a wiki entry is missing `## Source`**, distrust it and verify against the current codebase before acting.
- **New decisions / milestones / lessons** must be written back into the appropriate wiki file and logged in `Holonomic_Brain/knowledge/log.md` before the session ends.

## Memory Separation

Two memory systems coexist — do **not** mix them:

| System | Content | Location |
|--------|---------|----------|
| **Claude Code Auto Memory** | 개인 맥락: 사용자 역할, 선호, 피드백 규칙 | `~/.claude/projects/.../memory/*.md` |
| **Holonomic Brain** | 프로젝트 맥락: 아키텍처, 마일스톤, 결정, 기술 계약 | `Holonomic_Brain/knowledge/wiki/*.md` |

Personal preferences go to memory. Objective project facts go to Holonomic Brain. They **reference** each other, they do **not copy** each other.

## Anti-Patterns (금지)

- `Source`가 없는 새 주장 작성
- 낡은 결정을 삭제 (→ `**Superseded**` 표기로 남겨둘 것)
- 개인 메모리 내용을 wiki에 복제
- `00_index.md`를 읽지 않고 다른 wiki로 바로 점프
- 변경 후 `log.md` 미기록

## 진입 확인 카나리

세션 시작 후 첫 응답에서 다음 중 하나 이상 언급하라:
- 현재 돌고 있는 환경 (VDI/데스크탑/노트북/블랙웰) + IP
- 관련 wiki 파일명 (예: "04_sisyphus_milestones.md 참조")

이게 없으면 부트스트랩이 누락된 것으로 간주한다.

---

*본 프롬프트의 권위는 `Holonomic_Brain/knowledge/wiki/11_agent_evolution_protocol.md`에 있다.*
