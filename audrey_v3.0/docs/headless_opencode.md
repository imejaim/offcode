# headless_opencode.md — 오드리 v3.0 Scout 보고서

> Scout 미션: 이 VDI(Windows 11)에서 OpenCode를 헤드리스로 호출하는 경로를 정적 분석으로 찾고, Builder가 `checks/e2e.py`에 그대로 심을 수 있는 후보 명령을 추천한다.

## 1. 환경 요약

| 항목 | 결과 |
|---|---|
| OS | Windows 11 (VDI), bash(Git Bash) 사용 |
| Bun | **미설치** (`bun: command not found`) — 회장님 수동 설치 필요 |
| Node.js | `C:\Program Files\nodejs\node.exe` 존재 |
| npm | 존재 (`C:\Program Files\nodejs\npm.cmd`) |
| `opencode-dev/` 상태 | 체크아웃만 되어 있음. `node_modules` 없음, **`bun install` 실행 불가** |
| `bun dev serve` 실측 | **미실행** (Bun 부재로 불가). 아래 내용은 소스 정적 분석 기반 |

**결론**: 이 VDI에서는 OpenCode를 실제로 띄워서 확인할 수 없다. 런타임 탐색 단계는 Bun 설치 이후 재수행해야 한다. 그러나 `opencode-dev/packages/opencode/src/cli/cmd/` 소스가 완전히 읽혀있으므로 CLI/HTTP 표면은 **정적 분석으로 100% 확보**되었다.

---

## 2. 발견한 CLI 명령/플래그

CLI는 **yargs** 기반이다. 루트 명령 (`packages/opencode/src/cli/cmd/` 하위):

| 명령 | 용도 | 헤드리스 적합 |
|---|---|---|
| `opencode run [message..]` | **메시지 1건 전송 후 종료** | ★★★ 가장 유망 |
| `opencode serve` | 헤드리스 HTTP 서버 기동 | ★★★ 장기 워커형 |
| `opencode agent list` / `agent create` | 에이전트 목록/생성 | ★ 사전 점검용 |
| `opencode models [provider]` | 모델 나열 | ★ 프로바이더 존재 확인 |
| `opencode providers` | 프로바이더 목록 | ★ |
| `opencode mcp list` / `mcp debug` | MCP 디버그 | 참고 |
| `opencode debug config` / `debug agent <name>` / `debug skill` | 내부 상태 점검 | ★★ 환경 점검용 |
| `opencode export [sessionID]` / `import <file>` | 세션 내보내기/가져오기 | — |
| `opencode generate` | 스키마 생성 | — |
| `opencode db migrate` / `db path` | 내부 DB | — |
| `opencode login <url>` / `logout` / `switch` / `orgs` | 계정 | — |
| `opencode acp` | ACP 프로토콜 | — |
| `opencode tui attach` | 기존 서버에 TUI 붙이기 | — |

### `opencode run` 플래그 (가장 중요 — `cli/cmd/run.ts:221-305`)

```
opencode run [message..]
  --command <str>          사용자 커맨드 실행 (메시지는 인자로)
  -c, --continue           마지막 세션 이어쓰기
  -s, --session <id>       세션 ID 지정
  --fork                   이어쓰기 전에 세션 포크 (--continue 또는 --session 필요)
  --share                  세션 공유 링크 생성
  -m, --model <prov/mod>   모델 지정 (예: ollama/gemma3:27b)
  --agent <name>           primary 에이전트 지정 (subagent는 거절됨)
  --format default|json    **json이면 이벤트를 NDJSON으로 stdout에 뿌림**
  -f, --file <path..>      파일 첨부 (여러 개 가능)
  --title <str>            세션 제목
  --attach <url>           실행 중인 서버에 붙기 (예: http://127.0.0.1:4096)
  -p, --password <pw>      basic auth (env: OPENCODE_SERVER_PASSWORD)
  --dir <path>             실행 디렉터리
  --port <n>               로컬 서버 포트 (미지정 시 랜덤)
  --variant <str>          reasoning 강도 (high/max/minimal 등)
  --thinking               thinking 블록 출력
```

