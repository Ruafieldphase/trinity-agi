# Register Local LLM Monitoring as Windows Scheduled Task
# Provides 24/7 automated monitoring with optional auto-restart

param(
    [switch]$EnableAutoRestart,  # Enable automatic LLM restart
    [switch]$Unregister,         # Remove the scheduled task
    [switch]$Status,             # Show task status
    [int]$CheckIntervalMinutes = 5  # How often to check
)

$ErrorActionPreference = "Stop"

$taskName = "AGI_Local_LLM_Monitor"
$scriptPath = "$PSScriptRoot\auto_restart_local_llm.ps1"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Local LLM Monitor - Scheduled Task Registration" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Status check
if ($Status) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

    if ($task) {
        Write-Host "Task Status:" -ForegroundColor Cyan
        Write-Host "  Name: $($task.TaskName)" -ForegroundColor White
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq "Ready") { "Green" } else { "Yellow" })
        Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor White
        Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor White
        Write-Host ""

        $info = Get-ScheduledTaskInfo -TaskName $taskName
        Write-Host "Task Info:" -ForegroundColor Cyan
        Write-Host "  Last Result: $($info.LastTaskResult)" -ForegroundColor $(if ($info.LastTaskResult -eq 0) { "Green" } else { "Red" })
        Write-Host "  Number of Runs: $($info.NumberOfMissedRuns)" -ForegroundColor White
        Write-Host ""
    }
    else {
        Write-Host "Task '$taskName' is not registered" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Run without -Status to register the task" -ForegroundColor Gray
    }

    exit 0
}

# Unregister
if ($Unregister) {
    Write-Host "Unregistering task '$taskName'..." -ForegroundColor Yellow

    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "✅ Task unregistered successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Task not found or already unregistered" -ForegroundColor Red
    }

    Write-Host ""
    exit 0
}

# Register task
Write-Host "Registering task '$taskName'..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Error: Monitor script not found at $scriptPath" -ForegroundColor Red
    exit 1
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠️  Task already exists!" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to replace it? (y/N)"

    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Cancelled" -ForegroundColor Yellow
        exit 0
    }

    Write-Host ""
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Build arguments
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

if ($EnableAutoRestart) {
    $arguments += " -AutoRestart"
    Write-Host "⚠️  AUTO-RESTART ENABLED" -ForegroundColor Yellow
    Write-Host "LLM will be automatically restarted if offline" -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host "ℹ️  Auto-restart DISABLED" -ForegroundColor Cyan
    Write-Host "Monitor will only check and log, not restart" -ForegroundColor Gray
    Write-Host ""
}

# Create action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $arguments

# Create trigger (run every X minutes)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $CheckIntervalMinutes)

# Create settings
$settings = New-ScheduledTaskSettingsSet `
$settings.Hidden = $true
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -DontStopOnIdleEnd `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3

# Create principal (run with current user)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Limited

# Register task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Monitors Local LLM (LM Studio) health and optionally restarts on failure" `
        -ErrorAction Stop

    Write-Host "✅ Task registered successfully!" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "❌ Failed to register task: $_" -ForegroundColor Red
    exit 1
}

# Show summary
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Task Summary" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Name: $taskName" -ForegroundColor White
Write-Host "Check Interval: Every $CheckIntervalMinutes minutes" -ForegroundColor White
Write-Host "Auto-Restart: $(if ($EnableAutoRestart) { 'ENABLED' } else { 'DISABLED' })" -ForegroundColor $(if ($EnableAutoRestart) { "Yellow" } else { "Green" })
Write-Host "Log File: outputs\llm_health_monitor.log" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Check task status: .\scripts\register_llm_monitor_task.ps1 -Status" -ForegroundColor Gray
Write-Host "  2. View logs: Get-Content outputs\llm_health_monitor.log -Tail 20" -ForegroundColor Gray
Write-Host "  3. Unregister: .\scripts\register_llm_monitor_task.ps1 -Unregister" -ForegroundColor Gray
Write-Host ""

Write-Host "The task will start automatically every $CheckIntervalMinutes minutes" -ForegroundColor Green
Write-Host ""

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""