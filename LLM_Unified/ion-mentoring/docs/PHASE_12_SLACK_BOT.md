# Phase 12: Slack Bot 통합 가이드

**작성일**: 2025년 10월 24일  
**Phase**: 12 - Slack Bot Integration  
**상태**: 🚧 진행 중  
**예상 소요**: 2-3일

---

## 📋 개요

ION API 배포 및 모니터링을 Slack을 통해 관리할 수 있는 Bot을 구현합니다.

### 목표

- ✅ **자연어 배포 명령**: Slack에서 바로 배포 실행
- ✅ **실시간 알림**: Critical/Warning 알림을 Slack으로 전송
- ✅ **인터랙티브 승인**: 버튼 클릭으로 배포 승인/거부
- ✅ **상태 조회**: 시스템 헬스, 성능 벤치마크 등

---

## 🎯 주요 기능

### 1. 배포 명령어

```
/ion deploy canary 5%        # 5% 카나리 배포
/ion deploy canary 50%       # 50% 카나리 배포
/ion deploy canary 100%      # 100% 카나리 배포
/ion rollback                # 즉시 롤백
/ion status                  # 현재 상태 확인
```

### 2. 상태 조회

```
/ion health                  # 시스템 헬스체크
/ion benchmark               # 성능 벤치마크 실행
/ion logs [service]          # 최근 로그 조회
/ion traffic [service]       # 트래픽 분배 상태
```

### 3. 자동 알림

- **Critical**: ION API Down, High Latency 등
- **Warning**: Mock Mode, Low Confidence 등
- **Deployment**: 배포 시작/완료/실패
- **Performance**: 성능 저하 감지

### 4. 인터랙티브 승인

```
배포 요청: canary 50%
[승인] [거부]

롤백 요청
[확인] [취소]
```

---

## 🛠️ 구현 계획

### Phase 12.1: Slack App 설정 (30분)

**작업**:
1. Slack Workspace에서 새 App 생성
2. Bot Token 발급
3. Scopes 설정
4. 환경 변수 설정

**필요한 Scopes**:
- `chat:write` - 메시지 전송
- `commands` - Slash Commands
- `incoming-webhook` - 알림 전송
- `users:read` - 사용자 정보 조회
- `channels:read` - 채널 정보 조회

**설정 파일**: `.env.slack`

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CHANNEL_ALERTS=#ion-alerts
SLACK_CHANNEL_DEPLOYMENTS=#ion-deployments
```

---

### Phase 12.2: 핵심 모듈 구현 (1일)

#### 1. slack_client.py
Slack API와의 통신을 담당하는 기본 클라이언트

**기능**:
- 메시지 전송
- 버튼 생성
- 스레드 응답
- 사용자 태그

#### 2. slack_commands.py
Slash Commands 파서 및 핸들러

**지원 명령어**:
- `/ion deploy <service> <percentage>`
- `/ion rollback`
- `/ion status`
- `/ion health`
- `/ion benchmark`
- `/ion help`

#### 3. slack_notifications.py
Prometheus/Alertmanager 알림을 Slack으로 전달

**알림 타입**:
- Critical (빨강, 즉시 알림)
- Warning (노랑, 요약 알림)
- Info (파랑, 배치 알림)

---

### Phase 12.3: 배포 통합 (1일)

#### 1. deployment_controller.py
기존 배포 스크립트와 Slack 통합

**흐름**:

```
1. Slack 명령 수신 (/ion deploy canary 50%)
2. 승인 요청 메시지 전송 (버튼 포함)
3. 승인 대기
4. 승인 시 배포 실행
5. 진행 상황 실시간 업데이트
6. 완료/실패 알림
```

#### 2. webhook_server.py
Slack 이벤트 수신용 웹훅 서버

**엔드포인트**:
- `/slack/events` - 이벤트 수신
- `/slack/commands` - Slash Commands
- `/slack/interactive` - 버튼 클릭 처리
- `/alertmanager` - Prometheus 알림

---

### Phase 12.4: 테스트 및 배포 (반나절)

**테스트 항목**:
1. [ ] 명령어 파싱 테스트
2. [ ] 메시지 전송 테스트
3. [ ] 버튼 인터랙션 테스트
4. [ ] 배포 명령 실행 테스트
5. [ ] 알림 전송 테스트
6. [ ] 에러 처리 테스트

---

## 📦 필요한 패키지

```bash
pip install slack-sdk slack-bolt flask requests python-dotenv
```

### 주요 라이브러리

- **slack-sdk**: Slack Web API 클라이언트
- **slack-bolt**: Bolt 프레임워크 (이벤트 처리)
- **flask**: 웹훅 서버
- **requests**: HTTP 요청
- **python-dotenv**: 환경 변수 관리

---

## 🏗️ 파일 구조

```
ion-mentoring/
├── slack_bot/
│   ├── __init__.py
│   ├── slack_client.py          # Slack API 클라이언트
│   ├── slack_commands.py        # 명령어 핸들러
│   ├── slack_notifications.py   # 알림 핸들러
│   ├── deployment_controller.py # 배포 컨트롤러
│   ├── webhook_server.py        # 웹훅 서버
│   └── utils.py                 # 유틸리티 함수
├── .env.slack                   # Slack 설정
└── scripts/
    └── start_slack_bot.ps1      # 봇 시작 스크립트
