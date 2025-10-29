# Ion Canary Slack Bot 설정 가이드

## 1. Slack App 생성

### 1.1 Slack App 만들기
1. https://api.slack.com/apps 접속
2. "Create New App" 클릭
3. "From scratch" 선택
4. App Name: `Ion Canary Bot`
5. Workspace 선택

### 1.2 Bot Token Scopes 설정
**OAuth & Permissions** 페이지에서 다음 권한 추가:
- `chat:write` - 메시지 전송
- `chat:write.public` - 공개 채널에 메시지 전송
- `channels:history` - 채널 메시지 읽기
- `channels:read` - 채널 정보 읽기
- `groups:history` - 프라이빗 채널 메시지 읽기
- `im:history` - DM 메시지 읽기
- `im:read` - DM 정보 읽기
- `commands` - 슬래시 명령어

### 1.3 Event Subscriptions 설정
**Event Subscriptions** 페이지에서:
1. Enable Events 활성화
2. Request URL 설정: `http://your-server:8080/slack/events`
3. Subscribe to bot events:
   - `message.channels` - 채널 메시지
   - `message.groups` - 프라이빗 채널 메시지
   - `message.im` - DM 메시지

### 1.4 Slash Commands 생성 (선택사항)
**Slash Commands** 페이지에서:
- Command: `/gitco`
- Request URL: `http://your-server:8080/slack/commands`
- Short Description: `깃코 명령 실행`
- Usage Hint: `상태 / 50% 배포 / 프로브`

### 1.5 앱 설치
1. **Install App** 페이지에서 "Install to Workspace" 클릭
2. **Bot User OAuth Token** 복사 (xoxb-로 시작)

## 2. 환경 변수 설정

### PowerShell에서 설정

```powershell
# Bot Token 설정
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-your-token-here", "User")

# Signing Secret 설정 (앱 Basic Information 페이지에서 복사)
[Environment]::SetEnvironmentVariable("SLACK_SIGNING_SECRET", "your-signing-secret", "User")
```

### 설정 확인

```powershell
$env:SLACK_BOT_TOKEN
$env:SLACK_SIGNING_SECRET
```

## 3. Python 패키지 설치

```powershell
# 가상환경 활성화
cd D:\nas_backup\LLM_Unified
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r ion-mentoring\slack_bot_requirements.txt
```

## 4. Bot 서버 실행

### 개발 모드 (로컬)

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
python slack_bot_server.py
```

서버가 `http://localhost:8080`에서 실행됩니다.

### ngrok으로 공개 URL 생성 (로컬 테스트)

```powershell
# ngrok 설치: https://ngrok.com/download
ngrok http 8080
```

생성된 URL을 Slack App의 Event Subscriptions와 Slash Commands에 설정합니다.

### 백그라운드 실행

```powershell
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"cd D:\nas_backup\LLM_Unified\.venv\Scripts; .\Activate.ps1; cd D:\nas_backup\LLM_Unified\ion-mentoring; python slack_bot_server.py`"" -WindowStyle Hidden
```

## 5. 사용 방법

### 5.1 채널에 봇 초대
1. Slack 채널에서 `/invite @Ion Canary Bot` 입력
2. 또는 DM으로 봇과 직접 대화

### 5.2 명령어 예시

**상태 확인:**

```
상태
status
현재 어떻게 돼?
```

**배포 실행:**

```
50% 배포
deploy 100%
카나리 100% 올려줘
```

**프로브 실행:**

```
프로브
gentle 프로브
aggressive 테스트
```

**로그 확인:**

```
로그
logs
에러 있어?
```

**리포트 생성:**

```
리포트
report
일일 보고서
```

**롤백:**

```
롤백
rollback
되돌려줘
```

**도움말:**

```
help
도움말
사용법
```

### 5.3 자연어 대화
봇은 자연어를 이해합니다:
- "지금 배포 상태 어떻게 돼?"
- "100% 배포 시작해줘"
- "프로브 한번 돌려봐"
- "최근 로그 보여줘"

## 6. 운영 환경 배포

### Windows 서비스로 등록

```powershell
# NSSM (Non-Sucking Service Manager) 사용
# 다운로드: https://nssm.cc/download

nssm install IonSlackBot "D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe" "D:\nas_backup\LLM_Unified\ion-mentoring\slack_bot_server.py"
nssm set IonSlackBot AppDirectory "D:\nas_backup\LLM_Unified\ion-mentoring"
nssm set IonSlackBot AppEnvironmentExtra SLACK_BOT_TOKEN=xoxb-your-token
nssm start IonSlackBot
```

### Cloud Run 배포 (GCP)

```bash
# Dockerfile 생성
cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY slack_bot_requirements.txt .
RUN pip install --no-cache-dir -r slack_bot_requirements.txt
COPY slack_bot_server.py .
COPY scripts/ ./scripts/
CMD ["python", "slack_bot_server.py"]
EOF

# 배포
gcloud run deploy ion-slack-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SLACK_BOT_TOKEN=xoxb-your-token,SLACK_SIGNING_SECRET=your-secret
```

## 7. 트러블슈팅

### Bot이 응답하지 않음
1. 토큰 확인: `$env:SLACK_BOT_TOKEN`
2. 서버 실행 확인: `http://localhost:8080/health`
3. Slack Event Subscriptions URL 검증 통과 확인

### 권한 오류
- Bot Token Scopes에 필요한 권한 추가 후 재설치

### 스크립트 실행 실패
- PowerShell ExecutionPolicy 확인
- 스크립트 경로 확인: `SCRIPTS_DIR` 변수

### 메시지가 두 번 전송됨
- Event Subscriptions에서 중복 이벤트 구독 제거

## 8. 보안 고려사항

1. **토큰 보호**: 환경 변수로만 관리, 코드에 하드코딩 금지
2. **Request Verification**: Signing Secret으로 요청 검증 구현 권장
3. **Rate Limiting**: 과도한 요청 방지 로직 추가
4. **Access Control**: 특정 사용자/채널만 허용하는 권한 체크

## 9. 확장 기능

### 인터랙티브 버튼 추가

```python
# Block Kit으로 버튼 UI 추가
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "배포 옵션을 선택하세요:"}
    },
    {
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "50%"}, "value": "deploy_50"},
            {"type": "button", "text": {"type": "plain_text", "text": "100%"}, "value": "deploy_100"}
        ]
    }
]
```

### 스케줄 리포트

```python
# APScheduler로 정기 리포트
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=9)
scheduler.start()
```

## 10. 모니터링

### 로그 확인

```powershell
# 서버 로그
Get-Content -Path "ion-mentoring\outputs\slack_bot.log" -Tail 100 -Wait
```

### Health Check

```powershell
# 서버 상태 확인
Invoke-RestMethod http://localhost:8080/health
```

---

**문의사항**: Slack 채널에서 `@Ion Canary Bot help` 입력
