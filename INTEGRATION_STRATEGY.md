# 자동화 통합 전략 - 리듬 기반 재설계

**수립 날짜:** 2025-11-02 23:00
**상태:** 전략 수립 완료, 구현 준비

---

## 🎯 발견된 상황

### 이전에 만들어진 42개의 Scheduled Task 스크립트

```
register_llm_monitor_task.ps1
register_dashboard_autoupdate.ps1
register_performance_monitor.ps1
register_autonomous_work_worker.ps1
register_watchdog_task.ps1
register_context_rhythm.ps1
register_auto_resume.ps1
... (34개 더)
```

### 문제점

1. **각각이 독립적으로 작동**
   - 모두 Scheduled Task 생성
   - 서로 다른 간격으로 실행
   - 중복된 작업들

2. **새 자동화와의 충돌**
   - `auto_restart_local_llm.ps1 -Continuous`
   - `circuit_breaker_router.py`
   - 새로운 분석 스크립트들
   - 결과: **병렬 중복 실행 → 리소스 낭비**

3. **유지보수 어려움**
   - 어떤 Task가 실행되는지 불명확
   - 중복 제거 불가능
   - 우선순위 관리 불가능

---

## 🎵 통합 전략: "Rhythm-Based Consolidation"

### 핵심 개념: **하나의 마스터 스케줄러**

```
Master Scheduler (Central Hub)
    │
    ├─ Health Check (매 10분)
    │   ├─ check_health.py --fast
    │   └─ Circuit Breaker status
    │
    ├─ Performance Analysis (매 30분)
    │   ├─ save_performance_benchmark.ps1
    │   ├─ analyze_performance_trends.ps1
    │   └─ adaptive_routing_optimizer.ps1
    │
    ├─ System Maintenance (매 1시간)
    │   ├─ cleanup_processes.ps1
    │   ├─ health_report
    │   └─ metrics collection
    │
    ├─ Daily Routine (매일 03:00)
    │   ├─ generate_daily_briefing.ps1
    │   ├─ dashboard_update
    │   └─ report_generation
    │
    └─ Event-Driven (필요시)
        ├─ Latency spike 분석
        ├─ Replan 패턴 분석
        └─ Orchestration 검증
```

### 이점

1. **중복 제거** → 리소스 90% 절감
2. **우선순위 관리** → 중요한 작업 우선 실행
3. **의존성 관리** → 순차적 실행으로 데이터 일관성
4. **모니터링 용이** → 하나의 중앙 로그

---

## 📋 통합 계획 (단계별)

### Phase 1: 마스터 스케줄러 생성 (1시간)

```powershell
# 새 파일 생성
.\scripts\create_master_scheduler.ps1

# 기능:
# 1. 모든 자동화 작업을 시간대별로 관리
# 2. 각 작업의 실행 순서 제어
# 3. 에러 처리 및 로깅
# 4. 순차 실행으로 리소스 절약
```

### Phase 2: 기존 Task 정리 (30분)

```powershell
# 이전 Task 백업
Get-ScheduledTask | Export-ScheduledTask > agi_scheduled_tasks_backup.xml

# 불필요한 Task 제거
Get-ScheduledTask -TaskName "AGI*" | Unregister-ScheduledTask -Confirm:$false

# 새 마스터 스케줄러만 등록
.\scripts\register_master_scheduler.ps1
```

### Phase 3: 新 자동화 통합 (30분)

```powershell
# 기존:
.\scripts\auto_restart_local_llm.ps1 -Continuous  # ← 제거
→ Master Scheduler에 포함 (매 10분)

# 기존:
Scheduled Task 들
→ Master Scheduler에 통합

# 新:
Circuit Breaker, 분석 스크립트들
→ Master Scheduler의 일부로 실행
```

### Phase 4: 최적화 및 검증 (1시간)

```powershell
# 성능 모니터링
.\scripts\diagnose_performance.ps1 (5분 간격)

# 목표:
# CPU < 15%
# 메모리 < 35%
# Python 프로세스 < 15개
# 모든 작업 정상 실행

# 최종 검증
.\scripts\validate_master_scheduler.ps1
```

