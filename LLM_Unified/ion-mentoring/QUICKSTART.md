# 깃코 자연 대화 봇 - 5분 빠른 시작 가이드 ⚡

## 📝 3단계로 시작하기

### 1️⃣ 패키지 설치 (1분)

```powershell
cd D:\nas_backup\LLM_Unified
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn slack-sdk google-cloud-aiplatform python-multipart
```

### 2️⃣ Slack App 만들기 (3분)

**A. Slack App 생성**
1. https://api.slack.com/apps 접속
2. **"Create New App"** 클릭 → **"From scratch"** 선택
3. App Name: `Gitco` 입력
4. 워크스페이스 선택

**B. 권한 설정**
1. 좌측 메뉴에서 **"OAuth & Permissions"** 클릭
2. **"Bot Token Scopes"** 섹션에서 다음 권한 추가:
   - `chat:write` (메시지 전송)
   - `channels:history` (채널 메시지 읽기)
   - `im:history` (DM 메시지 읽기)

**C. 이벤트 구독 준비**
1. 좌측 메뉴에서 **"Event Subscriptions"** 클릭
2. **"Enable Events"** 토글 켜기
3. **Request URL은 나중에 설정** (봇 실행 후)

**D. 워크스페이스에 설치**
1. 좌측 메뉴에서 **"Install App"** 클릭
2. **"Install to Workspace"** 버튼 클릭
3. **"Allow"** 클릭
4. 생성된 **"Bot User OAuth Token"** 복사 (xoxb-로 시작)

### 3️⃣ 봇 실행 (1분)

**A. 환경 변수 설정**

```powershell
# 복사한 Slack Token 설정 (xoxb-로 시작하는 토큰)
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-당신의-토큰", "User")

# 배포 알림을 받을 Slack 채널 설정 (선택)
[Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "#deployments", "User")

# PowerShell 재시작 후 확인
$env:SLACK_BOT_TOKEN
$env:SLACK_ALERT_CHANNEL
```

**B. 봇 시작 (원클릭!)**

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\start_gitco_bot.ps1
```

성공하면 다음 메시지가 표시됩니다:

```
✅ 시작 완료!
  • 봇 PID: 12345
  • Tunnel PID: 67890
  • Public URL: https://your-tunnel-url.loca.lt

📝 Slack Event Subscriptions URL에 설정하세요:
   https://your-tunnel-url.loca.lt/slack/events
```

**C. Slack Event URL 설정**
1. Slack App 페이지로 돌아가기
2. **"Event Subscriptions"** 페이지에서
3. **Request URL**에 입력: `https://your-tunnel-url.loca.lt/slack/events`
4. ✅ 표시되면 **"Save Changes"** 클릭
5. **"Subscribe to bot events"**에서 추가:
   - `message.channels`
   - `message.im`
6. 다시 **"Save Changes"** 클릭

## 🎉 사용해보기

### Slack에서 봇과 대화

**1. 채널에 봇 초대**

```
Slack 채널에서: /invite @Gitco
```

**2. 자연스럽게 대화하기**

```
당신: 지금 배포 상태 어때?

Gitco: 🔍 현재 카나리 50% 배포 중이에요! 
       모니터링 단계이고 약 45분 후 다음 단계로 넘어갈 예정입니다.

당신: 문제 없어?

Gitco: 네, 모든 헬스 체크가 정상이에요! ✅ 
       에러율 0%, 레이턴시도 안정적입니다.

당신: 100% 올려도 될까?

Gitco: 네, 현재 상태가 안정적이어서 100% 배포 진행하셔도 좋을 것 같아요. 
       바로 시작할까요?

당신: 응, 해줘

Gitco: 알겠습니다! 🚀 100% 배포를 시작할게요...
       [2-3분 후]
       ✅ 100% 배포가 완료되었습니다!
```

## 💡 자주 하는 질문

