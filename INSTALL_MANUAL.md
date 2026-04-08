# OFFCODE 사내 설치 매뉴얼

> OpenCode + OmO(oh-my-openagent) + 로컬 vLLM 환경 설치 가이드
> 대상 환경: Windows 11 (사내 PC)

---

## 1. 사전 요구사항

| 항목 | 최소 버전 | 확인 명령 |
|------|-----------|-----------|
| Node.js | v18+ | `node --version` |
| npm | v9+ | `npm --version` |
| Bun (선택) | v1.3+ | `bun --version` |
| vLLM 서버 접근 | - | `curl http://<vllm-host>:8000/v1/models` |

### 사내 프록시 설정 (필수)

npm이 사내망에서 외부 레지스트리에 접근할 수 있도록 프록시를 설정한다.

```bash
npm config set proxy http://168.219.61.252:8080
npm config set https-proxy http://168.219.61.252:8080
```

Node.js가 설치되어 있지 않다면 사내 소프트웨어 배포 시스템 또는 공유 폴더에서 설치 파일을 받는다.

---

## 2. OpenCode 설치

```bash
npm install -g opencode-ai
```

설치 확인:

```bash
opencode --version
```

> OpenCode는 `~/.cache/opencode/packages/`에 자체 패키지를 관리한다.
> 이 경로는 OpenCode 내부 동작용이므로 직접 수정하지 않는다.

---

## 3. OmO (oh-my-openagent) 플러그인 설치

이 섹션이 가장 중요하다. 사내망 환경에서는 반드시 아래 순서를 따른다.

### 3-1. 패키지 설치

```bash
cd ~/.config/opencode
npm install oh-my-openagent@3.15.3
```

> **패키지명 주의**: `oh-my-openagent`가 정확한 이름이다.
> `oh-my-openacode`, `oh-my-opencode` 등은 모두 오타이므로 주의한다.

### 3-2. 플러그인 경로 지정 (반드시 file:// 방식)

`opencode.json`에서 플러그인을 반드시 `file://` 로컬 경로로 지정해야 한다.

```json
"plugin": ["file://C:/Users/<username>/.config/opencode/node_modules/oh-my-openagent"]
```

**`<username>`을 본인의 Windows 사용자명으로 교체한다.**

### 왜 file:// 방식인가?

- OpenCode는 npm 레지스트리에서 플러그인을 직접 다운로드하는 방식도 지원하지만, 사내 프록시 환경에서는 이 방식이 실패한다.
- OpenCode는 자체 패키지 관리 경로(`~/.cache/opencode/packages/`)를 사용하므로, `node_modules`에 직접 설치해도 자동으로 찾지 못한다.
- **결론: 반드시 `file://` 절대 경로로 직접 지정한다.**

---

## 4. opencode.json 전체 템플릿

파일 경로: `~/.config/opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "file://C:/Users/<username>/.config/opencode/node_modules/oh-my-openagent"
  ],
  "provider": {
    "localvllm": {
      "name": "Local vLLM",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://<vllm-host>:8000/v1",
        "apiKey": "offspace1"
      },
      "models": {
        "<model-name>": {
          "name": "<model-name>",
          "limit": {
            "context": 131072,
            "tool_call": true,
            "output": 4096
          }
        }
      }
    }
  },
  "model": "localvllm/<model-name>"
}
```

**반드시 수정해야 하는 값:**
- `<username>` → Windows 사용자명 (예: `dongho.yoon`)
- `<vllm-host>` → vLLM 서버의 IP (예: `10.88.22.29`)
- `<model-name>` → vLLM에서 서빙 중인 모델명 (예: `Qwen3.5-35B-A3B`)
- `apiKey` → vLLM 서버에 설정된 API 키 (없으면 아무 값이나 넣어도 됨)

> vLLM 서버에서 사용 가능한 모델 확인:
> ```bash
> curl http://<vllm-host>:8000/v1/models
> ```

---

## 5. oh-my-openagent.jsonc 전체 템플릿

파일 경로: `~/.config/opencode/oh-my-openagent.jsonc`

