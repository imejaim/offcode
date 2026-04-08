# OFFCODE Phase 1 — 작업 계획서

> "이 문서 보고 시작하자" 하면 바로 실행 가능하도록 작성됨.
> 최종 산출물: 사내 로컬 LLM에서 시지푸스가 보이는 OFFCODE 환경 + 오드리(Dr. Oh) 환경검사 에이전트

---

## 배경: 시지푸스가 안 보이는 이유 (코드 분석 결과)

**원인: 모델 요구사항 미충족**

```
oh-my-openagent-dev/src/agents/builtin-agents/sisyphus-agent.ts (line 52):

if (disabledAgents.includes("sisyphus") || !meetsSisyphusAnyModelRequirement)
    return undefined  // ← 시지푸스 생성 자체가 안 됨
```

시지푸스의 폴백 체인 (`src/shared/model-requirements.ts`):
```
claude-opus-4-6 → kimi-k2.5 → gpt-5.4 → glm-5 → big-pickle
```

사내 vLLM에서 서빙하는 모델(Qwen3.5, Gemma4)은 이 체인에 **하나도 없음**.
→ `meetsSisyphusAnyModelRequirement = false` → 시지푸스 생성 안 됨 → 에이전트 목록에서 사라짐.

**해결 방향:**
1. OpenCode에 로컬 LLM 프로바이더 등록 (`opencode.json`)
2. OmO 설정에서 시지푸스 모델을 로컬 모델로 오버라이드 (`oh-my-opencode.jsonc`)

---
0. 사내 리눅스
이건 리눅스
전역설정 opencode.json 은 사용자 루트에 .config/opencode 경로에 있고, 같은 경로에 oh-my-openagent.jsonc 파일이 있음. 
혹시 몰라서 oh-my-opencode.json 파일도 같은 내용으로 같은 경로에 있음. 
또 .config/opencode/.opencode 라는 경로도 있는데 여기에 oh-my-opencode.jsonc 가 있음. 안에 내용은 같음. 

1. 사내 윈도우 환경에서의 상황 
프로젝트를 열었고, 터미널에서 opencode 라고 명령을 치면 전역설정에 따라 opencode 가 열림. 하지만 시지푸스는 안보임
vllm 을 리눅스 pc 에서 서빙하고 있고 연결이 된 상태여서 opencode 자체 만으로도 응답이 있음. 

윈도우에서는 

(base) PS C:\Users\dongho.yoon\AppData\Roaming\npm> ls


    디렉터리: C:\Users\dongho.yoon\AppData\Roaming\npm


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----      2026-04-06   오후 2:10                node_modules
-a----      2026-04-06   오후 2:10            417 opencode
-a----      2026-04-06   오후 2:10            339 opencode.cmd
-a----      2026-04-06   오후 2:10            861 opencode.ps1


(base) PS C:\Users\dongho.yoon\AppData\Roaming\npm> ls -al
Get-ChildItem : 매개 변수 이름 'al'과(와) 일치하는 매개 변수를 찾을 수 없습니다.



(base) PS C:\Users\dongho.yoon> cd .\.config\
(base) PS C:\Users\dongho.yoon\.config> ls


    디렉터리: C:\Users\dongho.yoon\.config


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----      2026-04-06   오후 3:25                opencode


(base) PS C:\Users\dongho.yoon\.config> cd .\opencode\
(base) PS C:\Users\dongho.yoon\.config\opencode> ls


    디렉터리: C:\Users\dongho.yoon\.config\opencode


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----      2026-03-12   오후 5:27                node_modules
d-----      2026-03-12   오후 5:27                sills
d-----      2026-03-12   오후 5:27                skills
-a----      2026-03-12   오후 5:27             45 .gitignore
-a----      2026-03-12   오후 5:27            756 bun.lock
-a----      2026-03-12   오후 5:27            428 mcp-settings.global
-a----      2026-04-07  오후 12:56           2285 oh-my-openagent.json
-a----      2026-04-07  오후 12:56           2511 oh-my-openagent.jsonc
-a----      2026-04-06   오후 3:24           2215 oh-my-opencode.json
-a----      2026-04-06   오후 2:57           2215 oh-my-opencode.jsonc
-a----      2026-04-07   오후 3:26            584 opencode.json
-a----      2026-04-06   오후 2:53            554 opencode.json.backup
-a----      2026-04-07   오후 3:31             63 package.json


