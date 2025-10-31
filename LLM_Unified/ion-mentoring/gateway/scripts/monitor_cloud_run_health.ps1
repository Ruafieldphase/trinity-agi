<#
.SYNOPSIS
    Cloud Run 서비스 헬스 모니터링 및 알림 필터링
    
.DESCRIPTION
    ION API Cloud Run 서비스의 실제 상태를 모니터링하고,
    불필요한 알림을 필터링하여 실제 문제만 보고합니다.
    
.PARAMETER CheckInterval
    헬스체크 간격 (초, 기본값: 60)
    
.PARAMETER AlertThreshold
    연속 실패 횟수 임계값 (기본값: 3)
    
.PARAMETER ServiceUrl
    Cloud Run 서비스 URL
    
.PARAMETER LogFile
    로그 파일 경로
    
.PARAMETER SendSlackAlert
    Slack 알림 전송 여부
    
.EXAMPLE
    .\monitor_cloud_run_health.ps1
    기본 설정으로 모니터링 시작
    
.EXAMPLE
    .\monitor_cloud_run_health.ps1 -CheckInterval 30 -AlertThreshold 2
    30초마다 체크, 2번 연속 실패 시 알림
#>

[CmdletBinding()]
param(
    [int]$CheckInterval = 60,
    [int]$AlertThreshold = 3,
    [string]$ServiceUrl = "https://ion-api-64076350717.us-central1.run.app",
    [string]$LogFile = "D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\cloud_run_health.log",
    [switch]$SendSlackAlert
)

$ErrorActionPreference = "Continue"

# 로그 디렉토리 확인
$logDir = Split-Path $LogFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

# 상태 추적 변수
$script:ConsecutiveFailures = 0
$script:LastAlertTime = $null
$script:TotalChecks = 0
$script:TotalFailures = 0
$script:StartTime = Get-Date

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # 콘솔 출력 (색상)
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Gray" }
    }
    Write-Host $logMessage -ForegroundColor $color
    
    # 파일 출력
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8
}

function Test-ServiceHealth {
    param(
        [string]$Url
    )
    
    try {
        $healthUrl = "$Url/health"
        $response = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.status -eq "healthy") {
            return @{
                Success       = $true
                Status        = $response.status
                Version       = $response.version
                PipelineReady = $response.pipeline_ready
                ResponseTime  = $null
            }
        }
        else {
            return @{
                Success = $false
                Status  = $response.status
                Error   = "Unhealthy status"
            }
        }
    }
    catch {
        return @{
            Success = $false
            Status  = "unreachable"
            Error   = $_.Exception.Message
        }
    }
}

function Send-SlackAlert {
    param(
        [string]$Message,
        [string]$Severity = "warning"
    )
    
    if (-not $SendSlackAlert -or -not $env:SLACK_WEBHOOK_URL) {
        return
    }
    
    $color = switch ($Severity) {
        "critical" { "#ff0000" }
        "warning" { "#ffa500" }
        "info" { "#00ff00" }
        default { "#808080" }
    }
    
    $payload = @{
        text        = "[ALERT] Cloud Run Health Alert"
        attachments = @(
            @{
                color  = $color
                text   = $Message
                footer = "Lumen Gateway Monitor"
                ts     = [int][double]::Parse((Get-Date -UFormat %s))
            }
        )
    } | ConvertTo-Json -Depth 3
    
    try {
        Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL -Method POST -Body $payload -ContentType "application/json" | Out-Null
        Write-Log "Slack alert sent" "INFO"
    }
    catch {
        Write-Log "Failed to send Slack alert: $_" "WARNING"
    }
}

function Get-ServiceStatus {
    param(
        [string]$ProjectId = "naeda-genesis",
        [string]$ServiceName = "ion-api",
        [string]$Region = "us-central1"
    )
    
    try {
        $output = gcloud run services describe $ServiceName `
            --project=$ProjectId `
            --region=$Region `
            --format="value(status.conditions[0].status,status.latestReadyRevisionName)" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $parts = $output -split '\s+'
            return @{
                Success  = $true
                Ready    = ($parts[0] -eq "True")
                Revision = $parts[1]
            }
        }
        return @{ Success = $false }
    }
    catch {
        return @{ Success = $false }
    }
}

# 메인 모니터링 루프
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Cloud Run Health Monitor" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "Service URL:      $ServiceUrl" -ForegroundColor Yellow
Write-Host "Check Interval:   $CheckInterval seconds" -ForegroundColor Yellow
Write-Host "Alert Threshold:  $AlertThreshold consecutive failures" -ForegroundColor Yellow
Write-Host "Log File:         $LogFile" -ForegroundColor Yellow
Write-Host "Slack Alerts:     $($SendSlackAlert -and $env:SLACK_WEBHOOK_URL)" -ForegroundColor Yellow
Write-Host "`nPress Ctrl+C to stop...`n" -ForegroundColor Gray

Write-Log "Health monitoring started" "INFO"

while ($true) {
    $script:TotalChecks++
    
    # 헬스체크 실행
    $healthResult = Test-ServiceHealth -Url $ServiceUrl
    
    if ($healthResult.Success) {
        $script:ConsecutiveFailures = 0
        
        # Cloud Run 서비스 상태도 확인
        $serviceStatus = Get-ServiceStatus
        $readyStatus = if ($serviceStatus.Ready) { "[OK]" } else { "[WARN]" }
        
        Write-Log "Service healthy - Version: $($healthResult.Version) | Pipeline: $($healthResult.PipelineReady) | Revision: $($serviceStatus.Revision) $readyStatus" "SUCCESS"
        
        # 통계 출력 (10번마다)
        if ($script:TotalChecks % 10 -eq 0) {
            $uptime = (Get-Date) - $script:StartTime
            $successRate = [math]::Round((($script:TotalChecks - $script:TotalFailures) / $script:TotalChecks * 100), 2)
            Write-Log "Stats - Checks: $($script:TotalChecks) | Success Rate: $successRate% | Uptime: $($uptime.ToString('hh\:mm\:ss'))" "INFO"
        }
    }
    else {
        $script:ConsecutiveFailures++
        $script:TotalFailures++
        
        Write-Log "Service check failed ($($script:ConsecutiveFailures)/$AlertThreshold) - Status: $($healthResult.Status) | Error: $($healthResult.Error)" "ERROR"
        
        # 임계값 도달 시 알림
        if ($script:ConsecutiveFailures -ge $AlertThreshold) {
            $now = Get-Date
            $timeSinceLastAlert = if ($script:LastAlertTime) { ($now - $script:LastAlertTime).TotalMinutes } else { 999 }
            
            # 5분 이내에는 중복 알림 방지
            if ($timeSinceLastAlert -gt 5) {
                $alertMessage = @"
[ALERT] ION API Health Alert

Service: $ServiceUrl
Status: $($healthResult.Status)
Consecutive Failures: $($script:ConsecutiveFailures)
Error: $($healthResult.Error)
Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

Total Checks: $($script:TotalChecks)
Total Failures: $($script:TotalFailures)
Success Rate: $([math]::Round((($script:TotalChecks - $script:TotalFailures) / $script:TotalChecks * 100), 2))%
"@
                
                Write-Log "ALERT TRIGGERED - Sending notifications" "ERROR"
                Send-SlackAlert -Message $alertMessage -Severity "critical"
                
                $script:LastAlertTime = $now
            }
            else {
                Write-Log "Alert suppressed (last alert was $([math]::Round($timeSinceLastAlert, 1)) minutes ago)" "WARNING"
            }
        }
    }
    
    Start-Sleep -Seconds $CheckInterval
}
