# Autonomous Goal Executor - Design Document

**Version**: 1.0  
**Date**: 2025-11-05  
**Status**: Phase 2 Design  
**Author**: AGI Trinity System

---

## 1. Executive Summary

Goal Executor는 **Autonomous Goal Generator**가 생성한 목표를 실제로 실행하는 자율 엔진입니다.

**핵심 기능**:

- **Goal → Task 분해**: 고수준 목표를 실행 가능한 작은 작업으로 분해
- **Task Queue 통합**: 기존 RPA Worker와 연동하여 작업 실행
- **실행 상태 추적**: 진행률, 성공/실패, 블로커 자동 감지
- **자율 재시도**: 실패 시 원인 분석 후 자동 재시도
- **피드백 루프**: 실행 결과를 Resonance Ledger에 기록하여 다음 목표 생성에 반영

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Goal Executor Engine                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Input]                                                    │
│  autonomous_goals_latest.json                               │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │  1. Goal Decomposer                          │          │
│  │     - Parse goal description                 │          │
│  │     - Extract action items                   │          │
│  │     - Generate task list                     │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │  2. Task Scheduler                           │          │
│  │     - Resolve dependencies                   │          │
│  │     - Estimate effort                        │          │
│  │     - Queue tasks                            │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │  3. Execution Monitor                        │          │
│  │     - Poll task queue server                 │          │
│  │     - Track progress                         │          │
│  │     - Detect blockers                        │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │  4. Autonomous Recovery                      │          │
│  │     - Analyze failures                       │          │
│  │     - Adjust strategy                        │          │
│  │     - Retry with modifications               │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │  5. Feedback Writer                          │          │
│  │     - Log execution events                   │          │
│  │     - Update resonance ledger                │          │
│  │     - Generate completion report             │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  [Output]                                                   │
│  - goal_execution_state.json                                │
│  - goal_completion_report.md                                │
│  - resonance_ledger.jsonl (append)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 Goal Decomposer

**책임**: 고수준 목표를 실행 가능한 작업으로 분해

**입력**:

```json
{
  "goal": "Refactor Core Components",
  "description": "Improve resonance by restructuring core logic",
  "actions": [
    "Review module architecture",
    "Identify refactoring candidates",
    "Plan incremental migration"
  ]
}
```

**출력**:

```json
{
  "tasks": [
    {
      "id": "task_001",
      "goal_id": "goal_001",
      "title": "Review module architecture",
      "type": "analysis",
      "estimated_hours": 4,
      "dependencies": [],
      "status": "pending"
    },
    {
      "id": "task_002",
      "goal_id": "goal_001",
      "title": "Identify refactoring candidates",
      "type": "analysis",
      "estimated_hours": 8,
      "dependencies": ["task_001"],
      "status": "pending"
    },
    {
      "id": "task_003",
      "goal_id": "goal_001",
      "title": "Plan incremental migration",
      "type": "planning",
      "estimated_hours": 6,
      "dependencies": ["task_002"],
      "status": "pending"
    }
  ]
}
```

**알고리즘**:

1. Action 리스트를 순회
2. 각 액션을 독립적 작업으로 변환
3. 순서가 있는 경우 의존성 추가
4. 노력 추정 (기본값: 2-8시간)

---

### 3.2 Task Scheduler

**책임**: 작업을 Task Queue에 등록하고 의존성 관리

**Task Queue 통합**:

```python
import requests

def enqueue_task(task: dict) -> str:
    """Task Queue Server에 작업 등록"""
    payload = {
        "type": "goal_execution",
        "payload": {
            "task_id": task["id"],
            "title": task["title"],
            "type": task["type"],
            "dependencies": task["dependencies"]
        }
    }
    response = requests.post(
        "http://127.0.0.1:8091/api/enqueue",
        json=payload,
        timeout=5
    )
    return response.json()["task_id"]
```

**의존성 해결**:

- DAG(Directed Acyclic Graph) 구조 검증
- 순환 의존성 감지 및 경고
- Topological Sort로 실행 순서 결정

---

### 3.3 Execution Monitor

**책임**: 실행 중인 작업 모니터링 및 상태 추적

**모니터링 주기**: 30초마다 폴링

**상태 전이**:

```
pending → queued → running → [completed | failed | blocked]
```

**Blocker 감지 규칙**:

1. **Timeout**: 예상 시간의 2배 초과
2. **Dependency Wait**: 의존 작업이 1시간 이상 대기
3. **Repeated Failure**: 3회 이상 연속 실패

