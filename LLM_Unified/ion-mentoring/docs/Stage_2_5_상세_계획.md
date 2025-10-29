# Stage 2-5 상세 계획 📋
## Canary Deployment 단계별 실행 가이드

**작성일**: 2025-10-22  
**작성자**: 깃코 (AI Agent)  
**목적**: Week 3 Day 2-7 Canary 배포 상세 절차  
**현재 상태**: Stage 1 완료 (5% 트래픽)

---

## 📊 5-Stage Canary 배포 개요

```
Stage 1: 5%   → 24시간 모니터링 ✅ 진행 중
Stage 2: 10%  → 24시간 모니터링 ⏳ 예정
Stage 3: 25%  → 48시간 모니터링 ⏳ 예정
Stage 4: 50%  → 72시간 모니터링 ⏳ 예정
Stage 5: 100% → 프로덕션 전환   ⏳ 예정
```

---

## 🚀 Stage 2: 10% 트래픽

### 기본 정보
- **트래픽 비율**: Legacy 90% / Canary 10%
- **모니터링 기간**: 24시간
- **예정일**: 2025-10-23
- **전제 조건**: Stage 1 성공 기준 충족

---

### Stage 1 성공 기준 검증

#### 자동 검증 스크립트

```powershell
# scripts/validate_stage1.ps1

param(
    [string]$LogPath = "outputs/monitor_*.json",
    [double]$MaxErrorRate = 0.01,        # 1%
    [int]$MaxP95ResponseTime = 15000,    # 15s
    [double]$MinSuccessRate = 0.95,      # 95%
    [double]$MinConfidence = 0.75        # 0.75
)

Write-Host "=== Stage 1 성공 기준 검증 ===" -ForegroundColor Cyan

# 최신 모니터링 데이터 로드
$latestLog = Get-ChildItem $LogPath | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1

if (-not $latestLog) {
    Write-Error "모니터링 데이터를 찾을 수 없습니다."
    exit 1
}

$data = Get-Content $latestLog.FullName | ConvertFrom-Json

# 검증 1: Error Rate
$errorRate = $data.canary.error_rate
if ($errorRate -gt $MaxErrorRate) {
    Write-Error "❌ Error Rate 초과: $errorRate > $MaxErrorRate"
    exit 1
} else {
    Write-Host "✅ Error Rate: $errorRate <= $MaxErrorRate" -ForegroundColor Green
}

# 검증 2: P95 Response Time
$p95ResponseTime = $data.canary.p95_response_time_ms
if ($p95ResponseTime -gt $MaxP95ResponseTime) {
    Write-Error "❌ P95 Response Time 초과: $p95ResponseTime ms > $MaxP95ResponseTime ms"
    exit 1
} else {
    Write-Host "✅ P95 Response Time: $p95ResponseTime ms <= $MaxP95ResponseTime ms" -ForegroundColor Green
}

# 검증 3: Success Rate
$successRate = $data.canary.success_rate
if ($successRate -lt $MinSuccessRate) {
    Write-Error "❌ Success Rate 미달: $successRate < $MinSuccessRate"
    exit 1
} else {
    Write-Host "✅ Success Rate: $successRate >= $MinSuccessRate" -ForegroundColor Green
}

# 검증 4: Confidence Score
$confidence = $data.canary.avg_confidence_score
if ($confidence -lt $MinConfidence) {
    Write-Error "❌ Confidence Score 미달: $confidence < $MinConfidence"
    exit 1
} else {
    Write-Host "✅ Confidence Score: $confidence >= $MinConfidence" -ForegroundColor Green
}

Write-Host "`n🎉 Stage 1 성공 기준 모두 충족!" -ForegroundColor Green
Write-Host "Stage 2 (10% 트래픽) 배포 승인됨." -ForegroundColor Cyan
```

---

### 배포 절차

#### Step 1: Stage 1 검증 (5분)

```powershell
# 성공 기준 자동 검증
.\scripts\validate_stage1.ps1

