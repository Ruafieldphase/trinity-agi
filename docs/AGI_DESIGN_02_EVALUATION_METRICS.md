# AGI 설계 문서 02: 자동 평가 지표 시스템 v1.0

**작성자**: 세나 (Sena)
**작성일**: 2025-10-12
**상태**: 초안
**목적**: 페르소나 응답의 품질을 자동으로 측정하고 개선 방향을 제시하는 시스템 설계

---

## 1. 목표

### 1.1 왜 필요한가?
현재는 **수동으로 응답 길이만 확인**하고 있습니다. AGI로 나아가려면:
- **객관적 지표**: 응답 품질을 수치화하여 개선 추적
- **자동 평가**: 매번 실험마다 수동 검토하지 않고 자동 분석
- **학습 신호**: 어떤 설정/프롬프트가 더 나은지 데이터 기반 판단

### 1.2 평가 대상
- 정반합 사이클의 각 페르소나 응답 (thesis, antithesis, synthesis)
- 전체 세션의 종합 품질
- 특정 백엔드/모델의 성능 비교

---

## 2. 스코프

### 2.1 v1.0에 포함할 것 ✅
- **정량 지표 3가지**: 응답 길이, 감성 점수, 완결성
- **정성 지표 1가지**: 키워드 기반 비판 강도
- **확장 QC 지표 4가지**: 투명성, 재현성, 검증성, 영향지수(impact score) — RUNE/EVAL 단계에서 계산
- **자동 계산**: PersonaOrchestrator 실행 시 자동 측정
- **JSONL 로그**: 기존 로그에 metrics 필드 추가 + Resonance Ledger 연동
- **간단한 리포트**: 세션 종료 후 요약 통계 출력

### 2.2 나중 버전으로 미룰 것 ⏳
- LLM 기반 평가 (GPT-4를 judge로 사용)
- 사용자 만족도 예측 모델
- 실시간 대시보드
- A/B 테스트 프레임워크

---

## 3. 평가 지표 설계

### 3.1 객관적 지표

#### (1) 응답 길이 (Response Length)

**목적**: 너무 짧거나 긴 응답 감지

```python
def calculate_length_metrics(response: str) -> Dict[str, Any]:
    """
    Returns:
        {
            "char_count": 1234,
            "word_count": 256,
            "sentence_count": 12,
            "avg_sentence_length": 21.3,
            "length_score": 0.85  # 0.0 ~ 1.0
        }
    """
    char_count = len(response)
    word_count = len(response.split())
    sentences = re.split(r'[.!?]+', response)
    sentence_count = len([s for s in sentences if s.strip()])
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # 길이 점수 계산 (적정 범위: 100~500 단어)
    if word_count < 50:
        length_score = word_count / 50 * 0.5  # 너무 짧음: 0.0 ~ 0.5
    elif word_count <= 500:
        length_score = 0.5 + (word_count - 50) / 450 * 0.5  # 적정: 0.5 ~ 1.0
    else:
        length_score = max(0.7, 1.0 - (word_count - 500) / 1000)  # 너무 김: 1.0 → 0.7

    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "length_score": round(length_score, 2)
    }
```

**해석**:
- `length_score >= 0.8`: 적절한 길이
- `0.5 <= length_score < 0.8`: 개선 필요
- `length_score < 0.5`: 문제 (너무 짧거나 김)

---

#### (2) 감성 점수 (Sentiment Score)

**목적**: 긍정/부정 균형, 페르소나별 특성 확인

