# Lumen Gateway v1.0 - Alertmanager Setup Guide

## 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [Alertmanager 설치](#alertmanager-설치)
3. [Prometheus 연동](#prometheus-연동)
4. [Slack 통합](#slack-통합)
5. [Email 통합 (선택)](#email-통합-선택)
6. [Alert 테스트](#alert-테스트)
7. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수 구성요소
- ✅ Prometheus 설치 및 실행 중
- ✅ Gateway Exporter 실행 중 (Port 9108)
- ✅ Slack Workspace (webhook URL 필요)

### 선택 구성요소
- Email SMTP 계정 (Gmail, Outlook 등)
- Windows Service 설정 (자동 시작)

---

## Alertmanager 설치

### Step 1: 다운로드

**Windows (PowerShell)**:

```powershell
# 다운로드 디렉토리 생성
New-Item -ItemType Directory -Force -Path C:\prometheus\alertmanager

# 최신 버전 다운로드 (예: 0.26.0)
$version = "0.26.0"
$url = "https://github.com/prometheus/alertmanager/releases/download/v$version/alertmanager-$version.windows-amd64.zip"
Invoke-WebRequest -Uri $url -OutFile "C:\prometheus\alertmanager.zip"

# 압축 해제
Expand-Archive -Path "C:\prometheus\alertmanager.zip" -DestinationPath "C:\prometheus" -Force

# 파일 이동
Move-Item -Path "C:\prometheus\alertmanager-$version.windows-amd64\*" -Destination "C:\prometheus\alertmanager" -Force

# 정리
Remove-Item "C:\prometheus\alertmanager.zip"
Remove-Item "C:\prometheus\alertmanager-$version.windows-amd64" -Recurse
```

**Linux/macOS**:

```bash
cd /opt
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
mv alertmanager-0.26.0.linux-amd64 alertmanager
rm alertmanager-0.26.0.linux-amd64.tar.gz
```

### Step 2: 설정 파일 복사

```powershell
# Gateway alerts 설정을 Alertmanager 디렉토리로 복사
Copy-Item "d:\nas_backup\LLM_Unified\ion-mentoring\gateway\alerts\alertmanager.yml" `
          -Destination "C:\prometheus\alertmanager\alertmanager.yml"
```

### Step 3: 환경 변수 설정

**Windows (PowerShell)**:

```powershell
# Slack Webhook URL 설정 (필수)
[Environment]::SetEnvironmentVariable("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/YOUR/WEBHOOK/URL", "User")

# Email 비밀번호 설정 (선택)
[Environment]::SetEnvironmentVariable("SMTP_PASSWORD", "your-app-password", "User")

# 환경 변수 즉시 적용
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Linux/macOS**:

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export SMTP_PASSWORD="your-app-password"
source ~/.bashrc
```

### Step 4: Alertmanager 실행

**Windows (PowerShell)**:

```powershell
# 포그라운드 실행 (테스트용)
cd C:\prometheus\alertmanager
.\alertmanager.exe --config.file=alertmanager.yml

# 백그라운드 실행 (운영용)
Start-Process -FilePath "C:\prometheus\alertmanager\alertmanager.exe" `
              -ArgumentList "--config.file=C:\prometheus\alertmanager\alertmanager.yml" `
              -WindowStyle Hidden
```

**Linux/macOS**:

```bash
# 포그라운드 실행
cd /opt/alertmanager
./alertmanager --config.file=alertmanager.yml

# 백그라운드 실행 (systemd 사용)
sudo systemctl start alertmanager
sudo systemctl enable alertmanager
```

### Step 5: 상태 확인

```powershell
# Web UI 접속
Start-Process "http://localhost:9093"

# API 엔드포인트 확인
Invoke-RestMethod -Uri "http://localhost:9093/-/healthy"
Invoke-RestMethod -Uri "http://localhost:9093/api/v2/status"
```

**기대 출력**:
- Web UI: Alertmanager dashboard 표시
- API: `{"status":"success"}` 또는 상태 정보 JSON

---

## Prometheus 연동

### Step 1: prometheus.yml 수정

**파일 위치**: `C:\prometheus\prometheus.yml`

```yaml
# Alertmanager 설정 추가
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Alert rules 파일 추가
rule_files:
  - "rules/prometheus_rules.yml"
```

### Step 2: Alert Rules 복사

```powershell
# Rules 디렉토리 생성
New-Item -ItemType Directory -Force -Path C:\prometheus\rules

# Gateway alert rules 복사
Copy-Item "d:\nas_backup\LLM_Unified\ion-mentoring\gateway\alerts\prometheus_rules.yml" `
          -Destination "C:\prometheus\rules\prometheus_rules.yml"
```

### Step 3: Prometheus 재시작

```powershell
# Prometheus 프로세스 찾기
$promProcess = Get-Process prometheus -ErrorAction SilentlyContinue

if ($promProcess) {
    # 프로세스 종료
    Stop-Process -Id $promProcess.Id -Force
    Start-Sleep -Seconds 2
}

# Prometheus 재시작
cd C:\prometheus
Start-Process -FilePath ".\prometheus.exe" `
              -ArgumentList "--config.file=prometheus.yml" `
              -WindowStyle Hidden
```

### Step 4: Rules 로드 확인

```powershell
# Prometheus UI에서 Rules 확인
Start-Process "http://localhost:9090/rules"

# API로 확인
Invoke-RestMethod -Uri "http://localhost:9090/api/v1/rules" | ConvertTo-Json -Depth 10
```

**기대 출력**:
- `lumen_gateway_alerts` 그룹이 표시됨
- 13개 alert rules 확인 (IONAPIDown, GatewayUnlocked, 등)

---

## Slack 통합

### Step 1: Slack Incoming Webhook 생성

1. Slack Workspace 접속
2. **Apps** → **Incoming Webhooks** 검색
3. **Add to Slack** 클릭
4. 채널 선택 (예: `#lumen-alerts-critical`)
5. Webhook URL 복사 (예: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

### Step 2: 환경 변수 설정

```powershell
# Webhook URL 설정
$webhookUrl = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
[Environment]::SetEnvironmentVariable("SLACK_WEBHOOK_URL", $webhookUrl, "User")
$env:SLACK_WEBHOOK_URL = $webhookUrl
```

### Step 3: Slack 채널 생성 (권장)

Alert 심각도별로 채널 분리:
- `#lumen-alerts-critical` → 즉시 대응 필요
- `#lumen-alerts-warnings` → 곧 대응 필요
- `#lumen-alerts-info` → 정보성 알림

각 채널에 Incoming Webhook 추가하고 `alertmanager.yml`의 `channel` 필드 수정

### Step 4: Alertmanager 재시작

```powershell
# Alertmanager 프로세스 종료
Get-Process alertmanager -ErrorAction SilentlyContinue | Stop-Process -Force

# 재시작 (환경 변수 반영)
cd C:\prometheus\alertmanager
Start-Process -FilePath ".\alertmanager.exe" `
              -ArgumentList "--config.file=alertmanager.yml" `
              -WindowStyle Hidden
```

---

## Email 통합 (선택)

### Gmail 사용 시

**Step 1: App Password 생성**
1. Google Account → Security → 2-Step Verification 활성화
2. **App passwords** → **Mail** → **Windows Computer** 선택
3. 생성된 16자리 비밀번호 복사

**Step 2: alertmanager.yml 수정**

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
```

**Step 3: 환경 변수 설정**

```powershell
$appPassword = "your-16-char-app-password"
[Environment]::SetEnvironmentVariable("SMTP_PASSWORD", $appPassword, "User")
$env:SMTP_PASSWORD = $appPassword
```

**Step 4: Email receiver 활성화**

`alertmanager.yml`에서 `email_configs` 주석 제거:

```yaml
receivers:
  - name: 'lumen-critical'
    email_configs:
      - to: 'oncall@your-company.com'
        subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        # ...
```

---

## Alert 테스트

### Method 1: Manual Alert Triggering (amtool)

**amtool 다운로드**:

```powershell
# Alertmanager에 포함되어 있음
cd C:\prometheus\alertmanager
```

**Test alert 전송**:

```powershell
.\amtool.exe alert add --alertmanager=http://localhost:9093 `
  --annotation=summary="Test Alert" `
  --annotation=description="This is a test alert" `
  alertname=TestAlert severity=warning component=gateway
```

### Method 2: 실제 조건 트리거

**IONAPIDown 테스트**:

```powershell
# Gateway Exporter 중지
Get-Process python | Where-Object { $_.CommandLine -like "*gateway_health_exporter*" } | Stop-Process -Force

# 2분 대기 (alert 조건: for 2m)
Start-Sleep -Seconds 120

# Prometheus UI에서 alert 확인
Start-Process "http://localhost:9090/alerts"

# Alertmanager UI에서 alert 확인
Start-Process "http://localhost:9093/#/alerts"

# Slack 확인 (critical 채널)
```

**MockModeDetected 테스트**:

```powershell
# gateway_activation.yaml 임시 수정 (테스트용)
# Mock response를 반환하도록 ION API 응답 조작

# 1분 대기
Start-Sleep -Seconds 60

# Alert 확인
```

### Method 3: Alert Rules 직접 평가

```powershell
# Prometheus query 실행
$query = "lumen_ion_health == 0"
Invoke-RestMethod -Uri "http://localhost:9090/api/v1/query?query=$query" | ConvertTo-Json -Depth 10
```

---

## 문제 해결

### Alertmanager가 시작되지 않음

**증상**: `alertmanager.exe` 실행 시 오류 발생

**해결 방법**:

```powershell
# 1. 설정 파일 유효성 검사
cd C:\prometheus\alertmanager
.\amtool.exe check-config alertmanager.yml

# 2. 로그 확인
.\alertmanager.exe --config.file=alertmanager.yml --log.level=debug

# 3. 포트 충돌 확인
Get-NetTCPConnection -LocalPort 9093 -ErrorAction SilentlyContinue
```

### Slack 알림이 전송되지 않음

**증상**: Alert가 firing 상태지만 Slack에 메시지 없음

**해결 방법**:

```powershell
# 1. Webhook URL 확인
$env:SLACK_WEBHOOK_URL

# 2. 수동 테스트
$body = @{
    text = "Test notification from Lumen Gateway"
} | ConvertTo-Json

Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL `
                  -Method Post `
                  -Body $body `
                  -ContentType "application/json"

# 3. Alertmanager 로그 확인
Get-Content "C:\prometheus\alertmanager\alertmanager.log" -Tail 50
```

### Alert Rules가 로드되지 않음

**증상**: Prometheus UI에서 Rules 표시 안 됨

**해결 방법**:

```powershell
# 1. YAML 문법 검사
cd C:\prometheus
.\promtool.exe check rules rules\prometheus_rules.yml

# 2. Prometheus 설정 검사
.\promtool.exe check config prometheus.yml

# 3. Prometheus 재시작
Get-Process prometheus | Stop-Process -Force
Start-Process -FilePath ".\prometheus.exe" -ArgumentList "--config.file=prometheus.yml"
```

### Email 알림이 전송되지 않음

**증상**: Slack은 작동하지만 Email 미수신

**해결 방법**:

```powershell
# 1. SMTP 설정 확인
# alertmanager.yml의 global.smtp_* 설정 검토

# 2. App Password 확인 (Gmail)
$env:SMTP_PASSWORD

# 3. SMTP 연결 테스트
Test-NetConnection -ComputerName smtp.gmail.com -Port 587

# 4. Alertmanager 로그에서 SMTP 오류 확인
Get-Content "C:\prometheus\alertmanager\alertmanager.log" | Select-String "smtp"
```

### Alert가 계속 firing 상태

**증상**: 문제 해결 후에도 alert 계속 발화

**해결 방법**:

```powershell
# 1. Alert 상태 확인
Invoke-RestMethod -Uri "http://localhost:9093/api/v2/alerts" | ConvertTo-Json -Depth 10

# 2. Silence 설정 (일시적 음소거)
Start-Process "http://localhost:9093/#/silences"

# 3. Alert 수동 삭제 (최후 수단)
Invoke-RestMethod -Uri "http://localhost:9093/api/v2/alerts" -Method Delete
```

---

## 다음 단계

1. ✅ **Alertmanager 설치 및 실행**
2. ✅ **Prometheus 연동 완료**
3. ✅ **Slack 통합 완료**
4. ⏳ **Windows Service 등록** (자동 시작)
5. ⏳ **Grafana 대시보드에 Alerts 추가**
6. ⏳ **On-call rotation 설정** (PagerDuty/Opsgenie 연동)

**다음 작업**:
- Windows Task Scheduler로 Alertmanager 자동 시작
- Grafana에서 Alert 상태 시각화
- Runbook 작성 및 팀 공유

---

**작성일**: 2025-10-24  
**문서 버전**: 1.0  
**관련 파일**:
- `gateway/alerts/prometheus_rules.yml`
- `gateway/alerts/alertmanager.yml`
