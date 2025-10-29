# Week 3 Day 1 시작 체크리스트 🚀
## Canary 배포 시작 준비

**날짜**: 2025-10-22  
**목표**: Stage 1 Canary 배포 (5% 트래픽)  
**예상 소요 시간**: 3-4시간

---

## 📋 사전 준비 체크리스트

### 1. 시스템 상태 확인 ✅

#### Ion API 서비스 상태

```powershell
# Ion API health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET

# 기대 결과:
{
  "status": "healthy",
  "lumen_gateway": "enabled",
  "timestamp": "2025-10-22T..."
}
```

**현재 상태**: ⏸️ 확인 필요

---

#### Lumen Gateway 상태

```powershell
# Lumen Gateway health check
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET

# 기대 결과:
{
  "status": "healthy",
  "gemini_api": "connected",
  "confidence_system": "active"
}
```

**현재 상태**: ⏸️ 확인 필요

---

### 2. 성능 기준선 확립 ✅

#### 빠른 스모크 테스트 (5 iterations)

```powershell
cd d:\nas_backup\LLM_Unified\ion-mentoring
d:\nas_backup\LLM_Unified\.venv\Scripts\python.exe test_performance_benchmark.py --iterations 5
```

**목적**: Canary 배포 전 현재 성능 스냅샷 저장

**예상 결과**:
- 응답 시간: 10-11초 (±6ms)
- 신뢰도: 82-90%
- 성공률: 100%

**현재 상태**: ⏸️ 실행 대기

---

### 3. GCP 프로젝트 연결 확인 ✅

#### Cloud Run 서비스 목록 조회

```powershell
gcloud run services list --project naeda-genesis --region us-central1
```

**기대 결과**:

```
SERVICE       REGION       URL
ion-api       us-central1  https://ion-api-64076350717.us-central1.run.app
ion-api-canary us-central1 https://ion-api-canary-64076350717.us-central1.run.app
```

**현재 상태**: ⏸️ 확인 필요

---

#### 현재 트래픽 분산 확인

```powershell
gcloud run services describe ion-api --project naeda-genesis --region us-central1 --format="value(status.traffic)"
```

**기대 결과**:

```
ion-api: 100%
ion-api-canary: 0%
```

**현재 상태**: ⏸️ 확인 필요

---

## 🎯 Canary 배포 DryRun

### Step 1: DryRun 스크립트 실행

```powershell
cd d:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\deploy_phase4_canary.ps1 -ProjectId naeda-genesis -DryRun
```

**검증 항목**:
- [ ] 스크립트 문법 오류 없음
- [ ] GCP 프로젝트 접근 가능
- [ ] Cloud Run 서비스 조회 성공
- [ ] 트래픽 분산 시뮬레이션 정상

**예상 출력**:

```
[DRY-RUN] Canary Deployment Simulation
======================================
Project: naeda-genesis
Region: us-central1
Current Traffic: ion-api (100%), ion-api-canary (0%)
Planned Traffic: ion-api (95%), ion-api-canary (5%)

[DRY-RUN] Would execute:
gcloud run services update-traffic ion-api \
  --project naeda-genesis \
  --region us-central1 \
  --to-revisions ion-api=95,ion-api-canary=5

[DRY-RUN] Deployment would succeed!
```

**현재 상태**: ⏸️ 실행 대기

---

### Step 2: DryRun 결과 분석

**성공 조건**:
1. ✅ GCP 프로젝트 연결 성공
2. ✅ Cloud Run 서비스 조회 성공
3. ✅ 트래픽 라우팅 시뮬레이션 정상
4. ✅ 예상 트래픽 분산: 95% (Legacy) + 5% (Canary)

**실패 시 대응**:
- GCP 인증 실패 → `gcloud auth login` 재실행
- 서비스 없음 → Cloud Run 서비스 배포 필요
- 권한 부족 → IAM 권한 확인

---

## 🚀 실제 Canary 배포 (Stage 1: 5%)

### Step 3: Stage 1 배포 실행

```powershell
# 실제 배포 (DryRun 성공 후에만 실행)
.\scripts\deploy_phase4_canary.ps1 -ProjectId naeda-genesis -CanaryPercentage 5
```

**실행 전 최종 확인**:
- [ ] DryRun 성공 확인
- [ ] 로컬 성능 테스트 완료
- [ ] 모니터링 대시보드 준비 완료
- [ ] 롤백 계획 숙지

**예상 소요 시간**: 2-3분

---

### Step 4: 배포 후 즉시 검증

#### 4.1 트래픽 분산 확인 (즉시)

```powershell
gcloud run services describe ion-api --project naeda-genesis --region us-central1 --format="value(status.traffic)"
```

**기대 결과**:

```
ion-api: 95%
ion-api-canary: 5%
```

**검증**: ✅/❌ ___________

---

#### 4.2 Canary 엔드포인트 Health Check (즉시)

```powershell
# Canary 서비스 직접 호출
Invoke-RestMethod -Uri "https://ion-api-canary-64076350717.us-central1.run.app/api/health" -Method GET
```

**기대 결과**:

```json
{
  "status": "healthy",
  "version": "canary",
  "lumen_gateway": "enabled"
}
```

**검증**: ✅/❌ ___________

---

#### 4.3 간단 기능 테스트 (5분 후)

