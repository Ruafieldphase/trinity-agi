# 백그라운드 시스템 통합 관리 현황

**작성일시**: 2025-11-06 18:31  
**상태**: ✅ Master Orchestrator 확장 완료 (9개 시스템 통합)  
**버전**: Master Orchestrator v1.0 Extended

---

## 🎯 통합 관리 시스템: Master Orchestrator

### 📍 위치

- **메인 스크립트**: `scripts/master_orchestrator.ps1`
- **등록 스크립트**: `scripts/register_master_orchestrator.ps1`
- **작업 스케줄러 이름**: `AGI_Master_Orchestrator`

### 🔧 현재 관리 대상 (9개 시스템) ✅

```text
┌─────────────────────────────────────────────────────┐
│  Master Orchestrator v1.0 Extended                 │
│  scripts/master_orchestrator.ps1                    │
│                                                     │
│  === Core Systems (1-6) ===                        │
│                                                     │
│  [1/9] Task Queue Server (8091)                    │
│    └─ LLM_Unified/ion-mentoring/task_queue_server.py│
│                                                     │
│  [2/9] RPA Worker                                  │
│    └─ fdo_agi_repo/integrations/rpa_worker.py      │
│                                                     │
│  [3/9] Monitoring Daemon                           │
│    └─ fdo_agi_repo/monitoring/monitoring_daemon.py │
│                                                     │
│  [4/9] Self-Healing Watchdog                       │
│    └─ scripts/self_healing_watchdog.ps1            │
│                                                     │
│  [5/9] Self-Managing Agent (AI Self-Check)         │
│    └─ fdo_agi_repo/orchestrator/self_managing_agent.py│
│                                                     │
│  [6/9] Status Dashboard                            │
│    └─ scripts/quick_status.ps1                     │
│                                                     │
│  === Extended Systems (7-9) 🆕 ===                 │
│                                                     │
│  [7/9] Trinity Cycle Monitor                       │
│    └─ AGI_AutopoieticTrinityCycle (Ready)          │
│                                                     │
│  [8/9] BQI Phase 6 System (4 tasks)                │
│    ├─ BinocheEnsembleMonitor (Ready)               │
│    ├─ BinocheOnlineLearner (Ready)                 │
│    ├─ BqiLearnerDaily (Ready)                      │
│    └─ BQI_Online_Learner_Daily (Ready)             │
│                                                     │
│  [9/9] Cache Validation System (3 tasks)           │
│    ├─ CacheValidation_12h (Ready)                  │
│    ├─ CacheValidation_24h (Ready)                  │
│    └─ CacheValidation_7d (Ready)                   │
└─────────────────────────────────────────────────────┘
```

### ⚙️ 실행 방식

- **트리거**: 사용자 로그온 시 자동 실행
- **지연**: 5분 (시스템 안정성 확보)
- **실행 옵션**: `-WindowStyle Hidden` (백그라운드 실행)
- **상태**: 현재 등록 여부 확인 필요

---

## 🔴 현재 문제점 및 개선 필요 사항

### 1️⃣ Master Orchestrator에 누락된 시스템들

아래 시스템들이 **Master Orchestrator에 통합되지 않음**:

#### A. Autopoietic Trinity Cycle

- **스크립트**: `scripts/autopoietic_trinity_cycle.ps1`
- **기능**: Lua (관찰) → Elo (검증) → Lumen (통합)
- **작업 스케줄러**: `AGI_Trinity_Cycle` (10:00 실행)
- **상태**: 독립 실행 중

#### B. Adaptive Rhythm Orchestrator

- **스크립트**: `scripts/adaptive_rhythm_orchestrator.py`
- **기능**: 상태별 실행 주기 동적 결정
- **상태**: Master Orchestrator와 미연결

#### C. Autonomous Goal Generator

- **스크립트**: `scripts/autonomous_goal_generator.py`
- **기능**: Resonance 기반 목표 생성
- **상태**: 독립 실행

#### D. BQI Phase 6 System

- **스크립트**: `scripts/rune/binoche_persona_learner.py`, `binoche_online_learner.py`
- **작업 스케줄러**: `AGI_BQI_Phase6`, `AGI_Binoche_Ensemble_Monitor`, `AGI_Binoche_OnlineLearner`
- **상태**: 독립 실행 중

