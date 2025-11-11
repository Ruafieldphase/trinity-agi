param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Minimal
)

if (-not ($Register -or $Unregister)) {
    Write-Host "Specify -Register or -Unregister" -ForegroundColor Yellow
    exit 1
}

function Invoke-TaskCall {
    param([string]$Path, [string[]]$CallArgs)
    try {
        Write-Host "[RUN] $Path $($CallArgs -join ' ')" -ForegroundColor Cyan
        & $Path @CallArgs
    }
    catch {
        Write-Host "  -> $_" -ForegroundColor Yellow
    }
}

$root = Split-Path -Parent $PSScriptRoot
$scripts = Join-Path $root 'scripts'

if ($Register) {
    Write-Host "`n=== Core Auto-Start Components ===" -ForegroundColor Cyan
    
    # Master Orchestrator (uses Scheduled Task or Registry fallback)
    & (Join-Path $scripts 'register_master_orchestrator.ps1') -Register
    
    # Task Queue Server (At Logon)
    $queueScript = Join-Path $scripts 'register_task_queue_server.ps1'
    if (Test-Path $queueScript) {
        & $queueScript -Register -Force
    }
    
    # Auto-Resume (VS Code + AGI session)
    & (Join-Path $scripts 'register_auto_resume.ps1') -Register

    if (-not $Minimal) {
        Write-Host "`n=== Monitoring & Maintenance ===" -ForegroundColor Cyan
        
        # Monitoring Collector (every 5 minutes)
        $collectorScript = Join-Path $scripts 'register_monitoring_collector_task.ps1'
        if (Test-Path $collectorScript) {
            & $collectorScript -Register -IntervalMinutes 5 -TaskName 'MonitoringCollector'
        }
        
        # Snapshot Rotation (daily 03:15)
        $snapshotScript = Join-Path $scripts 'register_snapshot_rotation_task.ps1'
        if (Test-Path $snapshotScript) {
            & $snapshotScript -Register -Time '03:15'
        }
        
        # Daily Maintenance (daily 03:20)
        $maintenanceScript = Join-Path $scripts 'register_daily_maintenance_task.ps1'
        if (Test-Path $maintenanceScript) {
            & $maintenanceScript -Register -Time '03:20'
        }
        
        Write-Host "`n=== Process Monitors ===" -ForegroundColor Cyan
        
        # Task Watchdog
        $watchdogScript = Join-Path $scripts 'register_task_watchdog_scheduled_task.ps1'
        if (Test-Path $watchdogScript) {
            & $watchdogScript -Register
        }
        
        # Worker Monitor
        $workerScript = Join-Path $scripts 'register_worker_monitor_task.ps1'
        if (Test-Path $workerScript) {
            & $workerScript -Register
        }
    }

    Write-Host "`n=== Pre/Post Reboot Snapshot & Verification ===" -ForegroundColor Cyan
    $preScript = Join-Path $scripts 'register_pre_reboot_snapshot_task.ps1'
    if (Test-Path $preScript) { & $preScript -Register }
    $postScript = Join-Path $scripts 'register_post_reboot_verification_task.ps1'
    if (Test-Path $postScript) { & $postScript -Register }

    Write-Host "`n✅ Auto-recovery registration complete." -ForegroundColor Green
    Write-Host "   These components will auto-start after reboot:" -ForegroundColor Cyan
    Write-Host "   - Master Orchestrator (manages queue, RPA, monitoring)" -ForegroundColor White
    Write-Host "   - Task Queue Server (port 8091)" -ForegroundColor White
    Write-Host "   - Auto-Resume (restores AGI session)" -ForegroundColor White
    if (-not $Minimal) {
        Write-Host "   - Monitoring Collector (every 5m)" -ForegroundColor White
        Write-Host "   - Snapshot Rotation (daily 03:15)" -ForegroundColor White
        Write-Host "   - Daily Maintenance (daily 03:20)" -ForegroundColor White
        Write-Host "   - Task Watchdog (monitors stuck tasks)" -ForegroundColor White
        Write-Host "   - Worker Monitor (ensures RPA worker)" -ForegroundColor White
    }
    Write-Host "   - Pre-Reboot Snapshot (logoff / optional shutdown event)" -ForegroundColor White
    Write-Host "   - Post-Reboot Verification (auto-fix)" -ForegroundColor White
    exit 0
}

if ($Unregister) {
    Invoke-TaskCall (Join-Path $scripts 'register_worker_monitor_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_task_watchdog_scheduled_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_daily_maintenance_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_snapshot_rotation_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_monitoring_collector_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_auto_resume.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_pre_reboot_snapshot_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_post_reboot_verification_task.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_task_queue_server.ps1') -CallArgs @('-Unregister')
    Invoke-TaskCall (Join-Path $scripts 'register_master_orchestrator.ps1') -CallArgs @('-Unregister')
    Write-Host "Auto-recovery unregistration complete." -ForegroundColor Green
    exit 0
}
