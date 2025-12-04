param(
    [switch]$CheckOnly,
    [switch]$StartIfStopped,
    [switch]$Register,
    [switch]$Unregister,
    [int]$Port = 8093,
    [int]$IntervalMinutes = 5,
    [string]$TaskName = "OriginalDataApiEnsure",
    [string]$WorkspaceRoot = "C:\workspace\agi"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Get-PythonPath {
    param([string]$Root)
    $candidates = @(
        (Join-Path $Root 'LLM_Unified\.venv\Scripts\python.exe'),
        (Join-Path $Root 'fdo_agi_repo\.venv\Scripts\python.exe'),
        'python'
    )
    foreach ($p in $candidates) {
        if ($p -eq 'python') { return $p }
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return 'python'
}

$ServerScript = Join-Path $WorkspaceRoot 'scripts\original_data_server.py'
if (-not (Test-Path -LiteralPath $ServerScript)) {
    Write-Err "Server script not found: $ServerScript"
    exit 1
}

function Test-OriginalDataHealth {
    param([int]$Port)
    try {
        $uri = "http://127.0.0.1:$Port/health"
        Invoke-RestMethod -Uri $uri -TimeoutSec 2 | Out-Null
        return $true
    }
    catch { return $false }
}

function Start-OriginalDataApi {
    param([int]$Port)
    $py = Get-PythonPath -Root $WorkspaceRoot
    $args = "`"$ServerScript`" --port $Port"
    Write-Info "Starting Original Data API on port $Port using: $py $args"
    try {
        Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $WorkspaceRoot -WindowStyle Hidden | Out-Null
        Start-Sleep -Seconds 1
    }
    catch {
        Write-Err "Failed to start API: $($_.Exception.Message)"
        throw
    }
}

# If user requested to register a Scheduled Task
if ($Register -or $Unregister) {
    if ($Register -and $Unregister) {
        Write-Err "Use either -Register or -Unregister, not both."
        exit 1
    }

    if ($Register) {
        Write-Info "Registering scheduled task '$TaskName' (every $IntervalMinutes minutes)"

        $scriptPath = $MyInvocation.MyCommand.Path
        $psArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -StartIfStopped -Port $Port"

        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $psArgs -WorkingDirectory $WorkspaceRoot
        $startAt = (Get-Date).Date.AddMinutes([math]::Ceiling(((Get-Date) - (Get-Date).Date).TotalMinutes))
        if ($startAt -lt (Get-Date)) { $startAt = (Get-Date).AddMinutes(1) }
        $trigger = New-ScheduledTaskTrigger -Once -At $startAt -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden

        try {
            if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Info "Existing task '$TaskName' removed."
            }
            Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
            Write-Info "Task '$TaskName' registered. It will run every $IntervalMinutes minutes."
            Write-Info "Start now: Start-ScheduledTask -TaskName '$TaskName'"
        }
        catch {
            Write-Err "Failed to register task: $($_.Exception.Message)"
            exit 1
        }
        exit 0
    }
    else {
        Write-Info "Unregistering scheduled task '$TaskName'"
        try {
            if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Info "Task '$TaskName' removed."
            }
            else { Write-Warn "Task '$TaskName' not found." }
        }
        catch {
            Write-Err "Failed to unregister task: $($_.Exception.Message)"
            exit 1
        }
        exit 0
    }
}

# Default behaviour: if no explicit mode, ensure once
if (-not $CheckOnly -and -not $StartIfStopped) {
    $StartIfStopped = $true
}

$online = Test-OriginalDataHealth -Port $Port
if ($online) {
    Write-Info "Original Data API is ONLINE on port $Port."
    exit 0
}

if ($CheckOnly) {
    Write-Err "Original Data API is OFFLINE on port $Port."
    exit 2
}

if ($StartIfStopped) {
    Write-Warn "Original Data API OFFLINE. Attempting to start..."
    Start-OriginalDataApi -Port $Port
    if (Test-OriginalDataHealth -Port $Port) {
        Write-Info "Original Data API is ONLINE after start."
        exit 0
    }
    else {
        Write-Err "Original Data API failed to come online after start attempt."
        exit 3
    }
}

