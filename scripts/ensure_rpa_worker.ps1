#Requires -Version 5.1
<##
.SYNOPSIS
    Ensure the RPA worker process is running and healthy.

.DESCRIPTION
    Uses a JSON configuration file to control how the RPA worker is launched, how health checks
    are performed, and how often restarts are permitted. Logs are written to
    outputs/ensure_rpa_worker.log (UTF-8, no BOM) with 1MB rotation.

.PARAMETER Config
    Optional path to configuration file (defaults to configs/rpa_worker.json)

.PARAMETER ForceRestart
    Force a restart even if the worker appears healthy.

.PARAMETER Stop
    Stop any running worker processes and exit.

.PARAMETER Status
    Print status (running/healthy) and exit.

.PARAMETER DryRun
    Preview actions without performing them.
#>

param(
    [string]$Config = "C:\workspace\agi\configs\rpa_worker.json",
    [switch]$ForceRestart,
    [switch]$Stop,
    [switch]$Status,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$logPath = Join-Path $workspaceRoot "outputs\ensure_rpa_worker.log"
$summaryPath = Join-Path $workspaceRoot "outputs\rpa_worker_status.txt"
$historyPath = Join-Path $workspaceRoot "outputs\rpa_worker_restart_history.json"

function Out-FileUtf8NoBomAppend {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    $sw = New-Object System.IO.StreamWriter($Path, $true, $enc)
    try { $sw.WriteLine($Text) } finally { $sw.Dispose() }
}

function Rotate-LogIfNeeded {
    param([string]$Path, [int64]$MaxBytes = 1MB)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        $info = Get-Item -LiteralPath $Path
        if ($info.Length -le $MaxBytes) { return }
        $backup = "$Path.1"
        if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue }
        Rename-Item -LiteralPath $Path -NewName (Split-Path -Leaf $backup) -Force
    } catch {}
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))] [$Level] $Message"
    Write-Host $line
    Rotate-LogIfNeeded -Path $logPath
    Out-FileUtf8NoBomAppend -Path $logPath -Text $line
    Set-Content -LiteralPath $summaryPath -Value $line -Encoding UTF8
}

function Load-Config($path) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Config file not found: $path"
    }
    try {
        $text = Get-Content -LiteralPath $path -Raw
        return $text | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Failed to parse config $path: $($_.Exception.Message)"
    }
}

function Get-WorkerProcesses($match) {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like $match }
}

function Stop-WorkerProcesses($procs, $dryRun) {
    if (-not $procs) { Write-Log "No RPA worker processes to stop." "WARN"; return }
    $pids = $procs | Select-Object -ExpandProperty ProcessId
    Write-Log "Stopping worker PID(s): $($pids -join ',')" "WARN"
    if (-not $dryRun) {
        foreach ($pid in $pids) {
            try { Stop-Process -Id $pid -Force -ErrorAction Stop } catch { Write-Log "Failed to stop PID $pid: $($_.Exception.Message)" "ERROR" }
        }
    }
}

function Test-Health($cfg) {
    $mode = ($cfg.health.mode ?? "none").ToLower()
    if ($mode -eq "none") { return $true }
    if ($mode -eq "http") {
        try {
            $timeout = [int]($cfg.health.timeout ?? 2)
            $result = Invoke-RestMethod -Uri $cfg.health.endpoint -TimeoutSec $timeout -ErrorAction Stop
            if ($result.status -and $result.status -match "ok|healthy") { return $true }
            return $false
        }
        catch {
            Write-Log "Health check failed: $($_.Exception.Message)" "WARN"
            return $false
        }
    }
    return $true
}

function Update-RestartHistory($path, $dryRun) {
    $history = @()
    if (Test-Path -LiteralPath $path) {
        try { $history = (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json) } catch { $history = @() }
    }
    $now = Get-Date
    $filtered = @($history | Where-Object { $_ -and ([DateTime]$_) -ge $now.AddSeconds(-($global:RestartWindow)) })
    $filtered += $now.ToString("o")
    if (-not $dryRun) {
        $filtered | ConvertTo-Json | Set-Content -LiteralPath $path -Encoding UTF8
    }
    return $filtered.Count
}

