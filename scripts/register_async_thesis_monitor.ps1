# Async Thesis 모니터링 자동화 스케줄러 등록
# 1시간마다 헬스 체크, 알림 조건 시 알림

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 60
)

$ErrorActionPreference = "Stop"
$TaskName = "AsyncThesisHealthMonitor"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptRoot
$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$MonitorScript = Join-Path $ScriptRoot "monitor_async_thesis_health.py"

function Register-Monitor {
    Write-Host "Registering Async Thesis Health Monitor..." -ForegroundColor Cyan
    
    # 기존 작업 제거
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 액션 생성
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"& '$PythonExe' '$MonitorScript' --hours 1 --json '$WorkspaceRoot\outputs\async_thesis_health_latest.json' --alert`""
    
    # 트리거 생성 (1시간마다, 무한 반복)
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
    
    # 설정
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # 등록
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Async Thesis 24/7 health monitoring (every $IntervalMinutes min)" `
        -User $env:USERNAME `
        | Out-Null
    
    Write-Host "✓ Monitor registered: $TaskName" -ForegroundColor Green
    Write-Host "  Interval: Every $IntervalMinutes minutes" -ForegroundColor Cyan
    Write-Host "  Script: $MonitorScript" -ForegroundColor Cyan
    
    # 즉시 실행
    Write-Host "`nRunning initial check..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host "✓ Task running" -ForegroundColor Green
    Write-Host "  State: $($task.State)" -ForegroundColor Cyan
    Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Cyan
    Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Cyan
}

function Unregister-Monitor {
    Write-Host "Unregistering Async Thesis Health Monitor..." -ForegroundColor Cyan
    
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ Monitor unregistered" -ForegroundColor Green
    } else {
        Write-Host "  Task not found" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "Async Thesis Health Monitor Status" -ForegroundColor Cyan
    Write-Host ("="*70) -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if (-not $task) {
        Write-Host "❌ Monitor NOT registered" -ForegroundColor Red
        Write-Host "`nTo register:" -ForegroundColor Yellow
        Write-Host "  .\register_async_thesis_monitor.ps1 -Register"
        return
    }
    
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host "✓ Monitor registered" -ForegroundColor Green
    Write-Host "  State: $($task.State)" -ForegroundColor Cyan
    Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Cyan
    Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Cyan
    Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
    
    # 최신 리포트 확인
    $latestReport = Join-Path $WorkspaceRoot "outputs\async_thesis_health_latest.md"
    if (Test-Path $latestReport) {
        $reportAge = (Get-Date) - (Get-Item $latestReport).LastWriteTime
        Write-Host "`nLatest Report:" -ForegroundColor Cyan
        Write-Host "  Path: $latestReport" -ForegroundColor Cyan
        Write-Host "  Age: $([math]::Round($reportAge.TotalMinutes, 1)) minutes" -ForegroundColor Cyan
        
        # Status 추출
        $content = Get-Content $latestReport -Raw
        if ($content -match '## Status: (.+)') {
            Write-Host "  Status: $($matches[1])" -ForegroundColor Cyan
        }
        if ($content -match '\*\*Improvement\*\*: (.+)') {
            Write-Host "  Improvement: $($matches[1])" -ForegroundColor Cyan
        }
    }
    
    Write-Host "`nCommands:" -ForegroundColor Yellow
    Write-Host "  Register:   .\register_async_thesis_monitor.ps1 -Register"
    Write-Host "  Unregister: .\register_async_thesis_monitor.ps1 -Unregister"
    Write-Host "  Status:     .\register_async_thesis_monitor.ps1 -Status"
    Write-Host "  View logs:  code $WorkspaceRoot\outputs\async_thesis_health_latest.md"
}

# Main
if ($Register) {
    Register-Monitor
} elseif ($Unregister) {
    Unregister-Monitor
} elseif ($Status) {
    Show-Status
} else {
    Show-Status
}
