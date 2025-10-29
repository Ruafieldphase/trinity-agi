# Weekly Batch Validation - Automated Task Scheduler
# =================================================
# 
# Purpose: Run comprehensive AGI batch validation every Sunday at midnight
# 
# This script sets up a scheduled task to execute full batch validation
# across all complexity levels (Simple, Medium, Complex) to monitor
# system performance trends over time.

param(
    [switch]$Create,
    [switch]$Delete,
    [switch]$Status,
    [switch]$RunNow
)

$TaskName = "AGI_Weekly_FullBatch_Validation"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptRoot
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    $PythonExe = "py"
}

# Validation script path
$ValidationScript = Join-Path $RootDir "scripts\large_batch_validation.py"
$OutputDir = Join-Path $RootDir "outputs"
$LogDir = Join-Path $OutputDir "scheduled_logs"

# Create log directory if not exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Show-Status {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($task) {
        Write-Host "[OK] Scheduled Task Status: ACTIVE" -ForegroundColor Green
        Write-Host ""
        Write-Host "Task Name    : $($task.TaskName)"
        Write-Host "State        : $($task.State)"
        Write-Host "Last Run     : $($task.LastRunTime)"
        Write-Host "Next Run     : $($task.NextRunTime)"
        Write-Host "Last Result  : $($task.LastTaskResult)"
        Write-Host ""
        Write-Host "Triggers:"
        foreach ($trigger in $task.Triggers) {
            Write-Host "  - $($trigger.DaysOfWeek) at $($trigger.StartBoundary.ToString('HH:mm'))"
        }
    }
    else {
        Write-Host "[ERROR] Scheduled Task: NOT FOUND" -ForegroundColor Red
        Write-Host ""
        Write-Host "Run with -Create to set up the scheduled task."
    }
}

function Create-ScheduledTask {
    # Check if task already exists
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "[WARN] Task already exists. Delete first with -Delete" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Creating scheduled task: $TaskName" -ForegroundColor Cyan
    
    # Action: Run full batch validation
    $LogFile = Join-Path $LogDir "batch_validation_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    $ActionArgs = "-NoProfile -ExecutionPolicy Bypass -Command `"cd '$RootDir'; $PythonExe '$ValidationScript' *> '$LogFile'`""
    
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $ActionArgs
    
    # Trigger: Every Sunday at 00:00
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "00:00"
    
    # Settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    
    # Principal (run as current user)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
    
    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Weekly AGI batch validation across all complexity levels (Simple, Medium, Complex). Monitors system performance trends." | Out-Null
    
    Write-Host "[OK] Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule: Every Sunday at 00:00"
    Write-Host "Script  : $ValidationScript"
    Write-Host "Logs    : $LogDir"
    Write-Host ""
    Write-Host "Use -Status to check task status"
    Write-Host "Use -RunNow to execute immediately"
}

function Delete-ScheduledTask {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Scheduled task deleted: $TaskName" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Task not found: $TaskName" -ForegroundColor Yellow
    }
}

function Run-TaskNow {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if (-not $task) {
        Write-Host "[ERROR] Task not found. Create it first with -Create" -ForegroundColor Red
        return
    }
    
    Write-Host "▶️ Running task immediately: $TaskName" -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "[OK] Task started. Check logs in: $LogDir" -ForegroundColor Green
}

# Main logic
if ($Create) {
    Create-ScheduledTask
}
elseif ($Delete) {
    Delete-ScheduledTask
}
elseif ($RunNow) {
    Run-TaskNow
}
elseif ($Status) {
    Show-Status
}
else {
    Write-Host "AGI Weekly Batch Validation Scheduler" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  -Create   : Create scheduled task (every Sunday 00:00)"
    Write-Host "  -Delete   : Remove scheduled task"
    Write-Host "  -Status   : Show task status and schedule"
    Write-Host "  -RunNow   : Execute task immediately"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\setup_weekly_batch.ps1 -Create"
    Write-Host "  .\setup_weekly_batch.ps1 -Status"
    Write-Host ""
}
