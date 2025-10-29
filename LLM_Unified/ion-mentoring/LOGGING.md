# ION Mentoring 로깅 가이드

ION Mentoring 프로젝트의 구조화된 로깅 시스템을 사용하는 방법을 설명합니다.

## 목차

1. [개요](#개요)
2. [로깅 아키텍처](#로깅-아키텍처)
3. [로깅 사용법](#로깅-사용법)
4. [로그 포맷](#로그-포맷)
5. [프로덕션 배포](#프로덕션-배포)
6. [모니터링 & 분석](#모니터링--분석)
7. [문제 해결](#문제-해결)

---

## 개요

### 로깅 시스템의 특징

- **구조화된 JSON 로깅** - 모든 로그가 JSON 형식으로 출력됨
- **멀티 레이어 전송** - Console + File + Google Cloud Logging
- **환경별 설정** - 개발/테스트/프로덕션 각각 최적화된 설정
- **성능 메트릭 통합** - 응답 시간, 에러율 등 자동 수집
- **예외 추적** - Full stack trace와 컨텍스트 정보

### 핵심 모듈

```
app/
├── logging_setup.py         # 로깅 시스템 구현
├── main.py                   # 로깅 통합
└── config.py                 # 로깅 설정
```

---

## 로깅 아키텍처

### 계층 구조

```
┌─────────────────────────────────────┐
│     Application Code                 │
│  logger.info("message", extra={})   │
└────────────┬────────────────────────┘
             │
┌────────────v────────────────────────┐
│  StructuredFormatter                 │
│  (Message → JSON 변환)              │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┬─────────────┐
      │             │             │
┌─────v─────┐ ┌────v─────┐ ┌────v──────────┐
│  Console  │ │   File   │ │ Cloud Logging │
│ Handler   │ │ Handler  │ │    Handler    │
└───────────┘ └──────────┘ └───────────────┘
      │             │             │
      └─────────────┴─────────────┘
                    │
              ┌─────v──────────┐
              │  Output/Store  │
              │  Stdout/Files/ │
              │  Cloud Service │
              └────────────────┘
```

### 로거 설정 흐름

```python
# 1. 로거 초기화
logger = setup_logging(
    __name__,
    level="INFO",
    log_file="logs/app.log",
    use_cloud_logging=True,
    cloud_logger=cloud_logger
)

# 2. 로깅
logger.info("Message", extra={"key": "value"})

# 3. 포맷팅 (자동)
# {"message": "Message", "key": "value", "timestamp": "...", ...}

# 4. 전송 (자동)
# Console, File, Cloud Logging으로 전송
```

---

## 로깅 사용법

### 기본 로깅

```python
from app.logging_setup import get_logger

logger = get_logger(__name__)

# 기본 로깅
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### 추가 컨텍스트와 함께 로깅

```python
# extra 파라미터로 구조화 데이터 추가
logger.info(
    "User login",
    extra={
        "user_id": 123,
        "email": "user@example.com",
        "ip_address": "192.168.1.1"
    }
)

# 출력 (JSON):
# {
#   "message": "User login",
#   "user_id": 123,
#   "email": "user@example.com",
#   "ip_address": "192.168.1.1",
#   "timestamp": "2025-10-18T00:40:00.000000",
#   "level": "INFO",
#   ...
# }
```

### 헬퍼 함수 사용

#### 작업 실행 로깅

```python
from app.logging_setup import log_execution

log_execution(
    logger,
    "database_query",
    query="SELECT * FROM users",
    timeout_seconds=30
)

# 출력: "Operation started: database_query"
```

#### 에러 로깅

```python
from app.logging_setup import log_error

try:
    risky_operation()
except Exception as e:
    log_error(
        logger,
        "process_payment",
        e,
        user_id=123,
        amount=99.99
    )

# 출력: "Operation failed: process_payment - ..."
# 추가: full stack trace
```

#### 메트릭 로깅

```python
from app.logging_setup import log_metric

log_metric(
    logger,
    "response_time_ms",
    value=145.67,
    endpoint="/chat",
    persona="Lua"
)

# 출력: "Metric recorded: response_time_ms"
```

#### HTTP 요청 로깅

```python
from app.logging_setup import log_request

log_request(
    logger,
    method="POST",
    path="/chat",
    status_code=200,
    duration_ms=456.78,
    user_agent="curl/7.68.0"
)

# 출력: "HTTP request: POST /chat 200 (456.78ms)"
```

---

## 로그 포맷

### JSON 로그 필드

```json
{
  "message": "주요 메시지",
  "timestamp": "2025-10-18T00:40:00.000000",
  "level": "INFO",
  "module": "app.main",
  "function": "chat",
  "line_number": 495,
  "environment": "production",
  "service": "내다AI Ion API",
  "version": "1.0.0",
  "extra_fields": {
    "user_id": 123,
    "duration_ms": 145.67
  },
  "exception": {
    "type": "ValueError",
    "message": "Invalid input",
    "traceback": "..."
  }
}
```

### 로그 레벨

| 레벨 | 용도 | 환경 |
|------|------|------|
| **DEBUG** | 개발 디버깅 정보 | 개발 환경 |
| **INFO** | 중요한 이벤트 | 모든 환경 |
| **WARNING** | 경고 상황 | 모든 환경 |
| **ERROR** | 에러 발생 | 모든 환경 |
| **CRITICAL** | 치명적 에러 | 모든 환경 |

---

## 프로덕션 배포

### 환경 변수 설정

```bash
# .env (프로덕션)
ENVIRONMENT=production
LOG_LEVEL=INFO

# Google Cloud Logging
USE_CLOUD_LOGGING=true
GCP_PROJECT_ID=your-project-id
```

### 파일 로깅 디렉토리 생성

```bash
# 프로덕션 서버
mkdir -p /var/log/ion-api
chown -R app:app /var/log/ion-api
chmod 755 /var/log/ion-api
```

### Docker 설정

```dockerfile
# Dockerfile
...
# 로그 디렉토리 생성
RUN mkdir -p /var/log/ion-api && \
    chown -R app:app /var/log/ion-api

WORKDIR /app
...
```

### Kubernetes 설정

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ion-api
spec:
  template:
    spec:
      containers:
      - name: ion-api
        image: ion-api:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: USE_CLOUD_LOGGING
          value: "true"
        - name: GCP_PROJECT_ID
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: gcp_project_id
        volumeMounts:
        - name: logs
          mountPath: /var/log/ion-api
      volumes:
      - name: logs
        emptyDir: {}
```

---

## 모니터링 & 분석

### Google Cloud Logging 쿼리

#### 에러 로그 조회

```
severity="ERROR"
resource.type="cloud_run_revision"
resource.labels.service_name="ion-api"
```

#### 성능 메트릭 조회

```
jsonPayload.metric_name="response_time_ms"
resource.type="cloud_run_revision"
```

#### 특정 사용자 추적

```
jsonPayload.user_id="123"
```

### 로그 분석 대시보드

#### Metrics Explorer

```
Metric: logging.googleapis.com/user/response_time_ms
Filter: resource.service_name="ion-api"
```

#### Log-based Metrics

```yaml
# 에러율 메트릭
name: ion_error_rate
description: Error rate for Ion API
filter: severity="ERROR" AND resource.service_name="ion-api"
metric_type: gauge
```

### 알림 설정

#### 높은 에러율

```yaml
alert_policy:
  display_name: High Error Rate
  conditions:
  - display_name: Error rate > 1%
    condition_threshold:
      filter: |
        metric.type="custom.googleapis.com/ion_error_rate"
        resource.service_name="ion-api"
      threshold_value: 0.01
      comparison: COMPARISON_GREATER_THAN
```

#### 느린 응답

```yaml
alert_policy:
  display_name: Slow Response Times
  conditions:
  - display_name: Response time > 5 seconds
    condition_threshold:
      filter: |
        metric.type="custom.googleapis.com/response_time_ms"
        resource.service_name="ion-api"
      threshold_value: 5000
      comparison: COMPARISON_GREATER_THAN
```

---

## 문제 해결

### 1. 로그가 출력되지 않음

**원인:** 로그 레벨 설정이 높음

```python
# 확인
logger.setLevel(logging.DEBUG)

# 또는 환경 변수
export LOG_LEVEL=DEBUG
```

### 2. Google Cloud Logging이 작동하지 않음

**원인:** 인증 문제

```bash
# GCP 인증 확인
gcloud auth list

# 서비스 계정 설정
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# 권한 확인
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

### 3. 로그 파일 크기 증가

**해결책:** 로그 로테이션 설정

```python
# app/logging_setup.py에서 RotatingFileHandler 사용
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### 4. 성능 영향

**최적화:**

```python
# 개발 환경에서는 DEBUG 레벨 비활성화
if settings.environment == "production":
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.DEBUG)

# 불필요한 핸들러 제거
logger.handlers = [h for h in logger.handlers if not isinstance(h, FileHandler)]
```

---

## 모범 사례

### ✅ 좋은 예

```python
# 구조화된 데이터 포함
logger.info(
    "Chat request processed",
    extra={
        "user_id": user_id,
        "message_length": len(message),
        "response_time_ms": duration,
        "persona": result.persona_used,
        "confidence": result.confidence
    }
)

# 에러 추적
try:
    process_data()
except Exception as e:
    log_error(logger, "process_data", e, user_id=123)
```

### ❌ 나쁜 예

```python
# f-string으로 메시지 조합 (검색 어려움)
logger.info(f"User {user_id} processed chat for {message_length} chars")

# 에러 정보 손실
logger.error("Something went wrong")

# 민감한 정보 포함
logger.info("Password reset", extra={"password": password})
```

---

## 참고 문서

- [Python logging 공식 문서](https://docs.python.org/3/library/logging.html)
- [JSON 로깅 라이브러리](https://github.com/madzak/python-json-logger)
- [Google Cloud Logging 문서](https://cloud.google.com/logging/docs)
- [구조화된 로깅 모범 사례](https://www.splunk.com/en_us/blog/security/structured-logging-best-practices.html)

---

**로깅 시스템이 제대로 작동하지 않나요?** 로깅 테스트를 실행해보세요:

```bash
pytest tests/unit/test_logging.py -v
```
