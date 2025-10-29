# Lumen Gateway 배포 자동 모니터링 실행 스크립트
# PowerShell 래퍼

param(
    [switch]$Wait = $false,
    [int]$MaxWaitMinutes = 10,
    [switch]$SkipHealthCheck = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$monitorScript = Join-Path $scriptDir "monitor_deployment.py"

Write-Host "== Lumen Gateway Deployment Monitor ==" -ForegroundColor Cyan
Write-Host ""

# Python 환경 확인
if (-not (Test-Path $pythonExe)) {
    Write-Host "Python venv not found: $pythonExe" -ForegroundColor Red
    Write-Host "Please create the virtual environment first." -ForegroundColor Yellow
    exit 1
}

# GitHub CLI 확인 (없거나 인증 불가 시 빠른 헬스체크로 폴백)
$usingGh = $true
try {
    $ghVersion = gh --version 2>&1 | Select-Object -First 1
    Write-Host "GitHub CLI: $ghVersion" -ForegroundColor Green
}
catch {
    Write-Host "GitHub CLI (gh) not found. Falling back to quick health-check only." -ForegroundColor Yellow
    $usingGh = $false
}

if ($usingGh) {
    # GitHub CLI 인증 확인 (비대화형 폴백 지원)
    try {
        gh auth status 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "GitHub CLI not authenticated. Falling back to quick health-check only." -ForegroundColor Yellow
            $usingGh = $false
        }
        else {
            Write-Host "GitHub authentication OK" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Could not verify GitHub auth status. Falling back to quick health-check only." -ForegroundColor Yellow
        $usingGh = $false
    }
}

Write-Host ""
Write-Host "Run options:" -ForegroundColor Cyan
Write-Host "  - Wait mode: $Wait" -ForegroundColor Gray
Write-Host "  - Max wait (minutes): $MaxWaitMinutes" -ForegroundColor Gray
Write-Host "  - Skip health check: $SkipHealthCheck" -ForegroundColor Gray
Write-Host ""

# 환경변수 설정
$env:PYTHONIOENCODING = "utf-8"

# Python 스크립트 실행
try {
    if (-not $usingGh) {
        $env:SKIP_GH_CHECK = "1"
        Write-Host "SKIP_GH_CHECK=1 set for quick health-check mode" -ForegroundColor Yellow
    }
    & $pythonExe $monitorScript
    $exitCode = $LASTEXITCODE
    
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "Deployment monitoring and validation completed successfully." -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Check reports in outputs directory" -ForegroundColor Gray
        Write-Host "  2. Prepare production deploy (if success)" -ForegroundColor Gray
        Write-Host "  3. Update ION API LUMEN_GATEWAY_URL" -ForegroundColor Gray
    }
    else {
        Write-Host "Issues detected during deployment validation." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  1. Check logs in outputs directory" -ForegroundColor Gray
        Write-Host "  2. Review GitHub Actions workflow logs" -ForegroundColor Gray
        Write-Host "  3. Review Cloud Run logs" -ForegroundColor Gray
        Write-Host "  4. See LUMEN_DEPLOY_TROUBLESHOOTING.md" -ForegroundColor Gray
    }
    
    exit $exitCode
    
}
catch {
    Write-Host "Error during execution: $_" -ForegroundColor Red
    exit 1
}