**Progress Tracking**:

```json
{
  "goal_id": "goal_001",
  "status": "in_progress",
  "tasks_total": 3,
  "tasks_completed": 1,
  "tasks_failed": 0,
  "tasks_blocked": 0,
  "progress_percent": 33.3,
  "estimated_completion": "2025-11-06T12:00:00Z"
}
```

---

### 3.4 Autonomous Recovery

**책임**: 실패한 작업 자동 복구

**Recovery 전략**:

| Failure Type | Strategy |
|-------------|----------|
| **Timeout** | Increase time limit, retry |
| **Resource Unavailable** | Wait 5min, retry max 3 times |
| **Dependency Failed** | Skip task, mark goal as blocked |
| **Syntax Error** | Log error, require manual fix |
| **Unknown Error** | Retry with exponential backoff |

**자율 재시도 로직**:

```python
def autonomous_retry(task: dict, failure: dict) -> bool:
    """자율 재시도 결정"""
    retry_count = task.get("retry_count", 0)
    
    if retry_count >= 3:
        return False  # Max retries reached
    
    failure_type = classify_failure(failure)
    
    if failure_type == "transient":
        # Transient errors: retry immediately
        return True
    elif failure_type == "resource":
        # Resource errors: wait and retry
        time.sleep(300)  # 5 minutes
        return True
    elif failure_type == "fatal":
        # Fatal errors: don't retry
        return False
    else:
        # Unknown: retry with backoff
        time.sleep(2 ** retry_count * 60)
        return True
```

---

### 3.5 Feedback Writer

**책임**: 실행 결과를 Resonance Ledger에 기록

**Feedback Format**:

```json
{
  "timestamp": "2025-11-05T18:30:00Z",
  "event_type": "goal_execution",
  "goal_id": "goal_001",
  "goal_title": "Refactor Core Components",
  "status": "completed",
  "tasks_completed": 3,
  "tasks_failed": 0,
  "duration_hours": 18,
  "impact": {
    "resonance_delta": +0.05,
    "entropy_delta": -0.12,
    "info_density_delta": +0.23
  },
  "lessons_learned": [
    "Incremental refactoring reduced risk",
    "Early testing caught 2 regressions"
  ]
}
```

**Resonance Ledger 통합**:

```python
import json
from pathlib import Path

def write_feedback(feedback: dict):
    """피드백을 Resonance Ledger에 추가"""
    ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
    
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(feedback, ensure_ascii=False) + "\n")
```

---

## 4. Data Schemas

### 4.1 Goal Execution State

**File**: `outputs/goal_execution_state.json`

```json
{
  "version": "1.0",
  "last_updated": "2025-11-05T18:30:00Z",
  "active_goals": [
    {
      "goal_id": "goal_001",
      "title": "Refactor Core Components",
      "priority": 13,
      "status": "in_progress",
      "started_at": "2025-11-05T10:00:00Z",
      "estimated_completion": "2025-11-06T12:00:00Z",
      "tasks": [
        {
          "task_id": "task_001",
          "title": "Review module architecture",
          "status": "completed",
          "completed_at": "2025-11-05T14:00:00Z"
        },
        {
          "task_id": "task_002",
          "title": "Identify refactoring candidates",
          "status": "running",
          "started_at": "2025-11-05T14:30:00Z"
        }
      ]
    }
  ],
  "completed_goals": [],
  "failed_goals": [],
  "blocked_goals": []
}
```

---

### 4.2 Goal Completion Report

**File**: `outputs/goal_completion_report.md`

```markdown
# Goal Execution Report

Generated: 2025-11-06 12:00:00

## Summary

- **Goals Completed**: 1
- **Goals Failed**: 0
- **Goals Blocked**: 0
- **Total Duration**: 26 hours

## Completed Goals

### 1. Refactor Core Components (Priority: 13)

**Status**: ✅ Completed  
**Duration**: 18 hours  
**Tasks Completed**: 3/3

**Impact**:
- Resonance: +0.05
- Entropy: -0.12
- Info Density: +0.23

**Lessons Learned**:
- Incremental refactoring reduced risk
- Early testing caught 2 regressions

---
```

---

## 5. Integration Points

### 5.1 Task Queue Server

**Endpoint**: `http://127.0.0.1:8091`

**APIs Used**:

- `POST /api/enqueue` - 작업 등록
- `GET /api/tasks` - 작업 목록 조회
- `GET /api/results` - 실행 결과 조회

