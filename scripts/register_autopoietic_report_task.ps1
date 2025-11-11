param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = "AutopoieticLoopDailyReport",
    [string]$Time = "03:25",
    [string]$WorkspaceRoot = "C:\workspace\agi",
    [int]$Hours = 24,
    [switch]$OpenMd
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

$Generator = Join-Path $WorkspaceRoot 'scripts/generate_autopoietic_report.ps1'
if (-not (Test-Path $Generator)) {
    Write-Err "Generator script not found: $Generator"
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

# Build PowerShell arguments to run daily autopoietic report
$openFlag = if ($OpenMd) { " -OpenMd" } else { "" }
$psArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$Generator`" -Hours $Hours$openFlag"

if ($Register) {
    Write-Info "Registering autopoietic report task '$TaskName' at $Time daily"

    try {
        $today = Get-Date
        $runAt = Get-Date ("{0} {1}" -f $today.ToString('yyyy-MM-dd'), $Time)
        if ($runAt -lt $today) { $runAt = $runAt.AddDays(1) }
    }
    catch {
        Write-Err "Invalid -Time format. Use HH:mm (e.g., 03:25)."
        exit 1
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $psArgs -WorkingDirectory $WorkspaceRoot
    $trigger = New-ScheduledTaskTrigger -Once -At $runAt -RepetitionInterval (New-TimeSpan -Days 1) -RepetitionDuration (New-TimeSpan -Days 3650)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$false -DontStopIfGoingOnBatteries:$false -StartWhenAvailable -WakeToRun
$settings.Hidden = $true
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    try {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Existing task '$TaskName' removed."
        }
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
        Write-Info "Task '$TaskName' registered for daily run at $Time."
        Write-Info "Trigger manually with: Start-ScheduledTask -TaskName '$TaskName'"
    }
    catch {
        Write-Err "Failed to register task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Unregister) {
    Write-Info "Unregistering autopoietic report task '$TaskName'"
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
