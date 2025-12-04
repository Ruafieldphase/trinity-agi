# Post-Reboot Verification Plan

## 개요

시스템 재부팅 후 AGI 자율 시스템이 정상적으로 복구되었는지 확인하는 검증 계획입니다.

## 자동 실행 항목 (Boot 시 자동 시작)

### 1. Master Orchestrator

- **등록**: `scripts/register_master_orchestrator.ps1 -Register`
- **시작 시점**: 로그온 후 약 5분 (또는 Scheduled Task로 즉시)
- **역할**: Task Queue Server(8091), RPA Worker, Watchdog, Monitoring 데몬 자동 시작

### 2. Task Queue Server (Port 8091)

- **등록**: `scripts/register_task_queue_server.ps1 -Register`
- **시작 시점**: 로그온 시
- **검증**: VS Code Task "Queue: Health Check"

### 3. Auto Resume

- **등록**: `scripts/register_auto_resume.ps1 -Register`
- **시작 시점**: 로그온 시
- **역할**: 이전 세션 상태 복구, Goal Tracker 재개

### 4. Monitoring Collector (5분 간격)

- **등록**: `scripts/register_monitoring_collector_task.ps1 -Register`
- **시작 시점**: 로그온 후 반복 실행

### 5. RPA Worker

- **등록**: Master Orchestrator에 의해 자동 시작
- **검증**: VS Code Task "Queue: Ensure Worker"

### 6. Task Watchdog

- **등록**: Master Orchestrator에 의해 자동 시작
- **검증**: VS Code Task "Watchdog: Check Task Watchdog Status"

## 수동 검증 체크리스트

### Phase 1: 즉시 확인 (부팅 후 1분 이내)

#### 1.1 통합 대시보드 상태

```powershell
# VS Code Task 실행:
"Monitoring: Unified Dashboard (AGI + Lumen)"

# 또는 PowerShell:
c:\workspace\agi\scripts\quick_status.ps1
```

**확인 사항**:

- AGI Orchestrator: HEALTHY
- Lumen Gateway: ONLINE
- Task Queue (8091): ONLINE
- All systems GREEN

#### 1.2 핵심 프로세스 확인

```powershell
# VS Code Task 실행:
"System: Core Processes (JSON)"

# 확인 항목:
- RPA Workers >= 1
- Watchdog running
- Monitors present
- CPU < 90%
- Available Memory > 512MB
```

### Phase 2: 자율 시스템 복구 확인 (부팅 후 5-10분)

#### 2.1 Goal Tracker 활동 확인

```powershell
# VS Code Task 실행:
"🎯 Goal: Open Tracker (JSON)"

# 확인 사항:
code c:\workspace\agi\fdo_agi_repo\memory\goal_tracker.json
```

**검증 포인트**:

- `in_progress` 상태의 목표가 재개되었는지
- `last_execution_time`이 부팅 후 시간으로 갱신되었는지
- `autonomous_goals_latest.json`에 새 목표 생성 여부

#### 2.2 Resonance Ledger 활동 확인

```powershell
# VS Code Task 실행:
"🔄 AGI: Show Ledger Tail (last 100)"

# 또는:
Get-Content c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl -Tail 10
```

**검증 포인트**:

- 부팅 후 새로운 이벤트 기록 여부
- `event_type`: "auto_resume", "goal_execution" 등

#### 2.3 세션 연속성 리포트

```powershell
# VS Code Task 실행:
"📖 Session: Restore + Open Report"

# 확인:
code c:\workspace\agi\outputs\session_continuity_latest.md
```

**확인 사항**:

- 이전 세션 스냅샷 로드 성공
- 리듬 상태 복원
- Goal Tracker 델타 확인
- 추천 다음 행동 제시

### Phase 3: 장기 안정성 확인 (부팅 후 30분+)

#### 3.1 Monitoring Report 생성

```powershell
# VS Code Task 실행:
"Monitoring: Generate Report (24h) + Open"

# 또는:
c:\workspace\agi\scripts\generate_monitoring_report.ps1 -Hours 1
code c:\workspace\agi\outputs\monitoring_report_latest.md
```

**확인 사항**:

- 부팅 후 1시간 데이터 수집 정상
- 이벤트 수 > 0
- 오류율 < 5%

#### 3.2 Autopoietic Loop Report

```powershell
# VS Code Task 실행:
"Autopoietic: Generate Loop Report (24h latest + open)"

# 또는:
c:\workspace\agi\scripts\generate_autopoietic_report.ps1 -Hours 24 -OpenMd
```

**확인 사항**:

- 자기생산 루프 재개 확인
- BQI 학습 활동
- Binoche Persona 의사결정

