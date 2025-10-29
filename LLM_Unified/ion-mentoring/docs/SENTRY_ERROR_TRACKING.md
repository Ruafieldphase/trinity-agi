# Sentry 에러 추적 통합 가이드

## 📋 개요

**목표**: 프로덕션 에러 실시간 추적 및 자동 알림
**이점**: 에러 재현 시간 90% 단축, 근본 원인 신속 파악
**비용**: 월 $29 (스타트업 플랜)

---

## 🛠️ 설치 및 설정 (4시간)

### Step 1: Sentry 프로젝트 생성

```bash
# https://sentry.io에서 계정 생성
# 새 프로젝트: ION Mentoring
# Platform: Python / FastAPI
# DSN: https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

### Step 2: SDK 설치

```bash
pip install sentry-sdk
pip install sentry-sdk[fastapi]
```

### Step 3: FastAPI 통합

```python
# app/main.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% 성능 트레이싱
    profiles_sample_rate=0.1,  # 10% 프로파일링
    environment=settings.environment,
    release=settings.app_version,
    debug=False,
)

# 이제 모든 예외가 자동으로 Sentry에 보고됨
```

### Step 4: 커스텀 이벤트 캡처

```python
# 에러 기록
try:
    result = risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)  # 자동으로 Sentry 전송

# 메시지 기록
sentry_sdk.capture_message("Important event occurred", level="warning")

# 컨텍스트 추가
with sentry_sdk.push_scope() as scope:
    scope.set_context("user_input", {"message": user_message})
    scope.set_tag("persona", persona_name)
    sentry_sdk.capture_exception(e)
```

---

## 📊 모니터링 규칙

### Alert 설정

```
1. 에러율 > 5% (5분) → Slack 알림
2. 새로운 에러 발생 → 이메일 알림
3. Performance regression > 10% → Slack 알림
4. Release 배포 후 에러 → 즉시 알림
```

### 대시보드 구성

```
Issues:
├─ Recent issues
├─ Unresolved issues
├─ Regressed issues

Performance:
├─ Slowest transactions
├─ Most impactful transactions
└─ Error rate trends

Releases:
├─ Deployment tracking
├─ Performance change
└─ Error impact
```

---

## 🔍 에러 분류 및 우선순위

```
Severity 매핑:
- Fatal (P1): 서비스 다운
- Error (P2): 기능 장애
- Warning (P3): 잠재적 문제
- Info (P4): 정보성
```

---

## ⏱️ 예상 소요 시간: 4시간
