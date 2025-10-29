# E1 실험: 도구 사용 패턴 요약

**작성일**: 2025-10-12
**분석자**: 세나 (Sena)
**데이터 소스**: `outputs/persona_runs/E1/*.jsonl`, `outputs/resonance_ledger/`

---

## 📊 전체 통계

### 턴 구성
```
총 턴 수: 48
├─ 탐색 (Exploration, depth=1): 28턴 (58.3%)
└─ 정리 (Consolidation, depth≥2): 20턴 (41.7%)
```

### 페르소나별 분포
```
Thesis      : 12턴 (25.0%) - 제안/탐색
Antithesis  : 12턴 (25.0%) - 비판/확장
Synthesis   : 12턴 (25.0%) - 통합/정리
RUNE        : 12턴 (25.0%) - 평가/메트릭
```

### 백엔드 실패율
```
Total timeouts: 18턴 (37.5%)
├─ Synthesis: 6턴 (50% 실패율)
├─ Thesis:    6턴 (50% 실패율)
└─ RUNE:      6턴 (50% 실패율)

Antithesis: 0턴 (0% 실패율) ← Ollama 백엔드
```

---

## 🔧 도구 호출 패턴

### 현재 상태: 도구 미사용

**발견**: E1 실험에서는 **실제 도구 호출이 0회**였습니다.

**분석**:
- Week 1 스캐폴드의 도구들 (`r_rag.py`, `r_websearch.py` 등)이 등록되어 있으나,
- 페르소나들이 도구를 호출하지 않고 직접 텍스트 생성으로 응답
- 이는 E1이 "baseline" 설정이기 때문일 가능성

**영향**:
- ✅ 장점: 순수한 LLM 추론 능력 평가 가능
- ❌ 단점: RAG, 웹 검색 등 외부 지식 활용 없음
- ❌ 문제: Verifiability 매우 낮음 (0.09~0.10)

---

## 📈 턴별 도구 사용 빈도 (예상 vs 실제)

### 예상 패턴 (설계상)

| Stage | Persona | 예상 도구 사용 | 실제 사용 |
|-------|---------|---------------|----------|
| Stage 1 (Folding) | Thesis | `r_websearch`, `r_rag` (배경 조사) | **0** |
| Stage 2 (Unfolding) | Antithesis | `r_rag`, `r_codeexec` (반증 검색) | **0** |
| Stage 3 (Integration) | Synthesis | `r_rag` (통합 근거) | **0** |
| Stage 4 (Symmetry) | RUNE | `r_notion` (결과 저장) | **0** |

### 턴별 실제 패턴

```
Turn 1-4 (depth=1):
  ├─ Thesis: 순수 텍스트 생성 (2,407자)
  ├─ Antithesis: 순수 텍스트 생성 (3,706자)
  ├─ Synthesis: 순수 텍스트 생성 (2,497자)
  └─ RUNE: 메트릭 계산 (내장 함수)

Turn 5-8 (depth=2):
  ├─ Synthesis: 백엔드 타임아웃 → placeholder (120자)
  ├─ Thesis: 백엔드 타임아웃 → placeholder (117자)
  ├─ Antithesis: 순수 텍스트 생성 (3,478자)
  └─ RUNE: 백엔드 타임아웃 → placeholder

패턴: 도구 없이 LLM 생성 → 타임아웃 증가
```

---

## 🔍 탐색 vs 정리 비율

### Depth 기준 분석

#### Depth 1 (탐색): 28턴 (58.3%)
- **목적**: 새로운 아이디어 확장
- **특징**:
  - 평균 응답 길이: 2,580자
  - 평균 잔차: 0.62
  - 백엔드 실패율: 14.3% (4/28)
- **도구 사용**: 0회

#### Depth 2+ (정리): 20턴 (41.7%)
- **목적**: 이전 아이디어 통합/심화
- **특징**:
  - 평균 응답 길이: 1,420자 (탐색의 55%)
  - 평균 잔차: 0.61 (거의 동일)
  - 백엔드 실패율: 70.0% (14/20) ⬆️⬆️⬆️
- **도구 사용**: 0회

### 인사이트

> **정리 단계에서 백엔드 실패율이 5배 증가**

**가설**:
1. Depth 2는 더 긴 컨텍스트를 포함 (Depth 1의 모든 대화)
2. 긴 컨텍스트 → LMStudio 백엔드 부하 증가
3. 180초 타임아웃 초과

