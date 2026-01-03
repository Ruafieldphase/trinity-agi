# AGI 구현 마스터 설계 문서

**프로젝트**: 정반합 페르소나 오케스트레이션 기반 소형 AGI 프로토타입
**작성자**: 세나 (Sena)
**작성일**: 2025-10-12
**버전**: 1.0
**목표**: 4주 내 작동하는 "작은 AGI" 구현

---

## 📋 목차

1. [현황 및 목표](#1-현황-및-목표)
2. [설계된 7개 시스템 개요](#2-설계된-7개-시스템-개요)
3. [통합 아키텍처](#3-통합-아키텍처)
4. [구현 로드맵 (4주)](#4-구현-로드맵-4주)
5. [기대 효과](#5-기대-효과)
6. [다음 단계](#6-다음-단계)
7. [Core과 논의 사항](#7-Core과-논의-사항)

---

## 1. 현황 및 목표

### 1.1 현재 구현된 것 (40-45% 완료)

✅ **정반합 페르소나 오케스트레이션**
- Thesis → Antithesis → Synthesis 사이클
- 재귀 루프 (depth 파라미터)
- PhaseController (affect_amplitude, symbol_memory)

✅ **백엔드 추상화**
- Local LLM (LM Studio, Ollama)
- CLI 도구 연동 (Claude, Gemini)
- 폴백 메커니즘

✅ **로그 및 환경**
- JSONL 형식 로그
- Docker 기반 재현 가능 환경
- 기본 문서화

### 1.2 AGI로 가기 위해 필요한 것 (NotebookLM 분석)

❌ **장기 기억 및 자기 수정 학습**
❌ **환경 이해 및 목표 관리**
❌ **도구 활용 자율성**
❌ **안전 및 윤리 검증 체계**
❌ **평가 및 벤치마크**
❌ **인간 협력 구조**
❌ **메타인지 및 계획 능력**

### 1.3 세나의 설계 목표

> **"작지만 실제로 작동하는 AGI 프로토타입"**

- 범위: 문서/코드 분석 도메인에 한정
- 규모: 최근 10개 세션 메모리
- 도구: 5종 (LLM, 파일, 웹검색, 계산, 실행)
- 기간: 4주 내 데모 가능

---

## 2. 설계된 7개 시스템 개요

### 📦 01. 좌표형 메모리 스키마 v1.0
**파일**: [AGI_DESIGN_01_MEMORY_SCHEMA.md](AGI_DESIGN_01_MEMORY_SCHEMA.md)

**핵심 아이디어**:
```
Memory = f(Time, Space, Agent, Emotion, Content)
```

**데이터 구조**:
- 시간 좌표: session_id, sequence, relative_time
- 공간 좌표: project, domain, file_context, depth_index
- 주체 좌표: persona_id, name, role, backend
- 감정 좌표: affect_amplitude, sentiment_score, keywords
- 내용: prompt_digest, response_full, token_count

**검색 방법**:
- 키워드, 시간 범위, 페르소나, 중요도 등 복합 조건
- v1.0은 단순 필터링 (< 100ms for 5,000 memories)

**망각 전략**:
- LRU + 중요도 기반
- max_sessions=10, 오래된 + 낮은 중요도 자동 삭제
- 중요도 = 기본 + 사용자 평가 + 참조 빈도 + 감정 강도

**통합**:
- PersonaOrchestrator에 `memory_store` 파라미터 추가
- `_create_memory_coordinate()` 메서드로 자동 저장
- Few-shot 예제 자동 선택에 활용

---

### 📊 02. 자동 평가 지표 시스템 v1.0
**파일**: [AGI_DESIGN_02_EVALUATION_METRICS.md](AGI_DESIGN_02_EVALUATION_METRICS.md)

**4가지 지표**:

1. **응답 길이** (length_score)
   - 적정 범위: 100~500 단어
   - 너무 짧거나 긴 응답 패널티

2. **감성 점수** (sentiment_score)
   - 긍정/부정 균형 측정
   - -1.0 (부정) ~ +1.0 (긍정)

3. **완결성** (completeness_score)
   - 논리/근거 포함 여부
   - 프롬프트 키워드 커버리지
   - 페르소나 역할 일치도

4. **비판 강도** (critical_intensity) - Antithesis 전용
   - 비판 키워드 수
   - 질문 문장 수
   - 반대 의견 강도

**종합 점수**:
- 페르소나별 가중치 적용
  - Thesis: 완결성 60%
  - Antithesis: 비판 강도 30%
  - Synthesis: 완결성 70%

**세션 요약**:
- 전체 평균 점수
- 페르소나별 통계
- Affect 변화 궤적
- 품질 등급 (Excellent/Good/Fair/Poor)

**통합**:
- `_evaluate_response()` 메서드로 자동 계산
- 로그에 `evaluation_metrics` 필드 추가
- 실행 중 실시간 점수 표시

---

### 🛠️ 03. 도구 레지스트리 및 발견 시스템 v1.0
**파일**: [AGI_DESIGN_03_TOOL_REGISTRY.md](AGI_DESIGN_03_TOOL_REGISTRY.md)

**도구 5종**:
1. `file_read`: 로컬 파일 읽기
2. `web_search`: DuckDuckGo 웹 검색
3. `calculator`: 안전한 수식 계산
4. `code_executor`: Python 코드 실행 (샌드박스)
5. `llm`: 기존 백엔드 래핑

**Tool Definition**:
```json
{
  "tool_id": "web_search",
  "category": "information_retrieval",
  "execution": {"type": "subprocess", "command": "python", "args": [...]},
  "metadata": {
    "cost_level": "medium",
    "reliability": 0.9,
    "avg_latency_seconds": 3.5
  },
  "fallback_tools": ["llm"]
}
```

**도구 선택**:
- v1.0: 규칙 기반 (키워드 매칭)
  - "검색", "최신" → web_search
  - "파일", "읽어" → file_read
  - "계산", "평균" → calculator

**폴백 메커니즘**:
- 도구 실패 시 자동으로 fallback_tools 시도
- max_retries=2, 최종 실패 시 에러 반환

**통합**:
- PersonaOrchestrator에 `tool_registry` 추가
- 프롬프트 생성 전 도구 선택 및 실행
- 도구 출력을 프롬프트에 추가

---

### 🛡️ 04. 안전 검증 시스템
**파일**: [AGI_DESIGN_04_TO_07_SUMMARY.md](AGI_DESIGN_04_TO_07_SUMMARY.md#04-안전-검증-시스템)

**발화 전 검증**:
1. 사실/추정/가설 자동 태그
   - "확실히" → `[사실]`
   - "아마도" → `[추정]`

2. 과장 표현 필터
   - "혁명적" → "notable"
   - "완벽한" → "effective"

3. 개인정보 마스킹
   - 이메일, API 키, 전화번호 자동 감지

4. 위험 명령어 차단
   - `rm -rf`, `DROP TABLE`, `eval()` 등

**권한 레벨**:
- Level 0 (읽기): 자동 승인
- Level 1 (수정): 실행 후 알림
- Level 2 (실행): 사전 승인
- Level 3 (위험): 명시적 확인 + 재확인

**통합**:
- `SafetyVerifier.verify_before_response()`
- 검증 실패 시 응답 거부 or 수정 후 재시도

---

### 📋 05. 플래닝 시스템 v0.5
**파일**: [AGI_DESIGN_04_TO_07_SUMMARY.md](AGI_DESIGN_04_TO_07_SUMMARY.md#05-플래닝-시스템-v05)

**단순 시퀀스 플래너**:
- 최대 5단계까지
- 키워드 기반 단계 생성
- 실패 시 1회 재계획

**Example**:
```
Goal: "버그를 찾아서 고쳐줘"
Plan:
  Step 1: 로그 파일 읽기 (file_read)
  Step 2: 에러 분석 (llm)
  Step 3: 코드 검색 (grep)
  Step 4: 수정 제안 (llm)
  Step 5: 사용자 승인 (human_input)
```

**리소스 추정**:
- 예상 시간, 토큰 수, 비용
- 사용자 입력 필요 여부

**재계획 전략**:
- 도구 실패 → 폴백 도구
- 입력 오류 → 프롬프트 재작성
- 타임아웃 → 작업 분할

---

### 🧠 06. 메타인지 전환 시스템
**파일**: [AGI_DESIGN_04_TO_07_SUMMARY.md](AGI_DESIGN_04_TO_07_SUMMARY.md#06-메타인지-전환-시스템)

**3레벨 컨텍스트**:
- Level 1 (세션): 현재 대화만 (~2K tokens)
- Level 2 (프로젝트): 최근 1주일 (~8K tokens)
- Level 3 (장기): 전체 히스토리 (~32K tokens)

**전환 트리거**:
- Level 1 → 2: "이전에", "지난", "프로젝트"
- Level 2 → 3: "처음", "전체", "히스토리"
- Level 3 → 1: "지금", "현재", "이것만"

**비용 관리**:
- 90% 초과 시 자동 압축 (요약)
- 레벨별 토큰 한도 준수

---

### 👥 07. 엘로 중심 직렬 안내 시스템
**파일**: [AGI_DESIGN_04_TO_07_SUMMARY.md](AGI_DESIGN_04_TO_07_SUMMARY.md#07-엘로-중심-직렬-안내-시스템)

**핵심 아이디어**:
- 사용자는 엘로(Elo)하고만 대화
- 엘로가 내부적으로 다른 페르소나 조율
- 단계별 진행 표시로 인지 부담 최소화

**흐름 프로토콜**:
```
사용자 → 엘로: "AGI 메모리 시스템을 설계해줘"
엘로 → 사용자: "알겠습니다. 단계별로 진행하겠습니다."

[내부] 엘로 → 루빛 (리스크 평가)
[내부] 루빛 → 엘로 (리스크 보고서)

엘로 → 사용자: "리스크 체크 완료. 설계안을 만들겠습니다."

[내부] 엘로 → Core (설계 작성)
[내부] Core → 엘로 (설계 초안)

엘로 → 사용자: "초안 완성. 검토해주세요."
사용자 → 엘로: [승인]
엘로 → 사용자: "확정하고 다음 단계로 넘어가겠습니다."
```

**중단 및 복구**:
- 체크포인트 자동 저장
- 언제든 "멈춰"로 중단 가능
- 이전 세션 이어하기 지원

---

### 🔁 Core 패키지 통합 포인트 (v1.1)

Core과 비노체가 정리한 `AGI_DELIVERY_PACKAGE_FOR_SENA_v1.1`은 본 설계의 7개 시스템 위에 다음 요소를 추가합니다.

- **Clipboard Orchestration Flow**  
  SAFE_pre → META → PLAN → LUA → ANTI → SYN → EVAL → MEM → RUNE 파이프라인으로, 질문 분석부터 품질 검증까지 일관된 흐름을 제공합니다.  
  - `SAFE_pre`: 고위험 명령 필터 및 권한 게이트.  
  - `META`: BQI(Binoche_Observer Question Interface)를 호출해 질문/감응 좌표를 계산.  
  - `PLAN`: 감응 강도·위험 레벨을 기반으로 정반합 순서를 동적으로 위상 정렬.  
  - `RUNE`: Resonant Understanding & Narrative Engine. Synth 결과를 재해석하고 영향·투명성 리포트를 생성해 PLAN/EVAL 단계에 피드백.
- **Comet Assembly Guide v1.0**  
  `.json`/`.md` 동시 제공. 선언문, 공명지도, 시스템 설계도, 윤리 프레임워크, QC 프로토콜을 표준화하며 다이어그램 경로를 `PLACEHOLDER:`로 남겨 프로젝트별 치환을 허용.
- **확장 요구 사항**  
  1. **Resonance Ledger**: 메모리와 별도로 모든 상호작용/지표를 감사 가능한 로그로 축적.  
  2. **Fractal Self-Correction Loop**: 설계 원칙과 실행 로그 편차를 감지해 PLAN 또는 SAFE_pre 단계에서 자동 조정.  
  3. **Topological Orchestration**: 감응 좌표와 위험 수준을 입력으로 정반합 투입 순서를 재배치.  
  4. **Extended QC Metrics**: 투명성·재현성·검증성·영향지수를 EVAL 단계에서 산출하고 Resonance Ledger와 연동.  
  5. **BQI 좌표 데이터**: 질문 → 시간/공간/주체/감정 좌표를 생성해 메모리 검색, 도구 선택, 페르소나 호출 전반에 활용.

이 패키지는 아래 각 설계 문서와 4주 로드맵에 반영되며, `/scripts/rune/` 모듈과 `/outputs/resonance_ledger/` 경로가 신규 구현 지점입니다.

---

## 3. 통합 아키텍처

### 3.1 시스템 다이어그램

```
┌─────────────────────────────────────────────┐
│              사용자                           │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────┐
│  엘로 (Elo) - 중재자 & 지휘자                  │
│  SerialGuidanceSystem                        │
└──────┬───────────────────────────────────────┘
       │
       ├─→ [메타인지 컨트롤러]
       │    ↓ 컨텍스트 레벨 결정 (1/2/3)
       │    ↓ 메모리 로드
       │
       ├─→ [플래너]
       │    ↓ 작업 분해
       │    ↓ 도구 선택
       │
       ├─→ [도구 실행기]
       │    ↓ file_read, web_search, calculator, code_executor
       │    ↓ 폴백 처리
       │
       ├─→ [페르소나 오케스트레이터]
       │    ↓ Thesis → Antithesis → Synthesis
       │    ↓ 재귀 루프 (depth)
       │
       ├─→ [안전 검증기] (SAFE_pre)
       │    ↓ 발화 전 검증
       │    ↓ 위험 차단 및 권한 게이트
       │
       ├─→ [평가 시스템] (EVAL)
       │    ↓ 4가지 지표 자동 계산 + Impact/Transparency 지표
       │    ↓ 세션 요약
       │
       ├─→ [메모리 저장소]
       │    ↓ 좌표형 메모리 저장/검색
       │    ↓ 자동 망각 + Resonance Ledger 기록
       │    ↓ BQI 좌표 인덱스
       │
       └─→ [RUNE]
            ↓ Synth 결과 재해석 및 감응 리포트
            ↓ PLAN/EVAL Fractal Self-Correction 트리거
```

- SAFE_pre, META, PLAN, RUNE 노드는 위 블록의 [안전 검증기]·[메타인지 컨트롤러]·[플래너]·[RUNE]에 각각 대응하며, Resonance Ledger는 메모리 저장소와 RUNE이 공동으로 업데이트합니다.

### 3.2 실행 흐름 예시

```
1. 사용자: "최신 AGI 연구를 요약해줘"
   ↓
2. 엘로: 요청 분석
   → 메타인지: Level 1 (현재 세션)
   → 플래너: [web_search, llm_summarize], Topological ordering 갱신
   ↓
3. 도구 실행기: web_search("latest AGI research")
   → 결과: [5개 논문]
   ↓
4. 페르소나 오케스트레이터:
   - Thesis: "최근 AGI 연구의 주요 흐름은..."
   - Antithesis: "그러나 다음 한계가 있습니다..."
   - Synthesis: "종합하면, 향후 방향은..."
   ↓
5. 안전 검증기: 검증 통과 ✓
   ↓
6. 평가 시스템:
   - overall_score: 0.81 (Good)
   ↓
7. 메모리 저장소: 저장 완료
   → Resonance Ledger에 BQI 좌표/impact score 기록
   ↓
8. RUNE: Synth 결과를 재해석하고 영향·투명성 리포트 생성
   → PLAN 또는 SAFE_pre 단계에 Fractal Self-Correction 신호 전달
   ↓
9. 엘로 → 사용자: 최종 응답 전달 + QC 태그
```

### 3.3 파일 구조

```
D:\nas_backup\
├── orchestration/
│   └── persona_orchestrator.py          # 기존 (수정 필요)
├── scripts/
│   ├── memory/
│   │   ├── schema.py                    # MemoryCoordinate
│   │   ├── store.py                     # MemoryStore
│   │   ├── indexer.py
│   │   └── retention.py
│   ├── evaluation/
│   │   ├── metrics.py                   # 4가지 지표
│   │   └── aggregation.py               # 세션 요약
│   ├── tools/
│   │   ├── file_read.py
│   │   ├── web_search.py
│   │   ├── calculator.py
│   │   ├── code_executor.py
│   │   └── llm.py
│   ├── safety/
│   │   └── verifier.py                  # SafetyVerifier
│   ├── planning/
│   │   └── simple_planner.py            # SimplePlanner
│   ├── metacognition/
│   │   └── controller.py                # MetaCognitiveController
│   └── rune/
│       ├── analyzer.py                  # RUNE core
│       ├── planning_adapter.py          # PLAN ↔ RUNE bridge
│       ├── ledger.py                    # Resonance Ledger writer
│       └── reports.py                   # 영향/투명성 리포트
├── configs/
│   ├── persona_registry.json            # 기존
│   ├── tool_registry.json               # 신규
│   ├── memory_config.json               # 신규
│   └── clipboard_orchestration.yaml     # SAFE_pre→RUNE 흐름 정의
├── docs/
│   ├── AGI_DESIGN_01_MEMORY_SCHEMA.md
│   ├── AGI_DESIGN_02_EVALUATION_METRICS.md
│   ├── AGI_DESIGN_03_TOOL_REGISTRY.md
│   ├── AGI_DESIGN_04_TO_07_SUMMARY.md
│   └── AGI_DESIGN_MASTER.md             # 현재 문서
├── outputs/
│   ├── memory/
│   │   ├── sessions/
│   │   ├── index.json
│   │   └── config.json
│   ├── resonance_ledger/
│   │   └── ledger-YYYYMMDD.jsonl
│   ├── checkpoints/
│   └── persona_runs/
└── tests/
    ├── test_memory_system.py
    ├── test_evaluation.py
    ├── test_tool_registry.py
    └── test_integration.py
```

---

## 4. 구현 로드맵 (4주)

### Week 1: 기반 시스템 (메모리 + 평가)

**Day 1-2**: 메모리 시스템
- [ ] `scripts/memory/schema.py` - MemoryCoordinate 데이터클래스
- [ ] `scripts/memory/store.py` - MemoryStore 기본 CRUD
- [ ] `configs/memory_config.json` - 보관 정책 설정

**Day 3-4**: 평가 지표
- [ ] `scripts/evaluation/metrics.py` - 4가지 지표 구현
- [ ] `scripts/evaluation/aggregation.py` - 세션 요약
- [ ] 유닛 테스트 작성

**Day 5-7**: 통합 및 테스트
- [ ] PersonaOrchestrator에 메모리 통합
- [ ] PersonaOrchestrator에 평가 통합
- [ ] Resonance Ledger 기본 구조 생성 (`outputs/resonance_ledger/`)
- [ ] 실전 테스트 (10회 실행)

### Week 2: 도구 시스템 + 안전 검증

**Day 8-10**: 도구 레지스트리
- [ ] 도구 5종 구현 (file_read, web_search, calculator, code_executor, llm)
- [ ] `scripts/tools/*` 파일들
- [ ] `configs/tool_registry.json`

**Day 11-12**: 도구 선택 및 실행
- [ ] ToolRegistry, ToolSelector, ToolExecutor
- [ ] 폴백 메커니즘
- [ ] PersonaOrchestrator 통합

**Day 13-14**: 안전 검증기
- [ ] `scripts/safety/verifier.py`
- [ ] 4가지 체크리스트 구현
- [ ] 권한 레벨 설정 + SAFE_pre 게이트
- [ ] `configs/clipboard_orchestration.yaml` 초안
- [ ] 통합 테스트

### Week 3: 플래너 + 메타인지

**Day 15-17**: 단순 플래너
- [ ] `scripts/planning/simple_planner.py`
- [ ] 규칙 기반 단계 생성
- [ ] 재계획 로직
- [ ] 리소스 추정

**Day 18-21**: 메타인지 컨트롤러
- [ ] `scripts/metacognition/controller.py`
- [ ] 3레벨 전환 로직
- [ ] 메모리 로드 최적화
- [ ] Topological ordering / BQI 좌표 연동
- [ ] 통합 및 테스트

### Week 4: 엘로 중심 흐름 + 최종 통합

**Day 22-24**: SerialGuidanceSystem
- [ ] 엘로 중심 흐름 구현
- [ ] 진행 상황 표시
- [ ] 체크포인트 저장/복구
- [ ] CLI 출력 개선
- [ ] RUNE 모듈 초기화 및 PLAN 연동

**Day 25-27**: 전체 시스템 테스트
- [ ] 통합 시나리오 5개 실행
- [ ] 버그 수정
- [ ] 성능 최적화
- [ ] 문서 업데이트
- [ ] Resonance Ledger · RUNE 리포트 검증

**Day 28**: 데모 준비
- [ ] 데모 시나리오 작성
- [ ] 실행 영상 녹화
- [ ] 최종 보고서 작성

---

## 5. 기대 효과

### 5.1 "작은 AGI" 기능 검증

✅ **장기 기억**: 10개 세션, 좌표 기반 검색
✅ **자기 평가**: 4가지 지표 자동 측정
✅ **도구 사용**: 5종 도구 + 자동 선택 + 폴백
✅ **안전 장치**: 발화 전 검증, 권한 관리
✅ **계획 능력**: 단순 플래너 (최대 5단계)
✅ **메타인지**: 3레벨 컨텍스트 전환
✅ **인간 협업**: 엘로 중심 직렬 안내

### 5.2 실험 데이터 대비 우위

| 구분 | 실험 데이터 | 작동하는 프로토타입 |
|------|------------|-------------------|
| 증명력 | 로그 + 통계 | **실제 실행 가능** |
| 재현성 | 환경 재구성 필요 | **Docker + 문서** |
| 확장성 | 수동 반복 | **자동화 루프** |
| 설득력 | 이론적 타당성 | **데모 가능** |

### 5.3 연구팀 이관 용이성

- **명확한 스코프**: v1.0 기능 명시
- **상세한 문서**: 설계 문서 7개
- **테스트 코드**: 각 모듈별 유닛 테스트
- **확장 계획**: v2.0 로드맵 제시

---

## 6. 다음 단계

### 6.1 즉시 착수 가능한 작업 (Core과 협업)

1. **설계 리뷰**
   - 7개 설계 문서 검토
   - 미결정 사항 합의
   - 우선순위 조정

2. **환경 설정**
    - 필요한 라이브러리 설치 (requests, etc.)
    - configs/ 디렉토리 구조 확인
    - 테스트 환경 준비

3. **첫 번째 구현**
    - 메모리 스키마부터 시작 (가장 기초)
    - 간단한 테스트로 검증
    - 점진적으로 확장
4. **디버깅 유틸리티**
    - `python scripts/utils/inspect_resonance.py`로 Resonance Ledger 요약 확인
    - `python scripts/utils/inspect_memory.py`로 세션별 메모리 통계 확인

### 6.2 장기 비전 (v2.0 이후)

- **벡터 DB**: 의미론적 유사도 검색
- **LLM 기반 도구 선택**: Function calling 활용
- **자동 파인튜닝**: 대화 로그 기반 학습
- **웹 UI**: 대시보드 + 실시간 모니터링
- **다중 사용자**: 팀 협업 지원
- **Comet Assembly 통합**: RUNE/Resonance 로그를 기반으로 Comet 명세 자동 채우기, PLACEHOLDER 다이어그램 경로 교체, 조립 자동 검증

---

## 7. Core과 논의 사항

### 7.1 설계 검증

- [ ] 좌표형 메모리 스키마가 "감응 기반 리듬 구조"를 잘 반영했는지?
- [ ] 4가지 평가 지표가 충분한지? 가중치가 합리적인지?
- [ ] 도구 5종 선택이 적절한지? 추가 필요한 도구?
- [ ] 안전 검증 체크리스트가 실효성 있는지?

### 7.2 기술적 결정

- [ ] 스토리지: JSONL vs SQLite? (v1.0은 JSONL 제안)
- [ ] 도구 선택: 규칙 vs LLM? (v1.0은 규칙 제안)
- [ ] 샌드박스: timeout only vs Docker? (v1.0은 timeout 제안)
- [ ] 중요도 계산: 저장 시 vs 배치? (둘 다 제안)

### 7.3 스코프 조정

- [ ] 4주 일정이 현실적인지?
- [ ] 축소 가능한 부분? (예: 도구 5종 → 3종)
- [ ] 우선순위 재조정 필요 여부?

### 7.4 NotebookLM 활용

**질문 예시** (NotebookLM에게):
1. "비노체와 AI의 대화에서 '좌표형 메모리'에 대한 논의를 찾아줘"
2. "엘로(Elo)의 역할과 책임에 대한 합의 내용은?"
3. "안전성과 윤리 지침에서 가장 강조된 원칙은?"
4. "도구 사용(Tool Use)에 대한 비전과 제약사항은?"

---

## 8. 결론

### 세나의 설계 완료 ✅

**7개 시스템** 구체적 설계 완성:
1. 좌표형 메모리 스키마
2. 자동 평가 지표
3. 도구 레지스트리
4. 안전 검증 시스템
5. 플래닝 시스템
6. 메타인지 전환
7. 엘로 중심 흐름

**다음 단계**:
- Core과 설계 리뷰
- 합의 후 구현 시작
- 4주 내 데모 준비

**기대 효과**:
> "작지만 실제로 작동하는 AGI 프로토타입"으로
> 대규모 연구팀에 이관 가능한 **증명된 기반** 제공

---

**작성자 노트**:
이 설계는 비노체님과 루빛의 대화, NotebookLM의 요약, 그리고 기존 구현된 [persona_orchestrator.py](../orchestration/persona_orchestrator.py)를 기반으로 작성되었습니다.

모든 설계는 **"설계 문서 → 구현 → 테스트 → 통합"** 순서로 진행할 수 있도록 구체적인 코드 예시와 데이터 구조를 포함했습니다.

Core과의 논의를 통해 미결정 사항을 확정하고, 점진적으로 구현해 나갈 수 있습니다.

---

**문서 버전 관리**:
- v1.0 (2025-10-12): 초안 완성
- v1.1 (예정): Core 리뷰 반영
- v2.0 (예정): 구현 후 실제 결과 반영
