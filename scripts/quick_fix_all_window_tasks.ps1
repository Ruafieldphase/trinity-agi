#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
Quick fix for all tasks missing -WindowStyle Hidden

.DESCRIPTION
Identifies tasks that don't have -WindowStyle Hidden in their arguments
and offers to update them.
#>

$ErrorActionPreference = 'Stop'

Write-Host "`n🔧 Scanning for tasks without -WindowStyle Hidden..." -ForegroundColor Cyan

$tasksToFix = @(
    'TaskQueueServer',
    'AGI_AutonomousGoalExecutor',
    'AGI_AutonomousGoalGenerator',
    'AutoDreamPipeline',
    'BinocheEnsembleMonitor',
    'BQI_Online_Learner_Daily'
)

$fixed = 0
$failed = 0

foreach ($taskName in $tasksToFix) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "  ⏭️  Task not found: $taskName (skipping)" -ForegroundColor Gray
        continue
    }
    
    $args = $task.Actions[0].Arguments
    if ($args -like '*-WindowStyle Hidden*') {
        Write-Host "  ✅ Already fixed: $taskName" -ForegroundColor Green
        continue
    }
    
    Write-Host "`n  🔨 Fixing: $taskName" -ForegroundColor Yellow
    Write-Host "     Current: $($task.Actions[0].Execute) $args" -ForegroundColor Gray
    
    # Determine the fix based on task type
    $registerScript = $null
    switch ($taskName) {
        'TaskQueueServer' { $registerScript = 'register_task_queue_server.ps1' }
        'AGI_AutonomousGoalExecutor' { $registerScript = 'register_autonomous_goal_loop.ps1' }
        'AGI_AutonomousGoalGenerator' { $registerScript = 'register_autonomous_goal_loop.ps1' }
        'AutoDreamPipeline' { $registerScript = 'register_dream_pipeline_task.ps1' }
        'BinocheEnsembleMonitor' { $registerScript = 'fdo_agi_repo\scripts\register_ensemble_monitor_task.ps1' }
        'BQI_Online_Learner_Daily' { $registerScript = 'fdo_agi_repo\scripts\register_online_learner_task.ps1' }
    }
    
    if ($registerScript) {
        $fullPath = Join-Path 'C:\workspace\agi' $registerScript
        if (Test-Path -LiteralPath $fullPath) {
            try {
                Write-Host "     Running: $registerScript -Register -Force" -ForegroundColor Cyan
                & $fullPath -Register -Force 2>&1 | Out-Null
                Write-Host "  ✅ Fixed: $taskName" -ForegroundColor Green
                $fixed++
            }
            catch {
                Write-Host "  ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
                $failed++
            }
        }
        else {
            Write-Host "  ⚠️  Register script not found: $registerScript" -ForegroundColor Yellow
            $failed++
        }
    }
    else {
        Write-Host "  ⚠️  No register script mapped for: $taskName" -ForegroundColor Yellow
        $failed++
    }
}

Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Fixed: $fixed" -ForegroundColor Green
Write-Host "   ❌ Failed: $failed" -ForegroundColor Red

if ($fixed -gt 0) {
    Write-Host "`n✨ All fixes applied! Tasks will now run with hidden windows." -ForegroundColor Green
}