function Check-RestartLimit($path) {
    if (-not (Test-Path -LiteralPath $path)) { return 0 }
    try { $history = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch { return 0 }
    $now = Get-Date
    return (@($history | Where-Object { $_ -and ([DateTime]$_) -ge $now.AddSeconds(-($global:RestartWindow)) })).Count
}

$configObj = Load-Config $Config
$pythonPath = $configObj.python
if (-not $pythonPath -or -not (Test-Path -LiteralPath (Join-Path $workspaceRoot $pythonPath))) {
    $pythonPath = "python"
} else {
    $pythonPath = Join-Path $workspaceRoot $pythonPath
}
$command = Join-Path $workspaceRoot ($configObj.command ?? "fdo_agi_repo\integrations\rpa_worker.py")
if (-not (Test-Path -LiteralPath $command)) {
    throw "Worker command not found: $command"
}
$argumentList = @()
if ($configObj.args) { $argumentList = $configObj.args }
$commandLineMatch = "*" + (Split-Path $command -Leaf) + "*"

$global:MaxRestarts = [int]($configObj.restart_policy.max_restarts ?? 3)
$global:RestartWindow = [int]($configObj.restart_policy.window_seconds ?? 600)

$mutex = $null
$mutexName = "Global\EnsureRPAWorkerMutex"
try {
    $mutex = New-Object System.Threading.Mutex($false, $mutexName)
    if (-not $mutex.WaitOne(10000)) {
        Write-Log "Could not acquire mutex. Another ensure operation is running." "WARN"
        exit 1
    }
}
catch {
    Write-Log "Failed to create/acquire mutex: $($_.Exception.Message)" "ERROR"
    exit 1
}

try {
    $procs = Get-WorkerProcesses $commandLineMatch

    if ($Stop) {
        Stop-WorkerProcesses $procs $DryRun
        return
    }

    if ($Status) {
        if ($procs) {
            $pids = $procs | Select-Object -ExpandProperty ProcessId
            $healthy = Test-Health $configObj
            Write-Log "Worker status: RUNNING (PID $($pids -join ','), healthy=$healthy)" "INFO"
        }
        else {
            Write-Log "Worker status: NOT RUNNING" "WARN"
        }
        return
    }

    $shouldRestart = $ForceRestart

    if ($procs -and -not $ForceRestart) {
        $healthy = Test-Health $configObj
        if ($healthy) {
            Write-Log "Worker already running and healthy." "INFO"
            return
        }
        else {
            Write-Log "Worker unhealthy. Will restart." "WARN"
            $shouldRestart = $true
        }
    }

    if ($procs -and $shouldRestart) {
        Stop-WorkerProcesses $procs $DryRun
        Start-Sleep -Milliseconds 500
        $procs = @()
    }

    if ($procs -and -not $shouldRestart) {
        Write-Log "Worker running but health unknown; no restart requested." "INFO"
        return
    }

    $recentRestarts = Check-RestartLimit $historyPath
    if ($recentRestarts -ge $global:MaxRestarts) {
        Write-Log "Restart limit reached ($recentRestarts within $global:RestartWindow s). Skipping restart." "ERROR"
        return
    }

    Write-Log "Starting RPA worker: $pythonPath $($argumentList -join ' ')" "INFO"
    if (-not $DryRun) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $pythonPath
        $psi.WorkingDirectory = $workspaceRoot
        $psi.Arguments = "`"$command`" " + ($argumentList -join ' ')
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        try {
            $proc = [System.Diagnostics.Process]::Start($psi)
            if ($proc) {
                Write-Log "Worker started PID=$($proc.Id)" "SUCCESS"
                $count = Update-RestartHistory -path $historyPath -dryRun:$false
                Write-Log "Restart history count in window: $count" "INFO"
            }
            else {
                Write-Log "Process start returned null." "ERROR"
            }
        }
        catch {
            Write-Log "Failed to start worker: $($_.Exception.Message)" "ERROR"
            return
        }
    }
    else {
        Write-Log "Dry-run: worker start skipped." "INFO"
    }
}
finally {
    if ($mutex) {
        try { $mutex.ReleaseMutex(); $mutex.Dispose() } catch {}
    }
}