(base) PS C:\Users\dongho.yoon\.config\opencode>



{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "oh-my-openagent@3.15.3"
  ],
  "provider": {
    "localvllm": {
      "name": "Local vLLM",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://127.0.0.1:8000/v1",
        "apiKey": "offspace1"
      },
      "models": {
        "Qwen3.5-35B-A3B": {
          "name": "Qwen3.5-35B-A3B",
          "limit": {
            "context": 131072,
            "tool_call": true,
            "output": 4096
          }
        }
      }
    }
  },
  "model": "localvllm/Qwen3.5-35B-A3B",
  "mcp": {
    "ssh-mcp": {
      "type": "local",
      "command": [
        "npx",
        "--yes",
        "ssh-mcp@latest",
        "-y",
        "--",
        "--host=168.219.244.198",
        "--port=22",
        "--user=spdmhpc7",
        "--key=/home/dongho.yoon/.ssh/id_rsa_spdm",
        "--timeout=30000"
      ],
      "enabled": true,
      "timeout": 30000
    }
  }
}




{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/dev/assets/oh-my-opencode.schema.json",
  "agents": {
    "sisyphus": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Main orchestrator" },
    "hephaestus": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Auto worker" },
    "oracle": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Read-only consultant" },
    "librarian": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Reference search" },
    "explore": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Contextual grep" },
    "multimodal-looker": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Vision analysis" },
    "metis": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Pre-planning consultant" },
    "momus": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Plan reviewer" },
    "atlas": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Task orchestrator" },
    "prometheus": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Strategic planner" }
  },
  "categories": {
    "visual-engineering": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Frontend/UX" },
    "ultrabrain": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Complex logic" },
    "deep": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Deep problem solving" },
    "artistry": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Creative/complex" },
    "quick": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Quick fixes" },
    "unspecified-low": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Low-priority" },
    "unspecified-high": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "High-priority" },
    "writing": { "model": "localvllm/Qwen3.5-35B-A3B", "description": "Documentation" }
  },
  "skills": {
    "sources": [{ "path": "~/.config/opencode/skills", "recursive": true }],
    "my-ssh-master": {
      "description": "Remote SSH command execution and file transfer via MCP",
      "template": "Execute remote commands on SPDM server using ssh-mcp integration.",
      "from": "~/.config/opencode/skills/ssh-master/SKILL.md",
      "mcp": "ssh-mcp"
    }
  }
}




---
## Work Items

### W1. 로컬 LLM 프로바이더 연결 확인
> 선행 조건: vLLM 서버 가동 중

**할 일:**
- [ ] vLLM 엔드포인트 접근 테스트
  ```bash
  curl http://<VLLM_HOST>:8000/v1/models
  curl http://<VLLM_HOST>:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"Qwen/Qwen3.5-32B","messages":[{"role":"user","content":"hello"}]}'
  ```
- [ ] 응답 정상 여부 확인 (모델 ID, 토큰 생성)
- [ ] 네트워크 지연시간 확인 (터미널 → vLLM)

**참고 코드:**
- `opencode-dev/packages/opencode/src/provider/provider.ts` (line 127~150): `@ai-sdk/openai-compatible` 프로바이더
- `opencode-dev/packages/opencode/src/config/config.ts` (line 788~847): 프로바이더 스키마

---

### W2. OpenCode 프로바이더 설정
> W1 완료 후

**할 일:**
- [ ] `opencode.json` (또는 `opencode.jsonc`)에 로컬 프로바이더 등록:
  ```jsonc
  {
    "provider": {
      "vllm": {
        "id": "vllm",
        "name": "사내 vLLM",
        "npm": "@ai-sdk/openai-compatible",
        "models": {
          "qwen3.5-32b": {
            "id": "Qwen/Qwen3.5-32B",
            "name": "Qwen 3.5 32B",
            "limit": { "context": 32768, "output": 8192 }
          },
          "gemma4-27b": {
            "id": "google/gemma-4-27b",
            "name": "Gemma 4 27B",
            "limit": { "context": 32768, "output": 8192 }
          }
        },
        "options": {
          "baseURL": "http://<VLLM_HOST>:8000/v1",
          "apiKey": "not-needed"
        }
      }
    },
    "model": "vllm/qwen3.5-32b"
  }
  ```
