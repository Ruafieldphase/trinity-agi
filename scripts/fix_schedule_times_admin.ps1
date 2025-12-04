#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Fix schedule times for remaining 03:xx tasks that need admin privileges.
.DESCRIPTION
    Unregisters and re-registers tasks that couldn't be updated due to permission issues.
#>

param()

$ErrorActionPreference = 'Continue'

Write-Host "`n=== Schedule Time Fix (Admin) ===" -ForegroundColor Cyan
Write-Host "Fixing remaining 03:xx schedules that require elevated privileges..." -ForegroundColor Yellow

# 1. Fix MonitoringSnapshotRotationDaily (03:15 -> 10:00)
Write-Host "`n[1/3] MonitoringSnapshotRotationDaily: 03:15 -> 10:00" -ForegroundColor Cyan
try {
    $task = Get-ScheduledTask -TaskName 'MonitoringSnapshotRotationDaily' -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "  - Current next run: $((Get-ScheduledTaskInfo -TaskName 'MonitoringSnapshotRotationDaily').NextRunTime)"
        Unregister-ScheduledTask -TaskName 'MonitoringSnapshotRotationDaily' -Confirm:$false -ErrorAction Stop
        Write-Host "  ✓ Unregistered" -ForegroundColor Green
    }
    
    & "$PSScriptRoot\register_snapshot_rotation_task.ps1" -Register -Time '10:00' -Zip
    Write-Host "  ✓ Re-registered at 10:00" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
}

# 2. Fix BinocheOnlineLearner (03:20 -> 10:25)
Write-Host "`n[2/3] BinocheOnlineLearner: 03:20 -> 10:25" -ForegroundColor Cyan
try {
    $task = Get-ScheduledTask -TaskName 'BinocheOnlineLearner' -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "  - Current next run: $((Get-ScheduledTaskInfo -TaskName 'BinocheOnlineLearner').NextRunTime)"
        Unregister-ScheduledTask -TaskName 'BinocheOnlineLearner' -Confirm:$false -ErrorAction Stop
        Write-Host "  ✓ Unregistered" -ForegroundColor Green
    }
    
    & "$PSScriptRoot\..\fdo_agi_repo\scripts\register_online_learner_task.ps1" -Register -Time '10:25'
    Write-Host "  ✓ Re-registered at 10:25" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
}

# 3. Fix AutopoieticLoopDailyReport if needed (03:25 -> 10:10)
Write-Host "`n[3/3] Checking AutopoieticLoopDailyReport..." -ForegroundColor Cyan
try {
    $task = Get-ScheduledTask -TaskName 'AutopoieticLoopDailyReport' -ErrorAction SilentlyContinue
    if ($task) {
        $info = Get-ScheduledTaskInfo -TaskName 'AutopoieticLoopDailyReport'
        Write-Host "  - Current next run: $($info.NextRunTime)"
        
        if ($info.NextRunTime -and $info.NextRunTime.Hour -ne 10) {
            Unregister-ScheduledTask -TaskName 'AutopoieticLoopDailyReport' -Confirm:$false -ErrorAction Stop
            Write-Host "  ✓ Unregistered" -ForegroundColor Green
            
            & "$PSScriptRoot\register_autopoietic_report_task.ps1" -Register -Time '10:10'
            Write-Host "  ✓ Re-registered at 10:10" -ForegroundColor Green
        }
        else {
            Write-Host "  ✓ Already at 10:10" -ForegroundColor Green
        }
    }
}
catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Verification ===" -ForegroundColor Cyan
$tasks = @('MonitoringSnapshotRotationDaily', 'BinocheOnlineLearner', 'AutopoieticLoopDailyReport')
foreach ($taskName in $tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $taskName
        $hour = if ($info.NextRunTime) { $info.NextRunTime.Hour } else { "N/A" }
        Write-Host "  $taskName : Hour=$hour, State=$($task.State)" -ForegroundColor $(if ($hour -ge 10 -or $hour -eq "N/A") { 'Green' } else { 'Yellow' })
    }
    catch {
        Write-Host "  $taskName : Not found" -ForegroundColor Red
    }
}

Write-Host "`n✓ Schedule fix complete!" -ForegroundColor Green
Write-Host "Re-run task list to verify all times are correct." -ForegroundColor Cyan
