# E2 실패 분석 및 E2.5 계획

**작성일**: 2025-10-12
**작성자**: 세나 (Sena) + 루빛 (Lubit) 분석 통합
**상태**: CRITICAL - 즉시 조치 필요

---

## 🚨 E2 실험 실패 확인

### 실험 결과 요약
```
E2 실행: 성공
로그 생성: 4개 세션 완료
메트릭 분석: 완료

하지만...
```

### 치명적 문제

| 메트릭 | E1 Baseline | E2 목표 | E2 실제 | 상태 |
|--------|-------------|---------|---------|------|
| **Stage 3 잔차** | 0.390 | 0.35 | **0.875** | ❌ +124% |
| **Risk 밴드** | 62.5% | 20% | **100%** | ❌ +60% |
| **Creative 밴드** | 25% | 60% | **0%** | ❌ -100% |
| **Stable 밴드** | 12.5% | 20% | **0%** | ❌ -100% |

**결론**: E2는 E1보다 **더 나빠졌습니다**.

---

## 🔍 실패 원인 분석

### 1. 설정만 바꾸고 코드는 그대로

**phase_controller_e2.yaml**에는 멋진 설정이 가득:
```yaml
synthesis:
  tools:
    enabled: true
    budget: 2
    preference:
      - r_rag
      - r_notion

  integration_validation:
    enabled: true
    max_thesis_similarity: 0.8
    min_antithesis_keywords: 3

  backend_retry:
    enabled: true
    max_retries: 2
```

**하지만 실제 코드**:
```python
# personas/synthesis.py (현재)
def generate_response(self, prompt):
    return self.backend.call(prompt)  # ← 도구 호출 없음!
```

**결과**: 설정은 무시되고, LLM이 프롬프트만 보고 응답

---

### 2. PhaseController가 실제로 제어하지 않음

**E2 설정**:
```yaml
symmetry:
  stage_3_integration:
    target_residual: 0.35
    decision_threshold:
      keep: 0.4
      review: 0.8

    integration_checks:
      - type: "thesis_similarity"
        max_similarity: 0.8
      - type: "antithesis_coverage"
        min_keywords: 3
```

**실제 코드**:
```python
# orchestration/persona_orchestrator.py (현재)
def _derive_symmetry_state(self, persona_id, evaluation_metrics, phase_meta):
    # 잔차 계산만 하고, 제어는 안 함
    residual = abs(affect_after - affect_before)
    decision = "pending"  # ← 항상 pending!
    return residual, decision
```

**결과**:
- 잔차가 0.875여도 "keep" 또는 "review" 결정 안 함
- Synthesis가 나쁜 응답을 해도 통과
- 재시도 로직 작동 안 함

---

### 3. Validator 로직 없음

**E2 설정**:
```yaml
# Synthesis 통합 검증
integration_validation:
  enabled: true
  max_thesis_similarity: 0.8
  min_antithesis_keywords: 3
  require_synthesis_markers: true
  on_failure: "review"
```

**실제 코드**: **없음!**

**결과**:
- Synthesis가 Thesis 95% 복사해도 통과
- Antithesis 키워드 0개여도 통과
- 통합 마커 없어도 통과

---

## 📊 E2 상세 분석

### Stage 3 (Synthesis) 폭발

**E1 Stage 3**: 잔차 0.390 (나쁘지만 견딜만)
**E2 Stage 3**: 잔차 **0.875** (완전 폭발)

**원인 추측**:
1. Ollama 백엔드가 더 긴 응답 생성
2. 프롬프트 "Address 3 concerns"에 따라 긴 설명 작성
3. 하지만 실제 통합은 안 하고 나열만 함
4. → Thesis와 Antithesis 사이 긴장이 전혀 해소 안 됨
5. → 잔차 0.875 (역대 최고)

### 전체 Risk 100%

**E1**: Risk 62.5%, Creative 25%, Stable 12.5%
**E2**: Risk **100%**, Creative 0%, Stable 0%

**의미**:
- 모든 턴이 "통합 불가능" 상태
- 변증법이 완전히 실패
- 프롬프트 강화가 오히려 악화시킴

---

## 💡 E2.5 계획 (긴급 수정)

### 목표
E2 설정을 **실제로 작동**하게 만들기

### Phase 1: Validator 구현 (최우선, 2시간)

**파일 생성**: `orchestration/validators.py`

