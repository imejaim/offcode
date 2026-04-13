# Agentis 서브프로젝트

> Agentis 플랫폼 빌드/배포 관련 작업 노트.
> 사내망(폐쇄망) 환경에서 OpenCode 기반 에이전트 환경을 올리는 절차를 정리한다.

## 문서

- [사내망에서 opencode 설치하기](./사내망_opencode_설치.md) — 메인 목표. 바이너리 이식 절차
- [Bun 설치 카드](./install_bun.md) — bun 오프라인 설치 (보조)
- [업데이트 전략](./UPDATE_STRATEGY.md) — opencode 본가 업데이트 반영 절차 (옵션 1: VDI빌드→Releases / 옵션 2: 사내직결, 결재항목)

## 배포 산출물

- [`dist/opencode-windows-x64/`](./dist/opencode-windows-x64/) — **빌드 완료 패키지 (2026-04-13)**
  - `opencode.exe` (157 MB, 단일 실행파일, TUI 전용)
  - `README_사내망_설치.md` — 복붙용 PowerShell 설치 명령어 포함
  - 사내망에 이 폴더 통째로 복사하면 끝

## 상위 문서

- `../docs/AGENTIS_ARCHITECTURE.md` — 3레이어 아키텍처
- `../docs/CONSTRAINTS.md` — 블랙웰 서버 제약사항
- `../docs/INSTALL_MANUAL.md` — 환경 설치 매뉴얼