```python
# 확장된 감성 토큰 (기존 POSITIVE_TOKENS, NEGATIVE_TOKENS 활용)
POSITIVE_EXTENDED = {
    "hope", "growth", "stability", "trust", "creative", "opportunity", "calm",
    "align", "care", "resilience", "insight", "balance", "support", "expand",
    "potential", "synergy", "harmony", "progress", "success", "improve"
}

NEGATIVE_EXTENDED = {
    "fear", "risk", "fail", "collapse", "danger", "stuck", "hurt", "doubt",
    "chaos", "conflict", "tension", "problem", "issue", "block",
    "weakness", "threat", "error", "concern", "limitation", "barrier"
}

def calculate_sentiment_metrics(response: str) -> Dict[str, Any]:
    """
    Returns:
        {
            "sentiment_score": 0.12,       # -1.0 (부정) ~ +1.0 (긍정)
            "positive_count": 5,
            "negative_count": 2,
            "neutral_ratio": 0.85,
            "confidence": 0.7              # 감정 표현 명확도
        }
    """
    tokens = [token.lower() for token in re.findall(r"\b[\w']+\b", response)]
    if not tokens:
        return {"sentiment_score": 0.0, "confidence": 0.0}

    pos_count = sum(1 for t in tokens if t in POSITIVE_EXTENDED)
    neg_count = sum(1 for t in tokens if t in NEGATIVE_EXTENDED)
    total_tokens = len(tokens)

    # 감성 점수: 긍정-부정 비율
    if pos_count + neg_count == 0:
        sentiment_score = 0.0
        confidence = 0.0
    else:
        sentiment_score = (pos_count - neg_count) / total_tokens * 10  # 스케일 조정
        sentiment_score = clamp(sentiment_score, -1.0, 1.0)
        confidence = (pos_count + neg_count) / total_tokens  # 감정 표현 비율
        confidence = clamp(confidence, 0.0, 1.0)

    neutral_ratio = 1.0 - (pos_count + neg_count) / total_tokens

    return {
        "sentiment_score": round(sentiment_score, 2),
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_ratio": round(neutral_ratio, 2),
        "confidence": round(confidence, 2)
    }
```

**해석**:
- `sentiment_score > 0`: 긍정적 응답
- `sentiment_score < 0`: 부정적 응답 (antithesis에서 기대됨)
- `confidence < 0.05`: 감정 표현 없음 (건조한 응답)

---

#### (3) 완결성 (Completeness)

**목적**: 요청한 내용을 모두 다뤘는지 확인

```python
def calculate_completeness_metrics(
    response: str,
    seed_prompt: str,
    persona_role: str
) -> Dict[str, Any]:
    """
    Returns:
        {
            "has_reasoning": True,         # 논리/근거 포함 여부
            "has_concrete_example": False, # 구체적 예시 포함 여부
            "addresses_prompt": True,      # 프롬프트 핵심 키워드 언급 여부
            "role_alignment": 0.9,         # 페르소나 역할 일치도
            "completeness_score": 0.75
        }
    """
    response_lower = response.lower()
    prompt_lower = seed_prompt.lower()

    # 논리/근거 포함 여부 (키워드 탐지)
    reasoning_keywords = ["because", "since", "therefore", "thus", "hence", "왜냐하면", "따라서", "그러므로"]
    has_reasoning = any(kw in response_lower for kw in reasoning_keywords)

    # 구체적 예시 포함 여부
    example_keywords = ["for example", "such as", "instance", "예를 들어", "가령", "구체적으로"]
    has_concrete_example = any(kw in response_lower for kw in example_keywords)

    # 프롬프트 핵심 키워드 언급 (단순 추출)
    prompt_keywords = extract_keywords(prompt_lower, top_n=5)
    keyword_coverage = sum(1 for kw in prompt_keywords if kw in response_lower) / len(prompt_keywords)
    addresses_prompt = keyword_coverage >= 0.4  # 40% 이상 키워드 포함

    # 페르소나 역할 일치도
    role_alignment = calculate_role_alignment(response_lower, persona_role)

    # 완결성 점수
    completeness_score = (
        0.3 * (1.0 if has_reasoning else 0.0) +
        0.2 * (1.0 if has_concrete_example else 0.0) +
        0.3 * keyword_coverage +
        0.2 * role_alignment
    )

    return {
        "has_reasoning": has_reasoning,
        "has_concrete_example": has_concrete_example,
        "addresses_prompt": addresses_prompt,
        "keyword_coverage": round(keyword_coverage, 2),
        "role_alignment": round(role_alignment, 2),
        "completeness_score": round(completeness_score, 2)
    }


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """간단한 TF-IDF 없이 빈도 기반 키워드 추출"""
    words = [w for w in re.findall(r"\b[\w']+\b", text) if len(w) > 3]
    stopwords = {"that", "this", "with", "from", "have", "will", "what", "when", "어떻게", "무엇"}
    filtered = [w for w in words if w not in stopwords]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]


def calculate_role_alignment(response: str, persona_role: str) -> float:
    """페르소나 역할 키워드 포함 여부로 간단 평가"""
    role_keywords = {
        "Seed explorer": ["explore", "expand", "discover", "potential", "탐색", "확장"],
        "Critical reflector": ["challenge", "question", "concern", "risk", "반박", "문제"],
        "Integrator": ["synthesize", "reconcile", "integrate", "combine", "통합", "조화"],
        "Affect monitor": ["emotion", "feeling", "affect", "drift", "감정", "분위기"],
        "Implementation planner": ["plan", "action", "step", "implement", "계획", "실행"]
    }

    keywords = role_keywords.get(persona_role, [])
    if not keywords:
        return 0.5  # 알 수 없는 역할

    matches = sum(1 for kw in keywords if kw in response)
    return min(matches / 3, 1.0)  # 3개 이상 매칭 시 1.0
```

