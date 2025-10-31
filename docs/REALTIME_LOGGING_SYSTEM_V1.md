# Real-time Logging System Design v1.0

## 📋 개요

AGI 시스템의 모든 중요 이벤트를 **실시간으로** Resonance Ledger에 기록하는 통합 시스템.

### 기존 문제점

- ❌ 일일 수확 방식 (harvest_daily_conversations.ps1) - 다음날 기록
- ❌ 중요 작업 누락 (migration 등 수동 추가 필요)
- ❌ 실시간성 부족 (작업 완료 후 24시간 지연)
- ❌ 분산된 logging 로직 (memory_bus, rune/ledger, 직접 append)

### 해결 방안

- ✅ 통합 Event Emitter 라이브러리 (`event_emitter.py`)
- ✅ PowerShell 래퍼 (`emit_event.ps1`)
- ✅ 주요 workflow 포인트에 자동 emission
- ✅ Backward compatibility 유지

---

## 🏗️ 아키텍처

### 1. Core Event Emitter (`fdo_agi_repo/orchestrator/event_emitter.py`)

**주요 기능**:

- Thread-safe JSONL append
- 구조화된 이벤트 타입 (50+ categories)
- 선택적 buffering (sync/async)
- 자동 timestamp 추가 (ISO 8601 + Unix)

**API**:

```python
from orchestrator.event_emitter import emit_event

# Basic usage
emit_event('task_started', {
    'goal': 'AGI 자기교정 루프 설명',
    'priority': 'high'
}, task_id='demo-001', persona_id='gitko')

# Convenience wrappers
emit_task_lifecycle('completed', 'demo-001', 
                    quality=0.85, confidence=0.78)

emit_alert('warning', 'Proxy port not responding', 
           component='proxy', port=18091)

emit_system_event('migration', 'D to C drive', 
                  reason='SSD_performance', status='completed')
```

### 2. PowerShell Wrapper (`scripts/emit_event.ps1`)

**Usage**:

```powershell
& "$PSScriptRoot\emit_event.ps1" -EventType "system_startup" `
    -Payload @{
        component = "quick_status"
        version = "1.0"
    }

& "$PSScriptRoot\emit_event.ps1" -EventType "health_check" `
    -Payload @{
        status = "HEALTHY"
        confidence = 0.786
        quality = 0.691
    } -SessionId $SessionId
```

### 3. Event Categories

**Core AGI Lifecycle**:

- `task_started`, `task_completed`, `task_failed`
- `thesis_start`, `thesis_end`
- `synthesis_start`, `synthesis_end`
- `eval`, `rune`, `replan`

**Evidence & RAG**:

- `evidence_search`, `evidence_added`, `evidence_rejected`
- `rag_retrieval`, `citation_added`

**Self-correction**:

- `second_pass`, `quality_check`, `confidence_check`

**System Operations**:

- `system_startup`, `system_shutdown`
- `health_check`, `performance_metric`

**Infrastructure**:

- `migration`, `deployment`, `rollback`
- `configuration_change`, `scale_event`

**BQI Learning**:

- `bqi_pattern_learned`, `bqi_rule_applied`
- `binoche_decision`, `ensemble_update`

**Monitoring & Alerts**:

- `alert_triggered`, `alert_resolved`
- `threshold_exceeded`, `anomaly_detected`

**Session Management**:

- `session_start`, `session_end`
- `persona_activated`, `persona_switched`

---

## 🔌 Integration Points

### 1. Python Workflows

#### orchestrator/self_correction.py

```python
from .event_emitter import emit_event

# In evidence_correction():
emit_event("evidence_correction", {
    "pass": used_pass,
    "cache_hit": bool(cache_hit),
    "added": int(added),
    "total_citations": int(after_cnt),
}, task_id=task.task_id)
```

#### monitor/metrics_collector.py

```python
from orchestrator.event_emitter import emit_monitoring_snapshot

# In collect():
emit_monitoring_snapshot({
    'confidence': avg_confidence,
    'quality': avg_quality,
    'second_pass_rate': second_pass_rate,
    'cpu_percent': cpu_usage,
    'memory_percent': memory_usage
})
```

### 2. PowerShell Scripts

#### scripts/quick_status.ps1

```powershell
# At startup
& "$PSScriptRoot\emit_event.ps1" -EventType "system_startup" -Payload @{
    component = "quick_status"
    timestamp = (Get-Date).ToString("o")
}

# On health check
& "$PSScriptRoot\emit_event.ps1" -EventType "health_check" -Payload @{
    status = if ($Healthy) { "HEALTHY" } else { "UNHEALTHY" }
    confidence = $Metrics.confidence
    quality = $Metrics.quality
}
```

#### scripts/harvest_daily_conversations.ps1

```powershell
# Record harvest completion
& "$PSScriptRoot\emit_event.ps1" -EventType "session_harvest_completed" -Payload @{
    date = $Date
    gitko_count = $GitkoConvCount
    sena_count = $SenaConvCount
    lubit_count = $LubitConvCount
    total = $Total
}
```

### 3. ChatOps Integration

#### scripts/chatops_router.ps1

```powershell
# Record user command
& "$PSScriptRoot\emit_event.ps1" -EventType "chatops_command" -Payload @{
    command = $Say
    action = $Action
    user = $env:USERNAME
}
```

---

## 📊 Benefits

### 실시간성

- ⏱️ **즉시 기록**: 이벤트 발생과 동시에 Ledger 기록
- 🔍 **실시간 모니터링**: 작업 진행 상황 즉시 확인 가능
- 🚨 **빠른 알림**: 문제 발생 시 즉시 감지

