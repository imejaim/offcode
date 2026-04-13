# 윈도우 데스크탑 시지푸스 — 수정 라운드 1

회장님, 진단 결과 깨끗합니다. **원인 1개**만 잡으면 됩니다.

## 진단 요약

| # | 항목 | 상태 |
|---|---|---|
| 1 | 블랙웰 Ollama 원격 접속 (`curl 10.88.22.29:11434`) | ✅ Gemma4 31b/26b/e4b/e2b 확인 |
| 2 | opencode.json `baseURL` | ❌ **`http://localhost:11434/v1`** ← 문제 |
| 3 | 플러그인 (`file://.../node_modules/oh-my-openagent`) | ✅ 에이전트 목록 뜨니 로드 OK |
| 4 | oh-my-openagent.jsonc Gemma4 3티어 배분 | ✅ 완료 |
| 5 | OpenCode 1.3.16 + 시지푸스 표시 | ✅ |
| 6 | "하이" 응답 | ❌ socket closed — baseURL 때문 |

**근본 원인**: `baseURL`이 `localhost:11434`로 돼 있는데 데스크탑에는 로컬 Ollama가 없음. 블랙웰(`10.88.22.29:11434`)로 바꾸면 끝.

---

## 수정 (PowerShell 1블록)

```powershell
# 1. 백업
copy $env:USERPROFILE\.config\opencode\opencode.json $env:USERPROFILE\.config\opencode\opencode.json.bak.localhost

# 2. baseURL 한 줄 치환 (localhost → 10.88.22.29)
(Get-Content $env:USERPROFILE\.config\opencode\opencode.json) `
  -replace 'http://localhost:11434/v1', 'http://10.88.22.29:11434/v1' `
  | Set-Content $env:USERPROFILE\.config\opencode\opencode.json -Encoding UTF8

# 3. 결과 확인
type $env:USERPROFILE\.config\opencode\opencode.json | Select-String baseURL
```

→ `"baseURL": "http://10.88.22.29:11434/v1"` 한 줄 뜨면 성공.

---

## 검증

```powershell
# 4. OpenCode 종료 후 재시작
# (실행 중이면 Ctrl+C로 종료 후)
cd <아무 프로젝트 폴더>
opencode
```

→ TUI 열면 `Tab` 눌러서 **시지푸스** 선택 → `하이, 넌 누구니?` 입력 → 응답 확인.

---

## 회신 부탁드립니다

- **성공**: 시지푸스 응답 전문 + 모델 표시(`▣ Sisyphus · Gemma4 31B · ??s`) 붙여넣기
- **실패**: 에러 메시지 전문 + 해당 시점의 OpenCode 화면

첫 응답은 31B 로드 때문에 30초+ 걸릴 수 있습니다. 급하지 않으면 기다려주시고, 너무 오래면 Ctrl+C 후 에러 회신.

---
*코부장 @ VDI — 2026-04-13*
