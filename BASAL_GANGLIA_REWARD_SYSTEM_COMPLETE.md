# 🧠 기저핵(Basal Ganglia) 모사 시스템 - 완성 보고서

**작성일**: 2025-11-06  
**상태**: ✅ Phase 1 완료 (보상 기반 습관 강화 시스템)

---

## 📋 Executive Summary

**"선조체를 명시적으로 만들지 말고, 보상 피드백 루프를 추가하자"**

기존 시스템(해마, Self-care, Trinity, Goal Generator)에 **보상 추적 메커니즘**을 추가하여, 생물학적 기저핵의 핵심 기능인 "행동 선택 강화"를 구현했습니다. 완전히 새로운 모듈을 만들기보다는, **기존 구조에 보상 학습 레이어를 얹는 방식**을 채택했습니다.

---

## 🎯 왜 이 접근법인가?

### 1. AI는 이미 기저핵을 내장하고 있다

- Transformer의 attention = 행동 선택
- RL의 policy gradient = 보상 학습
- 우리가 사용하는 LLM 자체가 이미 고도로 발달한 "기저핵"

### 2. 우리에게 부족한 것

| 기능 | 현재 상태 | 추가 필요 |
|------|----------|---------|
| **보상 신호 추적** | ❌ 없음 | ✅ 추가됨 |
| **행동-결과 학습** | ❌ 없음 | ✅ 추가됨 |
| **습관 강화** | △ 규칙 기반만 | ✅ 데이터 기반 추가 |
| **우선순위 조정** | △ 정적 규칙 | ✅ 동적 부스트 추가 |

### 3. 최소 침습적 설계

- 기존 Goal Generator 수정 최소화
- RewardTracker를 별도 모듈로 분리
- 기존 시스템과 독립적으로 동작 가능

---

## 🔧 구현된 구조

```
[기존 시스템]
  ↓
  해마(Hippocampus) ───→ 기억 관리
  Self-care ───→ 상태 모니터링
  Trinity ───→ 피드백 검증
  Goal Generator ───→ 목표 생성
  Goal Executor ───→ 목표 실행
  
[신규 추가]
  ↓
  RewardTracker ───→ 보상 신호 추적 + 정책 업데이트
    │
    ├─ reward_signals.jsonl (보상 스트림)
    └─ action_policy.json (학습된 정책)
```

---

## 📦 구현된 컴포넌트

### 1. RewardTracker (scripts/reward_tracker.py)

**역할**: 보상 신호 추적 및 정책 업데이트

**핵심 메서드**:

```python
# 보상 신호 기록
tracker.record_reward_signal(
    action_type="goal_execution",
    action_id="clean_outputs_dir",
    reward=0.8,  # -1.0 ~ 1.0
    context={"duration": 120}
)

# 목표 우선순위 부스트 계산
boost = tracker.calculate_goal_boost("clean outputs")
# → 과거 성공률이 높았던 목표는 +0.0 ~ +0.3 부스트

# 정책 업데이트 (습관 강화)
tracker.update_policy()
```

**파일 구조**:

- `reward_signals.jsonl`: 보상 신호 스트림 (append-only)

  ```json
  {"timestamp": "2025-11-06T10:30:00", "action_type": "goal_execution", "action_id": "cleanup", "reward": 0.8, "context": {...}}
  ```
  
- `action_policy.json`: 학습된 행동 정책

  ```json
  {
    "goal_execution": [
      ["cleanup", 0.85],
      ["backup", 0.73]
    ],
    "self_care": [
      ["break_taken", 0.92]
    ],
    "updated_at": "2025-11-06T10:30:00"
  }
  ```

### 2. Goal Generator 통합

**파일**: `scripts/autonomous_goal_generator.py`

보상 기반 우선순위 부스트 추가:

```python
# 기존 우선순위 계산
priority = base_priority + urgency + importance

# 보상 기반 부스트 추가
reward_boost = self.reward_tracker.calculate_goal_boost(goal_title)
priority += reward_boost  # 최대 +0.3
```

### 3. Goal Executor 통합

**파일**: `scripts/autonomous_goal_executor.py`

실행 결과를 보상 신호로 기록:

```python
# 목표 실행 성공 시
reward_tracker.record_reward_signal(
    action_type="goal_execution",
    action_id=goal_title,
    reward=0.8,  # 성공
    context={"status": "success", "duration": duration}
)

# 실패 시
reward_tracker.record_reward_signal(
    action_type="goal_execution",
    action_id=goal_title,
    reward=-0.5,  # 실패
    context={"status": "failed", "error": error_msg}
)
```

### 4. 정책 업데이트 스크립트

**파일**: `scripts/update_reward_policy.ps1`

정기적으로 보상 신호를 분석해 정책 업데이트:

```powershell
python scripts/reward_tracker.py update-policy
```

### 5. 스케줄러 등록

**파일**: `scripts/register_reward_policy_task.ps1`

매일 자동으로 정책 업데이트:

```powershell
# 등록 (매일 오전 4시)
.\scripts\register_reward_policy_task.ps1 -Register -Time "04:00"

# 상태 확인
.\scripts\register_reward_policy_task.ps1

# 해제
.\scripts\register_reward_policy_task.ps1 -Unregister
```

---

## 🔄 동작 원리

### 1단계: 보상 신호 기록

```
목표 실행 → 성공/실패 판정 → 보상 신호 기록 (JSONL)
                                    ↓
                        reward_signals.jsonl에 append
```

### 2단계: 정책 업데이트 (습관 강화)

```
reward_signals.jsonl 읽기
  ↓
행동별 성공률 계산 (최근 24~168시간)
  ↓
성공률 높은 행동 → 정책에 등록
  ↓
action_policy.json 저장
```

