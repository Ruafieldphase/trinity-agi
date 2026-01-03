#Requires -Version 5.1
<#
.SYNOPSIS
    시스템 메트릭 수집을 자동 스케줄 태스크로 등록

.DESCRIPTION
    - 5분마다 메트릭 수집 (collect_system_metrics.ps1)
    - 시스템 시작 시 자동 실행
    - 백그라운드 작동

.PARAMETER Register
    태스크 등록

.PARAMETER Unregister
    태스크 제거

.PARAMETER IntervalMinutes
    실행 간격 (기본: 5분)

.EXAMPLE
    .\register_metrics_collector.ps1 -Register
    .\register_metrics_collector.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [int]$IntervalMinutes = 5,
    [string]$TaskName = "AGI_MetricsCollector"
)

$ErrorActionPreference = 'Stop'

try {
    if ($Unregister) {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "Task '$TaskName' unregistered." -ForegroundColor Green
        }
        else {
            Write-Host "Task '$TaskName' not found." -ForegroundColor Yellow
        }
        exit 0
    }

    if ($Register) {
        # 기존 태스크 제거
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "Existing task removed." -ForegroundColor Yellow
        }

        $scriptPath = "$PSScriptRoot\collect_system_metrics.ps1"
        if (-not (Test-Path $scriptPath)) {
            Write-Host "Script not found: $scriptPath" -ForegroundColor Red
            exit 1
        }

        # 액션: PowerShell 스크립트 실행
        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

        # 트리거: 매 N분마다 반복 (최대 30일)
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 30)

        # 설정: 백그라운드 실행, 로그온 여부 무관
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable:$false `
            -DontStopOnIdleEnd `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

        # 주체: 현재 사용자
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U

        # 태스크 등록
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Collect AGI system metrics every $IntervalMinutes minutes" `
            -Force | Out-Null

        Write-Host "Task '$TaskName' registered successfully!" -ForegroundColor Green
        Write-Host "  Interval: Every $IntervalMinutes minutes" -ForegroundColor Cyan
        Write-Host "  Script: $scriptPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Check status:" -ForegroundColor Yellow
        Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
        
        exit 0
    }

    # Status
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Task '$TaskName' is registered." -ForegroundColor Green
        Write-Host "  State: $($task.State)" -ForegroundColor Cyan
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($info) {
            Write-Host "  Last Run: $($info.LastRunTime)" -ForegroundColor Cyan
            Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
            Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "Task '$TaskName' not found." -ForegroundColor Yellow
        Write-Host "Register with: .\register_metrics_collector.ps1 -Register" -ForegroundColor White
    }

    exit 0

}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}