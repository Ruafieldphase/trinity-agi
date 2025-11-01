# 🚀 AGI System Operations Quick Guide

> **목적**: 6대 통합 시스템의 일일 운영 가이드

**최종 업데이트**: 2025-11-01

---

## ⚡ Quick Start (처음 시작할 때)

### 1단계: VS Code Tasks 실행

**Ctrl+Shift+P** → `Tasks: Run Task` 입력

- **⭐ Quick: Daily Briefing** - 시스템 상태 확인
- **⭐ Quick: E2E Integration Test** - 전체 시스템 테스트
- **⭐ Quick: Start Auto Recovery** - 자동 복구 시작

### 2단계: 결과 확인

모든 작업은 `outputs/` 폴더에 저장됩니다:

```
outputs/
  ├── daily_briefing_YYYY-MM-DD.md      # 일일 브리핑
  ├── performance_dashboard_YYYY-MM-DD.md # 성능 대시보드
  └── e2e_test_results_*.json            # 테스트 결과
```

---

## 📅 Daily Operations (매일 할 일)

### ☀️ 아침 (출근 직후)

```powershell
# 터미널에서 실행
.\scripts\generate_daily_briefing.ps1 -OpenReport
```

또는 **VS Code Task**: `⭐ Quick: Daily Briefing`

**확인 사항**:

- [ ] 6대 시스템 상태 (PASS/FAIL)
- [ ] Resonance Ledger 최신 항목 수
- [ ] BQI Phase 6 학습 완료 여부
- [ ] YouTube Learning 실행 여부

### 🌙 저녁 (퇴근 전)

```powershell
# 성능 대시보드 확인
.\scripts\generate_performance_dashboard.ps1 -OpenDashboard
```

또는 **VS Code Task**: `⭐ Quick: Performance Dashboard`

**확인 사항**:

- [ ] 전체 성공률 90% 이상 유지
- [ ] 실패한 시스템 없음
- [ ] 자동 복구 시스템 실행 중

---

## 🔧 Troubleshooting (문제 발생 시)

### 문제 1: 시스템이 FAIL 상태

**원인 파악**:

```powershell
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube
```

**자동 복구 시도**:

```powershell
.\scripts\start_auto_recovery.ps1
```

### 문제 2: 성공률이 90% 미만

1. **대시보드 확인**:

   ```powershell
   .\scripts\generate_performance_dashboard.ps1 -OpenDashboard
   ```

2. **실패한 시스템 식별** (대시보드 "Recommendations" 섹션 참조)

3. **개별 시스템 재실행**:
   - Resonance Loop: `fdo_agi_repo\scripts\test_self_correction.ps1`
   - BQI Phase 6: `fdo_agi_repo\scripts\run_bqi_learner.ps1 -Phase 6`
   - Feedback: `fdo_agi_repo\scripts\test_feedback_engine.ps1`

### 문제 3: 자동 복구가 작동하지 않음

```powershell
# 상태 확인
.\scripts\start_auto_recovery.ps1 -Status

# 재시작
.\scripts\stop_auto_recovery.ps1
.\scripts\start_auto_recovery.ps1
```

---

## 📊 Weekly Operations (주 1회)

### 매주 월요일

```powershell
# 7일간 성과 리포트
.\scripts\generate_performance_dashboard.ps1 -Days 7 -OpenDashboard -ExportJson
```

**체크리스트**:

- [ ] 7일 평균 성공률 확인
- [ ] 트렌드 분석 (개선/악화)
- [ ] 반복 실패 시스템 식별
- [ ] 필요 시 수동 개입

---

## 🛠️ System Management

### 자동 복구 시스템

**시작**:

```powershell
.\scripts\start_auto_recovery.ps1
```

**중지**:

```powershell
.\scripts\stop_auto_recovery.ps1
```

**상태 확인**:

```powershell
.\scripts\start_auto_recovery.ps1 -Status
```

**동작 방식**:

- 5분마다 시스템 상태 체크
- 실패 시 자동 재시도 (최대 3회)
- 로그: `outputs/auto_recovery_log.jsonl`

### 수동 테스트

**전체 시스템**:

