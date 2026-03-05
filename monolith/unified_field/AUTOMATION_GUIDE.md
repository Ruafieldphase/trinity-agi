# 깃코 슬랙 봇 - 완전 자동화 가이드 🚀

## 🎯 목표

깃코 슬랙 봇을 **완전 자동화**하여 다음을 달성합니다:
- ✅ 시스템 시작 시 자동 실행
- ✅ 백그라운드에서 로그 기록
- ✅ 자동 상태 모니터링 및 재시작
- ✅ Slack 알림 (선택)

---

## 📋 사전 준비

### 1. 환경 변수 설정 (필수)

```powershell
# Slack Bot Token 설정
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-당신의-토큰", "User")

# Slack 알림 채널 ID (선택)
[Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "C01234567890", "User")
```

**PowerShell을 재시작**하여 환경 변수를 적용하세요.

---

## 🚀 빠른 설정 (3단계)

### 1단계: 봇 시작

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\start_gitco_bot.ps1
```

출력된 Public URL을 복사하세요:

```
🌐 Public URL: https://your-url.loca.lt
📝 Slack Event Subscriptions URL에 설정하세요:
   https://your-url.loca.lt/slack/events
```

### 2단계: Slack Event URL 설정

1. https://api.slack.com/apps → 당신의 앱 선택
2. **Event Subscriptions** → **Request URL**에 입력:

   ```
   https://your-url.loca.lt/slack/events
   ```

3. ✅ 확인 후 **Save Changes**

### 3단계: 자동 시작 등록

**관리자 권한 PowerShell**에서 실행:

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring
.\scripts\register_bot_scheduler.ps1
```

완료! 이제 시스템을 재시작해도 봇이 자동으로 실행됩니다.

---

## 🔧 고급 설정

### 헬스 모니터링 설정

봇이 죽으면 자동으로 재시작하도록 설정:

```powershell
# 기본 모니터링 (60초마다 체크)
.\scripts\monitor_bot_health.ps1

# Slack 알림 포함
.\scripts\monitor_bot_health.ps1 -SendSlackAlert

# 30초마다 체크, 24시간 동안 실행
.\scripts\monitor_bot_health.ps1 -IntervalSeconds 30 -DurationMinutes 1440 -SendSlackAlert
```

### 모니터링도 자동 시작하기

**관리자 권한 PowerShell**에서:

```powershell
# 모니터링 작업 생성
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\nas_backup\LLM_Unified\ion-mentoring\scripts\monitor_bot_health.ps1`" -SendSlackAlert"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "GitcoBotHealthMonitor" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "깃코 봇 헬스 모니터링 및 자동 재시작"
```

---

## 📊 관리 명령어

### 상태 확인

```powershell
# 현재 상태 확인 (PID, 메모리, 업타임, 헬스)
.\scripts\check_bot_status.ps1
```

출력 예시:

```
✅ 정상 작동 중
  • 봇 서버: ✅ 실행 중 (PID: 12345)
    - 업타임: 5시간 32분
    - 메모리: 45.2 MB
  • Localtunnel: ✅ 실행 중 (PID: 67890)
    - URL: https://your-url.loca.lt
```

### 로그 확인

```powershell
# 최근 로그 보기
.\scripts\show_bot_logs.ps1

# 실시간 로그 팔로우
.\scripts\show_bot_logs.ps1 -Lines 100 -Follow

# 봇 로그만
.\scripts\show_bot_logs.ps1 -Type bot

# 터널 로그만
.\scripts\show_bot_logs.ps1 -Type tunnel
```

### 재시작

```powershell
# 봇 재시작 (기존 프로세스 종료 후 시작)
.\scripts\start_gitco_bot.ps1 -KillExisting
```

### 종료

```powershell
# 봇 종료만
.\scripts\start_gitco_bot.ps1 -StopOnly
```

### 로그 정리

```powershell
# 7일 이상 된 로그 정리 (미리보기)
.\scripts\cleanup_old_bot_logs.ps1 -DryRun

# 실제 삭제
.\scripts\cleanup_old_bot_logs.ps1

# 14일 보관
.\scripts\cleanup_old_bot_logs.ps1 -KeepDays 14
```

---

## 🗓️ 작업 스케줄러 관리

### 작업 확인

```powershell
# 등록된 작업 확인
Get-ScheduledTask | Where-Object { $_.TaskName -like "*Gitco*" }
```

### 수동 시작/중지

```powershell
# 수동 시작
Start-ScheduledTask -TaskName "GitcoSlackBot"

# 중지
Stop-ScheduledTask -TaskName "GitcoSlackBot"

# 비활성화 (시작 시 실행 안 됨)
Disable-ScheduledTask -TaskName "GitcoSlackBot"

# 다시 활성화
Enable-ScheduledTask -TaskName "GitcoSlackBot"
```

### 작업 제거

```powershell
# 자동 시작 제거
.\scripts\unregister_bot_scheduler.ps1

