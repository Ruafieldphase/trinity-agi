#Requires -Version 5.1
<#
.SYNOPSIS
    Register or unregister scheduled task for BQI Phase 6 (Persona Learning).

.DESCRIPTION
    This script manages Windows Scheduled Task for automatic BQI Phase 6 execution.
    Phase 6: Binoche Persona Learning (Task Mining, Decision Learning, Pattern Recognition, Rule Automation)

.PARAMETER Register
    Register the scheduled task.

.PARAMETER Unregister
    Unregister the scheduled task.

.PARAMETER Time
    Time to run the task (default: 03:05 - after Phase 4 at 03:00).

.PARAMETER TaskName
    Name of the scheduled task (default: BQIPhase6PersonaLearner).

.EXAMPLE
    .\register_bqi_phase6_scheduled_task.ps1 -Register
    .\register_bqi_phase6_scheduled_task.ps1 -Register -Time "03:05"
    .\register_bqi_phase6_scheduled_task.ps1 -Unregister

.NOTES
    Phase 6 runs after Phase 4 (03:00) to leverage fresh feedback predictions.
#>

[CmdletBinding()]
param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "03:05",
    [string]$TaskName = "BQIPhase6PersonaLearner",
    [switch]$WakeFromSleep  # Optional: Wake computer from sleep (requires admin)
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$runnerScript = Join-Path $scriptDir "run_bqi_learner.ps1"

# Ensure runner script exists
if (-not (Test-Path $runnerScript)) {
    Write-Error "Runner script not found: $runnerScript"
    exit 1
}

# Parse time
if ($Time -notmatch '^\d{2}:\d{2}$') {
    Write-Error "Invalid time format. Use HH:MM (e.g., 03:05)"
    exit 1
}

# Check if task exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

# Unregister
if ($Unregister) {
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Scheduled task unregistered: $TaskName" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN]  Task not found: $TaskName" -ForegroundColor Yellow
    }
    exit 0
}

# Register
if ($Register) {
    if ($existingTask) {
        Write-Host "[WARN]  Task already exists: $TaskName. Unregistering first..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Create action (PowerShell command to run the script)
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runnerScript`" -Phase 6 -VerboseLog"

    # Create trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time

    # Create settings
    if ($WakeFromSleep) {
        # Wake from sleep mode (requires admin/highest privileges)
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable:$false `
            -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
            -WakeToRun
        
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
        
        Write-Host "`n[WARN]  WakeFromSleep mode enabled - requires admin privileges" -ForegroundColor Yellow
    }
    else {
        # Standard mode: run when computer is awake
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable:$false `
            -ExecutionTimeLimit (New-TimeSpan -Hours 1)
        
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    }

    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "BQI Phase 6: Binoche Persona Learning (Task Mining, Decision Learning, Pattern Recognition, Rule Automation)" `
    | Out-Null

    Write-Host "`n[OK] Scheduled task registered successfully!" -ForegroundColor Green
    Write-Host "   Task Name: $TaskName" -ForegroundColor Cyan
    Write-Host "   Run Time:  $Time (daily)" -ForegroundColor Cyan
    Write-Host "   Script:    $runnerScript" -ForegroundColor Cyan
    Write-Host "   Phase:     6 (Persona Learning)" -ForegroundColor Cyan
    
    if ($WakeFromSleep) {
        Write-Host "`n🌙 Wake Mode: ENABLED" -ForegroundColor Magenta
        Write-Host "   [OK] Will wake computer from sleep to run" -ForegroundColor Green
        Write-Host "   [WARN]  Requires BIOS 'Wake Timers' enabled" -ForegroundColor Yellow
    }
    else {
        Write-Host "`n� Standard Mode: StartWhenAvailable" -ForegroundColor Yellow
        Write-Host "   • Task runs when computer is awake" -ForegroundColor Gray
        Write-Host "   • If missed, runs at next boot/wake" -ForegroundColor Gray
        Write-Host "   • No admin privileges required" -ForegroundColor Gray
        Write-Host "`n[INFO] To enable wake from sleep:" -ForegroundColor Cyan
        Write-Host "   .\register_bqi_phase6_scheduled_task.ps1 -Register -WakeFromSleep" -ForegroundColor Gray
        Write-Host "   (requires running PowerShell as Administrator)" -ForegroundColor DarkGray
    }
    
    Write-Host "`n📂 Output: $repoRoot\outputs\bqi_learner_last_run.txt" -ForegroundColor Gray

    # Show next run time
    try {
        $nextRun = (Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime
        Write-Host "`n⏰ Next run: $nextRun" -ForegroundColor Magenta
    }
    catch {
        Write-Host "`n[WARN]  Could not get next run time: $_" -ForegroundColor Yellow
    }

    exit 0
}

# Show status
if ($existingTask) {
    Write-Host "`n[METRICS] Scheduled Task Status: $TaskName" -ForegroundColor Cyan
    Write-Host "   State:     $($existingTask.State)" -ForegroundColor Gray
    
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "   Last Run:  $($info.LastRunTime)" -ForegroundColor Gray
    Write-Host "   Next Run:  $($info.NextRunTime)" -ForegroundColor Gray
    Write-Host "   Last Exit: $($info.LastTaskResult)" -ForegroundColor Gray
    
    Write-Host "`n[INFO] Usage:" -ForegroundColor Yellow
    Write-Host "   Register:   .\register_bqi_phase6_scheduled_task.ps1 -Register"
    Write-Host "   Unregister: .\register_bqi_phase6_scheduled_task.ps1 -Unregister"
}
else {
    Write-Host "`n[WARN]  Scheduled task not found: $TaskName" -ForegroundColor Yellow
    Write-Host "`n[INFO] Usage:" -ForegroundColor Yellow
    Write-Host "   Register:   .\register_bqi_phase6_scheduled_task.ps1 -Register [-Time HH:MM]"
    Write-Host "   Unregister: .\register_bqi_phase6_scheduled_task.ps1 -Unregister"
}

exit 0
