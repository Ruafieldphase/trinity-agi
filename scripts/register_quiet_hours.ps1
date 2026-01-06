param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Start = "01:00",
    [string]$End = "09:00",
    [int]$IntervalMinutes = 30,
    [string]$TaskName = "AGI_QuietHours_AlertCheck"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Get-MinutesFromHHmm([string]$hhmm) {
    if ($hhmm -notmatch '^[0-2]?[0-9]:[0-5][0-9]$') { throw "Invalid time format: $hhmm (expected HH:mm)" }
    $parts = $hhmm.Split(':')
    return ([int]$parts[0]) * 60 + ([int]$parts[1])
}

try {
    if (-not ($Register -or $Unregister -or $Status)) {
        Write-Host "Usage:" -ForegroundColor Gray
        Write-Host "  .\register_quiet_hours.ps1 -Register [-Start HH:mm] [-End HH:mm] [-IntervalMinutes 30]" -ForegroundColor Gray
        Write-Host "  .\register_quiet_hours.ps1 -Unregister" -ForegroundColor Gray
        Write-Host "  .\register_quiet_hours.ps1 -Status" -ForegroundColor Gray
        exit 0
    }

    if ($Status) {
        try {
            $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            $t | Select-Object TaskName, State, TaskPath, Triggers | Format-List
            Write-Info ("LastRunTime={0}, NextRunTime={1}" -f $info.LastRunTime, $info.NextRunTime)
        }
        catch {
            Write-Warn "Task '$TaskName' not found."
            exit 1
        }
        exit 0
    }

    if ($Unregister) {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
            Write-Info "Quiet hours task '$TaskName' unregistered."
        }
        catch {
            Write-Warn "Task '$TaskName' not found or already removed."
        }
        exit 0
    }

    if ($Register) {
        $startMin = Get-MinutesFromHHmm $Start
        $endMin = Get-MinutesFromHHmm $End
        $durMin = if ($endMin -ge $startMin) { $endMin - $startMin } else { (24 * 60 - $startMin) + $endMin }
        if ($durMin -le 0) { throw "Computed repetition duration is non-positive. Check Start/End times." }

        $repetitionDuration = [TimeSpan]::FromMinutes($durMin)
        $repetitionInterval = [TimeSpan]::FromMinutes([math]::Max(5, $IntervalMinutes))

        # Build a concrete DateTime for today's start time
        $startParts = $Start.Split(':')
        $startDt = (Get-Date).Date.AddHours([int]$startParts[0]).AddMinutes([int]$startParts[1])

        # Compatibility-first: register a simple daily trigger at the start time (no repetition)
        $trigger = New-ScheduledTaskTrigger -Daily -At $startDt

        $scriptPath = Join-Path $WorkspaceRoot "fdo_agi_repo\scripts\alert_system.ps1"
        if (-not (Test-Path -LiteralPath $scriptPath)) { throw "alert_system.ps1 not found at $scriptPath" }
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -NoAlert"

        Write-Info "Registering quiet-hours alert check '$TaskName' at $Start (quiet window $Start-$End)."
        try {
            # Create or replace
            Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Description "Run alert_system.ps1 -NoAlert during quiet hours" -Force | Out-Null
        }
        catch {
            Write-Warn "Register-ScheduledTask reported an error: $($_.Exception.Message). Will try minimal registration."
            $trigger = New-ScheduledTaskTrigger -Daily -At $startDt
            Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Force | Out-Null
        }

        try {
            $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-Info ("Task registered. NextRunTime={0}" -f $info.NextRunTime)
        }
        catch {
            Write-Warn "Registered, but could not fetch task info."
        }
        Write-Warn "Note: This registers a single daily run at the start of quiet hours. To run more frequently, extend this script with repetition triggers on your OS version."
        Write-Warn "This only suppresses alerts during quiet hours. Core monitoring remains active."
        exit 0
    }
}
catch {
    Write-Err $_
    exit 1
}