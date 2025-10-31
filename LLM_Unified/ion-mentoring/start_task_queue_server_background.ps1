<#
.SYNOPSIS
    Start Task Queue Server in background for Gitko-Comet collaboration

.DESCRIPTION
    Starts task_queue_server.py on port 8091 in background PowerShell job.
    Checks if already running before starting new instance.

.PARAMETER Port
    Server port (default: 8091)

.PARAMETER KillExisting
    Kill existing server process before starting new one

.EXAMPLE
    .\start_task_queue_server_background.ps1
    .\start_task_queue_server_background.ps1 -KillExisting
#>

param(
    [int]$Port = 8091,
    [switch]$KillExisting
)

$ErrorActionPreference = "Stop"

# Fix path - ion-mentoring is already inside LLM_Unified
$ionMentoringDir = $PSScriptRoot
$llmUnifiedRoot = Split-Path -Parent $ionMentoringDir
$nasBackupRoot = Split-Path -Parent $llmUnifiedRoot
${venvPythonCandidates} = @(
    (Join-Path $ionMentoringDir ".venv\Scripts\python.exe"),
    (Join-Path $llmUnifiedRoot ".venv\Scripts\python.exe")
)
$venvPython = $null
foreach ($cand in $venvPythonCandidates) {
    if (Test-Path $cand) { $venvPython = $cand; break }
}
$serverScript = Join-Path $ionMentoringDir "task_queue_server.py"

# Check if server already running (by port or process)
function Test-ServerHealth {
    param([int]$p)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/api/health" -TimeoutSec 2 -ErrorAction Stop
        return $r.StatusCode -eq 200
    }
    catch { return $false }
}

$owningProc = $null
try {
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn -and $conn.OwningProcess -gt 4) {
        $owningProc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    }
}
catch {}

if (-not $owningProc) {
    # Fallback: use CIM to find python with script name in commandline
    try {
        $cim = Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*task_queue_server.py*' } | Select-Object -First 1
        if ($cim) { $owningProc = Get-Process -Id $cim.ProcessId -ErrorAction SilentlyContinue }
    }
    catch {}
}

if ($owningProc) {
    $healthy = Test-ServerHealth -p $Port
    if ($KillExisting) {
        Write-Host "🛑 Killing existing task queue server (PID: $($owningProc.Id))..." -ForegroundColor Yellow
        try { Stop-Process -Id $owningProc.Id -Force -ErrorAction Stop } catch {}
        Start-Sleep -Seconds 2
    }
    elseif ($healthy) {
        Write-Host "[OK] Task queue server already running (PID: $($owningProc.Id))" -ForegroundColor Green
        Write-Host "   API Base: http://localhost:$Port/api" -ForegroundColor Cyan
        Write-Host "   Use -KillExisting to restart" -ForegroundColor Gray
        exit 0
    }
    else {
        Write-Host "[WARN] Process detected (PID: $($owningProc.Id)) but health check failed. Will attempt restart." -ForegroundColor Yellow
        try { Stop-Process -Id $owningProc.Id -Force -ErrorAction SilentlyContinue } catch {}
        Start-Sleep -Seconds 2
    }
}

# Check if port is available (consider only LISTEN state)
$listenConn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listenConn) {
    Write-Host "[WARN] Port $Port is already LISTENING by PID $($listenConn.OwningProcess)" -ForegroundColor Red
    if ($KillExisting -and $listenConn.OwningProcess -gt 4) {
        try {
            Write-Host "Attempting to free port by killing PID $($listenConn.OwningProcess)..." -ForegroundColor Yellow
            Stop-Process -Id $listenConn.OwningProcess -Force
            Start-Sleep -Seconds 2
        }
        catch {}
        # re-check
        $listenConn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listenConn) {
            Write-Host "[ERROR] Port still LISTENING after kill attempt." -ForegroundColor Red
            exit 1
        }
    }
    else {
        exit 1
    }
}

# Check if venv Python exists
if (-not $venvPython) {
    Write-Host "[ERROR] Virtual environment not found under:" -ForegroundColor Red
    $venvPythonCandidates | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    Write-Host "   Create venv in 'ion-mentoring\\.venv' (recommended) and install deps (pip install -r requirements.txt)." -ForegroundColor Yellow
    exit 1
}

# Start server in background job
Write-Host "[DEPLOY] Starting task queue server on port $Port..." -ForegroundColor Cyan

$job = Start-Job -ScriptBlock {
    param($pythonPath, $scriptPath, $port)
    & $pythonPath $scriptPath --port $port
} -ArgumentList $venvPython, $serverScript, $Port

# Wait for server to start
Write-Host "[WAIT] Waiting for server to start..." -ForegroundColor Gray
$maxRetries = 10
$retryCount = 0
$serverReady = $false

while ($retryCount -lt $maxRetries) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $serverReady = $true
            break
        }
    }
    catch {
        $retryCount++
    }
}

if ($serverReady) {
    Write-Host "[OK] Task queue server started successfully!" -ForegroundColor Green
    Write-Host "   API Base: http://localhost:$Port/api" -ForegroundColor Cyan
    Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[LOG] To stop the server:" -ForegroundColor Yellow
    Write-Host "   Stop-Job -Id $($job.Id); Remove-Job -Id $($job.Id)" -ForegroundColor Gray
}
else {
    Write-Host "[ERROR] Server failed to start within timeout" -ForegroundColor Red
    Write-Host "   Check job output: Receive-Job -Id $($job.Id)" -ForegroundColor Yellow
    exit 1
}
