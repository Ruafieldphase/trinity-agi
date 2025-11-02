# Register Dashboard Auto-Update Task
# Automatically regenerates enhanced dashboard every 5 minutes
# Part of Phase 3+ Real-Time Monitoring Enhancement

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 5
)

$ErrorActionPreference = "Stop"

$taskName = "AGI_Dashboard_AutoUpdate"
$scriptPath = "$PSScriptRoot\generate_enhanced_dashboard.ps1"

function Test-AdminRights {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if ($Unregister) {
    if (-not (Test-AdminRights)) {
        Write-Host "❌ Admin rights required to unregister scheduled task" -ForegroundColor Red
        exit 1
    }
    
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "✓ Task '$taskName' unregistered" -ForegroundColor Green
    } else {
        Write-Host "⚠ Task '$taskName' not found" -ForegroundColor Yellow
    }
    exit 0
}

if ($Status -or (-not $Register -and -not $Unregister)) {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "✓ Task '$taskName' is registered" -ForegroundColor Green
        Write-Host "  State: $($existing.State)"
        Write-Host "  Last Run: $($existing.LastRunTime)"
        Write-Host "  Next Run: $($existing.NextRunTime)"
        Write-Host "  Trigger: Every $IntervalMinutes minutes (repeating indefinitely)"
    } else {
        Write-Host "⚠ Task '$taskName' not registered" -ForegroundColor Yellow
        Write-Host "  Run with -Register to set up auto-update"
    }
    exit 0
}

if ($Register) {
    if (-not (Test-AdminRights)) {
        Write-Host "❌ Admin rights required to register scheduled task" -ForegroundColor Red
        Write-Host "  Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "📋 Registering dashboard auto-update task..." -ForegroundColor Cyan
    
    # Unregister if exists
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
    
    # Create trigger (repeating every N minutes, indefinitely)
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -MultipleInstances IgnoreNew
    
    # Register task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Auto-regenerates AGI system dashboard every $IntervalMinutes minutes" `
        -User $env:USERNAME `
        -RunLevel Limited
    
    Write-Host "✓ Task registered successfully" -ForegroundColor Green
    Write-Host "  Task Name: $taskName"
    Write-Host "  Interval: Every $IntervalMinutes minutes"
    Write-Host "  Script: $scriptPath"
    Write-Host "  User: $env:USERNAME (non-admin)"
    Write-Host ""
    Write-Host "  Dashboard will be updated automatically in the background" -ForegroundColor Cyan
    Write-Host "  Check status with: .\register_dashboard_autoupdate.ps1 -Status" -ForegroundColor Cyan
    
    exit 0
}
