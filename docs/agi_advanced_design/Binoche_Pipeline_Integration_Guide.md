# BinocheDecisionEngine 파이프라인 통합 가이드

**날짜**: 2025-10-30  
**목적**: 학습된 BinochePersona를 AGI 파이프라인에 통합하여 70-80% 자동 의사결정 달성

---

## 📋 통합 완료 상태

### ✅ 완료된 작업

1. **BinocheDecisionEngine 구현** (`orchestrator/binoche_integration.py`)
   - 8가지 학습된 규칙 적용
   - BQI 패턴 기반 자동 승인/수정/거절
   - 낮은 확신도 시 사용자 확인 요청
   - 통계 추적 기능

2. **Pipeline Adapter 구현** (`orchestrator/pipeline_binoche_adapter.py`)
   - 기존 복잡한 Binoche 시스템과 새 엔진 연결
   - 싱글톤 패턴으로 세션 통계 추적
   - 간소화된 의사결정 API 제공

3. **테스트 검증**
   - 4가지 시나리오 테스트 완료 (승인/수정/거절/사용자확인)
   - 75-100% 자동화율 달성

---

## 🔧 파이프라인 통합 방법

### Option 1: 기존 시스템 완전 대체 (권장)

**파일**: `fdo_agi_repo/orchestrator/pipeline.py`

**Line 219-280** 기존 Binoche 코드를 다음으로 대체:

```python
# Phase 6b: Enhanced Binoche Decision Engine (Simplified)
from .pipeline_binoche_adapter import enhanced_binoche_decision, print_session_stats

binoche_decision = enhanced_binoche_decision(
    task_goal=task.goal,
    eval_report=eval_report.model_dump(),
    bqi_coord=bqi_coord.to_dict(),
    meta_confidence=thesis_eval.get("confidence")  # Meta-cognition 확신도 사용
)

append_ledger({
    "event": "binoche_decision",
    "task_id": task.task_id,
    "action": binoche_decision["action"],
    "confidence": binoche_decision["confidence"],
    "rule_applied": binoche_decision["rule_applied"],
    "reason": binoche_decision["reason"],
    "bqi_pattern": binoche_decision["bqi_pattern"],
    "quality": float(eval_report.quality)
})

# Auto-approve 처리
if binoche_decision["auto_approved"]:
    append_ledger({
        "event": "binoche_auto_approve",
        "task_id": task.task_id,
        "confidence": binoche_decision["confidence"],
        "reason": binoche_decision["reason"]
    })
    
    result = {
        "task_id": task.task_id,
        "summary": out_synth.summary,
        "citations": out_synth.citations,
        "notes": "auto_approved_by_binoche",
        "confidence": binoche_decision["confidence"]
    }
    
    # 대화 메모리 저장
    conv_memory.add_turn(
        question=task.goal,
        answer=out_synth.summary,
        task_id=task.task_id,
        bqi_coord=bqi_coord
    )
    
    append_coordinate({"event": "task_end", "task_id": task.task_id, "result": result, "binoche_auto_approved": True})
    return result

# Auto-revise 처리
if binoche_decision["auto_revised"]:
    append_ledger({
        "event": "binoche_auto_revise",
        "task_id": task.task_id,
        "confidence": binoche_decision["confidence"],
        "reason": binoche_decision["reason"]
    })
    planning_auto_revise_triggered = True

# 이후 기존 evidence_gate 로직 유지...
```

---

### Option 2: 기존 시스템과 병행 (A/B 테스트)

기존 코드는 유지하고, 새로운 의사결정 로그만 추가:

```python
# Line 219 이후 추가
from .pipeline_binoche_adapter import enhanced_binoche_decision

# 새 엔진 테스트
enhanced_decision = enhanced_binoche_decision(
    task_goal=task.goal,
    eval_report=eval_report.model_dump(),
    bqi_coord=bqi_coord.to_dict()
)

append_ledger({
    "event": "binoche_enhanced_decision",
    "task_id": task.task_id,
    "enhanced_action": enhanced_decision["action"],
    "enhanced_confidence": enhanced_decision["confidence"],
    "legacy_action": binoche_decision,  # 기존 결과
    "match": enhanced_decision["action"] == binoche_decision
})

# 기존 로직 계속...
```

---

