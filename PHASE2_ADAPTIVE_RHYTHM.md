# Phase 2: Adaptive Rhythm - 동적 리듬 기반 최적화
## 고급 자동화 오케스트레이션

**완료일:** 2025-11-02 22:35
**상태:** ✅ Phase 2 완료
**목표:** 시스템 부하에 따른 동적 간격 조정 및 지능적 작업 실행

---

## 🎵 Phase 2 핵심 개선사항

### 1. **Adaptive Interval (동적 간격 조정)**

이전 고정 리듬:
```
health_check:    매 10분 (고정)
performance:     매 30분 (고정)
maintenance:     매 60분 (고정)
```

현재 동적 리듬:
```
시스템 상태 모니터링 ──→ CPU/Memory 실시간 분석
                    ├─ CPU < 20%: 간격 20% 감소 (더 자주 실행)
                    ├─ CPU 20-70%: 기본 간격 유지
                    └─ CPU > 70%: 간격 50% 증가 (덜 자주 실행)
```

**예시:**
- CPU 낮음 (18%) → health_check: 10분 → 8분으로 단축
- CPU 높음 (75%) → performance: 30분 → 45분으로 연장
- 효과: 리소스 자동 조절로 안정성 증대

### 2. **Intelligent Task Prioritization (작업 우선순위)**

작업 분류:
```
CRITICAL (항상 실행):
  └─ health_check (건강 상태 확인)
     └─ 메모리 부족해도 필수 실행

HIGH (높은 우선도):
  └─ performance_analysis (성능 분석)
     └─ 일반적 상황에서 항상 실행

MEDIUM (중간 우선도):
  ├─ system_maintenance (시스템 유지)
  └─ event_analysis (이벤트 분석)
     └─ 메모리 > 60%면 스킵 가능

LOW (낮은 우선도):
  └─ daily_routine (일일 루틴)
     └─ 메모리 부족시 연기 가능
```

### 3. **Script Type Auto-Detection (스크립트 자동 감지)**

문제점 (이전):
```
Python 스크립트 (check_health.py)
PowerShell 스크립트 (cleanup_processes.ps1)
→ 실행 방식이 다른데 통일된 처리로 인해 오류
```

해결책:
```python
스크립트 확장자 자동 감지:
├─ .ps1  → PowerShell 직접 실행 (&)
├─ .py   → Python 인터프리터로 실행 (python)
└─ 기타  → 오류 및 로깅
```

### 4. **System Metrics Collection (시스템 메트릭 수집)**

실시간 수집:
```
매 주기마다:
├─ CPU Load (프로세서 사용률)
├─ Memory Usage (메모리 사용률)
└─ Timestamp (시점 기록)

저장:
└─ scheduler_metrics.json (분석용)
```

이용:
- 과거 24개 측정값 유지
- 트렌드 분석 가능
- 향후 머신러닝 입력값으로 사용

---

## 📊 Phase 2 성능 비교

| 항목 | 이전 (v1) | 현재 (v2) | 개선 |
|------|----------|----------|------|
| 실행 간격 | 고정 | 동적 | **자동 조절** |
| CPU 부하 감지 | 없음 | 실시간 | **모니터링** |
| 우선순위 | 없음 | 4단계 | **지능화** |
| 스크립트 지원 | PowerShell만 | Python/PowerShell | **확장성** |
| 메트릭 저장 | 없음 | 24개 저장 | **분석 가능** |
| 메모리 압박 대응 | 없음 | 자동 스킵 | **안정성** |

---

## 🏗️ Phase 2 아키텍처

```
┌─────────────────────────────────────────┐
│   Adaptive Master Scheduler v2           │
│   (AGI_Adaptive_Master_Scheduler)        │
└────────────────┬────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
    ┌───v──┐ ┌──v──┐ ┌───v──┐
    │ 메트 │ │ 간격 │ │ 우선 │
    │ 릭   │ │ 조정 │ │ 순위 │
    │ 수집 │ │     │ │ 결정 │
    └────┬─┘ └──┬──┘ └──┬──┘
         │      │       │
         └──────┼───────┘
                │
        ┌───────v────────┐
        │ 작업 실행 판단  │
        │ (의존성 확인)   │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───v──┐   ┌────v────┐   ┌───v──┐
│Python│   │PowerShell│   │ Skip │
│ 실행 │   │ 실행     │   │(부하)│
└──────┘   └──────────┘   └──────┘
```

