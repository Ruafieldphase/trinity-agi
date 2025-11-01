# Daily Performance Report Generator
# Automatically generates and emails daily performance summaries

param(
    [int]$Days = 7,
    [switch]$SendEmail,
    [string]$EmailTo = $env:PERF_REPORT_EMAIL,
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"
$timestamp = Get-Date -Format "yyyy-MM-dd"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Daily Performance Report Generator" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

# Generate comprehensive dashboard
Write-Host "Generating performance dashboard..." -ForegroundColor Yellow
& "$scriptDir\generate_performance_dashboard.ps1" -Days $Days -ExportJson -ExportCsv -WriteLatest | Out-Null

# Generate comparison reports
Write-Host "Generating trend comparison (3d vs 7d)..." -ForegroundColor Yellow
& "$scriptDir\compare_performance_periods.ps1" -PeriodDays1 3 -PeriodDays2 7 -Label1 "Recent" -Label2 "Week" | Out-Null

# Create daily summary
$summaryPath = Join-Path $outputDir "daily_report_$timestamp.md"
$dashboardPath = Join-Path $outputDir "performance_dashboard_latest.md"
$comparisonPath = Join-Path $outputDir "performance_comparison_$timestamp.md"
$jsonPath = Join-Path $outputDir "performance_metrics_latest.json"

Write-Host "Creating daily summary..." -ForegroundColor Yellow

# Read JSON for summary stats
$json = Get-Content $jsonPath -Raw | ConvertFrom-Json

$summary = @"
# Daily Performance Report - $timestamp

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Period**: Last $Days days

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Overall Success Rate | $($json.OverallSuccessRate)% | $(if ($json.OverallSuccessRate -ge 90) { '[OK] Excellent' } elseif ($json.OverallSuccessRate -ge 75) { '[WARN] Good' } else { '[CRIT] Needs Attention' }) |
| Effective Success Rate | $($json.OverallEffectiveSuccessRate)% | $(if ($json.OverallEffectiveSuccessRate -ge 90) { '[OK] Excellent' } elseif ($json.OverallEffectiveSuccessRate -ge 75) { '[WARN] Good' } else { '[CRIT] Needs Attention' }) |
| Test Runs | $($json.TestRuns) | - |
| Systems Monitored | $($json.SystemsConsidered) | - |

### Band Distribution

- **Excellent**: $($json.BandCounts.Excellent) systems
- **Good**: $($json.BandCounts.Good) systems
- **Needs Attention**: $($json.BandCounts.Needs) systems
- **No Data**: $($json.BandCounts.NoData) systems

---

## Top Priorities

$(if ($json.TopAttention -and $json.TopAttention.Count -gt 0) {
    $priorities = ""
    foreach ($item in $json.TopAttention) {
        $priorities += "### $($item.System)`n`n"
        $priorities += "**Effective Success Rate**: $($item.EffectiveSuccessRate)%`n`n"
        $priorities += "**Action Required**: Review recent failures and implement fixes.`n`n"
    }
    $priorities
} else {
    "[SUCCESS] **No critical issues!** All systems performing at or above excellent threshold.`n`n"
})

---

## Recent Trends

See attached comparison report for 3-day vs 7-day trend analysis.

---

## Detailed Reports

1. **Full Dashboard**: ``performance_dashboard_latest.md``
2. **Trend Comparison**: ``performance_comparison_$timestamp.md``
3. **Raw Data (JSON)**: ``performance_metrics_latest.json``
4. **CSV Export**: ``performance_metrics_$timestamp.csv``

---

## Recommendations

$(if ($json.BandCounts.Needs -gt 0) {
    "- **Immediate**: Address $($json.BandCounts.Needs) system(s) in 'Needs Attention' band`n"
})
$(if ($json.BandCounts.NoData -gt 0) {
    "- **Investigation**: Review $($json.BandCounts.NoData) system(s) with no recent data`n"
})
$(if ($json.BandCounts.Good -gt 0) {
    "- **Improvement**: Optimize $($json.BandCounts.Good) 'Good' system(s) to reach Excellent`n"
})
$(if ($json.BandCounts.Excellent -eq $json.SystemsConsidered) {
    "- [SUCCESS] **Celebrate**: All systems excellent! Maintain current quality standards.`n"
})

---

**Next Report**: $((Get-Date).AddDays(1).ToString('yyyy-MM-dd'))  
**Report Type**: Automated Daily Summary  
**Contact**: AGI Operations Team
"@

$summary | Out-File -FilePath $summaryPath -Encoding UTF8

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "  Daily Report Generated!" -ForegroundColor Green
Write-Host "======================================================================`n" -ForegroundColor Green

Write-Host "Summary: $summaryPath" -ForegroundColor Cyan
Write-Host "Dashboard: $dashboardPath" -ForegroundColor Cyan
Write-Host "Comparison: $comparisonPath" -ForegroundColor Cyan
Write-Host "JSON: $jsonPath" -ForegroundColor Cyan

if ($OpenReport) {
    Write-Host "`nOpening summary report..." -ForegroundColor Yellow
    code $summaryPath
}

if ($SendEmail -and $EmailTo) {
    Write-Host "`nEmail functionality not yet implemented." -ForegroundColor Yellow
    Write-Host "Set up SMTP configuration to enable email reports." -ForegroundColor Yellow
}

Write-Host ""
