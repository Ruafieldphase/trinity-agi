# Rhythm Mode Categories

## 🎯 Overview

데몬 및 태스크를 리듬 상태(Work/Rest)에 따라 분류하고 자동 관리합니다.

---

## 📋 Category Definitions

### 🟢 Essential (24/7)

**항상 실행되어야 하는 핵심 프로세스**

- Task Queue Server (8091)
- RPA Worker (최소 1개)
- Task Watchdog
- Master Orchestrator
- Original Data API (8093)
- Observer Dashboard Server (8095)

### 🔵 Work Mode Active

**업무 시간에만 활성화**

- Worker Monitor (고빈도 체크: 5초)
- Monitoring Collector (5분 간격)
- Flow Observer (ADHD 집중도 추적)
- Music Daemon (적응형 음악)
- YouTube Bot (라이브 채팅 자동 응답)
- OBS Streaming (방송 중일 때)

### 🟣 Rest Mode Preferred

**휴식 시간에 활성화**

- Background Cache Validator (저빈도)
- Daily Maintenance (03:20 scheduled)
- Snapshot Rotation (03:15 scheduled)
- BQI Learner (03:10 scheduled)
- Ensemble Monitor (03:15 scheduled)

### 🟡 Adaptive (Frequency Adjustment)

**모드에 따라 실행 빈도 조절**

| Process | Work Interval | Rest Interval |
|---------|--------------|---------------|
| Core Probe | 10분 | 30분 |
| Monitoring Report | 1시간 | 6시간 |
| Cache Validation | 12시간 | 24시간 |
| Autopoietic Report | 매일 03:25 | 변경 없음 |

### 🔴 Optional (Conditional)

**특정 작업 시에만 필요**

- YouTube Live Observer (라이브 스트림 중)
- Canary Monitor (배포 검증 중)
- Load Testing (성능 테스트 중)
- Inbox Watcher (이메일 자동화 필요 시)

---

## 🔄 Mode Transition Rules

### Work Mode

```powershell
# Start
- Worker Monitor (5s interval)
- Flow Observer
- Music Daemon
- Monitoring Collector (5min)

# Increase Frequency
- Core Probe: 10min
- Cache Validation: 12h
```

### Rest Mode

```powershell
# Stop (권장)
- Worker Monitor (→ Watchdog만 유지)
- Flow Observer
- Music Daemon (선택적)

# Decrease Frequency
- Core Probe: 30min
- Monitoring Report: 6h
- Cache Validation: 24h
```

### Auto Mode

**시간 기반 자동 판단**

- 09:00 ~ 18:00: Work Mode
- 18:00 ~ 23:00: Adaptive (점진적 감소)
- 23:00 ~ 09:00: Rest Mode

**RHYTHM 파일 기반**

- `RHYTHM_REST_PHASE_*.md` 존재 → Rest Mode
- `RHYTHM_WORK_PHASE_*.md` 존재 → Work Mode
- 없음 → 시간 기반 판단

---

## 📊 Health Check Priority

### Critical (즉시 복구)

- Task Queue Server
- RPA Worker
- Watchdog

### Important (5분 내 복구)

- Original Data API
- Observer Dashboard

### Low Priority (24시간 내)

- Cache Validator
- Daily Maintenance

---

## 🎵 Music Daemon Special Handling

**Work Mode**

- Interval: 60초
- Threshold: 0.3 (적극적 재생)
- 감정 신호 강화

**Rest Mode**

- Interval: 300초 (5분)
- Threshold: 0.7 (보수적)
- 또는 완전 중지 (사용자 선택)

---

## 🔧 Implementation Status

- [x] Category Definition
- [ ] `rhythm_mode_manager.ps1` Script
- [ ] `config/rhythm_modes.json` Config
- [ ] DryRun Testing
- [ ] Live Mode Testing
- [ ] Master Orchestrator Integration

---

## 📝 Usage Example

```powershell
# Work 모드 전환
.\scripts\rhythm_mode_manager.ps1 -Mode work

# Rest 모드 전환
.\scripts\rhythm_mode_manager.ps1 -Mode rest

# 자동 판단
.\scripts\rhythm_mode_manager.ps1 -Mode auto

# DryRun (실제 변경 없이 미리보기)
.\scripts\rhythm_mode_manager.ps1 -Mode work -DryRun
```

---

**Last Updated**: 2025-11-10  
**Status**: Design Complete → Implementation Next