아래에서 `localvllm/<model-name>`을 opencode.json의 model과 동일하게 맞춘다.

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/dev/assets/oh-my-opencode.schema.json",
  "agents": {
    "sisyphus": { "model": "localvllm/<model-name>", "description": "Main orchestrator" },
    "hephaestus": { "model": "localvllm/<model-name>", "description": "Auto worker" },
    "oracle": { "model": "localvllm/<model-name>", "description": "Read-only consultant" },
    "librarian": { "model": "localvllm/<model-name>", "description": "Reference search" },
    "explore": { "model": "localvllm/<model-name>", "description": "Contextual grep" },
    "multimodal-looker": { "model": "localvllm/<model-name>", "description": "Vision analysis" },
    "prometheus": { "model": "localvllm/<model-name>", "description": "Strategic planner" },
    "metis": { "model": "localvllm/<model-name>", "description": "Pre-planning consultant" },
    "momus": { "model": "localvllm/<model-name>", "description": "Plan reviewer" },
    "atlas": { "model": "localvllm/<model-name>", "description": "Task orchestrator" },
    "sisyphus-junior": { "model": "localvllm/<model-name>" }
  },
  "categories": {
    "visual-engineering": { "model": "localvllm/<model-name>", "description": "Frontend/UX" },
    "ultrabrain": { "model": "localvllm/<model-name>", "description": "Complex logic" },
    "deep": { "model": "localvllm/<model-name>", "description": "Deep problem solving" },
    "artistry": { "model": "localvllm/<model-name>", "description": "Creative/complex" },
    "quick": { "model": "localvllm/<model-name>", "description": "Quick fixes" },
    "unspecified-low": { "model": "localvllm/<model-name>", "description": "Low-priority" },
    "unspecified-high": { "model": "localvllm/<model-name>", "description": "High-priority" },
    "writing": { "model": "localvllm/<model-name>", "description": "Documentation" }
  }
}
```

> **`<model-name>`을 전부 동일한 모델명으로 교체한다** (예: `Qwen3.5-35B-A3B`).
> 모델이 여러 개 있으면 에이전트별로 다른 모델을 지정할 수 있다 (예: quick은 경량 모델).

---

## 6. 주의사항 정리

### 경로 관련

| 항목 | 경로 |
|------|------|
| OpenCode 설정 | `~/.config/opencode/` (APPDATA 아님!) |
| opencode.json | `~/.config/opencode/opencode.json` |
| oh-my-openagent.jsonc | `~/.config/opencode/oh-my-openagent.jsonc` |
| OpenCode 로그 | `~/.local/share/opencode/log/` |
| OmO 로그 | `%TEMP%/oh-my-opencode.log` |
| OpenCode 자체 패키지 | `~/.cache/opencode/packages/` (수정 금지) |

> Windows에서 `~`는 `C:\Users\<username>`을 의미한다.

### 자주 하는 실수

1. **패키지명 오타**: `oh-my-openagent`가 맞다. `oh-my-openacode`가 아니다.
2. **npm 레지스트리 방식 사용**: 사내 프록시 문제로 실패한다. 반드시 `file://` 방식을 사용한다.
3. **APPDATA 경로에 설정 파일 생성**: OpenCode는 `~/.config/opencode/`를 사용한다. `%APPDATA%`가 아니다.
4. **모델명 불일치**: `opencode.json`과 `oh-my-openagent.jsonc`의 모델명이 다르면 에이전트가 동작하지 않는다.
5. **vLLM 엔드포인트 미확인**: 설정 전에 반드시 `curl`로 vLLM 서버 응답을 확인한다.

---

## 7. 설치 검증

### 7-1. 설정 확인

```bash
opencode debug config
```

출력에서 확인할 항목:
- `provider.localvllm` 항목이 존재하는지
- `plugin` 경로가 올바른지
- **`agents` 항목이 비어있지 않은지** (비어있으면 OmO 플러그인 로드 실패)

### 7-2. 모델 확인

```bash
opencode models --refresh
```

출력에서 `localvllm` 프로바이더 아래에 모델이 표시되어야 한다.
모델이 안 보이면 vLLM 서버 연결을 다시 확인한다.

### 7-3. 에이전트 확인

OpenCode를 실행한 뒤 에이전트 탭(또는 에이전트 목록)에서 **Sisyphus**가 표시되는지 확인한다.

```bash
opencode
```

Sisyphus가 보이면 OmO 플러그인이 정상 로드된 것이다.

---

## 8. 문제 해결 가이드

