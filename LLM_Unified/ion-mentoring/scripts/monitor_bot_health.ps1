#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 봇의 상태를 모니터링하고 자동으로 재시작합니다.

.DESCRIPTION
    주기적으로 봇의 헬스를 체크하고, 응답이 없으면 자동으로 재시작합니다.
    Slack으로 알림을 보낼 수도 있습니다.

.PARAMETER IntervalSeconds
    헬스 체크 주기 (기본값: 60초)

.PARAMETER MaxFailures
    재시작 전 허용할 연속 실패 횟수 (기본값: 3)

.PARAMETER SendSlackAlert
    Slack으로 알림을 보냅니다.

.PARAMETER DurationMinutes
    모니터링 지속 시간 (0 = 무한, 기본값: 0)

.EXAMPLE
    .\monitor_bot_health.ps1
    # 기본 설정으로 무한 모니터링

.EXAMPLE
    .\monitor_bot_health.ps1 -IntervalSeconds 30 -SendSlackAlert
    # 30초마다 체크, Slack 알림 활성화

.EXAMPLE
    .\monitor_bot_health.ps1 -DurationMinutes 1440
    # 24시간 동안 모니터링
#>

[CmdletBinding()]
param(
    [int]$IntervalSeconds = 60,
    [int]$MaxFailures = 3,
    [switch]$SendSlackAlert,
    [int]$DurationMinutes = 0
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUTPUTS_DIR = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\outputs"
$STATE_FILE = Join-Path $OUTPUTS_DIR "gitco_bot_state.json"
$START_SCRIPT = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\scripts\start_gitco_bot.ps1"
$HEALTH_LOG = Join-Path $OUTPUTS_DIR "logs\health_monitor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# 로그 디렉토리 생성
$logDir = Split-Path $HEALTH_LOG
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage -ForegroundColor White }
    }
    
    Add-Content -Path $HEALTH_LOG -Value $logMessage
}

function Send-SlackAlert {
    param(
        [string]$Message,
        [string]$Emoji = "[ALERT]"
    )
    
    if (-not $SendSlackAlert) {
        return
    }
    
    try {
        $slackToken = [Environment]::GetEnvironmentVariable("SLACK_BOT_TOKEN", "User")
        if ([string]::IsNullOrEmpty($slackToken)) {
            Write-Log "Slack 토큰이 설정되지 않았습니다." "WARN"
            return
        }
        
        # 채널 ID는 환경 변수나 설정 파일에서 읽어와야 합니다
        $channelId = [Environment]::GetEnvironmentVariable("SLACK_ALERT_CHANNEL", "User")
        if ([string]::IsNullOrEmpty($channelId)) {
            Write-Log "Slack 알림 채널이 설정되지 않았습니다." "WARN"
            return
        }
        
        $body = @{
            channel = $channelId
            text    = "$Emoji $Message"
        } | ConvertTo-Json
        
        $headers = @{
            "Authorization" = "Bearer $slackToken"
            "Content-Type"  = "application/json"
        }
        
        Invoke-RestMethod -Uri "https://slack.com/api/chat.postMessage" -Method Post -Headers $headers -Body $body | Out-Null
        Write-Log "Slack 알림 전송: $Message" "INFO"
        
    }
    catch {
        Write-Log "Slack 알림 실패: $($_.Exception.Message)" "WARN"
    }
}

function Test-BotHealth {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

function Restart-Bot {
    Write-Log "[SYNC] 봇 재시작 중..." "WARN"
    Send-SlackAlert "깃코 봇이 응답하지 않아 재시작합니다..." "[WARN]"
    
    try {
        & $START_SCRIPT -KillExisting
        Start-Sleep -Seconds 10
        
        if (Test-BotHealth) {
            Write-Log "[OK] 봇 재시작 성공" "SUCCESS"
            Send-SlackAlert "깃코 봇이 정상적으로 재시작되었습니다." "[OK]"
            return $true
        }
        else {
            Write-Log "[ERROR] 봇 재시작 실패 - 헬스 체크 실패" "ERROR"
            Send-SlackAlert "깃코 봇 재시작 후에도 응답이 없습니다!" "[ERROR]"
            return $false
        }
    }
    catch {
        Write-Log "[ERROR] 봇 재시작 중 오류: $($_.Exception.Message)" "ERROR"
        Send-SlackAlert "깃코 봇 재시작 실패: $($_.Exception.Message)" "[ERROR]"
        return $false
    }
}

# =============================================================================
# Main
# =============================================================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           깃코 봇 - 상태 모니터링 시작                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Log "[SEARCH] 모니터링 시작" "INFO"
Write-Log "  • 체크 주기: $IntervalSeconds 초" "INFO"
Write-Log "  • 최대 실패 허용: $MaxFailures 회" "INFO"
Write-Log "  • Slack 알림: $(if($SendSlackAlert){'활성화'}else{'비활성화'})" "INFO"
if ($DurationMinutes -gt 0) {
    Write-Log "  • 모니터링 시간: $DurationMinutes 분" "INFO"
}
else {
    Write-Log "  • 모니터링 시간: 무한 (Ctrl+C로 종료)" "INFO"
}
Write-Log "  • 로그 파일: $HEALTH_LOG" "INFO"

$startTime = Get-Date
$consecutiveFailures = 0
$totalChecks = 0
$totalFailures = 0
$totalRestarts = 0

try {
    while ($true) {
        $currentTime = Get-Date
        
        # 지속 시간 체크
        if ($DurationMinutes -gt 0) {
            $elapsed = ($currentTime - $startTime).TotalMinutes
            if ($elapsed -ge $DurationMinutes) {
                Write-Log "⏰ 모니터링 시간 종료 ($DurationMinutes 분)" "INFO"
                break
            }
        }
        
        $totalChecks++
        
        # 헬스 체크
        if (Test-BotHealth) {
            if ($consecutiveFailures -gt 0) {
                Write-Log "[OK] 봇 복구됨 (이전 실패: $consecutiveFailures 회)" "SUCCESS"
                $consecutiveFailures = 0
            }
            else {
                Write-Log "[OK] 봇 정상 (체크: $totalChecks, 실패: $totalFailures, 재시작: $totalRestarts)" "INFO"
            }
        }
        else {
            $consecutiveFailures++
            $totalFailures++
            Write-Log "[ERROR] 헬스 체크 실패 ($consecutiveFailures/$MaxFailures)" "ERROR"
            
            if ($consecutiveFailures -ge $MaxFailures) {
                Write-Log "[ALERT] 최대 실패 횟수 도달 - 재시작 시도" "ERROR"
                
                if (Restart-Bot) {
                    $consecutiveFailures = 0
                    $totalRestarts++
                }
                else {
                    Write-Log "[WARN]  재시작 실패 - 다음 체크에서 재시도" "WARN"
                }
            }
        }
        
        # 대기
        Start-Sleep -Seconds $IntervalSeconds
    }
    
}
catch {
    if ($_.Exception.Message -notmatch "pipeline has been stopped") {
        Write-Log "모니터링 중 오류: $($_.Exception.Message)" "ERROR"
    }
}
finally {
    Write-Log "[METRICS] 모니터링 종료 통계" "INFO"
    Write-Log "  • 총 체크: $totalChecks 회" "INFO"
    Write-Log "  • 총 실패: $totalFailures 회" "INFO"
    Write-Log "  • 총 재시작: $totalRestarts 회" "INFO"
    $uptime = (Get-Date) - $startTime
    Write-Log "  • 모니터링 시간: $([math]::Floor($uptime.TotalHours))시간 $($uptime.Minutes)분" "INFO"
    
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                  모니터링 종료                            ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
}
