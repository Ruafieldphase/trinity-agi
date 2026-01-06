# Register Meta-Layer Observer as Scheduled Task
# OS-level supervision that monitors ALL processes

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$TaskName = "AGI_MetaLayerObserver"
$ScriptPath = "$WorkspaceRoot\scripts\meta_observer_daemon.ps1"

# Status check
if ($Status -or (!$Register -and !$Unregister)) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "`n✅ Task '$TaskName' is registered" -ForegroundColor Green
        Write-Host "   State: $($task.State)" -ForegroundColor Cyan
        Write-Host "   Last Run: $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "   Next Run: $($task.NextRunTime)" -ForegroundColor Gray
        Write-Host "`n📊 Current Status:" -ForegroundColor Yellow
        
        # Check if actually running
        $running = Get-Process -Name pwsh, powershell -ErrorAction SilentlyContinue | Where-Object {
            try {
                (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like '*meta_observer_daemon*'
            }
            catch { $false }
        }
        
        if ($running) {
            Write-Host "   🟢 Process is RUNNING (PID: $($running.Id))" -ForegroundColor Green
        }
        else {
            Write-Host "   🔴 Process is NOT RUNNING" -ForegroundColor Red
            Write-Host "   Start now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "`n⚠️  Task '$TaskName' is NOT registered" -ForegroundColor Yellow
        Write-Host "   Run with -Register to enable OS-level process monitoring" -ForegroundColor Gray
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

# Register (requires admin)
if ($Register) {
    # Check admin rights
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (!$isAdmin) {
        Write-Host "`n❌ Administrator rights required" -ForegroundColor Red
        Write-Host "   Re-run PowerShell as Administrator" -ForegroundColor Yellow
        exit 1
    }
    
    # Check if already registered
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "`n⚠️  Task '$TaskName' already exists. Unregistering first..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Create action (with hidden window)
    $arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -IntervalSeconds 30 -TimeoutSeconds 300"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $WorkspaceRoot

    # Create trigger (at logon + 3 minutes delay)
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $trigger.Delay = "PT3M"

    # Create settings (with hidden task)
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 99 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -Hidden  # No time limit

    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "Meta-Layer Observer: OS-level supervision of all AGI processes" `
            -ErrorAction Stop | Out-Null
            
        Write-Host "`n✅ Task '$TaskName' registered successfully" -ForegroundColor Green
        Write-Host "   Trigger: At logon + 3 minutes delay" -ForegroundColor Cyan
        Write-Host "   Monitors: ALL AGI processes" -ForegroundColor Gray
        Write-Host "   Interval: Every 30 seconds" -ForegroundColor Gray
        Write-Host "   Timeout: 300 seconds (5 minutes)" -ForegroundColor Gray
        Write-Host "   Auto-restart: Enabled (99 retries)" -ForegroundColor Gray
        Write-Host "`nMeta-Layer Observer will auto-start on next login!" -ForegroundColor Green
        Write-Host "`n🚀 Start now:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    }
    catch {
        Write-Host "`n❌ Failed to register: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}