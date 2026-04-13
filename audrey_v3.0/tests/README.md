# audrey_v3.0/tests — 테스트 키트

오드리 v3.0의 시나리오·픽스처·테스트 전략이 모여 있는 폴더. 현재는 **명세와 픽스처만** 있고, 실제 `test_*.py`는 Builder가 `scenarios.md` + `test_strategy.md`를 참조해서 작성한다.

## 구성

```
tests/
├── README.md              ← 본 파일
├── scenarios.md           ← 환경 4개 + 회귀 4개 시나리오 명세 (메인)
├── test_strategy.md       ← stdlib-only 모킹 전략 + Builder 가이드
└── fixtures/
    ├── config.v2.json                         ← v2.31 호환 config (R1)
    ├── opencode.json.ollama_remote.json       ← S2/S3 정상 (원격 Ollama)
    ├── opencode.json.localhost_trap.json      ← R2 (localhost 함정)
    ├── opencode.json.qwen_legacy.json         ← R3 (구 Qwen/vLLM 스타일)
    ├── oh-my-openagent.jsonc.gemma4_tiered.json  ← OmO 3티어 배분
    └── provider_responses/
        ├── ollama_models.json                 ← /v1/models 샘플
        └── ollama_chat.json                   ← /v1/chat/completions 샘플
```

> 픽스처 JSON에는 `"_note"` 키로 용도가 한 줄 설명되어 있다. 오드리 설정 파서는 알 수 없는 키를 무시해야 한다(또는 테스트에서 `_note`를 제거한 뒤 기록).

## 테스트 실행 (코드가 작성된 이후)

```bash
cd C:/Users/dongho.yoon/project/999_offcode
python -m unittest discover audrey_v3.0/tests
```

카테고리 단위 또는 시나리오 단위 실행:

```bash
python -m unittest audrey_v3.0.tests.test_scenario_s2_desktop
python -m unittest audrey_v3.0.tests.test_regression_r2_localhost
```

## 시나리오를 수동으로 확인하려면

본격 Python 테스트가 없더라도 픽스처 + 실 CLI로 각 시나리오 일부를 재현 가능하다.

### S2 수동 재현 (사내 데스크탑에서 실행)

```bash
cp audrey_v3.0/tests/fixtures/opencode.json.ollama_remote.json ~/.config/opencode/opencode.json
python -m audrey_v3.0 --config audrey_v3.0/config.example.v3.json --json
# 기대: verdict.ready == true
```

### R2 수동 재현 (localhost 함정)

```bash
cp audrey_v3.0/tests/fixtures/opencode.json.localhost_trap.json ~/.config/opencode/opencode.json
python -m audrey_v3.0 --config audrey_v3.0/config.example.v3.json --json
# 기대: B5 FAIL, fix 제안 텍스트에 "10.88.22.29" 포함
python -m audrey_v3.0 --config audrey_v3.0/config.example.v3.json --auto-fix --dry-run
# 기대: 치환 diff 출력
```

### R1 수동 재현 (v2 config)

```bash
python -m audrey_v3.0 --config audrey_v3.0/tests/fixtures/config.v2.json --json
# 기대: stderr/로그에 "v2 config detected; migrated to v3 in-memory"
#       디스크의 config.v2.json은 변경되지 않아야 한다
```

## 시나리오 맵

자세한 내용은 [scenarios.md](./scenarios.md) 참조. 요약:

| ID | 환경 | READY | 핵심 검증 |
|----|------|-------|-----------|
| S1 | VDI | false | VDI 자각 + SKIP 분기 |
| S2 | 데스크탑 | **true** | 골든 케이스 (수용 기준 #1) |
| S3 | 노트북 | true | ENV 분기 오염 없음 |
| S4 | 블랙웰 | true | localhost도 정답일 수 있음 |
| R1 | v2 config | false | 후방 호환 (수용 기준 #6) |
| R2 | localhost 함정 | false | B5 FAIL + autofix (수용 기준 #3) |
| R3 | Qwen legacy | false | provider/endpoint 불일치 탐지 |
| R4 | 멀티 alive | **true** | priority 선택 로직 |

## Builder가 반드시 봐야 할 것

1. **scenarios.md의 S2와 R2** — 이 둘이 오드리 v3.0의 레종데트르. 여기가 통과 못 하면 v3는 실패.
2. **test_strategy.md §2** — 네트워크 모킹 방식 A/B 중 시나리오별 권장이 정리되어 있음.
3. **fixtures/\*.json의 `_note` 키** — 파싱 시 무시하도록 오드리 쪽이 관대해야 한다.

## 향후

현재 수동 기반이지만, Phase 6 이후 `run_tests.sh` + JSON 리포트 → gist 업로드 루프로 CI 대체 예정. 이는 테스트 코드 작성 이후 별도 트랙.
