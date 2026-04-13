# 사내망에서 opencode 설치하기

> **목표**: 인터넷이 막힌 사내망(블랙웰 서버 등)에 `opencode` CLI를 올린다.
> **전략**: VDI/노트북에서 빌드 → 산출물을 사내망으로 옮긴다 (오프라인 이식).

---

## 전체 흐름

```
[VDI/노트북 - 인터넷 O]              [사내망 - 인터넷 X]
  1. opencode-dev 클론         →
  2. bun install                       (산출물 이식)         3. 압축 해제
  3. bun run build              ───────────────▶            4. PATH 등록
  4. dist/ 압축                                              5. 실행 확인
```

빌드 단계는 인터넷이 필요하니까 **무조건 사외에서**.
사내망은 **받아서 풀기만** 한다.

---

## 옵션 A: 단일 바이너리 이식 (권장)

가장 깔끔. `opencode.exe` 하나 + 동봉 자산만 옮기면 끝.

### 1단계 — VDI에서 빌드

```bash
cd opencode-dev
bun install
cd packages/opencode
bun run build
# 결과물: packages/opencode/dist/  (opencode.exe + 임베드된 web UI)
```

빌드 스크립트(`packages/opencode/script/build.ts`)가 하는 일:
- `https://models.dev/api.json` 받아서 `models-snapshot.js` 생성
- `migration/` SQL 임베드
- `packages/app` 웹 UI 빌드 후 바이너리에 임베드
- Bun으로 단일 실행파일 컴파일

폐쇄망 빌드 우회:
```bash
# models.dev fetch 막힐 때 — 미리 받아둔 JSON 사용
MODELS_DEV_API_JSON=/path/to/api.json bun run build

# 웹 UI 임베드 건너뛰기 (TUI만 쓸 거면)
bun run build -- --skip-embed-web-ui
```

### 2단계 — 압축

```bash
cd packages/opencode
tar czf opencode-windows-x64.tar.gz dist/
# 또는 7z a opencode-windows-x64.7z dist/
```

### 3단계 — 사내망으로 이송

USB / 사내 파일서버 / gist (작은 텍스트 산출물 한정) — 회사 정책 따라.

### 4단계 — 사내망 설치

```bash
# 1. 압축 해제
mkdir -p ~/tools/opencode
tar xzf opencode-windows-x64.tar.gz -C ~/tools/opencode

# 2. PATH 등록 (Windows PowerShell, 영구)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\$env:USERNAME\tools\opencode\dist", "User")

# 또는 bash (.bashrc)
echo 'export PATH="$HOME/tools/opencode/dist:$PATH"' >> ~/.bashrc

# 3. 확인
opencode --version
```

---

## 옵션 B: 소스+node_modules 통째 이식

빌드 안 하고 `bun dev`로 굴리고 싶을 때. 무겁지만 디버깅엔 유리.

### VDI에서

```bash
cd opencode-dev
bun install
# node_modules 까지 통째로 압축
cd ..
tar czf opencode-dev-full.tar.gz opencode-dev/
```

### 사내망에서

```bash
tar xzf opencode-dev-full.tar.gz
cd opencode-dev
bun dev   # bun이 사내망에 설치되어 있어야 함 → install_bun.md 참고
```

⚠️ 사내망에 **bun이 깔려 있어야** 한다. 옵션 A는 단일 바이너리라 bun 불필요.

---

## 체크리스트

- [ ] VDI에서 `bun install` 성공
- [ ] `bun run build` 성공, `dist/opencode.exe` 생성 확인
- [ ] 압축 → 이송 → 사내망 압축 해제
- [ ] PATH 등록
- [ ] `opencode --version` 동작
- [ ] `opencode` 실행 시 TUI 진입 확인

---

## 관련 문서

- [bun 설치 (사내망)](./install_bun.md) — 옵션 B를 쓸 때만 필요
- 상위 프로젝트: `../docs/CONSTRAINTS.md` — 블랙웰 서버 제약사항