## 📊 성능 예측

### 학습 데이터 기반 예측

- **총 작업**: 404 tasks
- **승인 비율**: 70% (280건)
- **수정 비율**: 28% (112건)
- **거절 비율**: 2% (8건)

### 자동화 수준

- **완전 자동 승인**: ~70% (BQI 패턴 매칭 + 품질 기준)
- **자동 수정 요청**: ~5% (Planning 패턴)
- **사용자 확인 필요**: ~25% (낮은 확신도)

**예상 자동화율**: **75%** (목표 80% 근접)

---

## 🔍 모니터링 방법

### 1. 세션 통계 조회

```python
from orchestrator.pipeline_binoche_adapter import print_session_stats

# 파이프라인 실행 후
print_session_stats()
```

**출력 예시**:

```
[Binoche] Automation Statistics:
  Total decisions: 50
  Automation rate: 76.0%
    - Approved: 35
    - Revised: 3
    - Rejected: 0
    - Asked user: 12
```

### 2. Resonance Ledger 분석

```bash
# 최근 Binoche 의사결정 조회
Get-Content D:\nas_backup\fdo_agi_repo\memory\resonance_ledger.jsonl | Select-String "binoche_decision" | Select-Object -Last 10
```

### 3. Ops Dashboard 통합

`scripts/quick_status.ps1`에 Binoche 통계 추가:

```powershell
# Binoche 자동화율 계산
$binocheEvents = Get-Content $ledger | ConvertFrom-Json | Where-Object { $_.event -eq "binoche_decision" }
$autoApproved = ($binocheEvents | Where-Object { $_.action -eq "approve" }).Count
$automationRate = if ($binocheEvents.Count -gt 0) { ($autoApproved / $binocheEvents.Count * 100).ToString("F1") } else { "N/A" }

Write-Host "Binoche Automation: $automationRate% ($autoApproved/$($binocheEvents.Count))"
```

---

## 🎯 다음 단계

### Phase 6c: 온라인 학습 (Online Learning)

- [ ] 실시간 피드백 수집
- [ ] 가중치 적응적 조정
- [ ] 일일 재학습 스케줄

### Phase 6d: 메타인지 통합

- [ ] 낮은 확신도 자동 감지
- [ ] Ops Dashboard에 경고 표시
- [ ] 자동 에스컬레이션

### Phase 6e: 고도화

- [ ] Multi-judge 앙상블
- [ ] 도메인별 특화 규칙
- [ ] 사용자 선호도 학습

---

## 📝 테스트 체크리스트

- [x] BinocheDecisionEngine 단위 테스트 (4/4 통과)
- [x] Pipeline Adapter 통합 테스트 (2/2 통과)
- [ ] 실제 파이프라인 통합 테스트
- [ ] 10개 작업 실행 후 자동화율 측정
- [ ] 100개 작업 실행 후 장기 안정성 검증

---

## 🚨 주의사항

### 1. 품질 임계값 조정

현재 설정: `quality >= 0.7` 자동 승인

너무 낮으면 품질 저하, 너무 높으면 자동화율 저하.

### 2. BQI 패턴 매칭

학습 데이터에 없는 새로운 BQI 패턴은 "ask_user"로 처리됨.

### 3. Meta-cognition 확신도

시스템 확신도가 낮으면 자동 승인 불가 → 사용자 확인 요청.

---

## 📞 문제 해결

### Q: 자동화율이 목표보다 낮음 (< 70%)

**A**:

1. `binoche_persona.json` 모델 최신 버전 확인
2. 학습 데이터 품질 검증 (404 tasks 충분?)
3. 품질 임계값 낮추기 (0.7 → 0.65)

### Q: 너무 많은 작업이 자동 승인됨 (품질 저하)

**A**:

1. 품질 임계값 높이기 (0.7 → 0.75)
2. 증거 검증 강화 (evidence_ok 체크)
3. Meta-cognition 확신도 임계값 높이기

### Q: "ask_user" 비율이 너무 높음

**A**:

1. 확신도 임계값 낮추기 (0.6 → 0.55)
2. 더 많은 학습 데이터 수집 (목표: 600+ tasks)
3. BQI 패턴 다양화

---

**작성**: Gitko AI Assistant  
**최종 업데이트**: 2025-10-30
