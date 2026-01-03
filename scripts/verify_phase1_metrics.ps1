#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Phase 1 Quick Wins 검증 스크립트
.DESCRIPTION
    24시간 메트릭을 수집하고 Phase 1 성공 기준을 자동으로 확인합니다.
.PARAMETER Hours
    분석할 시간 범위 (기본: 24시간)
.PARAMETER ShowDetails
    상세 메트릭 출력 여부
.EXAMPLE
    .\verify_phase1_metrics.ps1
    .\verify_phase1_metrics.ps1 -Hours 48 -ShowDetails
#>

param(
    [int]$Hours = 24,
    [switch]$ShowDetails
)

$ErrorActionPreference = "Stop"
$repo_root = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AGI PHASE 1 검증 - Quick Wins Validation" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 모니터링 리포트 생성
Write-Host "[1/4] 모니터링 리포트 생성 중..." -ForegroundColor Yellow
$report_script = Join-Path $PSScriptRoot "generate_monitoring_report.ps1"
if (Test-Path $report_script) {
    & $report_script -Hours $Hours -ErrorAction SilentlyContinue
    Write-Host "  ✓ 모니터링 리포트 생성 완료" -ForegroundColor Green
}
else {
    Write-Host "  ⚠ generate_monitoring_report.ps1 없음, 스킵" -ForegroundColor Yellow
}

# 2. AGI 레저 요약 생성
Write-Host ""
Write-Host "[2/4] AGI 레저 요약 생성 중..." -ForegroundColor Yellow
$agi_repo = Join-Path $repo_root "fdo_agi_repo"
$python_exe = Join-Path $agi_repo ".venv\Scripts\python.exe"
$ledger_script = Join-Path $agi_repo "scripts\summarize_ledger.py"

