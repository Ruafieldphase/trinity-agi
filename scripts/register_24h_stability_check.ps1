# 24?úÍ∞Ñ ?àÏ†ï??Ï≤¥ÌÅ¨ ?êÎèô???§Ï?Ï§?# Windows Task Scheduler ?±Î°ù ?§ÌÅ¨Î¶ΩÌä∏

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'

$taskName = "AGI_24H_Stability_Check"
$scriptPath = "C:\workspace\agi\scripts\monitor_stability_24h.ps1"
$logPath = "C:\workspace\agi\outputs\scheduled_stability_check.log"

# 2025-10-28 17:47 ?¥ÌõÑ ?§Ìñâ
$triggerTime = Get-Date "2025-10-28 17:47:00"

if ($Status) {
    Write-Host "=== Task Status ===" -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Task Name: $($task.TaskName)" -ForegroundColor Green
        Write-Host "State: $($task.State)" -ForegroundColor Green
        Write-Host "Last Run: $($task.LastRunTime)" -ForegroundColor Green
        Write-Host "Next Run: $($task.NextRunTime)" -ForegroundColor Green
        
        $trigger = $task.Triggers[0]
        Write-Host "Trigger: $($trigger.StartBoundary)" -ForegroundColor Yellow
    }
    else {
        Write-Host "Task '$taskName' not found." -ForegroundColor Red
        Write-Host "Run with -Register to create the task." -ForegroundColor Yellow
    }
    exit 0
}

if ($Unregister) {
    Write-Host "Unregistering scheduled task '$taskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[OK] Task unregistered successfully." -ForegroundColor Green
    exit 0
}

if ($Register) {
    Write-Host "Registering scheduled task '$taskName'..." -ForegroundColor Cyan
    
    # Unregister if exists
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Task Action: Run PowerShell script
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action Check >> `"$logPath`" 2>&1"
    
    # Task Trigger: One-time at specified date/time
    $trigger = New-ScheduledTaskTrigger -Once -At $triggerTime
    
    # Task Principal: Run with highest privileges
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Highest
    
    # Task Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -DontStopOnIdleEnd
    
    # Register Task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "AGI 24?úÍ∞Ñ ?àÏ†ï??Ï≤¥ÌÅ¨ (2025-10-27 17:47 ??2025-10-28 17:47)" `
    | Out-Null
    
    Write-Host "[OK] Task registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== Task Details ===" -ForegroundColor Cyan
    Write-Host "Task Name: $taskName"
    Write-Host "Trigger: $triggerTime"
    Write-Host "Script: $scriptPath"
    Write-Host "Log: $logPath"
    Write-Host ""
    Write-Host "Check status: .\scripts\register_24h_stability_check.ps1 -Status" -ForegroundColor Yellow
    exit 0
}

Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  -Register    Register the scheduled task" -ForegroundColor Gray
Write-Host "  -Unregister  Remove the scheduled task" -ForegroundColor Gray
Write-Host "  -Status      Show task status" -ForegroundColor Gray
Write-Host ""
Write-Host "Example:" -ForegroundColor Cyan
Write-Host "  .\scripts\register_24h_stability_check.ps1 -Register" -ForegroundColor Gray
