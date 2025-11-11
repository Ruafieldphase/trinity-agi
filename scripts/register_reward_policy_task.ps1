#!/usr/bin/env pwsh
<#
.SYNOPSIS
    보상 기반 정책 업데이트 스케줄러 등록/해제
    
.DESCRIPTION
    보상 신호를 분석해 행동 정책을 자동으로 업데이트하는 태스크를 등록합니다.
    기저핵의 습관 강화 기능을 모사합니다.
    
.PARAMETER Register
    태스크 등록 (기본값은 상태 확인)
    
.PARAMETER Unregister
    태스크 해제
    
.PARAMETER Time
    실행 시각 (기본: 04:00)
    
.PARAMETER UpdateInterval
    정책 업데이트 주기 (시간, 기본: 12)
    
.EXAMPLE
    .\register_reward_policy_task.ps1 -Register -Time "04:00"
    
.EXAMPLE
    .\register_reward_policy_task.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "04:00",
    [int]$UpdateInterval = 12
)

$ErrorActionPreference = "Stop"
$taskName = "AGI_RewardPolicyUpdate"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

function Show-TaskStatus {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($task) {
        Write-Host "✅ Reward Policy Update Task: REGISTERED" -ForegroundColor Green
        Write-Host "   Name: $taskName"
        Write-Host "   State: $($task.State)"
        Write-Host "   Next Run: $($task.Triggers[0].StartBoundary)"
        
        # 최근 실행 기록
        $info = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
        if ($info) {
            Write-Host "   Last Run: $($info.LastRunTime)"
            Write-Host "   Last Result: $($info.LastTaskResult)"
        }
    }
    else {
        Write-Host "❌ Reward Policy Update Task: NOT REGISTERED" -ForegroundColor Red
        Write-Host "   Use -Register to enable reward-based learning"
    }
}

# 상태 확인만 (기본)
if (-not $Register -and -not $Unregister) {
    Show-TaskStatus
    exit 0
}

# 해제
if ($Unregister) {
    Write-Host "🗑️ Unregistering Reward Policy Update Task..." -ForegroundColor Yellow
    
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    Write-Host "✅ Task unregistered" -ForegroundColor Green
    exit 0
}

# 등록
if ($Register) {
    Write-Host "📋 Registering Reward Policy Update Task..." -ForegroundColor Cyan
    Write-Host "   Schedule: Daily at $Time"
    Write-Host "   Update Interval: $UpdateInterval hours"
    
    # 스크립트 경로
    $scriptPath = Join-Path $workspaceRoot "scripts\update_reward_policy.ps1"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Script not found: $scriptPath" -ForegroundColor Red
        exit 1
    }
    
    # 기존 태스크 제거
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # 트리거 생성 (매일 지정 시각)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # 액션 생성
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -UpdateInterval $UpdateInterval"
    
    # 설정
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # 태스크 등록
    Register-ScheduledTask `
        -TaskName $taskName `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -Description "Updates reward-based behavior policy (basal ganglia-like habit learning)" `
        -User $env:USERNAME `
        -RunLevel Highest | Out-Null
    
    Write-Host "✅ Task registered successfully" -ForegroundColor Green
    Write-Host ""
    Show-TaskStatus
}
