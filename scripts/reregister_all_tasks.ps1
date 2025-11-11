#requires -Version 5.1
<#
.SYNOPSIS
    Re-register all scheduled tasks with fixed hidden window settings
.DESCRIPTION
    Re-registers all scheduled tasks to apply the hidden window fixes
#>
param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (!$isAdmin) {
    Write-Host "`n❌ Administrator rights required" -ForegroundColor Red
    Write-Host "   Re-run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

$workspaceRoot = Split-Path -Parent $PSScriptRoot

# List of tasks to re-register (5분 간격 + 핵심 백그라운드 작업)
$tasksToReregister = @(
    @{
        Name        = 'MonitoringCollector'
        Script      = 'scripts\register_monitoring_collector_task.ps1'
        Args        = '-Register -IntervalMinutes 5'
        Description = '5분 간격 모니터링 수집'
    },
    @{
        Name        = 'StreamObserverTelemetry'
        Script      = 'scripts\register_observer_telemetry_task.ps1'
        Args        = '-Register'
        Description = 'Stream Observer 텔레메트리'
    },
    @{
        Name        = 'MetaObserver'
        Script      = 'scripts\register_meta_observer_task.ps1'
        Args        = '-Register'
        Description = 'Meta Observer (30초 간격)'
    },
    @{
        Name        = 'WorkerMonitor'
        Script      = 'scripts\register_worker_monitor_task.ps1'
        Args        = '-Register'
        Description = 'RPA Worker 모니터'
    },
    @{
        Name        = 'AgiWatchdog'
        Script      = 'scripts\register_task_watchdog_scheduled_task.ps1'
        Args        = '-Register'
        Description = 'Task Queue Watchdog'
    },
    @{
        Name        = 'LumenProbeMonitor'
        Script      = 'scripts\register_lumen_probe_task.ps1'
        Args        = '-Register -IntervalMinutes 10'
        Description = 'Lumen Health Probe'
    },
    @{
        Name        = 'SnapshotRotation'
        Script      = 'scripts\register_snapshot_rotation_task.ps1'
        Args        = '-Register -Time 03:15 -Zip'
        Description = '스냅샷 로테이션 (새벽 3:15)'
    },
    @{
        Name        = 'DailyMaintenance'
        Script      = 'scripts\register_daily_maintenance_task.ps1'
        Args        = '-Register -Time 03:20'
        Description = '일일 유지보수 (새벽 3:20)'
    },
    @{
        Name        = 'BqiPhase6Learning'
        Script      = 'fdo_agi_repo\scripts\register_bqi_phase6_scheduled_task.ps1'
        Args        = '-Register -Time 03:05'
        Description = 'BQI Phase 6 학습 (새벽 3:05)'
    },
    @{
        Name        = 'BqiOnlineLearner'
        Script      = 'fdo_agi_repo\scripts\register_online_learner_task.ps1'
        Args        = '-Register -Time 03:20'
        Description = 'BQI Online Learner (새벽 3:20)'
    },
    @{
        Name        = 'BqiEnsembleMonitor'
        Script      = 'fdo_agi_repo\scripts\register_ensemble_monitor_task.ps1'
        Args        = '-Register -Time 03:15 -Hours 24'
        Description = 'BQI Ensemble Monitor (새벽 3:15)'
    },
    @{
        Name        = 'AutopoieticReport'
        Script      = 'scripts\register_autopoietic_report_task.ps1'
        Args        = '-Register -Time 03:25 -OpenMd'
        Description = 'Autopoietic Report (새벽 3:25)'
    },
    @{
        Name        = 'TrinityCycle'
        Script      = 'scripts\register_trinity_cycle_task.ps1'
        Args        = '-Register -Time 10:00'
        Description = 'Trinity Cycle (오전 10시)'
    }
)

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Re-register All Tasks (Hidden Window Fix)       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📊 Tasks to re-register: $($tasksToReregister.Count)`n" -ForegroundColor Gray

$successCount = 0
$failCount = 0

foreach ($task in $tasksToReregister) {
    $scriptPath = Join-Path $workspaceRoot $task.Script
    
    Write-Host "🔄 $($task.Description)" -ForegroundColor Cyan
    Write-Host "   Task: $($task.Name)" -ForegroundColor Gray
    
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        Write-Host "   ⚠️  Script not found: $($task.Script)" -ForegroundColor Yellow
        $failCount++
        continue
    }
    
    try {
        # Build command
        $cmd = "& `"$scriptPath`" $($task.Args)"
        
        # Execute
        $output = Invoke-Expression $cmd 2>&1
        
        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
            Write-Host "   ✅ SUCCESS" -ForegroundColor Green
            $successCount++
        }
        else {
            Write-Host "   ❌ FAILED (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    }
    catch {
        Write-Host "   ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "   Total: $($tasksToReregister.Count)" -ForegroundColor Gray
Write-Host "   Success: $successCount" -ForegroundColor Green
Write-Host "   Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { 'Red' } else { 'Gray' })

if ($successCount -eq $tasksToReregister.Count) {
    Write-Host "`n✨ All tasks re-registered successfully!" -ForegroundColor Green
    Write-Host "`n💡 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Wait 5 minutes to verify no windows appear" -ForegroundColor Gray
    Write-Host "   2. Check task status: Get-ScheduledTask | Where-Object State -eq 'Running'" -ForegroundColor Gray
}
else {
    Write-Host "`n⚠️  Some tasks failed to re-register" -ForegroundColor Yellow
    Write-Host "   Check logs above for details" -ForegroundColor Gray
}

exit $(if ($failCount -gt 0) { 1 } else { 0 })