### 구조화

- 📋 **표준 포맷**: 모든 이벤트 일관된 스키마
- 🏷️ **타입 시스템**: 50+ 이벤트 카테고리로 분류
- 🔗 **연관성 추적**: task_id, session_id로 관계 파악

### 확장성

- 🐍 **Python & PowerShell**: 양쪽 언어 모두 지원
- 🔌 **간편한 통합**: 단일 함수 호출로 이벤트 발생
- ⚡ **Async 준비**: 향후 queue 기반 buffering 가능

### 안정성

- 🔒 **Thread-safe**: Lock 기반 동시성 제어
- 🛡️ **Silent failure**: Logging 실패가 main workflow 차단 안 함
- 🔄 **Backward compatible**: 기존 append_ledger 유지

---

## 🚀 Rollout Plan

### Phase 1: Core Implementation ✅

- [x] event_emitter.py 작성
- [x] emit_event.ps1 래퍼 작성
- [x] self_correction.py 통합

### Phase 2: System Scripts 🔄

- [ ] quick_status.ps1 통합
- [ ] harvest_daily_conversations.ps1 통합
- [ ] ops_dashboard.ps1 통합
- [ ] chatops_router.ps1 통합

### Phase 3: BQI & Monitoring 📋

- [ ] binoche_online_learner.py 통합
- [ ] metrics_collector.py 통합
- [ ] alert_system.ps1 통합

### Phase 4: Advanced Features 🔮

- [ ] Queue-based buffering (high throughput)
- [ ] Event filtering/routing
- [ ] Real-time event stream (WebSocket)
- [ ] Event replay/debugging tools

---

## 📖 Usage Examples

### Example 1: Task Lifecycle

```python
# scripts/run_task.py
from orchestrator.event_emitter import emit_task_lifecycle

# Start
emit_task_lifecycle('started', task_id, 
                    goal='AGI 설명', persona='gitko')

# ... work ...

# Complete
emit_task_lifecycle('completed', task_id,
                    quality=0.85, confidence=0.78, 
                    evidence_added=5, cache_hit=True)
```

### Example 2: System Operation

```powershell
# scripts/migrate_repository.ps1

# Start
& "$PSScriptRoot\emit_event.ps1" -EventType "migration" -Payload @{
    action = "started"
    from = "D:\nas_backup"
    to = "C:\workspace\agi"
    reason = "SSD_performance"
}

# ... migration work ...

# Complete
& "$PSScriptRoot\emit_event.ps1" -EventType "migration" -Payload @{
    action = "completed"
    duration_seconds = $Duration
    files_moved = $FileCount
    status = "success"
}
```

### Example 3: Health Monitoring

```python
# monitor/metrics_collector.py
from orchestrator.event_emitter import emit_alert, emit_monitoring_snapshot

# Regular snapshot
emit_monitoring_snapshot({
    'confidence': 0.786,
    'quality': 0.691,
    'second_pass_rate': 0.137
})

# Alert on issue
if confidence < threshold:
    emit_alert('warning', 
               'Confidence below threshold',
               component='agi_core',
               confidence=confidence,
               threshold=threshold)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Ledger path (optional, default: fdo_agi_repo/memory/resonance_ledger.jsonl)
export AGI_LEDGER_PATH=/custom/path/to/ledger.jsonl

# Enable async buffering (future)
export AGI_EVENT_ASYNC=true
export AGI_EVENT_BUFFER_SIZE=100
export AGI_EVENT_FLUSH_INTERVAL=5  # seconds
```

---

## 📝 Backward Compatibility

기존 코드는 **변경 없이 작동**합니다:

```python
# Old code (still works)
from .memory_bus import append_ledger

append_ledger({
    "event": "eval",
    "task_id": task_id,
    "quality": 0.85
})

# New code (recommended)
from .event_emitter import emit_event

emit_event("eval", {
    "quality": 0.85
}, task_id=task_id)
```

---

## 🎯 Success Metrics

### Before (10/29)

- ⏱️ **Recording Delay**: 24+ hours (next day harvest)
- 📊 **Coverage**: ~70% (manual events missed)
- 🔍 **Visibility**: Low (batch processing only)

### After (Target)

- ⏱️ **Recording Delay**: <1 second (real-time)
- 📊 **Coverage**: 95%+ (automated emission)
- 🔍 **Visibility**: High (live monitoring possible)

---

## 🛠️ Testing

### Unit Test

```bash
# Test Python emitter
python -m fdo_agi_repo.orchestrator.event_emitter

# Test PowerShell wrapper
pwsh scripts/emit_event.ps1 -EventType "test_event" -Payload @{test=$true}
```

### Integration Test

```bash
# Run task with emission
python scripts/run_task.py --task-id test-001 --goal "Test real-time logging"

# Verify ledger
tail -f fdo_agi_repo/memory/resonance_ledger.jsonl | grep "test-001"
```

---

## 📚 Related Documents

- `AGI_DESIGN_01_MEMORY_SCHEMA.md` - Memory system overview
- `PHASE_CONTROLLER_E3.md` - Workflow orchestration
- `docs/MONITORING_THRESHOLDS.md` - Health check thresholds

---

## 📅 Version History

- **v1.0** (2025-10-30): Initial design
  - Core event_emitter.py
  - PowerShell wrapper
  - self_correction.py integration

---

## 👥 Authors

- Gitko (깃코) - Design & Implementation
- Ruafield - Architecture Review

---

**Last Updated**: 2025-10-30  
**Status**: Phase 1 Complete, Phase 2 In Progress