```python
from typing import Dict, Any, Tuple, List
import re

def validate_synthesis_integration(
    synthesis_text: str,
    thesis_text: str,
    antithesis_text: str,
    config: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Synthesis 통합 검증

    Returns:
        ("keep" | "review" | "damp", validation_details)
    """
    issues = []

    # 1. Thesis 유사도 체크
    similarity = calculate_similarity(synthesis_text, thesis_text)
    max_sim = config.get("max_thesis_similarity", 0.8)

    if similarity > max_sim:
        issues.append({
            "type": "high_thesis_similarity",
            "value": similarity,
            "threshold": max_sim,
            "message": f"Synthesis too similar to Thesis ({similarity:.2f} > {max_sim})"
        })

    # 2. Antithesis 키워드 커버리지
    anti_keywords = extract_keywords(antithesis_text, top_k=10)
    covered = sum(1 for kw in anti_keywords if kw.lower() in synthesis_text.lower())
    min_coverage = config.get("min_antithesis_keywords", 3)

    if covered < min_coverage:
        issues.append({
            "type": "low_antithesis_coverage",
            "value": covered,
            "threshold": min_coverage,
            "message": f"Only {covered}/{len(anti_keywords)} antithesis keywords covered"
        })

    # 3. 통합 마커 체크
    synthesis_markers = ["therefore", "thus", "by combining", "to address",
                         "따라서", "그러므로", "통합하여", "해결하기 위해"]
    has_markers = any(marker in synthesis_text.lower() for marker in synthesis_markers)

    if config.get("require_synthesis_markers", True) and not has_markers:
        issues.append({
            "type": "no_synthesis_markers",
            "message": "No integrative language found"
        })

    # 4. 인용 체크
    citations = len(re.findall(r'\[Source:|https?://|\(Source:', synthesis_text))
    min_citations = config.get("min_citations", 1)

    if citations < min_citations:
        issues.append({
            "type": "insufficient_citations",
            "value": citations,
            "threshold": min_citations,
            "message": f"Only {citations} citations (need {min_citations})"
        })

    # 결정
    if not issues:
        return "keep", {"status": "valid", "issues": []}
    elif len(issues) >= 3:
        return "review", {"status": "critical", "issues": issues}
    else:
        return "damp", {"status": "warning", "issues": issues}


def calculate_similarity(text1: str, text2: str) -> float:
    """간단한 Jaccard 유사도"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """간단한 키워드 추출 (중요 단어)"""
    # 불용어 제거
    stopwords = {"the", "a", "an", "is", "are", "to", "of", "in", "for", "on",
                 "이", "그", "저", "것", "수", "등", "및"}

    words = re.findall(r'\w+', text.lower())
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]

    # 빈도 계산
    from collections import Counter
    counts = Counter(keywords)

    return [word for word, count in counts.most_common(top_k)]
```

---

### Phase 2: PhaseController 제어 로직 (2시간)

**파일 수정**: `orchestration/persona_orchestrator.py`

```python
from orchestration.validators import validate_synthesis_integration

def _derive_symmetry_state(self, persona_id, evaluation_metrics, phase_meta):
    """기존 함수에 validator 추가"""

    # 기존 잔차 계산
    affect_before = phase_meta.get("affect_before", 0.5)
    affect_after = phase_meta.get("affect_after", 0.5)
    residual = abs(affect_after - 0.5)  # 목표: 0.5
    tension = abs(affect_after - affect_before)

    symmetry_stage = phase_meta.get("symmetry_stage", 0)

    # NEW: Validator 호출
    decision = "pending"
    validation_details = {}

    if persona_id == "synthesis" and symmetry_stage == 3:
        # Synthesis 전용 검증
        synthesis_text = self.conversation_history[-1].get("response", "")
        thesis_text = self.conversation_history[-3].get("response", "")
        antithesis_text = self.conversation_history[-2].get("response", "")

        validator_config = {
            "max_thesis_similarity": 0.8,
            "min_antithesis_keywords": 3,
            "require_synthesis_markers": True,
            "min_citations": 1
        }

        decision, validation_details = validate_synthesis_integration(
            synthesis_text, thesis_text, antithesis_text, validator_config
        )

    # 잔차 기반 결정 (기존 로직)
    elif residual < 0.4:
        decision = "keep"
    elif residual < 0.7:
        decision = "damp"
    else:
        decision = "review"

    return residual, tension, decision, validation_details
```

---

### Phase 3: 재시도 로직 (1시간)

**파일 수정**: `orchestration/persona_orchestrator.py`

