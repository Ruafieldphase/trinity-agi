<#
.SYNOPSIS
Register / Unregister the post-reboot verification scheduled task.

.DESCRIPTION
Creates an AtLogon task that runs `run_post_reboot_verification.ps1` with
auto-fix enabled (delegated to underlying script). Hidden task; user scope.

.EXAMPLES
  ./register_post_reboot_verification_task.ps1 -Register
  ./register_post_reboot_verification_task.ps1 -Unregister
  ./register_post_reboot_verification_task.ps1 -Status
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Register')][switch]$Register,
    [Parameter(ParameterSetName = 'Unregister')][switch]$Unregister,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
    [string]$TaskName = 'PostRebootVerify',
    [switch]$Force,
    [int]$DelaySeconds = 45
)

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m) { Write-Host "[ERR ] $m" -ForegroundColor Red }

$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$runner = Join-Path $root 'run_post_reboot_verification.ps1'
if (!(Test-Path -LiteralPath $runner)) { Err "Runner missing: $runner"; exit 1 }

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($Register) {
    if ($existing) {
        if (-not $Force) { Warn "Task already exists. Use -Force to recreate."; exit 0 }
        try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null } catch { Warn "Failed to remove existing task: $($_.Exception.Message)" }
    }
    $pwsh = (Get-Command powershell).Source
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
    $action = New-ScheduledTaskAction -Execute $pwsh -Argument $arg
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    # Delay implementation: Use ScheduledTask settings StartWhenAvailable + a wrapper Sleep built into runner (simpler)
    # We implement delay by creating a small wrapper inline using -Command if >0.
    if ($DelaySeconds -gt 0) {
        $wrapper = "Start-Sleep -Seconds $DelaySeconds; & '$runner'"
        $arg = "-NoProfile -ExecutionPolicy Bypass -Command `"$wrapper`""
        $action = New-ScheduledTaskAction -Execute $pwsh -Argument $arg
    }
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $settings.Hidden = $true
    try {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Post reboot verification (auto-fix)' | Out-Null
        Info "Task '$TaskName' registered (logon + delay ${DelaySeconds}s)."
        Info "Manual test: .\\run_post_reboot_verification.ps1 -OpenMd"
    }
    catch { Err "Failed to register: $($_.Exception.Message)"; exit 1 }
    exit 0
}
elseif ($Unregister) {
    if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null; Info "Task removed: $TaskName" }
    else { Warn "Task not found: $TaskName" }
    exit 0
}
else {
    Info "Post-Reboot Verification Task Status"
    if ($existing) { Write-Host "  REGISTERED: $TaskName" -ForegroundColor Green; Write-Host "  State: $($existing.State)" -ForegroundColor Gray } else { Write-Host "  NOT REGISTERED" -ForegroundColor Yellow }
    Write-Host "  Runner: $runner" -ForegroundColor Gray
    Write-Host "  Test: .\\run_post_reboot_verification.ps1 -OpenMd" -ForegroundColor Gray
    exit 0
}