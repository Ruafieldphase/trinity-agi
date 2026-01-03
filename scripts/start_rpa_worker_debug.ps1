# RPA Worker 시작 스크립트 (로그 파일 출력)
param(
    [string] $ServerUrl = "http://127.0.0.1:8091",
    [float] $Interval = 0.5,
    [string] $LogLevel = "DEBUG"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Join-Path $WorkspaceRoot "fdo_agi_repo"
$OutputsDir = Join-Path $WorkspaceRoot "outputs"
$LogFile = Join-Path $OutputsDir "rpa_worker_debug.log"
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvScriptsDir = Join-Path $VenvDir "Scripts"
$VenvPython = Join-Path $VenvScriptsDir "python.exe"
$IntegrationsDir = Join-Path $RepoRoot "integrations"
$WorkerScript = Join-Path $IntegrationsDir "rpa_worker.py"

Write-Host "[DEBUG] Starting RPA Worker..." -ForegroundColor Cyan
Write-Host "[DEBUG] Server: $ServerUrl" -ForegroundColor Gray
Write-Host "[DEBUG] Interval: $Interval" -ForegroundColor Gray
Write-Host "[DEBUG] Log Level: $LogLevel" -ForegroundColor Gray
Write-Host "[DEBUG] Log File: $LogFile" -ForegroundColor Gray

# Ensure output directory exists
$null = New-Item -Path (Split-Path $LogFile -Parent) -ItemType Directory -Force -ErrorAction SilentlyContinue

# Start worker and redirect output
$proc = Start-Process -FilePath $VenvPython `
    -ArgumentList $WorkerScript, "--server", $ServerUrl, "--interval", $Interval, "--log-level", $LogLevel `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError "$LogFile.err"

Write-Host "[DEBUG] Worker started (PID: $($proc.Id))" -ForegroundColor Green
Write-Host "[DEBUG] Monitor log: Get-Content '$LogFile' -Wait" -ForegroundColor Yellow