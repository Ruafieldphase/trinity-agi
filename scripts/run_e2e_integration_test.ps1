# E2E Integration Test for 6 Systems
# Runs all systems in sequence and validates results

param(
    [switch]$SkipYouTube,  # Skip YouTube test (requires URL)
    [string]$YouTubeUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    [switch]$OpenReports
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n  E2E Integration Test - 6 Systems`n" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n"

$results = @()
$startTime = Get-Date

# Test 1: Resonance Loop + Lumen
Write-Host "Test 1/6: Resonance Loop + Lumen Integration..." -ForegroundColor Cyan
try {
    & "$scriptDir\run_resonance_lumen_integration.ps1" -ErrorAction Stop
    $results += @{
        System = "Resonance Loop"
        Status = "PASS"
        Error  = $null
    }
    Write-Host "  PASS" -ForegroundColor Green
}
catch {
    $results += @{
        System = "Resonance Loop"
        Status = "FAIL"
        Error  = $_.Exception.Message
    }
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: BQI Phase 6 + Lumen
Write-Host "Test 2/6: BQI Phase 6 + Lumen Integration..." -ForegroundColor Cyan
try {
    & "$scriptDir\run_bqi_lumen_integration.ps1" -ErrorAction Stop
    $results += @{
        System = "BQI Phase 6"
        Status = "PASS"
        Error  = $null
    }
    Write-Host "  PASS" -ForegroundColor Green
}
catch {
    $results += @{
        System = "BQI Phase 6"
        Status = "FAIL"
        Error  = $_.Exception.Message
    }
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: YouTube + Lumen (optional)
if (-not $SkipYouTube) {
    Write-Host "Test 3/6: YouTube + Lumen Enhancement..." -ForegroundColor Cyan
    try {
        & "$scriptDir\run_youtube_lumen_enhancement.ps1" -Url $YouTubeUrl -ErrorAction Stop
        $results += @{
            System = "YouTube Learning"
            Status = "PASS"
            Error  = $null
        }
        Write-Host "  PASS" -ForegroundColor Green
    }
    catch {
        $results += @{
            System = "YouTube Learning"
            Status = "FAIL"
            Error  = $_.Exception.Message
        }
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    }
}
else {
    Write-Host "Test 3/6: YouTube + Lumen Enhancement... SKIPPED" -ForegroundColor Yellow
    $results += @{
        System = "YouTube Learning"
        Status = "SKIP"
        Error  = "Skipped by user"
    }
}
Write-Host ""

# Test 4: Intelligent Feedback
Write-Host "Test 4/6: Intelligent Feedback System..." -ForegroundColor Cyan
try {
    & "$scriptDir\run_intelligent_feedback.ps1" -ErrorAction Stop
    $results += @{
        System = "Intelligent Feedback"
        Status = "PASS"
        Error  = $null
    }
    Write-Host "  PASS" -ForegroundColor Green
}
catch {
    $results += @{
        System = "Intelligent Feedback"
        Status = "FAIL"
        Error  = $_.Exception.Message
    }
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Orchestration
Write-Host "Test 5/6: Persona Orchestration..." -ForegroundColor Cyan
try {
    & "$scriptDir\run_orchestration.ps1" -Topic "E2E Integration Test" -ErrorAction Stop
    $results += @{
        System = "Orchestration"
        Status = "PASS"
        Error  = $null
    }
    Write-Host "  PASS" -ForegroundColor Green
}
catch {
    $results += @{
        System = "Orchestration"
        Status = "FAIL"
        Error  = $_.Exception.Message
    }
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Daily Briefing
Write-Host "Test 6/6: Daily Briefing Generation..." -ForegroundColor Cyan
try {
    & "$scriptDir\generate_daily_briefing.ps1" -ErrorAction Stop
    $results += @{
        System = "Daily Briefing"
        Status = "PASS"
        Error  = $null
    }
    Write-Host "  PASS" -ForegroundColor Green
}
catch {
    $results += @{
        System = "Daily Briefing"
        Status = "FAIL"
        Error  = $_.Exception.Message
    }
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

$endTime = Get-Date
$duration = $endTime - $startTime

# Summary
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "`n  Test Summary`n" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$skipCount = ($results | Where-Object { $_.Status -eq "SKIP" }).Count
$totalCount = $results.Count

foreach ($result in $results) {
    $color = switch ($result.Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
    }
    Write-Host "  [$($result.Status)]  $($result.System)" -ForegroundColor $color
    if ($result.Error) {
        Write-Host "    Error: $($result.Error)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Results:" -ForegroundColor Cyan
Write-Host "  Total:   $totalCount" -ForegroundColor White
Write-Host "  Passed:  $passCount" -ForegroundColor Green
Write-Host "  Failed:  $failCount" -ForegroundColor Red
Write-Host "  Skipped: $skipCount" -ForegroundColor Yellow
Write-Host ""
Write-Host "Duration: $($duration.TotalSeconds.ToString('F1'))s" -ForegroundColor Gray
Write-Host ""

# Save results
$reportPath = Join-Path $outputDir "e2e_test_results_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').json"
$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "Results saved: $reportPath" -ForegroundColor Cyan

# Overall status
Write-Host ("=" * 70) -ForegroundColor Cyan
if ($failCount -eq 0) {
    Write-Host "`n  ALL TESTS PASSED!  `n" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
    exit 0
}
else {
    Write-Host "`n  SOME TESTS FAILED  `n" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