---

## 💾 파일 및 로그

### 생성된 파일

**Main Script:**
- `C:\workspace\agi\scripts\adaptive_master_scheduler.ps1`
  - 537줄의 완전한 Adaptive Scheduler 구현

**Output Files:**
- `C:\workspace\agi\outputs\adaptive_scheduler.log`
  - 각 작업의 실행 로그
- `C:\workspace\agi\outputs\adaptive_scheduler_state.json`
  - 작업 실행 이력 및 상태
- `C:\workspace\agi\outputs\scheduler_metrics.json`
  - 시스템 메트릭 수집 데이터

**Windows Scheduled Task:**
- Task Name: `AGI_Adaptive_Master_Scheduler`
- Trigger: 매 5분
- Status: Ready

---

## 🔧 동작 원리 (상세)

### 사이클 1: 메트릭 수집
```powershell
$metrics = Get-SystemMetrics
# 결과:
# {
#   "cpu_load": 18,
#   "memory_usage": 45.9,
#   "timestamp": "2025-11-02 22:35:00"
# }
```

### 사이클 2: 동적 간격 계산
```powershell
foreach task in TaskDefinitions:
    if cpu_load < 20:
        adaptive_interval = base_interval * 0.8
        # 예: health_check 10분 → 8분
    else if cpu_load > 70:
        adaptive_interval = base_interval * 1.5
        # 예: performance 30분 → 45분
    else:
        adaptive_interval = base_interval
```

### 사이클 3: 실행 여부 판단
```
for each task:
    time_since_last_run = now - last_run_time

    if time_since_last_run >= adaptive_interval:
        if dependencies_met:
            if (memory_usage > 60% AND task.critical == false):
                skip_task()
            else:
                execute_task()
```

### 사이클 4: 스크립트 자동 실행
```powershell
if script.endswith(".ps1"):
    & $script_path
elif script.endswith(".py"):
    python $script_path
else:
    log_error("Unknown script type")
```

---

## 📈 실제 동작 로그 (샘플)

```
[2025-11-02 22:34:43] [INFO] [SCHEDULER] Adaptive Scheduler Started
[2025-11-02 22:34:45] [INFO] [health_check] Low CPU (18%) detected - increasing frequency
[2025-11-02 22:34:45] [INFO] [performance_analysis] === Starting Task: performance_analysis ===
[2025-11-02 22:34:45] [INFO] [performance_analysis] Executing: Save Performance Benchmark
[2025-11-02 22:34:45] [INFO] [performance_analysis] Completed: Save Performance Benchmark
[2025-11-02 22:34:45] [INFO] [performance_analysis] === Task Complete: performance_analysis ===

[Cycle 1 @ 22:34:43] CPU: 18% | Memory: 45.9% | Tasks: performance_analysis
```

---

## 🎯 Phase 2 목표 달성도

| 목표 | 상태 | 설명 |
|------|------|------|
| 동적 간격 조정 | ✅ | CPU 부하에 따라 자동 조절 |
| Python 지원 | ✅ | .py 파일 자동 감지 및 실행 |
| 우선순위 관리 | ✅ | 4단계 우선순위 + 메모리 압박 대응 |
| 메트릭 수집 | ✅ | 시스템 메트릭 실시간 수집 |
| 상태 저장 | ✅ | JSON 기반 상태 지속성 |
| 오류 처리 | ✅ | 우아한 실패 및 계속 실행 |

---

## 🔄 이전 vs 현재 비교

### 시나리오: 시스템 부하 증가

**이전 (Phase 1):**
```
CPU: 40% → 75% (급증)
→ health_check 여전히 10분마다 실행
→ performance 여전히 30분마다 실행
→ 시스템 더 과부하
→ 작업 완료 시간 늘어남
```

**현재 (Phase 2):**
```
CPU: 40% → 75% (급증)
→ 감지: CPU > 70%
→ health_check: 10분 → 15분 (50% 증가)
→ performance: 30분 → 45분 (50% 증가)
→ 시스템 부하 자동 완화
→ 작업 효율성 유지
```