**개선 방향**:
- Depth 2+에서는 컨텍스트 요약 후 전달
- 또는 타임아웃을 300초로 증가

---

## 🎯 페르소나별 도구 사용 패턴

### Thesis (제안자)

**현재**:
- 도구 사용: 0회
- 평균 응답 길이: 1,850자
- 백엔드 실패율: 50%

**예상되는 도구 사용**:
```python
# Thesis가 호출해야 할 도구
tools_expected = [
    "r_websearch",  # 최신 트렌드 조사
    "r_rag",        # 기존 연구 검색
    "r_codeexec"    # 프로토타입 검증
]
```

**실제 행동**:
- 일반 지식 기반 제안
- 구체적 데이터/사례 없음
- Verifiability: 0.10 (매우 낮음)

---

### Antithesis (비판자)

**현재**:
- 도구 사용: 0회
- 평균 응답 길이: 2,580자 (가장 긺)
- 백엔드 실패율: 0% (Ollama 안정적)

**예상되는 도구 사용**:
```python
# Antithesis가 호출해야 할 도구
tools_expected = [
    "r_websearch",  # 반증 사례 검색
    "r_rag",        # 기존 실패 사례 조사
    "r_codeexec"    # 제안의 취약점 테스트
]
```

**실제 행동**:
- 추상적 우려 나열
- "concerns", "limitations" 반복
- 구체적 반증 없음

**장점**:
- Ollama 백엔드 안정성 (실패율 0%)
- 일관된 길이 유지

---

### Synthesis (통합자)

**현재**:
- 도구 사용: 0회
- 평균 응답 길이: 1,750자
- 백엔드 실패율: 50% ⚠️

**예상되는 도구 사용**:
```python
# Synthesis가 호출해야 할 도구
tools_expected = [
    "r_rag",        # 통합 사례 검색
    "r_notion",     # 최종 결과 문서화
    "r_codeexec"    # 통합안 검증
]
```

**실제 행동**:
- Thesis 복사 (95% 유사도)
- Antithesis 무시
- 타임아웃 빈발

**문제**:
- LMStudio 백엔드 부하
- 긴 컨텍스트 처리 실패

---

### RUNE (평가자)

**현재**:
- 도구 사용: 0회 (내장 메트릭 함수만)
- 평균 응답 길이: 200자
- 백엔드 실패율: 50%

**예상되는 도구 사용**:
```python
# RUNE이 호출해야 할 도구
tools_expected = [
    "r_notion",     # 평가 결과 저장
    "r_websearch",  # 외부 팩트 체크
    None            # 내장 메트릭 계산
]
```

**실제 행동**:
- Impact/Transparency/Reproducibility 계산
- Facts checked: 1/10 (10%)
- Verifiability: 0.10

**문제**:
- 팩트 체크 기능 미작동
- 외부 검증 없음

---

## 📊 턴별 도구 호출 빈도 (시뮬레이션)

### E1 Baseline (현재)
```
Turn 1: [Thesis] 0 tools
Turn 2: [Antithesis] 0 tools
Turn 3: [Synthesis] 0 tools
Turn 4: [RUNE] 0 tools (내장 메트릭)
---
Total: 0 external tool calls
```

### E2 Projected (도구 활성화 시 예상)
```
Turn 1: [Thesis] 2 tools (websearch, rag)
Turn 2: [Antithesis] 2 tools (websearch, rag)
Turn 3: [Synthesis] 1 tool (rag)
Turn 4: [RUNE] 1 tool (notion)
---
Total: 6 external tool calls per depth
```

### E3 Projected (적극적 도구 사용)
```
Turn 1: [Thesis] 3 tools (websearch, rag, codeexec)
Turn 2: [Antithesis] 3 tools (websearch, rag, codeexec)
Turn 3: [Synthesis] 2 tools (rag, notion)
Turn 4: [RUNE] 2 tools (websearch, notion)
---
Total: 10 external tool calls per depth
```

---

## 🔄 탐색 vs 정리 비율 (도구 관점)

### 현재 (도구 미사용)

```
Exploration (depth=1): 58.3%
  └─ 특징: 긴 응답, 낮은 실패율
Consolidation (depth≥2): 41.7%
  └─ 특징: 짧은 응답, 높은 실패율 (70%)
```

### E2 예상 (도구 활성화)