# 예상 출력:
# ✅ Error Rate: 0.003 <= 0.01
# ✅ P95 Response Time: 580 ms <= 15000 ms
# ✅ Success Rate: 0.987 >= 0.95
# ✅ Confidence Score: 0.85 >= 0.75
# 🎉 Stage 1 성공 기준 모두 충족!
```

#### Step 2: Canary 설정 업데이트 (2분)

```python
# app/config/canary_config.py

CANARY_CONFIG = {
    "enabled": True,
    "current_stage": 2,  # Stage 1 → Stage 2
    "traffic_percent": 10,  # 5% → 10%
    "stages": [
        {"name": "Stage 1", "traffic_percent": 5, "duration_hours": 24},
        {"name": "Stage 2", "traffic_percent": 10, "duration_hours": 24},  # 현재
        # ... (나머지 동일)
    ]
}
```

#### Step 3: Git Commit (1분)

```bash
git add app/config/canary_config.py
git commit -m "feat: Stage 2 Canary 배포 (10% 트래픽)"
git push origin main
```

#### Step 4: GCP 배포 (DryRun) (5초)

```powershell
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId naeda-genesis `
    -CanaryPercentage 10 `
    -DryRun
```

#### Step 5: 실제 배포 (30-60초)

```powershell
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId naeda-genesis `
    -CanaryPercentage 10
```

#### Step 6: 배포 검증 (2분)

```powershell
# Health Check
curl https://ion-api-canary-x4qvsargwa-uc.a.run.app/health

# 트래픽 비율 확인 (100 requests)
.\scripts\compare_canary_vs_legacy.ps1 `
    -RequestsPerSide 100 `
    -DelayMsBetweenRequests 50 `
    -OutJson compare_stage2.json

# 예상 결과:
# Legacy: ~90 requests
# Canary: ~10 requests
```

#### Step 7: 24시간 모니터링 시작 (1분)

```powershell
# 기존 모니터링 종료
Stop-Job -Name CanaryMonitoring

# Stage 2 모니터링 시작
Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    .\scripts\start_monitor_loop.ps1 `
        -KillExisting `
        -IntervalSeconds 1800 `
        -DurationMinutes 1440
} -ArgumentList (Get-Location).Path -Name "CanaryMonitoring_Stage2"
```

---

### 체크리스트

#### 배포 전
- [ ] Stage 1 성공 기준 검증 완료
- [ ] Canary 설정 파일 업데이트
- [ ] Git commit 및 push
- [ ] DryRun 성공 확인

#### 배포 중
- [ ] 실제 배포 실행
- [ ] Health Check 통과
- [ ] 트래픽 분산 확인 (90/10)

#### 배포 후
- [ ] 24시간 모니터링 시작
- [ ] 첫 1시간 집중 관찰
- [ ] 알림 설정 확인

---

### 롤백 계획

#### 자동 롤백 조건

```python
ROLLBACK_THRESHOLD = {
    "error_rate": 0.02,         # 2% (Stage 1의 2배)
    "p95_response_time": 20000, # 20s
    "success_rate": 0.90,       # 90%
    "confidence_score": 0.70    # 0.70
}
```

#### 긴급 롤백 명령어

```powershell
# Stage 2 → Stage 1 (10% → 5%)
.\scripts\rollback_phase4_canary.ps1 `
    -ProjectId naeda-genesis `
    -AutoApprove

# 또는 완전 롤백 (100% Legacy)
.\scripts\emergency_rollback.ps1 `
    -Force `
    -SkipConfirmation
```

---

### 성공 기준 (Stage 3 진입 조건)

```yaml
Stage 2 성공 기준:
  error_rate: < 1.5%
  p95_response_time: < 18s
  success_rate: > 93%
  confidence_score: > 0.73
  monitoring_duration: 24시간
```

---

## 🚀 Stage 3: 25% 트래픽

### 기본 정보
- **트래픽 비율**: Legacy 75% / Canary 25%
- **모니터링 기간**: 48시간
- **예정일**: 2025-10-24
- **전제 조건**: Stage 2 성공 기준 충족