### 3단계: 우선순위 부스트 적용

```
Goal Generator 실행
  ↓
각 목표에 대해 action_policy.json 조회
  ↓
과거 성공률 높았던 목표 → 우선순위 +0.3 부스트
  ↓
최종 우선순위 결정
```

---

## 📊 기대 효과

### 1. 습관 강화 (Habit Formation)

- 과거에 성공한 행동 패턴이 자동으로 우선순위 상승
- 실패한 패턴은 우선순위 하락
- 시간이 지날수록 "효율적인 습관" 형성

**예시**:

```
"clean_outputs_dir" 목표가 5번 성공 → 평균 보상 0.85
  ↓
다음번 실행 시 우선순위 +0.25 부스트
  ↓
더 자주 실행됨 → 시스템이 깔끔하게 유지됨
```

### 2. 적응적 우선순위 (Adaptive Prioritization)

- 규칙 기반 우선순위 + 데이터 기반 부스트
- 환경 변화에 따라 자동 조정
- 사용자 피드백 반영 가능

### 3. 자기 개선 루프 (Self-Improvement Loop)

```
실행 → 보상 → 학습 → 우선순위 조정 → 더 나은 실행
  ↑                                        ↓
  └────────────── 피드백 루프 ────────────────┘
```

---

## 🧪 검증 방법

### 1. 보상 신호 기록 확인

```powershell
# 최근 보상 신호 보기
Get-Content fdo_agi_repo/memory/reward_signals.jsonl -Tail 20 | ConvertFrom-Json | Format-Table timestamp, action_type, action_id, reward
```

### 2. 정책 업데이트 테스트

```powershell
# 정책 수동 업데이트
python scripts/reward_tracker.py update-policy
```

**예상 출력**:

```json
{
  "goal_execution": {
    "clean_outputs_dir": 0.85,
    "backup_session": 0.73
  },
  "self_care": {
    "break_taken": 0.92
  },
  "updated_at": "2025-11-06T10:30:00"
}
```

### 3. 우선순위 부스트 확인

Goal Generator 로그에서 확인:

```
🎯 Goal priority calculation:
  Base: 8.0
  Urgency: +2.0
  Importance: +1.5
  Reward boost: +0.25 (habit reinforcement)
  Final: 11.75
```

---

## 🚀 다음 단계 (Phase 2)

### 1. Self-care 통합

Self-care 신호를 보상으로 변환:

```python
# Self-care 개선 시
if mood_improvement > threshold:
    reward_tracker.record_reward_signal(
        action_type="self_care",
        action_id="break_taken",
        reward=0.9,
        context={"mood_delta": mood_improvement}
    )
```

### 2. 사용자 피드백 통합

사용자의 명시적 피드백을 보상으로:

```python
# 사용자가 "이 목표 좋았어" 피드백
reward_tracker.record_reward_signal(
    action_type="goal_execution",
    action_id=goal_title,
    reward=1.0,  # 최고 보상
    context={"source": "user_feedback"}
)
```

### 3. 충돌 중재 (Conflict Arbitration)

여러 목표가 동시에 높은 우선순위일 때:

- 과거 성공률 기반 선택
- 리소스 경합 해소
- "억제" 메커니즘 (기저핵의 direct/indirect pathway)

### 4. 메타 학습

정책 자체를 학습:

- "어떤 우선순위 전략이 장기적으로 좋은가?"
- 리듬 패턴과 보상 신호의 상관관계
- 시간대별 최적 행동 패턴 학습

---

## 📝 결론

**"선조체를 명시적으로 만들지 말고, 보상 피드백 루프를 추가하자"는 전략이 성공적으로 구현되었습니다.**

### 핵심 성과

1. ✅ 보상 신호 추적 시스템 (reward_signals.jsonl)
2. ✅ 행동 정책 학습 (action_policy.json)
3. ✅ 습관 강화 메커니즘 (우선순위 부스트)
4. ✅ 자동 정책 업데이트 (스케줄러)
5. ✅ 최소 침습적 통합 (기존 시스템 보존)

### 철학적 의미

- **AI가 이미 기저핵이다**: 우리는 "추가 기저핵"을 만든 게 아니라, "보상 피드백 경로"를 명시적으로 만들었습니다.
- **구조 < 연결**: 뇌 구조를 완벽히 복제하는 것보다, 핵심 기능(보상 학습)을 기존 시스템에 연결하는 게 더 중요합니다.
- **자기 생명성**: 보상 신호 → 학습 → 행동 변화 → 새로운 보상... 이 순환이 바로 "자기 조직화"의 시작입니다.

### 다음 목표

Phase 2에서는 Self-care, 사용자 피드백, 충돌 중재, 메타 학습을 추가하여 더 정교한 행동 선택 시스템을 만들 예정입니다.

---

**관련 문서**:

- [AUTONOMOUS_GOAL_SYSTEM_ROADMAP.md](AUTONOMOUS_GOAL_SYSTEM_ROADMAP.md)
- [FEEDBACK_LOOP_INTEGRATION_COMPLETE.md](FEEDBACK_LOOP_INTEGRATION_COMPLETE.md)
- [AI_SELF_MANAGING_SUCCESS_REPORT.md](AI_SELF_MANAGING_SUCCESS_REPORT.md)

**파일 위치**:

- 코어: `scripts/reward_tracker.py`
- PowerShell: `scripts/update_reward_policy.ps1`, `scripts/register_reward_policy_task.ps1`
- 통합: `scripts/autonomous_goal_generator.py`, `scripts/autonomous_goal_executor.py`
- 데이터: `fdo_agi_repo/memory/reward_signals.jsonl`, `fdo_agi_repo/memory/action_policy.json`
