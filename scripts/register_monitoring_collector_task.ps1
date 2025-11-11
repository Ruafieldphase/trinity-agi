param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = "MonitoringCollector",
    [int]$IntervalMinutes = 5,
    [string]$WorkspaceRoot = "C:\workspace\agi",
    [string]$CollectorScript = "C:\workspace\agi\scripts\collect_monitoring_samples.ps1",
    [string]$LogDir = "C:\workspace\agi\outputs"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

if (-not (Test-Path $CollectorScript)) {
    Write-Err "Collector script not found: $CollectorScript"
    exit 1
}

if (-not (Test-Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
}

if ($Register -and $Unregister) {
    Write-Err "Use either -Register or -Unregister, not both."
    exit 1
}

if (-not $Register -and -not $Unregister) {
    Write-Warn "No action specified. Use -Register or -Unregister."
    exit 2
}

# Build PowerShell command to run collector once and exit
# One sample, immediate run; collector is responsible for calling quick_status with -LogJsonl
$collectorArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$CollectorScript`" -MaxSamples 1 -IntervalSeconds 1"

if ($Register) {
    Write-Info "Registering scheduled task '$TaskName' (every $IntervalMinutes minutes)"

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $collectorArgs -WorkingDirectory $WorkspaceRoot

    # Start once at top of the next minute, repeat indefinitely at fixed interval
    $startTime = (Get-Date).Date.AddMinutes([math]::Ceiling(((Get-Date) - (Get-Date).Date).TotalMinutes))
    if ($startTime -lt (Get-Date)) { $startTime = (Get-Date).AddMinutes(1) }

    $trigger = New-ScheduledTaskTrigger -Once -At $startTime -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)

    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden

    try {
        # If exists, replace
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Existing task '$TaskName' removed."
        }
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
        Write-Info "Task '$TaskName' registered. It will run every $IntervalMinutes minutes."
        Write-Info "You can start it immediately with: Start-ScheduledTask -TaskName '$TaskName'"
    }
    catch {
        Write-Err "Failed to register task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Unregister) {
    Write-Info "Unregistering scheduled task '$TaskName'"
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