---

### Stage 2 성공 기준 검증

#### 자동 검증 스크립트

```powershell
# scripts/validate_stage2.ps1

param(
    [string]$LogPath = "outputs/monitor_*.json",
    [double]$MaxErrorRate = 0.015,       # 1.5%
    [int]$MaxP95ResponseTime = 18000,    # 18s
    [double]$MinSuccessRate = 0.93,      # 93%
    [double]$MinConfidence = 0.73        # 0.73
)

# (검증 로직 동일, threshold만 다름)
```

---

### 배포 절차

#### Step 1-7: Stage 2와 동일

```powershell
# Step 1: Stage 2 검증
.\scripts\validate_stage2.ps1

# Step 2: Canary 설정 업데이트 (traffic_percent = 25)
# Step 3: Git commit
# Step 4: DryRun
# Step 5: 실제 배포 (CanaryPercentage 25)
# Step 6: 배포 검증 (75/25 트래픽 확인)
# Step 7: 48시간 모니터링 시작
```

---

### 추가 검증: Load Testing

#### Locust 부하 테스트 (1시간)

```powershell
# scripts/run_all_load_tests.ps1

.\scripts\run_all_load_tests.ps1 `
    -ScenarioProfile light `
    -OverrideRunTime 60m

# 시나리오:
# - Users: 50 concurrent
# - Spawn rate: 5 users/sec
# - Duration: 60 minutes
# - Endpoints: /chat, /api/v2/recommend/personalized
```

#### 예상 결과 분석

```powershell
# 결과 요약
.\scripts\summarize_locust_results.ps1

# 예상 출력:
# Legacy (75%):
#   - RPS: ~37.5 (50 users × 75%)
#   - P95: 1,200ms
#   - Error Rate: 0.8%
#
# Canary (25%):
#   - RPS: ~12.5 (50 users × 25%)
#   - P95: 600ms
#   - Error Rate: 0.2%
```

---

### 성공 기준 (Stage 4 진입 조건)

```yaml
Stage 3 성공 기준:
  error_rate: < 2%
  p95_response_time: < 20s
  success_rate: > 91%
  confidence_score: > 0.71
  monitoring_duration: 48시간
  load_test_passed: true
```

---

## 🚀 Stage 4: 50% 트래픽

### 기본 정보
- **트래픽 비율**: Legacy 50% / Canary 50%
- **모니터링 기간**: 72시간
- **예정일**: 2025-10-25
- **전제 조건**: Stage 3 성공 기준 충족 + Load Test 통과

---

### Stage 3 성공 기준 검증

#### 자동 검증 스크립트

```powershell
# scripts/validate_stage3.ps1

param(
    [string]$LogPath = "outputs/monitor_*.json",
    [double]$MaxErrorRate = 0.02,        # 2%
    [int]$MaxP95ResponseTime = 20000,    # 20s
    [double]$MinSuccessRate = 0.91,      # 91%
    [double]$MinConfidence = 0.71,       # 0.71
    [bool]$RequireLoadTestPass = $true
)

# 검증 로직 + Load Test 결과 확인
if ($RequireLoadTestPass) {
    $loadTestResult = Get-Content "outputs/load_test_summary.json" | ConvertFrom-Json
    if ($loadTestResult.status -ne "PASSED") {
        Write-Error "❌ Load Test 실패"
        exit 1
    }
}
```

---

### 배포 절차

#### Step 1-7: 이전 Stage와 동일

```powershell
# Step 1: Stage 3 검증 (Load Test 포함)
.\scripts\validate_stage3.ps1 -RequireLoadTestPass $true

# Step 2: Canary 설정 업데이트 (traffic_percent = 50)
# Step 3: Git commit
# Step 4: DryRun
# Step 5: 실제 배포 (CanaryPercentage 50)
# Step 6: 배포 검증 (50/50 트래픽 확인)
# Step 7: 72시간 모니터링 시작
```

---

### 추가 검증: A/B Test 결과 분석

#### BigQuery 쿼리 (30일간 데이터)

