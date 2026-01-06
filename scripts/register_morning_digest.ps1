param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "09:45",
    [string]$TaskName = "MonitoringMorningDigest"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

try {
    if (-not ($Register -or $Unregister -or $Status)) {
        Write-Host "Usage:" -ForegroundColor Gray
        Write-Host "  .\register_morning_digest.ps1 -Register [-Time HH:mm]" -ForegroundColor Gray
        Write-Host "  .\register_morning_digest.ps1 -Unregister" -ForegroundColor Gray
        Write-Host "  .\register_morning_digest.ps1 -Status" -ForegroundColor Gray
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
            Write-Info "Morning digest task '$TaskName' unregistered."
        }
        catch {
            Write-Warn "Task '$TaskName' not found or already removed."
        }
        exit 0
    }

    if ($Register) {
        if ($Time -notmatch '^[0-2]?[0-9]:[0-5][0-9]$') { throw "Invalid time format: $Time (expected HH:mm)" }
        $parts = $Time.Split(':')
        $at = (Get-Date).Date.AddHours([int]$parts[0]).AddMinutes([int]$parts[1])

        $reportScript = Join-Path $WorkspaceRoot "scripts\generate_monitoring_report.ps1"
        if (-not (Test-Path -LiteralPath $reportScript)) { throw "generate_monitoring_report.ps1 not found at $reportScript" }

        # Generate 24h report and metrics without auto-opening UI
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$reportScript`" -Hours 24"
        $trigger = New-ScheduledTaskTrigger -Daily -At $at

        Write-Info "Registering morning digest '$TaskName' at $Time"
        Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Description "Generate 24h monitoring report (no auto-open)" -Force | Out-Null

        try {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-Info ("Task registered. NextRunTime={0}" -f $info.NextRunTime)
        }
        catch {}
        exit 0
    }
}
catch {
    Write-Err $_
    exit 1
}