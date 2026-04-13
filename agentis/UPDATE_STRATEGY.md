# opencode 사내망 업데이트 전략

> opencode 본가가 업데이트되었을 때 사내망에 설치된 버전을 어떻게 갱신할 것인가.
> 두 가지 길이 있고, 지금은 **옵션 1**로 간다. 옵션 2는 차후 과제.

---

## 옵션 1 — VDI 빌드 → GitHub Releases → 사내 덮어쓰기 ✅ (현재 채택)

```
[VDI] 업데이트 pull → 빌드 → GitHub Releases 업로드
                              ↓
[사내망] gh/브라우저로 다운로드 → opencode.exe 덮어쓰기
```

### 절차

#### 1단계 — VDI에서 빌드 갱신

```bash
cd opencode-dev
git pull origin dev                  # 최신 코드
ELECTRON_SKIP_BINARY_DOWNLOAD=1 bun install
cd packages/opencode
bun run build --skip-embed-web-ui --skip-install --single
```

산출물: `packages/opencode/dist/opencode-windows-x64/bin/opencode.exe`

#### 2단계 — agentis/dist에 복사 후 GitHub Release 발행

```bash
cp packages/opencode/dist/opencode-windows-x64/bin/opencode.exe \
   ../../../agentis/dist/opencode-windows-x64/

cd /c/Users/dongho.yoon/project/999_offcode

# 새 릴리스 만들기 (날짜 + opencode 버전)
gh release create opencode-2026-04-13 \
  agentis/dist/opencode-windows-x64/opencode.exe \
  --title "opencode 2026-04-13 (windows-x64)" \
  --notes "opencode-dev dev 브랜치 빌드. 단일 exe, TUI 전용."
```

#### 3단계 — 사내망(노트북/사내PC)에서 받기

**방법 A — gh CLI**
```powershell
gh release download opencode-2026-04-13 -R imejaim/offcode -p "opencode.exe"
Move-Item .\opencode.exe "$env:USERPROFILE\tools\opencode\opencode.exe" -Force
opencode --version
```

**방법 B — 브라우저**
1. https://github.com/imejaim/offcode/releases 접속
2. 최신 릴리스의 `opencode.exe` 다운로드
3. `%USERPROFILE%\tools\opencode\opencode.exe`에 덮어쓰기

### 장단점

| 구분 | 내용 |
|------|------|
| 👍 | 결재·방화벽 작업 0. 지금 당장 가능. exe 한 개만 갈아치우면 끝 |
| 👍 | 빌드 검증을 사외에서 끝내고 내려보내므로 사내 환경 오염 없음 |
| 👍 | 깃허브가 곧 배포 채널 + 변경 이력 (Release notes로 추적) |
| 👎 | 매번 사람이 빌드·업로드해야 함 (자동화 가능하긴 함) |
| 👎 | 빌드 시점에 폐쇄망 회피 옵션 3종 챙겨야 함 (메모리/문서로 관리) |

---

## 옵션 2 — 사내망에서 직접 업데이트 ⏳ (차후 과제)

```
[사내망 PC] opencode upgrade  → npm/github releases 직접 호출
            └─ 방화벽·프록시·도메인 화이트리스트 결재 필요
```

### 필요한 결재 항목 (예상 — 확인 필요)

| 항목 | 무엇을 위해 | 결재 대상 |
|------|------------|----------|
| 도메인 화이트리스트: `github.com`, `objects.githubusercontent.com` | release 자산 다운로드 | 보안팀/네트워크팀 |
| 도메인 화이트리스트: `registry.npmjs.org` | npm 패키지 (만약 npm 경로 쓸 거면) | 보안팀 |
| 도메인 화이트리스트: `bun.sh`, `github.com/oven-sh/bun` | bun 자체 업데이트 | 보안팀 |
| 프록시 인증서 설치 | HTTPS 프록시 통과 | IT지원팀 |
| 프록시 환경변수 (`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`) | bun/gh/curl이 프록시 인식 | 사용자 가이드 |
| `opencode upgrade` 명령 또는 자체 갱신 스크립트 | 실제 업데이트 트리거 | (구현 필요) |
| (선택) 사내 npm 미러 / 사내 GitHub 미러 | 외부 직결 회피 | 인프라팀 |

### 결재 절차 (가설)

1. **현황 조사** — 사내 보안 정책, 기존에 외부 접근 허용된 도구 목록 확인
2. **신청서 작성** — "AI 코딩 에이전트 업데이트 채널 확보" 명목
3. **테스트 환경에서 PoC** — 1대 PC로 화이트리스트 효과 검증
4. **전사 배포** — 안내 문서 + 자동화 스크립트 + 헬프데스크 가이드

### 장단점

| 구분 | 내용 |
|------|------|
| 👍 | 한 번만 뚫으면 그 뒤로 사람 손 안 가도 됨 |
| 👍 | 사용자가 본인 PC에서 `opencode upgrade` 한 줄로 끝 |
| 👍 | 빌드 노하우 잊혀져도 본가 릴리스를 그대로 받음 |
| 👎 | 결재 항목·관계부서 파악만으로도 한 달치 작업 |
| 👎 | 보안팀이 GitHub 직결을 막을 수도 있음 (대안: 사내 미러) |
| 👎 | 한 번 뚫리면 다른 도구도 같은 채널 노릴 거라 거버넌스 부담 |

---

## 결정

- **지금**: 옵션 1로 간다. 빌드 노하우는 이미 검증됨 (`project_opencode_build` 메모리)
- **차차**: 옵션 2의 결재 항목 리스트를 회사 정책 확인하면서 채워나간다
- **트리거**: opencode 본가가 메이저 릴리스를 자주 내거나, 사용자 수가 늘어 수동 배포가 부담될 때 옵션 2로 전환 검토

---

## 버전/릴리스 명명 규칙

GitHub Release 태그 형식:
```
opencode-YYYY-MM-DD              # 예: opencode-2026-04-13
opencode-YYYY-MM-DD-hotfix1      # 같은 날 핫픽스
```

Release 본문에는 반드시 기록:
- opencode-dev 커밋 해시 (`git rev-parse HEAD`)
- 빌드 옵션 (`--skip-embed-web-ui --skip-install --single` 등)
- 변경 요약 (본가 changelog 참고)
- 알려진 제약 (예: 웹 UI 미포함)