```sql
-- A/B 테스트 최종 분석
-- (2025-10-22 ~ 2025-11-22)

WITH ab_test_results AS (
  SELECT
    group AS ab_group,
    COUNT(*) AS total_requests,
    AVG(response_time_ms) AS avg_response_time,
    APPROX_QUANTILES(response_time_ms, 100)[OFFSET(95)] AS p95_response_time,
    AVG(confidence_score) AS avg_confidence,
    COUNTIF(success = true) / COUNT(*) AS success_rate
  FROM `naeda-genesis.ab_test.results`
  WHERE timestamp BETWEEN '2025-10-22' AND '2025-11-22'
  GROUP BY ab_group
)

SELECT
  ab_group,
  total_requests,
  ROUND(avg_response_time, 2) AS avg_response_time_ms,
  p95_response_time AS p95_response_time_ms,
  ROUND(avg_confidence, 3) AS avg_confidence_score,
  ROUND(success_rate, 3) AS success_rate
FROM ab_test_results
ORDER BY ab_group;
```

#### 예상 결과

```
Group A (Legacy):
  total_requests: 150,000
  avg_response_time_ms: 450
  p95_response_time_ms: 1,200
  avg_confidence_score: 0.72
  success_rate: 0.988

Group B (Vertex AI / Canary):
  total_requests: 150,000
  avg_response_time_ms: 220
  p95_response_time_ms: 600
  avg_confidence_score: 0.85
  success_rate: 0.997

Improvement:
  - Response Time: 51% 개선
  - P95: 50% 개선
  - Confidence: 18% 개선
  - Success Rate: 0.9% 개선
```

---

### 의사결정: Stage 5 진입 여부

#### 자동 의사결정 스크립트

```powershell
# scripts/decide_stage5.ps1

param(
    [string]$ABTestResultsPath = "outputs/ab_test_analysis.json"
)

$data = Get-Content $ABTestResultsPath | ConvertFrom-Json

# Canary가 Legacy보다 명확히 우수한지 확인
$improvementThreshold = 0.10  # 10% 개선 필요

$responseTimeImprovement = 
    ($data.legacy.avg_response_time - $data.canary.avg_response_time) / 
    $data.legacy.avg_response_time

if ($responseTimeImprovement -gt $improvementThreshold) {
    Write-Host "✅ Canary 성능 우수: Response Time $($responseTimeImprovement * 100)% 개선" -ForegroundColor Green
    Write-Host "🎯 Stage 5 (100% 트래픽) 진입 승인" -ForegroundColor Cyan
    exit 0
} else {
    Write-Warning "⚠️ Canary 성능 개선 미미: $($responseTimeImprovement * 100)%"
    Write-Warning "Stage 5 진입 보류, 추가 분석 필요"
    exit 1
}
```

---

### 성공 기준 (Stage 5 진입 조건)

```yaml
Stage 4 성공 기준:
  error_rate: < 2.5%
  p95_response_time: < 22s
  success_rate: > 89%
  confidence_score: > 0.69
  monitoring_duration: 72시간
  ab_test_canary_better: true  # Canary가 Legacy보다 10% 이상 개선
```

---

## 🚀 Stage 5: 100% 트래픽 (프로덕션 전환)

### 기본 정보
- **트래픽 비율**: Legacy 0% / Canary 100%
- **모니터링 기간**: 계속 (무기한)
- **예정일**: 2025-10-26 ~ 2025-10-28
- **전제 조건**: Stage 4 성공 기준 충족 + A/B 테스트 승인

---

### Stage 4 성공 기준 검증

#### 자동 검증 스크립트

```powershell
# scripts/validate_stage4.ps1

param(
    [string]$LogPath = "outputs/monitor_*.json",
    [double]$MaxErrorRate = 0.025,       # 2.5%
    [int]$MaxP95ResponseTime = 22000,    # 22s
    [double]$MinSuccessRate = 0.89,      # 89%
    [double]$MinConfidence = 0.69,       # 0.69
    [bool]$RequireABTestApproval = $true
)

# 검증 로직 + A/B Test 의사결정 확인
if ($RequireABTestApproval) {
    $decision = .\scripts\decide_stage5.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ A/B Test 승인 실패"
        exit 1
    }
}
```

