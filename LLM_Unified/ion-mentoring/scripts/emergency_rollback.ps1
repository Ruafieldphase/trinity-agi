# 긴급 롤백 스크립트
# 목적: 카나리 배포에 문제 발생 시 빠른 롤백 수행

param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectId = "naeda-genesis",
    [switch]$Force,
    [switch]$SkipConfirmation
)

$ErrorActionPreference = 'Stop'

Write-Host "`n=== EMERGENCY ROLLBACK ===" -ForegroundColor Red
Write-Host "This will roll back canary deployment to 0%" -ForegroundColor Yellow
Write-Host "Traffic will be restored to legacy service`n" -ForegroundColor Yellow

# 현재 상태 확인
Write-Host "[1/4] Checking current health status..." -ForegroundColor Cyan
$checkScript = Join-Path $PSScriptRoot 'check_monitoring_status.ps1'
if (Test-Path $checkScript) {
    try {
        $tmpJson = [System.IO.Path]::GetTempFileName()
        $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $checkScript,
            '-ReturnExitCode', '-OutJson', $tmpJson
        ) -WindowStyle Hidden -Wait -PassThru -NoNewWindow
        
        if ($proc.ExitCode -eq 0) {
            Write-Host "  Status: HEALTHY" -ForegroundColor Green
            if (-not $Force) {
                Write-Host "  System appears healthy. Use -Force to rollback anyway." -ForegroundColor Yellow
                exit 0
            }
            else {
                Write-Host "  -Force specified, proceeding with rollback..." -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  Status: UNHEALTHY - rollback recommended" -ForegroundColor Red
        }
        
        if (Test-Path $tmpJson) {
            $status = Get-Content $tmpJson | ConvertFrom-Json
            Write-Host ("  Error Rate: {0}%, P95: {1}ms" -f $status.error_rate_percent, $status.p95_ms) -ForegroundColor Gray
        }
    }
    catch {
        Write-Warning "Could not check current status: $($_.Exception.Message)"
    }
    finally {
        if (Test-Path $tmpJson) { Remove-Item $tmpJson -Force -ErrorAction SilentlyContinue }
    }
}

# 확인 프롬프트
if (-not $SkipConfirmation) {
    Write-Host "`nAre you sure you want to rollback? (yes/no): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne 'yes') {
        Write-Host "Rollback cancelled." -ForegroundColor Cyan
        exit 0
    }
}

# 롤백 실행
Write-Host "`n[2/4] Executing rollback..." -ForegroundColor Cyan
$rollbackScript = Join-Path $PSScriptRoot 'rollback_phase4_canary.ps1'
if (-not (Test-Path $rollbackScript)) {
    Write-Error "Rollback script not found: $rollbackScript"
    exit 1
}

try {
    $params = @('-ProjectId', $ProjectId, '-AutoApprove')
    & $rollbackScript @params
    if ($LASTEXITCODE -ne 0) {
        throw "Rollback script exited with code $LASTEXITCODE"
    }
    Write-Host "  ✓ Rollback completed" -ForegroundColor Green
}
catch {
    Write-Error "Rollback failed: $($_.Exception.Message)"
    exit 1
}

# 재확인
Write-Host "`n[3/4] Waiting 30 seconds for traffic to stabilize..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "`n[4/4] Verifying post-rollback status..." -ForegroundColor Cyan
if (Test-Path $checkScript) {
    try {
        $proc2 = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $checkScript
        ) -WindowStyle Hidden -Wait -PassThru -NoNewWindow
        
        if ($proc2.ExitCode -eq 0) {
            Write-Host "  ✓ Post-rollback status: HEALTHY" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ Post-rollback status: UNHEALTHY" -ForegroundColor Yellow
            Write-Host "  Manual investigation required." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Warning "Could not verify post-rollback status: $($_.Exception.Message)"
    }
}

Write-Host "`n=== ROLLBACK COMPLETE ===" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Monitor logs: LLM_Unified/ion-mentoring/logs/" -ForegroundColor White
Write-Host "  2. Review metrics in Cloud Console" -ForegroundColor White
Write-Host "  3. Investigate root cause before re-deploying canary`n" -ForegroundColor White

exit 0
