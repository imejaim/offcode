# Bun 설치 카드

> opencode는 **Bun 1.3+** 만 지원. npm/yarn 안 됨.
> 사외(인터넷 O)와 사내망(폐쇄망) 절차가 다르다.

---

## 사외 (VDI / 노트북) — 표준 설치

### Windows (PowerShell)

```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

### Linux / macOS

```bash
curl -fsSL https://bun.sh/install | bash
```

### 확인

```bash
bun --version    # 1.3.x 이상이어야 함
```

설치 위치:
- Windows: `%USERPROFILE%\.bun\bin\bun.exe`
- Linux/macOS: `~/.bun/bin/bun`

PATH 자동 추가됨. 안 되면 셸 재시작.

---

## 사내망 (폐쇄망) — 오프라인 설치

### 1단계 — VDI에서 바이너리 받기

GitHub releases에서 직접 다운로드:
```
https://github.com/oven-sh/bun/releases/latest
```

플랫폼별 zip:
- `bun-windows-x64.zip`
- `bun-linux-x64.zip`
- `bun-darwin-x64.zip` / `bun-darwin-aarch64.zip`

```bash
# Linux 예시
wget https://github.com/oven-sh/bun/releases/download/bun-v1.3.x/bun-linux-x64.zip
```

### 2단계 — 사내망으로 이송

USB / 사내 파일서버 등.

### 3단계 — 사내망 설치

```bash
# Linux
unzip bun-linux-x64.zip
mkdir -p ~/.bun/bin
mv bun-linux-x64/bun ~/.bun/bin/
chmod +x ~/.bun/bin/bun
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows (PowerShell)
Expand-Archive bun-windows-x64.zip -DestinationPath $env:USERPROFILE\.bun
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:USERPROFILE\.bun\bun-windows-x64", "User")
```

### 4단계 — 확인

```bash
bun --version
```

---

## ⚠️ 주의

- **블랙웰 서버**는 `wget`만 가능 (`docs/CONSTRAINTS.md` 참고). curl 설치 스크립트 ❌
- bun은 **단일 바이너리**라 의존성 없음. 그냥 실행파일 한 개 PATH에 넣으면 끝
- 단, `bun install`로 패키지 받으려면 npm registry 접근이 필요 → 폐쇄망에서는 의미 없음
- 그래서 사내망에서 bun이 필요한 경우는 **거의 없다**. opencode는 [옵션 A 단일 바이너리](./사내망_opencode_설치.md#옵션-a-단일-바이너리-이식-권장)로 가는 게 정석.

---

## 언제 bun이 사내망에 필요한가

- opencode를 **소스로 굴려야** 할 때 (디버깅, 코드 수정)
- OmO 플러그인을 **사내망에서 빌드**해야 할 때
- 그 외 → 불필요. 단일 바이너리만 옮기자.
