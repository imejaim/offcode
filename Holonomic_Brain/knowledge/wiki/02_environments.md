# 02. 환경 토폴로지 (4환경)

Agentis가 배포·검증되는 4개 물리/가상 환경.

## VDI (현재 코부장 실행 환경)

- **IP**: 10.44.33.205 (Windows 11)
- **호스트**: SEC-AI-D-02887 (사내 데스크탑 안에서 VDI 클라이언트로 실행)
- **GPU**: 없음
- **역할**: 코부장(Claude Code) 전용 — 문서/코드 작성, 리서치, gist 소통
- **네트워크**: 사내 직접 제어는 불가하지만 **블랙웰 Ollama(10.88.22.29:11434)에는 실제 도달**(2026-04-13 확인, 118ms 응답). 구 가정 "VDI 완전 분리"는 **Superseded**
- **전달 채널**: github push/pull + gist 댓글
- **자기참조 규칙**: 코부장은 "VDI에서 돌아가는 Claude Code" 정체성을 매 세션 메모리에서 복원

## 사내 데스크탑 (DONGHO-YOON04)

- **IP**: 10.88.21.220 (Windows 11)
- **GPU**: GT 1030 2GB (디스플레이용), RAM 32GB
- **역할**: 메인 개발 PC. 블랙웰 원격으로 OpenCode/OmO 구동
- **OpenCode**: 1.3.16, OmO oh-my-openagent 3.15.3
- **마일스톤**: 2026-04-13 시지푸스 Gemma4 31B 원격 응답 성공 (블랙웰 baseURL로 1줄 치환 후)

## 사내 노트북 (DONGHO-YOON01)

- **IP**: 10.88.22.208 (Windows 11)
- **GPU**: RTX 4070 8GB, RAM 64GB
- **역할**: 테스트베드. 블랙웰 없이 **자체 Gemma4 구동 검증용**(팀원 배포 전)
- **상태**: 현재 클린 (OpenCode/OmO/Ollama 미설치)

## 블랙웰 서버

- **IP**: 10.88.22.29 (Ubuntu)
- **GPU**: RTX PRO 6000 Blackwell × 2 (96GB)
- **호스트**: user-GNRD8-2L2T
- **LLM 서빙**: Ollama 0.20.4 (메인) + vLLM gemma4venv (백업)
- **역할**: 사내 LLM 서빙 본체. SSH 접속으로 회장님이 터미널 작업
- **마일스톤**: 2026-04-10 시지푸스 첫 응답 / 2026-04-13 오드리 v3.1 `AGENTIS_READY=TRUE` 첫 획득

## 관계도

```
    ┌──── VDI (10.44.33.205) ────┐
    │  코부장 실행, 원격 Ollama OK│
    └───┬────────────┬───────────┘
        │ github      │ gist
        ▼             ▼
    ┌──────────────────────────┐
    │ 데스크탑 (10.88.21.220)   │──┐
    │ 메인 개발, 원격 Ollama    │  │
    └──────────────────────────┘  │ OpenCode
                                   ├─→ 블랙웰 (10.88.22.29)
    ┌──────────────────────────┐  │    Ollama :11434 + vLLM :8000
    │ 노트북 (10.88.22.208)     │  │    Gemma4 31B/26B/E4B
    │ 테스트베드, 자체 Gemma4   │──┘
    └──────────────────────────┘
```

## 관련 노드

- [03. Gemma4 Ollama 서빙](03_gemma4_ollama.md) — 블랙웰이 서빙하는 것
- [04. 시지푸스 마일스톤](04_sisyphus_milestones.md) — 각 환경의 검증 이력
- [05. 오드리 v3.1](05_audrey_v31.md) — 환경 자각 로직 (ENV1)
- [09. 블랙웰 제약사항](09_constraints_blackwell.md) — 블랙웰 특이사항

## Source

- memory `user_current_env.md`, memory `project_environments.md`
- `CLAUDE.md` (Gist 소통 규칙)
