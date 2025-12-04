# Performance Dashboard Comparison Tool
# Compare metrics across different time periods or band filters

param(
    [int]$PeriodDays1 = 7,
    [int]$PeriodDays2 = 30,
    [string]$Label1 = "Short-term",
    [string]$Label2 = "Long-term",
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Performance Comparison Tool" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

Write-Host "Generating first dashboard ($Label1 - $PeriodDays1 days)..." -ForegroundColor Yellow
& powershell -NoProfile -ExecutionPolicy Bypass -File "$scriptDir\generate_performance_dashboard.ps1" `
    -Days $PeriodDays1 -ExportJson -WriteLatest | Out-Null

$json1Path = Join-Path $outputDir "performance_metrics_latest.json"
$json1TempPath = Join-Path $outputDir "perf_compare_temp1.json"
if (Test-Path $json1Path) {
    Copy-Item $json1Path $json1TempPath -Force
}

if (-not (Test-Path $json1TempPath)) {
    Write-Host "  [ERROR] Failed to generate first dashboard" -ForegroundColor Red
    exit 1
}

Write-Host "Generating second dashboard ($Label2 - $PeriodDays2 days)..." -ForegroundColor Yellow
& powershell -NoProfile -ExecutionPolicy Bypass -File "$scriptDir\generate_performance_dashboard.ps1" `
    -Days $PeriodDays2 -ExportJson -WriteLatest | Out-Null

$json2Path = Join-Path $outputDir "performance_metrics_latest.json"
$json2TempPath = Join-Path $outputDir "perf_compare_temp2.json"
if (Test-Path $json2Path) {
    Copy-Item $json2Path $json2TempPath -Force
}

if (-not (Test-Path $json2TempPath)) {
    Write-Host "  [ERROR] Failed to generate second dashboard" -ForegroundColor Red
    exit 1
}

# Load both JSON files
$data1 = Get-Content $json1TempPath -Raw | ConvertFrom-Json
$data2 = Get-Content $json2TempPath -Raw | ConvertFrom-Json

# Generate comparison report
$reportPath = Join-Path $outputDir "performance_comparison_$(Get-Date -Format 'yyyy-MM-dd').md"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$report = @"
# Performance Comparison Report

**Generated**: $timestamp  
**Comparison**: $Label1 ($PeriodDays1 days) vs $Label2 ($PeriodDays2 days)

---

## Overall Metrics Comparison

| Metric | $Label1 | $Label2 | Delta |
|--------|---------|---------|-------|
| Test Runs | $($data1.TotalTestRuns) | $($data2.TotalTestRuns) | $('{0:+#;-#;0}' -f ($data2.TotalTestRuns - $data1.TotalTestRuns)) |
| Overall Success | $($data1.OverallSuccessRate)% | $($data2.OverallSuccessRate)% | $('{0:+0.0;-0.0;0.0}' -f ($data2.OverallSuccessRate - $data1.OverallSuccessRate))% |
| Effective Success | $($data1.OverallEffectiveSuccessRate)% | $($data2.OverallEffectiveSuccessRate)% | $('{0:+0.0;-0.0;0.0}' -f ($data2.OverallEffectiveSuccessRate - $data1.OverallEffectiveSuccessRate))% |
| Excellent Systems | $($data1.BandCounts.Excellent) | $($data2.BandCounts.Excellent) | $('{0:+#;-#;0}' -f ($data2.BandCounts.Excellent - $data1.BandCounts.Excellent)) |
| Needs Attention | $($data1.BandCounts.Needs) | $($data2.BandCounts.Needs) | $('{0:+#;-#;0}' -f ($data2.BandCounts.Needs - $data1.BandCounts.Needs)) |

---

## System-by-System Comparison

"@

# Create lookup for period 2
$systems2 = $data2.Systems

# Compare each system from period 1
foreach ($sysName in $data1.Systems.PSObject.Properties.Name) {
    $sys1 = $data1.Systems.$sysName
    $sys2 = $systems2.$sysName
    
    $report += "`n### $sysName`n`n"
    
    if ($sys2) {
        $rate1 = [double]$sys1.EffectiveSuccessRate
        $rate2 = [double]$sys2.EffectiveSuccessRate
        $delta = $rate2 - $rate1
        
        $trend = if ($delta -gt 5) { "[UP] IMPROVED" }
        elseif ($delta -lt -5) { "[DOWN] DEGRADED" }
        else { "[=] STABLE" }
        
        # Get band strings
        $band1 = if ($sys1.Band) { $sys1.Band } else { "N/A" }
        $band2 = if ($sys2.Band) { $sys2.Band } else { "N/A" }
        
        $report += "**Trend**: $trend`n`n"
        $report += "| Metric | $Label1 | $Label2 | Change |`n"
        $report += "|--------|---------|---------|--------|`n"
        $report += "| Success Rate | $($sys1.SuccessRate)% | $($sys2.SuccessRate)% | $('{0:+0.0;-0.0;0.0}' -f ($sys2.SuccessRate - $sys1.SuccessRate))% |`n"
        $report += "| Effective Rate | $($sys1.EffectiveSuccessRate)% | $($sys2.EffectiveSuccessRate)% | $('{0:+0.0;-0.0;0.0}' -f $delta)% |`n"
        $report += "| Band | $band1 | $band2 | - |`n"
        $report += "| Total Runs | $($sys1.TotalRuns) | $($sys2.TotalRuns) | $('{0:+#;-#;0}' -f ($sys2.TotalRuns - $sys1.TotalRuns)) |`n"
    }
    else {
        $band1 = if ($sys1.Band) { $sys1.Band } else { "N/A" }
        $report += "**Status**: Only in $Label1 (not found in $Label2)`n`n"
        $report += "| Metric | Value |`n"
        $report += "|--------|-------|`n"
        $report += "| Success Rate | $($sys1.SuccessRate)% |`n"
        $report += "| Band | $band1 |`n"
    }
}

# Check for systems only in period 2
foreach ($sysName in $systems2.PSObject.Properties.Name) {
    $foundInPeriod1 = $data1.Systems.PSObject.Properties.Name -contains $sysName
    
    if (-not $foundInPeriod1) {
        $sys2 = $systems2.$sysName
        $band2 = if ($sys2.Band) { $sys2.Band } else { "N/A" }
        $report += "`n### $sysName`n`n"
        $report += "**Status**: Only in $Label2 (new system)`n`n"
        $report += "| Metric | Value |`n"
        $report += "|--------|-------|`n"
        $report += "| Success Rate | $($sys2.SuccessRate)% |`n"
        $report += "| Band | $band2 |`n"
    }
}

$report += @"

---

## Summary

- **Period 1** ($Label1): $PeriodDays1 days, $($data1.TotalTestRuns) runs
- **Period 2** ($Label2): $PeriodDays2 days, $($data2.TotalTestRuns) runs
- **Overall trend**: $(if ($data2.EffectiveOverallSuccessRate -gt $data1.EffectiveOverallSuccessRate) { "Improving" } elseif ($data2.EffectiveOverallSuccessRate -lt $data1.EffectiveOverallSuccessRate) { "Declining" } else { "Stable" })

Generated by: Performance Dashboard Comparison Tool  
Timestamp: $timestamp
"@

# Write report
$report | Out-File -FilePath $reportPath -Encoding UTF8 -Force

# Cleanup temp files
Remove-Item $json1TempPath -Force -ErrorAction SilentlyContinue
Remove-Item $json2TempPath -Force -ErrorAction SilentlyContinue

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Comparison Complete!" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan
Write-Host "Report: $reportPath" -ForegroundColor Green

if ($OpenReport) {
    Write-Host "`nOpening report..." -ForegroundColor Cyan
    code $reportPath
}

Write-Host ""
