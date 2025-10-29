<#
.SYNOPSIS
    웹 대시보드 생성 (JSON + HTML)

.DESCRIPTION
    AGI 운영 대시보드를 웹 브라우저로 볼 수 있도록 JSON 데이터를 생성하고
    HTML 대시보드를 엽니다.

.PARAMETER Hours
    분석할 시간 범위 (기본: 6시간)

.PARAMETER NoBrowser
    생성 후 브라우저를 열지 않음 (기본: 자동으로 열림)

.EXAMPLE
    .\generate_web_dashboard.ps1
    # 기본 6시간 데이터로 대시보드 생성 및 브라우저 열기

.EXAMPLE
    .\generate_web_dashboard.ps1 -Hours 24
    # 24시간 데이터로 대시보드 생성

.EXAMPLE
    .\generate_web_dashboard.ps1 -NoBrowser
    # 브라우저를 열지 않고 데이터만 생성
#>

param(
    [double]$Hours = 6.0,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

# 프로젝트 루트 찾기
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir

# 출력 디렉토리 확인
$outputDir = Join-Path $repoRoot "outputs"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Python 가상환경 경로
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] Python venv not found: $venvPython" -ForegroundColor Red
    exit 1
}

# ops_dashboard.py 경로
$dashboardScript = Join-Path $scriptDir "ops_dashboard.py"
if (-not (Test-Path $dashboardScript)) {
    Write-Host "[ERROR] ops_dashboard.py not found: $dashboardScript" -ForegroundColor Red
    exit 1
}

# JSON 데이터 생성
$jsonPath = Join-Path $outputDir "dashboard_status.json"
Write-Host "[INFO] Generating JSON data (last $Hours hours)..." -ForegroundColor Cyan

try {
    & $venvPython $dashboardScript --json --hours $Hours > $jsonPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] JSON generation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    Write-Host "[OK] JSON generated: $jsonPath" -ForegroundColor Green
    
}
catch {
    Write-Host "[ERROR] JSON generation error: $_" -ForegroundColor Red
    exit 1
}

# HTML 대시보드 경로
$htmlPath = Join-Path $outputDir "dashboard.html"

if (-not (Test-Path $htmlPath)) {
    Write-Host "[WARN] HTML dashboard not found: $htmlPath" -ForegroundColor Yellow
    Write-Host "       Please create outputs/dashboard.html first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] HTML dashboard: $htmlPath" -ForegroundColor Green

# 브라우저 열기
if ($NoBrowser) {
    Write-Host "[INFO] -NoBrowser flag set, not opening browser." -ForegroundColor Gray
}
else {
    Write-Host "[INFO] Opening browser..." -ForegroundColor Cyan
    Start-Process $htmlPath
}

Write-Host ""
Write-Host "======================================" -ForegroundColor DarkGray
Write-Host "Web Dashboard Ready" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "JSON: $jsonPath" -ForegroundColor White
Write-Host "HTML: $htmlPath" -ForegroundColor White
Write-Host ""
Write-Host "Auto-refresh: Every 30 seconds" -ForegroundColor Cyan
Write-Host "Manual refresh: Re-run this script or press F5 in browser" -ForegroundColor Gray
Write-Host ""
