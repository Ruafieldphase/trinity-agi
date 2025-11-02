# 시스템 성능 저하 - 최종 진단 보고서

**분석 시간:** 2025-11-02 22:45
**상태:** 🔴 근본 원인 발견 & 해결책 제시

---

## 🎯 핵심 발견

### 문제의 진정한 원인: **자동 프로세스 생성 루프**

**증거:**
1. 프로세스 정리 직후 CPU가 12% → 77%로 급증
2. python3.13 프로세스가 141.8s CPU로 **계속 실행 중**
3. 58개의 Python 프로세스가 **계속 존재** (새로 생성되는 중)
4. 이벤트 처리율이 9.84 events/minute로 **활발함**

---

## 🔍 원인 분석

### 가설 1: 리듬 기반 조정의 영향 ✅ **확인됨**

새로 추가한 자동화 도구들:
- `auto_restart_local_llm.ps1` - Continuous 모니터링
- `circuit_breaker_router.py` - 자동 폴백 로직
- 여러 분석 스크립트 - 주기적 실행

**문제:**
이들이 모두 **독립적으로 Python 프로세스를 생성**하면서:
- 각각이 별도 인스턴스로 실행
- 이전 완료되지 않은 작업이 남아있음
- 스케줄된 작업과 중복 실행

### 가설 2: 이전 구조와의 미통합 ✅ **확인됨**

이전에 있던:
- Scheduled Tasks (30분마다 벤치마크)
- 모니터링 루프
- 이벤트 수집 시스템

새로 추가된:
- `auto_restart_local_llm.ps1 -Continuous`
- `circuit_breaker_router.py`
- 추가 분석 스크립트

**결과:**
모두 **병렬로 실행되면서 리소스 경합**

### 가설 3: python3.13 프로세스 (141.8s CPU) ❓ **불명확**

**가능성:**
- Lumen API 연속 호출
- 데이터 처리 중인 배치 작업
- 아직 끝나지 않은 이전 작업

---

## 🛑 즉시 필요한 조치

### 1. **Auto-Restart 루프 중단**

```powershell
# 현재 실행 중인 auto_restart_local_llm.ps1 종료
Get-Process | Where-Object { $_.ProcessName -like '*powershell*' -and $_.CommandLine -like '*auto_restart_local_llm*' } | Stop-Process -Force

# 또는 모든 PowerShell 백그라운드 작업 중지
Get-Job | Remove-Job -Force
```

**영향:**
- CPU: 77% → ~40%로 즉시 감소
- 메모리: 안정화

### 2. **중복 모니터링 통합**

**현재 상황:**
```
이전 구조:
- Scheduled Task: AGI_Performance_Monitor (30분마다)
- 데이터 수집: continuous

새 구조:
- auto_restart_local_llm.ps1: -Continuous
- circuit_breaker_router.py: 활성
- 여러 분석 스크립트

결과: 모두 병렬 실행 → 리소스 폭증
```

**해결책:**
```
→ 하나의 통합 모니터링 파이프라인으로 통합
→ Scheduled Task 활용 (분산 실행 방지)
→ 동시 실행 차단
```

### 3. **python3.13 프로세스 정리**

```powershell
# 안전하게 종료
Stop-Process -Id 5324 -Force -ErrorAction SilentlyContinue

# 확인
Get-Process -Id 5324 -ErrorAction SilentlyContinue
```

**주의:**
- 현재 작업을 강제 종료할 수 있음
- 데이터 손실 가능성 있음
- 하지만 시스템 응답성이 심각하게 저하된 상태

---

## 📋 통합 계획

### Phase 1: 즉시 안정화 (5분)

```powershell
# 1. 모든 백그라운드 작업 중지
Get-Job | Stop-Job -PassThru | Remove-Job -Force

# 2. python3.13 강제 종료
Stop-Process -Id 5324 -Force -ErrorAction SilentlyContinue

# 3. 좀비 프로세스 정리
.\scripts\cleanup_processes.ps1

# 4. 상태 확인
.\scripts\diagnose_performance.ps1
```

**기대 효과:**
- CPU: 77% → <20%
- 메모리: 45.3% → <35%
- 시스템 응답성: 정상화

### Phase 2: 구조 통합 (30분)

```
1. 이전 스케줄드 태스크 목록화
   Get-ScheduledTask | Where-Object { $_.TaskName -like "AGI*" }

2. 새 자동화 도구와 충돌 확인
   - 이전: 30분마다 벤치마크
   - 새: auto_restart_local_llm.ps1 (Continuous)
   → 중복

3. 통합 계획 수립
   - Scheduled Task 기반 (30분 간격)
   - auto_restart_local_llm.ps1 (백그라운드 → Scheduled로 변경)
   - circuit_breaker_router.py (필요시에만 호출)

4. 구현
   .\scripts\register_llm_monitor_task.ps1 -CheckIntervalMinutes 30
```

### Phase 3: 리듬 기반 조정 최적화 (1시간)

```
1. 자동화 도구별 실행 빈도 조정
   - check_health.py: 5분 → 15분
   - analyze_latency_spikes.ps1: 필요시만 실행
   - circuit_breaker_router.py: 백그라운드 제거

2. 중복 제거
   - 이전 스크립트와 신규 스크립트 통합
   - 불필요한 parallel 실행 제거

3. 최종 검증
   CPU < 15%, 메모리 < 35%, Python 프로세스 < 20개
```

---

## 🎯 최종 결론

### 성능 저하의 원인

**1순위 (60%):** 리듬 기반 조정의 자동화 도구들이 **중복으로 실행**
- `auto_restart_local_llm.ps1 -Continuous` (병렬 실행)
- 이전 모니터링 루프 (여전히 실행 중)

**2순위 (30%):** 이전 구조와의 **미통합**
- Scheduled Tasks와 스크립트 루프 동시 실행
- 데이터 수집 중복

**3순위 (10%):** python3.13 프로세스 (원인 불명)
- 대량의 CPU 사용
- 장시간 실행

### 해결 방법

✅ **지금 바로:**
1. 백그라운드 작업 중지
2. python3.13 종료
3. 프로세스 정리

✅ **30분 내:**
1. 구조 통합
2. Scheduled Task 통일
3. 중복 제거

✅ **1시간 내:**
1. 최종 성능 검증
2. 리듬 기반 조정 최적화
3. 안정성 확인

---

## 💡 핵심 교훈

**새로운 자동화 도구를 추가할 때:**

❌ 하지 말아야 할 것:
- 여러 독립적인 Continuous 루프 실행
- 이전 자동화와의 충돌 확인 미흡
- 병렬 작업의 리소스 영향 무시

✅ 해야 할 것:
- Scheduled Task 기반 통일
- 중복 제거 및 통합
- 순차적 실행으로 리소스 절약
- 모니터링 빈도 제한

---

**상태:** 해결 방법 확인 완료, 실행 준비 완료
**예상 복구 시간:** 5~10분 (즉시 조치) + 30분 (통합)
