# Second Brain — 자기참조 에이전트 서브프로젝트

> 에이전트가 자기 자신을 인식하고, 세션을 넘어 기억·지식을 축적하는 구조를 연구하고 Agentis에 이식한다.

## 배경

2026-04-13 회장님 지시로 시작. 직접 계기는 코부장(Claude Code)이 본인이 돌아가는 환경을 "사내 데스크탑"으로 혼동한 사건. 현재 실행 환경은 VDI(10.44.33.205)지만, 이걸 매 세션 메모리로부터 복원하지 않으면 계속 틀린다. → **자기참조는 실전 문제**.

출발점: Karpathy 자기참조 gist — <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>

## 구조

```
Second_Brain/
├── README.md                    # 본 문서
├── PLAN.md                      # 울트라플랜 (단계별)
├── research/                    # 병렬 리서치 산출물
│   ├── karpathy_gist_analysis.md   # L1: Karpathy gist 원문 분석
│   ├── latest_methods_2026.md      # L2: 2025–2026 최신 방법론
│   └── application_cases.md        # L3: 실제 적용 사례
└── apply/                       # Agentis 적용 설계 (Phase 2 이후)
```

## 핵심 질문

1. 에이전트가 "자기 자신"을 안다는 것은 구체적으로 어떤 구조인가? (정체성 / 상태 / 히스토리 / 능력 인식)
2. 장기 기억(long-term memory)과 자기 참조(self-reference)의 차이와 경계는?
3. 기존 접근(MemGPT·Letta·A-MEM·Mem0·MIRIX·Claude Code auto memory)과 Karpathy 방식의 차이는?
4. Agentis의 시지푸스/프로메테우스/아틀라스 등이 각자 자기 역할·히스토리·능력을 인식하려면 어떻게 이식해야 하는가?
5. 로컬 LLM(Gemma4) + 폐쇄망 환경 제약 하에서 구현 가능한 최소 설계는?

## 원칙

- **자기참조는 문서가 아니라 프로토콜**: 읽히고, 갱신되고, 검증되어야 한다.
- **세션 경계를 넘는 기억**: 파일 기반(MEMORY.md) → 구조화 저장소 → 능동 재인덱싱으로 단계 확장.
- **로컬 우선**: 외부 API 의존 금지. Agentis 원칙과 일치.
- **최소 PoC 먼저**: 이론 과투자 금지. 1개 에이전트에 먼저 붙여 돌려본다.