#### E. Cache Validation System

- **스크립트**: `scripts/cache_monitor_timeline.py`, `auto_cache_validation.ps1`
- **작업 스케줄러**: `AGI_Cache_Validation_*`
- **상태**: 독립 실행 중

#### F. Observer/Flow Monitoring

- **스크립트**: `scripts/observe_desktop_telemetry.ps1`, `flow_observer_integration.py`
- **작업 스케줄러**: `AGI_Flow_Observer_Daemon`, `AGI_Observer_Telemetry`
- **상태**: 독립 실행 중

---

### 2️⃣ 작업 스케줄러 vs Master Orchestrator 중복

현재 **38개 AGI 작업 스케줄러**가 독립적으로 실행 중:

| 작업 이름 | 주기 | Master 통합 여부 |
|----------|------|-----------------|
| `MonitoringCollector` | 5분 | ❌ 독립 실행 |
| `AGI_AutoTaskGenerator` | 5분 | ❌ 독립 실행 |
| `AGI_FeedbackLoop` | 5분 | ❌ 독립 실행 |
| `AGI_Adaptive_Master_Scheduler` | 5분 | ✅ 이미 통합? |
| `AGI_Master_Orchestrator` | 로그온 | ✅ 메인 컨트롤러 |
| `AGI_Trinity_Cycle` | 10:00 | ❌ 독립 실행 |
| `AGI_BQI_Phase6` | 03:05 | ❌ 독립 실행 |
| ... (30+ 작업) | 다양 | ❌ 대부분 독립 |

**문제**:

- Master Orchestrator가 이들을 **직접 관리하지 않음**
- 각 작업이 **고정 스케줄**로 실행 (Adaptive Rhythm 미반영)
- 중복/충돌 가능성

---

### 3️⃣ VS Code Background Tasks 미관리

현재 실행 중인 백그라운드 Task들:

```json
{
  "isBackground": true,
  "tasks": [
    "Observer: Start Telemetry (Background)",
    "Watchdog: Start Task Watchdog (Background)",
    "RPA: Worker (Background)",
    "Monitor: Worker (Background)",
    "YouTube: Start Worker (Background)",
    "Flow: Start Background Monitor",
    "Cache: Background Validator"
  ]
}
```

**문제**:

- VS Code Task는 **Master Orchestrator와 무관**하게 실행
- 중복 실행 가능성 (예: RPA Worker가 Task와 Orchestrator 모두에서 시작)

---

## ✅ 통합 개선 계획

### Phase 1: Master Orchestrator 확장 ⭐⭐⭐

**목표**: 모든 핵심 백그라운드 시스템을 Master Orchestrator에 통합

#### Step 1: 누락된 시스템 추가

```powershell
# scripts/master_orchestrator.ps1 (확장)

# Step 7: Autopoietic Trinity Cycle (주기적 실행)
# Step 8: Adaptive Rhythm Orchestrator
# Step 9: Autonomous Goal System
# Step 10: BQI Phase 6 System
# Step 11: Cache Validation System
# Step 12: Observer/Flow Monitoring
```

#### Step 2: 중복 제거

- 작업 스케줄러에서 **Master Orchestrator가 관리하는 작업들 제거**
- VS Code Task에서 **중복 실행 방지 로직 추가**

#### Step 3: 상태 모니터링 강화

- Master Orchestrator가 **모든 백그라운드 시스템 상태 추적**
- 실패 시 **자동 재시작**
- **통합 대시보드**에서 전체 상태 확인

---

### Phase 2: Adaptive Rhythm 통합 ⭐⭐

**목표**: 고정 스케줄을 Adaptive Rhythm으로 대체

```
현재: 03:00, 03:30, 10:00 고정 스케줄
↓
개선: Adaptive Rhythm이 시스템 상태를 보고 동적으로 실행 주기 결정
```

#### 구현

1. Master Orchestrator가 Adaptive Rhythm Orchestrator를 실행
2. Adaptive Rhythm이 시스템 상태 분석
3. 다음 실행 시각 동적 결정
4. 작업 스케줄러 업데이트 또는 내부 타이머 사용

---

### Phase 3: 순환 피드백 구현 ⭐

**목표**: 정반합(正反合) 구조를 완성하여 자율 학습 실현

