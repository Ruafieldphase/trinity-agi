# 🎯 최종 스케줄 마이그레이션 완료 보고서

**생성 시각**: 2025-11-02 23:49  
**완료 상태**: ✅ 모든 작업 성공

---

## 📋 변경 요약

### 1️⃣ 강제 증거 점검 (Force Evidence Check)

- **변경**: 03:00 → **10:20**
- **상태**: ✅ 완료
- **Task Name**: `AGI_ForcedEvidenceCheck_Daily`
- **다음 실행**: 2025-11-03 10:20

### 2️⃣ 일일 백업 (Daily Backup)

- **변경**: 03:30 → **21:00**
- **상태**: ✅ 완료
- **Task Name**: `AGI_Auto_Backup`
- **다음 실행**: 2025-11-03 21:00

### 3️⃣ BQI Phase 6 학습 파이프라인

| 구분 | 이전 시각 | 신규 시각 | Task Name | 상태 |
|------|----------|----------|-----------|------|
| Phase 6 Persona Learner | 03:05 | **10:15** | `BQIPhase6PersonaLearner` | ✅ |
| Ensemble Monitor | 03:15 | **10:20** | `BinocheEnsembleMonitor` | ✅ |
| Online Learner | 03:20 | **10:25** | `BinocheOnlineLearner` | ✅ |

---

## 🕐 최종 스케줄 타임라인 (10:00-10:25)

```
10:00 ┬─ MonitoringSnapshotRotationDaily (스냅샷 회전 + 압축)
      └─ AGI_Morning_Kickoff (아침 킥오프)

10:05 ── MonitoringDailyMaintenance (일일 유지보수)

10:10 ── AutopoieticLoopDailyReport (자기생산 루프 리포트)

10:15 ── BQIPhase6PersonaLearner (Binoche 페르소나 학습)

10:20 ┬─ AGI_ForcedEvidenceCheck_Daily (강제 증거 점검)
      └─ BinocheEnsembleMonitor (앙상블 모니터)

10:25 ── BinocheOnlineLearner (온라인 학습)
```

---

## 🔍 전체 스케줄 맵 (시간순)

| 시각 | Task Name | 설명 | 상태 |
|------|-----------|------|------|
| **로그인 시** | TaskQueueServer, IonInboxWatcher | 자동 시작 서비스 | 🔄 |
| **5분마다** | MonitoringCollector | 메트릭 수집 | 🔄 |
| 06:00 | AGI_WakeUp | 아침 기상 | ✅ |
| **10:00** | **MonitoringSnapshotRotationDaily** | **스냅샷 회전** | ✅ |
| **10:00** | **AGI_Morning_Kickoff** | **아침 킥오프** | ✅ |
| **10:05** | **MonitoringDailyMaintenance** | **일일 유지보수** | ✅ |
| **10:10** | **AutopoieticLoopDailyReport** | **자기생산 리포트** | ✅ |
| **10:15** | **BQIPhase6PersonaLearner** | **BQI Phase 6** | ✅ |
| **10:20** | **AGI_ForcedEvidenceCheck_Daily** | **증거 점검** | ✅ |
| **10:20** | **BinocheEnsembleMonitor** | **앙상블 모니터** | ✅ |
| **10:25** | **BinocheOnlineLearner** | **온라인 학습** | ✅ |
| **21:00** | **AGI_Auto_Backup** | **일일 백업** | ✅ |
| 22:00 | AGI_Sleep | 저녁 정리 | ✅ |

---

## 🚀 아침 워크플로우 (10:00-10:30)

### PC를 10:00 전후로 켜면

1. **자동 실행 서비스** (로그인 시)
   - Task Queue Server (포트 8091)
   - Inbox Watcher (모든 에이전트)

2. **자동 실행 작업** (10:00-10:25)

   ```
   10:00 → 스냅샷 회전 + 아침 킥오프
   10:05 → 일일 유지보수 (로그 정리, 리포트 생성)
   10:10 → 자기생산 루프 리포트
   10:15 → BQI Phase 6 페르소나 학습
   10:20 → 강제 증거 점검 + 앙상블 모니터
   10:25 → 온라인 학습
   ```

