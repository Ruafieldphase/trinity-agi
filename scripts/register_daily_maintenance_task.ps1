param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = "MonitoringDailyMaintenance",
    [string]$Time = "03:20",
    [string]$WorkspaceRoot = "C:\workspace\agi",
    [string]$MaintenanceScript = "C:\workspace\agi\scripts\daily_monitoring_maintenance.ps1",
    [int]$ReportHours = 24,
    [int]$ArchiveKeepDays = 14,
    [switch]$NoZip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (-not (Test-Path $MaintenanceScript)) {
    Write-Err "Maintenance script not found: $MaintenanceScript"
    exit 1
}

if ($Register -and $Unregister) {
    Write-Err "Use either -Register or -Unregister, not both."
    exit 1
}

if (-not $Register -and -not $Unregister) {
    Write-Warn "No action specified. Use -Register or -Unregister."
    exit 2
}

# Build PowerShell arguments to run daily maintenance
$maintArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$MaintenanceScript`" -ReportHours $ReportHours -ArchiveKeepDays $ArchiveKeepDays"
if ($NoZip) { $maintArgs += " -NoZip" }

if ($Register) {
    Write-Info "Registering daily maintenance task '$TaskName' at $Time daily"

    # Parse time (HH:mm)
    try {
        $today = Get-Date
        $runAt = Get-Date ("{0} {1}" -f $today.ToString('yyyy-MM-dd'), $Time)
        if ($runAt -lt $today) { $runAt = $runAt.AddDays(1) }
    }
    catch {
        Write-Err "Invalid -Time format. Use HH:mm (e.g., 03:20)."
        exit 1
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $maintArgs -WorkingDirectory $WorkspaceRoot
    $trigger = New-ScheduledTaskTrigger -Once -At $runAt -RepetitionInterval (New-TimeSpan -Days 1) -RepetitionDuration (New-TimeSpan -Days 3650)

    # Settings & principal
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$false -DontStopIfGoingOnBatteries:$false -StartWhenAvailable -WakeToRun
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    try {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Existing task '$TaskName' removed."
        }
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
        Write-Info "Task '$TaskName' registered for daily run at $Time."
        Write-Info "You can trigger it with: Start-ScheduledTask -TaskName '$TaskName'"
    }
    catch {
        Write-Err "Failed to register maintenance task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Unregister) {
    Write-Info "Unregistering daily maintenance task '$TaskName'"
    try {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Task '$TaskName' removed."
        }
        else {
            Write-Warn "Task '$TaskName' not found. Nothing to do."
        }
    }
    catch {
        Write-Err "Failed to unregister task: $($_.Exception.Message)"
        exit 1
    }
}