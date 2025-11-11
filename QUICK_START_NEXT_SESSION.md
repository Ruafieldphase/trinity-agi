# 🚀 Quick Start - 다음 세션용 (5분)

**마지막 업데이트**: 2025-11-06 23:35  
**현재 진행률**: 1/8 완료 (12.5%)  
**다음 작업**: Meta Supervisor 자동화 (1시간)

---

## 📋 지금 바로 시작하기

### 1️⃣ 현재 상황 파악 (2분)

```powershell
# 진단 리포트 열기
code AGI_SYSTEM_GAPS_DIAGNOSTIC_REPORT.md

# 요약 보기
code AGI_GAPS_RESOLUTION_SUMMARY.md

# 방금 완료된 Consolidation 결과
code outputs\consolidation_report_latest.md
```

### 2️⃣ 시스템 상태 확인 (1분)

```powershell
# Task Queue 서버 확인
.\scripts\queue_health_check.ps1

# Consolidation 스케줄 확인
.\scripts\register_nightly_consolidation.ps1 -Status

# 전체 시스템 상태
.\scripts\system_health_check.ps1
```

### 3️⃣ 다음 작업 시작 (즉시)

```powershell
# Meta Supervisor 파일 열기
code scripts\meta_supervisor.py

# 관련 파일도 함께
code scripts\ensure_task_queue_server.ps1
code scripts\ensure_rpa_worker.ps1
```

---

## 3️⃣ 실제 데이터 수집 (백그라운드)

```bash
# 1시간 동안 telemetry 수집
scripts/observe_desktop_telemetry.ps1 -IntervalSeconds 5 -DurationSeconds 3600
```

---

## 4️⃣ 분석 실행 (5분)

```python
from fdo_agi_repo.copilot.flow_observer_integration import FlowObserver

observer = FlowObserver()
state = observer.analyze_recent_activity(hours=1)

print(f"상태: {state.state}")
print(f"분노 강도: {state.social_context['anger_intensity']:.2%}")
print(f"두려움 증폭: {state.social_context['fear_amplification']:.2%}")
print(f"투영 점수: {state.social_context['projection_score']:.2%}")

# 리포트 생성
report = observer.generate_flow_report(hours=1)
print(report)
```

---

## 5️⃣ 핵심 파일 위치

- **구현**: `fdo_agi_repo/copilot/social_fear_analyzer.py`
- **통합**: `fdo_agi_repo/copilot/flow_observer_integration.py`
- **문서**: `SOCIAL_FEAR_INFORMATION_THEORY_COMPLETE.md`
- **Telemetry**: `fdo_agi_repo/memory/desktop_telemetry.jsonl`
- **상세 컨텍스트**: `CURRENT_WORK_SESSION_2025-11-06.md`

---

## 🎯 다음 목표

1. **검증**: 실제 데이터로 수치 확인
2. **상관관계**: Resonance Ledger와 비교
3. **개입**: 높은 fear_amplification 감지 시 알림
4. **Dashboard**: 모니터링 리포트에 추가

---

## ⚡ One-Liner

```bash
# 전체 상태 한 번에 확인
python -c "from fdo_agi_repo.copilot.flow_observer_integration import FlowObserver; print(FlowObserver().analyze_recent_activity(hours=1).social_context)"
```
