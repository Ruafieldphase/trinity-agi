# Phase 8: 24시간 안정화 모니터링 계획

**시작일**: 2025년 11월 3일 18:30  
**예상 기간**: 24-48시간  
**목표**: Phase 7 개선사항의 실전 안정성 검증

---

## 🎯 Phase 8 목표

### 핵심 목표

**"Phase 7 개선사항이 24시간 무인 운영 환경에서 안정적으로 작동함을 검증"**

### 구체적 성과

1. **Success Rate 안정화**: 70% → 85%+ (24h 평균)
2. **Worker 중복 제거**: 2-3개 → 1개 (Mutex 효과)
3. **Auto-healing 검증**: 장애 자동 복구 5회 이상
4. **Performance Baseline**: Normal behavior 데이터 수집

---

## 📋 Task 분해

### Task 1: 현재 시스템 상태 확인 🔍

**예상 시간**: 30분

#### 목표

Phase 7 완료 후 시스템 현재 상태 파악 및 Baseline 측정

#### 세부 작업

1. **Component 상태 확인**
   - Queue Server: ✅ (<http://127.0.0.1:8091>)
   - RPA Worker: ❌ (0개 실행 중)
   - Task Watchdog: ⚠️ (2개 중복 실행!)
   - Worker Monitor: 미확인

2. **Success Rate 측정**

   ```powershell
   # 최근 1시간 Success Rate
   Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/results?count=20'
   ```

3. **중복 프로세스 정리**
   - Watchdog 2개 → 1개로 정리
   - Worker Monitor 상태 확인
   - `scripts/ensure_rpa_worker.ps1` 실행 시 재시작 지수 백오프가 적용되므로 반복 호출 간 최소 대기(기본 5s→최대 60s)를 고려

#### 완료 조건

- [ ] Queue Server: OK
- [ ] Worker: 1개 실행
- [ ] Watchdog: 1개 실행
- [ ] Worker Monitor: 상태 확인
- [ ] Success Rate: 측정 완료

---

### Task 2: Background 모니터링 시작 📊

**예상 시간**: 1시간

#### 목표

24시간 모니터링을 위한 Background 프로세스 시작

#### 세부 작업

1. **Canary Loop 시작**

   ```powershell
   # 30분 간격으로 Canary 실행
   .\scripts\start_monitor_loop_with_probe.ps1 -IntervalSeconds 1800 -DurationMinutes 1440
   ```

2. **Worker Monitor 시작**

   ```powershell
   # 5분 간격으로 Worker 상태 확인
   .\scripts\start_worker_monitor_daemon.ps1 -IntervalSeconds 300
   ```

3. **Realtime Pipeline 시작**

   ```powershell
   # 실시간 이벤트 수집 및 분석
   .\scripts\run_realtime_pipeline.ps1 -Hours 24
   ```

#### 완료 조건

- [ ] Canary Loop: 실행 중 (Background)
- [ ] Worker Monitor: 실행 중 (Background)
- [ ] Realtime Pipeline: 완료 (24h 데이터)

---

### Task 3: Normal Behavior Baseline 수립 📈

**예상 시간**: 6-8시간 (자동)

#### 목표

정상 운영 시 시스템 메트릭 수집 및 Threshold 계산

#### 수집 메트릭

1. **Success Rate**
   - Time Window: 1h, 6h, 24h
   - Threshold: 평균 - 2σ (최소 70%)

2. **Latency**
   - P50, P95, P99
   - Threshold: P95 + 2σ

3. **Worker Count**
   - Target: 1개
   - Alert: 2개 이상

4. **Queue Size**
   - Normal: 0-5
   - Warning: 6-20
   - Critical: 21+

#### 완료 조건

- [ ] 6시간 이상 데이터 수집
- [ ] Threshold 자동 계산
- [ ] Baseline 문서 생성

---

### Task 4: Auto-healing 검증 🛠️

**예상 시간**: 8-12시간 (자동)

#### 목표

Watchdog 및 Auto-recover 시스템이 장애를 자동 복구하는지 검증

#### 검증 시나리오

1. **Worker Crash 시뮬레이션**

   ```powershell
   # Worker 강제 종료
   Get-Process python | Where-Object { $_.CommandLine -like '*rpa_worker.py*' } | Stop-Process -Force
   
   # 기대: 60초 이내 자동 재시작
   ```
   - 재시작 한도 초과 시 `outputs/alerts/rpa_worker_alert.json` 생성 여부 확인 (Monitoring Report / Enhanced Dashboard에서 자동 표기)

2. **Queue Overload 시뮬레이션**

   ```powershell
   # 100개 Task 동시 Enqueue
   1..100 | ForEach-Object { .\scripts\enqueue_rpa_smoke.ps1 }
   
   # 기대: Worker가 순차 처리 (Queue Size < 20)
   ```

3. **Success Rate 하락 시뮬레이션**

   ```powershell
   # Invalid Task 반복 Enqueue
   1..20 | ForEach-Object { 
       Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8091/api/tasks' `
           -Body '{"action":"invalid_action"}' -ContentType 'application/json'
   }
   
   # 기대: Success Rate < 70% 시 Alert 발생
   ```

#### 완료 조건

- [ ] Worker Crash → 자동 재시작 (3회 이상)
- [ ] Queue Overload → 정상 처리
- [ ] Success Rate Alert → 발생 및 복구

---

### Task 5: Performance Dashboard 자동 생성 📊

**예상 시간**: 2-3시간

#### 목표

24시간 모니터링 결과를 자동으로 Dashboard에 표시

#### 생성 항목

1. **Monitoring Report (MD)**

   ```powershell
   .\scripts\generate_monitoring_report.ps1 -Hours 24
   ```

2. **Performance Dashboard (HTML)**

   ```powershell
   .\scripts\generate_enhanced_dashboard.ps1 -OpenBrowser
   ```

3. **Autopoietic Loop Report**

   ```powershell
   .\scripts\autopoietic_trinity_cycle.ps1 -Hours 24 -OpenReport
   ```

#### 완료 조건

- [ ] Monitoring Report 생성
- [ ] Performance Dashboard 생성
- [ ] Autopoietic Loop Report 생성

---

### Task 6: Phase 8 완료 보고서 📝

**예상 시간**: 1시간

#### 목표

Phase 8 검증 결과 및 Phase 9 계획 수립

#### 보고서 항목

1. **Success Rate 개선**
   - Before: 60-70%
   - After: 85%+
   - 개선율: +15-25%p

2. **Worker 중복 제거**
   - Before: 2-3개
   - After: 1개
   - 개선율: -50% ~ -66%

3. **Auto-healing 효과**
   - Crash 복구: 5회 이상
   - 평균 복구 시간: < 60s
   - Alert 정확도: 95%+

4. **Phase 9 제안**
   - ML 기반 Anomaly Detection
   - Resource Optimization (동적 할당)
   - Disaster Recovery (자동 백업)

#### 완료 조건

- [ ] 보고서 작성
- [ ] Phase 9 계획 수립
- [ ] Git Commit

---

## 🎯 성공 기준

### Critical (필수)

1. ✅ **Success Rate 85%+** (24h 평균)
2. ✅ **Worker 1개 유지** (24h 동안)
3. ✅ **Auto-healing 3회+** (자동 복구)

### Important (중요)

4. ⭐ **Queue Size < 10** (평균)
5. ⭐ **P95 Latency < 5s** (평균)
6. ⭐ **Watchdog 1개 유지** (24h 동안)

### Nice-to-have (선택)

7. 🌟 **Canary 100% Success** (24h)
8. 🌟 **Dashboard 자동 생성** (매 1h)
9. 🌟 **Alert 정확도 95%+**

---

## 📊 예상 타임라인

```
Day 1 (2025-11-03)
18:30 - Task 1: 현재 상태 확인 (30m)
19:00 - Task 2: Background 모니터링 시작 (1h)
20:00 - Task 3: Baseline 수립 시작 (자동)

Day 2 (2025-11-04)
02:00 - Task 3: Baseline 완료 (6h 데이터)
06:00 - Task 4: Auto-healing 검증 시작
14:00 - Task 4: Auto-healing 검증 완료
15:00 - Task 5: Dashboard 생성
17:00 - Task 6: 보고서 작성
18:00 - Phase 8 COMPLETE 🎉
```

---

## 🚨 알려진 이슈

### 해결 필요

1. **Watchdog 중복 실행** (2개)
   - 원인: VS Code Task 중복 시작?
   - 해결: Mutex 또는 PID file 추가

2. **Worker 0개**
   - 원인: Watchdog가 Worker를 시작하지 않음
   - 해결: ensure_rpa_worker.ps1 호출 확인

### 모니터링 필요

3. **Worker Monitor 상태 미확인**
   - 확인 필요: Background Job 또는 Scheduled Task

---

## 📝 Notes

- Phase 7에서 Worker 중복 문제를 해결했으나, Watchdog 중복 문제가 발견됨
- Mutex 방식을 Watchdog에도 적용할 필요 있음
- 24시간 모니터링 중 추가 이슈 발견 시 Phase 8.5로 긴급 수정

**상태**: 🟡 **PHASE 8 IN PROGRESS**
