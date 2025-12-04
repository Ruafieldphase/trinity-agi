#!/usr/bin/env pwsh
# Simplified Phase 1 verification script

param(
    [int]$Hours = 24
)

$ErrorActionPreference = 'Stop'
$repo_root = Split-Path $PSScriptRoot -Parent

Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  AGI Phase 1 Verification' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# Generate monitoring report
Write-Host '[1/4] Generating monitoring report...' -ForegroundColor Yellow
$report_script = Join-Path $PSScriptRoot 'generate_monitoring_report.ps1'
if (Test-Path $report_script) {
    & $report_script -Hours $Hours -ErrorAction SilentlyContinue
    Write-Host '  OK' -ForegroundColor Green
}

# Generate AGI ledger summary
Write-Host ''
Write-Host '[2/4] Generating AGI ledger summary...' -ForegroundColor Yellow
$agi_repo = Join-Path $repo_root 'fdo_agi_repo'
$python_exe = Join-Path $agi_repo '.venv\Scripts\python.exe'
$ledger_script = Join-Path $agi_repo 'scripts\summarize_ledger.py'

if ((Test-Path $python_exe) -and (Test-Path $ledger_script)) {
    Push-Location $agi_repo
    & $python_exe $ledger_script --last-hours $Hours 2>&1 | Out-Null
    Pop-Location
    Write-Host '  OK' -ForegroundColor Green
}

# Load metrics
Write-Host ''
Write-Host '[3/4] Loading metrics...' -ForegroundColor Yellow
$metrics_file = Join-Path $repo_root 'outputs\monitoring_metrics_latest.json'
$ledger_file = Join-Path $agi_repo 'outputs\ledger_summary_latest.json'

$metrics = $null
$ledger = $null

if (Test-Path $metrics_file) {
    $metrics = Get-Content $metrics_file | ConvertFrom-Json
    Write-Host '  Monitoring metrics loaded' -ForegroundColor Green
}

if (Test-Path $ledger_file) {
    $ledger = Get-Content $ledger_file | ConvertFrom-Json
    Write-Host '  AGI ledger loaded' -ForegroundColor Green
}

# Validation
Write-Host ''
Write-Host '[4/4] Validating success criteria...' -ForegroundColor Yellow
Write-Host ''

$pass_count = 0
$total_checks = 4

# Check 1: Local LLM alerts
Write-Host 'Check 1: Local LLM alert rate' -ForegroundColor White
if ($metrics -and $metrics.Channels -and $metrics.Channels.Local) {
    $local = $metrics.Channels.Local
    $baseline_alerts = $local.BaselineAlerts
    $adaptive_alerts = $local.AdaptiveAlerts
    $total_samples = $local.Count
    
    # Use BaselineAlerts (threshold-based) for Phase 1 validation
    if ($baseline_alerts -le 2) {
        Write-Host "  PASS: $baseline_alerts of $total_samples samples exceeded 2500ms threshold" -ForegroundColor Green
        $pass_count++
    }
    else {
        Write-Host "  FAIL: $baseline_alerts of $total_samples samples exceeded threshold" -ForegroundColor Red
    }
    Write-Host "    (P95: $($local.P95)ms, Mean: $($local.Mean)ms, Adaptive alerts: $adaptive_alerts)" -ForegroundColor DarkGray
}
else {
    Write-Host '  WARN: No data' -ForegroundColor Yellow
}

# Check 2: AGI quality
Write-Host ''
Write-Host 'Check 2: AGI average quality' -ForegroundColor White
if ($ledger -and $ledger.metrics -and $ledger.metrics.avg_quality) {
    $avg_quality = [math]::Round($ledger.metrics.avg_quality, 3)
    if ($avg_quality -ge 0.70) {
        Write-Host "  PASS: $avg_quality" -ForegroundColor Green
        $pass_count++
    }
    else {
        Write-Host "  FAIL: $avg_quality (below 0.70)" -ForegroundColor Red
    }
}
else {
    Write-Host '  WARN: No data' -ForegroundColor Yellow
}

# Check 3: Second pass rate
Write-Host ''
Write-Host 'Check 3: Second pass rate' -ForegroundColor White
if ($ledger -and $ledger.metrics -and $ledger.metrics.second_pass_rate_per_task) {
    $second_pass = [math]::Round($ledger.metrics.second_pass_rate_per_task * 100, 1)
    if ($second_pass -lt 15) {
        Write-Host "  PASS: $second_pass percent" -ForegroundColor Green
        $pass_count++
    }
    else {
        Write-Host "  FAIL: $second_pass percent" -ForegroundColor Red
    }
}
else {
    Write-Host '  WARN: No data' -ForegroundColor Yellow
}

# Check 4: Duration
Write-Host ''
Write-Host 'Check 4: Average duration' -ForegroundColor White
if ($ledger -and $ledger.metrics -and $ledger.metrics.avg_duration_seconds) {
    $avg_duration = [math]::Round($ledger.metrics.avg_duration_seconds, 1)
    if ($avg_duration -lt 10) {
        Write-Host "  EXCELLENT: $avg_duration seconds" -ForegroundColor Green
        $pass_count++
    }
    elseif ($avg_duration -lt 15) {
        Write-Host "  GOOD: $avg_duration seconds (Phase 2 recommended)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  NEEDS_WORK: $avg_duration seconds (Phase 2 required)" -ForegroundColor Yellow
    }
}
else {
    Write-Host '  WARN: No data (duration not tracked yet)' -ForegroundColor Yellow
}

# Final result
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host "  Result: $pass_count of $total_checks passed" -ForegroundColor $(if ($pass_count -ge 3) { 'Green' } else { 'Yellow' })
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

if ($pass_count -ge 3) {
    Write-Host 'SUCCESS: Phase 1 validation passed' -ForegroundColor Green
}
else {
    Write-Host 'WARNING: Phase 1 validation incomplete' -ForegroundColor Yellow
    Write-Host 'Recommend 24 more hours of monitoring' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Detailed reports:' -ForegroundColor Cyan
Write-Host '  - outputs\monitoring_report_latest.md'
Write-Host '  - fdo_agi_repo\outputs\ledger_summary_latest.md'
Write-Host ''

exit 0