**해석**:
- `completeness_score >= 0.7`: 충분히 완결된 응답
- `0.4 <= completeness_score < 0.7`: 부분적 완결
- `completeness_score < 0.4`: 불완전한 응답

---

### 3.2 정성 지표

#### (4) 비판 강도 (Critical Intensity) - Antithesis 전용

**목적**: Antithesis의 비판이 충분히 날카로운지 측정

```python
def calculate_critical_intensity(response: str, persona_id: str) -> Dict[str, Any]:
    """
    Antithesis 페르소나에만 적용

    Returns:
        {
            "critical_keywords_count": 5,
            "question_count": 3,           # 질문 문장 수
            "disagreement_level": 0.8,     # 반대 의견 강도
            "intensity_score": 0.75
        }
    """
    if persona_id != "antithesis":
        return {"intensity_score": None}  # 다른 페르소나는 N/A

    response_lower = response.lower()

    # 비판 키워드
    critical_keywords = [
        "however", "but", "concern", "problem", "overlook", "ignore",
        "risk", "fail", "weakness", "limitation", "flaw",
        "하지만", "그러나", "문제", "우려", "간과", "위험", "한계"
    ]
    critical_count = sum(1 for kw in critical_keywords if kw in response_lower)

    # 질문 문장 수
    question_count = response.count("?") + response.count("？")

    # 반대 의견 강도 (부정 감성 활용)
    sentiment = calculate_sentiment_metrics(response)
    disagreement_level = abs(min(sentiment["sentiment_score"], 0.0))  # 부정 부분만

    # 비판 강도 점수
    intensity_score = (
        0.4 * min(critical_count / 5, 1.0) +       # 비판 키워드 (5개가 만점)
        0.3 * min(question_count / 3, 1.0) +       # 질문 (3개가 만점)
        0.3 * disagreement_level
    )

    return {
        "critical_keywords_count": critical_count,
        "question_count": question_count,
        "disagreement_level": round(disagreement_level, 2),
        "intensity_score": round(intensity_score, 2)
    }
```

**해석**:
- `intensity_score >= 0.7`: 충분히 날카로운 비판
- `0.4 <= intensity_score < 0.7`: 온건한 비판
- `intensity_score < 0.4`: 비판 부족 (Antithesis 역할 미달)

### 3.3 확장 QC 지표 (RUNE + EVAL 연동)

Core 패키지에서 제안된 `투명성·재현성·검증성·영향지수`는 RUNE 분석 결과와 평가 시스템(EVAL 노드)에서 산출합니다.

```python
def calculate_resonance_metrics(
    response: str,
    tools_used: List[str],
    facts_verified: int,
    facts_total: int,
    reproducible: bool,
    external_references: List[str],
) -> Dict[str, Any]:
    """
    Returns:
        {
            "impact_score": 0.74,
            "transparency": 0.9,
            "reproducibility": 0.85,
            "verifiability": 0.8,
            "notes": "2 external references cited"
        }
    """
    impact_score = min(len(response) / 1000 + len(tools_used) * 0.05, 1.0)
    transparency = min(len(tools_used) * 0.1 + 0.5, 1.0)  # 도구 사용 및 근거 공개 정도
    repro_score = 0.85 if reproducible else 0.5
    verifiability = facts_verified / facts_total if facts_total else 0.7

    return {
        "impact_score": round(impact_score, 2),
        "transparency": round(transparency, 2),
        "reproducibility": round(repro_score, 2),
        "verifiability": round(verifiability, 2),
        "notes": f"{facts_verified}/{facts_total} facts checked; {len(external_references)} references"
    }
```