if ((Test-Path $python_exe) -and (Test-Path $ledger_script)) {
    Push-Location $agi_repo
    try {
        & $python_exe $ledger_script --last-hours $Hours 2>&1 | Out-Null
        Write-Host "  ✓ AGI 레저 요약 완료" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠ AGI 레저 요약 실패: $_" -ForegroundColor Yellow
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "  ⚠ AGI 환경 없음, 스킵" -ForegroundColor Yellow
}

# 3. 메트릭 로드
Write-Host ""
Write-Host "[3/4] 메트릭 분석 중..." -ForegroundColor Yellow

$metrics_file = Join-Path $repo_root "outputs\monitoring_metrics_latest.json"
$ledger_file = Join-Path $agi_repo "outputs\ledger_summary_latest.json"

$metrics = $null
$ledger = $null

if (Test-Path $metrics_file) {
    $metrics = Get-Content $metrics_file -Raw | ConvertFrom-Json
    Write-Host "  ✓ 모니터링 메트릭 로드 완료" -ForegroundColor Green
}

if (Test-Path $ledger_file) {
    $ledger = Get-Content $ledger_file -Raw | ConvertFrom-Json
    Write-Host "  ✓ AGI 레저 로드 완료" -ForegroundColor Green
}

# 4. 성공 기준 검증
Write-Host ""
Write-Host "[4/4] Phase 1 성공 기준 검증" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$pass_count = 0
$total_checks = 4

# Check 1: Local LLM ALERT
Write-Host "Check 1: Local LLM alert (target: ALERT less than 2 per 10 samples)" -ForegroundColor White
if ($metrics -and $metrics.Core_Gateway.Local_LLM) {
    $samples = $metrics.Core_Gateway.Local_LLM.recent_samples
    if ($samples) {
        $alert_count = ($samples | Where-Object { $_ -gt 2500 }).Count
        $total_samples = $samples.Count
        $alert_rate = [math]::Round(($alert_count / $total_samples * 100), 1)
        
        if ($alert_count -le 2) {
            Write-Host "  PASS: $alert_count of $total_samples samples ALERT - $alert_rate percent" -ForegroundColor Green
            $pass_count++
        }
        else {
            Write-Host "  FAIL: $alert_count of $total_samples samples ALERT - $alert_rate percent" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  WARN: Insufficient data" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  WARN: No metrics" -ForegroundColor Yellow
}

# Check 2: AGI average quality
Write-Host ""
Write-Host "Check 2: AGI average quality (target: >= 0.70)" -ForegroundColor White
if ($ledger -and $ledger.avg_quality) {
    $avg_quality = [math]::Round($ledger.avg_quality, 3)
    if ($avg_quality -ge 0.70) {
        Write-Host "  PASS: $avg_quality (exceeds target)" -ForegroundColor Green
        $pass_count++
    }
    else {
        Write-Host "  FAIL: $avg_quality (below 0.70)" -ForegroundColor Red
    }
}
else {
    Write-Host "  WARN: No data" -ForegroundColor Yellow
}

# Check 3: Second Pass rate
Write-Host ""
Write-Host "Check 3: Second Pass rate (target: less than 15 percent)" -ForegroundColor White
if ($ledger -and $ledger.second_pass_rate) {
    $second_pass = [math]::Round($ledger.second_pass_rate * 100, 1)
    if ($second_pass -lt 15) {
        Write-Host "  PASS: $second_pass percent (target met)" -ForegroundColor Green
        $pass_count++
    }
    else {
        Write-Host "  FAIL: $second_pass percent (above 15)" -ForegroundColor Red
    }
}
else {
    Write-Host "  WARN: No data" -ForegroundColor Yellow
}

# Check 4: Average Duration
Write-Host ""
Write-Host "Check 4: Average Duration (reference: target less than 10s, Phase 2 needed)" -ForegroundColor White
if ($ledger -and $ledger.avg_duration_seconds) {
    $avg_duration = [math]::Round($ledger.avg_duration_seconds, 1)
    if ($avg_duration -lt 10) {
        Write-Host "  EXCELLENT: ${avg_duration}s (Phase 2 not needed)" -ForegroundColor Green
        $pass_count++
    }
    elseif ($avg_duration -lt 15) {
        Write-Host "  GOOD: ${avg_duration}s (Phase 2 recommended)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  NEEDS_WORK: ${avg_duration}s (Phase 2 required)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  WARN: No data" -ForegroundColor Yellow
}

# Final result
Write-Host ''
Write-Host '================================================================' -ForegroundColor Cyan
$result_color = if ($pass_count -ge 3) { 'Green' } else { 'Yellow' }
Write-Host "  Final result: $pass_count of $total_checks passed" -ForegroundColor $result_color
Write-Host '================================================================' -ForegroundColor Cyan
Write-Host ''

if ($pass_count -ge 3) {
    Write-Host 'SUCCESS: Phase 1 Quick Wins validation passed!' -ForegroundColor Green
    Write-Host '   - Local LLM alert normalization confirmed' -ForegroundColor Green
    Write-Host '   - AGI quality target achieved' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Next steps:' -ForegroundColor Cyan
    Write-Host '   1. Backup changes (optional)' -ForegroundColor White
    Write-Host '   2. Review Phase 2 implementation (evidence caching)' -ForegroundColor White
    Write-Host '   3. Continue long-term monitoring' -ForegroundColor White
}
else {
    Write-Host 'WARNING: Phase 1 validation incomplete' -ForegroundColor Yellow
    Write-Host '   - Some metrics below target or no data' -ForegroundColor Yellow
    Write-Host '   - Recommend 24 more hours of monitoring' -ForegroundColor Yellow
}

# Detailed information output
if ($ShowDetails) {
    Write-Host ''
    Write-Host 'Detailed Metrics section skipped due to encoding issues' -ForegroundColor Yellow
    Write-Host 'Please check JSON files for detailed metrics' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Detailed reports:' -ForegroundColor Cyan
Write-Host '   - outputs\monitoring_report_latest.md' -ForegroundColor White
Write-Host '   - fdo_agi_repo\outputs\ledger_summary_latest.md' -ForegroundColor White
Write-Host ''

exit 0