---

### 배포 절차

#### Step 1: Stage 4 검증 (5분)

```powershell
.\scripts\validate_stage4.ps1 -RequireABTestApproval $true
```

#### Step 2: 최종 배포 승인 (수동)

```
==================================================
🚨 FINAL DEPLOYMENT APPROVAL REQUIRED 🚨
==================================================

Stage 5: 100% 트래픽 전환
- Canary가 프로덕션 메인 서비스가 됩니다.
- Legacy 서비스는 백업 역할로 전환됩니다.

승인하시겠습니까? (Y/N):
```

#### Step 3: Canary 설정 업데이트 (2분)

```python
# app/config/canary_config.py

CANARY_CONFIG = {
    "enabled": False,  # True → False (Canary 모드 종료)
    "current_stage": 5,
    "traffic_percent": 100,
    "production_service": "ion-api-canary"  # 새로 추가
}
```

#### Step 4: Git Commit (1분)

```bash
git add app/config/canary_config.py
git commit -m "feat: Stage 5 프로덕션 전환 (100% Canary)"
git push origin main
```

#### Step 5: GCP 배포 (100%) (30-60초)

```powershell
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId naeda-genesis `
    -CanaryPercentage 100
```

#### Step 6: Legacy 서비스 백업 모드 (5분)

```bash
# Legacy 서비스 스케일 다운 (비용 절감)
gcloud run services update ion-api \
    --region us-central1 \
    --min-instances 0 \
    --max-instances 1 \
    --project naeda-genesis

# Canary 서비스 스케일 업 (프로덕션 대응)
gcloud run services update ion-api-canary \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 10 \
    --project naeda-genesis
```

#### Step 7: 서비스 이름 변경 (선택 사항)

```bash
# Canary → Main (서비스 재배포)
# 또는 DNS 설정으로 처리
```

#### Step 8: 모니터링 계속 (무기한)

```powershell
# 프로덕션 모니터링 (영구 실행)
Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    .\scripts\start_monitor_loop.ps1 `
        -KillExisting `
        -IntervalSeconds 3600 `
        -DurationMinutes 0  # 무기한
} -ArgumentList (Get-Location).Path -Name "ProductionMonitoring"
```

---

### 체크리스트

#### 배포 전
- [ ] Stage 4 성공 기준 검증 완료
- [ ] A/B Test 최종 승인
- [ ] 최종 배포 승인 (수동)
- [ ] 백업 계획 확인

#### 배포 중
- [ ] 100% 트래픽 배포
- [ ] Legacy 서비스 스케일 다운
- [ ] Canary 서비스 스케일 업
- [ ] Health Check 통과

#### 배포 후
- [ ] 프로덕션 모니터링 시작
- [ ] 첫 24시간 집중 관찰
- [ ] 알림 정책 업데이트
- [ ] Legacy 서비스 종료 일정 수립

---

### Legacy 서비스 종료 계획

#### 30일 유지 기간

```
Day 1-7 (10/26-11/01):
  - Legacy 백업 모드 (min=0, max=1)
  - 긴급 롤백 대비

Day 8-30 (11/02-11/24):
  - 롤백 가능성 낮음
  - Legacy 서비스 비활성화 준비

Day 31+ (11/25~):
  - Legacy 서비스 완전 종료
  - 리소스 정리
```

#### 완전 종료 스크립트

```bash
# 30일 후 실행
gcloud run services delete ion-api \
    --region us-central1 \
    --project naeda-genesis \
    --quiet

# Container Registry 정리
gcloud container images delete gcr.io/naeda-genesis/ion-api:latest \
    --quiet
```

---

### 롤백 계획 (마지막 수단)

#### Stage 5 → Stage 4 (100% → 50%)

```powershell
.\scripts\rollback_phase4_canary.ps1 `
    -ProjectId naeda-genesis `
    -RollbackToStage 4 `
    -AutoApprove
