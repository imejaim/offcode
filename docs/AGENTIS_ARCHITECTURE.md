# Agentis 아키텍처 & 로드맵

> **Agentis** — 사내 로컬 LLM 기반 에이전트 플랫폼(브랜드).
> 이전명: Agentis (2026-04-13 리브랜딩)

---

## 0. Agentis 플랫폼 구조

```
Agentis              ← 전체 플랫폼 (브랜드)
 ├── Agentium        ← 실행 엔진 (core runtime)
 ├── AgentMesh       ← 에이전트 네트워크
 ├── AgentHub        ← UI / dashboard
 └── AgentSDK        ← 개발용 툴킷
```

| 컴포넌트 | 역할 | 현재 구현 |
|----------|------|-----------|
| **Agentium** | 에이전트 실행 런타임. 프로바이더(Ollama/vLLM/…)→LLM 호출→도구 실행→응답 루프 | OpenCode + OmO(oh-my-openagent) |
| **AgentMesh** | 에이전트 간 통신·위임·오케스트레이션 네트워크 | OmO 서브에이전트(시지푸스→헤파이스토스 등) |
| **AgentHub** | UI/대시보드. 에이전트 모니터링, 로그, 작업 큐 | 미구현(장기) |
| **AgentSDK** | 개발자가 새 에이전트·도구·스킬 만드는 툴킷 | OmO plugin SDK, PydanticAI |

오드리(Dr. Oh)는 **Agentium 헬스체크 에이전트**로 포지셔닝된다.

---

## 1. 아키텍처 개요

```
┌──────────────────────────────────────────────────────┐
│  Agentis — 에이전트 빌더 (Layer 1: 만드는 도구)       │
│                                                      │
│  OpenCode + OmO (oh-my-opencode)                     │
│  하네스 구조: 도구 실행, MCP, CLI, 훅, 서브에이전트     │
│  로컬 LLM: Gemma4 31B/26B/E4B (Ollama 서빙)          │
│                                                      │
│  역할: 에이전트 코드를 작성, 테스트, 디버깅, 배포       │
│        의존성 해결, 환경 구축을 하네스적으로 수행        │
└───────────────────────┬──────────────────────────────┘
                        │ 만들어 낸다
                        ▼
┌──────────────────────────────────────────────────────┐
│  업무 에이전트 런타임 (Layer 2: 돌아가는 엔진)         │
│                                                      │
│  PydanticAI — 타입 안전 에이전트 프레임워크 (Python)   │
│  LangGraph  — 복잡한 멀티스텝 워크플로우 (필요시)      │
│  Ollama     — OpenAI 호환 API (11434/v1, 멀티모델 핫스왑) │
│  MCP 서버   — 메일, DB, 파일, Slack 등 도구 연결       │
│                                                      │
│  역할: 만들어진 에이전트가 실제 업무를 수행하는 환경     │
│        크론잡, API 서버, CLI 등으로 운영               │
└───────────────────────┬──────────────────────────────┘
                        │ 조회한다
                        ▼
┌──────────────────────────────────────────────────────┐
│  지식 인프라 (Layer 3: 아는 것)                        │
│                                                      │
│  벡터DB: pgvector 또는 Qdrant (사내 셀프호스팅)        │
│  인덱싱: LLM 기반 문맥 강화 (Contextual Retrieval)    │
│  문서 처리: 멀티모달 (Qwen-VL로 엑셀/PDF 이미지 해석)  │
│  GraphRAG: 관계형 추론 필요시 (Microsoft GraphRAG)     │
│  하이브리드 검색: BM25 + 밀집 벡터 + 크로스인코더 리랭킹│
│                                                      │
│  역할: 사내 전문지식 저장, 검색, 추론                   │
│        단순 벡터 유사도가 아닌 맥락 있는 검색            │
└──────────────────────────────────────────────────────┘
```

---

## 2. 에이전트 목록

### 이미 만든 에이전트
| 에이전트 | 이름 | 역할 | 동작 환경 |
|---|---|---|---|
| **뀨리 (GGuri)** | 문서자동화 에이전트 | 자료 수집 → 문서 작성 → 메일 발송 | Agentis 하네스 (CLI) |
| **오드리 (Dr. Oh)** | 환경검사 에이전트 | Agentis 환경 구축 상태 점검 | Agentis 하네스 (CLI) |

### 향후 만들 에이전트 (예정)
| 에이전트 | 역할 | 예상 런타임 |
|---|---|---|
| 사내 전문지식 Q&A | RAG 기반 사내 문서 검색 + 답변 | PydanticAI + 벡터DB |
| 일일/주간 보고서 자동화 | 다중 소스 수집 → 보고서 생성 | PydanticAI 또는 하네스 |
| 회의록 정리 | 회의 메모 → 요약 + 액션아이템 | PydanticAI (단일 에이전트) |
| 코드 리뷰/PR 자동 검토 | PR 자동 리뷰 + 보안 체크 | Agentis 하네스 (코딩 에이전트) |
| 온보딩 도우미 | 신입사원 질문 응답, 사내 규정 안내 | PydanticAI + RAG |
| 이상 감지/알림 | 시스템 모니터링 → 이상 탐지 → 알림 | PydanticAI + 스케줄러 |