> RUNE는 Synth 단계 이후 `calculate_resonance_metrics`를 호출하고, 결과는 Resonance Ledger와 평가 로그에 동시에 기록합니다.

--- 

## 4. 통합 평가 점수

### 4.1 페르소나별 종합 점수

```python
def calculate_overall_score(
    length_metrics: Dict,
    sentiment_metrics: Dict,
    completeness_metrics: Dict,
    critical_metrics: Dict,
    persona_id: str
) -> float:
    """
    페르소나별 가중치 적용하여 종합 점수 계산

    Returns:
        overall_score: 0.0 ~ 1.0
    """
    weights = {
        "thesis": {
            "length": 0.2,
            "sentiment": 0.2,      # 긍정적이어야 함
            "completeness": 0.6
        },
        "antithesis": {
            "length": 0.2,
            "sentiment": 0.1,      # 부정적이어도 OK
            "completeness": 0.4,
            "critical_intensity": 0.3  # 비판 강도 중요
        },
        "synthesis": {
            "length": 0.2,
            "sentiment": 0.1,
            "completeness": 0.7    # 완결성 가장 중요
        }
    }

    w = weights.get(persona_id, weights["thesis"])  # 기본값

    score = (
        w.get("length", 0) * length_metrics["length_score"] +
        w.get("sentiment", 0) * abs(sentiment_metrics["sentiment_score"]) +
        w.get("completeness", 0) * completeness_metrics["completeness_score"] +
        w.get("critical_intensity", 0) * (critical_metrics.get("intensity_score") or 0)
    )

    return round(score, 2)
```

### 4.2 세션 종합 평가

```python
def calculate_session_summary(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    전체 세션의 통계 요약

    Returns:
        {
            "total_turns": 12,
            "avg_length_score": 0.82,
            "avg_completeness_score": 0.75,
            "avg_overall_score": 0.78,
            "persona_breakdown": {
                "thesis": {"count": 4, "avg_score": 0.80},
                "antithesis": {"count": 4, "avg_score": 0.75},
                "synthesis": {"count": 4, "avg_score": 0.80}
            },
            "affect_trajectory": [0.5, 0.55, 0.62, ...],  # PhaseController affect 변화
            "quality_rating": "Good"  # Excellent | Good | Fair | Poor
        }
    """
    persona_scores = defaultdict(list)
    affect_trajectory = []
    all_overall_scores = []
    resonance_totals = {
        "impact_score": 0.0,
        "transparency": 0.0,
        "reproducibility": 0.0,
        "verifiability": 0.0,
        "count": 0,
    }

    for entry in log_entries:
        persona_id = entry["persona"]["id"]
        metrics = entry.get("evaluation_metrics", {})
        overall_score = metrics.get("overall_score", 0.0)

        persona_scores[persona_id].append(overall_score)
        all_overall_scores.append(overall_score)
        affect_trajectory.append(entry["state_after"]["affect_amplitude"])
        resonance_metrics = metrics.get("resonance")
        if resonance_metrics:
            resonance_totals["impact_score"] += resonance_metrics.get("impact_score", 0)
            resonance_totals["transparency"] += resonance_metrics.get("transparency", 0)
            resonance_totals["reproducibility"] += resonance_metrics.get("reproducibility", 0)
            resonance_totals["verifiability"] += resonance_metrics.get("verifiability", 0)
            resonance_totals["count"] += 1

    # 페르소나별 요약
    persona_breakdown = {}
    for pid, scores in persona_scores.items():
        persona_breakdown[pid] = {
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0
        }

    # 전체 평균
    avg_overall = sum(all_overall_scores) / len(all_overall_scores) if all_overall_scores else 0.0

    # 품질 등급
    if avg_overall >= 0.8:
        quality_rating = "Excellent"
    elif avg_overall >= 0.65:
        quality_rating = "Good"
    elif avg_overall >= 0.5:
        quality_rating = "Fair"
    else:
        quality_rating = "Poor"

    resonance_average = None
    if resonance_totals["count"]:
        c = resonance_totals["count"]
        resonance_average = {
            "impact_score": round(resonance_totals["impact_score"] / c, 2),
            "transparency": round(resonance_totals["transparency"] / c, 2),
            "reproducibility": round(resonance_totals["reproducibility"] / c, 2),
            "verifiability": round(resonance_totals["verifiability"] / c, 2),
        }

    return {
        "total_turns": len(log_entries),
        "avg_overall_score": round(avg_overall, 2),
        "persona_breakdown": persona_breakdown,
        "affect_trajectory": [round(a, 2) for a in affect_trajectory],
        "quality_rating": quality_rating,
        "avg_resonance_metrics": resonance_average
    }
```

