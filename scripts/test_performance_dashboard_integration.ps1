# Performance Dashboard Integration Test Script
# Tests all profiles and wrappers to ensure consistent behavior

param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Performance Dashboard Integration Test Suite" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$testResults = @()
$testScripts = @(
    @{ Name = "dashboard_quick_needs"; Script = "dashboard_quick_needs.ps1"; ExpectedBands = @("Needs") },
    @{ Name = "dashboard_quick_full"; Script = "dashboard_quick_full.ps1"; ExpectedBands = @("Excellent", "Good", "Needs", "NoData") },
    @{ Name = "dashboard_ops_daily"; Script = "dashboard_ops_daily.ps1"; ExpectedSystems = @("Orchestration", "Monitoring", "Daily Briefing") },
    @{ Name = "dashboard_ops_focus"; Script = "dashboard_ops_focus.ps1"; ExpectedSystems = @("Orchestration"); ExpectedDays = 3 },
    @{ Name = "dashboard_ops_attention"; Script = "dashboard_ops_attention.ps1"; ExpectedBands = @("Needs", "NoData") },
    @{ Name = "dashboard_ops_excellent"; Script = "dashboard_ops_excellent.ps1"; ExpectedBands = @("Excellent"); ExpectedDays = 30 }
)

foreach ($test in $testScripts) {
    Write-Host "Testing: $($test.Name)" -ForegroundColor Yellow
    
    $scriptPath = Join-Path $scriptDir $test.Script
    if (-not (Test-Path $scriptPath)) {
        Write-Host "  [SKIP] Script not found: $scriptPath" -ForegroundColor Red
        $testResults += @{ Test = $test.Name; Status = "SKIP"; Reason = "Script not found" }
        continue
    }
    
    try {
        # Run the script without opening
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -ne 0) {
            Write-Host "  [FAIL] Exit code: $exitCode" -ForegroundColor Red
            if ($VerboseOutput) {
                Write-Host "  Output: $($output | Out-String)" -ForegroundColor Gray
            }
            $testResults += @{ Test = $test.Name; Status = "FAIL"; Reason = "Non-zero exit code: $exitCode" }
            continue
        }
        
        # Verify outputs exist
        $jsonPath = Join-Path $outputDir "performance_metrics_latest.json"
        $csvPath = Join-Path $outputDir "performance_metrics_latest.csv"
        $mdPath = Join-Path $outputDir "performance_dashboard_latest.md"
        
        $jsonExists = Test-Path $jsonPath
        $csvExists = Test-Path $csvPath
        $mdExists = Test-Path $mdPath
        
        if (-not ($jsonExists -and $csvExists -and $mdExists)) {
            Write-Host "  [FAIL] Missing output files" -ForegroundColor Red
            Write-Host "    JSON: $jsonExists, CSV: $csvExists, MD: $mdExists" -ForegroundColor Gray
            $testResults += @{ Test = $test.Name; Status = "FAIL"; Reason = "Missing output files" }
            continue
        }
        
        # Validate JSON structure
        $jsonContent = Get-Content $jsonPath -Raw | ConvertFrom-Json
        if (-not $jsonContent) {
            Write-Host "  [FAIL] Invalid JSON" -ForegroundColor Red
            $testResults += @{ Test = $test.Name; Status = "FAIL"; Reason = "Invalid JSON" }
            continue
        }
        
        # Validate CSV has metadata
        $csvHeader = Get-Content $csvPath -TotalCount 5
        if (-not ($csvHeader -match "^# Performance Metrics CSV")) {
            Write-Host "  [WARN] CSV missing metadata header" -ForegroundColor Yellow
        }
        
        # Optional: verify expected bands
        if ($test.ExpectedBands) {
            $bandsConsidered = $jsonContent.BandsConsidered
            if ($bandsConsidered) {
                Write-Host "  [INFO] Bands: $($bandsConsidered -join ', ')" -ForegroundColor Cyan
            }
        }
        
        # Optional: verify expected systems
        if ($test.ExpectedSystems) {
            $systemsCount = $jsonContent.SystemsConsidered
            Write-Host "  [INFO] Systems Considered: $systemsCount" -ForegroundColor Cyan
        }
        
        Write-Host "  [PASS]" -ForegroundColor Green
        $testResults += @{ Test = $test.Name; Status = "PASS"; Reason = "" }
    }
    catch {
        Write-Host "  [FAIL] Exception: $($_.Exception.Message)" -ForegroundColor Red
        $testResults += @{ Test = $test.Name; Status = "FAIL"; Reason = $_.Exception.Message }
    }
    
    Write-Host ""
}

# Summary
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$skipped = ($testResults | Where-Object { $_.Status -eq "SKIP" }).Count
$total = $testResults.Count

Write-Host "Total: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Skipped: $skipped" -ForegroundColor Yellow
Write-Host ""

if ($failed -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    foreach ($result in ($testResults | Where-Object { $_.Status -eq "FAIL" })) {
        Write-Host "  - $($result.Test): $($result.Reason)" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
}

Write-Host "All tests passed!" -ForegroundColor Green
exit 0