3. **수동 확인** (선택)

   ```powershell
   # 큐 헬스 체크
   & C:\workspace\agi\scripts\queue_health_check.ps1
   
   # 대시보드 열기
   Start-Process C:\workspace\agi\outputs\monitoring_dashboard_latest.html
   
   # 자기생산 리포트 열기
   code C:\workspace\agi\outputs\autopoietic_loop_report_latest.md
   ```

---

## 🌙 저녁 워크플로우 (21:00)

### 21:00 자동 백업

- **Task Name**: `AGI_Auto_Backup`
- **스크립트**: `scripts/auto_backup.ps1`
- **백업 위치**: `backup/` 디렉터리
- **압축 형식**: ZIP (날짜별)

### 수동 종료 (선택)

```powershell
# 세션 저장 + 백업
& C:\workspace\agi\scripts\end_daily_session.ps1 -Note "작업 완료"

# 또는 ChatOps로
$env:CHATOPS_SAY = "일과 종료"
& C:\workspace\agi\scripts\chatops_router.ps1
```

---

## ✅ 검증 완료 항목

- [x] 모든 03:xx 스케줄 제거됨
- [x] 10:xx 스케줄 정상 등록됨
- [x] 21:00 백업 등록됨
- [x] 로그인 시 자동 시작 서비스 확인됨
- [x] 5분 수집기 유지됨
- [x] 다음 실행 시각 모두 정상 확인됨
- [x] Task State 모두 Ready 확인됨

---

## 📂 관련 파일

### 등록 스크립트

- `scripts/register_snapshot_rotation_task.ps1`
- `scripts/register_autopoietic_report_task.ps1`
- `scripts/register_daily_maintenance_task.ps1`
- `scripts/register_auto_backup.ps1`
- `fdo_agi_repo/scripts/register_forced_evidence_scheduled_task.ps1`
- `fdo_agi_repo/scripts/register_bqi_phase6_scheduled_task.ps1`
- `fdo_agi_repo/scripts/register_ensemble_monitor_task.ps1`
- `fdo_agi_repo/scripts/register_online_learner_task.ps1`

### 실행 스크립트

- `scripts/rotate_status_snapshots.ps1`
- `scripts/generate_autopoietic_report.ps1`
- `scripts/daily_monitoring_maintenance.ps1`
- `scripts/auto_backup.ps1`
- `fdo_agi_repo/scripts/run_forced_evidence_check.ps1`
- `fdo_agi_repo/scripts/run_bqi_learner.ps1`
- `fdo_agi_repo/scripts/rune/binoche_success_monitor.py`
- `fdo_agi_repo/scripts/rune/binoche_online_learner.py`

### 출력 파일

- `outputs/monitoring_dashboard_latest.html`
- `outputs/autopoietic_loop_report_latest.md`
- `outputs/ensemble_success_report.txt`
- `outputs/online_learning_log.jsonl`
- `backup/agi_backup_<date>.zip`

---

## 🔧 문제 해결

### 작업이 실행되지 않으면

```powershell
# 1. 작업 상태 확인
Get-ScheduledTask -TaskName 'BQIPhase6PersonaLearner' | Get-ScheduledTaskInfo

# 2. 수동 실행
Start-ScheduledTask -TaskName 'BQIPhase6PersonaLearner'

# 3. 로그 확인
code C:\workspace\agi\fdo_agi_repo\outputs\bqi_learner_last_run.txt
```

### Wake from Sleep가 필요하면

```powershell
# Wake 지원 확인
& C:\workspace\agi\fdo_agi_repo\scripts\check_wake_timer_support.ps1

# Wake 옵션으로 재등록 (관리자 권한 필요)
& C:\workspace\agi\fdo_agi_repo\scripts\register_bqi_phase6_scheduled_task.ps1 -Register -Time '10:15' -WakeFromSleep
```

---

## 🎉 완료

모든 스케줄이 10:00 중심으로 정상 마이그레이션되었습니다.  
PC를 내일 10:00 전후로 켜면 자동으로 모든 작업이 순차 실행됩니다.

**다음 확인 시각**: 2025-11-03(월) 10:30  
**예상 작업**: 모든 10:xx 작업 완료 확인

---

**생성자**: GitHub Copilot + PowerShell Automation  
**마지막 업데이트**: 2025-11-02 23:49
