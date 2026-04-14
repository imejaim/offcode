# Raw Sources Manifest

> Karpathy LLM Wiki의 "Raw sources" 레이어. 본 파일은 물리 복제 대신 **인벤토리(manifest)** 형식이다.
> 원본은 각자의 정규 위치에 있고, 컴파일은 여기에 등재된 파일을 읽어 `../wiki/*.md`를 생성한다.

## 왜 manifest 형식인가

1. 중복 저장 방지 (Karpathy Wiki 원칙: single source of truth)
2. 원본 편집이 즉시 반영됨 (다음 ingest 사이클에서)
3. git log가 원본과 manifest 양쪽에 남아 이중 추적

## 컴파일 규칙

- 타임스탬프 상충 시 최신이 우선, 옛 버전은 wiki에 `**Superseded**`로 남긴다 (삭제 금지)
- 원본 파일이 사라지면 manifest에 `⚠️ missing @ <date>` 표기 후 wiki lint 실행
- 새 원본 추가 시 본 파일의 해당 카테고리 말미에 라인 추가 후 `log.md`에 기록

---

## 인벤토리

### A. 플랫폼 설계 문서

| 경로 | 컴파일 대상 wiki | 최종 편집 | 비고 |
|------|------------------|-----------|------|
| `../../../docs/AGENTIS_ARCHITECTURE.md` | 01, 02 | 2026-04-13 | Agentis 브랜드 + 4서브브랜드 |
| `../../../docs/CONSTRAINTS.md` | 09 | 2026-04-13 | 블랙웰 제약 (단일 진실) |
| `../../../docs/INSTALL_MANUAL.md` | (대기) | 2026-04-13 | 재작성 예정 |
| `../../../CLAUDE.md` | 00, 11 | 2026-04-14 | 프로젝트 규칙 = Karpathy Schema |

### B. 오드리 (Agentium 헬스체크)

| 경로 | 컴파일 대상 | 최종 편집 |
|------|-------------|-----------|
| `../../../audrey_v3.0/README.md` | 05 | 2026-04-13 |
| `../../../audrey_v3.0/DESIGN.md` | 05 | 2026-04-13 |
| `../../../audrey_v3.0/docs/headless_opencode.md` | 04, 05 | 2026-04-13 (Scout) |
| `../../../audrey_v3.0/tests/scenarios.md` | 05 | 2026-04-13 (Tester) |
| `../../../audrey_v3.0/src/` | 05 | 2026-04-13 (Builder, 16파일) |
| `../../../audrey/UPGRADE_PLAN_v3.md` | 05 | 2026-04-13 |

### C. Second Brain 리서치 (원전 → wiki 일부 재컴파일)

| 경로 | 컴파일 대상 | 최종 편집 |
|------|-------------|-----------|
| `../../../Second_Brain/research/karpathy_gist_analysis.md` | 06 | 2026-04-13 (L1) |
| `../../../Second_Brain/research/latest_methods_2026.md` | 07 | 2026-04-13 (L2) |
| `../../../Second_Brain/research/application_cases.md` | 08 | 2026-04-13 (L3) |
| `../../../Second_Brain/PLAN.md` | 06, 10 | 2026-04-13 |

### D. 대화 기록 (gist 아카이브)

| 경로 | 컴파일 대상 | 기간 |
|------|-------------|------|
| `../../../_archive/WORKPLAN_OFFCODE_PHASE1.md` | 04 | 2026-04-07 ~ 10 (Superseded by Agentis rebranding) |
| `../../../_archive/gist_comments_20260410.txt` | 03, 04 | 2026-04-10 Gemma4/Ollama 전환 디버깅 |
| `../../../_archive/gist_comment_20260413_win_sisyphus_diag.md` | 04 | 2026-04-13 데스크탑 진단 |
| `../../../_archive/gist_comment_20260413_win_sisyphus_fix1.md` | 04 | 2026-04-13 baseURL 수정 |
| `../../../_archive/gist_comment_20260413_audrey_v31.md` | 05 | 2026-04-13 오드리 v3.1 패치 댓글 |

### E. Agentis 서브 (사내망 설치)

| 경로 | 컴파일 대상 | 최종 편집 |
|------|-------------|-----------|
| `../../../agentis/README.md` | 02 | 2026-04-13 |
| `../../../agentis/사내망_opencode_설치.md` | (09 보강 후보) | 2026-04-13 |
| `../../../agentis/install_bun.md` | (09 보강 후보) | 2026-04-13 |

### F. 개인 메모리 (코부장 자기참조)

프로젝트 레포 외부, `~/.claude/projects/.../memory/*.md`. 본 매니페스트의 S 카테고리로 참조만 하고 Holonomic Brain에 직접 컴파일하지 않는다(개인 맥락 보호).

| 메모리 파일 | wiki 교차참조 |
|-------------|----------------|
| `project_offcode.md` (Agentis 브랜드) | 01 |
| `project_environments.md`, `user_current_env.md` | 02 |
| `project_gemma4_model_plan.md`, `project_blackwell_env.md` | 03, 09 |
| `project_sisyphus_fix.md` | 04 |
| `project_audrey_v23.md` (v3.1 업데이트됨) | 05 |
| `project_second_brain.md` | 06, 10 |
| `reference_karpathy_self_ref.md` | 06 |

---

*Manifest 초기화: 2026-04-14 | 다음 lint 권장: 2026-04-21*