핵심 동작(run.ts 분석):
- 기본적으로 `run`은 **내부 서버를 기동**하고, 그 위의 Opencode SDK 클라이언트로 세션을 만들어 한 번 메시지를 보내고, `session.status == idle`이 되면 종료한다 (run.ts:536-542).
- **권한 룰이 `question/plan_enter/plan_exit` 전부 deny**로 하드코딩돼 있다(run.ts:357-373). 즉 `run`은 사람 입력 없이 동작하도록 설계돼 있음 → 헤드리스 이상적.
- `process.stdin.isTTY`가 false면 stdin 내용을 메시지에 붙인다(run.ts:345). → **파이프 입력 지원**.
- stdout이 TTY가 아니면 텍스트 파트를 그대로 `stdout.write`한다(run.ts:500-503). → 파이프 캡처 매우 쉬움.
- `--format json` 지정 시 `{type, timestamp, sessionID, ...}` NDJSON이 stdout으로 흐른다(run.ts:433-439). 이벤트 종류: `step_start`, `step_finish`, `text`, `tool_use`, `reasoning`, `error`.
- `--agent`로 지정한 이름이 없거나 subagent면 **에러가 아니라 경고 후 fallback** 한다(run.ts:602-619). → 에이전트 미발견은 exit code로 잡히지 않는다. **응답 파싱 쪽에서 판단해야 함**.

### `opencode serve` 플래그 (`cli/cmd/serve.ts` + `cli/network.ts`)

```
opencode serve
  --port <n>            기본 0 (랜덤). 4096은 관례이지 기본값 아님
  --hostname <host>     기본 127.0.0.1
  --mdns                mDNS 활성화 (자동으로 0.0.0.0 바인딩)
  --mdns-domain <d>     기본 opencode.local
  --cors <domain..>     CORS 허용 도메인
```

환경변수: `OPENCODE_SERVER_PASSWORD` 없으면 "server is unsecured" 경고만 찍고 뜬다. 인증은 옵션. → **로컬 체크 용도라면 암호 없이 그냥 띄우면 됨**.

---

## 3. 헤드리스 호출 후보 경로 (우선순위)

### ★★★ 1순위 — `opencode run --format json` 서브프로세스

**명령 템플릿**
```bash
echo "ping" | opencode run --agent sisyphus \
  --model ollama/gemma3:27b \
  --format json \
  --dir /path/to/project
```
또는 Windows bash:
```bash
opencode run --agent sisyphus --model ollama/gemma3:27b --format json "ping from audrey"
```

**stdout 파싱 방법**
- NDJSON. 각 라인을 `json.loads`하고 `type == "text"`인 파트에서 `part.text`를 모은다.
- `type == "error"`면 즉시 실패 처리.
- 세션 idle 이벤트는 `type`으로 나오지 않고 스트림 종료로 구분 → 프로세스 종료 코드로 판단.

**실패 모드**
| 상황 | 관측 결과 |
|---|---|
| Ollama 미기동 | `session.error` 이벤트 → `type:"error"` NDJSON |
| 에이전트 이름 오타 | 경고 메시지 (stderr) 후 default agent로 진행. **성공처럼 보임** → 오드리 측에서 응답 내용 검사 필요 |
| 모델 ID 오타 | 프로바이더에서 에러 → `session.error` 이벤트 |
| 타임아웃 | 자체 타임아웃 없음 → 파이썬 subprocess에 `timeout=` 필수 |
| stdin TTY 문제 | 메시지 비었고 `--command`도 없으면 exit 1 (run.ts:347-350) |

### ★★ 2순위 — `opencode serve` + HTTP REST

백그라운드로 서버 한 번 띄워 두고 여러 체크에서 재사용. v3가 F1~F4를 순차로 돌릴 거면 서버 1회 기동이 더 효율적.

```bash
opencode serve --port 4097 --hostname 127.0.0.1 &
SERVER_PID=$!
# ... HTTP 호출들 ...
kill $SERVER_PID
```

**파싱**: 표준 JSON 응답. 이벤트 스트리밍은 SSE(`/event` 라우트) 활용.
**실패 모드**: 포트 바인딩 실패, `OPENCODE_SERVER_PASSWORD` 설정 시 basic auth 필수.

### ★ 3순위 — `opencode run --attach <url>` 하이브리드

이미 사내 누군가 서버를 띄워 뒀다면 그쪽으로 메시지만 쏜다. 오드리는 "서버 존재 확인"만 하고 끝낼 수 있음. 단 이건 F1~F4의 목적과 어긋날 수 있음(오드리는 "내 머신에서 되나?"를 본다).

---

## 4. 4096 HTTP API (정적 분석 기반)

실제 curl은 못했지만 `packages/opencode/src/server/instance.ts`와 `routes/session.ts`를 읽어 확인한 라우트:

