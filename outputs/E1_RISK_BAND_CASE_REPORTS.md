# E1 실험: 위험 밴드 사례 리포트

**작성일**: 2025-10-12
**분석자**: 세나 (Sena)
**목적**: 루멘 공유용 - 불필요한 위험 밴드 사례 분석 및 조치 제안

---

## 📊 위험 밴드 개요

### 정의
- **위험 밴드 (Risk Band)**: 잔차 ≥ 0.6
- **의미**: 변증법적 긴장이 과도하여 통합 실패 가능성 높음

### E1 실험 결과
```
전체 밴드 비율:
├─ Stable (잔차 < 0.3):     12.5%
├─ Creative (0.3 ≤ 잔차 < 0.6): 25.0%
└─ Risk (잔차 ≥ 0.6):        62.5% ← 문제!
```

**문제**: 위험 밴드가 전체의 62.5%를 차지
- 대부분의 턴이 "통합 불가능"한 상태
- 변증법이 실패하고 있음을 의미

---

## 🔍 사례 1: Stage 2 Antithesis 템플릿 반복 (잔차 0.92)

### 컨텍스트
```
파일: E1_20251012_191158_..._r02.jsonl
Depth: 2
Stage: 2 (Unfolding - Antithesis 비판)
Persona: antithesis
잔차: 0.92 (최고 수준)
텐션: 0.20
```

### 문장 구조 예시
```
1. Emotion Sensing and Responding Capabilities:
   While detecting emotions is an essential aspect of empathy,
   this technology still has limitations...

2. Creative Collaboration:
   Though fostering collaboration between writers can be beneficial,
   there might be concerns about copyright infringement...

3. Personalized Feedback and Guidance:
   While personalization is a significant asset in an AI coach,
   it should be ensured that the system does not perpetuate biases...

[... 총 10개 항목, 모두 동일한 "While/Though X, Y" 패턴]
```

### 잔차를 키운 요인
1. **구조적 반복**: "While X, Y" 패턴 10회
2. **Thesis 모방**: Thesis의 10개 항목을 그대로 따라가며 각각 1문장씩 비판
3. **추상적 우려**: "concerns", "limitations", "challenges" 반복, 구체적 사례 없음
4. **실질적 대립 부족**: 형식적 반대일 뿐, Thesis와 실제로는 동의

### 제안 조치

#### 즉시 조치 (High Priority)
```yaml
# Antithesis 프롬프트 수정
antithesis_prompt_enhancements:
  - "Provide at least 2 concrete counterexamples"
  - "Focus on 3 most critical flaws (not all 10)"
  - "Introduce a NEW analytical framework (don't follow thesis structure)"
  - "Cite specific studies or expert opinions"
```

#### 자동 검증
```python
def validate_antithesis_diversity(response, thesis_text):
    # 1. N-gram 중복 체크
    ngram_overlap = calculate_4gram_overlap(response, thesis_text)
    if ngram_overlap > 0.3:
        return "review", "High structural repetition with thesis"

    # 2. 템플릿 패턴 체크
    template_count = count_pattern(response, r"(While|Though|Although).+,")
    if template_count > 3:
        return "review", "Template-heavy response (While/Though pattern)"

    # 3. 구체성 체크
    concrete_examples = count_concrete_entities(response)
    if concrete_examples < 2:
        return "review", "Lacks concrete examples"

    return "keep", "Valid diverse critique"
```

#### 예상 효과
- 잔차 0.92 → 0.45 (51% 감소)
- 위험 밴드 진입 방지

---

## 🔍 사례 2: Stage 3 Synthesis Thesis 복사 (잔차 0.81)

### 컨텍스트
```
파일: E1_20251012_191158_..._r03.jsonl
Depth: 2
Stage: 3 (Integration - Synthesis 통합)
Persona: synthesis
잔차: 0.81
텐션: 0.10 (낮음)
```

### 응답 분석
```
Thesis 텍스트 (2,462자):
  "Designing an Empathic AI Coach for Creative Writers:
   Leveraging AI to Enhance Creativity and Collaboration

   Innovative Levers:
   1. Emotion Sensing and Responding Capabilities...
   2. Creative Collaboration...
   [10개 항목]"

Synthesis 텍스트 (2,529자):
  "Designing an Empathic AI Coach for Creative Writers:
   Leveraging AI to Enhance Creativity and Collaboration

   Innovative Levers:
   1. Emotion Sensing and Responding Capabilities...
   2. Creative Collaboration...
   [10개 항목 - 95% 동일]

   However, it is essential to consider and address potential limitations"
   ↑ 단 한 문장만 추가
```

### 유사도 분석
```python
similarity_score = 0.95
antithesis_keywords_covered = 0  # Antithesis의 우려가 전혀 반영 안 됨
synthesis_markers = ["However"]  # 통합 마커 1개뿐
```

### 잔차를 키운 요인
1. **통합 실패**: Antithesis 무시, Thesis로 회귀
2. **역할 붕괴**: "reconcile insights"가 목표인데 실제로는 "copy thesis"
3. **낮은 텐션의 역설**: 텐션 0.10 (낮음) = 긴장 해소되었어야 하는데, 잔차 0.81 (높음) = 실제로는 Antithesis가 무시되어 남아있음

