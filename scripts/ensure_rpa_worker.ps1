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
    # Mutex-based lock to prevent race condition (cross-process)
    $mutexName = 'Global\RPAWorkerEnsureMutex'
    $mutex = $null
    $mutexAcquired = $false
    
    try {
        $mutex = New-Object System.Threading.Mutex($false, $mutexName)
        $mutexAcquired = $mutex.WaitOne(10000)  # 10 second timeout
        
        if (-not $mutexAcquired) {
            Write-Warning "Failed to acquire mutex after 10s. Another instance may be running."
            exit 1
        }
    } catch {
        Write-Warning "Failed to create/acquire mutex: $_"
        exit 1
    }
    
    # Worker PID file for additional safety
    $pidFile = Join-Path $env:TEMP 'rpa_worker.pid'
    
    # Discover processes running rpa_worker.py
    $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
    
    # Check PID file validity
    if ((Test-Path -LiteralPath $pidFile) -and -not $running) {
        Write-Warning "Stale PID file found. Removing."
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }

    if ($KillAll) {
        if (-not $running) { 
            if ($mutexAcquired -and $mutex) { $mutex.ReleaseMutex(); $mutex.Dispose() }
            Write-Host 'No RPA worker processes found to kill.' -ForegroundColor Yellow
            exit 0 
        }
        $pids = $running | Select-Object -ExpandProperty ProcessId
        Write-Host ("Killing all RPA workers: {0}" -f ($pids -join ',')) -ForegroundColor Yellow
        if (-not $DryRun) { $pids | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {} } }
        if ($mutexAcquired -and $mutex) { $mutex.ReleaseMutex(); $mutex.Dispose() }
        exit 0
    }

    if ($EnforceSingle -and $running) {
        # Keep newest MaxWorkers, terminate the rest
        $sorted = @($running | Sort-Object -Property CreationDate -Descending)
        $keep = @($sorted | Select-Object -First ([Math]::Max(1, $MaxWorkers)))
        $kill = @($sorted | Select-Object -Skip ([Math]::Max(1, $MaxWorkers)))
        
        if ($kill.Count -gt 0) {
            $killPids = @($kill | Select-Object -ExpandProperty ProcessId)
            Write-Host ("Enforcing single worker: keeping {0}, killing {1}" -f (($keep | Select-Object -ExpandProperty ProcessId) -join ','), ($killPids -join ',')) -ForegroundColor Yellow
            if (-not $DryRun) { 
                $killPids | ForEach-Object { 
                    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch { Write-Warning "Failed to kill PID ${_}: $($_.Exception.Message)" } 
                }
            }
            # Refresh running list after kills
            Start-Sleep -Milliseconds 500
            $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
        }
        
        # After enforcing, exit without starting new worker
        if ($mutexAcquired -and $mutex) { $mutex.ReleaseMutex(); $mutex.Dispose() }
        exit 0
    }

    if ($running) {
        if ($mutexAcquired -and $mutex) { $mutex.ReleaseMutex(); $mutex.Dispose() }
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
    else { 
        $proc = [System.Diagnostics.Process]::Start($psi)
        if ($proc) {
            # Save PID to file
            $proc.Id | Out-File -FilePath $pidFile -Encoding ASCII -Force
        }
    }
    Start-Sleep -Milliseconds 400

    # Re-check
    $running2 = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
    
    # Release mutex
    if ($mutexAcquired -and $mutex) { $mutex.ReleaseMutex(); $mutex.Dispose() }
    
    if ($running2) {
        Write-Host ("RPA worker started (PID(s): {0})" -f (($running2 | Select-Object -ExpandProperty ProcessId) -join ',')) -ForegroundColor Green
        exit 0
    }
    else {
        throw 'Failed to start RPA worker.'
    }
}
catch {
    # Release mutex on error
    if ($mutexAcquired -and $mutex) { 
        try { $mutex.ReleaseMutex(); $mutex.Dispose() } catch {}
    }
    Write-Error $_.Exception.Message
    exit 1
}