---

## 3. 사내 배포 로드맵

### Phase 0: 인프라 확인 ✅ (2026-04-10 완료)
```
[사내 GPU 서버] RTX PRO 6000 Blackwell x2 (Ubuntu)
       │
       ▼
[Ollama 0.20.4 서빙] Gemma4 31B / 26B / E4B (0.0.0.0:11434)
       │
       ▼
[터미널 접속 확인]
```
- Ollama 서버 정상 동작 확인 (systemd, 외부 접속 허용)
- 블랙웰 로컬에서 시지푸스 응답 확인 (Gemma4 31B, 34.2s)
- 사내 데스크탑(윈도우)에서 `10.88.22.29:11434` 원격 접속 확인은 진행 중
- vLLM은 백업으로 보류 (31B chat_template 미해결)

### 3모델 배분 (Gemma4 / Ollama)

| 티어 | 모델 | 에이전트 | 카테고리 |
|------|------|---------|---------|
| 🧠 Heavy | `gemma4:31b` | 시지푸스, 프로메테우스, 메티스, 모무스 | ultrabrain, deep |
| ⚙️ Medium | `gemma4:26b` | 헤파이스토스, 아틀라스, 멀티모달 | artistry, writing, visual, high |
| ⚡ Light | `gemma4:e4b` | 오라클, 라이브러리안, 익스플로어 | quick, low |

### Phase 1: Agentis 환경 구축
```
배포 패키지 (zip/폴더)
├── opencode-dev/          # OpenCode 소스
├── oh-my-openagent-dev/   # OmO 소스
├── bootstrap.sh           # 자동 설치 스크립트
└── README.md              # 설치 가이드
```
- 배포 패키지를 사내 공유 → 대상 환경에 복사
- Agentis 환경 설치 (OpenCode + OmO)
- 로컬 LLM 엔드포인트 연결 설정

### Phase 2: 의존성 해결 (하네스적 접근)
- Node.js / Bun 설치 확인 및 해결
- Python 환경 확인
- 사내 프록시 설정
- 기타 시스템 의존성
- **오드리(Dr. Oh)로 환경 점검 자동화**

### Phase 3: 뀨리(GGuri) v1.0 배포 및 동작 확인
```
배포 패키지에 추가
├── gguri/                 # 뀨리 에이전트 (CLI)
│   ├── agent config
│   ├── prompts
│   └── tools (MCP 설정)
```
- 뀨리 설치
- **최초 동작 확인** ← 핵심 마일스톤
- 문서 자동화 기본 플로우 검증

### Phase 3.5: PydanticAI PoC (Phase 3과 병행 가능)
```
├── pydantic-poc/          # PydanticAI 실험
│   ├── simple_agent.py    # vLLM 연결 + 기본 도구 호출
│   ├── gguri_pydantic.py  # 뀨리 로직을 PydanticAI로 재구현
│   └── compare.md         # 하네스 vs PydanticAI 비교 결과
```

**PydanticAI는 Phase 3 이전에도 시작 가능합니다.**

이유:
- PydanticAI는 순수 Python + vLLM 엔드포인트만 있으면 동작
- OpenCode/OmO 설치 불필요 — Phase 0 완료 시점에 바로 실험 가능
- 오히려 빨리 해보면 뀨리 v2.0의 런타임을 PydanticAI로 할지 판단 근거가 됨

**추천 순서:**
```
Phase 0 (vLLM 확인)
    ├── Phase 1~2 (Agentis 구축)     ← 병렬 진행 가능
    └── Phase 3.5 (PydanticAI PoC)   ← 병렬 진행 가능
         │
Phase 3 (뀨리 v1.0 동작 확인)
         │
Phase 4 (비교 판단: 하네스 vs PydanticAI vs 하이브리드)
```

### Phase 4: 비교 및 방향 결정
- 뀨리 v1.0 (하네스) vs 뀨리 PydanticAI 버전 비교
- 판단 기준:
  - 도구 호출 안정성
  - 로컬 LLM 함수 콜링 품질
  - 에러 핸들링 / 타입 안전성
  - 배포 편의성
  - 사용자(비개발자) 접근성
- **결과에 따라 뀨리 2.0 런타임 결정**