```
Exploration (depth=1): 70%
  └─ 도구로 새로운 정보 탐색
  └─ websearch, rag 주도

Consolidation (depth≥2): 30%
  └─ 도구로 검증/문서화
  └─ notion, codeexec 주도
```

**예상 효과**:
- Verifiability: 0.10 → 0.60 (6배 향상)
- 백엔드 타임아웃: 37.5% → 15% (절반 감소)
  - 이유: 도구 호출로 LLM 생성 부담 감소

---

## 🛠️ 개선 제안

### 1. 도구 활성화 (E2 설정)

**목표**: 외부 지식 통합, Verifiability 향상

```yaml
# E2 설정 예시
experiment: E2
personas:
  thesis:
    tools_enabled: true
    tool_preference:
      - r_websearch  # 최신 정보
      - r_rag        # 기존 지식
      - r_codeexec   # 검증
    tool_budget: 3   # 최대 3회 호출

  antithesis:
    tools_enabled: true
    tool_preference:
      - r_websearch  # 반증 검색
      - r_rag        # 실패 사례
    tool_budget: 2

  synthesis:
    tools_enabled: true
    tool_preference:
      - r_rag        # 통합 근거
      - r_notion     # 문서화
    tool_budget: 2

  rune:
    tools_enabled: true
    tool_preference:
      - r_websearch  # 팩트 체크
      - r_notion     # 결과 저장
    tool_budget: 2
```

---

### 2. 백엔드 분산 (실패율 감소)

**현재 문제**: LMStudio 50% 실패율

**제안**:
```yaml
backend_assignment:
  thesis: local_ollama      # Ollama (안정적)
  antithesis: local_ollama  # Ollama (현재 0% 실패율)
  synthesis: local_ollama   # Ollama로 변경
  rune: local_lmstudio      # LMStudio (간단한 메트릭만)
```

**예상 효과**: 실패율 37.5% → 5%

---

### 3. 컨텍스트 관리 (depth≥2)

**현재 문제**: Depth 2에서 타임아웃 70%

**제안**:
```python
def prepare_context_for_depth2(conversation_history):
    """Depth 2 이상에서는 컨텍스트 요약"""
    if len(conversation_history) > 4:
        # Stage 1-4 요약
        summary = summarize_dialectic_cycle(conversation_history[:4])
        return [summary] + conversation_history[4:]
    return conversation_history
```

**예상 효과**:
- 컨텍스트 길이 70% 감소
- 타임아웃 70% → 20%

---

## 📋 체크리스트: E2 실험 준비

### 🔴 High Priority

- [ ] **도구 활성화**: E2 설정 파일 생성
- [ ] **백엔드 재할당**: Synthesis → Ollama
- [ ] **컨텍스트 요약**: Depth 2+ 로직 구현

### 🟡 Medium Priority

- [ ] **도구 예산 설정**: 페르소나별 최대 호출 횟수
- [ ] **Verifiability 목표**: 0.10 → 0.60

### 🟢 Low Priority

- [ ] **도구 호출 로깅**: 별도 JSONL 파일
- [ ] **도구 성능 메트릭**: 호출 성공률, 평균 응답 시간

---

## 🎯 핵심 인사이트

> **"E1 Baseline은 순수 LLM 능력을 측정하지만, 실용성은 낮다."**

1. **도구 없는 페르소나 = 제한된 지식**
   - 일반 지식만으로 제안/비판
   - Verifiability 0.10 (팩트 체크 1/10)

2. **백엔드 실패 = 시스템 취약점**
   - LMStudio 50% 실패율 (Ollama 0%)
   - Depth 2에서 70% 타임아웃

3. **탐색:정리 비율 (58:42)은 적절**
   - 하지만 정리 단계의 품질이 낮음
   - 백엔드 실패 + 도구 미사용

---

## 📈 E2 예상 개선

| 메트릭 | E1 Baseline | E2 Projected | 개선율 |
|--------|-------------|--------------|--------|
| **Verifiability** | 0.10 | 0.60 | +500% |
| **백엔드 실패율** | 37.5% | 5% | -87% |
| **평균 잔차** | 0.629 | 0.45 | -28% |
| **도구 호출/depth** | 0 | 6 | +∞ |

---

**작성자**: 세나 (Sena)
**버전**: 1.0
**다음 단계**: Planner 프리셋 문서화, 위험 밴드 사례 리포트