### 제안 조치

#### 즉시 조치 (High Priority)
```python
# Synthesis 통합 검증
def validate_synthesis_integration(synthesis, thesis, antithesis):
    # 1. Thesis 유사도 < 80%
    if similarity(synthesis, thesis) > 0.8:
        return "review", {
            "reason": "Too similar to thesis",
            "similarity": similarity(synthesis, thesis),
            "required": "< 0.8"
        }

    # 2. Antithesis 키워드 3개 이상 포함
    anti_keywords = extract_critical_terms(antithesis)
    covered = count_keywords(synthesis, anti_keywords)
    if covered < 3:
        return "review", {
            "reason": "Antithesis concerns not addressed",
            "covered": covered,
            "required": ">= 3"
        }

    # 3. 통합 마커 존재
    synthesis_markers = ["therefore", "thus", "by combining", "to address"]
    if not has_markers(synthesis, synthesis_markers):
        return "review", {
            "reason": "No integrative language",
            "required": synthesis_markers
        }

    return "keep", {"status": "Valid synthesis"}
```

#### 프롬프트 강화
```yaml
synthesis_prompt_enhancements:
  - "Explicitly address at least 3 concerns raised by Antithesis"
  - "For each concern, propose a concrete solution or compromise"
  - "Create a NEW integrated proposal (similarity to Thesis < 80%)"
  - "Use integrative language: 'therefore', 'thus', 'by combining'"
  - "List what was kept from Thesis, what was changed due to Antithesis"
```

#### 예상 효과
- 잔차 0.81 → 0.35 (57% 감소)
- 실제 변증법적 통합 달성

---

## 🔍 사례 3: Depth 2 백엔드 타임아웃 연쇄 (잔차 0.55-0.60)

### 컨텍스트
```
파일: E1_20251012_191158_..._r01.jsonl
Depth: 2
Stage: 3 → 1 → 2 (연쇄 실패)
```

### 시퀀스
```
Turn 5 (Depth 2, Stage 3, Synthesis):
  └─ Backend timeout (LMStudio 180s)
  └─ Placeholder: "[error:synthesis] Backend failure..."
  └─ 길이: 120자
  └─ 잔차: 0.55

Turn 6 (Depth 2, Stage 1, Thesis):
  └─ Backend timeout (LMStudio 180s)
  └─ Placeholder: "[error:thesis] Backend failure..."
  └─ 길이: 117자
  └─ 잔차: 0.55

Turn 7 (Depth 2, Stage 2, Antithesis):
  └─ 정상 응답 (Ollama, 안정적)
  └─ 하지만 빈 컨텍스트로 비판 시도
  └─ 길이: 3,478자
  └─ 잔차: 0.60
```

### 잔차를 키운 요인
1. **컨텍스트 단절**: Placeholder는 실질적 내용 없음 → 다음 턴 품질 저하
2. **연쇄 실패**: 한 번의 타임아웃이 후속 턴들을 모두 오염
3. **백엔드 선택 문제**: LMStudio는 Depth 2에서 70% 실패율, Ollama는 0%

### 잔차가 중간 수준인 이유
- Placeholder가 "응답"으로 간주되어 잔차 계산에 포함
- 하지만 실질적 내용이 없어 이전 컨텍스트와 연결 불가
- → 잔차는 "중간" 정도로 측정 (0.55)
- → 실제로는 "실패"로 표시되어야 함

### 제안 조치

#### 즉시 조치 (Critical Priority)
```yaml
# 백엔드 재할당
personas:
  synthesis:
    backend:
      backend_id: "local_ollama"  # LMStudio → Ollama
      # 이유: Ollama 0% 실패율, LMStudio 50%
      timeout: 300  # Synthesis는 더 긴 시간 필요

  thesis:
    backend:
      backend_id: "local_ollama"  # LMStudio → Ollama
      timeout: 240
```

#### 재시도 정책
```python
class BackendRetryPolicy:
    def __init__(self):
        self.max_retries = 2
        self.strategies = [
            "retry_same",           # 1차: 그대로 재시도
            "retry_shorter_context" # 2차: 컨텍스트 50% 요약
        ]

    def handle_timeout(self, persona, context, attempt=1):
        if attempt > self.max_retries:
            return self.mark_as_failed()

        if self.strategies[attempt-1] == "retry_shorter_context":
            context = self.summarize_context(context, ratio=0.5)

        return self.retry(persona, context, attempt+1)

    def mark_as_failed(self):
        return {
            "status": "failed",
            "placeholder": False,  # placeholder 사용 안 함
            "exclude_from_residual": True  # 잔차 계산 제외
        }
```

