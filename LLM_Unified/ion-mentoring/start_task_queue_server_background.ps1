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
$venvPython = Join-Path $llmUnifiedRoot ".venv\Scripts\python.exe"
$serverScript = Join-Path $ionMentoringDir "task_queue_server.py"

# Check if server already running
$existingProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like "*task_queue_server.py*" }

if ($existingProcess) {
    if ($KillExisting) {
        Write-Host "🛑 Killing existing task queue server (PID: $($existingProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $existingProcess.Id -Force
        Start-Sleep -Seconds 2
    }
    else {
        Write-Host "✅ Task queue server already running (PID: $($existingProcess.Id))" -ForegroundColor Green
        Write-Host "   Use -KillExisting to restart" -ForegroundColor Gray
        exit 0
    }
}

# Check if port is available
$portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️ Port $Port already in use" -ForegroundColor Red
    exit 1
}

# Check if venv Python exists
if (-not (Test-Path $venvPython)) {
    Write-Host "❌ Virtual environment not found: $venvPython" -ForegroundColor Red
    Write-Host "   Run setup script first" -ForegroundColor Yellow
    exit 1
}

# Start server in background job
Write-Host "🚀 Starting task queue server on port $Port..." -ForegroundColor Cyan

$job = Start-Job -ScriptBlock {
    param($pythonPath, $scriptPath, $port)
    & $pythonPath $scriptPath --port $port
} -ArgumentList $venvPython, $serverScript, $Port

# Wait for server to start
Write-Host "⏳ Waiting for server to start..." -ForegroundColor Gray
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
    Write-Host "✅ Task queue server started successfully!" -ForegroundColor Green
    Write-Host "   API Base: http://localhost:$Port/api" -ForegroundColor Cyan
    Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 To stop the server:" -ForegroundColor Yellow
    Write-Host "   Stop-Job -Id $($job.Id); Remove-Job -Id $($job.Id)" -ForegroundColor Gray
}
else {
    Write-Host "❌ Server failed to start within timeout" -ForegroundColor Red
    Write-Host "   Check job output: Receive-Job -Id $($job.Id)" -ForegroundColor Yellow
    exit 1
}
