# AGI Dashboard 시작 스크립트 (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🚀 AGI 실시간 모니터링 대시보드 시작..." -ForegroundColor Cyan

# 현재 디렉토리 확인
$MonitorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $MonitorDir

Write-Host "📁 Monitor Directory: $MonitorDir" -ForegroundColor Gray
Write-Host "📁 Repo Root: $RepoRoot" -ForegroundColor Gray

# Python 가상환경 활성화 (있으면)
$VenvPath = Join-Path $RepoRoot ".venv"
if (Test-Path $VenvPath) {
    Write-Host "🐍 가상환경 활성화: $VenvPath" -ForegroundColor Yellow
    & "$VenvPath\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  가상환경 없음. 시스템 Python 사용" -ForegroundColor Yellow
}

# Flask 설치 확인
try {
    python -c "import flask" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Flask 설치 중..." -ForegroundColor Yellow
        pip install flask
    }
} catch {
    Write-Host "📦 Flask 설치 중..." -ForegroundColor Yellow
    pip install flask
}

# 대시보드 실행
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "🎉 AGI 대시보드가 시작됩니다!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "📊 브라우저에서 열기: http://localhost:5000" -ForegroundColor Cyan
Write-Host "⏱️  자동 새로고침: 10초마다" -ForegroundColor Gray
Write-Host "🛑 종료하려면: Ctrl+C" -ForegroundColor Gray
Write-Host ""

# dashboard.py 실행
Set-Location $MonitorDir
python dashboard.py