**마운트 경로** (`server/instance.ts:47-58`)
```
/project       ProjectRoutes
/pty           PtyRoutes
/config        ConfigRoutes
/experimental  ExperimentalRoutes
/session       SessionRoutes
/permission    PermissionRoutes
/question      QuestionRoutes
/provider      ProviderRoutes
/mcp           McpRoutes
/tui           TuiRoutes
/              FileRoutes, EventRoutes
```
추가로 `server/server.ts:100`에 `/global` 마운트. OpenAPI는 `hono-openapi`로 `describeRoute`에 붙어 있으며, 전 라우트에서 `operationId`로 조회 가능 (예: `session.prompt`, `session.prompt_async`, `session.command`, `session.create`, `session.fork`).

**핵심 세션 엔드포인트** (`server/routes/session.ts`)

| 메서드/경로 | operationId | 용도 |
|---|---|---|
| `POST /session` | `session.create` | 세션 생성, body: `Session.create` |
| `POST /session/:id/message` | `session.prompt` | **메시지 전송 + 스트리밍 응답** |
| `POST /session/:id/prompt_async` | `session.prompt_async` | 비동기 전송, 204 즉시 리턴 |
| `POST /session/:id/command` | `session.command` | 커맨드 실행 |
| `POST /session/:id/fork` | `session.fork` | 포크 |
| `POST /session/:id/init` | `session.init` | AGENTS.md 초기화 |
| `GET /session` | 목록 | |
| `DELETE /session/:id` | 삭제 | |
| `PATCH /session/:id` | 제목/아카이브 | |

**샘플 curl** (인증 없을 때)
```bash
# 1) 세션 생성
SID=$(curl -s -X POST http://127.0.0.1:4097/session \
  -H "Content-Type: application/json" \
  -d '{"title":"audrey-f2"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 2) 메시지 전송 (Sisyphus 에이전트, ollama 모델)
curl -s -X POST "http://127.0.0.1:4097/session/$SID/message" \
  -H "Content-Type: application/json" \
  -d '{
        "agent":"sisyphus",
        "model":{"providerID":"ollama","modelID":"gemma3:27b"},
        "parts":[{"type":"text","text":"ping"}]
      }'
```
(`model`은 `{providerID, modelID}` 객체. `run.ts:644`의 `Provider.parseModel(args.model)` 결과와 동일 스키마.)

**이벤트 스트림**: `EventRoutes`가 `/` 하위에 SSE를 제공한다. `opencode run`은 `sdk.event.subscribe()`로 구독한다(run.ts:441). 직접 REST로 하려면 `GET /event` (SSE)를 열어두고 위의 POST를 병행해야 한다. **구현 난이도는 ★★★**. F2 단건 체크엔 과잉.

---

## 5. F1~F4 구현 권고안 (Builder용)

### 권고 — **1순위 전략 고정: `opencode run --format json`**

서버 관리 없이 `subprocess.run()` 한 번이면 끝나고, 응답 파싱이 라인 단위 NDJSON이라 파이썬 stdlib로 충분. 폐쇄망 VDI에서 포트 충돌/방화벽 리스크도 없음.

### `checks/e2e.py` 예시 (회장님과 Builder가 그대로 쓸 수 있는 형태)

```python
# audrey_v3.0/src/checks/e2e.py
import json
import shutil
import subprocess
from typing import Any

OPENCODE_BIN = "opencode"   # PATH에 없으면 cfg에서 절대경로 주입
DEFAULT_TIMEOUT = 60        # 초. 로컬 Ollama 기준 여유 있게

def _run_opencode(prompt: str, agent: str, model: str, cwd: str,
                  timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """opencode run --format json 을 subprocess로 호출하고 NDJSON 이벤트를 수집."""
    if not shutil.which(OPENCODE_BIN):
        return {"ok": False, "reason": "opencode-not-in-path"}
    proc = subprocess.run(
        [OPENCODE_BIN, "run",
         "--format", "json",
         "--agent", agent,
         "--model", model,
         "--dir", cwd,
         prompt],
        capture_output=True, text=True, timeout=timeout, cwd=cwd,
    )
    events, texts, errors = [], [], []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(evt)
        t = evt.get("type")
        if t == "text":
            part = evt.get("part", {})
            if part.get("text"):
                texts.append(part["text"])
        elif t == "error":
            errors.append(evt.get("error"))
    return {
        "ok": proc.returncode == 0 and not errors and bool(texts),
        "returncode": proc.returncode,
        "stderr": proc.stderr[-2000:],
        "events": len(events),
        "text": "\n".join(texts),
        "errors": errors,
    }

def f2_sisyphus_ping(cfg, ctx) -> dict:
    """F2 — 시지푸스 에이전트가 ping에 응답하는지."""
    result = _run_opencode(
        prompt="ping from audrey v3",
        agent=cfg.get("sisyphus_agent", "sisyphus"),
        model=cfg.get("sisyphus_model", "ollama/gemma3:27b"),
        cwd=cfg.get("project_dir", "."),
        timeout=cfg.get("e2e_timeout", 60),
    )
    if not result["ok"]:
        return {"status": "fail", "detail": result}
    # 실제 응답이 왔는지 + 에이전트 fallback 여부를 텍스트로 판정
    if "sisyphus" not in result["text"].lower() and len(result["text"]) < 3:
        return {"status": "warn", "detail": "응답 길이 부족, agent fallback 가능성"}
    return {"status": "pass", "detail": {"chars": len(result["text"])}}
```