- [ ] OpenCode 실행 후 모델 목록에 vllm 모델 표시 확인
- [ ] 기본 대화 테스트 (모델 응답 확인)

**참고 코드:**
- `opencode-dev/packages/opencode/src/provider/models.ts`: 모델 해석 로직
- `opencode-dev/packages/opencode/src/plugin/loader.ts`: 플러그인 로딩 순서

---

### W3. OmO 플러그인 로딩 확인
> W2 완료 후 (또는 병렬)

**할 일:**
- [ ] `opencode.json`의 `plugin` 항목에 OmO 등록 확인:
  ```jsonc
  {
    "plugin": ["oh-my-opencode"]
    // 또는 로컬 빌드: ["file:///path/to/oh-my-opencode/dist/index.js"]
  }
  ```
- [ ] OpenCode 시작 시 OmO 플러그인 로드 로그 확인
- [ ] 로그 파일 확인: `/tmp/oh-my-opencode.log` (Linux) 또는 Windows 동등 경로
- [ ] `bunx oh-my-opencode doctor` 실행하여 진단

**참고 코드:**
- `opencode-dev/packages/opencode/src/plugin/index.ts` (line 152~193): 외부 플러그인 로딩
- `oh-my-openagent-dev/src/index.ts`: OmO 플러그인 진입점
- `oh-my-openagent-dev/src/cli/doctor/`: 닥터 진단 체크

---

### W4. 시지푸스 모델 오버라이드 설정
> W2 + W3 완료 후. **핵심 작업.**

**할 일:**
- [ ] OmO 설정 파일 생성/수정:
  ```
  프로젝트: .opencode/oh-my-opencode.jsonc
  글로벌:   ~/.config/opencode/oh-my-opencode.jsonc
  ```
- [ ] 시지푸스 모델을 로컬 모델로 오버라이드:
  ```jsonc
  {
    // 에이전트별 모델 오버라이드
    "agents": {
      "sisyphus": {
        "model": "vllm/qwen3.5-32b"
      },
      "hephaestus": {
        "model": "vllm/qwen3.5-32b"
      },
      "prometheus": {
        "model": "vllm/qwen3.5-32b"
      }
    },
    // 카테고리별 모델 매핑
    "categories": {
      "deep": {
        "model": "vllm/qwen3.5-32b"
      },
      "quick": {
        "model": "vllm/gemma4-27b"
      },
      "ultrabrain": {
        "model": "vllm/qwen3.5-32b"
      }
    }
  }
  ```
- [ ] OpenCode 재시작
- [ ] **에이전트 목록에 시지푸스 표시 확인** ← 핵심 마일스톤
- [ ] 시지푸스로 간단한 작업 수행 테스트

**참고 코드:**
- `oh-my-openagent-dev/src/agents/builtin-agents/sisyphus-agent.ts` (line 43~66): 모델 해석 로직
- `oh-my-openagent-dev/src/agents/builtin-agents/model-resolution.ts`: 모델 가용성 체크
- `oh-my-openagent-dev/src/shared/model-requirements.ts` (line 21~46): 폴백 체인 정의
- `oh-my-openagent-dev/src/plugin-handlers/agent-config-handler.ts` (line 149~157): 에이전트 등록 조건

---

### W5. 전체 에이전트 동작 검증
> W4 완료 후

**할 일:**
- [ ] 에이전트 목록 전체 확인 (시지푸스, 헤파이스토스, 프로메테우스, 아틀라스 등)
- [ ] 각 에이전트로 간단한 작업 수행
- [ ] 서브에이전트 위임 동작 확인 (시지푸스 → 다른 에이전트)
- [ ] MCP 도구 연결 확인 (파일시스템, 웹검색 등)
- [ ] 훅 동작 확인 (OmO 로그에서 확인)
- [ ] 문제 발생 시 로그 분석 및 설정 조정

---

### W6. 오드리(Dr. Oh) 환경검사 에이전트 설계
> W1~W5의 경험을 바탕으로

위 W1~W5에서 수동으로 했던 모든 체크를 자동화하는 에이전트.

**오드리 체크리스트 (자동화 대상):**

