<#
.SYNOPSIS
    Check status of Lumen Gateway scheduled task
    
.DESCRIPTION
    Displays detailed information about the Gateway scheduled task
    
.PARAMETER TaskName
    Name of the scheduled task (default: LumenGatewayAutoStart)
    
.EXAMPLE
    .\status_gateway_task.ps1
    Show task status
#>

param(
    [string]$TaskName = "LumenGatewayAutoStart"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Lumen Gateway Task Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get task
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "[ERROR] Task '$TaskName' not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available Gateway/Lumen tasks:" -ForegroundColor Cyan
    $relatedTasks = Get-ScheduledTask | Where-Object { 
        $_.TaskName -like "*Gateway*" -or 
        $_.TaskName -like "*Lumen*" -or
        $_.TaskName -like "*ION*"
    }
    
    if ($relatedTasks) {
        $relatedTasks | Format-Table TaskName, State, LastRunTime, NextRunTime -AutoSize
    }
    else {
        Write-Host "  No related tasks found" -ForegroundColor Gray
    }
    exit 1
}

# Task info
$info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Task Details:" -ForegroundColor Green
Write-Host "  Name:             $($task.TaskName)" -ForegroundColor White
Write-Host "  State:            $($task.State)" -ForegroundColor White
Write-Host "  Author:           $($task.Author)" -ForegroundColor White
Write-Host "  Description:      $($task.Description)" -ForegroundColor White
Write-Host ""

Write-Host "Execution Info:" -ForegroundColor Green
Write-Host "  Last Run Time:    $($info.LastRunTime)" -ForegroundColor White
Write-Host "  Last Result:      $($info.LastTaskResult) (0 = Success)" -ForegroundColor White
Write-Host "  Next Run Time:    $($info.NextRunTime)" -ForegroundColor White
Write-Host "  Number of Runs:   $($info.NumberOfMissedRuns + 1)" -ForegroundColor White
Write-Host ""

Write-Host "Triggers:" -ForegroundColor Green
foreach ($trigger in $task.Triggers) {
    $triggerType = $trigger.GetType().Name
    Write-Host "  - Type:    $triggerType" -ForegroundColor White
    Write-Host "    Enabled: $($trigger.Enabled)" -ForegroundColor White
    
    if ($trigger.StartBoundary) {
        Write-Host "    Start:   $($trigger.StartBoundary)" -ForegroundColor White
    }
    
    if ($trigger.EndBoundary) {
        Write-Host "    End:     $($trigger.EndBoundary)" -ForegroundColor White
    }
}
Write-Host ""

Write-Host "Actions:" -ForegroundColor Green
foreach ($action in $task.Actions) {
    Write-Host "  - Execute:        $($action.Execute)" -ForegroundColor White
    Write-Host "    Arguments:      $($action.Arguments)" -ForegroundColor White
    Write-Host "    Working Dir:    $($action.WorkingDirectory)" -ForegroundColor White
}
Write-Host ""

Write-Host "Settings:" -ForegroundColor Green
$settings = $task.Settings
Write-Host "  Allow Start On Batteries:      $($settings.AllowStartOnBatteries)" -ForegroundColor White
Write-Host "  Don't Stop On Battery:         $($settings.DisallowStartIfOnBatteries -eq $false)" -ForegroundColor White
Write-Host "  Start When Available:          $($settings.StartWhenAvailable)" -ForegroundColor White
Write-Host "  Restart on Failure:            $($settings.RestartCount) times" -ForegroundColor White
Write-Host "  Restart Interval:              $($settings.RestartInterval)" -ForegroundColor White
Write-Host ""

# Check if Gateway is actually running
Write-Host "Gateway Process Status:" -ForegroundColor Green

$collectorProcess = Get-Process python -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like "*ion_metrics_collector*" }

$exporterPort = Get-NetTCPConnection -LocalPort 9108 -State Listen -ErrorAction SilentlyContinue

if ($collectorProcess) {
    Write-Host "  [OK] Collector:  Running (PID: $($collectorProcess.Id))" -ForegroundColor Green
}
else {
    Write-Host "  [ERROR] Collector:  Not running" -ForegroundColor Red
}

if ($exporterPort) {
    Write-Host "  [OK] Exporter:   Listening on port 9108 (PID: $($exporterPort.OwningProcess))" -ForegroundColor Green
}
else {
    Write-Host "  [ERROR] Exporter:   Not running" -ForegroundColor Red
}

Write-Host ""

# Quick actions
Write-Host "Quick Actions:" -ForegroundColor Cyan
Write-Host "  Start task:   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Stop task:    Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Enable task:  Enable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Disable task: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
