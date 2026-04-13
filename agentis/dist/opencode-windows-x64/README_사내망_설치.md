# opencode 사내망 설치 가이드 (Windows x64)

> **이 폴더 안의 `opencode.exe` 파일 하나만 있으면 끝입니다.**
> 의존성·인터넷·bun·node 전부 불필요. 단일 실행파일.

---

## 0. 패키지 정보

| 항목 | 값 |
|------|-----|
| 파일 | `opencode.exe` |
| 크기 | 약 157 MB |
| 빌드 일시 | 2026-04-13 |
| 버전 | `0.0.0-main-202604130702` |
| 빌드 환경 | VDI (Windows 11, Bun 1.3.12, opencode-dev `dev` 브랜치) |
| 빌드 옵션 | `--single --skip-embed-web-ui --skip-install` (TUI 전용, 웹 UI 미포함) |
| 대상 OS | Windows 10/11 x64 |

---

## 1. 가장 빠른 설치 (1분)

폴더에 압축 해제만 해도 바로 실행 가능합니다.

### PowerShell — 한 줄로 설치

USB나 파일서버에서 `opencode.exe`를 받아두었다면:

```powershell
# 1) 설치 폴더 만들고 복사
$dst = "$env:USERPROFILE\tools\opencode"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item .\opencode.exe $dst\

# 2) PATH에 영구 등록 (사용자 단위)
$old = [Environment]::GetEnvironmentVariable("Path", "User")
if ($old -notlike "*$dst*") {
    [Environment]::SetEnvironmentVariable("Path", "$old;$dst", "User")
    Write-Host "PATH 등록 완료. 새 PowerShell 창을 열어주세요."
}

# 3) 새 PowerShell 창에서 확인
opencode --version
```

---

## 2. 단계별 안내

### 2-1. 파일 복사

이 폴더의 `opencode.exe`를 원하는 위치에 둡니다. 권장 위치:

```
C:\Users\<사번>\tools\opencode\opencode.exe
```

또는

```
D:\bin\opencode.exe
```

> **중요**: `C:\Program Files\` 같은 관리자 권한 폴더는 피하세요.
> 사용자 폴더(`%USERPROFILE%`) 아래가 권한 문제 없습니다.

### 2-2. PATH 등록

#### 방법 A — PowerShell (영구, 권장)

```powershell
$dst = "C:\Users\$env:USERNAME\tools\opencode"
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$dst",
    "User"
)
```

→ **새 PowerShell 창을 열어야 적용됩니다.**

#### 방법 B — GUI (시스템 속성)

1. `Win + R` → `sysdm.cpl` → **고급** 탭 → **환경 변수**
2. **사용자 변수**의 `Path` 선택 → **편집** → **새로 만들기**
3. `C:\Users\<사번>\tools\opencode` 추가 → **확인**
4. 새 터미널 열기

### 2-3. 동작 확인

새로 연 PowerShell/터미널에서:

```powershell
opencode --version
# → 0.0.0-main-202604130702 가 나오면 성공

opencode --help
# 도움말 출력되면 정상

opencode
# TUI 진입
```

---

## 3. 첫 실행 시 체크

opencode는 처음 실행하면 `~/.config/opencode/`(Windows: `%APPDATA%\opencode\`)에 설정 파일을 만듭니다.

폐쇄망(사내망)에서 LLM 호출이 필요하면 사내 LLM 서버(블랙웰 등)를 가리키도록 `opencode.json` 또는 `opencode.jsonc` 설정이 필요합니다. 자세한 건 상위 프로젝트의 `docs/CONSTRAINTS.md`와 `docs/Agentis_ARCHITECTURE.md` 참고.

---

## 4. 제거

```powershell
# 파일 삭제
Remove-Item "$env:USERPROFILE\tools\opencode\opencode.exe"

# PATH에서 제거 (수동: sysdm.cpl 또는)
$dst = "$env:USERPROFILE\tools\opencode"
$path = [Environment]::GetEnvironmentVariable("Path", "User")
$new = ($path -split ";" | Where-Object { $_ -ne $dst }) -join ";"
[Environment]::SetEnvironmentVariable("Path", $new, "User")
```

---

## 5. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `opencode : 용어가 인식되지 않습니다` | PATH 미적용 | 새 PowerShell 창 열기. 그래도 안 되면 PATH 등록 재확인 |
| `이 앱을 실행할 수 없습니다` | SmartScreen 차단 | 우클릭 → 속성 → "차단 해제" 체크 → 확인 |
| 실행은 되는데 LLM 호출 실패 | 사내망 LLM 엔드포인트 미설정 | `opencode.jsonc`에 사내 LLM URL 등록 |
| 한글 깨짐 | 콘솔 코드페이지 | `chcp 65001` 입력 후 재실행 |

---

## 6. 빌드 재현 정보 (참고)

이 exe를 다시 만들고 싶다면 (사외 환경에서):

```bash
git clone https://github.com/anomalyco/opencode.git
cd opencode
ELECTRON_SKIP_BINARY_DOWNLOAD=1 bun install
cd packages/opencode
bun run build --skip-embed-web-ui --skip-install --single
# → packages/opencode/dist/opencode-windows-x64/bin/opencode.exe
```

폐쇄망 빌드 우회 옵션:
- `ELECTRON_SKIP_BINARY_DOWNLOAD=1` — electron 바이너리 다운로드 차단 우회
- `--skip-embed-web-ui` — 웹 UI 임베드 생략 (ghostty-web github 의존성 회피)
- `--skip-install` — 빌드 중 추가 `bun install` 호출 생략 (workspace ghostty-web 의존성 회피)
- `--single` — 현재 플랫폼 단일 타깃만 빌드
