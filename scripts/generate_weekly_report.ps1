# Weekly Performance Report Generator
# ====================================
# 
# Generates comprehensive weekly report from AGI performance data
# 
# Usage:
#   .\scripts\generate_weekly_report.ps1                 # Last 7 days
#   .\scripts\generate_weekly_report.ps1 -Days 14        # Last 14 days
#   .\scripts\generate_weekly_report.ps1 -OutputDir docs # Custom output directory

param(
    [int]$Days = 7,
    [string]$OutputDir = "outputs"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptRoot

# Ensure output directory exists
$OutputPath = Join-Path $RootDir $OutputDir
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

$ReportDate = Get-Date -Format "yyyy-MM-dd"
$ReportFile = Join-Path $OutputPath "weekly_report_$ReportDate.md"

Write-Host "[INFO] Generating Weekly Performance Report..." -ForegroundColor Cyan
Write-Host "   Period: Last $Days days" -ForegroundColor White
Write-Host "   Output: $ReportFile" -ForegroundColor White
Write-Host ""

# Helper function to safely read JSON
function Get-JsonContent {
    param([string]$Path)
    if (Test-Path $Path) {
        try {
            return Get-Content $Path -Raw | ConvertFrom-Json
        }
        catch {
            Write-Host "   [WARN]  Failed to read: $Path" -ForegroundColor Yellow
            return $null
        }
    }
    return $null
}

# Helper function to calculate average
function Get-Average {
    param([array]$Values)
    if ($Values.Count -eq 0) { return 0 }
    return ($Values | Measure-Object -Average).Average
}

# Collect data
Write-Host "[SEARCH] Collecting performance data..." -ForegroundColor Cyan

# 1. Latest dashboard data
$ComplexityData = Get-JsonContent (Join-Path $RootDir "outputs\complexity_spectrum_latest.json")
$ReplanData = Get-JsonContent (Join-Path $RootDir "outputs\replan_analysis_latest.json")

# 2. Batch validation files (last N days)
$CutoffDate = (Get-Date).AddDays(-$Days)
$BatchFiles = Get-ChildItem -Path (Join-Path $RootDir "outputs") -Filter "batch_validation_*.json" |
Where-Object { $_.LastWriteTime -gt $CutoffDate } |
Sort-Object LastWriteTime -Descending

Write-Host "   Found $($BatchFiles.Count) batch validation files" -ForegroundColor Gray

# 3. Resonance ledger analysis (last N days)
$LedgerPath = Join-Path $RootDir "fdo_agi_repo\memory\resonance_ledger.jsonl"
$RecentEvents = @()
$CutoffTimestamp = ([DateTimeOffset](Get-Date).AddDays(-$Days)).ToUnixTimeSeconds()

if (Test-Path $LedgerPath) {
    $AllLines = Get-Content $LedgerPath
    foreach ($line in $AllLines) {
        try {
            $event = $line | ConvertFrom-Json
            # Try Unix timestamp first (ts field)
            if ($event.ts -and $event.ts -gt $CutoffTimestamp) {
                $RecentEvents += $event
            }
            # Fallback to timestamp field
            elseif ($event.timestamp) {
                try {
                    $eventTime = [DateTime]::Parse($event.timestamp)
                    if ($eventTime -gt (Get-Date).AddDays(-$Days)) {
                        $RecentEvents += $event
                    }
                }
                catch {
                    # Skip if timestamp parsing fails
                }
            }
        }
        catch {
            # Skip invalid lines
        }
    }
    Write-Host "   Found $($RecentEvents.Count) recent AGI events" -ForegroundColor Gray
}

# Calculate statistics
Write-Host "[UP] Calculating statistics..." -ForegroundColor Cyan

# Group events by task_id to get complete task information
$TaskEvents = @{}
foreach ($event in $RecentEvents) {
    $taskId = $event.task_id
    if (-not $taskId) { continue }
    
    if (-not $TaskEvents.ContainsKey($taskId)) {
        $TaskEvents[$taskId] = @{
            Events     = @()
            Citations  = 0
            Quality    = 0
            Confidence = 0
            Duration   = 0
            Replanned  = $false
        }
    }
    
    $TaskEvents[$taskId].Events += $event
    
    # Extract metrics from different event types
    if ($event.event -eq "synthesis_end" -and $event.citations) {
        $TaskEvents[$taskId].Citations = $event.citations
    }
    if ($event.event -eq "eval" -and $event.quality) {
        $TaskEvents[$taskId].Quality = $event.quality
    }
    if ($event.event -eq "rune") {
        if ($event.rune.confidence) {
            $TaskEvents[$taskId].Confidence = $event.rune.confidence
        }
        if ($event.rune.replan -eq $true) {
            $TaskEvents[$taskId].Replanned = $true
        }
    }
    if ($event.duration_sec) {
        $TaskEvents[$taskId].Duration = [math]::Round($event.duration_sec * 1000, 0)
    }
}

$Stats = @{
    TotalTasks   = $TaskEvents.Count
    SuccessCount = 0
    ReplanCount  = 0
    Citations    = @()
    Quality      = @()
    Confidence   = @()
    Duration     = @()
}

foreach ($taskId in $TaskEvents.Keys) {
    $task = $TaskEvents[$taskId]
    
    # Count as success if quality > 0
    if ($task.Quality -gt 0) {
        $Stats.SuccessCount++
    }
    
    if ($task.Replanned) {
        $Stats.ReplanCount++
    }
    
    if ($task.Citations -gt 0) { $Stats.Citations += $task.Citations }
    if ($task.Quality -gt 0) { $Stats.Quality += $task.Quality }
    if ($task.Confidence -gt 0) { $Stats.Confidence += $task.Confidence }
    if ($task.Duration -gt 0) { $Stats.Duration += $task.Duration }
}

# Calculate rates and averages
$SuccessRate = if ($Stats.TotalTasks -gt 0) { 
    [math]::Round(($Stats.SuccessCount / $Stats.TotalTasks) * 100, 1) 
}
else { 0 }

$ReplanRate = if ($Stats.TotalTasks -gt 0) { 
    [math]::Round(($Stats.ReplanCount / $Stats.TotalTasks) * 100, 1) 
}
else { 0 }

$AvgCitations = [math]::Round((Get-Average $Stats.Citations), 1)
$AvgQuality = [math]::Round((Get-Average $Stats.Quality), 3)
$AvgConfidence = [math]::Round((Get-Average $Stats.Confidence), 3)
$AvgDuration = [math]::Round((Get-Average $Stats.Duration), 0)

# Generate report
Write-Host "[NOTE] Generating report..." -ForegroundColor Cyan

$Report = @"
# Weekly AGI Performance Report

**Report Date**: $ReportDate  
**Period**: Last $Days days  
**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

---

## [INFO] Executive Summary

### Overall Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Success Rate** | $SuccessRate% | >= 70% | $(if ($SuccessRate -ge 70) { 'PASS' } else { 'FAIL' }) |
| **Replan Rate** | $ReplanRate% | < 15% | $(if ($ReplanRate -lt 15) { 'PASS' } else { 'FAIL' }) |
| **Avg Quality** | $AvgQuality | >= 0.7 | $(if ($AvgQuality -ge 0.7) { 'PASS' } else { 'FAIL' }) |
| **Avg Confidence** | $AvgConfidence | >= 0.6 | $(if ($AvgConfidence -ge 0.6) { 'PASS' } else { 'FAIL' }) |
| **Avg Citations** | $AvgCitations | >= 3 | $(if ($AvgCitations -ge 3) { 'PASS' } else { 'FAIL' }) |
| **Avg Duration** | $AvgDuration ms | < 30000 | $(if ($AvgDuration -lt 30000) { 'PASS' } else { 'FAIL' }) |

### Activity Summary

- **Total Tasks**: $($Stats.TotalTasks)
- **Successful**: $($Stats.SuccessCount)
- **Replanned**: $($Stats.ReplanCount)

---

## [UP] Performance Trends

### Success Rate Trend
``````
Success: $($Stats.SuccessCount) / $($Stats.TotalTasks) = $SuccessRate%
``````

### Quality Metrics Distribution
``````
Quality:    Min $(if ($Stats.Quality.Count -gt 0) { [math]::Round(($Stats.Quality | Measure-Object -Minimum).Minimum, 3) } else { 0 }) | Avg $AvgQuality | Max $(if ($Stats.Quality.Count -gt 0) { [math]::Round(($Stats.Quality | Measure-Object -Maximum).Maximum, 3) } else { 0 })
Confidence: Min $(if ($Stats.Confidence.Count -gt 0) { [math]::Round(($Stats.Confidence | Measure-Object -Minimum).Minimum, 3) } else { 0 }) | Avg $AvgConfidence | Max $(if ($Stats.Confidence.Count -gt 0) { [math]::Round(($Stats.Confidence | Measure-Object -Maximum).Maximum, 3) } else { 0 })
Citations:  Min $(if ($Stats.Citations.Count -gt 0) { ($Stats.Citations | Measure-Object -Minimum).Minimum } else { 0 }) | Avg $AvgCitations | Max $(if ($Stats.Citations.Count -gt 0) { ($Stats.Citations | Measure-Object -Maximum).Maximum } else { 0 })
``````

---

## [TARGET] Complexity Analysis

"@

# Add complexity spectrum data if available
if ($ComplexityData) {
    $Report += @"

### Performance by Complexity

| Complexity | Success Rate | Avg Quality | Avg Time |
|------------|--------------|-------------|----------|
| **Simple** | $($ComplexityData.simple.avg_success_rate)% | $($ComplexityData.simple.avg_quality) | $([math]::Round($ComplexityData.simple.avg_time_sec, 1))s |
| **Medium** | $($ComplexityData.medium.avg_success_rate)% | $($ComplexityData.medium.avg_quality) | $([math]::Round($ComplexityData.medium.avg_time_sec, 1))s |
| **Complex** | $($ComplexityData.complex.avg_success_rate)% | $($ComplexityData.complex.avg_quality) | $([math]::Round($ComplexityData.complex.avg_time_sec, 1))s |

### Gap Analysis

- Success Rate Gap: $([math]::Round($ComplexityData.simple.avg_success_rate - $ComplexityData.complex.avg_success_rate, 1))%
- Quality Gap: $([math]::Round($ComplexityData.simple.avg_quality - $ComplexityData.complex.avg_quality, 3))
- Time Increase: $([math]::Round((($ComplexityData.complex.avg_time_sec - $ComplexityData.simple.avg_time_sec) / $ComplexityData.simple.avg_time_sec) * 100, 1))%

"@
}

# Add replan analysis if available
if ($ReplanData) {
    $Report += @"

---

## [RELOAD] Replan Analysis

### Historical vs Recent

| Period | Events | Replan Rate |
|--------|--------|-------------|
| **Historical** | $($ReplanData.historical.total_events) | $($ReplanData.historical.replan_rate)% |
| **Recent** | $($ReplanData.recent.total_events) | $($ReplanData.recent.replan_rate)% |

**Improvement**: $(if ($ReplanData.historical.replan_rate -gt $ReplanData.recent.replan_rate) { 
    [math]::Round($ReplanData.historical.replan_rate - $ReplanData.recent.replan_rate, 1) 
} else { 0 })% reduction

"@
}

# Add batch validation summary
if ($BatchFiles.Count -gt 0) {
    $Report += @"

---

## [TEST] Batch Validation Results

### Recent Batch Tests

"@

    foreach ($batchFile in ($BatchFiles | Select-Object -First 5)) {
        $batchData = Get-JsonContent $batchFile.FullName
        if ($batchData -and $batchData.summary) {
            $batchDate = $batchFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            $successRate = if ($batchData.summary.success_rate_percent) { 
                $batchData.summary.success_rate_percent 
            }
            else { 
                $batchData.summary.success_rate 
            }
            $avgQuality = if ($batchData.summary.avg_quality_score) {
                $batchData.summary.avg_quality_score
            }
            else {
                $batchData.summary.avg_quality
            }
            
            $Report += @"

**$batchDate**
- Total Tasks: $($batchData.summary.total_tasks)
- Success Rate: $successRate%
- Avg Quality: $avgQuality

"@
        }
    }
}

# Add recommendations
$Report += @"

---

## [TIP] Recommendations

"@

$Recommendations = @()

if ($SuccessRate -lt 70) {
    $Recommendations += "[WARN] **Action Required**: Success rate ($SuccessRate%) below target (70%). Review failed tasks and improve error handling."
}

if ($ReplanRate -gt 15) {
    $Recommendations += "[WARN] **Action Required**: Replan rate ($ReplanRate%) above target (15%). Investigate root causes and improve initial planning."
}

if ($AvgQuality -lt 0.7) {
    $Recommendations += "[WARN] **Action Required**: Quality score ($AvgQuality) below target (0.7). Review output quality and enhance evaluation criteria."
}

if ($SuccessRate -ge 95) {
    $Recommendations += "[OK] **Excellent**: Success rate at $SuccessRate%. System performing exceptionally well."
}

if ($ReplanRate -lt 5) {
    $Recommendations += "[OK] **Excellent**: Replan rate at $ReplanRate%. Planning accuracy is very high."
}

if ($Recommendations.Count -eq 0) {
    $Recommendations += "[OK] All metrics within target ranges. Continue monitoring for stability."
}

foreach ($rec in $Recommendations) {
    $Report += "- $rec`n"
}

$Report += @"

---

## 📅 Next Steps

### Immediate Actions
- [ ] Review any failed tasks from the past week
- [ ] Monitor success rate daily with ``quick_status.ps1``
- [ ] Check dashboard for real-time performance

### Weekly Maintenance
- [ ] Run full batch validation: ``python scripts/large_batch_validation.py``
- [ ] Review performance dashboard: ``outputs/agi_performance_dashboard.html``
- [ ] Update this report: ``.\scripts\generate_weekly_report.ps1``

### Long-term Monitoring
- [ ] Track monthly trends
- [ ] Identify seasonal patterns
- [ ] Plan capacity improvements

---

**Report Generated by**: AGI Monitoring System  
**Script**: ``scripts/generate_weekly_report.ps1``  
**Next Report**: $((Get-Date).AddDays($Days).ToString("yyyy-MM-dd"))

---

## 📚 Resources

- **Operations Guide**: ``깃코_운영_가이드_2025-10-27.md``
- **Quick Status**: ``.\scripts\quick_status.ps1``
- **Dashboard**: ``outputs/agi_performance_dashboard.html``
- **Batch Validation**: ``python scripts/large_batch_validation.py``

"@

# Write report
$Report | Out-File -FilePath $ReportFile -Encoding UTF8 -Force

Write-Host ""
Write-Host "[OK] Report generated successfully!" -ForegroundColor Green
Write-Host "   File: $ReportFile" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Summary:" -ForegroundColor Cyan
Write-Host "   Events: $($Stats.TotalEvents)" -ForegroundColor White
Write-Host "   Success Rate: $SuccessRate%" -ForegroundColor $(if ($SuccessRate -ge 70) { 'Green' } else { 'Yellow' })
Write-Host "   Replan Rate: $ReplanRate%" -ForegroundColor $(if ($ReplanRate -lt 15) { 'Green' } else { 'Yellow' })
Write-Host "   Avg Quality: $AvgQuality" -ForegroundColor $(if ($AvgQuality -ge 0.7) { 'Green' } else { 'Yellow' })
Write-Host ""
Write-Host "📖 Open report: Start-Process '$ReportFile'" -ForegroundColor Gray