```

---

## 🔐 보안 고려사항

### 1. 토큰 보안
- `.env.slack` 파일을 `.gitignore`에 추가
- 환경 변수로만 토큰 관리
- 코드에 하드코딩 금지

### 2. 서명 검증

```python
def verify_slack_signature(request):
    """Slack 요청의 서명을 검증"""
    timestamp = request.headers['X-Slack-Request-Timestamp']
    signature = request.headers['X-Slack-Signature']
    
    # 타임스탬프 검증 (5분 이내)
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    # 서명 검증
    # ... (HMAC SHA256)
```

### 3. 권한 제어

```python
ALLOWED_USERS = [
    'U12345678',  # 사용자 ID
    'U87654321',
]

def is_authorized(user_id):
    return user_id in ALLOWED_USERS
```

---

## 📊 메시지 포맷 예시

### 배포 요청

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 배포 요청"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*서비스:*\nion-api-canary"},
        {"type": "mrkdwn", "text": "*비율:*\n50%"}
      ]
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "승인"},
          "style": "primary",
          "value": "approve"
        },
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "거부"},
          "style": "danger",
          "value": "deny"
        }
      ]
    }
  ]
}
```

### Critical 알림

```json
{
  "attachments": [
    {
      "color": "#ff0000",
      "blocks": [
        {
          "type": "header",
          "text": {
            "type": "plain_text",
            "text": "🚨 CRITICAL: ION API Down"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Summary:* ION API health check failed\n*Duration:* 2 minutes\n*Time:* 2025-10-24 22:30:15"
          }
        },
        {
          "type": "actions",
          "elements": [
            {
              "type": "button",
              "text": {"type": "plain_text", "text": "View Logs"},
              "url": "https://console.cloud.google.com/..."
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 배포 명령

```
입력: /ion deploy canary 10%
기대 결과:
1. 승인 요청 메시지 전송
2. [승인] 버튼 클릭
3. "배포 시작..." 메시지
4. 진행 상황 업데이트
5. "배포 완료 ✅" 메시지
```

### 시나리오 2: 상태 조회

```
입력: /ion status
기대 결과:
- 시스템 건강도 (5/5)
- Main/Canary 상태
- 응답시간
- 트래픽 분배
```

### 시나리오 3: 알림 수신

```
트리거: Prometheus alert (ION API Down)
기대 결과:
- #ion-alerts 채널에 메시지 전송
- Critical 알림 (빨강)
- 로그 링크 포함
```

---

## 🚀 다음 단계

1. **Phase 12.1**: Slack App 설정 및 환경 구성
2. **Phase 12.2**: 핵심 모듈 구현 (클라이언트, 명령어, 알림)
3. **Phase 12.3**: 배포 통합 및 웹훅 서버
4. **Phase 12.4**: 테스트 및 프로덕션 배포

---

**시작**: 2025년 10월 24일  
**예상 완료**: 2025년 10월 26일
