# ion-mentoring Cache Dashboard Launcher

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "ion-mentoring Cache Performance Dashboard" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리
$MonitorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $MonitorDir

Write-Host "[INFO] Monitor Directory: $MonitorDir" -ForegroundColor Gray
Write-Host "[INFO] Repo Root: $RepoRoot" -ForegroundColor Gray
Write-Host ""

# Python 가상환경 활성화 (있으면)
$VenvPath = Join-Path $RepoRoot ".venv"
if (Test-Path $VenvPath) {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
    & "$VenvPath\Scripts\Activate.ps1"
}

# Flask 설치 확인
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Yellow
python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INSTALL] Installing Flask..." -ForegroundColor Yellow
    pip install flask
}

# Redis 설치 확인
python -c "import redis" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INSTALL] Installing redis..." -ForegroundColor Yellow
    pip install redis
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Starting Dashboard Server..." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[URL] http://localhost:5001" -ForegroundColor Cyan
Write-Host "[TIP] Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# 대시보드 실행
Set-Location $MonitorDir
python cache_dashboard.py
