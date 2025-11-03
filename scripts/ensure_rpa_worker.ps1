param(
    [string]$Server = 'http://127.0.0.1:8091',
    [double]$Interval = 0.5,
    [ValidateSet('INFO', 'DEBUG', 'WARNING', 'ERROR')]
    [string]$LogLevel = 'INFO',
    [switch]$EnforceSingle,
    [int]$MaxWorkers = 1,
    [switch]$KillAll,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
try {
    # Lock mechanism to prevent race condition
    $lockFile = Join-Path $env:TEMP 'rpa_worker_lock.tmp'
    $lockTimeout = 10  # seconds
    $lockStart = Get-Date
    
    while (Test-Path -LiteralPath $lockFile) {
        if (((Get-Date) - $lockStart).TotalSeconds -gt $lockTimeout) {
            Write-Warning "Lock file timeout after ${lockTimeout}s. Removing stale lock."
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
            break
        }
        Start-Sleep -Milliseconds 100
    }
    
    # Create lock file
    New-Item -ItemType File -Path $lockFile -Force | Out-Null
    
    # Discover processes running rpa_worker.py
    $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }

    if ($KillAll) {
        if (-not $running) { 
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
            Write-Host 'No RPA worker processes found to kill.' -ForegroundColor Yellow
            exit 0 
        }
        $pids = $running | Select-Object -ExpandProperty ProcessId
        Write-Host ("Killing all RPA workers: {0}" -f ($pids -join ',')) -ForegroundColor Yellow
        if (-not $DryRun) { $pids | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {} } }
        Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        exit 0
    }

    if ($EnforceSingle -and $running) {
        # Keep newest MaxWorkers, terminate the rest
        $sorted = $running | Sort-Object -Property CreationDate -Descending
        $keep = $sorted | Select-Object -First ([Math]::Max(1, $MaxWorkers))
        $kill = $sorted | Select-Object -Skip ([Math]::Max(1, $MaxWorkers))
        if ($kill -and $kill.Count -gt 0) {
            $killPids = $kill | Select-Object -ExpandProperty ProcessId
            Write-Host ("Enforcing single worker: keeping {0}, killing {1}" -f (($keep | Select-Object -ExpandProperty ProcessId) -join ','), ($killPids -join ',')) -ForegroundColor Yellow
            if (-not $DryRun) { $killPids | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {} } }
            # Refresh running list after kills
            $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
        }
    }

    if ($running) {
        Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        Write-Host ("RPA worker already running (PID(s): {0})" -f (($running | Select-Object -ExpandProperty ProcessId) -join ',')) -ForegroundColor Green
        exit 0
    }

    $repoRoot = Join-Path $PSScriptRoot '..'
    $fdo = Join-Path $repoRoot 'fdo_agi_repo'
    $pyVenv = Join-Path $fdo '.venv\Scripts\python.exe'
    $pyExe = if (Test-Path -LiteralPath $pyVenv) { $pyVenv } else { 'python' }

    $workerPath = Join-Path $fdo 'integrations\rpa_worker.py'
    if (-not (Test-Path -LiteralPath $workerPath)) {
        throw "Worker script not found: $workerPath"
    }

    $procArgs = @($workerPath, '--server', $Server, '--interval', [string]$Interval, '--log-level', $LogLevel)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pyExe
    $psi.Arguments = ($procArgs -join ' ')
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError = $false

    if ($DryRun) { Write-Host "DRY-RUN: would start worker: $($psi.FileName) $($psi.Arguments)" -ForegroundColor DarkCyan }
    else { [void][System.Diagnostics.Process]::Start($psi) }
    Start-Sleep -Milliseconds 400

    # Re-check
    $running2 = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
    
    # Release lock
    Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
    
    if ($running2) {
        Write-Host ("RPA worker started (PID(s): {0})" -f (($running2 | Select-Object -ExpandProperty ProcessId) -join ',')) -ForegroundColor Green
        exit 0
    }
    else {
        throw 'Failed to start RPA worker.'
    }
}
catch {
    # Release lock on error
    $lockFile = Join-Path $env:TEMP 'rpa_worker_lock.tmp'
    Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
    Write-Error $_.Exception.Message
    exit 1
}
