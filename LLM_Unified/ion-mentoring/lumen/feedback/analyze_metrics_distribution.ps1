#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Analyze actual metric distributions from Cloud Logging

.DESCRIPTION
  Queries recent logs to calculate p50, p90, p95, p99 percentiles
  for feedback loop metrics to inform alert threshold tuning.

.PARAMETER ProjectId
  GCP project ID (default: naeda-genesis)

.PARAMETER Hours
  Number of hours to look back (default: 24)

.PARAMETER OutputJson
  Optional path to save analysis results as JSON

.EXAMPLE
  ./analyze_metrics_distribution.ps1
  ./analyze_metrics_distribution.ps1 -Hours 48 -OutputJson analysis.json
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [int]$Hours = 24,
    [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Feedback Loop Metrics Distribution Analysis ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Time Range: Last $Hours hour(s)" -ForegroundColor Gray
Write-Host ""

# Query logs
Write-Host "📊 Querying logs..." -ForegroundColor Yellow
$logFilter = "jsonPayload.component=`"feedback_loop`""
$freshness = "${Hours}h"
$logCmd = "gcloud logging read `"$logFilter`" --project=$ProjectId --format=json --freshness=$freshness 2>&1"
$logJson = cmd /c $logCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to query logs: $logJson" -ForegroundColor Red
    exit 1
}

$logEntries = $logJson | ConvertFrom-Json
$count = $logEntries.Count

if ($count -eq 0) {
    Write-Host "⚠️  No logs found in last $Hours hour(s)" -ForegroundColor Yellow
    exit 0
}

Write-Host "   Found $count log entries" -ForegroundColor Green
Write-Host ""

# Extract metric values
$cacheHitRates = @()
$memoryUsages = @()
$avgTTLs = @()
$healthScores = @()

foreach ($entry in $logEntries) {
    $payload = $entry.jsonPayload
    if ($payload.cache_hit_rate) { $cacheHitRates += [double]$payload.cache_hit_rate }
    if ($payload.cache_memory_usage_percent) { $memoryUsages += [double]$payload.cache_memory_usage_percent }
    if ($payload.cache_avg_ttl_seconds) { $avgTTLs += [double]$payload.cache_avg_ttl_seconds }
    if ($payload.unified_health_score) { $healthScores += [double]$payload.unified_health_score }
}

# Calculate percentiles
function Get-Percentile {
    param([double[]]$values, [double]$percentile)
    if ($values.Count -eq 0) { return $null }
    $sorted = $values | Sort-Object
    $index = [Math]::Ceiling($sorted.Count * $percentile / 100) - 1
    if ($index -lt 0) { $index = 0 }
    return $sorted[$index]
}

function Get-Stats {
    param([double[]]$values)
    if ($values.Count -eq 0) {
        return @{
            count = 0
            min   = $null
            max   = $null
            mean  = $null
            p50   = $null
            p90   = $null
            p95   = $null
            p99   = $null
        }
    }
  
    $sorted = $values | Sort-Object
    return @{
        count = $values.Count
        min   = $sorted[0]
        max   = $sorted[-1]
        mean  = ($values | Measure-Object -Average).Average
        p50   = Get-Percentile $values 50
        p90   = Get-Percentile $values 90
        p95   = Get-Percentile $values 95
        p99   = Get-Percentile $values 99
    }
}

# Analyze each metric
Write-Host "📈 Metric Distributions:" -ForegroundColor Cyan
Write-Host ""

$analysis = @{}