---

## 5. PersonaOrchestrator 통합

### 5.1 _run_recursive 수정

```python
def _run_recursive(self, seed_prompt: str, depth: int, depth_index: int) -> str:
    # ... 기존 코드 ...

    # 응답 생성 후
    response = backend.generate(...)
    phase_meta = self.phase.integrate_response(persona.identifier, response)

    # 평가 지표 계산 (추가)
    evaluation_metrics = self._evaluate_response(
        persona=persona,
        response=response,
        seed_prompt=seed_prompt,
        phase_meta=phase_meta
    )

    self.history.append(history_entry("persona", persona.identifier, response))

    log_record = {
        # ... 기존 필드 ...
        "evaluation_metrics": evaluation_metrics,  # 추가
    }
    self.log_entries.append(log_record)

    # ... 기존 코드 계속 ...
```

### 5.2 _evaluate_response 메서드 추가

```python
def _evaluate_response(
    self,
    persona: Persona,
    response: str,
    seed_prompt: str,
    phase_meta: Dict[str, Any]
) -> Dict[str, Any]:
    """응답에 대한 모든 평가 지표 계산"""
    length_metrics = calculate_length_metrics(response)
    sentiment_metrics = calculate_sentiment_metrics(response)
    completeness_metrics = calculate_completeness_metrics(
        response=response,
        seed_prompt=seed_prompt,
        persona_role=persona.role
    )
    critical_metrics = calculate_critical_intensity(response, persona.identifier)
    resonance_metrics = calculate_resonance_metrics(
        response=response,
        tools_used=self._tools_used_in_current_step,
        facts_verified=self._facts_verified,
        facts_total=self._facts_total,
        reproducible=self._plan_replayable,
        external_references=self._external_references,
    )

    overall_score = calculate_overall_score(
        length_metrics=length_metrics,
        sentiment_metrics=sentiment_metrics,
        completeness_metrics=completeness_metrics,
        critical_metrics=critical_metrics,
        persona_id=persona.identifier
    )

    return {
        "length": length_metrics,
        "sentiment": sentiment_metrics,
        "completeness": completeness_metrics,
        "critical_intensity": critical_metrics if persona.identifier == "antithesis" else None,
        "resonance": resonance_metrics,
        "overall_score": overall_score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

### 5.3 run 메서드에 세션 요약 추가

```python
def run(self, seed_prompt: str, depth: int = 1) -> Dict[str, Any]:
    # ... 기존 코드 ...

    final_output = self._run_recursive(seed_prompt, depth=depth, depth_index=1)

    # 세션 요약 계산 (추가)
    session_summary = calculate_session_summary(self.log_entries)

    if self.log_path:
        self._write_log()
        # 요약 파일도 저장
        summary_path = self.log_path.with_suffix(".summary.json")
        summary_path.write_text(json.dumps(session_summary, ensure_ascii=False, indent=2))

    return {
        "final_output": final_output,
        "history": self.history,
        "phase_state": serialize_state(self.phase.state),
        "log_entries": self.log_entries,
        "session_summary": session_summary,  # 추가
    }