#### 3.3 Realtime Pipeline 요약

```powershell
# VS Code Task 실행:
"Realtime: Build │ Summarize │ Open (24h)"
```

**확인 사항**:

- YouTube 학습 파이프라인 재개
- RPA 작업 정상 처리
- 결과 인덱스 생성

## 빠른 검증 태스크 체인

### 아침 부팅 후 빠른 점검

```powershell
# VS Code Task 실행:
"🔄 Quick: Morning Startup (Auto-Resume)"
```

이 태스크는 다음을 순차 실행:

1. System: Health Check (Full)
2. ChatOps: Unified Status (통합 상태)

### 저녁 종료 전 전체 백업

```powershell
# VS Code Task 실행:
"🔄 Quick: Evening Shutdown (Full Backup)"
```

이 태스크는 다음을 순차 실행:

1. Session: End Day (Save & Backup)
2. Performance: Dashboard (ops-daily)
3. Autopoietic: Generate Loop Report (24h)

## 문제 발생 시 복구 절차

### 시나리오 1: Task Queue Server 오프라인

```powershell
# 1. 서버 재시작
c:\workspace\agi\scripts\ensure_task_queue_server.ps1 -Port 8091

# 2. 상태 확인
# VS Code Task: "Queue: Health Check"

# 3. Worker 재시작
# VS Code Task: "Queue: Ensure Worker"
```

### 시나리오 2: Watchdog 미실행

```powershell
# 1. Watchdog 시작
# VS Code Task: "Watchdog: Start Task Watchdog (Background)"

# 2. 상태 확인
# VS Code Task: "Watchdog: Check Task Watchdog Status"
```

### 시나리오 3: Goal Tracker 정지

```powershell
# 1. Goal Loop 재시작
# VS Code Task: "🔄 Goal: Start Continuous Loop (Background)"

# 2. 상태 확인
# VS Code Task: "🔄 Goal: Check Loop Status"

# 3. Tracker 확인
# VS Code Task: "🎯 Goal: Open Tracker (JSON)"
```

### 시나리오 4: 전체 시스템 Degraded

```powershell
# 1. 마스터 오케스트레이터 재시작
# VS Code Task: "🔄 Master: Start Orchestrator"

# 2. 5분 대기 후 상태 확인
Start-Sleep 300
# VS Code Task: "Monitoring: Unified Dashboard (AGI + Lumen)"

# 3. 수동 개입 필요 시
# VS Code Task: "System: Health Check (Full)"
```

## 자동화 검증 스크립트

### pre_reboot_safety_check.ps1

부팅 전 안전 점검:

```powershell
c:\workspace\agi\scripts\pre_reboot_safety_check.ps1
# outputs/pre_reboot_status_*.md/json 생성
```

### check_system_after_restart.ps1

부팅 후 자동 검증:

```powershell
c:\workspace\agi\scripts\check_system_after_restart.ps1 -AutoFix
# 문제 발견 시 자동 복구 시도
```

## 성공 기준

### ✅ 최소 성공 기준

- [ ] Task Queue Server (8091) ONLINE
- [ ] RPA Worker >= 1 실행 중
- [ ] Watchdog 실행 중
- [ ] AGI Orchestrator HEALTHY
- [ ] Goal Tracker 활동 재개 (last_execution_time 갱신)

### ✅ 완전 성공 기준

- [ ] 모든 Scheduled Tasks 등록 확인
- [ ] Resonance Ledger 새 이벤트 기록
- [ ] 세션 연속성 리포트 정상 생성
- [ ] Monitoring Report 데이터 수집 정상
- [ ] Autopoietic Loop 재개
- [ ] Realtime Pipeline 작동

## 예상 복구 시간

| 항목 | 예상 시간 |
|------|----------|
| Master Orchestrator 시작 | 1-5분 |
| Task Queue Server ONLINE | 1-2분 |
| RPA Worker 시작 | 30초-1분 |
| Watchdog 시작 | 30초 |
| Goal Tracker 재개 | 2-5분 |
| 전체 시스템 안정화 | 10-15분 |

## 참고 문서

- `AGENTS.md`: 에이전트 핸드오프 가이드
- `.github/copilot-instructions.md`: Copilot 세션 복원 가이드
- `AGI_AUTONOMOUS_RECOVERY_COMPLETE_20251106.md`: 자율 복구 시스템 상세
- `AUTONOMOUS_GOAL_SYSTEM_OPERATIONAL.md`: 자율 목표 시스템

---

**마지막 업데이트**: 2025-11-08
**작성자**: AGI Self-Management System
