#!/usr/bin/env powershell
<#
.SYNOPSIS
    Register/Unregister Windows Scheduled Task for Binoche Online Learner (Phase 6l).

.DESCRIPTION
    This script creates or removes a scheduled task that runs the Binoche Online Learner
    daily to update ensemble judge weights based on prediction accuracy.
    
    Default schedule: 03:20 AM daily (runs after Phase 6k monitoring at 03:15 AM)

.PARAMETER Register
    Register the scheduled task.

.PARAMETER Unregister
    Unregister the scheduled task.

.PARAMETER Time
    Time to run the task (default: 03:20 AM).

.PARAMETER TaskName
    Name of the scheduled task (default: BinocheOnlineLearner).

.PARAMETER WindowHours
    Time window for learning in hours (default: 24).

.PARAMETER LearningRate
    Learning rate for gradient descent (default: 0.01).

.EXAMPLE
    .\register_online_learner_task.ps1 -Register
    Register task with default settings (03:20 AM daily, 24h window, lr=0.01).

.EXAMPLE
    .\register_online_learner_task.ps1 -Register -Time "04:00" -WindowHours 48
    Register task at 4:00 AM with 48-hour window.

.EXAMPLE
    .\register_online_learner_task.ps1 -Unregister
    Remove the scheduled task.
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "03:20",
    [string]$TaskName = "BinocheOnlineLearner",
    [int]$WindowHours = 24,
    [double]$LearningRate = 0.01
)

$ErrorActionPreference = "Stop"

# Determine repo root
$RepoRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$ScriptPath = Join-Path $RepoRoot "fdo_agi_repo\scripts\rune\binoche_online_learner.py"
$VenvPython = Join-Path $RepoRoot "fdo_agi_repo\.venv\Scripts\python.exe"

if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

# Check if task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($Register) {
    Write-Host "🔧 Registering Binoche Online Learner Scheduled Task..." -ForegroundColor Cyan
    Write-Host "   Task Name: $TaskName"
    Write-Host "   Schedule: Daily at $Time"
    Write-Host "   Window: $WindowHours hours"
    Write-Host "   Learning Rate: $LearningRate"
    Write-Host ""

    # Determine Python executable
    if (Test-Path $VenvPython) {
        $PythonExe = $VenvPython
        Write-Host "✅ Using venv Python: $PythonExe" -ForegroundColor Green
    }
    else {
        $PythonExe = "python"
        Write-Host "⚠️ Using system Python (venv not found)" -ForegroundColor Yellow
    }

    # Build command
    $Arguments = "scripts\rune\binoche_online_learner.py --window-hours $WindowHours --learning-rate $LearningRate"
    
    # Task action
    $Action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument $Arguments `
        -WorkingDirectory (Join-Path $RepoRoot "fdo_agi_repo")

    # Task trigger (daily at specified time)
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time

    # Task settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

    # Principal (run whether user is logged on or not)
    $Principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType S4U `
        -RunLevel Highest

    # Register task
    if ($ExistingTask) {
        Write-Host "⚠️ Task already exists. Updating..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $Task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Binoche Online Learner (Phase 6l) - Updates ensemble judge weights daily based on prediction accuracy."

    Write-Host ""
    Write-Host "✅ Scheduled Task registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Task Details:" -ForegroundColor Cyan
    Write-Host "   Name: $($Task.TaskName)"
    Write-Host "   State: $($Task.State)"
    Write-Host "   Next Run: $(Get-ScheduledTaskInfo -TaskName $TaskName | Select-Object -ExpandProperty NextRunTime)"
    Write-Host ""
    Write-Host "💡 To manually trigger: Run-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "💡 To view logs: Check fdo_agi_repo\outputs\online_learning_log.jsonl" -ForegroundColor Gray
    Write-Host ""

}
elseif ($Unregister) {
    Write-Host "🗑️ Unregistering Binoche Online Learner Scheduled Task..." -ForegroundColor Cyan
    Write-Host "   Task Name: $TaskName"
    Write-Host ""

    if (-not $ExistingTask) {
        Write-Host "⚠️ Task '$TaskName' not found." -ForegroundColor Yellow
        exit 0
    }

    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ Task unregistered successfully!" -ForegroundColor Green
    Write-Host ""

}
else {
    # Show status
    Write-Host "📊 Binoche Online Learner Scheduled Task Status" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""

    if ($ExistingTask) {
        $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "✅ Task is registered" -ForegroundColor Green
        Write-Host "   Name: $($ExistingTask.TaskName)"
        Write-Host "   State: $($ExistingTask.State)"
        Write-Host "   Next Run: $($TaskInfo.NextRunTime)"
        Write-Host "   Last Run: $($TaskInfo.LastRunTime)"
        Write-Host "   Last Result: $($TaskInfo.LastTaskResult)"
        Write-Host ""
        Write-Host "💡 To unregister: .\register_online_learner_task.ps1 -Unregister" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Task is not registered" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 To register: .\register_online_learner_task.ps1 -Register" -ForegroundColor Gray
    }
    Write-Host ""
}