# Cache Hit Rate
Write-Host "1️⃣  Cache Hit Rate" -ForegroundColor Yellow
$hitRateStats = Get-Stats $cacheHitRates
$analysis.cache_hit_rate = $hitRateStats
if ($hitRateStats.count -gt 0) {
    Write-Host "   Count: $($hitRateStats.count)" -ForegroundColor Gray
    Write-Host "   Min: $($hitRateStats.min)" -ForegroundColor Gray
    Write-Host "   Max: $($hitRateStats.max)" -ForegroundColor Gray
    Write-Host "   Mean: $([Math]::Round($hitRateStats.mean, 3))" -ForegroundColor Gray
    Write-Host "   p50: $($hitRateStats.p50)" -ForegroundColor Cyan
    Write-Host "   p90: $($hitRateStats.p90)" -ForegroundColor Cyan
    Write-Host "   p95: $($hitRateStats.p95)" -ForegroundColor Cyan
    Write-Host "   p99: $($hitRateStats.p99)" -ForegroundColor Cyan
  
    # Threshold recommendation
    $currentThreshold = 0.50
    $recommendedThreshold = [Math]::Max(0.30, $hitRateStats.p50 * 0.7)
    Write-Host "   Current Alert Threshold: < $currentThreshold" -ForegroundColor Yellow
    Write-Host "   Recommended Threshold: < $([Math]::Round($recommendedThreshold, 2))" -ForegroundColor Green
}
else {
    Write-Host "   No data" -ForegroundColor Red
}
Write-Host ""

# Memory Usage
Write-Host "2️⃣  Cache Memory Usage %" -ForegroundColor Yellow
$memoryStats = Get-Stats $memoryUsages
$analysis.cache_memory_usage_percent = $memoryStats
if ($memoryStats.count -gt 0) {
    Write-Host "   Count: $($memoryStats.count)" -ForegroundColor Gray
    Write-Host "   Min: $($memoryStats.min)%" -ForegroundColor Gray
    Write-Host "   Max: $($memoryStats.max)%" -ForegroundColor Gray
    Write-Host "   Mean: $([Math]::Round($memoryStats.mean, 1))%" -ForegroundColor Gray
    Write-Host "   p50: $($memoryStats.p50)%" -ForegroundColor Cyan
    Write-Host "   p90: $($memoryStats.p90)%" -ForegroundColor Cyan
    Write-Host "   p95: $($memoryStats.p95)%" -ForegroundColor Cyan
    Write-Host "   p99: $($memoryStats.p99)%" -ForegroundColor Cyan
  
    $currentThreshold = 90
    $recommendedThreshold = [Math]::Min(95, $memoryStats.p90 + 10)
    Write-Host "   Current Alert Threshold: > $currentThreshold%" -ForegroundColor Yellow
    Write-Host "   Recommended Threshold: > $([Math]::Round($recommendedThreshold, 0))%" -ForegroundColor Green
}
else {
    Write-Host "   No data" -ForegroundColor Red
}
Write-Host ""

# Avg TTL
Write-Host "3️⃣  Cache Avg TTL (seconds)" -ForegroundColor Yellow
$ttlStats = Get-Stats $avgTTLs
$analysis.cache_avg_ttl_seconds = $ttlStats
if ($ttlStats.count -gt 0) {
    Write-Host "   Count: $($ttlStats.count)" -ForegroundColor Gray
    Write-Host "   Min: $($ttlStats.min)s" -ForegroundColor Gray
    Write-Host "   Max: $($ttlStats.max)s" -ForegroundColor Gray
    Write-Host "   Mean: $([Math]::Round($ttlStats.mean, 0))s" -ForegroundColor Gray
    Write-Host "   p50: $($ttlStats.p50)s" -ForegroundColor Cyan
    Write-Host "   p90: $($ttlStats.p90)s" -ForegroundColor Cyan
    Write-Host "   p95: $($ttlStats.p95)s" -ForegroundColor Cyan
    Write-Host "   p99: $($ttlStats.p99)s" -ForegroundColor Cyan
  
    $currentThreshold = 300
    $recommendedThreshold = [Math]::Max(60, $ttlStats.p50 * 0.5)
    Write-Host "   Current Alert Threshold: < ${currentThreshold}s" -ForegroundColor Yellow
    Write-Host "   Recommended Threshold: < $([Math]::Round($recommendedThreshold, 0))s" -ForegroundColor Green
}
else {
    Write-Host "   No data" -ForegroundColor Red
}
Write-Host ""