```

---

## 6. 로그 출력 예시

### 6.1 JSONL 로그 (개별 응답)

```json
{
  "timestamp": "2025-10-12T10:30:45.123Z",
  "depth_index": 1,
  "step_index": 2,
  "persona": {
    "id": "antithesis",
    "name": "Boundary Challenger",
    "role": "Critical reflector",
    "backend": {"backend_id": "local_ollama", "type": "subprocess"}
  },
  "prompt_digest": "System instruction: You challenge blind spots...",
  "response": "While the thesis proposes...",
  "evaluation_metrics": {
    "length": {
      "char_count": 842,
      "word_count": 156,
      "sentence_count": 8,
      "avg_sentence_length": 19.5,
      "length_score": 0.85
    },
    "sentiment": {
      "sentiment_score": -0.18,
      "positive_count": 2,
      "negative_count": 7,
      "neutral_ratio": 0.92,
      "confidence": 0.06
    },
    "completeness": {
      "has_reasoning": true,
      "has_concrete_example": false,
      "addresses_prompt": true,
      "keyword_coverage": 0.6,
      "role_alignment": 0.85,
      "completeness_score": 0.72
    },
    "critical_intensity": {
      "critical_keywords_count": 6,
      "question_count": 2,
      "disagreement_level": 0.18,
      "intensity_score": 0.68
    },
    "resonance": {
      "impact_score": 0.74,
      "transparency": 0.88,
      "reproducibility": 0.85,
      "verifiability": 0.8,
      "notes": "2/3 facts checked; 1 references"
    },
    "overall_score": 0.74
  },
  "phase": {...},
  "state_after": {...}
}
```

### 6.2 세션 요약 (summary.json)

```json
{
  "total_turns": 12,
  "avg_overall_score": 0.76,
  "persona_breakdown": {
    "thesis": {
      "count": 4,
      "avg_score": 0.78
    },
    "antithesis": {
      "count": 4,
      "avg_score": 0.72
    },
    "synthesis": {
      "count": 4,
      "avg_score": 0.79
    }
  },
    "affect_trajectory": [0.5, 0.53, 0.58, 0.62, 0.65, 0.67, 0.7, 0.72, 0.74, 0.75, 0.76, 0.77],
    "quality_rating": "Good",
    "avg_resonance_metrics": {
      "impact_score": 0.72,
      "transparency": 0.85,
      "reproducibility": 0.82,
      "verifiability": 0.78
    }
  }
```

---

## 7. CLI 출력 개선

### 7.1 실행 중 실시간 피드백

```python
# main() 함수에서
result = orchestrator.run(seed_prompt=seed_prompt, depth=args.depth)

# 실시간 출력 추가
for entry in result["log_entries"]:
    persona_name = entry["persona"]["name"]
    overall_score = entry["evaluation_metrics"]["overall_score"]
    resonance = entry["evaluation_metrics"]["resonance"]
    print(f"  [{persona_name}] Score: {overall_score:.2f} | Impact {resonance['impact_score']:.2f}")

# 세션 요약 출력
summary = result["session_summary"]
print("\n==== Session Summary ====")
print(f"Total turns: {summary['total_turns']}")
print(f"Average score: {summary['avg_overall_score']:.2f}")
print(f"Quality rating: {summary['quality_rating']}")
if summary["avg_resonance_metrics"]:
    ar = summary["avg_resonance_metrics"]
    print(
        "Resonance (impact/transparency/reproducibility/verifiability): "
        f"{ar['impact_score']:.2f} / {ar['transparency']:.2f} / "
        f"{ar['reproducibility']:.2f} / {ar['verifiability']:.2f}"
    )
print("\nPersona breakdown:")
for persona_id, stats in summary["persona_breakdown"].items():
    print(f"  {persona_id}: {stats['avg_score']:.2f} ({stats['count']} turns)")
```

**출력 예시**:
```
==== Persona Orchestration Running ====
Depth 1, Step 1/3: Dialectic Thesis
  [Dialectic Thesis] Score: 0.78
Depth 1, Step 2/3: Boundary Challenger
  [Boundary Challenger] Score: 0.72
Depth 1, Step 3/3: Fractal Synthesiser
  [Fractal Synthesiser] Score: 0.79

==== Session Summary ====
Total turns: 12
Average score: 0.76
Quality rating: Good

