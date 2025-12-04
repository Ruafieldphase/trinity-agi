<#
.SYNOPSIS
Ensures Goal Executor Monitor is registered and running (user mode)

.DESCRIPTION
Checks Windows Scheduled Task 'AGI_GoalExecutorMonitor'. If missing, registers
it in user mode without requiring admin. Prints concise status.

.PARAMETER IntervalMinutes
Repetition interval minutes (default: 10)

.PARAMETER ThresholdMinutes
Staleness threshold minutes (default: 15)

.PARAMETER Quiet
Suppresses non-essential output

.EXAMPLE
./scripts/ensure_goal_executor_monitor.ps1

.EXAMPLE
./scripts/ensure_goal_executor_monitor.ps1 -IntervalMinutes 15 -ThresholdMinutes 20
#>

param(
  [int]$IntervalMinutes = 10,
  [int]$ThresholdMinutes = 15,
  [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$taskName = 'AGI_GoalExecutorMonitor'
$registerScript = Join-Path $PSScriptRoot 'register_goal_executor_monitor_task.ps1'

function Write-Info($msg){ if(-not $Quiet){ Write-Host $msg -ForegroundColor Cyan } }
function Write-Ok($msg){ if(-not $Quiet){ Write-Host $msg -ForegroundColor Green } }
function Write-Warn($msg){ if(-not $Quiet){ Write-Host $msg -ForegroundColor Yellow } }
function Write-Err($msg){ if(-not $Quiet){ Write-Host $msg -ForegroundColor Red } }

try {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    Write-Ok "Goal Monitor already registered: $taskName"
  }
  else {
    Write-Info "Registering Goal Monitor (user mode)..."
    & $registerScript -Register -UserMode -IntervalMinutes $IntervalMinutes -ThresholdMinutes $ThresholdMinutes | Out-Null
  }

  # Show brief status
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Ok ("Status: {0}, Next: {1:yyyy-MM-dd HH:mm:ss}, LastResult: {2}" -f $task.State, $info.NextRunTime, $info.LastTaskResult)
  } else {
    Write-Err "Goal Monitor not registered"
    exit 1
  }
}
catch {
  Write-Err "Ensure failed: $_"
  exit 1
}

exit 0

