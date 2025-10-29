# 모니터링 및 알림 설정 가이드 (4시간 작업)

## 📋 개요

**목표**: 프로덕션 서비스의 상태를 지속적으로 모니터링하고 문제 발생 시 즉시 알림
**현재 상태**: ⚠️ 기본 로깅만 있음 - 체계적 모니터링 부재
**목표 상태**: ✅ 실시간 메트릭 수집, 알림 규칙 설정, 대시보드 구성

---

## 🎯 모니터링 목표

| 메트릭 | 경고 임계값 | 심각도 |
|--------|-----------|--------|
| **응답 시간 (P95)** | > 5초 | ⚠️ 경고 |
| **응답 시간 (P99)** | > 10초 | 🔴 심각 |
| **에러율** | > 1% | ⚠️ 경고 |
| **에러율** | > 5% | 🔴 심각 |
| **CPU 사용률** | > 80% | ⚠️ 경고 |
| **CPU 사용률** | > 95% | 🔴 심각 |
| **메모리 사용률** | > 85% | ⚠️ 경고 |
| **메모리 사용률** | > 95% | 🔴 심각 |
| **디스크 사용률 (DB)** | > 80% | ⚠️ 경고 |
| **데이터베이스 연결** | > 80 (max 100) | ⚠️ 경고 |
| **서비스 가동률** | < 99.9% | 🔴 심각 |

---

## 🛠️ 구현 가이드

### Phase 1: Google Cloud Monitoring 설정 (1시간)

#### Step 1-1: Monitoring API 활성화

```bash
# 환경 변수 설정
export GCP_PROJECT_ID="your-project-id"
export SERVICE_NAME="ion-api"
export REGION="us-central1"

# Monitoring API 활성화
gcloud services enable monitoring.googleapis.com \
  --project=$GCP_PROJECT_ID
```

#### Step 1-2: 알림 채널 생성

```bash
# 이메일 알림 채널 생성
gcloud alpha monitoring channels create \
  --display-name="Team Email" \
  --type=email \
  --channel-labels=email_address=devops@ion-mentoring.com \
  --project=$GCP_PROJECT_ID

# Slack 알림 채널 생성 (필요시)
gcloud alpha monitoring channels create \
  --display-name="Slack #alerts" \
  --type=slack \
  --channel-labels=channel_name="#alerts" \
  --project=$GCP_PROJECT_ID

# SMS 알림 채널 생성 (긴급용)
gcloud alpha monitoring channels create \
  --display-name="On-call Phone" \
  --type=sms \
  --channel-labels=number="+1234567890" \
  --project=$GCP_PROJECT_ID

# 알림 채널 목록 확인
gcloud alpha monitoring channels list --project=$GCP_PROJECT_ID
```

#### Step 1-3: 메트릭 확인

```bash
# Cloud Run 메트릭 확인
gcloud monitoring metrics-descriptors list \
  --filter="metric.type:run.googleapis.com" \
  --project=$GCP_PROJECT_ID

# 주요 메트릭:
# - run.googleapis.com/request_count: 요청 수
# - run.googleapis.com/request_latencies: 응답 시간
# - run.googleapis.com/container_memory_utilization: 메모리 사용률
# - run.googleapis.com/container_cpu_utilization: CPU 사용률
```

---

### Phase 2: 알림 규칙 생성 (2시간)

#### Step 2-1: 응답 시간 알림 (P95 > 5초)

**파일**: `gcp-configs/alert-policy-latency.yaml`

```yaml
# Monitoring Alert Policy - Latency (P95)

displayName: "High Latency Warning (P95 > 5s)"
documentation:
  content: |
    응답 시간 P95 초과

    ## 증상
    - 사용자가 느린 응답 보고
    - API 응답이 5초 이상

    ## 원인
    - 백엔드 과부하
    - 데이터베이스 성능 저하
    - 네트워크 지연

    ## 대응
    1. Monitoring 대시보드 확인
    2. 데이터베이스 쿼리 성능 분석
    3. Cloud Run 인스턴스 스케일 확인
    4. 필요시 수동 스케일링

conditions:
  - displayName: "Request latency p95 > 5s"
    conditionThreshold:
      filter: |
        metric.type="run.googleapis.com/request_latencies"
        resource.type="cloud_run_revision"
        resource.labels.service_name="ion-api"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_PERCENTILE_95"
      comparison: "COMPARISON_GT"
      thresholdValue: 5000  # milliseconds
      duration: "300s"      # alert after 5 minutes

notificationChannels:
  - "projects/$PROJECT_ID/notificationChannels/$CHANNEL_EMAIL_ID"

alertStrategy:
  autoClose: "1800s"  # Auto close after 30 minutes of normal operation
```