# 모니터링 제거
Unregister-ScheduledTask -TaskName "GitcoBotHealthMonitor" -Confirm:$false
```

---

## 🚨 문제 해결

### 봇이 시작되지 않아요

```powershell
# 1. 환경 변수 확인
[Environment]::GetEnvironmentVariable("SLACK_BOT_TOKEN", "User")

# 2. Python 경로 확인
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe --version

# 3. 로그 확인
.\scripts\show_bot_logs.ps1 -Type bot

# 4. 수동 실행으로 에러 확인
$env:SLACK_BOT_TOKEN = "xoxb-..."
python slack_bot_v2.py
```

### localtunnel이 연결 안 돼요

```powershell
# 1. localtunnel 설치 확인
npx localtunnel --version

# 2. 재설치
npm install -g localtunnel

# 3. 수동 테스트
npx localtunnel --port 8080
```

### Slack Event URL 검증 실패

1. **봇이 실행 중인지 확인**:

   ```powershell
   .\scripts\check_bot_status.ps1
   ```

2. **헬스 엔드포인트 테스트**:

   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8080/health"
   ```

3. **터널 URL 확인**:

   ```powershell
   .\scripts\check_bot_status.ps1
   # Public URL이 표시되는지 확인
   ```

4. **Slack에 올바른 URL 입력**:
   - `https://your-url.loca.lt/slack/events` (끝에 `/slack/events` 필수!)

### 자동 시작이 안 돼요

```powershell
# 1. 작업 상태 확인
Get-ScheduledTask -TaskName "GitcoSlackBot"

# 2. 작업 히스토리 확인
Get-ScheduledTaskInfo -TaskName "GitcoSlackBot"

# 3. 이벤트 로그 확인 (관리자 권한)
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" -MaxEvents 50 | 
  Where-Object { $_.Message -like "*GitcoSlackBot*" } |
  Select-Object TimeCreated, Message

# 4. 수동 실행 테스트
Start-ScheduledTask -TaskName "GitcoSlackBot"
Start-Sleep -Seconds 10
.\scripts\check_bot_status.ps1
```

---

## 📈 모니터링 대시보드

### 실시간 상태 확인 스크립트

`watch_bot.ps1` 생성:

```powershell
while ($true) {
    Clear-Host
    Write-Host "깃코 봇 실시간 모니터링" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Gray
    Write-Host ""
    
    .\scripts\check_bot_status.ps1
    
    Write-Host ""
    Write-Host "마지막 업데이트: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
    Write-Host "Ctrl+C로 종료" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 5
}
```

실행:

```powershell
.\watch_bot.ps1
```

---

## 🎯 권장 운영 방식

### 개발/테스트 환경

```powershell
# 수동 실행
.\scripts\start_gitco_bot.ps1

# 로그 팔로우
.\scripts\show_bot_logs.ps1 -Follow

# 종료
.\scripts\start_gitco_bot.ps1 -StopOnly
```

### 프로덕션 환경

1. **자동 시작 설정**:

   ```powershell
   .\scripts\register_bot_scheduler.ps1
   ```

2. **헬스 모니터링 등록** (위의 "모니터링도 자동 시작하기" 참조)

3. **주기적 로그 정리** (작업 스케줄러에 등록):

   ```powershell
   # 매주 일요일 새벽 3시에 로그 정리
   $action = New-ScheduledTaskAction `
       -Execute "PowerShell.exe" `
       -Argument "-NoProfile -ExecutionPolicy Bypass -File `"D:\nas_backup\LLM_Unified\ion-mentoring\scripts\cleanup_old_bot_logs.ps1`" -KeepDays 7"
   
   $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
   
   Register-ScheduledTask `
       -TaskName "GitcoBotLogCleanup" `
       -Action $action `
       -Trigger $trigger `
       -Description "깃코 봇 로그 정리 (7일 이상)"
   ```

4. **Slack 알림 활성화**:

   ```powershell
   [Environment]::SetEnvironmentVariable("SLACK_ALERT_CHANNEL", "C01234567890", "User")
   ```

---

## 📝 체크리스트

설정 완료 후 다음을 확인하세요:

- [ ] 환경 변수 `SLACK_BOT_TOKEN` 설정 완료
- [ ] 봇이 정상 실행됨 (`check_bot_status.ps1`)
- [ ] Slack Event Subscriptions URL 설정 완료
- [ ] Slack에서 봇과 대화 테스트 완료
- [ ] 작업 스케줄러에 자동 시작 등록 완료
- [ ] 헬스 모니터링 설정 완료 (선택)
- [ ] Slack 알림 설정 완료 (선택)
- [ ] 로그 정리 작업 등록 완료 (선택)

---

**🎉 완료!** 이제 깃코 봇이 완전 자동으로 운영됩니다!

문제가 발생하면:
1. `.\scripts\check_bot_status.ps1` 로 상태 확인
2. `.\scripts\show_bot_logs.ps1` 로 로그 확인
3. `.\scripts\start_gitco_bot.ps1 -KillExisting` 로 재시작