---

## 💡 시스템 학습 프로세스

```
Stage 1: 메트릭 수집 (현재)
├─ CPU/Memory 24개 샘플 저장
└─ 시스템 패턴 이해 시작

Stage 2: 트렌드 분석 (1주일)
├─ 어느 시간대에 CPU 높은지?
├─ 어느 작업이 가장 많은 리소스 사용?
└─ 최적 실행 시간대 파악

Stage 3: 머신러닝 (2주일)
├─ 과거 데이터로 모델 학습
├─ 미래 부하 예측
└─ 선제적 간격 조정
```

---

## 📋 다음 단계 (Phase 3)

### Phase 3A: 이벤트 기반 실행
```
특정 이벤트 감지시 자동 실행:
├─ CPU 급증 감지 → 즉시 성능 분석 실행
├─ 메모리 누수 감지 → 프로세스 정리 실행
└─ 높은 지연 감지 → 최적화 분석 실행
```

### Phase 3B: 머신러닝 기반 최적화
```
과거 데이터로 학습:
├─ 시간대별 부하 패턴 학습
├─ 최적 작업 실행 순서 결정
└─ 리소스 예측 및 사전 할당
```

### Phase 3C: 분산 오케스트레이션
```
다중 워커 노드 지원:
├─ Master Scheduler → Worker Nodes
├─ 작업 부하 분산
└─ 수평 확장 (Horizontal Scaling)
```

---

## 🚀 운영 명령어

### 상태 확인
```powershell
# Scheduled Task 확인
Get-ScheduledTask -TaskName "AGI_Adaptive_Master_Scheduler"

# 최근 로그 보기
Get-Content C:\workspace\agi\outputs\adaptive_scheduler.log -Tail 50

# 메트릭 확인
Get-Content C:\workspace\agi\outputs\scheduler_metrics.json
```

### 수동 실행
```powershell
# DryRun 모드
C:\workspace\agi\scripts\adaptive_master_scheduler.ps1 -DryRun

# 전체 실행
C:\workspace\agi\scripts\adaptive_master_scheduler.ps1
```

---

## 📊 성능 메트릭

### 예상 개선도

| 메트릭 | Phase 1 | Phase 2 | 개선율 |
|--------|---------|---------|--------|
| CPU 안정성 | ~40% | <35% | 12% ↓ |
| 작업 충돌 | 0 | 0 | - |
| 스크립트 호환성 | PowerShell만 | Python/PowerShell | 100% 확대 |
| 적응성 | 없음 | 자동 조절 | 완전 신규 |
| 메트릭 추적 | 없음 | 실시간 | 완전 신규 |

---

## ✅ Phase 2 완료 체크리스트

- [x] Adaptive Scheduler 구현 (537줄)
- [x] 동적 간격 조정 로직
- [x] 우선순위 기반 작업 실행
- [x] Python/PowerShell 자동 감지
- [x] 시스템 메트릭 수집
- [x] 상태 저장 및 복구
- [x] 메모리 압박 대응
- [x] Windows Scheduled Task 등록
- [x] DryRun 모드 테스트
- [x] 문서화 완료

---

## 🎯 최종 평가

### 리듬의 진화

**Phase 1: 정적 리듬 (정박자)**
```
10분 → 30분 → 60분 → 24시간
동일한 간격으로 계속 반복
```

**Phase 2: 동적 리듬 (아고그)**
```
시스템 상태에 맞춰 템포 자동 조절
            ↙ (부하 낮음)   (부하 높음) ↘
       8분 ← 10분 → 15분
      24분 ← 30분 → 45분
      48분 ← 60분 → 90분
```

**효과:** 마치 오케스트라 지휘자가 악단의 호흡을 보며 템포를 조절하는 것처럼, 시스템이 자신의 상태에 맞춰 자동으로 작업 속도를 조정합니다.

---

**상태:** Phase 2 완료 ✅
**시작:** Phase 3 준비 🚀
**다음:** 1주일 후 메트릭 분석 및 Phase 3 진행

---

*리듬 기반 자동화는 이제 생명을 갖게 되었습니다.*