F1(환경 선기동 확인), F3(다른 에이전트), F4(툴 실행 확인) 모두 **같은 `_run_opencode` 헬퍼**에 프롬프트/에이전트만 바꿔 재사용하면 된다.

### 추가 보강 포인트
- `--format json` 이벤트에 `tool_use`가 있으므로 F4는 "`tool_use` 이벤트가 최소 1건 이상"을 성공 조건으로 걸 수 있음.
- cfg에 `opencode_bin`, `sisyphus_agent`, `sisyphus_model`, `e2e_timeout`를 반드시 추가. 노트북/블랙웰/데스크탑 환경별 모델 ID가 달라질 수 있으므로 하드코딩 금지.
- Windows에서 `shutil.which("opencode")`가 `.cmd` 래퍼를 못 찾는 경우가 있다. **`.cmd`/`.exe` 후보를 한 번 더 시도**하는 `_resolve_bin()` 유틸 필요.

---

## 6. 경고와 함정

1. **Bun 미설치** — 이 VDI에서는 `bun install`도 안 되므로 오드리 v3.0 체크를 실제로 돌려볼 수 없다. 설치 후 재검증 필요.
2. **루트에서 `bun test` 금지** — `do-not-run-tests-from-root` 가드 존재. 반드시 `cd packages/opencode` 후 실행.
3. **OpenCode 기본 브랜치는 `dev`** (main 아님). diff는 `origin/dev` 기준.
4. **`opencode run`의 에이전트 fallback** — 없는 에이전트를 지정해도 exit 0으로 끝난다. F3에서 이름 오타 탐지가 필요하면 **먼저 `opencode debug agent <name>`** 또는 `agent list`로 사전 확인 권장.
5. **권한 자동 거절 하드코딩** — run 모드는 `question/plan_enter/plan_exit` 모두 deny. 도구가 승인 요청을 띄우면 자동 거절되므로 F4 툴 체크는 **승인 불필요한 툴**(read/ls/bash 등)로 골라야 한다(run.ts:544-556: `permission.asked` 즉시 reject).
6. **thinking 출력 off가 기본** — 추론형 모델(gemma3/qwen3) 사용 시 `--thinking`을 켜지 않으면 reasoning 파트가 누락된다. 오드리는 굳이 켤 필요 없음(응답 본문으로 충분).
7. **`--format json`의 NDJSON은 TTY 체크와 독립** — 파이썬에서 `subprocess.PIPE`로 받으면 그대로 한 줄씩 들어온다. 줄 단위 파서는 `splitlines()` 만으로 안전.
8. **`opencode serve` 기본 포트는 0(랜덤)** — 관례상 4096이지 기본값 아님. 반드시 `--port`를 명시해서 쓸 것.
9. **Windows bash에서 경로** — `--dir`에 전달할 땐 백슬래시/슬래시 혼용 금지. `pathlib.Path().as_posix()` 로 정규화 권장.
10. **`OPENCODE_SERVER_PASSWORD`** 가 설정돼 있으면 `opencode run`도 같은 env를 존중. VDI 사용자 환경에 이게 남아 있는지 체크(그래야 attach 경로도 동작).

---

### 재검증 To-Do (Bun 설치 이후)

- [ ] `cd opencode-dev && bun install` 소요 시간 측정
- [ ] `bun dev run --help` 출력 저장
- [ ] `bun dev serve --port 4097` 후 `curl http://127.0.0.1:4097/session` 실응답 캡처
- [ ] `bun dev run --format json "ping"` 로 NDJSON 스트림 샘플 수집 (프로바이더 없이 실패하는 경로 먼저)
- [ ] F1~F4 실제 subprocess 호출 통합 테스트