Persona breakdown:
  thesis: 0.78 (4 turns)
  antithesis: 0.72 (4 turns)
  synthesis: 0.79 (4 turns)
```

---

## 8. 구현 파일 구조

```
scripts/
└── evaluation/
    ├── __init__.py
    ├── metrics.py            # 모든 지표 계산 함수
    ├── aggregation.py        # 세션 요약 계산
    └── visualizer.py         # (v2.0) 그래프 생성

tests/
└── test_evaluation.py        # 유닛 테스트
```

---

## 9. 테스트 계획

### 9.1 성공 기준
1. ✅ 길이 점수: 100단어 응답 → length_score ≈ 0.6
2. ✅ 감성 점수: 긍정 키워드 5개, 부정 2개 → sentiment_score > 0
3. ✅ 완결성: 논리+예시+키워드 포함 → completeness_score > 0.7
4. ✅ 비판 강도: antithesis에서 critical_keywords >= 5 → intensity_score > 0.7
5. ✅ 세션 요약: 12 turns → persona_breakdown에 각 4개씩

### 9.2 테스트 시나리오

#### 시나리오 1: 단일 응답 평가
```python
response = "This is a test response with hope and growth. However, there are concerns."
metrics = calculate_sentiment_metrics(response)
assert metrics["positive_count"] == 2
assert metrics["negative_count"] == 1
```

#### 시나리오 2: 페르소나별 종합 점수
```python
# Thesis: 긍정적이고 완결된 응답
thesis_response = "We can explore this opportunity by expanding our framework with concrete examples..."
thesis_metrics = evaluate_response(persona_thesis, thesis_response, seed_prompt)
assert thesis_metrics["overall_score"] > 0.7

# Antithesis: 비판적이고 질문 많은 응답
antithesis_response = "However, this approach overlooks several risks. What about edge cases? The limitation is clear..."
antithesis_metrics = evaluate_response(persona_antithesis, antithesis_response, seed_prompt)
assert antithesis_metrics["critical_intensity"]["intensity_score"] > 0.7
assert antithesis_metrics["resonance"]["impact_score"] >= 0.6
```

#### 시나리오 3: 세션 요약
```python
log_entries = [...]  # 12개 엔트리
summary = calculate_session_summary(log_entries)
assert summary["total_turns"] == 12
assert "thesis" in summary["persona_breakdown"]
assert summary["quality_rating"] in ["Excellent", "Good", "Fair", "Poor"]
```

---

## 10. 미결정 사항 (Core과 논의 필요)

### 10.1 지표 가중치 조정
- 현재 제안한 가중치가 합리적인지?
- 실험 후 조정 필요 가능성

### 10.2 품질 등급 기준
- Excellent: 0.8+ / Good: 0.65+ / Fair: 0.5+ / Poor: <0.5
- 이 기준이 너무 관대하거나 엄격한지?

### 10.3 LLM 기반 평가 (v2.0)
- GPT-4 또는 Claude를 "judge"로 사용하여 정성 평가?
- 비용 vs 정확도 트레이드오프

### 10.4 실시간 피드백
- 응답 생성 중 품질 예측하여 재생성 여부 결정?
- (예: overall_score < 0.5이면 재시도)

---

## 11. 다음 단계

1. ✅ 설계 문서 작성 완료
2. ⏳ Core과 설계 리뷰
3. ⏳ `scripts/evaluation/metrics.py` 구현
4. ⏳ PersonaOrchestrator 통합
5. ⏳ 테스트 실행 (10회 세션)
6. ⏳ 가중치 튜닝 및 기준 조정
7. ⏳ 문서 업데이트

---

## 12. 참고 자료

- 기존 감성 추정: [persona_orchestrator.py:316-339](../orchestration/persona_orchestrator.py#L316-L339)
- PhaseController: [naeda_langgraph_demo.py](../naeda_langgraph_demo.py)
- 루빛과의 모델 비교: [docs/model_comparison.md](model_comparison.md)

---

**검토 요청 사항**:
1. 4가지 지표가 충분한지? (추가 필요한 지표?)
2. 페르소나별 가중치가 합리적인지?
3. v1.0 스코프가 1주 내 구현 가능한지?