### 5.2 RPA Worker

**Worker Pool**: `rpa_worker.py` (기존)

**통합 방식**:

- Goal Executor는 작업만 생성
- RPA Worker가 실제 실행 담당
- 결과는 Task Queue Server를 통해 수신

### 5.3 Resonance Ledger

**File**: `fdo_agi_repo/memory/resonance_ledger.jsonl`

**Write Pattern**: Append-only JSONL

**Event Types**:

- `goal_started`
- `goal_progress`
- `goal_completed`
- `goal_failed`
- `goal_blocked`

---

## 6. Safety Mechanisms

### 6.1 Resource Limits

- **Max Concurrent Goals**: 3
- **Max Tasks per Goal**: 20
- **Max Retry per Task**: 3
- **Execution Timeout**: 24 hours per goal

### 6.2 Human Override

**Manual Controls**:

- `--pause-goal <goal_id>` - 목표 일시중지
- `--cancel-goal <goal_id>` - 목표 취소
- `--force-retry <task_id>` - 작업 강제 재시도

**Approval Required**:

- High-risk operations (file deletion, system changes)
- Budget exceeds threshold (>8 hours effort)
- External API calls

---

## 7. Phase 2 Implementation Plan

### Week 1 (2025-11-12 ~ 2025-11-15)

**Goal**: Goal Decomposer + Task Scheduler 구현

**Tasks**:

1. `decompose_goal()` 함수 구현
2. `schedule_tasks()` 함수 구현
3. Task Queue 통합 테스트
4. Unit tests (coverage > 80%)

**Deliverables**:

- `scripts/autonomous_goal_executor.py` (partial)
- `tests/test_goal_executor.py`

---

### Week 2 (2025-11-18 ~ 2025-11-22)

**Goal**: Execution Monitor + Autonomous Recovery 구현

**Tasks**:

1. `monitor_execution()` 함수 구현
2. `autonomous_retry()` 함수 구현
3. Blocker 감지 로직 구현
4. End-to-end test (1개 목표 실행)

**Deliverables**:

- `scripts/autonomous_goal_executor.py` (complete)
- `outputs/goal_execution_state.json` (template)

---

### Week 3 (2025-11-25 ~ 2025-11-29)

**Goal**: Feedback Writer + System Integration

**Tasks**:

1. `write_feedback()` 함수 구현
2. Resonance Ledger 통합
3. VS Code Tasks 등록
4. Documentation 완성

**Deliverables**:

- Phase 2 완료 선언
- `AUTONOMOUS_GOAL_SYSTEM_ROADMAP.md` 업데이트

---

## 8. Success Metrics

### Phase 2 Completion Criteria

1. ✅ **Functional**:
   - 1개 이상 목표를 자율 실행 성공
   - 실패 시 자동 재시도 동작
   - 실행 결과가 Resonance Ledger에 기록

2. ✅ **Quality**:
   - Unit test coverage > 80%
   - E2E test 통과
   - No critical bugs

3. ✅ **Integration**:
   - Task Queue Server 연동 안정
   - RPA Worker 호환
   - VS Code Tasks로 실행 가능

---

## 9. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Task Queue 불안정 | High | Health check + auto-restart |
| RPA Worker 충돌 | Medium | Worker pool 분리 운영 |
| 무한 루프 | High | Max retry limit + timeout |
| 잘못된 목표 실행 | Medium | Dry-run mode + approval gate |

---

## 10. Future Enhancements (Phase 3+)

1. **Multi-Goal Parallelization**: 여러 목표 동시 실행
2. **Dynamic Replanning**: 실행 중 목표 수정
3. **Learning from Failures**: 실패 패턴 학습 및 예방
4. **Human-in-the-Loop**: 중요 결정 시 승인 요청
5. **Cross-Goal Optimization**: 목표 간 리소스 최적 분배

---

## 11. References

- [Autonomous Goal System Roadmap](../AUTONOMOUS_GOAL_SYSTEM_ROADMAP.md)
- [Goal Generator Design](./autonomous_goal_generator_design.md)
- [Task Queue Server API](../LLM_Unified/ion-mentoring/task_queue_server.py)
- [RPA Worker Implementation](../fdo_agi_repo/integrations/rpa_worker.py)
- [Resonance Ledger Format](../fdo_agi_repo/memory/resonance_ledger.jsonl)

---

**Status**: Design Complete ✅  
**Next Step**: Begin Week 1 Implementation (2025-11-12)
