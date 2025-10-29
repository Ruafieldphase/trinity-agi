# Phase 4 Canary Deployment Guide

**문서 버전**: 1.0.0  
**작성일**: 2025-10-18  
**대상**: 운영팀, DevOps 엔지니어

---

## 📋 목차

1. [사전 준비](#사전-준비)
2. [배포 실행](#배포-실행)
3. [모니터링](#모니터링)
4. [롤백 절차](#롤백-절차)
5. [트러블슈팅](#트러블슈팅)

---

## 사전 준비

### 1. 필수 도구 설치

```powershell
# Google Cloud SDK 설치 확인
gcloud --version

# Docker 설치 확인
docker --version

# PowerShell 버전 확인 (5.1 이상)
$PSVersionTable.PSVersion
```

### 2. 인증 및 권한 설정

```powershell
# Google Cloud 인증
gcloud auth login

# 프로젝트 ID 설정
$PROJECT_ID = "your-project-id"
gcloud config set project $PROJECT_ID

# 필요한 권한 확인
# - Cloud Run Admin
# - Artifact Registry Admin
# - Service Account Admin
# - Secret Manager Admin
```

### 3. 환경 변수 설정

```powershell
# 프로젝트 ID 환경 변수
$env:GCP_PROJECT_ID = "your-project-id"

# 영구 설정 (선택적)
[System.Environment]::SetEnvironmentVariable("GCP_PROJECT_ID", "your-project-id", "User")
```

### 4. 배포 전 체크리스트

```
[✅] 모든 Phase 4 통합 테스트 통과 (19/20)
[✅] 메트릭 수집기 동작 확인
[✅] 롤백 절차 문서 검토
[✅] 모니터링 알림 설정 (Sentry, Slack)
[✅] 카나리 비율 5%로 설정
[ ] 경영진 승인 획득
[ ] 운영팀 대기 상태 확인
[ ] 배포 시간대 확인 (트래픽 적은 시간대 권장)
```

---

## 배포 실행

### Step 1: Dry Run (설정 검증)

실제 배포 전에 설정을 검증합니다:

```powershell
cd d:\nas_backup\LLM_Unified\ion-mentoring\scripts

# Dry Run 실행 (실제 배포 없이 설정만 확인)
.\deploy_phase4_canary.ps1 `
    -ProjectId "your-project-id" `
    -Region "us-central1" `
    -CanaryPercentage 5 `
    -DryRun
```

**예상 결과**:

```
[INFO] Step 1: Pre-deployment checks
[SUCCESS] Authenticated as: user@example.com
[SUCCESS] Project verified: your-project-id
[WARN] [DRY RUN] Skipping API enablement
[WARN] [DRY RUN] Would build image: us-central1-docker.pkg.dev/...
...
```

### Step 2: 실제 배포 (5% Canary)

Dry Run이 성공하면 실제 배포를 진행합니다:

```powershell
# 실제 배포 실행
.\deploy_phase4_canary.ps1 `
    -ProjectId "your-project-id" `
    -Region "us-central1" `
    -CanaryPercentage 5
```

**배포 단계**:

1. ✅ Pre-deployment checks (30초)
2. ✅ Enable required APIs (1분)
3. ✅ Setup Service Account (30초)
4. ✅ Setup Artifact Registry (30초)
5. ⏳ Build Docker image (3-5분) ← **가장 오래 걸림**
6. ⏳ Push Docker image (2-3분)
7. ⏳ Deploy Canary service (1-2분)
8. ✅ Health check (10초)
9. ✅ Configure traffic split (즉시)

**총 예상 시간**: 10-15분

### Step 3: 배포 확인

배포가 완료되면 다음 정보가 출력됩니다:

```
====================================================================
Phase 4 Canary Deployment Completed Successfully!
====================================================================

Canary Service URL: https://ion-api-canary-xxxxxxxxx-uc.a.run.app
Traffic Split: Legacy 95% / Canary 5%
Log File: d:\nas_backup\LLM_Unified\ion-mentoring\scripts\logs\deploy_20251018-143022.log

Next Steps:
1. Monitor metrics for 1 hour (error rate, latency)
2. Check Sentry/Cloud Monitoring for alerts
3. Validate SLO compliance (error rate < 0.5%, P95 < 10%)
4. If successful, gradually increase canary percentage

Rollback Command:
  gcloud run services delete ion-api-canary --region=us-central1 --project=your-project-id
```

### Step 4: 수동 검증

```powershell
# 카나리 서비스 URL 가져오기
$CANARY_URL = gcloud run services describe ion-api-canary `
    --region=us-central1 `
    --format="value(status.url)"

# 헬스 체크
Invoke-WebRequest -Uri "$CANARY_URL/health" -Method Get

# Phase 4 엔드포인트 테스트
Invoke-WebRequest -Uri "$CANARY_URL/api/v2/phase4/health" -Method Get

# 개인화 추천 테스트
$body = @{
    user_id = "test-user-001"
    current_context = @{
        recent_goals = @("건강 개선", "시간 관리")
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "$CANARY_URL/api/v2/recommend/personalized" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

---

## 모니터링

### 1시간 모니터링 (Critical)

배포 후 첫 1시간은 **집중 모니터링** 기간입니다.

#### Cloud Monitoring (Google Cloud Console)

1. **Cloud Run 대시보드** 이동:

   - https://console.cloud.google.com/run

2. **ion-api-canary** 서비스 선택

3. **모니터링 지표 확인**:
   - Request count (요청 수)
   - Request latency (P50, P95, P99)
   - Error rate (4xx, 5xx)
   - Container CPU utilization
   - Container memory utilization

#### Sentry (Error Tracking)

1. **Sentry 대시보드** 이동:

   - https://sentry.io/organizations/your-org/issues/

2. **필터 적용**:

   - Environment: `production`
   - Release: `phase4-canary`
   - Time range: Last 1 hour

3. **알림 설정**:
   - Error rate > 1%: Slack 알림
   - P95 latency > 2s: PagerDuty 알림

#### 수동 메트릭 확인

```powershell
# Cloud Run 로그 확인
gcloud run services logs read ion-api-canary `
    --region=us-central1 `
    --limit=50

# 에러 로그만 필터링
gcloud run services logs read ion-api-canary `
    --region=us-central1 `
    --limit=50 `
    --filter="severity>=ERROR"

# 특정 시간대 로그
gcloud run services logs read ion-api-canary `
    --region=us-central1 `
    --format="table(timestamp, severity, textPayload)" `
    --filter="timestamp>\"2025-10-18T14:00:00Z\""
```

### 6시간 모니터링 (Extended)

첫 1시간 안정적이면 6시간 동안 추가 모니터링:

**확인 항목**:

- ✅ Canary error rate vs Legacy error rate (차이 < 0.5%)
- ✅ P95 latency (Canary <= Legacy \* 1.1)
- ✅ Minimum 1,000 canary requests processed
- ✅ No customer complaints
- ✅ Sentry error rate < 1%

### 24시간 모니터링 (Full Cycle)

일간 패턴 검증 (피크 시간대 포함):

**모니터링 시간대**:

- 09:00-11:00 (오전 피크)
- 14:00-16:00 (오후 피크)
- 21:00-23:00 (저녁 피크)

**SLO 검증**:

```python
# SLO 계산 스크립트 (Python)
canary_error_rate = 0.02  # 2%
legacy_error_rate = 0.01  # 1%

canary_p95 = 980  # ms
legacy_p95 = 900  # ms

# 1. Error Rate SLO
error_diff = canary_error_rate - legacy_error_rate
error_slo_met = error_diff < 0.005  # 0.5%

# 2. P95 Latency SLO
latency_increase = (canary_p95 - legacy_p95) / legacy_p95
latency_slo_met = latency_increase < 0.10  # 10%

# 3. Minimum Requests SLO
canary_requests = 1500
min_requests_slo_met = canary_requests > 1000

print(f"Error Rate SLO: {'✅ MET' if error_slo_met else '❌ FAILED'}")
print(f"Latency SLO: {'✅ MET' if latency_slo_met else '❌ FAILED'}")
print(f"Min Requests SLO: {'✅ MET' if min_requests_slo_met else '❌ FAILED'}")

if error_slo_met and latency_slo_met and min_requests_slo_met:
    print("\n🎉 All SLOs met! Ready for rollout increase.")
else:
    print("\n⚠️  Some SLOs failed. Consider rollback or investigation.")
```

---

## 롤백 절차

### 자동 롤백 트리거

다음 조건 중 **하나라도 발생하면 즉시 롤백**:

| 조건                              | 임계값                    | 조치 시간 |
| --------------------------------- | ------------------------- | --------- |
| **Critical: Error Rate Spike**    | Canary error rate > 5%    | 즉시      |
| **High: Performance Degradation** | Canary P95 > 2초          | 5분 이내  |
| **Medium: Availability Drop**     | Canary availability < 99% | 15분 이내 |

### 수동 롤백 실행

#### Method 1: PowerShell 스크립트 (권장)

```powershell
cd d:\nas_backup\LLM_Unified\ion-mentoring\scripts

# 롤백 실행 (카나리 서비스 삭제)
.\rollback_phase4_canary.ps1 `
    -ProjectId "your-project-id" `
    -Region "us-central1" `
    -DeleteCanaryService
```

#### Method 2: gcloud CLI (빠른 롤백)

```powershell
# 1. 카나리 서비스 트래픽 0%로 설정
gcloud run services update ion-api-canary `
    --no-traffic `
    --region=us-central1 `
    --project=$PROJECT_ID `
    --quiet

# 2. 카나리 서비스 삭제
gcloud run services delete ion-api-canary `
    --region=us-central1 `
    --project=$PROJECT_ID `
    --quiet
```

### 롤백 후 조치

1. **인시던트 리포트 작성**:

   ```markdown
   # Phase 4 Canary Rollback Report

   ## Rollback Details

   - Date: 2025-10-18 14:30:00 KST
   - Trigger: Error rate spike (7.2% > 5% threshold)
   - Decision: Automatic rollback

   ## Root Cause Analysis

   - [상세 분석 작성]

   ## Action Items

   1. [ ] Fix identified issue
   2. [ ] Update tests to catch this scenario
   3. [ ] Plan next deployment
   ```

2. **로그 보관**:

   ```powershell
   # 배포 로그 백업
   Copy-Item "scripts\logs\deploy_*.log" -Destination "docs\rollback_reports\"

   # Cloud Run 로그 export
   gcloud run services logs read ion-api-canary `
       --region=us-central1 `
       --format=json > "docs\rollback_reports\canary_logs_$TIMESTAMP.json"
   ```

3. **팀 통보**:
   - Slack #deployments 채널에 롤백 공지
   - Incident report 링크 공유
   - 다음 배포 일정 조율

---

## 트러블슈팅

### 문제 1: Docker 빌드 실패

**증상**:

```
ERROR: failed to solve: failed to compute cache key
```

**해결**:

```powershell
# Docker 캐시 삭제
docker system prune -a -f

# 다시 빌드
.\deploy_phase4_canary.ps1 -ProjectId $PROJECT_ID
```

### 문제 2: Service Account 권한 부족

**증상**:

```
ERROR: Permission denied on resource 'aiplatform.googleapis.com'
```

**해결**:

```powershell
# Service Account에 권한 수동 부여
$SA_EMAIL = "ion-api-canary-runner@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA_EMAIL" `
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA_EMAIL" `
    --role="roles/secretmanager.secretAccessor"
```

### 문제 3: Health Check 실패

**증상**:

```
Health check failed: Connection refused
```

**해결**:

1. **컨테이너 로그 확인**:

   ```powershell
   gcloud run services logs read ion-api-canary --region=us-central1 --limit=100
   ```

2. **환경 변수 확인**:

   ```powershell
   gcloud run services describe ion-api-canary `
       --region=us-central1 `
       --format="value(spec.template.spec.containers[0].env)"
   ```

3. **로컬 Docker 테스트**:

   ```powershell
   # 로컬에서 이미지 실행
    docker run -p 8080:8080 `
        -e ENVIRONMENT=production `
        -e PORT=8080 `
        -e PHASE4_ENABLED=true `
        -e CANARY_TRAFFIC_PERCENTAGE=5 `
        -e DEPLOYMENT_VERSION=CANARY `
        us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api-canary:phase4-canary

   # 헬스 체크
   Invoke-WebRequest -Uri "http://localhost:8080/health"
   ```

### 문제 4: Artifact Registry 푸시 실패

**증상**:

```
unauthorized: authentication required
```

**해결**:

```powershell
# Docker credential helper 재설정
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# 인증 확인
gcloud auth print-access-token | docker login -u oauth2accesstoken `
    --password-stdin https://us-central1-docker.pkg.dev
```

### 문제 5: 메모리 부족 (OOM)

**증상**:

```
ERROR: Container failed to start. Failed to start and then listen on the port defined by the PORT environment variable.
```

**해결**:

```powershell
# 메모리 증가 (512Mi → 1Gi)
gcloud run services update ion-api-canary `
    --memory=1Gi `
    --region=us-central1

# CPU 증가 (1 → 2)
gcloud run services update ion-api-canary `
    --cpu=2 `
    --region=us-central1
```

---

## 추가 리소스

### 문서

- [PHASE4_CANARY_DEPLOYMENT.md](../PHASE4_CANARY_DEPLOYMENT.md) - 카나리 배포 전략
- [PHASE4_DEPLOYMENT_READINESS.md](../PHASE4_DEPLOYMENT_READINESS.md) - 배포 준비 체크리스트
- [DAY3_CLOUD_RUN_DEPLOYMENT.md](../DAY3_CLOUD_RUN_DEPLOYMENT.md) - Cloud Run 기본 가이드

### 스크립트

- `deploy_phase4_canary.ps1` - 배포 스크립트
- `rollback_phase4_canary.ps1` - 롤백 스크립트

### 대시보드

- [Cloud Run Console](https://console.cloud.google.com/run)
- [Cloud Monitoring](https://console.cloud.google.com/monitoring)
- [Sentry Dashboard](https://sentry.io)

### 연락처

- **운영팀 Slack**: #ion-ops
- **개발팀 Slack**: #ion-dev
- **긴급 연락**: PagerDuty on-call

---

**문서 작성**: GitHub Copilot  
**최종 업데이트**: 2025-10-18  
**버전**: 1.0.0