### Sisyphus(시지푸스)가 안 보일 때 체크리스트

아래 항목을 순서대로 확인한다.

#### 1단계: 플러그인 파일 존재 확인

```bash
ls ~/.config/opencode/node_modules/oh-my-openagent/dist/index.js
```

파일이 없으면 3번 섹션(OmO 설치)을 다시 수행한다.

#### 2단계: opencode.json 플러그인 경로 확인

```bash
cat ~/.config/opencode/opencode.json
```

`plugin` 배열에 `file://` 경로가 정확한지 확인한다.
- 슬래시 방향: Windows에서도 `/` (포워드 슬래시) 사용
- 사용자명 정확한지 확인
- `node_modules/oh-my-openagent` 경로가 정확한지 확인

#### 3단계: oh-my-openagent.jsonc 문법 확인

JSONC 파일에 문법 오류가 있으면 전체 플러그인 로드가 실패한다.

```bash
# 파일이 존재하는지 확인
cat ~/.config/opencode/oh-my-openagent.jsonc
```

- 쉼표가 빠지거나 중복되지 않았는지
- 주석(`//`)이 올바르게 사용되었는지
- 중괄호/대괄호 짝이 맞는지

#### 4단계: OmO 로그 확인

```bash
cat $TEMP/oh-my-opencode.log
```

또는 Windows 파일 탐색기에서 `%TEMP%\oh-my-opencode.log`를 열어본다.
로드 실패 시 에러 메시지가 기록된다.

#### 5단계: OpenCode 로그 확인

```bash
ls ~/.local/share/opencode/log/
cat ~/.local/share/opencode/log/<최신 로그 파일>
```

플러그인 로드 관련 에러가 기록되어 있는지 확인한다.

#### 6단계: 버전 호환성 확인

```bash
# OpenCode 버전
opencode --version

# OmO 패키지 버전
cat ~/.config/opencode/node_modules/oh-my-openagent/package.json | grep version
```

OmO 3.15.3은 특정 OpenCode 버전과 호환된다. 버전이 크게 다르면 호환성 문제일 수 있다.

#### 7단계: 캐시 초기화 후 재시도

```bash
# OpenCode 캐시 삭제
rm -rf ~/.cache/opencode/packages/

# OmO 재설치
cd ~/.config/opencode
rm -rf node_modules
npm install oh-my-openagent@3.15.3

# OpenCode 재시작
opencode
```

### vLLM 모델이 안 보일 때

```bash
# 1. vLLM 서버 접근 확인
curl http://<vllm-host>:8000/v1/models

# 2. 프록시가 내부 통신을 가로채는지 확인
# vLLM이 사내 서버라면 no_proxy에 추가
set NO_PROXY=<vllm-host>
# 또는 bash 환경:
export no_proxy=<vllm-host>

# 3. opencode.json의 url이 정확한지 확인
# /v1 까지 포함해야 함: http://<vllm-host>:8000/v1
```

### 에이전트는 보이지만 응답이 안 올 때

```bash
# 1. 모델이 실제로 로드되어 있는지 확인
curl http://<vllm-host>:8000/v1/models

# 2. 직접 API 호출 테스트
curl http://<vllm-host>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3.5-32B", "messages": [{"role": "user", "content": "hello"}]}'

# 3. oh-my-openagent.jsonc의 모델명이 vLLM 모델명과 일치하는지 확인
```

---

## 9. 빠른 설치 요약 (체크리스트)

```
[ ] 1. Node.js, npm 설치 확인
[ ] 2. npm 프록시 설정 (http://168.219.61.252:8080)
[ ] 3. npm install -g opencode-ai
[ ] 4. cd ~/.config/opencode && npm install oh-my-openagent@3.15.3
[ ] 5. opencode.json 작성 (provider + model + plugin file:// 경로)
[ ] 6. oh-my-openagent.jsonc 작성 (agents + category_model_overrides)
[ ] 7. opencode debug config → agents 비어있지 않은지 확인
[ ] 8. opencode models --refresh → localvllm 모델 표시 확인
[ ] 9. opencode 실행 → 에이전트 탭에서 Sisyphus 확인
```

---

*문서 작성일: 2026-04-07*
*프로젝트: OFFCODE (오프코드)*
*대상 환경: Windows 11 사내 PC*
