# 오드리 v3.0 — 테스트 전략

> stdlib-only 제약(`DESIGN.md §0`) 하에서 어떻게 테스트를 짤 것인가.
> 본 문서는 Builder가 `test_*.py`를 작성할 때의 **설계 지침**이다.

---

## 1. 제약

- **외부 패키지 금지**: `pytest`, `responses`, `httpx-mock`, `mock` (외부) 전부 불가.
- 사용 가능: `unittest`, `unittest.mock`(stdlib), `http.server`, `socketserver`, `threading`, `tempfile`, `pathlib`, `json`, `socket`, `contextlib`.
- 테스트 러너: `python -m unittest discover audrey_v3.0/tests`

---

## 2. 네트워크 모킹 — 2가지 방식

### 방식 A. `unittest.mock.patch`로 http.py 모듈 패치 (권장, 단위 테스트)

오드리 v3의 `src/http.py`가 `http_get(url, timeout)` / `http_post_json(url, body, timeout)` 두 함수를 export한다는 전제(DESIGN.md §9). 테스트에서는:

```python
from unittest.mock import patch
from audrey_v3.src import http

def fake_get(url, timeout=3.0):
    if "10.88.22.29:11434" in url and url.endswith("/v1/models"):
        return 200, json.loads(Path("tests/fixtures/provider_responses/ollama_models.json").read_text())
    if "10.88.22.29:8000" in url:
        raise ConnectionError("vllm down")
    raise ConnectionError(f"unexpected: {url}")

with patch.object(http, "http_get", side_effect=fake_get):
    ...
```

**장점**: 빠르고 결정적. 포트 충돌 없음.
**단점**: http.py 내부 URL 가공 로직은 우회됨 → A2에서 URL 조립 버그는 못 잡음.

### 방식 B. 로컬 `http.server` 픽스처 서버 (통합 테스트)

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, json, socket
from pathlib import Path

FIX = Path(__file__).parent / "fixtures/provider_responses"

class FakeOllamaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/v1/models":
            body = FIX.joinpath("ollama_models.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            body = FIX.joinpath("ollama_chat.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, *a, **kw):
        pass  # 조용히

def start_fake_server():
    s = HTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    port = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    return s, port
```

- 테스트에서 `Provider.base_url`을 `http://127.0.0.1:{port}`로 덮어 씌운다.
- 종료 시 `s.shutdown()`.
- **장점**: 실제 http 스택 관통, URL 조립 버그 포착.
- **단점**: 포트 경합/윈도우 방화벽 이슈 가능.

**가이드라인**: S2/S4/R4 같은 "정상 동작" 시나리오는 방식 B로 한 번씩 관통 테스트. 나머지(S1, R1~R3, 오류 분기)는 방식 A로 빠르게.

---

## 3. 파일시스템 모킹

`tempfile.TemporaryDirectory`로 가짜 `opencode_config_dir`를 구성한다.

```python
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # opencode.json 복사
    (td / "opencode.json").write_text(
        (FIXTURES / "opencode.json.ollama_remote.json").read_text(),
        encoding="utf-8",
    )
    # oh-my-openagent.jsonc (픽스처는 .json이지만 JSONC 파서는 순수 JSON도 읽어야 함)
    (td / "oh-my-openagent.jsonc").write_text(
        (FIXTURES / "oh-my-openagent.jsonc.gemma4_tiered.json").read_text(),
        encoding="utf-8",
    )
    cfg.opencode_config_dir = td
    ctx = build_context(cfg)
    ...
```

**주의**: 픽스처 JSON에는 `"_note"` 키가 들어있다. 오드리 파서는 알 수 없는 키를 **무시**해야 한다 (DESIGN에 명시 없음 → Builder에게 주의 사항으로 전달). Builder가 strict 파싱을 택한다면 테스트에서 `_note`를 제거한 뒤 기록해야 한다.

---

## 4. 환경 자각(ENV1) 모킹

`env.detect_environment`는 `socket.gethostname`, `subprocess.run(["nvidia-smi",...])`, `socket.create_connection` 등에 의존할 것이다. 테스트는 두 갈래:

1. **hint 강제**: `environment_hint="vdi"` 처럼 Config 레벨에서 강제 → ENV1은 PASS로 기록되고 판정 로직만 테스트.
2. **완전 모킹**: `patch("audrey_v3.src.env.socket.gethostname", return_value="VDI-1234")` 등.

S1/S3/S4 같은 ENV 분기 테스트는 두 방식을 모두 시도 — Builder가 쉬운 쪽을 고를 수 있도록 열어 둔다.

---

## 5. 서브프로세스 모킹 (opencode run, nvidia-smi)

- `run_command()`는 `subprocess.run`을 래핑한다고 가정 (DESIGN §0).
- 테스트에서는 `patch("audrey_v3.src.util.run_command", side_effect=fake_run)` 로 대체.

```python
def fake_run(cmd, timeout=30):
    if cmd[0] == "opencode" and "run" in cmd:
        return 0, "pong — Gemma4 31B\n", ""
    if cmd[0] == "nvidia-smi":
        return 0, "RTX PRO 6000 Blackwell", ""
    return 127, "", "not mocked"
```

---

## 6. 시나리오 → 테스트 파일 매핑 (Builder 제안)

| 시나리오 | 권장 테스트 파일 | 방식 |
|----------|------------------|------|
| S1 (VDI) | `test_scenario_s1_vdi.py` | A |
| S2 (데스크탑) | `test_scenario_s2_desktop.py` | **B** (골든 관통) |
| S3 (노트북) | `test_scenario_s3_laptop.py` | A |
| S4 (블랙웰) | `test_scenario_s4_blackwell.py` | **B** |
| R1 (v2 config) | `test_regression_r1_v2_config.py` | A + 단위 테스트 `test_config_migrate.py` |
| R2 (localhost 함정) | `test_regression_r2_localhost.py` | A + 단위 `test_autofix_baseurl.py` |
| R3 (Qwen legacy) | `test_regression_r3_qwen_legacy.py` | A |
| R4 (둘 다 alive) | `test_regression_r4_multi_alive.py` | **B** (두 서버 병렬) |

추가 단위 테스트 권장:
- `test_config_migrate.py` — `migrate_v2_to_v3` 입출력
- `test_provider_pick.py` — `pick_actual_provider` priority 정렬
- `test_judge.py` — `judge()` 5축 조합 진리표

---

## 7. 실행 / CI

- **현재는 수동**: `cd audrey_v3.0 && python -m unittest discover tests`
- **CI 가능성**: 폐쇄망(블랙웰/사내)에서는 `cron` + JSON 리포트 → gist 업로드 쪽으로 진화. GitHub Actions는 사용 불가(회장님 환경 제약).
- **재현성**: 모든 테스트는 네트워크 I/O가 mock 또는 127.0.0.1 임시 포트로 격리되어야 한다. 실제 10.88.22.29 실 호출을 테스트에서 하지 않는다 (실 진단은 `python -m audrey_v3.0` 직접 실행으로 대체).

---

## 8. 테스트 종료 조건 (어디까지가 "충분한가")

- S2 + R2 + R4가 PASS → MVP (수용 기준 #1, #3, 멀티 프로바이더 커버)
- 추가로 S1 + S4가 PASS → 환경 자각 기능 검증 완료 (수용 기준 #4, #5)
- R1 PASS → 후방 호환 검증 (수용 기준 #6)
- S3 + R3는 추가 신뢰도 확보용 (옵션)

---

*본 문서는 살아있는 전략서다. Builder가 테스트 코드를 작성하면서 발견되는 파싱/모킹 이슈는 여기에 덧붙인다.*
