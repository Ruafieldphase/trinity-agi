<#
.SYNOPSIS
Register / Unregister a pre-reboot snapshot task.

.DESCRIPTION
Creates a Scheduled Task that captures a lightweight system snapshot (safety
check + continuity artifacts) when the user logs off. Optionally attempts to
bind to the shutdown event (Event ID 1074) using `schtasks /Create /SC ONEVENT`.
Event trigger creation may fail without elevated rights; script falls back to
an AtLogoff trigger automatically unless -StrictEvent is specified.

Use `run_pre_reboot_snapshot.ps1` to build the snapshot.

.EXAMPLES
  ./register_pre_reboot_snapshot_task.ps1 -Register
  ./register_pre_reboot_snapshot_task.ps1 -Register -UseShutdownEvent
  ./register_pre_reboot_snapshot_task.ps1 -Unregister
  ./register_pre_reboot_snapshot_task.ps1 -Status
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Register')][switch]$Register,
    [Parameter(ParameterSetName = 'Unregister')][switch]$Unregister,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
    [string]$TaskName = 'PreRebootSnapshot',
    [switch]$UseShutdownEvent,
    [switch]$StrictEvent,
    [switch]$Force
)

function Write-Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m) { Write-Host "[ERR ] $m" -ForegroundColor Red }

$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$runner = Join-Path $scriptRoot 'run_pre_reboot_snapshot.ps1'
if (-not (Test-Path -LiteralPath $runner)) { Write-Err "Snapshot runner missing: $runner"; exit 1 }

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($Register) {
    if ($existing) {
        if (-not $Force) { Write-Warn "Task already exists. Use -Force to recreate."; exit 0 }
        try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false } catch { Write-Warn "Could not remove existing task: $($_.Exception.Message)" }
    }

    $pwsh = (Get-Command powershell).Source
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""

    $taskRegistered = $false
    if ($UseShutdownEvent) {
        Write-Info "Attempting event-based trigger (System/User32 EventID 1074)"
        $xmlQuery = '*[System[(EventID=1074)]]'
        try {
            $cmd = "schtasks /Create /TN $TaskName /TR `"$pwsh -NoProfile -ExecutionPolicy Bypass -File $runner`" /SC ONEVENT /EC System /MO `$xmlQuery /F"
            Write-Info $cmd
            cmd.exe /c $cmd | Out-Null
            $existing2 = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($existing2) { Write-Info "Event trigger task registered."; $taskRegistered = $true }
            elseif ($StrictEvent) { Write-Err "Event trigger registration failed and -StrictEvent specified."; exit 1 }
            else { Write-Warn "Event trigger failed; falling back to logoff." }
        }
        catch {
            if ($StrictEvent) { Write-Err "Event trigger exception: $($_.Exception.Message)"; exit 1 }
            Write-Warn "Event trigger failed: $($_.Exception.Message) -> fallback to logoff"
        }
    }

    if (-not $taskRegistered) {
        Write-Info "Registering AtLogoff trigger"
        $trigger = New-ScheduledTaskTrigger -AtLogOff
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        $settings.Hidden = $true
        try {
            Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Pre-reboot snapshot (logoff trigger)' | Out-Null
            $taskRegistered = $true
        }
        catch { Write-Err "Failed to register logoff task: $($_.Exception.Message)"; exit 1 }
    }

    if ($taskRegistered) {
        Write-Info "Task '$TaskName' registered."; Write-Info "You can test now by running: .\\run_pre_reboot_snapshot.ps1"
    }
    exit 0
}
elseif ($Unregister) {
    if ($existing) {
        try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null; Write-Info "Task '$TaskName' removed." }
        catch { Write-Err "Failed to remove task: $($_.Exception.Message)"; exit 1 }
    }
    else { Write-Warn "Task not found: $TaskName" }
    exit 0
}
else {
    # Status
    Write-Info "Pre-Reboot Snapshot Task Status"
    if ($existing) {
        Write-Host "  REGISTERED: $TaskName" -ForegroundColor Green
        Write-Host "  State: $($existing.State)" -ForegroundColor Gray
        if ($existing.Triggers) {
            foreach ($t in $existing.Triggers) { Write-Host "  Trigger: $($t.TriggerType)" -ForegroundColor Gray }
        }
    }
    else { Write-Host "  NOT REGISTERED" -ForegroundColor Yellow }
    Write-Host "  Runner: $runner" -ForegroundColor Gray
    Write-Host "  Test manual run: .\\run_pre_reboot_snapshot.ps1 -OpenMd" -ForegroundColor Gray
    exit 0
}