# 08. 실제 적용 사례와 운영 교훈

> Second Brain Researcher L3. 2025–2026 프로덕션/OSS 배포 실측.

## 최적 레퍼런스: Claude Code 4레이어

**Claude Code의 4레이어 구조**가 Agentis 폐쇄망 환경에 가장 적합하다는 것이 L3의 결론.

```
Layer 1: CLAUDE.md          ← 사용자가 직접 쓰는 프로젝트 규칙 + 지시
Layer 2: Auto Memory        ← MEMORY.md 인덱스 + 개별 memory/*.md 파일들
Layer 3: Session Memory     ← 현재 대화 맥락 (휘발성, 세션 종료 시 소멸)
Layer 4: Auto Dream         ← 주기적 consolidation (요약, 링크, 재기록)
```

**장점**:
- 파일 기반 → 폐쇄망 친화 (외부 DB 없음)
- 시맨틱 서치 불필요 → Gemma4 같은 로컬 모델로도 동작
- git-backed → 롤백·블레임·diff 자연스러움
- 사용자 투명 (수동 편집 가능)

**한계와 보완 포인트**:
- MEMORY.md 25KB / 200라인 로딩 한계 → **Holonomic Brain이 카테고리 분할로 해결**
- 멀티에이전트 레이스 컨디션 → 병렬 쓰기 시 파일 락 필요
- "왜"를 저장 못 하는 경향 → **feedback 메모리에 `Why:` 필드 강제**

## OSS 순위 (L3 선정)

| 순위 | 프로젝트 | ⭐ | 특징 | Agentis 적용성 |
|------|----------|----|------|-----------------|
| 1 | **Mem0** | 41k | AWS Agent SDK exclusive, LOCOMO +26% | graph DB 의존 → 폐쇄망 개조 필요 |
| 2 | **Graphiti** | 20k | **FalkorDB 로컬 가능**, Gemma4 26B 친화 | 하이브리드 후보 (Karpathy Wiki + 의사결정 그래프 레이어) |

## 운영 실패 교훈 (반면교사)

### LangChain 이메일 에이전트
- consolidation을 **일반화 못 해** 메모리 무한 증식
- "프롬프팅 full-time 전담자" 필요 수준 → **단순한 규칙 + 수동 lint 조합이 더 안정**

### POC → 프로덕션 비용 폭증
- 월 $500 → $847K
- full-context 호출당 17초 latency
- **교훈**: 토큰 예산 먼저 정하고, 해당 예산 내에서만 consolidation 돌려라

### ChatGPT 2025-02 사일런트 메모리 붕괴
- 벤더가 메모리 포맷을 바꾸면서 사용자 데이터 일부 소실
- **교훈**: 벤더 락인 금지. **git-backed 로컬 메모리**가 답

### Devin / Cognition Labs
- 장기메모리를 **아예 포기**하고 세션 내 파일시스템 활용
- **교훈**: 장기 기억이 꼭 필요한지 먼저 질문. 세션 파일시스템 + git 히스토리만으로도 많은 경우 충분

## 벤치마크 현황 (2026-04 기준)

| 벤치 | 지표 | SOTA |
|------|------|------|
| LoCoMo | 종합 | MemMachine 0.9169 |
| LongMemEval | 정답율 | OMEGA 95.4% |

**Agentis용 회귀 테스트 권장**: 한국어 축소판을 만들어 Holonomic Brain에 얹고, ingest 품질이 떨어지면 알람.

## Holonomic Brain이 채택한 운영 규율 (L3 권고)

1. **스키마 validation 강제** — 모든 wiki 엔트리는 `Source` 섹션 필수
2. **세션 종료 시 reflect/compact** — `log.md`에 한 줄 기록 + 깨진 링크 lint
3. **중요 업데이트 human-in-the-loop** — 아키텍처 결정 등은 회장님 승인 후 커밋
4. **메모리 파일 크기 모니터링** — 개별 wiki 파일 8KB 초과 시 분할 고려
5. **벤더 락인 금지** — git + markdown 외 의존 금지 (vis-network는 CDN 옵션이지만 fallback은 로컬 복사본 준비)

## 관련 노드

- [07. 메모리 수렴선 2026](07_memory_convergence_2026.md) — L2 기술 서베이
- [10. Holonomic Brain 자기참조](10_holonomic_brain_itself.md) — 본 시스템이 적용한 선택

## Source

- `Second_Brain/research/application_cases.md` (L3 전체 리포트, 소스 URL 포함)