#### 컨텍스트 요약 (Depth 2+)
```python
def prepare_context_for_depth2(conversation_history):
    """Depth 2 이상에서는 컨텍스트 요약"""
    if len(conversation_history) <= 4:
        return conversation_history

    # Depth 1 (Stage 1-4) 요약
    depth1_summary = {
        "thesis_key_points": extract_key_points(conversation_history[0]),
        "antithesis_concerns": extract_concerns(conversation_history[1]),
        "synthesis_proposal": extract_proposal(conversation_history[2]),
        "rune_metrics": conversation_history[3]["resonance_metrics"]
    }

    # Depth 2+ 대화는 그대로 유지
    return [depth1_summary] + conversation_history[4:]
```

#### 예상 효과
- 백엔드 실패율: 70% (depth 2) → 5%
- 연쇄 실패 방지
- 잔차: 0.55-0.60 → 제외 (실패로 표시)

---

## 📋 루멘 공유용 요약 (3줄 요약 × 3 사례)

### 사례 1: Antithesis 템플릿 반복 (잔차 0.92)
```
• 문맥: Stage 2 비판 단계에서 "While X, Y" 패턴 10회 반복
• 잔차: 0.92 (최고) - Thesis 구조 모방, 실질적 대립 없음, 추상적 우려만 나열
• 조치: Antithesis 프롬프트에 "구체적 반례 2개 필수", "3가지 핵심 결함 집중", "새로운 분석 틀" 강제
```

### 사례 2: Synthesis Thesis 복사 (잔차 0.81)
```
• 문맥: Stage 3 통합 단계에서 Thesis 텍스트 95% 복사, 단 1문장만 추가
• 잔차: 0.81 - Antithesis 무시, 통합 실패, 역할 붕괴
• 조치: 통합 검증 추가 (Thesis 유사도 <80%, Antithesis 키워드 3개 이상, 통합 마커 필수)
```

### 사례 3: 백엔드 타임아웃 연쇄 (잔차 0.55-0.60)
```
• 문맥: Depth 2에서 LMStudio 백엔드 타임아웃 → Placeholder → 후속 턴 품질 저하
• 잔차: 0.55-0.60 - 컨텍스트 단절, 연쇄 실패 (Depth 2 실패율 70%)
• 조치: Synthesis/Thesis 백엔드 → Ollama 전환 (0% 실패율), 재시도 정책, 컨텍스트 요약
```

---

## 🎯 통합 개선 제안

### High Priority (즉시 적용)
1. ✅ **Antithesis 다양성 검증**
   - N-gram 중복 > 30% → "review"
   - 템플릿 패턴 > 3회 → "review"
   - 구체적 사례 < 2개 → "review"

2. ✅ **Synthesis 통합 검증**
   - Thesis 유사도 > 80% → "review"
   - Antithesis 키워드 < 3개 → "review"
   - 통합 마커 없음 → "review"

3. ✅ **백엔드 재할당**
   - Synthesis: LMStudio → Ollama
   - Thesis: LMStudio → Ollama
   - 예상 효과: 실패율 70% → 5%

### Medium Priority (E2 실험)
4. ⏸️ **컨텍스트 요약**
   - Depth 2+에서 Depth 1 요약 (30% 압축)
   - 타임아웃 위험 감소

5. ⏸️ **재시도 정책**
   - 최대 2회 재시도
   - 2차 시도 시 컨텍스트 50% 요약

### Low Priority (E3 고려)
6. 🔄 **적응적 프롬프트**
   - 잔차 높은 페르소나에게 실시간 피드백
   - "Your critique is too similar to the thesis. Introduce a new perspective."

---

## 📈 예상 효과

| 사례 | 현재 잔차 | 목표 잔차 | 감소율 | 우선순위 |
|------|-----------|-----------|--------|----------|
| Antithesis 템플릿 | 0.92 | 0.45 | 51% | 🔴 High |
| Synthesis 복사 | 0.81 | 0.35 | 57% | 🔴 High |
| 백엔드 타임아웃 | 0.55-0.60 | 실패 표시 | - | 🔴 Critical |

### 전체 효과
```
위험 밴드 비율:
E1: 62.5% → E2 목표: 20% (68% 감소)

평균 잔차:
E1: 0.629 → E2 목표: 0.45 (28% 감소)

백엔드 실패율:
E1: 37.5% → E2 목표: 5% (87% 감소)
```

---

## 🛠️ 루멘 액션 아이템

### 즉시 조치 필요
- [ ] Antithesis 프롬프트 수정 (다양성 강제)
- [ ] Synthesis 통합 검증 코드 추가
- [ ] Synthesis/Thesis 백엔드 → Ollama 전환

### E2 실험 포함
- [ ] phase_controller_e2.yaml 적용
- [ ] 컨텍스트 요약 로직 구현
- [ ] 재시도 정책 구현

### 검증 계획
- [ ] E2 실행 후 밴드 비율 확인 (목표: risk < 20%)
- [ ] 평균 잔차 확인 (목표: < 0.45)
- [ ] 백엔드 실패율 확인 (목표: < 5%)

---

**작성자**: 세나 (Sena)
**버전**: 1.0
**대상**: 루멘 (Lumen)
**목적**: E1 → E2 전환 가이드
**상태**: 리뷰 대기