# Unified Health Score
Write-Host "4️⃣  Unified Health Score" -ForegroundColor Yellow
$healthStats = Get-Stats $healthScores
$analysis.unified_health_score = $healthStats
if ($healthStats.count -gt 0) {
    Write-Host "   Count: $($healthStats.count)" -ForegroundColor Gray
    Write-Host "   Min: $($healthStats.min)" -ForegroundColor Gray
    Write-Host "   Max: $($healthStats.max)" -ForegroundColor Gray
    Write-Host "   Mean: $([Math]::Round($healthStats.mean, 1))" -ForegroundColor Gray
    Write-Host "   p50: $($healthStats.p50)" -ForegroundColor Cyan
    Write-Host "   p90: $($healthStats.p90)" -ForegroundColor Cyan
    Write-Host "   p95: $($healthStats.p95)" -ForegroundColor Cyan
    Write-Host "   p99: $($healthStats.p99)" -ForegroundColor Cyan
  
    $currentThreshold = 60
    $recommendedThreshold = [Math]::Max(40, $healthStats.p50 * 0.7)
    Write-Host "   Current Alert Threshold: < $currentThreshold" -ForegroundColor Yellow
    Write-Host "   Recommended Threshold: < $([Math]::Round($recommendedThreshold, 0))" -ForegroundColor Green
}
else {
    Write-Host "   No data" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "=== Recommendations ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Based on $count data points from last $Hours hour(s):" -ForegroundColor Magenta
Write-Host ""

if ($hitRateStats.count -gt 0) {
    $hitRateRecommended = [Math]::Round([Math]::Max(0.30, $hitRateStats.p50 * 0.7), 2)
    Write-Host "1. Cache Hit Rate Alert:" -ForegroundColor Yellow
    Write-Host "   Current: p50 < 0.50" -ForegroundColor Gray
    Write-Host "   Suggested: p50 < $hitRateRecommended" -ForegroundColor Green
    Write-Host ""
}

if ($memoryStats.count -gt 0) {
    $memoryRecommended = [Math]::Round([Math]::Min(95, $memoryStats.p90 + 10), 0)
    Write-Host "2. Memory Usage Alert:" -ForegroundColor Yellow
    Write-Host "   Current: p90 > 90%" -ForegroundColor Gray
    Write-Host "   Suggested: p90 > ${memoryRecommended}%" -ForegroundColor Green
    Write-Host ""
}

if ($healthStats.count -gt 0) {
    $healthRecommended = [Math]::Round([Math]::Max(40, $healthStats.p50 * 0.7), 0)
    Write-Host "3. Health Score Alert:" -ForegroundColor Yellow
    Write-Host "   Current: p50 < 60" -ForegroundColor Gray
    Write-Host "   Suggested: p50 < $healthRecommended" -ForegroundColor Green
    Write-Host ""
}

Write-Host "📝 To apply these thresholds:" -ForegroundColor Cyan
Write-Host "   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_alert_policies.ps1 ``" -ForegroundColor Gray
Write-Host "     -ProjectId naeda-genesis ``" -ForegroundColor Gray
if ($hitRateStats.count -gt 0) {
    $hitRateRecommended = [Math]::Round([Math]::Max(0.30, $hitRateStats.p50 * 0.7), 2) * 100
    Write-Host "     -HitRateThresholdPercent $hitRateRecommended ``" -ForegroundColor Gray
}
if ($memoryStats.count -gt 0) {
    $memoryRecommended = [Math]::Round([Math]::Min(95, $memoryStats.p90 + 10), 0)
    Write-Host "     -MemoryThresholdPercent $memoryRecommended ``" -ForegroundColor Gray
}
if ($healthStats.count -gt 0) {
    $healthRecommended = [Math]::Round([Math]::Max(40, $healthStats.p50 * 0.7), 0)
    Write-Host "     -HealthThreshold $healthRecommended" -ForegroundColor Gray
}
Write-Host ""

# Save JSON if requested
if ($OutputJson) {
    $output = @{
        timestamp      = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        project_id     = $ProjectId
        hours_analyzed = $Hours
        total_samples  = $count
        metrics        = $analysis
    }
    $output | ConvertTo-Json -Depth 10 | Set-Content $OutputJson
    Write-Host "✅ Analysis saved to: $OutputJson" -ForegroundColor Green
}
