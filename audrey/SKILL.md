---
name: audrey
description: OFFCODE 환경 검사 에이전트 오드리(Dr. Oh). 환경 설정 문제를 진단하고 해결 방법을 안내합니다.
---

# audrey — OFFCODE 환경 검사 스킬

## 개요

오드리(Dr. Oh)는 OFFCODE(OpenCode + OmO + vLLM) 환경이 올바르게 설치되었는지 검사하는 에이전트입니다.

## 사용법

OpenCode의 `.opencode/command/` 또는 skill로 등록하여 사용합니다.

```
/audrey
```

## 동작 흐름

1. `python audrey/doctor_oh_check.py --json` 실행
2. JSON 결과를 파싱하여 각 항목의 PASS/WARN/FAIL 상태 확인
3. 실패 항목에 대해 원인 분석 및 해결 방법 안내
4. 자동 수정 가능 항목은 `--auto-fix` 옵션으로 자동 복구 시도
5. 수정 후 재검사하여 결과 보고

## 검사 항목

| # | 항목 | 설명 |
|---|------|------|
| 1 | vLLM 서버 연결 | vLLM 엔드포인트 접근 가능 여부 및 모델 로드 상태 |
| 2 | OpenCode CLI | `opencode` 명령어 PATH 존재 여부 |
| 3 | OmO 플러그인 | oh-my-opencode(oh-my-openagent) 플러그인 로드 상태 |
| 4 | OmO 설정 파일 | `.opencode/oh-my-opencode.jsonc` 존재 및 파싱 |
| 5 | opencode.json | 프로젝트 설정 파일 유효성 |
| 6 | sisyphus 에이전트 | OmO 빌트인 에이전트 등록 상태 |
| 7 | Bun 런타임 | Bun 설치 및 버전 확인 |
| 8 | Node.js | Node.js 설치 여부 (fallback) |
| 9 | Python | Python 3.9+ 설치 여부 |
| 10 | 프록시 설정 | 사내 프록시 환경변수 설정 상태 |

## 사내 환경 자동 감지

오드리는 다음과 같은 사내 환경 특이사항을 자동으로 감지합니다:

- **프록시 설정**: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` 환경변수 누락 감지
- **file:// 경로**: OmO 플러그인이 로컬 경로(`file:///...`)로 설정된 경우 경로 유효성 검증
- **패키지명 오타**: `oh-my-opencode` vs `oh-my-openagent` 혼용 감지 및 올바른 이름 안내
- **vLLM 엔드포인트**: `config.json`의 `vllm_url` 접근 가능 여부 확인
- **방화벽/네트워크**: 사내망에서 vLLM 서버 포트 접근 차단 감지

## 설정 파일

`audrey/config.json`에서 환경별 설정을 관리합니다:

```json
{
  "vllm_url": "http://10.88.22.29:8000",
  "vllm_model": "Qwen3.5-35B-A3B",
  "opencode_config_dir": "~/.config/opencode",
  "expected_plugin": "oh-my-openagent"
}
```

## 프롬프트

상세 에이전트 프롬프트는 `audrey/audrey_prompt.md`를 참조하세요.
