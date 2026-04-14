# 03. Gemma4 Ollama 서빙 (3티어 배분)

## 서빙 스택

- **메인**: Ollama 0.20.4, systemd 서비스, `0.0.0.0:11434` 외부 접속 허용 (override.conf)
- **백업**: vLLM gemma4venv (0.19.1rc1 + transformers 5.5.0)
- **모델 파일**: `~/models/` 및 Ollama 로컬 스토어

이전 세대(Qwen3.5 + vLLM)는 **Superseded** (2026-04-10 전환).

## 3티어 모델 배분

| 티어 | 모델 | Ollama 크기 | 에이전트 | 카테고리 |
|------|------|-------------|----------|----------|
| 🧠 Heavy | `gemma4:31b` | 19 GB (Q4_K_M) | sisyphus, prometheus, metis, momus | ultrabrain, deep |
| ⚙️ Medium | `gemma4:26b` | 17 GB (Q4_K_M) | hephaestus, atlas, multimodal-looker | artistry, writing, visual, high |
| ⚡ Light | `gemma4:e4b` | 9.6 GB (Q4_K_M) | oracle, librarian, explore | quick, low |

예비: `gemma4:e2b` (7.2GB), `glm-4.7-flash` (19GB)

## 응답 검증 현황

| 경로 | 결과 | 확인일 |
|------|------|--------|
| Ollama E2B tool_calls + thinking | ✅ | 2026-04-10 |
| Ollama E4B tool_calls + thinking | ✅ | 2026-04-10 |
| Ollama 31B tool_calls + reasoning | ✅ | 2026-04-10 |
| Ollama 26B chat | ✅ (tool 미테스트) | 2026-04-10 |
| vLLM E4B | ✅ (gemma4venv) | 이전 |
| vLLM 26B-A4B | ✅ (GPU1, port 8001, util 0.7) | 2026-04-10 |
| **vLLM 31B chat_template** | ❌ **Superseded by Ollama** | tokenizer_config.json에 template 없음, chatml.jinja 비호환 |

## OpenCode 설정 예시

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "name": "Ollama Gemma4",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://10.88.22.29:11434/v1",
        "apiKey": "ollama"
      },
      "models": {
        "gemma4:31b": { "limit": { "context": 131072, "tool_call": true, "output": 8192 } },
        "gemma4:26b": { "limit": { "context": 131072, "tool_call": true, "output": 8192 } },
        "gemma4:e4b": { "limit": { "context": 131072, "tool_call": true, "output": 4096 } }
      }
    }
  },
  "model": "ollama/gemma4:31b"
}
```

**함정**: `baseURL`을 `localhost`로 두면 데스크탑/노트북에서 연결 실패 (4월 13일 실제 버그). 블랙웰 서버에서 실행할 때만 localhost가 정답. → 오드리 v3.1 B5 체크가 구분한다.

## 관련 노드

- [04. 시지푸스 마일스톤](04_sisyphus_milestones.md) — 이 배분으로 시지푸스가 움직였다
- [05. 오드리 v3.1](05_audrey_v31.md) — B5 baseURL 함정 탐지
- [09. 블랙웰 제약사항](09_constraints_blackwell.md) — HF 다운로드 등 인프라 제약

## Source

- memory `project_gemma4_model_plan.md`, `project_blackwell_env.md`
- `docs/CONSTRAINTS.md`
- `_archive/gist_comments_20260410.txt`