```powershell
# Canary 엔드포인트로 실제 요청
$body = @{
    message = "Python의 장점을 간단히 설명해주세요"
    user_id = "test-canary-001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://ion-api-canary-64076350717.us-central1.run.app/chat" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

**검증 항목**:
- [ ] 응답 시간 < 15초
- [ ] 응답 포함: `success: true`
- [ ] 신뢰도 > 80%
- [ ] 오류 없음

**검증**: ✅/❌ ___________

---

## 📊 24시간 모니터링 계획

### 모니터링 지표

#### 핵심 메트릭 (5분 간격 체크)
1. **에러율**
   - 목표: < 1%
   - 롤백 트리거: > 5%
   - 모니터링: CloudWatch, GCS logs

2. **응답 시간 (P95)**
   - 목표: < 15초
   - 롤백 트리거: > 20초
   - 모니터링: Cloud Run metrics

3. **성공률**
   - 목표: > 95%
   - 롤백 트리거: < 90%
   - 모니터링: Application logs

---

### 모니터링 스크립트 실행

#### 자동 Canary 모니터링 (30분 간격)

```powershell
# 30분마다 자동 체크 (24시간 실행)
.\scripts\start_monitor_loop.ps1 -KillExisting -IntervalSeconds 1800 -DurationMinutes 1440
```

**설정**:
- 체크 간격: 30분 (1800초)
- 실행 시간: 24시간 (1440분)
- 자동 재시작: 예

**시작 시각**: ___________  
**종료 예정**: ___________ (+ 24시간)

---

#### Rate Limit 프로브 (선택 사항)

```powershell
# Canary와 Legacy 동시 테스트 (10 requests, 1초 간격)
.\scripts\rate_limit_probe.ps1 -RequestsPerSide 10 -DelayMsBetweenRequests 1000
```

**목적**: 두 서비스의 성능 및 안정성 비교

---

## 🔄 롤백 계획

### 자동 롤백 조건
1. **에러율 > 5%** (5분 윈도우)
2. **응답 시간 > 20초** (10분 윈도우)
3. **성공률 < 90%** (5분 윈도우)

### 수동 롤백 절차

#### 긴급 롤백 (즉시 실행)

```powershell
# 확인 없이 즉시 롤백 (Canary 0%)
.\scripts\emergency_rollback.ps1 -Force -SkipConfirmation
```

**실행 조건**:
- 심각한 오류 발생
- 서비스 다운
- 데이터 손실 위험

**예상 소요 시간**: 1분

---

#### 일반 롤백 (확인 후 실행)

```powershell
# 대화형 롤백 (Canary 0%)
.\scripts\rollback_phase4_canary.ps1 -ProjectId naeda-genesis -AutoApprove
```

**실행 조건**:
- 성능 저하 지속
- 사용자 불만 증가
- 기대 효과 미달

**예상 소요 시간**: 2-3분

---

## 📝 보고서 작성 계획

### 24시간 후 중간 보고서
**파일명**: `Week_3_Day_1_Stage1_중간보고서.md`

**내용**:
- 배포 과정 상세 기록
- 24시간 모니터링 결과
- 핵심 메트릭 분석:
  - 에러율
  - 응답 시간 (P50, P95, P99)
  - 성공률
  - 사용자 피드백
- Stage 2 진행 여부 결정

---

### 48시간 후 최종 보고서
**파일명**: `Week_3_Day_1_Stage1_완료보고서.md`

**내용**:
- 전체 Stage 1 결과 요약
- 성공/실패 분석
- 학습 사항
- Stage 2 계획 (10% 트래픽)

---

## 🎯 성공 기준

### Stage 1 (5% 트래픽) 성공 조건
- [x] 배포 완료 (트래픽 95% + 5%)
- [ ] 24시간 안정성 검증
  - [ ] 에러율 < 1%
  - [ ] 응답 시간 P95 < 15초
  - [ ] 성공률 > 95%
- [ ] 자동 롤백 트리거 없음
- [ ] 사용자 불만 사항 없음

**전체 평가**: ⏸️ 진행 중

---

## 📞 비상 연락망

### 문제 발생 시 대응 순서
1. **즉시**: 로그 확인 (`filter_logs_by_time.ps1 -Last 1h`)
2. **5분 내**: 롤백 여부 결정
3. **10분 내**: 긴급 롤백 실행 (필요 시)
4. **30분 내**: 원인 분석 및 보고서 작성

---

## 🚦 진행 상태 트래킹

### 체크리스트 진행률

#### 사전 준비 (0/3)
- [ ] Ion API 서비스 상태 확인
- [ ] Lumen Gateway 상태 확인
- [ ] GCP 프로젝트 연결 확인

#### Canary 배포 (0/4)
- [ ] 빠른 스모크 테스트 실행
- [ ] DryRun 스크립트 실행 및 검증
- [ ] Stage 1 실제 배포 (5%)
- [ ] 배포 후 즉시 검증

#### 모니터링 (0/2)
- [ ] 자동 모니터링 시작 (30분 간격)
- [ ] 24시간 안정성 검증

**전체 진행률**: 0% (0/9)

---

## 📌 다음 단계 미리보기

### Week 3 Day 2-3: Stage 2 준비 (10%)
- Stage 1 결과 분석
- Stage 2 배포 계획 수립
- 트래픽 10%로 증가

### Week 3 Day 4-5: Stage 3 (25%)
- 중간 규모 트래픽 테스트
- 성능 최적화

### Week 3 Day 6-7: Stage 4-5 (50% → 100%)
- 대규모 트래픽 검증
- 프로덕션 완전 전환

---

## ✅ 서명

**작성자**: 깃코 (AI Agent)  
**작성 시각**: 2025-10-22  
**상태**: 🔜 **준비 완료 - 실행 대기**

**첫 번째 명령어**:

```powershell
# GCP 프로젝트 연결 확인
gcloud run services list --project naeda-genesis --region us-central1
```

---

**체크리스트 종료**  
📋 준비 완료 → 🚀 실행 시작!
