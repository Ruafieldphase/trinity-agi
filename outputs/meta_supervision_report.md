# 메타-감독 보고서

생성 시각: 2025-11-14 11:55:27

## 📊 전체 상태

- **상태**: 🚨 CRITICAL
- **점수**: 19.0/100
- **개입 수준**: CRITICAL

## 🔍 루프별 상태

### Self-Care

- 점수: 35.0/100
- 상태: 🚨 critical

### Goal Generation

- 점수: 30.0/100
- 상태: 🚨 critical

### Goal Execution

- 점수: 30.0/100
- 상태: 🚨 critical

### Feedback

- 점수: 0/100
- 상태: 🚨 critical

### Trinity

- 점수: 0/100
- 상태: 🚨 critical

## ⏰ 리듬 동기화

- 동기화 상태: ⚠️  비동기
- 최대 시간 차이: 784.1분

## ⚙️  자동 개입

**사유**:
- 심각한 상태: 점수 19.0/100
- 리듬 동기화 필요 (차이: 784.1분)
- Self-care 루프 점검 필요
- 목표 생성기 재실행 필요
- 피드백 분석 필요
- Trinity 사이클 누락 (선택적)

**수행된 액션**:
- ✅ `generate_goals`: 목표 생성 완료
- ✅ `emergency_recovery`: 긴급 복구 완료: Task Queue Server 재시작; RPA Worker 재시작; Self-care 요약 갱신 완료; 목표 생성 완료
- ✅ `analyze_feedback`: 분석 실패: 2025-11-14 11:54:06,074 - INFO - 🔄 피드백 분석 시작 (최근 24시간)
2025-11-14 11:54:06,077 - INFO - Goal Tracker 로드 완료: 13 goals
2025-11-14 11:54:06,883 - INFO - Resonance Ledger: 0 events (last 24h)
2025-11-14 11:54:06,884 - INFO - Self-Care 요약 로드 완료
2025-11-14 11:54:06,912 - INFO - ✅ 피드백 분석 저장: C:\workspace\agi\outputs\feedback_analysis_20251114_115406.json
2025-11-14 11:54:06,914 - INFO - 📄 Markdown 보고서 생성: C:\workspace\agi\outputs\feedback_analysis_20251114_115406.md
2025-11-14 11:54:07,071 - INFO - ✅ Latest 링크 업데이트 완료

- ✅ `update_self_care`: Self-care 요약 갱신 완료
- ✅ `notify_admin`: 알림 기록: C:\workspace\agi\outputs\meta_supervisor_alerts.log

## 🧪 셀프-검증

- **검증 강도**: STRICT

- ✅ validate_settings_json (exit 0)
- ❌ validate_observer_dashboard (exit 1)
- ✅ validate_performance_dashboard (exit 0)
- ✅ system_integration_diagnostic (exit 0)

**자동 시정 조치**:
- observer_dashboard_refresh_failed

## 💡 권장사항

- ⏰ 리듬 동기화 필요: 최대 784.1분 차이 발생
- 🛟 Self-care 루프 점검 필요: scripts/update_self_care_metrics.ps1 실행
- 🎯 목표 생성기 재실행 필요: python scripts/autonomous_goal_generator.py

## ⏭️  다음 체크

예상 시각: 2025-11-14 12:25:27

---

*이 보고서는 메타-감독 시스템에 의해 자동 생성되었습니다.*