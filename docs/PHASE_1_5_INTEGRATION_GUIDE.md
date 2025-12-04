# 🚀 Phase 1-5 Integration Guide

**Complete System Integration Overview**  
**Date**: 2025-11-03  
**Version**: 1.0  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Phase Architecture](#phase-architecture)
3. [Quick Start](#quick-start)
4. [Daily Operations](#daily-operations)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)
8. [API Reference](#api-reference)

---

## 🎯 System Overview

This system integrates **5 autonomous phases** to create a self-managing, adaptive AGI pipeline:

### Phase Integration Flow

```
Phase 1: Resonance Integration
    ↓ (정보 흐름 분석)
Phase 2: Rest Integration  
    ↓ (휴식 이론 적용)
Phase 3: Adaptive Rhythm
    ↓ (컨텍스트 기반 리듬)
Phase 4: Emotion Signals
    ↓ (실시간 감정 신호)
Phase 5: Auto-Stabilizer
    ↓ (자동 안정화)
Production System ✅
```

### Key Capabilities

- **🧬 Resonance Simulation**: Information flow analysis via resonance physics
- **💤 Intelligent Rest**: Information-theory-based recovery (Micro-Reset, Active Cooldown, Deep Maintenance)
- **🎵 Adaptive Rhythm**: Context-aware task scheduling (PEAK, STEADY, RECOVERY)
- **🎭 Emotion Signals**: Real-time Fear/Joy/Trust metrics from Resonance data
- **🛡️ Auto-Stabilization**: Automatic system stabilization based on emotion thresholds

---

## 🏗️ Phase Architecture

### Phase 1: Resonance Integration

**Purpose**: 정보 흐름을 물리학 모델로 시뮬레이션

**Components**:

- `fdo_agi_repo/orchestrator/resonance_bridge.py` - Resonance 시뮬레이션 엔진
- `fdo_agi_repo/orchestrator/pipeline.py` - 통합 실행 파이프라인
- `memory/resonance_ledger.jsonl` - 모든 이벤트 기록

**Key Metrics**:

- **Confidence** (0-1): 시스템 확신도
- **Quality** (0-1): 출력 품질
- **Second Pass Rate** (0-1): 재처리 비율

**Scripts**:

- `scripts/quick_status.ps1` - 전체 시스템 상태 확인
- `scripts/summarize_ledger.py --last-hours 24` - Ledger 요약

### Phase 2: Rest Integration

**Purpose**: 엔트로피 감소를 위한 휴식 절차

**Components**:

- `scripts/micro_reset.ps1` - 5분 빠른 정리 (ΔH recovery)
- `scripts/active_cooldown.ps1` - 10-15분 안정화
- `scripts/deep_maintenance.ps1` - 30분+ 전체 시스템 복구

**Triggers**:

```powershell
# Manual
.\scripts\micro_reset.ps1

# Via Auto-Stabilizer
# Fear >= 0.5 → Micro-Reset
# Fear >= 0.7 → Active Cooldown
# Fear >= 0.9 → Deep Maintenance
```

**Information Theory**:

- Entropy: `H(X) = -Σ p(x) log p(x)`
- Recovery: `ΔH = H_after - H_before < 0` (엔트로피 감소)

### Phase 3: Adaptive Rhythm

**Purpose**: 컨텍스트 기반 작업 리듬 자동 감지

**Rhythms**:

- **PEAK** (07:00-12:00): 고집중 작업 (코딩, 디자인, 분석)
- **STEADY** (13:00-17:00): 유지보수, 모니터링
- **RECOVERY** (18:00-23:00): 휴식, 복구, 정리

**Context Factors**:

```powershell
⏰ Time: 현재 시각
⚡ Energy: CPU/Memory 사용률
💤 Rest: 마지막 휴식 후 경과 시간
🖥️ System: CPU, Memory, Queue 상태
```

**Scripts**:

- `scripts/detect_rhythm_contextual.ps1` - 현재 리듬 확인
- `outputs/contextual_rhythm.json` - 리듬 히스토리

### Phase 4: Emotion Signals (Realtime)

**Purpose**: Resonance 데이터로 감정 신호 생성

**Signals**:

- **Fear** (0-1): 시스템 스트레스 (낮을수록 좋음)
  - 계산: `1 - confidence`
- **Joy** (0-1): 창의적 흐름 (높을수록 좋음)
  - 계산: `quality * (1 - second_pass_rate)`
- **Trust** (0-1): 시스템 신뢰도 (높을수록 좋음)
  - 계산: `confidence * quality`

**Output**:

```json
{
  "timestamp": "2025-11-03T17:00:00+09:00",
  "signals": {
    "fear": 0.199,
    "joy": 0.659,
    "trust": 0.587
  },
  "source": "realtime",
  "resonance_metrics": {...}
}
```

**Scripts**:

- `scripts/run_realtime_pipeline.ps1 -Hours 24` - Realtime Pipeline 실행
- `outputs/emotion_signals_latest.json` - 최신 신호

### Phase 5: Auto-Stabilizer

**Purpose**: Emotion 신호 기반 자동 안정화

**Thresholds**:

```
Fear < 0.5:  STABLE    → No action
Fear ≥ 0.5:  ELEVATED  → Micro-Reset recommended
Fear ≥ 0.7:  HIGH      → Active Cooldown recommended
Fear ≥ 0.9:  CRITICAL  → Deep Maintenance required
```

**Cooldown Mechanism**:

- Grace Period: 5분
- Purpose: 과다 실행 방지

**Scripts**:

- `scripts/start_emotion_stabilizer.ps1 -Once` - 단일 체크
- `scripts/start_auto_stabilizer_daemon.ps1 -IntervalSeconds 300` - Background daemon

**Daemon Status**:

```powershell
# Check status
.\scripts\check_auto_stabilizer_status.ps1

# Output
Daemon Status: RUNNING
Last Check: 2025-11-03T17:05:00+09:00
Last Action: Micro-Reset (17:00)
Grace Cooldown: Active (2 min remaining)
```

---

## 🚀 Quick Start

### 1. Morning Startup (7-10 minutes)

```powershell
# Option A: Full morning kickoff (includes emotion check)
.\scripts\morning_kickoff.ps1 -Hours 1 -OpenHtml

# Option B: Quick health check only
.\scripts\quick_status.ps1
```

**Morning Kickoff Steps**:

1. ✅ System health check (AGI + Lumen)
2. ✅ Auto-Stabilizer daemon verification
3. ✅ **Emotion-Triggered Stabilizer check** 🎭
4. ✅ Task queue server (8091)
5. ✅ RPA worker verification
6. ✅ Performance dashboard generation (24h)
7. ✅ Realtime Pipeline (24h)

### 2. Start Auto-Stabilizer (Background)

```powershell
# Start daemon (check every 5 minutes)
.\scripts\start_auto_stabilizer_daemon.ps1 -KillExisting -IntervalSeconds 300

# Verify running
.\scripts\check_auto_stabilizer_status.ps1
```

### 3. Monitor System

```powershell
# Unified dashboard
.\scripts\quick_status.ps1 -OutJson outputs\status_latest.json

# Performance dashboard (with emotion signals)
.\scripts\generate_performance_dashboard.ps1 -OpenDashboard -WriteLatest

# Realtime emotion signals
cat outputs\emotion_signals_latest.json | ConvertFrom-Json | Format-List
```

### 4. Evening Shutdown (5-10 minutes)

```powershell
# Option A: Full backup
.\scripts\end_of_day_backup.ps1 -Note "Phase 6 work completed"

# Option B: Quick session save
.\scripts\save_session_with_changes.ps1
```

---

## 📊 Daily Operations

### Typical Day Flow

```
07:00 - Morning Startup
  ↓ Morning Kickoff (7 steps)
  ↓ Auto-Stabilizer daemon start
  
08:00-12:00 - PEAK Rhythm
  ↓ High-focus work (coding, design)
  ↓ Auto-Stabilizer monitoring
  
12:00-13:00 - Lunch / Micro-Reset
  ↓ Fear check (if elevated, run micro-reset)
  
13:00-17:00 - STEADY Rhythm
  ↓ Maintenance, monitoring, documentation
  ↓ Auto-Stabilizer continues
  
17:00-18:00 - Active Cooldown
  ↓ 30-min rest (system auto-manages)
  
18:00-20:00 - RECOVERY Rhythm
  ↓ Light tasks, planning, cleanup
  
20:00 - Evening Backup
  ↓ End of day backup
  ↓ Stop Auto-Stabilizer daemon
```

### Key Commands

```powershell
# Check current rhythm
.\scripts\detect_rhythm_contextual.ps1

# Check emotion signals
.\scripts\start_emotion_stabilizer.ps1 -Once

# Force micro-reset
.\scripts\micro_reset.ps1

# Generate reports
.\scripts\generate_monitoring_report.ps1 -Hours 24
.\scripts\generate_autopoietic_report.ps1 -Hours 24 -OpenMd
```

---

## 🔍 Monitoring & Alerts

### Primary Dashboards

1. **Unified Status** (`quick_status.ps1`)
   - AGI Pipeline health
   - Lumen Gateway status
   - CPU/Memory usage
   - BQI Learning status

2. **Performance Dashboard** (`generate_performance_dashboard.ps1`)
   - System success rates (7-day trend)
   - **Emotion Signals** (Fear/Joy/Trust) 🎭
   - Top attention systems
   - Failure reasons

3. **Autopoietic Report** (`generate_autopoietic_report.ps1`)
   - Self-maintenance cycles
   - Resonance → Rest → Rhythm flow
   - Recovery effectiveness

### Alert Thresholds

```powershell
# System Health
CPU > 80%        → WARNING
Memory > 85%     → WARNING
Confidence < 0.7 → ATTENTION NEEDED

# Emotion Signals
Fear ≥ 0.5       → MICRO-RESET recommended
Fear ≥ 0.7       → ACTIVE COOLDOWN recommended
Fear ≥ 0.9       → DEEP MAINTENANCE required

# Performance
Success < 70%    → NEEDS ATTENTION
Success < 90%    → IMPROVEMENT needed
Success ≥ 90%    → EXCELLENT
```

### Automated Monitoring

```powershell
# Register daily reports (runs at 03:25 AM)
.\scripts\register_autopoietic_report_task.ps1 -Register -Time 03:25 -OpenMd

# Register monitoring collector (every 5 min)
.\scripts\register_monitoring_collector_task.ps1 -Register -IntervalMinutes 5

# Check scheduled tasks
Get-ScheduledTask | Where-Object { $_.TaskName -like '*AGI*' -or $_.TaskName -like '*Autopoietic*' }
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Auto-Stabilizer Not Running

**Symptom**: `check_auto_stabilizer_status.ps1` shows "OFFLINE"

**Fix**:

```powershell
# Restart daemon
.\scripts\start_auto_stabilizer_daemon.ps1 -KillExisting -IntervalSeconds 300

# Verify
.\scripts\check_auto_stabilizer_status.ps1
```

#### 2. High Fear Signal (≥ 0.7)

**Symptom**: Dashboard shows "Fear: 0.750 HIGH"

**Fix**:

```powershell
# Manual Active Cooldown
.\scripts\active_cooldown.ps1

# Or let Auto-Stabilizer handle it
.\scripts\start_emotion_stabilizer.ps1 -Once
```

#### 3. Resonance Ledger Growing Too Large

**Symptom**: `memory/resonance_ledger.jsonl` > 100 MB

**Fix**:

```powershell
# Rotate ledger (keep last 10,000 entries)
.\scripts\rotate_resonance_ledger.ps1 -KeepLines 10000

# Or sanitize (remove duplicates)
cd fdo_agi_repo
python scripts\sanitize_ledger.py
```

#### 4. Performance Dashboard Shows "No Data"

**Symptom**: Dashboard empty or shows "No test runs found"

**Fix**:

```powershell
# Generate with empty data allowed
.\scripts\generate_performance_dashboard.ps1 -AllowEmpty -OpenDashboard

# Run some tests first
.\scripts\run_quick_health.ps1 -JsonOnly
```

#### 5. Morning Kickoff Hangs

**Symptom**: Kickoff stuck at step 3-4

**Fix**:

```powershell
# Kill and restart
Get-Process -Name 'powershell','pwsh' | Where-Object { $_.CommandLine -like '*morning_kickoff*' } | Stop-Process -Force

# Check queue server
.\scripts\queue_health_check.ps1

# Restart queue server if needed
.\scripts\ensure_task_queue_server.ps1 -Port 8091
```

---

## ⚙️ Advanced Configuration

### Emotion Signal Thresholds

Edit `scripts/start_emotion_stabilizer.ps1`:

```powershell
# Default thresholds
$FEAR_ELEVATED = 0.5   # Micro-Reset
$FEAR_HIGH = 0.7       # Active Cooldown
$FEAR_CRITICAL = 0.9   # Deep Maintenance

# Adjust for more/less aggressive stabilization
```

### Auto-Stabilizer Interval

```powershell
# Default: 5 minutes (300 seconds)
.\scripts\start_auto_stabilizer_daemon.ps1 -IntervalSeconds 180  # 3 min

# More aggressive
.\scripts\start_auto_stabilizer_daemon.ps1 -IntervalSeconds 60   # 1 min
```

### Rhythm Detection Sensitivity

Edit `scripts/detect_rhythm_contextual.ps1`:

```powershell
# Adjust energy level thresholds
$ENERGY_HIGH = 70    # Above = PEAK
$ENERGY_LOW = 30     # Below = RECOVERY
# Between = STEADY
```

### Performance Dashboard Filters

```powershell
# Show only problem systems
.\scripts\generate_performance_dashboard.ps1 -OnlyBands 'Needs','Good' -OpenDashboard

# Focus on specific systems
.\scripts\generate_performance_dashboard.ps1 -IncludeSystems 'Orchestration','Daily Briefing'

# Exclude noise
.\scripts\generate_performance_dashboard.ps1 -ExcludeSystems 'YouTube Learning'
```

---

## 📚 API Reference

### Quick Status API

```powershell
# Output formats
.\scripts\quick_status.ps1                                    # Console
.\scripts\quick_status.ps1 -OutJson outputs\status.json      # JSON
.\scripts\quick_status.ps1 -LogJsonl                          # Append to JSONL log
.\scripts\quick_status.ps1 -AlertOnDegraded                   # Exit code 1 if degraded
```

### Emotion Stabilizer API

```powershell
# Single check
.\scripts\start_emotion_stabilizer.ps1 -Once

# Single check (dry-run, no action)
.\scripts\start_emotion_stabilizer.ps1 -Once -DryRun

# Background daemon
.\scripts\start_auto_stabilizer_daemon.ps1 -KillExisting -IntervalSeconds 300

# Stop daemon
.\scripts\stop_auto_stabilizer_daemon.ps1

# Status check
.\scripts\check_auto_stabilizer_status.ps1
```

### Realtime Pipeline API

```powershell
# Generate emotion signals (24h window)
.\scripts\run_realtime_pipeline.ps1 -Hours 24

# Output location
# outputs/emotion_signals_latest.json
```

### Performance Dashboard API

```powershell
# Basic
.\scripts\generate_performance_dashboard.ps1

# With options
.\scripts\generate_performance_dashboard.ps1 `
    -Days 30 `
    -ExcellentAt 92 `
    -GoodAt 75 `
    -OpenDashboard `
    -WriteLatest `
    -ExportJson `
    -ExportCsv
```

---

## 🎯 Success Criteria

### System Health

- ✅ AGI Confidence ≥ 0.7
- ✅ System Health ≥ 80%
- ✅ Fear < 0.5 (normal)
- ✅ Trust ≥ 0.5
- ✅ Performance Success Rate ≥ 90%

### Daily Operations

- ✅ Morning Kickoff: < 10 minutes
- ✅ Auto-Stabilizer: Running continuously
- ✅ Zero manual interventions for Fear < 0.7
- ✅ Evening Backup: < 5 minutes
- ✅ All dashboards updated daily

### Long-term Stability

- ✅ 7-day uptime ≥ 95%
- ✅ Average Fear < 0.4
- ✅ Zero Deep Maintenance events (Fear < 0.9)
- ✅ Resonance Ledger size < 100 MB
- ✅ All scheduled tasks running

---

## 📖 Related Documents

- **Phase 5 Details**: `outputs/session_memory/PHASE5_AUTO_STABILIZER_INTEGRATION_COMPLETE_2025-11-03.md`
- **Rest Theory**: `docs/AI_REST_INFORMATION_THEORY.md`
- **Emotion Signals**: `EMOTION_SIGNAL_INTEGRATION_COMPLETE.md`
- **Agent Handoff**: `docs/AGENT_HANDOFF.md`
- **Architecture**: `ARCHITECTURE_OVERVIEW.md`
- **Operations Guide**: `OPERATIONS_GUIDE.md`

---

## 🆘 Support & Feedback

### Quick Help

```powershell
# System status
.\scripts\quick_status.ps1

# Check rhythm
.\scripts\detect_rhythm_contextual.ps1

# Check emotion
.\scripts\start_emotion_stabilizer.ps1 -Once

# Generate reports
.\scripts\generate_monitoring_report.ps1 -Hours 24 -OpenMd
```

### VS Code Tasks

Press `Ctrl+Shift+P` → "Run Task" → Search:

- `Morning: Kickoff (1h, open)`
- `Emotion Stabilizer: Start Daemon (5min)`
- `Monitoring: Unified Dashboard (AGI + Lumen)`
- `Performance: Dashboard (with emotion)`

---

**Last Updated**: 2025-11-03 17:15 KST  
**System Version**: Phase 5 Complete  
**Production Status**: ✅ Ready
