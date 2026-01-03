param(
    [int]$Port = 8091
)

$ErrorActionPreference = 'Stop'

function Test-ServerOnline {
    param([int]$Port)
    try {
        $uri = "http://127.0.0.1:$Port/api/health"
        $resp = Invoke-WebRequest -Uri $uri -TimeoutSec 2 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

try {
    $workspace = Split-Path -Parent $PSCommandPath | Split-Path -Parent

    if (Test-ServerOnline -Port $Port) {
        Write-Host "Task Queue Server is already ONLINE on :$Port" -ForegroundColor Green
        exit 0
    }

    $ionPath = Join-Path $workspace 'LLM_Unified/ion-mentoring'
    if (-not (Test-Path -LiteralPath $ionPath)) {
        Write-Host "ion-mentoring directory not found: $ionPath" -ForegroundColor Yellow
        exit 1
    }

    $venvPy = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'

    if (Test-Path -LiteralPath $venvPy) {
        Write-Host "Starting Task Queue Server with repo venv python..." -ForegroundColor DarkGray
        Start-Process -FilePath $venvPy -ArgumentList @('task_queue_server.py', '--port', "$Port") -WorkingDirectory $ionPath -WindowStyle Hidden -PassThru | Out-Null
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        Write-Host "Starting Task Queue Server with 'py -3'..." -ForegroundColor DarkGray
        Start-Process -FilePath 'py' -ArgumentList @('-3', 'task_queue_server.py', '--port', "$Port") -WorkingDirectory $ionPath -WindowStyle Hidden -PassThru | Out-Null
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Starting Task Queue Server with 'python'..." -ForegroundColor DarkGray
        Start-Process -FilePath 'python' -ArgumentList @('task_queue_server.py', '--port', "$Port") -WorkingDirectory $ionPath -WindowStyle Hidden -PassThru | Out-Null
    }
    else {
        Write-Host "No Python interpreter found to start Task Queue Server." -ForegroundColor Red
        exit 1
    }

    Start-Sleep -Seconds 2

    if (Test-ServerOnline -Port $Port) {
        Write-Host "Task Queue Server started and ONLINE on :$Port" -ForegroundColor Green
        exit 0
    }
    else {
        Write-Host "Task Queue Server did not respond to health check on :$Port" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "(non-fatal) ensure_task_queue_server.ps1: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
}