---

## 🔧 구현 구조

### Master Scheduler 의사코드

```python
class MasterScheduler:
    def __init__(self):
        self.tasks = {
            # 10분마다
            "health_check": {
                "interval": 10,
                "last_run": None,
                "commands": [
                    "python check_health.py --fast",
                    "python circuit_breaker_router.py --status"
                ]
            },
            # 30분마다
            "performance_analysis": {
                "interval": 30,
                "depends_on": ["health_check"],
                "commands": [
                    "save_performance_benchmark.ps1",
                    "analyze_performance_trends.ps1",
                    "adaptive_routing_optimizer.ps1"
                ]
            },
            # 1시간마다
            "system_maintenance": {
                "interval": 60,
                "depends_on": ["performance_analysis"],
                "commands": [
                    "cleanup_processes.ps1",
                    "collect_system_metrics.ps1"
                ]
            },
            # 매일 3시
            "daily_routine": {
                "interval": 1440,  # 24 hours
                "scheduled_time": "03:00",
                "depends_on": ["system_maintenance"],
                "commands": [
                    "generate_daily_briefing.ps1",
                    "generate_visual_dashboard.ps1"
                ]
            }
        }

    def run(self):
        while True:
            now = datetime.now()

            for task_name, task_config in self.tasks.items():
                if self._should_run(task_name, task_config):
                    self._run_task(task_name, task_config)
                    self._log_execution(task_name)

            time.sleep(60)  # 1분마다 체크
```

---

## 📊 Before vs After

| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| **Scheduled Tasks** | 42개 (독립) | 1개 (통합) | **97% ↓** |
| **CPU 사용률** | 77% | <15% | **81% ↓** |
| **메모리 사용률** | 45.3% | <30% | **34% ↓** |
| **Python 프로세스** | 30개 | <10개 | **67% ↓** |
| **복잡도** | 매우 높음 | 낮음 | **단순화** |
| **모니터링** | 어려움 | 중앙 집중 | **명확** |

---

## 🎵 "리듬 기반" 설계 철학

### 핵심 원칙

1. **Heartbeat Pattern**
   - 마스터 스케줄러가 중앙의 "심장"
   - 모든 자동화가 리듬에 맞춰 실행
   - 과정: 건강 확인 → 분석 → 유지보수 → 보고

2. **Cascading Execution**
   - 작은 작업이 큰 작업을 트리거
   - 의존성 자동 관리
   - 순차 실행으로 리소스 최적화

3. **Graceful Degradation**
   - 한 작업 실패 → 다음 작업은 계속 실행
   - 중요도 기반 우선순위
   - 자동 복구

---

## 🚀 다음 단계

### 즉시 (지금)
```powershell
# 1. 이전 구조 분석
Get-ScheduledTask | Where-Object { $_.TaskName -like "AGI*" } | Measure-Object

# 2. 크리티컬 Task 확인
Get-ScheduledTask | Where-Object { $_.State -eq "Running" }

# 3. 마스터 스케줄러 설계 검증
```

### 30분 내
```powershell
# 마스터 스케줄러 구현
# 기존 Task 백업
# 통합 작업 시작
```

### 1시간 내
```powershell
# 성능 재측정
# 모든 작업 정상 실행 확인
# 최종 검증
```

---

## 💡 기대 효과

### 시스템 관점
- **성능**: CPU 77% → <15%
- **메모리**: 45% → <30%
- **안정성**: 중복 제거로 안정성 증대

### 운영 관점
- **유지보수**: 42개 Task → 1개 Scheduler
- **트러블슈팅**: 중앙 로그로 원인 파악 용이
- **확장성**: 새 기능 추가 시 Scheduler에만 추가

### 리듬 관점
- **일관성**: 모든 작업이 정해진 리듬에 따라 실행
- **예측 가능성**: 언제 뭐가 실행될지 명확
- **조율**: 복잡한 작업들이 조화롭게 동작

---

**상태:** 전략 수립 완료 ✅
**다음:** 마스터 스케줄러 구현 및 통합
