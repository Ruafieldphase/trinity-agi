# Task 1.2: Alert Policies 설정 가이드

## 📋 개요

Production 안정성 모니터링을 위한 Alert Policies 설정

**목표**: 
- Critical 문제 즉시 탐지
- Warning 수준 조기 경보
- 이메일 알림 자동화

---

## 🚨 Alert Policies 설정 현황

### ⚠️ gcloud alpha 컴포넌트 필요

현재 시스템에 `gcloud alpha` 컴포넌트가 설치되지 않았습니다.

**설치 방법**:

```powershell
# 관리자 권한으로 Google Cloud SDK Shell 실행 후:
gcloud components install alpha
```

---

## 📊 대안: Cloud Console에서 수동 설정

gcloud CLI 대신 Cloud Console에서 Alert Policies를 설정할 수 있습니다.

### 1. Notification Channel 생성

**URL**: https://console.cloud.google.com/monitoring/alerting/notifications?project=naeda-genesis

**설정**:
1. **CREATE NOTIFICATION CHANNEL** 클릭
2. **Channel Type**: Email
3. **Display Name**: ION Team Email
4. **Email Address**: devops@ion-mentoring.com (또는 실제 이메일)
5. **SAVE** 클릭

---

### 2. Critical Alert Policies 생성

#### 🚨 Critical #1: 5xx Error Rate > 5%

**URL**: https://console.cloud.google.com/monitoring/alerting/policies/create?project=naeda-genesis

**설정**:
- **Alert Name**: ION Critical - ion-api 5xx Error > 5%
- **Target**: Cloud Run Revision
- **Metric**: Request Count (run.googleapis.com/request_count)
- **Filter**: 
  - `service_name = "ion-api"`
  - `response_code_class = "5xx"`
- **Threshold**: > 0.05 (5%)
- **Duration**: 5 minutes
- **Notification Channel**: ION Team Email

**반복**:
- `service_name = "lumen-gateway"`로도 동일 설정

---

#### 🚨 Critical #2: P99 Latency > 2000ms

**설정**:
- **Alert Name**: ION Critical - ion-api P99 Latency > 2s
- **Target**: Cloud Run Revision
- **Metric**: Request Latencies (run.googleapis.com/request_latencies)
- **Filter**: `service_name = "ion-api"`
- **Aggregation**: 99th percentile
- **Threshold**: > 2000 ms
- **Duration**: 5 minutes
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

#### 🚨 Critical #3: No Running Instances

**설정**:
- **Alert Name**: ION Critical - ion-api No Instances
- **Target**: Cloud Run Revision
- **Metric**: Container Instance Count (run.googleapis.com/container/instance_count)
- **Filter**: `service_name = "ion-api"`
- **Threshold**: < 1
- **Duration**: 1 minute
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

### 3. Warning Alert Policies 생성

#### ⚠️ Warning #1: 4xx Error Rate > 10%

**설정**:
- **Alert Name**: ION Warning - ion-api 4xx Error > 10%
- **Target**: Cloud Run Revision
- **Metric**: Request Count (run.googleapis.com/request_count)
- **Filter**: 
  - `service_name = "ion-api"`
  - `response_code_class = "4xx"`
- **Threshold**: > 0.10 (10%)
- **Duration**: 10 minutes
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

#### ⚠️ Warning #2: P95 Latency > 1500ms

**설정**:
- **Alert Name**: ION Warning - ion-api P95 Latency > 1.5s
- **Target**: Cloud Run Revision
- **Metric**: Request Latencies (run.googleapis.com/request_latencies)
- **Filter**: `service_name = "ion-api"`
- **Aggregation**: 95th percentile
- **Threshold**: > 1500 ms
- **Duration**: 10 minutes
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

#### ⚠️ Warning #3: CPU > 80%

**설정**:
- **Alert Name**: ION Warning - ion-api CPU > 80%
- **Target**: Cloud Run Revision
- **Metric**: Container CPU Utilization (run.googleapis.com/container/cpu/utilizations)
- **Filter**: `service_name = "ion-api"`
- **Threshold**: > 0.80 (80%)
- **Duration**: 15 minutes
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

#### ⚠️ Warning #4: Memory > 85%

**설정**:
- **Alert Name**: ION Warning - ion-api Memory > 85%
- **Target**: Cloud Run Revision
- **Metric**: Container Memory Utilization (run.googleapis.com/container/memory/utilizations)
- **Filter**: `service_name = "ion-api"`
- **Threshold**: > 0.85 (85%)
- **Duration**: 15 minutes
- **Notification Channel**: ION Team Email

**반복**: lumen-gateway도 설정

---

## 📊 설정 완료 체크리스트

### Services: ion-api, lumen-gateway (각 2개 서비스)

#### Critical Alerts (각 서비스당 3개)
- [ ] 5xx Error Rate > 5% (5분)
- [ ] P99 Latency > 2000ms (5분)
- [ ] Instance Count < 1 (1분)

#### Warning Alerts (각 서비스당 4개)
- [ ] 4xx Error Rate > 10% (10분)
- [ ] P95 Latency > 1500ms (10분)
- [ ] CPU > 80% (15분)
- [ ] Memory > 85% (15분)

**총 Alert Policies**: 2 services × 7 alerts = **14 policies**

---

## 🎯 예상 효과

### 즉각 대응
- **Critical Alerts**: 5분 이내 심각한 문제 탐지
- **Warning Alerts**: 10-15분 이내 성능 저하 감지

### 운영 효율
- **Before**: 사용자 신고 → 문제 인지 (수 시간 지연)
- **After**: 자동 알림 → 즉시 대응 (5-15분)

### 비용 절감
- 장애 시간 단축: 평균 2시간 → 15분
- 월 1회 장애 가정: 월 2시간 절약
- **연간 절감**: 24시간 × $100/h = $2,400

---

## 📝 현재 상태

**Status**: ⏸️ **수동 설정 필요**

**Reason**: gcloud alpha 컴포넌트 미설치

**Options**:
1. ✅ **추천**: Cloud Console에서 수동 설정 (15-20분)
2. ⏳ **자동화**: gcloud alpha 설치 후 스크립트 실행 (5분)

---

## 🔗 Quick Links

- [Notification Channels](https://console.cloud.google.com/monitoring/alerting/notifications?project=naeda-genesis)
- [Create Alert Policy](https://console.cloud.google.com/monitoring/alerting/policies/create?project=naeda-genesis)
- [Existing Policies](https://console.cloud.google.com/monitoring/alerting/policies?project=naeda-genesis)
- [Cloud Monitoring Dashboard](https://console.cloud.google.com/monitoring/dashboards?project=naeda-genesis)

---

## 다음 단계

**Option A**: Cloud Console에서 수동 설정 (지금 바로 가능)
- 예상 시간: 15-20분
- 위 가이드 참조하여 14개 Alert Policies 생성

**Option B**: 자동화 스크립트 실행 (gcloud alpha 설치 후)
- gcloud alpha 설치 필요
- 예상 시간: 5분

**추천**: Option A (수동 설정)로 먼저 진행하여 즉시 모니터링 시작