#### A. 인프라 체크
| # | 체크 항목 | 검증 방법 | 통과 기준 |
|---|---|---|---|
| A1 | vLLM 엔드포인트 접근 | `GET /v1/models` | HTTP 200 + 모델 목록 반환 |
| A2 | 모델 응답 테스트 | `POST /v1/chat/completions` | 정상 토큰 생성 |
| A3 | 네트워크 지연 | 응답 시간 측정 | < 5초 (첫 토큰) |
| A4 | GPU 상태 | `nvidia-smi` (서버 접근 가능 시) | GPU 메모리 사용률 확인 |

#### B. OpenCode 체크
| # | 체크 항목 | 검증 방법 | 통과 기준 |
|---|---|---|---|
| B1 | Node.js/Bun 설치 | `bun --version` / `node --version` | Bun 1.3+ |
| B2 | OpenCode 설치 | `opencode --version` | 정상 버전 출력 |
| B3 | opencode.json 존재 | 파일 존재 체크 | 파일 있음 |
| B4 | 프로바이더 설정 | opencode.json 파싱 | vllm 프로바이더 등록됨 |
| B5 | 모델 설정 | opencode.json 파싱 | model 필드에 vllm/* 설정됨 |
| B6 | 모델 목록 조회 | OpenCode API 또는 설정 파싱 | 로컬 모델 목록 표시 |

#### C. OmO 체크
| # | 체크 항목 | 검증 방법 | 통과 기준 |
|---|---|---|---|
| C1 | OmO 플러그인 등록 | opencode.json plugin 배열 확인 | oh-my-opencode 포함 |
| C2 | OmO 설정 파일 | oh-my-opencode.jsonc 존재 | 파일 있음 |
| C3 | 에이전트 모델 오버라이드 | 설정 파싱 | sisyphus에 vllm 모델 지정됨 |
| C4 | disabled_agents 확인 | 설정 파싱 | sisyphus가 비활성화 안 됨 |
| C5 | OmO 로그 확인 | /tmp/oh-my-opencode.log | 에러 없음 |
| C6 | 닥터 진단 | `bunx oh-my-opencode doctor` | 전체 통과 |

#### D. 에이전트 체크
| # | 체크 항목 | 검증 방법 | 통과 기준 |
|---|---|---|---|
| D1 | 시지푸스 표시 | 에이전트 목록 조회 | sisyphus 존재 |
| D2 | 시지푸스 응답 | 간단한 프롬프트 테스트 | 정상 응답 |
| D3 | 서브에이전트 위임 | 멀티태스크 테스트 | 위임 동작 확인 |
| D4 | MCP 도구 | 도구 목록 조회 | 기본 도구 사용 가능 |

---

### W7. 오드리(Dr. Oh) 구현
> W6 설계 완료 후

**구현 계획:**

```
audrey/
├── doctor_oh_check.py        # 메인 체크 스크립트 (Python 3.9+, stdlib only)
├── checks/
│   ├── infra.py              # A1~A4: 인프라 체크
│   ├── opencode.py           # B1~B6: OpenCode 체크
│   ├── omo.py                # C1~C6: OmO 체크
│   └── agent.py              # D1~D4: 에이전트 체크
├── audrey_ascii.txt          # 오드리 ASCII 아트
├── audrey_prompt.md          # 오드리 에이전트 프롬프트 (하네스용)
├── config.json               # 체크 대상 설정 (vLLM URL, 경로 등)
└── README.md                 # 사용법
```

**실행 방식:**
```bash
# 전체 체크
python doctor_oh_check.py --json

# 특정 카테고리만
python doctor_oh_check.py --category infra
python doctor_oh_check.py --category opencode
python doctor_oh_check.py --category omo
python doctor_oh_check.py --category agent

# 자동 수정 시도
python doctor_oh_check.py --auto-fix
```

**출력 예시:**
```
╔══════════════════════════════════════════╗
║  오드리 (Dr. Oh) - OFFCODE 환경 검사     ║
╚══════════════════════════════════════════╝

[인프라]
  ✅ A1. vLLM 엔드포인트 접근        OK (http://10.0.0.1:8000)
  ✅ A2. 모델 응답 테스트             OK (Qwen3.5-32B, 1.2s)
  ✅ A3. 네트워크 지연                OK (320ms)
  ⚠️  A4. GPU 상태                   SKIP (서버 접근 불가)

[OpenCode]
  ✅ B1. Bun 설치                    OK (1.3.11)
  ✅ B2. OpenCode 설치               OK (1.3.17)
  ✅ B3. opencode.json               OK
  ❌ B4. 프로바이더 설정              FAIL - vllm 프로바이더 미등록
  ❌ B5. 모델 설정                   FAIL - model 필드 미설정

[OmO]
  ✅ C1. 플러그인 등록               OK
  ❌ C2. OmO 설정 파일               FAIL - oh-my-opencode.jsonc 없음
  ...

결과: 12/16 통과 | 3 실패 | 1 스킵
자동 수정 가능: B4, B5, C2 → --auto-fix 로 수정하시겠습니까?
```

**auto-fix 기능 (구현할 것):**
| 체크 | 자동 수정 내용 |
|---|---|
| B4 | opencode.json에 vllm 프로바이더 추가 |
| B5 | opencode.json에 model 필드 설정 |
| C2 | oh-my-opencode.jsonc 템플릿 생성 |
| C3 | 시지푸스 모델 오버라이드 추가 |
| C4 | disabled_agents에서 sisyphus 제거 |

---

### W8. 오드리 테스트 및 배포 패키지화
> W7 완료 후

**할 일:**
- [ ] 리눅스 환경에서 오드리 전체 체크 실행 + auto-fix 테스트
- [ ] 윈도우 환경에서 오드리 전체 체크 실행 + auto-fix 테스트
- [ ] 오드리를 OFFCODE 배포 패키지에 포함
- [ ] 오드리 하네스 프롬프트 작성 (OpenCode 안에서 `/audrey` 로 실행 가능하도록)

---

## 실행 순서 요약

```
W1. vLLM 연결 확인 ─────────────────────────────┐
                                                  │
W2. OpenCode 프로바이더 설정 ──┐                   │ 병렬 가능
                               ├── W4. 시지푸스    │
W3. OmO 플러그인 로딩 확인 ───┘     모델 오버라이드 │
                                        │         │
                                  W5. 전체 검증    │
                                        │         │
                                  W6. 오드리 설계 ←┘ (W1~W5 경험이 체크리스트가 됨)
                                        │
                                  W7. 오드리 구현
                                        │
                                  W8. 오드리 테스트 + 배포
```

**예상 소요:** W1~W5 (환경 구축) 1세션, W6~W8 (오드리) 1~2세션

---

## 다음 세션에서 "시작하자" 하면

1. 이 문서를 읽는다
2. W1부터 순서대로 실행한다
3. 각 단계에서 체크박스를 채워간다
4. W5까지 완료되면 시지푸스가 보인다
5. W6~W8로 오드리를 만든다

---

## 참조 파일 (코드 분석 결과)

### 시지푸스가 안 보이는 코드 경로
```
oh-my-openagent-dev/src/agents/builtin-agents/sisyphus-agent.ts
  line 43-50: meetsSisyphusAnyModelRequirement 체크
  line 52:    모델 없으면 return undefined
  line 54-66: applyModelResolution → 모델 해석

oh-my-openagent-dev/src/shared/model-requirements.ts
  line 21-46: 시지푸스 폴백 체인 (claude-opus → kimi → gpt → glm)

oh-my-openagent-dev/src/plugin-handlers/agent-config-handler.ts
  line 149: isSisyphusEnabled 체크
  line 157: 에이전트를 config에 등록하는 조건
```

### OpenCode 프로바이더 등록
```
opencode-dev/packages/opencode/src/provider/provider.ts
  line 127-150: @ai-sdk/openai-compatible 번들 프로바이더

opencode-dev/packages/opencode/src/config/config.ts
  line 788-847: Provider 스키마 (options.baseURL)
  line 849-960: opencode.json 전체 스키마
```

### OmO 플러그인 로딩
```
opencode-dev/packages/opencode/src/plugin/index.ts
  line 152-193: 외부 플러그인 로딩

opencode-dev/packages/plugin/src/index.ts
  Plugin 인터페이스 (config hook으로 에이전트 주입)
```

---

*작성일: 2026-04-07*
*프로젝트: OFFCODE Phase 1*
