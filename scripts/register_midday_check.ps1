#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Register/unregister mid-day milestone check task

.PARAMETER Register
    Register the scheduled task

.PARAMETER Unregister
    Unregister the scheduled task

.PARAMETER Status
    Show task status
#>
param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [switch]$NoAdmin
)

$ErrorActionPreference = 'Stop'
$taskName = "AGI_MidDay_Milestone_Check"

if ($Unregister) {
    Write-Host "`n🗑️ Unregistering task: $taskName" -ForegroundColor Yellow
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "✅ Task unregistered" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ Task not found" -ForegroundColor Yellow
    }
    exit 0
}

if ($Status -or (-not $Register)) {
    Write-Host "`n📋 Task Status: $taskName" -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
        $info = Get-ScheduledTaskInfo -TaskName $taskName
        Write-Host "  Last run: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Next run: $($info.NextRunTime)" -ForegroundColor Gray
        Write-Host "  Last result: $($info.LastTaskResult)" -ForegroundColor Gray
    }
    else {
        Write-Host "  ❌ Task not registered" -ForegroundColor Red
        Write-Host "`n  To register: .\register_midday_check.ps1 -Register" -ForegroundColor Yellow
    }
    exit 0
}

# Register task
Write-Host "`n📝 Registering mid-day milestone check..." -ForegroundColor Cyan

# 기존 작업 삭제
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# 작업 생성
$scriptPath = "C:\workspace\agi\scripts\midday_milestone_check.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-NoProfile -ExecutionPolicy Bypass -File "$scriptPath"
"@

# 12:00 KST에 매일 실행 (오늘만)
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 기본 Principal: 관리자 권한 요구 (가능 시)
$principalHigh = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
# 대안 Principal: 일반 권한 (관리자 권한 없을 때)
$principalUser = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

try {
    if ($NoAdmin) {
        Write-Host "  Registering with LeastPrivilege (-NoAdmin)" -ForegroundColor Yellow
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalUser -Description "Phase 10.1 mid-day milestone check (12:00 KST)" | Out-Null
    }
    else {
        Write-Host "  Attempting registration with RunLevel=Highest" -ForegroundColor Gray
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalHigh -Description "Phase 10.1 mid-day milestone check (12:00 KST)" | Out-Null
    }
}
catch {
    Write-Host "  ⚠️ Registration with RunLevel=Highest failed or access denied. Retrying with LeastPrivilege..." -ForegroundColor Yellow
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalUser -Description "Phase 10.1 mid-day milestone check (12:00 KST)" | Out-Null
}

Write-Host "✅ Task registered successfully!" -ForegroundColor Green
Write-Host "`n📅 Schedule:" -ForegroundColor Cyan
Write-Host "  Time: 12:00 KST daily" -ForegroundColor White
Write-Host "  Script: midday_milestone_check.ps1" -ForegroundColor Gray
Write-Host "`n💡 Tip: Check status with .\register_midday_check.ps1 -Status" -ForegroundColor Yellow
