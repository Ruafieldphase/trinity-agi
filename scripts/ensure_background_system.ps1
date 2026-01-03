<#
.SYNOPSIS
Ensure core background automation is active (scheduler + daemon hooks)

.DESCRIPTION
Runs lightweight checks and ensures the Goal Executor Monitor is registered.
Reports Meta Supervisor scheduler status and optionally starts its daemon.

.PARAMETER StartDaemon
Start Meta Supervisor background job in this session if not running.

.EXAMPLE
./scripts/ensure_background_system.ps1

.EXAMPLE
./scripts/ensure_background_system.ps1 -StartDaemon
#>

param(
  [switch]$StartDaemon
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent

function Section($title){ Write-Host "`n=== $title ===" -ForegroundColor Cyan }
function Ok($msg){ Write-Host $msg -ForegroundColor Green }
function Warn($msg){ Write-Host $msg -ForegroundColor Yellow }
function Info($msg){ Write-Host $msg -ForegroundColor Gray }

# 1) Meta Supervisor scheduler status
Section 'Meta Supervisor Scheduler'
$regMeta = Join-Path $PSScriptRoot 'register_meta_supervisor_task.ps1'
if (Test-Path $regMeta) {
  & $regMeta -Status | Write-Host
} else {
  Warn "register_meta_supervisor_task.ps1 not found"
}

# 2) Ensure Goal Executor Monitor registered (user mode)
Section 'Goal Executor Monitor Ensure'
$ensureGoal = Join-Path $PSScriptRoot 'ensure_goal_executor_monitor.ps1'
if (Test-Path $ensureGoal) {
  & $ensureGoal -IntervalMinutes 10 -ThresholdMinutes 15
} else {
  Warn "ensure_goal_executor_monitor.ps1 not found"
}

# 3) Optionally start Meta Supervisor daemon in-session
if ($StartDaemon) {
  Section 'Meta Supervisor Daemon'
  $startDaemon = Join-Path $PSScriptRoot 'start_meta_supervisor_daemon.ps1'
  if (Test-Path $startDaemon) {
    & $startDaemon
  } else {
    Warn "start_meta_supervisor_daemon.ps1 not found"
  }
}

Ok "\nAll checks completed."
