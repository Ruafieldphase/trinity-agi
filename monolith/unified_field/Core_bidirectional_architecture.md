# Core 양방향 통신 아키텍처

## 개요

MCP(단방향) + HTTP API(양방향)를 결합하여 AI 클라이언트와 Core 시스템이 서로 대화할 수 있는 구조입니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   AI Client (Cursor)                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  MCP Tools (Pull)          HTTP API (Push)               │
│  ┌──────────────┐          ┌───────────────┐            │
│  │ get_quality  │          │ subscribe     │            │
│  │ get_weights  │          │ notifications │            │
│  │ trigger_     │          │               │            │
│  │ learning     │          │ long_polling  │            │
│  └──────┬───────┘          └───────▲───────┘            │
│         │                          │                     │
└─────────┼──────────────────────────┼─────────────────────┘
          │                          │
          ▼                          │
┌─────────────────────────────────────────────────────────┐
│            Core MCP+API Server (Port 8090)              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  MCP Protocol (stdio)     NotificationManager            │
│  ┌─────────────────┐      ┌──────────────────┐          │
│  │ Tool Handlers   │◄─────┤ Publish Events   │          │
│  │ - get_quality   │      │ - quality_alert  │          │
│  │ - get_weights   │      │ - learning_done  │          │
│  │ - trigger_learn │──────►│ - phase_change   │          │
│  └─────────────────┘      └──────────────────┘          │
│                                    │                     │
│  FastAPI HTTP Server               │                     │
│  ┌─────────────────┐              │                     │
│  │ /subscribe      │              │                     │
│  │ /notifications  │◄─────────────┘                     │
│  │ /notify         │                                     │
│  └─────────────────┘                                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
          │                          ▲
          │                          │
          ▼                          │
┌─────────────────────────────────────────────────────────┐
│                 Core Backend System                     │
├─────────────────────────────────────────────────────────┤
│  resonance_ledger.jsonl                                  │
│  ensemble_weights.json                                   │
│  binoche_online_learner.py                               │
│  summarize_ledger.py                                     │
│                                                           │
│  → Events trigger notifications                          │
│     (quality < 0.8, learning complete, etc.)            │
└─────────────────────────────────────────────────────────┘
```

## 통신 방식

### 1. Pull 방식 (MCP, 단방향)

AI가 필요할 때 요청:

```python
# Cursor에서 실행
result = await client.call_tool("core_get_quality_metrics", {"hours": 24})
# → Core이 처리하고 결과 반환
```

### 2. Push 방식 (HTTP API, 양방향)

Core이 먼저 알림:

```python
# 1. AI가 구독 등록
await client.subscribe("cursor-001", ["quality_alert", "learning_complete"])

# 2. AI가 대기 (long polling)
notification = await client.get_notifications("cursor-001", timeout=30)

# 3. Core이 이벤트 발생 시 자동 알림
# - Quality 0.7로 떨어짐 → quality_alert 발행
# - Phase 6l 학습 완료 → learning_complete 발행
# - AI는 즉시 알림 수신
```

## 사용 예시

### Case 1: AI가 정기적으로 상태 확인 (Pull)

```python
# Cursor에서 1시간마다 실행
quality = await core_get_quality_metrics(hours=1)
if quality.avg_quality < 0.8:
    print("⚠️ Quality degraded!")
```

### Case 2: Core이 문제 발생 시 알림 (Push)

```python
# AI가 한 번만 구독 설정
await core_subscribe_notifications("cursor-001", ["quality_alert"])

# 이후 계속 대기
while True:
    notification = await core_get_notifications("cursor-001")
    if notification.topic == "quality_alert":
        print(f"🚨 Quality alert: {notification.data}")
        # 자동으로 대응 조치 실행
        await core_trigger_learning(window_hours=6, learning_rate=0.02)
```

### Case 3: 다른 PC에서 안전하게 사용 (네트워크)

```bash
# PC A: Core 서버 실행
python core_mcp_api_server.py

# PC B: Cursor에서 HTTP API 호출
curl http://pc-a-ip:8090/api/v1/subscribe \
  -d '{"client_id": "cursor-pc-b", "topics": ["learning_complete"]}'

# PC B가 PC A의 Core 이벤트를 실시간 수신
```

## 장점

1. **단방향 문제 해결**: AI가 계속 polling 하지 않아도 Core이 먼저 알림
2. **네트워크 안전**: 다른 PC에서 HTTP로 접근 가능 (파일 충돌 없음)
3. **확장성**: 여러 AI 클라이언트가 동시에 구독 가능
4. **효율성**: Long polling으로 실시간성 유지하면서 리소스 절약

## 설치

```bash
pip install fastapi uvicorn
```

## 실행

```bash
# MCP + API 동시 실행
python core_mcp_api_server.py
```

## API 엔드포인트

### POST /api/v1/subscribe

AI 클라이언트 구독 등록

```json
{
  "client_id": "cursor-001",
  "topics": ["quality_alert", "learning_complete", "phase_transition"]
}
```

### GET /api/v1/notifications/{client_id}?timeout=30

알림 대기 (long polling, 최대 30초)

### POST /api/v1/notify

Core 내부에서 알림 발행 (scheduled tasks에서 호출)

```json
{
  "topic": "quality_alert",
  "data": {"avg_quality": 0.75, "threshold": 0.8}
}
```

### GET /api/v1/health

헬스 체크

## 다음 단계

1. **Scheduled Tasks 통합**: `alert_system.ps1`에서 HTTP API로 알림 발행
2. **Webhook 지원**: AI 클라이언트가 callback URL 제공 시 자동 POST
3. **인증 추가**: API Key로 보안 강화
4. **Cloud 배포**: Google Cloud Run에 배포하여 인터넷에서 접근