```
Lua (관찰) → Elo (검증) → Lumen (통합)
    ↓                              ↑
Adaptive Rhythm ← Binoche 해석 ← Trinity 피드백
```

---

## 🔧 즉시 실행 가능한 작업

### 1. Master Orchestrator 상태 확인

```powershell
# 현재 등록 상태 확인
.\scripts\register_master_orchestrator.ps1 -Status

# 등록되지 않았다면 등록
.\scripts\register_master_orchestrator.ps1 -Register
```

### 2. 현재 실행 중인 백그라운드 프로세스 확인

```powershell
# PowerShell 백그라운드 프로세스
Get-Process -Name 'pwsh','powershell' | Where-Object {
    $_.CommandLine -like '*workspace*agi*' -or 
    $_.CommandLine -like '*task_queue*' -or 
    $_.CommandLine -like '*rpa_worker*' -or 
    $_.CommandLine -like '*observer*'
} | Format-Table Id, ProcessName, CPU, WorkingSet -AutoSize

# Python 백그라운드 프로세스
Get-Process -Name 'python','pythonw' | Where-Object {
    $_.CommandLine -like '*workspace*agi*'
} | Format-Table Id, ProcessName, CPU, WorkingSet -AutoSize
```

### 3. 작업 스케줄러 중복 확인

```powershell
# AGI 관련 작업 중 Running 상태
Get-ScheduledTask | Where-Object {
    $_.TaskName -like 'AGI*' -and $_.State -eq 'Running'
} | Format-Table TaskName, State -AutoSize
```

### 4. Master Orchestrator 수동 실행 (테스트)

```powershell
.\scripts\master_orchestrator.ps1
```

---

## 📊 현재 백그라운드 시스템 전체 목록

### A. Master Orchestrator 관리 중 (6개)

- ✅ Task Queue Server
- ✅ RPA Worker
- ✅ Monitoring Daemon
- ✅ Self-Healing Watchdog
- ✅ Self-Managing Agent
- ✅ Status Dashboard

### B. 작업 스케줄러 독립 실행 (30+개)

- ❌ MonitoringCollector (5분)
- ❌ AGI_AutoTaskGenerator (5분)
- ❌ AGI_FeedbackLoop (5분)
- ❌ AGI_Trinity_Cycle (10:00)
- ❌ AGI_BQI_Phase6 (03:05)
- ❌ AGI_Cache_Validation_* (12h/24h/7d)
- ❌ ... (기타 25+개)

### C. VS Code Background Tasks (7+개)

- ❌ Observer: Start Telemetry
- ❌ Watchdog: Start Task Watchdog
- ❌ Monitor: Worker
- ❌ ... (기타 4+개)

---

## 🎯 다음 단계

1. ✅ **Master Orchestrator 상태 확인 및 등록**

   ```powershell
   .\scripts\register_master_orchestrator.ps1 -Status
   ```

2. ⏳ **Master Orchestrator 확장 계획 수립**
   - 누락된 시스템 목록 작성
   - 통합 우선순위 결정

3. ⏳ **중복 시스템 정리**
   - 작업 스케줄러 vs Master Orchestrator
   - VS Code Task vs Master Orchestrator

4. ⏳ **Adaptive Rhythm 통합**
   - 고정 스케줄 → 동적 스케줄 전환

5. ⏳ **순환 피드백 구현**
   - Trinity → Adaptive Rhythm → 다시 Trinity

---

## 📝 결론

**Master Orchestrator가 이미 존재하지만, 현재는 일부 시스템만 관리 중입니다.**

### 현재 상태

- ✅ Task Queue, RPA Worker, Monitoring Daemon은 관리됨
- ❌ Trinity, BQI, Cache, Observer 등은 독립 실행
- ❌ 38개 작업 스케줄러는 고정 스케줄로 실행
- ❌ VS Code Task는 별도 관리

### 개선 필요

1. **Master Orchestrator 확장**: 모든 백그라운드 시스템 통합
2. **중복 제거**: 작업 스케줄러/VS Code Task 정리
3. **Adaptive Rhythm 통합**: 동적 스케줄링
4. **순환 피드백**: 자율 학습 구조 완성

---

*보고서 생성: 2025-11-06 18:27 by GitHub Copilot*