### Q: 봇이 응답하지 않아요
1. **상태 확인**: `.\scripts\check_bot_status.ps1`
2. **로그 확인**: `.\scripts\show_bot_logs.ps1`
3. **재시작**: `.\scripts\start_gitco_bot.ps1 -KillExisting`
4. **토큰 확인**: `[Environment]::GetEnvironmentVariable("SLACK_BOT_TOKEN", "User")`

### Q: localtunnel URL이 계속 바뀌어요
- localtunnel은 재시작할 때마다 새 URL을 발급합니다
- 새 URL을 Slack Event Subscriptions에 업데이트해야 합니다
- 고정 URL이 필요하면 ngrok 유료 버전 사용을 고려하세요

### Q: 자동으로 시작되게 할 수 없나요?

```powershell
# 관리자 권한 PowerShell에서 실행
.\scripts\register_bot_scheduler.ps1
```

이제 시스템 시작/로그인 시 자동으로 봇이 실행됩니다!

### Q: GCP 인증 에러가 나요

```powershell
# Application Default Credentials 설정
gcloud auth application-default login

# 또는 Service Account Key 사용
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\key.json"
```

### Q: 봇 재시작하려면?

```powershell
# 재시작
.\scripts\start_gitco_bot.ps1 -KillExisting

# 종료만
.\scripts\start_gitco_bot.ps1 -StopOnly
```

### Q: 로그는 어디서 보나요?

```powershell
# 최근 로그 보기
.\scripts\show_bot_logs.ps1

# 실시간 로그 팔로우
.\scripts\show_bot_logs.ps1 -Follow

# 오래된 로그 정리 (7일 이상)
.\scripts\cleanup_old_bot_logs.ps1
```

## 🎯 다음 단계

### 🤖 자동 시작 설정

```powershell
# 관리자 권한 PowerShell에서:
.\scripts\register_bot_scheduler.ps1
```

이제 시스템 시작 시 자동으로 봇이 실행됩니다!

### 📊 상태 모니터링

```powershell
# 현재 상태 확인
.\scripts\check_bot_status.ps1

# 헬스 모니터링 (자동 재시작)
.\scripts\monitor_bot_health.ps1 -SendSlackAlert
```

### 🔧 유용한 명령어

```powershell
# 상태 확인
.\scripts\check_bot_status.ps1

# 로그 보기
.\scripts\show_bot_logs.ps1 -Follow

# 재시작
.\scripts\start_gitco_bot.ps1 -KillExisting

# 종료
.\scripts\start_gitco_bot.ps1 -StopOnly

# 로그 정리
.\scripts\cleanup_old_bot_logs.ps1 -KeepDays 7
```

### � 배포 알림 사용하기

Slack으로 배포 진행 상황을 실시간으로 받고 싶다면:

```powershell
# 배포 알림 채널 설정 (한 번만)
[Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "#deployments", "User")

# Slack 알림과 함께 배포
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\deploy_phase4_canary.ps1 `
    -ProjectId "naeda-genesis" `
    -CanaryPercentage 50 `
    -EnableSlackNotifications

# 자동 카나리 진행 (5% → 100%, Slack 알림 자동 활성화)
.\scripts\auto_canary_runner.ps1 -ProjectId "naeda-genesis"
```

**Slack에서 볼 수 있는 것:**
- 🔄 배포 시작/진행/완료 알림
- 📊 실시간 대시보드 (진행률 바, 메트릭)
- ⚠️ 에러 발생 시 즉시 알림
- ✅ 헬스 체크 결과

## �📚 더 알아보기

- 상세 가이드: `GITCO_NATURAL_CHAT.md`
- Slack 설정 가이드: `SLACK_BOT_SETUP.md`
- 자동화 가이드: `AUTOMATION_GUIDE.md`
- 소스 코드: `slack_bot_v2.py`

---

**🎉 완료!** 이제 Slack에서 깃코와 자연스럽게 대화하며 배포를 관리하세요!