#### Step 2-2: 에러율 알림 (> 1%)

**파일**: `gcp-configs/alert-policy-error-rate.yaml`

```yaml
displayName: "High Error Rate Alert (> 1%)"
documentation:
  content: |
    에러율 임계값 초과

    ## 조사
    1. Cloud Logging에서 에러 로그 확인
    2. 특정 엔드포인트 확인
    3. 데이터베이스 연결 상태 확인

conditions:
  - displayName: "Error rate > 1%"
    conditionThreshold:
      filter: |
        metric.type="run.googleapis.com/request_count"
        resource.type="cloud_run_revision"
        resource.labels.service_name="ion-api"
        metric.labels.response_code_class="5xx"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_RATE"
      comparison: "COMPARISON_GT"
      thresholdValue: 0.01  # 1% (ratio)
      duration: "180s"

notificationChannels:
  - "projects/$PROJECT_ID/notificationChannels/$CHANNEL_EMAIL_ID"
```

#### Step 2-3: CPU 사용률 알림 (> 80%)

**파일**: `gcp-configs/alert-policy-cpu.yaml`

```yaml
displayName: "High CPU Usage Warning (> 80%)"

conditions:
  - displayName: "CPU > 80%"
    conditionThreshold:
      filter: |
        metric.type="run.googleapis.com/container_cpu_utilization"
        resource.type="cloud_run_revision"
        resource.labels.service_name="ion-api"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_MEAN"
      comparison: "COMPARISON_GT"
      thresholdValue: 0.80  # 80%
      duration: "300s"

notificationChannels:
  - "projects/$PROJECT_ID/notificationChannels/$CHANNEL_EMAIL_ID"
```

#### Step 2-4: 메모리 사용률 알림 (> 85%)

```yaml
displayName: "High Memory Usage Warning (> 85%)"

conditions:
  - displayName: "Memory > 85%"
    conditionThreshold:
      filter: |
        metric.type="run.googleapis.com/container_memory_utilization"
        resource.type="cloud_run_revision"
        resource.labels.service_name="ion-api"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_MEAN"
      comparison: "COMPARISON_GT"
      thresholdValue: 0.85
      duration: "300s"

notificationChannels:
  - "projects/$PROJECT_ID/notificationChannels/$CHANNEL_EMAIL_ID"
```

#### Step 2-5: 데이터베이스 디스크 사용률 (> 80%)

```yaml
displayName: "Database Disk Usage High (> 80%)"

conditions:
  - displayName: "DB Disk > 80%"
    conditionThreshold:
      filter: |
        metric.type="cloudsql.googleapis.com/database/disk/utilization"
        resource.type="cloudsql_database"
        resource.labels.database_id="$PROJECT_ID:ion-db"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_MEAN"
      comparison: "COMPARISON_GT"
      thresholdValue: 0.80
      duration: "300s"

notificationChannels:
  - "projects/$PROJECT_ID/notificationChannels/$CHANNEL_EMAIL_ID"
```

#### 알림 규칙 배포

```bash
# 알림 규칙 생성
gcloud alpha monitoring policies create \
  --policy-from-file=gcp-configs/alert-policy-latency.yaml \
  --project=$GCP_PROJECT_ID

# 또는 gcloud CLI로 직접 생성 (권장)
CHANNEL_ID=$(gcloud alpha monitoring channels list \
  --filter='displayName:"Team Email"' \
  --format='value(name)' \
  --project=$GCP_PROJECT_ID | head -1)

# 응답 시간 알림
gcloud alpha monitoring policies create \
  --notification-channels=$CHANNEL_ID \
  --display-name="High Latency Warning (P95 > 5s)" \
  --condition-display-name="Request latency p95 > 5s" \
  --condition-threshold-value=5000 \
  --condition-threshold-duration=300s \
  --condition-threshold-filter='metric.type="run.googleapis.com/request_latencies" AND resource.type="cloud_run_revision"' \
  --project=$GCP_PROJECT_ID
```

---

### Phase 3: 커스텀 메트릭 구현 (1시간)

#### Step 3-1: 애플리케이션에서 커스텀 메트릭 발행

**파일**: `app/metrics.py` (새로 생성)

