# ChatResponse Metadata Reference

**작성자**: 루빛  
**작성일**: 2025-10-21

---

## 1. Overview

`ChatResponse.metadata`는 PersonaPipeline이 생성하는 부가 정보를 묶어 전달합니다.  
이 문서에서는 각 하위 키의 의미와 예시 값을 정리합니다.

### Top-level Structure

```json
{
  "rhythm": { ... },
  "tone": { ... },
  "routing": { ... },
  "phase": { ... },
  "rune": { ... }
}
```

---

## 2. Rhythm

| 필드 | 타입 | 설명 |
|------|------|------|
| `pace` | string | 분석된 리듬 속도 (`burst`, `flowing`, `medium`) |
| `avg_length` | float | 문장 평균 길이 (토큰 기준) |
| `punctuation_density` | float | 구두점 비율 (0.0~1.0) |

**활용**: 사용자 메시지 패턴을 기반으로 텍스트 생성 전략 조정, 속도 기반 모니터링.

---

## 3. Tone

| 필드 | 타입 | 설명 |
|------|------|------|
| `primary` | string | 주요 감정 톤 (`frustrated`, `calm` 등) |
| `confidence` | float | 탐지 확신도 (0.0~1.0) |
| `secondary` | Optional[string] | 보조 감정 톤 |

**활용**: 감정 기반 라우팅 검증, 피드백 루프의 감성 지표.

---

## 4. Routing

| 필드 | 타입 | 설명 |
|------|------|------|
| `secondary_persona` | Optional[string] | 2순위로 추천된 페르소나 |
| `reasoning` | string | Tone/Pace/Intent 분석을 기반으로 한 선택 사유 |

**활용**: 라우팅 결정 감사 로그, 퍼소나 튜닝에 대한 근거 데이터.

---

## 5. Phase (Phase Injection Snapshot)

| 필드 | 타입 | 설명 |
|------|------|------|
| `phase_index` | int | 현재 페이즈(0-based) |
| `phase_label` | string | 페이즈 이름 (`Attune`, `Structure`, `Elevate`) |
| `guidance` | string | 해당 페이즈에서 강조할 응답 방향 |
| `bqi` | object | Beauty/Quality/Impact 점수 (`0.0~1.0`) |
| `timestamp` | float | 페이즈 결정 시점 (epoch seconds) |

**활용**: 페이즈 별 응답 성향 모니터링, BQI 로그 분석.

---

## 6. RUNE (Quality Evaluation)

| 필드 | 타입 | 설명 |
|------|------|------|
| `overall_quality` | float | 최종 품질 점수 (0.0~1.0) |
| `regenerate` | bool | 재생성 여부 |
| `feedback` | string | 개선 코멘트 |
| `transparency` | object | RUNE 내부 평가 메타데이터 (impact, confidence, risks 등) |

**활용**: 품질 지표 대시보드, 재생성 비율 모니터링, 품질 회귀 분석.

---

## 7. Full Example

```json
{
  "rhythm": {
    "pace": "burst",
    "avg_length": 3.5,
    "punctuation_density": 0.15
  },
  "tone": {
    "primary": "frustrated",
    "confidence": 0.85,
    "secondary": null
  },
  "routing": {
    "secondary_persona": "Nana",
    "reasoning": "tone=frustrated pace=burst intent=expressive → Lua 선택"
  },
  "phase": {
    "phase_index": 1,
    "phase_label": "Structure",
    "guidance": "Lay out a clear plan with concrete steps.",
    "bqi": {
      "beauty": 0.72,
      "quality": 0.83,
      "impact": 0.68
    },
    "timestamp": 1697539200.0
  },
  "rune": {
    "overall_quality": 0.82,
    "regenerate": false,
    "feedback": "- 응답이 사용자 질문의 핵심을 다루고 있습니다.",
    "transparency": {
      "impact": 0.82,
      "confidence": 0.5,
      "risks": [],
      "source": "heuristic"
    }
  }
}
```

---

## 8. Sample Dataset

- 샘플 로그(JSONL): `../samples/chat_responses_sample.jsonl`
- 예제 실행:

```bash
python scripts/analyze_chat_metadata.py --input ../samples/chat_responses_sample.jsonl
# 또는
cat ../samples/chat_responses_sample.jsonl | python scripts/analyze_chat_metadata.py --json
```

위 샘플을 활용하면 분석 스크립트 출력 형식을 빠르게 확인할 수 있습니다.

---

## 9. Logging & Monitoring Tips

1. **Phase 변화 추적**  
   - 로그 필터: `metadata.phase.phase_label`, `metadata.phase.timestamp`
   - 알림 조건: 동일 페이즈에서 장시간 정체 (`phase_index` 고정)

2. **품질 점수 모니터링**  
   - 지표: `metadata.rune.overall_quality`
   - 알림 조건: 평균 품질 < 0.7, 또는 `metadata.rune.regenerate = true` 비율 급증

3. **라우팅 감사**  
   - `metadata.routing.reasoning`을 저장하여 페르소나 선택 근거 분석
   - A/B 실험 시 secondary persona 비교에 활용

---

## 10. FAQ

| 질문 | 답변 |
|------|------|
| `metadata` 필드를 전부 사용해야 하나요? | 필수는 아니며, 필요한 항목만 파싱하면 됩니다. |
| `phase`/`rune`을 비활성화할 수 있나요? | `PersonaPipeline` 생성 시 `enable_phase_injection=False` 또는 `enable_rune=False` 옵션으로 제어 가능합니다. |
| 커스텀 메타데이터를 추가하려면? | `PersonaResponse.metadata`는 dict이므로, 추가 키를 삽입해도 기존 소비자에게 영향이 없습니다. |

---

## 11. Change Log

| 날짜 | 변경 내용 |
|------|-----------|
| 2025-10-21 | 초기 버전 작성 |