```powershell
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube
```

**개별 시스템** (VS Code Tasks 이용):

- `AGI: Summarize Ledger (24h)` - Resonance Loop
- `BQI: Run Phase 6 (Full Pipeline)` - BQI Phase 6
- `YouTube (8092): Smoke E2E` - YouTube Learning

---

## 📁 Important Files & Locations

### 스크립트

```
scripts/
  ├── generate_daily_briefing.ps1      # 일일 브리핑
  ├── run_e2e_integration_test.ps1     # E2E 테스트
  ├── generate_performance_dashboard.ps1 # 성능 대시보드
  ├── auto_recovery_system.ps1         # 복구 로직
  ├── start_auto_recovery.ps1          # 복구 시작
  └── stop_auto_recovery.ps1           # 복구 중지
```

### 출력 파일

```
outputs/
  ├── daily_briefing_*.md              # 일일 상태
  ├── performance_dashboard_*.md       # 성능 분석
  ├── performance_metrics_*.json       # 메트릭 (JSON)
  ├── e2e_test_results_*.json          # 테스트 결과
  └── auto_recovery_log.jsonl          # 복구 로그
```

### 시스템 데이터

```
fdo_agi_repo/memory/
  └── resonance_ledger.jsonl           # Resonance Loop 데이터

fdo_agi_repo/outputs/
  ├── bqi_pattern_model.json           # BQI 모델
  ├── feedback_prediction_model.json   # Feedback 모델
  └── binoche_persona.json             # Persona 모델
```

---

## 🚨 Emergency Procedures

### 긴급 상황 1: 시스템 전체 다운

```powershell
# 1. 자동 복구 중지
.\scripts\stop_auto_recovery.ps1

# 2. 수동 재시작
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube

# 3. 복구 재시작
.\scripts\start_auto_recovery.ps1
```

### 긴급 상황 2: 디스크 공간 부족

```powershell
# 오래된 로그 정리 (7일 이상)
.\LLM_Unified\ion-mentoring\scripts\cleanup_old_logs.ps1 -KeepDays 7
```

### 긴급 상황 3: Resonance Ledger 손상

```powershell
# 백업 확인
ls fdo_agi_repo\memory\resonance_ledger.jsonl.backup*

# 복구 (가장 최근 백업)
copy fdo_agi_repo\memory\resonance_ledger.jsonl.backup.YYYYMMDD `
     fdo_agi_repo\memory\resonance_ledger.jsonl
```

---

## 📞 Support & Documentation

### 상세 문서

- **아키텍처**: `ARCHITECTURE_OVERVIEW.md`
- **완료 보고서**: `PROJECT_COMPLETION.md`
- **Phase 5 완료**: `PHASE_5_COMPLETION_REPORT.md`

### 로그 확인

```powershell
# 자동 복구 로그
Get-Content outputs\auto_recovery_log.jsonl -Tail 10

# Resonance Ledger
Get-Content fdo_agi_repo\memory\resonance_ledger.jsonl -Tail 20

# 시스템 상태
Get-Content outputs\quick_status_latest.json
```

---

## ✅ Daily Checklist

### 아침 (10분)

- [ ] Daily Briefing 확인
- [ ] 6대 시스템 상태 확인
- [ ] 자동 복구 시스템 실행 중 확인

### 저녁 (5분)

- [ ] Performance Dashboard 확인
- [ ] 성공률 90% 이상 확인
- [ ] 문제 시스템 없음 확인

### 주간 (15분)

- [ ] 7일 리포트 생성
- [ ] 트렌드 분석
- [ ] 반복 문제 식별 및 조치

---

## 🎯 Success Metrics

**목표 KPI**:

- ✅ 전체 시스템 성공률: **≥ 90%**
- ✅ 일일 가동률: **≥ 95%**
- ✅ 평균 복구 시간: **≤ 10분**
- ✅ Resonance Loop 증분: **≥ 1/day**

**현재 상태**:

```powershell
.\scripts\generate_performance_dashboard.ps1
```

---

**마지막 업데이트**: 2025-11-01  
**담당자**: AGI Operations Team  
**버전**: v1.0