```python
"""Google Cloud Monitoring을 위한 커스텀 메트릭"""

from google.cloud import monitoring_v3
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)


class CustomMetricsCollector:
    """Google Cloud Monitoring 커스텀 메트릭"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

    def write_metric(self, metric_type: str, value: float, labels: dict = None):
        """
        커스텀 메트릭 기록

        Args:
            metric_type: 메트릭 타입 (custom.googleapis.com/ion/...)
            value: 메트릭 값
            labels: 레이블 딕셔너리
        """
        try:
            # 시계열 데이터 포인트 생성
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10 ** 9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point(
                {"interval": interval, "value": {"double_value": value}}
            )

            # 메트릭 쓰기
            series = monitoring_v3.TimeSeries(
                {
                    "metric": {
                        "type": metric_type,
                        "labels": labels or {}
                    },
                    "points": [point],
                }
            )

            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            logger.debug(f"Metric recorded: {metric_type} = {value}")
        except Exception as e:
            logger.error(f"Failed to record metric {metric_type}: {str(e)}")

    def track_request_latency(self, endpoint: str):
        """요청 지연 시간 추적 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    latency = (time.time() - start_time) * 1000  # milliseconds
                    self.write_metric(
                        "custom.googleapis.com/ion/request_latency",
                        latency,
                        {"endpoint": endpoint}
                    )
            return wrapper
        return decorator

    def track_persona_selection(self, persona: str):
        """페르소나 선택 횟수 추적"""
        self.write_metric(
            "custom.googleapis.com/ion/persona_selection_count",
            1.0,
            {"persona": persona}
        )

    def track_cache_hit_rate(self, is_hit: bool):
        """캐시 히트율 추적"""
        self.write_metric(
            "custom.googleapis.com/ion/cache_hit",
            1.0 if is_hit else 0.0,
            {}
        )

    def track_token_usage(self, tokens: int, model: str):
        """토큰 사용량 추적"""
        self.write_metric(
            "custom.googleapis.com/ion/token_usage",
            float(tokens),
            {"model": model}
        )


# 싱글톤 인스턴스
_metrics_collector = None


def get_metrics_collector(project_id: str) -> CustomMetricsCollector:
    """메트릭 수집기 싱글톤 반환"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = CustomMetricsCollector(project_id)
    return _metrics_collector
```

#### Step 3-2: 메인 애플리케이션에 통합

**파일**: `app/main.py` (수정)

```python
# 기존 임포트 후 추가
from app.metrics import get_metrics_collector

# 메트릭 수집기 초기화
metrics = None
if is_production() and settings.gcp_project_id:
    metrics = get_metrics_collector(settings.gcp_project_id)

# /chat 엔드포인트에 메트릭 추가
@app.post("/chat", response_model=ChatResponse, ...)
@metrics.track_request_latency("/chat") if metrics else lambda f: f  # 조건부 데코레이터
async def chat(request: Request, chat_request: ChatRequest):
    try:
        # ... 기존 코드 ...

        result = pipeline.process(chat_request.message)

        # 페르소나 선택 기록
        if metrics:
            metrics.track_persona_selection(result.persona_used)

        return ChatResponse(
            content=result.content,
            persona_used=result.persona_used,
            resonance_key=result.resonance_key,
            confidence=result.confidence,
            metadata=result.metadata
        )
    except Exception as e:
        # ... 기존 에러 처리 ...
```

---

### Phase 4: 대시보드 생성 (30분)

#### Step 4-1: 모니터링 대시보드

**파일**: `gcp-configs/dashboard.json`

```json
{
  "displayName": "ION API Monitoring Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Latency (P95)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"ion-api\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_PERCENTILE_95"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.labels.response_code_class=\"5xx\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "CPU Utilization",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/container_cpu_utilization\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Memory Utilization",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/container_memory_utilization\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "yPos": 8,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Request Volume",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ]
          }
        }
      }
    ]
  }
}
```

#### Step 4-2: 대시보드 배포

```bash
# 대시보드 생성
gcloud monitoring dashboards create --config-from-file=gcp-configs/dashboard.json \
  --project=$GCP_PROJECT_ID

# 대시보드 확인
gcloud monitoring dashboards list --project=$GCP_PROJECT_ID
```

---

### Phase 5: 로깅 및 분석 (30분)

#### Step 5-1: Cloud Logging 쿼리 설정

**파일**: `gcp-configs/log-queries.sql`

```sql
-- 에러 로그 조회
SELECT
  timestamp,
  severity,
  jsonPayload.message,
  labels.function_name,
  httpRequest.requestUrl,
  httpRequest.status
FROM `project-id.region.cloud_run_instance`
WHERE severity = "ERROR"
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC
LIMIT 100;

-- 느린 요청 조회 (P95 > 5s)
SELECT
  timestamp,
  httpRequest.requestUrl,
  httpRequest.latency,
  httpRequest.status,
  labels.user_id
FROM `project-id.region.cloud_run_instance`
WHERE CAST(SUBSTR(httpRequest.latency, 1, LENGTH(httpRequest.latency) - 1) AS INT64) > 5000
ORDER BY timestamp DESC;

-- 페르소나별 요청 수
SELECT
  jsonPayload.persona_used,
  COUNT(*) as request_count,
  AVG(CAST(SUBSTR(httpRequest.latency, 1, LENGTH(httpRequest.latency) - 1) AS INT64)) as avg_latency_ms
FROM `project-id.region.cloud_run_instance`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY jsonPayload.persona_used
ORDER BY request_count DESC;
```

