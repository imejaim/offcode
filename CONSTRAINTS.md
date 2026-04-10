# 블랙웰 서버 제약사항 (확인된 것만 기록)

> 코부장이 gist 댓글 작성 전 반드시 이 파일을 확인하고, 안 되는 방법을 제안하지 않는다.

## ❌ 안 되는 것

| 항목 | 이유 | 확인일 |
|------|------|--------|
| `huggingface-cli download` | 프록시에서 병렬 전송 행걸림 (밤새 31MB) | 2026-04-08 |
| `hf download` (동일) | 위와 같음. `--max-workers 1` 미검증 | 2026-04-08 |
| Docker Hub pull | 방화벽 차단 | 2026-04-08 |
| npm 플러그인 로딩 (`oh-my-opencode@3.15.3`) | OpenCode 플러그인 로더 버그 | 2026-04-08 |
| vLLM 0.18.0 + Gemma4 | transformers 버전 충돌 (GitHub #39216) | 2026-04-08 |
| `--tool-call-parser hermes` (Gemma4) | Gemma4는 `gemma4` 파서 사용 | 2026-04-08 |
| 26B-A4B + `--gpu-memory-utilization 0.5` | 모델 49GB > 48GB(96GB×0.5). KV캐시 -5.7GB. 최소 0.7 필요 | 2026-04-10 |
| vLLM 31B + `--chat-template chatml.jinja` | Gemma4에 ChatML 템플릿 안 맞음. `<\|im_end\|>` 반복, tool call 무한생성 | 2026-04-10 |
| vLLM 31B chat_template 미해결 | tokenizer_config.json에 chat_template 없음. Gemma4 전용 jinja 필요 | 2026-04-10 |
| `ollama pull gemma4:27b` | 태그 없음. 올바른 태그는 `gemma4:26b` | 2026-04-10 |
| dongho.yoon 계정 sudo | sudoers 미등록. 시스템 작업은 user 계정으로 | 2026-04-10 |

## ✅ 되는 것

| 항목 | 비고 | 확인일 |
|------|------|--------|
| `wget -c` 모델 다운로드 | 프록시 경유 61MB/s 정상 | 2026-04-08 |
| `file://` 플러그인 경로 | npm 대신 글로벌 설치 후 file:// 참조 | 2026-04-08 |
| gemma4venv (vLLM 0.19.1rc1 + transformers 5.5.0) | Gemma4 전용 가상환경 | 2026-04-08 |
| vllmvenv (vLLM 0.18.0) | Qwen 전용 가상환경 | 2026-04-08 |
| `--tool-call-parser gemma4` | Gemma4 tool call 정상 | 2026-04-08 |
| `--tool-call-parser qwen3_coder` | Qwen3.5 tool call 정상 | 2026-04-08 |
| OmO `file://` 시지푸스 | 윈도우+블랙웰 모두 동작 확인 | 2026-04-08 |
| 26B-A4B 서빙 (GPU1, port 8001) | `--gpu-memory-utilization 0.7`, 70053/97887 MiB | 2026-04-10 |
| 31B 다운로드 완료 | `~/models/gemma-4-31b-it/` (wget) | 2026-04-10 |
| Ollama 0.20.4 설치 | systemd 서비스, 0.0.0.0:11434 외부 접속 허용 | 2026-04-10 |
| Ollama Gemma4 전모델 | 31b(19GB), 26b(17GB), e4b(9.6GB), e2b(7.2GB) 다운완료 | 2026-04-10 |
| Ollama tool call (E2B/E4B/31B) | OpenAI-compatible API, tool_calls 정상 반환 | 2026-04-10 |
| Ollama Gemma4 thinking | e2b/e4b에서 reasoning 필드로 thinking 과정 출력 | 2026-04-10 |
| 블랙웰 시지푸스 (Ollama) | OmO + Ollama/gemma4:31b로 시지푸스 응답 확인 | 2026-04-10 |
| vLLM 31B 서버 시작 | processor_config.json E4B에서 복사, --enable-auto-tool-choice 필요 | 2026-04-10 |