### Phase 5: 진화
- 모델 교체/튜닝 (Gemma4 → 더 나은 모델, 또는 파인튜닝)
- 뀨리 2.0 (Phase 4 결과 반영)
- 추가 에이전트 개발 (Q&A, 보고서, 코드리뷰 등)
- RAG 인프라 구축 (벡터DB + 문맥 강화 인덱싱)
- **사용자 주도 진화** — 사용자가 직접 에이전트를 커스터마이징

---

## 4. 배포 방식

### 현재 방식: zip/폴더 배포 (Phase 1~3)
```
offcode-package.zip
├── opencode/              # OpenCode 바이너리 또는 소스
├── omo/                   # OmO 플러그인
├── gguri/                 # 뀨리 에이전트
├── audrey/                # 오드리 환경검사
├── bootstrap.sh           # 원클릭 설치
├── bootstrap.ps1          # Windows용
└── config-templates/      # vLLM 엔드포인트 등 설정 템플릿
```
- **장점**: 확실함. 사내망에서 가장 신뢰할 수 있는 방법
- **단점**: 업데이트 시 매번 재배포, 버전 관리 수동

### 대안 1: 단일 바이너리 배포 (추천 - Phase 5 이후)
```
offcode-linux-x64          # Bun compile 단일 실행파일
gguri-linux-x64            # PyInstaller 단일 실행파일
```
- OpenCode는 이미 `bun build --compile`로 플랫폼별 바이너리 생성 구조 있음
- Python 에이전트는 PyInstaller 또는 Nuitka로 단일 바이너리
- **장점**: Node/Bun/Python 설치 불필요. 복사 → 실행 끝
- **단점**: 빌드 파이프라인 구축 필요

### 대안 2: Docker 이미지 (인프라 허용 시)
```bash
# 외부에서 빌드
docker build -t offcode:1.0 .
docker save -o offcode-1.0.tar offcode:1.0

# 사내로 전달 후
docker load -i offcode-1.0.tar
docker run -it offcode:1.0 --env VLLM_ENDPOINT=http://internal:8000
```
- **장점**: 환경 재현 100%. 의존성 문제 원천 차단. 업데이트도 이미지 교체
- **단점**: 사내에 Docker/Podman 필요 (보통 개발 조직에는 있음)

### 대안 3: 사내 패키지 레지스트리 (장기)
```
[Verdaccio (npm)] + [PyPI Mirror]
     ↓
npm install -g offcode    # 사내 레지스트리에서
pip install gguri          # 사내 PyPI에서
```
- **장점**: `npm install`, `pip install` 그대로 사용. 버전 관리 자동
- **단점**: 초기 구축 비용 높음. IT 인프라 협조 필요

### 배포 방식 로드맵
```
Phase 1~3:  zip/폴더 배포 (빠르게 시작)
Phase 4~5:  단일 바이너리 배포 (의존성 제거)
장기:       Docker 이미지 또는 사내 레지스트리 (규모 확장 시)
```

---

## 5. 기술 스택 요약

| 레이어 | 기술 | 역할 |
|---|---|---|
| LLM 서빙 | Ollama (메인) / vLLM (백업) | Gemma4 31B/26B/E4B 서빙, OpenAI 호환 API |
| 코딩 에이전트 하네스 | OpenCode + OmO | 에이전트 빌더 (Agentis) |
| 업무 에이전트 런타임 | PydanticAI | 타입 안전 에이전트 실행 (Python) |
| 복잡 워크플로우 | LangGraph | 멀티스텝 상태머신 (필요시에만) |
| 도구 연결 | MCP 서버 | 메일, DB, 파일 등 표준 도구 연결 |
| 벡터DB | pgvector / Qdrant | 사내 지식 임베딩 저장 |
| 문서 처리 | Qwen-VL / Unstructured.io | 비정형 엑셀/PDF 멀티모달 처리 |
| 검색 | 하이브리드 (BM25+벡터) + 리랭킹 | 프로덕션급 검색 품질 |
| 환경 검사 | 오드리 (Dr. Oh) | Agentis 환경 자동 점검 |

---

## 6. 핵심 원칙

1. **Agentis는 만드는 도구, 만들어진 에이전트는 별도 런타임** — 하네스로 만들되, 돌아가는 건 PydanticAI/API 서버
2. **단순 RAG 금지** — 반드시 LLM 문맥 강화 + 하이브리드 검색 + 리랭킹 적용
3. **단계적 배포** — zip → 바이너리 → 컨테이너 순으로 성숙
4. **사용자 주도 진화** — 초기 환경과 첫 에이전트를 제공하면, 이후는 사용자가 발전시킴
5. **로컬 우선** — 모든 것이 사내망에서 완결. 외부 의존성 최소화

---

*문서 작성일: 2026-04-07*
*최종 업데이트: 2026-04-13 (Gemma4/Ollama 전환 반영)*
*프로젝트: Agentis (오프코드)*