#### Step 5-2: 로그 싱크 생성 (BigQuery로 내보내기)

```bash
# BigQuery 데이터셋 생성
bq mk --dataset \
  --location=US \
  --description="ION API Logs" \
  ion_logs

# 로그 싱크 생성 (자동 내보내기)
gcloud logging sinks create ion-api-logs \
  bigquery.googleapis.com/projects/$GCP_PROJECT_ID/datasets/ion_logs \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api"' \
  --project=$GCP_PROJECT_ID
```

---

## 📊 모니터링 체크리스트

### 배포 전 확인
- [ ] Monitoring API 활성화
- [ ] 알림 채널 생성 (이메일, Slack 등)
- [ ] 알림 규칙 5개 생성 (응답시간, 에러율, CPU, 메모리, DB)
- [ ] 대시보드 생성 및 테스트
- [ ] 로깅 싱크 설정

### 배포 후 검증
- [ ] 메트릭 수집 시작 확인
- [ ] 대시보드에서 실시간 데이터 표시
- [ ] 테스트 알림 발송 (임계값 초과 테스트)
- [ ] Cloud Logging에서 로그 확인
- [ ] BigQuery로 로그 내보내기 확인

### 정기 검증 (주 1회)
- [ ] 대시보드에서 트렌드 분석
- [ ] 알림 규칙 작동 상태 확인
- [ ] 거짓 양성 알림 조정
- [ ] 새로운 메트릭 필요성 평가

---

## 🚨 Incident Response 프로세스

### Incident 1: High Error Rate Alert

**알림**: "High Error Rate Alert (> 1%)"

**1단계: 즉시 조사 (5분)**
```bash
# 실시간 에러 로그 확인
gcloud logging read \
  'severity=ERROR AND resource.type="cloud_run_revision"' \
  --limit=50 \
  --format=json \
  --project=$GCP_PROJECT_ID

# 에러 패턴 분석
gcloud logging read \
  'severity=ERROR' \
  --limit=100 \
  --format='value(jsonPayload.message)' \
  --project=$GCP_PROJECT_ID | sort | uniq -c | sort -rn
```

**2단계: 영향도 평가 (5분)**
- [ ] 에러 범위 확인 (특정 엔드포인트? 모든 엔드포인트?)
- [ ] 영향받은 사용자 수 추정
- [ ] 서비스 복구 가능성 평가

**3단계: 완화 조치 (10분)**
- [ ] 트래픽 스케일링 (인스턴스 추가)
- [ ] 문제 있는 버전 롤백
- [ ] 캐시 재설정

**4단계: 근본 원인 분석**
- [ ] 데이터베이스 성능 확인
- [ ] 외부 API 연동 상태 확인
- [ ] 최근 배포 내역 검토

### Incident 2: High Latency Alert

**알림**: "High Latency Warning (P95 > 5s)"

**조사**:
```bash
# Slow query 확인
gcloud logging read \
  'jsonPayload.message=~"Slow request"' \
  --limit=20 \
  --format=json \
  --project=$GCP_PROJECT_ID

# 데이터베이스 연결 풀 확인
gcloud sql instances describe ion-db \
  --format="value(currentDiskSize, settings.backupConfiguration)" \
  --project=$GCP_PROJECT_ID
```

**완화**:
- CPU/메모리 제한 증가
- 데이터베이스 인스턴스 업그레이드
- 캐시 추가

---

## 📞 지원 연락처

| 역할 | 담당자 | 연락처 | 근무시간 |
|------|--------|--------|---------|
| **DevOps** | 온콜 | +1 (555) 123-4567 | 24/7 |
| **백엔드** | On-call | Slack @backend | 평일 9-18시 |
| **데이터베이스** | DBA | dba@ion-mentoring.com | 평일 9-18시 |

---

## 📅 다음 단계

✅ **Phase 1 모든 작업 완료 (11시간)**
- ✅ CORS 보안 강화 (0.5시간)
- ✅ Google Secret Manager 통합 (4시간)
- ✅ 자동 백업 및 복구 (2시간)
- ✅ 모니터링 및 알림 (4시간)

🎯 **프로덕션 배포 준비 완료**

➡️ **Phase 2: 고우선순위 개선사항** (90시간 - 1-2주)
- Pre-commit hooks 설정 (3시간)
- WAF/Cloud Armor 설정 (6시간)
- 추가 보안 테스트 (4시간)
- 운영 가이드 문서 작성 (8시간)
- 기타 개선사항...