```

#### 완전 롤백 (100% Legacy)

```powershell
.\scripts\emergency_rollback.ps1 `
    -Force `
    -SkipConfirmation
```

**주의**: Stage 5 롤백은 중대한 결정입니다. 신중히 판단하세요.

---

## 📊 모니터링 대시보드

### Cloud Monitoring 메트릭

#### 주요 메트릭 (Stage별 추적)

```yaml
Latency:
  - run.googleapis.com/request_latencies (P50, P95, P99)
  
Traffic:
  - run.googleapis.com/request_count (Legacy vs Canary)
  
Errors:
  - run.googleapis.com/container/billable_instance_time
  - Custom: error_rate (errors / requests)
  
Saturation:
  - run.googleapis.com/container/cpu/utilization
  - run.googleapis.com/container/memory/utilization
```

#### 알림 정책

```yaml
Critical Alerts (즉시 대응):
  - error_rate > 5%
  - p95_response_time > 30s
  - success_rate < 80%

Warning Alerts (모니터링):
  - error_rate > 2%
  - p95_response_time > 20s
  - success_rate < 90%
```

---

### Grafana 대시보드 (권장)

#### 패널 구성

```
Row 1: Overview
  - Request Count (Legacy vs Canary)
  - Error Rate (Legacy vs Canary)
  - Success Rate (Legacy vs Canary)

Row 2: Latency
  - P50 Response Time (time series)
  - P95 Response Time (time series)
  - P99 Response Time (time series)

Row 3: Confidence
  - Avg Confidence Score (gauge)
  - Confidence Distribution (histogram)

Row 4: Resources
  - CPU Utilization (Legacy vs Canary)
  - Memory Utilization (Legacy vs Canary)
```

---

## 🔄 롤백 결정 트리

```
모니터링 중 이상 감지
    │
    ▼
Error Rate > 5%?
    │
    ├─ Yes → 즉시 롤백 (emergency_rollback.ps1)
    │
    └─ No
        │
        ▼
P95 Response Time > 30s?
    │
    ├─ Yes → 즉시 롤백
    │
    └─ No
        │
        ▼
Success Rate < 80%?
    │
    ├─ Yes → 즉시 롤백
    │
    └─ No → 계속 모니터링
        │
        ▼
Warning Alert 발생? (error_rate > 2%)
    │
    ├─ Yes → 집중 관찰 (1시간)
    │    │
    │    ▼
    │    개선 없음?
    │    │
    │    ├─ Yes → 이전 Stage로 롤백
    │    └─ No → 계속 모니터링
    │
    └─ No → 정상 운영
```

---

## 📝 최종 체크리스트

### Week 3 전체 (7일)

```
Day 1 (Stage 1, 5%):
  ✅ 배포 완료
  ✅ 24시간 모니터링 시작

Day 2 (Stage 2, 10%):
  ⏳ Stage 1 검증
  ⏳ 배포 실행
  ⏳ 24시간 모니터링

Day 3 (Stage 3, 25%):
  ⏳ Stage 2 검증
  ⏳ Load Testing
  ⏳ 배포 실행
  ⏳ 48시간 모니터링

Day 4-5 (Stage 4, 50%):
  ⏳ Stage 3 검증
  ⏳ A/B Test 분석
  ⏳ 배포 실행
  ⏳ 72시간 모니터링

Day 6-7 (Stage 5, 100%):
  ⏳ Stage 4 검증
  ⏳ 최종 승인
  ⏳ 프로덕션 전환
  ⏳ Legacy 백업 모드
```

---

## ✅ 서명

**작성자**: 깃코 (AI Agent)  
**작성일**: 2025-10-22  
**상태**: ✅ **Stage 2-5 상세 계획 완료**  
**현재**: Stage 1 모니터링 진행 중  
**다음**: Stage 1 완료 후 Stage 2 배포

---

**문서 종료**  
5-Stage Canary Deployment → 실행 준비 완료! 🚀