```python
def _execute_persona_turn(self, persona, depth_index):
    """Persona 실행 + 재시도"""

    max_retries = 2
    attempt = 0

    while attempt < max_retries:
        # 응답 생성
        response = persona.generate_response(prompt)
        evaluation_metrics = self.evaluate_response(response)

        # Symmetry 상태 확인
        residual, tension, decision, validation = self._derive_symmetry_state(
            persona.identifier, evaluation_metrics, phase_meta
        )

        # 결정에 따라 처리
        if decision == "keep":
            return response, evaluation_metrics

        elif decision == "damp":
            # 경고 로그만 찍고 통과
            print(f"[WARN] {persona.identifier}: {validation.get('issues')}")
            return response, evaluation_metrics

        elif decision == "review":
            attempt += 1
            if attempt < max_retries:
                print(f"[RETRY {attempt}] {persona.identifier}: {validation.get('issues')}")
                # 프롬프트에 피드백 추가
                feedback = self._generate_feedback(validation)
                prompt = f"{prompt}\n\n[Previous attempt had issues: {feedback}]"
            else:
                print(f"[FAIL] {persona.identifier}: Max retries reached")
                return response, evaluation_metrics  # 최종 실패도 통과

    return response, evaluation_metrics
```

---

## 📋 E2.5 작업 체크리스트

### 🔴 Phase 1: Validator 구현 (High Priority, 2시간)
- [ ] `orchestration/validators.py` 생성
- [ ] `validate_synthesis_integration()` 구현
- [ ] `calculate_similarity()` 구현
- [ ] `extract_keywords()` 구현
- [ ] 단위 테스트 (간단한 예제로)

### 🔴 Phase 2: PhaseController 연결 (High Priority, 2시간)
- [ ] `persona_orchestrator.py`에 validator import
- [ ] `_derive_symmetry_state()`에서 validator 호출
- [ ] `decision` 로직을 실제로 사용
- [ ] 로그에 validation details 출력

### 🟡 Phase 3: 재시도 로직 (Medium Priority, 1시간)
- [ ] `_execute_persona_turn()`에 while 루프 추가
- [ ] `decision == "review"` 시 재시도
- [ ] 피드백 프롬프트 생성
- [ ] 최대 2회 재시도 제한

### 🟢 Phase 4: E2.5 실험 (1시간)
- [ ] 위 코드 모두 적용
- [ ] E2.5 실행 (동일 명령)
- [ ] symmetry_summary.txt 확인
- [ ] Stage 3 잔차 < 0.5 목표

---

## 🎯 E2.5 목표

| 메트릭 | E2 (실패) | E2.5 목표 | E3 최종 목표 |
|--------|-----------|-----------|--------------|
| **Stage 3 잔차** | 0.875 | < 0.5 | < 0.35 |
| **Risk 밴드** | 100% | < 50% | < 20% |
| **Creative 밴드** | 0% | > 30% | > 60% |
| **Validator 작동** | ❌ | ✅ | ✅ |

---

## 📈 예상 효과

### E2 (현재)
```
프롬프트 강화 → LLM 긴 응답 생성 → 통합 실패 → 잔차 0.875
```

### E2.5 (Validator 추가)
```
프롬프트 강화 → LLM 응답 → Validator 체크 →
  실패 시 재시도 (피드백 포함) → 통과 시 완료 → 잔차 < 0.5
```

### E3 (RAG 통합)
```
프롬프트 + RAG 조회 → LLM 응답 (증거 포함) → Validator 체크 →
  통과 → 잔차 < 0.35
```

---

## 💬 루빛에게

E2 실패 분석 정확합니다! 👍

**문제**: 설정만 바꾸고 코드는 그대로
**해결**: Phase 1-3 구현 (총 5시간)

**우선순위**:
1. **Phase 1**: Validator (2시간) - 가장 중요!
2. **Phase 2**: PhaseController 연결 (2시간)
3. **Phase 3**: 재시도 로직 (1시간)

Validator만 구현해도 E2.5에서 큰 개선 기대됩니다.

**시작할까요?** 😊

---

**작성자**: 세나 (Sena) + 루빛 (Lubit) 분석
**버전**: 1.0 - E2.5 긴급 계획
**상태**: 구현 대기 중
\n## Updated Metrics (analysis/persona_metrics.py v2)\n- Stage 3 ���� ����: E1 0.547 �� E2 0.875 �� E2_fix2 0.395 (PASS).\n- â�� ��� ������: E2 Fix2���� Stage 1/2/3 ��� 100%.
