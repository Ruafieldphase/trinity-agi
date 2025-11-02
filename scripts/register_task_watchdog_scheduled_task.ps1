# Register Task Watchdog as Scheduled Task
# This monitors Task Queue for stuck tasks and auto-recovers them

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)

$TaskName = "AGI_TaskWatchdog"
$WorkspaceRoot = "C:\workspace\agi"
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$ScriptPath = "$WorkspaceRoot\fdo_agi_repo\scripts\task_watchdog.py"

# Status check
if ($Status -or (!$Register -and !$Unregister)) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "`n✅ Task '$TaskName' is registered" -ForegroundColor Green
        Write-Host "   State: $($task.State)" -ForegroundColor Cyan
        Write-Host "   Last Run: $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "   Next Run: $($task.NextRunTime)" -ForegroundColor Gray
    }
    else {
        Write-Host "`n⚠️  Task '$TaskName' is NOT registered" -ForegroundColor Yellow
        Write-Host "   Run with -Register to enable automatic stuck task detection" -ForegroundColor Gray
    }
    exit 0
}

# Unregister
if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "`n✅ Task '$TaskName' unregistered successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "`n❌ Failed to unregister: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    exit 0
}

# Register
if ($Register) {
    # Check if already registered
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "`n⚠️  Task '$TaskName' already exists. Unregistering first..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Create action
    $arguments = "`"$ScriptPath`" --server http://127.0.0.1:8091 --interval 60 --auto-recover"
    $action = New-ScheduledTaskAction -Execute $PythonExe -Argument $arguments -WorkingDirectory $WorkspaceRoot

    # Create trigger (at logon + 2 minutes delay)
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $trigger.Delay = "PT2M"

    # Create settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

    # Register task
    try {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Monitors Task Queue for stuck tasks and auto-recovers them" -ErrorAction Stop | Out-Null
        Write-Host "`n✅ Task '$TaskName' registered successfully" -ForegroundColor Green
        Write-Host "   Trigger: At logon + 2 minutes delay" -ForegroundColor Cyan
        Write-Host "   Monitors: Task Queue (http://127.0.0.1:8091)" -ForegroundColor Gray
        Write-Host "   Interval: Every 60 seconds" -ForegroundColor Gray
        Write-Host "   Auto-recover: Enabled" -ForegroundColor Gray
        Write-Host "`nTask Watchdog will auto-start on next login!" -ForegroundColor Green
        Write-Host "`nTest now:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    }
    catch {
        Write-Host "`n❌ Failed to register: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
