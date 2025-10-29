# Cost Rhythm Loop - 통합 가이드

**Lumen v1.4-v1.7 철학 기반 비용 관리 시스템**

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [설치 및 설정](#설치-및-설정)
- [사용 방법](#사용-방법)
- [운영 매뉴얼](#운영-매뉴얼)
- [트러블슈팅](#트러블슈팅)

---

## 개요

Cost Rhythm Loop는 Lumen v1.4-v1.7의 철학을 ION 시스템에 적용한 비용 관리 시스템입니다.

### 핵심 개념

**감응(Resonance) → 증빙(Proof) → 적응(Feedback) 루프**

1. **감응 (Budget Resonance Mapper)**
   - 비용 리듬 측정: coherence (일관성), phase (위상), entropy (엔트로피)
   - RESONANT / DISSONANT / CHAOTIC 상태 분류

2. **증빙 (Proof Ledger)**
   - 상태 저장 (`outputs/cost_rhythm_state.json`)
   - Markdown 리포트 생성
   - Cloud Monitoring 메트릭 전송

3. **적응 (Auto-Remediation + Approval Bridge)**
   - 자동 행동 제안: SCALE_DOWN / ROLLBACK / EMERGENCY_STOP
   - HMAC 서명 승인 링크 (5분 윈도우)
   - Slack 알림 연동

### Lumen 철학 통합

- **v1.4**: `auto_remediation_service.py` + `approval_bridge_linked.py` 패턴
- **v1.5**: `maturity_spectrum` 정보이론 기반 성숙도
- **v1.6**: `unified_gate_card` (ROI × SLO × Maturity)
- **v1.7**: `resonance_memory_bridge` 감응 기억

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Cost Rhythm Loop                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐          ┌────▼────┐
   │ Billing │           │  Rhythm │          │ Unified │
   │ Client  │           │ Metrics │          │  Gate   │
   └────┬────┘           └────┬────┘          └────┬────┘
        │                     │                     │
        │ Daily Costs         │ Coherence/Phase     │ ROI/SLO
        │                     │ /Entropy            │ /Maturity
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Rhythm Status    │
                    │  RESONANT         │
                    │  DISSONANT        │
                    │  CHAOTIC          │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Adaptive Action   │
                    │ NONE              │
                    │ SCALE_DOWN        │
                    │ ROLLBACK          │
                    │ EMERGENCY_STOP    │
                    └─────────┬─────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
      ┌────▼────┐       ┌─────▼─────┐     ┌─────▼─────┐
      │ Approval│       │   Slack   │     │Remediation│
      │ Bridge  │       │ Notifier  │     │  Actions  │
      └─────────┘       └───────────┘     └───────────┘
          │                    │                 │
          │ HMAC Token         │ Alert           │ gcloud
          │ 5min window        │                 │ update
          │                    │                 │
          └────────────────────┴─────────────────┘
```

---

## 설치 및 설정

### 1. Python 패키지 설치

```bash
cd LLM_Unified/ion-mentoring

# 필수 패키지
pip install google-cloud-monitoring google-cloud-bigquery requests numpy

# 선택 (BigQuery Billing Export 사용 시)
pip install google-cloud-billing
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# GCP 설정
GCP_PROJECT=naeda-genesis
SERVICE_NAME=ion-api-canary
GCP_REGION=us-central1

# 비용 설정
MONTHLY_BUDGET_USD=200.0

# BigQuery Billing Export (선택)
BILLING_DATASET=billing_export
BILLING_TABLE=gcp_billing_export_v1_*

# Slack 연동
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#ion-cost-alerts

# 승인 브리지
APPROVAL_SECRET=lumen-ion-approval-secret-key-2025
APPROVAL_BASE_URL=http://localhost:8080
EOF

# 환경 변수 로드
source .env
```

### 3. BigQuery Billing Export 설정 (권장)

1. GCP Console → Billing → Billing export 이동
2. BigQuery export 활성화
3. Dataset ID 입력 (예: `billing_export`)
4. 저장

### 4. Cloud Monitoring API 활성화

```bash
gcloud services enable monitoring.googleapis.com --project=$GCP_PROJECT
gcloud services enable cloudscheduler.googleapis.com --project=$GCP_PROJECT
gcloud services enable pubsub.googleapis.com --project=$GCP_PROJECT
```

---

## 사용 방법

### 기본 사용

#### 1. Cost Rhythm 상태 확인

```bash
cd LLM_Unified/ion-mentoring
python lumen/monitoring/cost_rhythm_loop.py
```

**출력 예시:**

```
======================================================================
Cost Rhythm Loop - Lumen 철학 통합
======================================================================

🔄 비용 리듬 상태 계산 중...

🟢 Rhythm Status: RESONANT
💰 Forecasted: $24.36 / $200.00
📊 Coherence: 0.850 | Phase: 0.920 | Entropy: 0.320
🎯 Action: NONE (Confidence: 100%)

✅ 상태 저장 완료: outputs/cost_rhythm_state.json

======================================================================
Cost Rhythm Report
======================================================================

# Cost Rhythm Loop Report

**Generated**: 2025-10-25T12:30:00.000000

## Rhythm Status

🟢 **Status**: RESONANT

## Cost Metrics

| Metric | Value |
|--------|-------|
| Current Spend (7d) | $5.70 |
| Daily Average | $0.81/day |
| Forecasted Monthly | $24.36 |
| Budget | $200.00 |

## Resonance Metrics (Lumen Philosophy)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Coherence (일관성) | 0.850 | ≥ 0.700 | ✅ |
| Phase (위상) | 0.920 | ≥ 0.800 | ✅ |
| Entropy (엔트로피) | 0.320 | ≤ 0.500 | ✅ |

## Recommendations

✅ Cost rhythm is stable. No action required.
```

#### 2. 승인 요청 테스트

```bash
python lumen/gates/approval_bridge.py
```

#### 3. Billing 데이터 조회

```bash
python lumen/monitoring/billing_client.py
```

#### 4. Slack 알림 테스트

```bash
python lumen/monitoring/slack_notifier.py
```

#### 5. 시나리오 테스트

```bash
python lumen/scripts/test_cost_rhythm_loop.py
```

### Cloud Monitoring Dashboard

Dashboard에 Cost Rhythm 메트릭이 추가되었습니다:

- **Row 6: Cost Rhythm Metrics**
  - Cost Coherence (일관성)
  - Cost Phase (위상)
  - Cost Entropy (엔트로피)
  - Budget Usage Trend
  - Cost Rhythm Status

배포:

```bash
python lumen/scripts/deploy_dashboard.py
```

### Cloud Scheduler 설정

매시간 자동으로 Cost Rhythm을 체크하도록 설정:

```bash
python lumen/scripts/setup_cost_rhythm_scheduler.py
```

---

## 운영 매뉴얼

### 일일 점검

1. **Cost Rhythm 상태 확인**

```bash
python lumen/monitoring/cost_rhythm_loop.py
```

2. **Cloud Monitoring Dashboard 확인**
   - GCP Console → Monitoring → Dashboards → "Lumen System - ION API Monitoring"
   - Row 6: Cost Rhythm Metrics 확인

3. **Slack 알림 확인**
   - `#ion-cost-alerts` 채널
   - DISSONANT 또는 CHAOTIC 알림 시 즉시 대응

### 승인 프로세스

**Scenario: DISSONANT 상태 발생**

1. **Slack 알림 수신**

```
⚠️ Approval Required: SCALE_DOWN (scale_down_1729876543)

Request ID: scale_down_1729876543
Reason: Forecasted spend > budget + dissonant rhythm

Details:
  Current Spend: $25.50
  Forecasted: $220.00
  Budget: $200.00

[✅ Approve] [❌ Reject]

⏰ Expires at 2025-10-25T12:35:00 UTC (5 minutes)
```

2. **승인 결정**
   - ✅ Approve 클릭 → 자동으로 min_instances 감소
   - ❌ Reject 클릭 → 아무 조치 없음

3. **실행 확인**

```
✅ SCALE_DOWN APPROVED by admin@example.com

Request ID: scale_down_1729876543
Status: EXECUTED

Previous min_instances: 3
New min_instances: 1
```

### 비용 급등 대응

**Scenario: CHAOTIC 상태 + 예산 120% 초과**

1. **긴급 알림 수신**

```
❌ Approval Required: EMERGENCY_STOP

Forecasted spend: $240.00 (120% over budget)
Rhythm Status: CHAOTIC

[✅ Approve Emergency Stop]
```

2. **승인 후 자동 실행**
   - 모든 Cloud Run 인스턴스 중지 (min=0, max=0)
   - 비용 발생 중단

3. **원인 분석**

```bash
# 최근 로그 확인
gcloud logging read "resource.type=cloud_run_revision" \
  --project=$GCP_PROJECT \
  --limit=100 \
  --format=json

# 비용 급등 원인 파악
python lumen/monitoring/billing_client.py
```

4. **복구 계획**
   - 원인 제거
   - 설정 조정
   - 수동으로 인스턴스 재활성화

### 수동 Remediation

필요 시 수동으로 remediation 실행:

#### Scale Down

```bash
python lumen/monitoring/remediation_actions.py \
  --action=scale_down \
  --min-instances=1
```

#### Rollback

```bash
python lumen/monitoring/remediation_actions.py \
  --action=rollback \
  --target-revision=ion-api-canary-00005-xyz
```

#### Emergency Stop

```bash
python lumen/monitoring/remediation_actions.py \
  --action=emergency_stop
```

---

## 트러블슈팅

### 문제: BigQuery 쿼리 실패

**증상:**

```
⚠️  BigQuery 쿼리 실패: 403 Access Denied
```

**해결:**

1. BigQuery Billing Export가 설정되어 있는지 확인
2. 서비스 계정에 BigQuery Data Viewer 권한 부여

```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

3. 더미 데이터로 fallback (자동)

### 문제: Slack 알림 전송 실패

**증상:**

```
❌ Slack 전송 실패 (400): invalid_payload
```

**해결:**

1. SLACK_WEBHOOK_URL 환경변수 확인
2. Slack App 설정에서 Incoming Webhooks 활성화
3. 채널 권한 확인

### 문제: HMAC 토큰 검증 실패

**증상:**

```
❌ HMAC 토큰 검증 실패: scale_down_1729876543
```

**해결:**

1. APPROVAL_SECRET 환경변수가 일관되게 설정되어 있는지 확인
2. 승인 링크가 5분 이내에 클릭되었는지 확인 (만료 여부)
3. `outputs/approval_states.json` 파일 확인

### 문제: gcloud 명령 실패

**증상:**

```
❌ Scale Down 실패: ERROR: (gcloud.run.services.update) Permission denied
```

**해결:**

1. gcloud 인증 확인

```bash
gcloud auth list
gcloud config set project $GCP_PROJECT
```

2. 서비스 계정에 Cloud Run Admin 권한 부여

```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

---

## 참고 자료

- **Lumen v1.4 설계**: `auto_remediation_service` + `approval_bridge_linked`
- **Lumen v1.5 설계**: `maturity_spectrum` (정보이론 기반)
- **Lumen v1.6 설계**: `unified_gate_card` (ROI × SLO × Maturity)
- **Lumen v1.7 설계**: `resonance_memory_bridge` (Track A/B/C)

### 디렉토리 구조

```
LLM_Unified/ion-mentoring/lumen/
├── monitoring/
│   ├── cost_rhythm_loop.py          # 핵심 모듈
│   ├── billing_client.py            # BigQuery 연동
│   ├── slack_notifier.py            # Slack 알림
│   └── remediation_actions.py       # 자동복구 실행
├── gates/
│   └── approval_bridge.py           # HMAC 승인 브리지
├── dashboards/
│   └── cloud_monitoring_dashboard.yaml  # Dashboard (Row 6 추가됨)
├── scripts/
│   ├── test_cost_rhythm_loop.py     # 시나리오 테스트
│   ├── setup_cost_rhythm_scheduler.py  # Cloud Scheduler 설정
│   └── deploy_dashboard.py          # Dashboard 배포
└── docs/
    └── COST_RHYTHM_GUIDE.md         # 이 문서
```

---

## 지원

문의: GitHub Issues 또는 Slack `#ion-dev` 채널

**생성일**: 2025-10-25  
**버전**: 1.0.0  
**Lumen 철학**: v1.4-v1.7 통합
