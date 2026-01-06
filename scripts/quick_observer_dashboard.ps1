<# 
.SYNOPSIS
    Stream Observer + Monitoring Dashboard 통합 실행
.DESCRIPTION
    Stream Observer 텔레메트리 수집 후 통합 대시보드 생성
#>
param(
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
$ws = $PSScriptRoot | Split-Path -Parent

Write-Host "🔍 Stream Observer + Dashboard Integration" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. Observer 실행 확인
Write-Host "`n▶ Observer 상태 확인 중..." -ForegroundColor Yellow
& "$ws\scripts\ensure_observer_telemetry.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Observer 시작 실패" -ForegroundColor Red
    exit 1
}

# 2. 통합 스크립트 실행
Write-Host "`n▶ 통합 대시보드 생성 중..." -ForegroundColor Yellow
$pyExe = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path $pyExe)) { $pyExe = "python" }

& $pyExe "$ws\scripts\integrate_stream_observer_dashboard.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 통합 스크립트 실패" -ForegroundColor Red
    exit 1
}

$dashboardPath = "$ws\outputs\monitoring_dashboard_latest.html"
if (!(Test-Path $dashboardPath)) {
    Write-Host "❌ Dashboard 파일이 생성되지 않음" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ 통합 완료!" -ForegroundColor Green
Write-Host "📁 $dashboardPath" -ForegroundColor Cyan

if ($OpenBrowser) {
    Write-Host "`n🌐 브라우저에서 열기..." -ForegroundColor Cyan
    Start-Process $dashboardPath
}

exit 0