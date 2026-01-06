# Analyze Latency Spikes from Monitoring Data
# Identifies patterns and root causes of latency spikes

param(
    [string]$MetricsFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\monitoring_metrics_latest.json",
    [int]$SpikeThreshold = 1000,  # ms
    [switch]$ExportReport,
    [string]$OutputFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\latency_spike_analysis.md"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Latency Spike Analysis" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Load metrics
if (-not (Test-Path $MetricsFile)) {
    Write-Host "Error: Metrics file not found: $MetricsFile" -ForegroundColor Red
    exit 1
}

$metrics = Get-Content $MetricsFile -Raw | ConvertFrom-Json

# Analyze Gateway latency spikes
$gateway = $metrics.Channels.Gateway
$hourlyLatencies = $gateway.HourlyLatency

Write-Host "Gateway Statistics:" -ForegroundColor Cyan
Write-Host "  Mean: $($gateway.Mean)ms" -ForegroundColor White
Write-Host "  Median: $($gateway.Median)ms" -ForegroundColor White
Write-Host "  Min: $($gateway.Min)ms" -ForegroundColor White
Write-Host "  Max: $($gateway.Max)ms" -ForegroundColor White
Write-Host "  P95: $($gateway.P95)ms" -ForegroundColor White
Write-Host "  Std Dev: $($gateway.Std)ms" -ForegroundColor White
Write-Host "  Spikes: $($gateway.Spikes)" -ForegroundColor Yellow
Write-Host ""

# Identify spike hours
$spikeHours = @()
for ($i = 0; $i -lt $hourlyLatencies.Count; $i++) {
    if ($hourlyLatencies[$i] -gt $SpikeThreshold) {
        $hour = $metrics.AvailabilityTimeline.Hours[$i]
        $spikeHours += @{
            Hour = $hour
            Latency = $hourlyLatencies[$i]
            Index = $i
        }
    }
}

Write-Host "Latency Spikes (>$($SpikeThreshold)ms):" -ForegroundColor Red
if ($spikeHours.Count -eq 0) {
    Write-Host "  No spikes detected in the last 24 hours" -ForegroundColor Green
}
else {
    foreach ($spike in $spikeHours) {
        Write-Host "  $($spike.Hour): $($spike.Latency)ms" -ForegroundColor Yellow
    }
}
Write-Host ""

# Pattern analysis
Write-Host "Pattern Analysis:" -ForegroundColor Cyan

# Time of day analysis
$peakHourSpikes = 0
$offPeakSpikes = 0

foreach ($spike in $spikeHours) {
    $hour = [datetime]::Parse($spike.Hour).Hour
    if ($hour -ge 9 -and $hour -le 18) {
        $peakHourSpikes++
    }
    else {
        $offPeakSpikes++
    }
}

Write-Host "  Peak hours (9-18): $peakHourSpikes spikes" -ForegroundColor White
Write-Host "  Off-peak hours: $offPeakSpikes spikes" -ForegroundColor White
Write-Host ""

# Critical alerts analysis
$criticalAlerts = $metrics.AlertsBySeverity.Critical | Where-Object { $_.Message -like "*Gateway*" }

Write-Host "Critical Gateway Alerts:" -ForegroundColor Red
if ($criticalAlerts.Count -eq 0) {
    Write-Host "  No critical alerts" -ForegroundColor Green
}
else {
    foreach ($alert in $criticalAlerts) {
        Write-Host "  [$($alert.Timestamp)] $($alert.Message)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Recommendations
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host ""

if ($gateway.Max -gt 2000) {
    Write-Host "[HIGH] Extreme Latency Spike Detected ($($gateway.Max)ms)" -ForegroundColor Red
    Write-Host "  Root Causes:" -ForegroundColor Yellow
    Write-Host "    - Network congestion or timeout" -ForegroundColor Gray
    Write-Host "    - Gateway cold start (if cloud-based)" -ForegroundColor Gray
    Write-Host "    - Upstream API rate limiting" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Actions:" -ForegroundColor Yellow
    Write-Host "    1. Check network stability during spike times" -ForegroundColor White
    Write-Host "    2. Implement circuit breaker pattern" -ForegroundColor White
    Write-Host "    3. Add fallback to local LLM for critical queries" -ForegroundColor White
    Write-Host "    4. Increase timeout threshold temporarily: 500ms -> 1500ms" -ForegroundColor White
    Write-Host ""
}

if ($gateway.Std -gt 100) {
    Write-Host "[MEDIUM] High Latency Variability (σ=$($gateway.Std)ms)" -ForegroundColor Yellow
    Write-Host "  This suggests inconsistent performance" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Actions:" -ForegroundColor Yellow
    Write-Host "    1. Monitor network quality (jitter, packet loss)" -ForegroundColor White
    Write-Host "    2. Consider dedicated connection or VPN" -ForegroundColor White
    Write-Host "    3. Implement adaptive timeout based on recent latency" -ForegroundColor White
    Write-Host ""
}

if ($peakHourSpikes -gt $offPeakSpikes * 2) {
    Write-Host "[INFO] Spikes correlate with peak hours" -ForegroundColor Cyan
    Write-Host "  This suggests load-related issues" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Actions:" -ForegroundColor Yellow
    Write-Host "    1. Schedule non-critical tasks during off-peak hours" -ForegroundColor White
    Write-Host "    2. Implement request queuing and rate limiting" -ForegroundColor White
    Write-Host ""
}

Write-Host "[RECOMMENDED] Adaptive Routing Policy Adjustment:" -ForegroundColor Green
Write-Host "  Current threshold: 500ms" -ForegroundColor White
Write-Host "  Suggested: 1000ms (to handle occasional spikes)" -ForegroundColor White
Write-Host "  Command: Update routing_policy.json manually or run optimizer" -ForegroundColor Gray
Write-Host ""

# Export report
if ($ExportReport) {
    $report = @"
# Latency Spike Analysis Report

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Analysis Period**: Last 24 hours

---

## Gateway Statistics

| Metric | Value |
|--------|-------|
| Mean | $($gateway.Mean)ms |
| Median | $($gateway.Median)ms |
| Min | $($gateway.Min)ms |
| Max | $($gateway.Max)ms |
| P95 | $($gateway.P95)ms |
| Std Dev | $($gateway.Std)ms |
| Spike Count | $($gateway.Spikes) |

---

## Detected Spikes (>$($SpikeThreshold)ms)

$(if ($spikeHours.Count -eq 0) { "_No spikes detected_" } else {
    ($spikeHours | ForEach-Object { "- **$($_.Hour)**: $($_.Latency)ms" }) -join "`n"
})

---

## Pattern Analysis

- **Peak Hour Spikes** (9-18): $peakHourSpikes
- **Off-Peak Spikes**: $offPeakSpikes

---

## Critical Alerts

$(if ($criticalAlerts.Count -eq 0) { "_No critical alerts_" } else {
    ($criticalAlerts | ForEach-Object { "- [$($_.Timestamp)] $($_.Message)" }) -join "`n"
})

---

## Recommendations

### High Priority

$(if ($gateway.Max -gt 2000) {
@"
- **Extreme latency spike** detected ($($gateway.Max)ms)
  - Investigate network during spike time
  - Implement circuit breaker pattern
  - Increase timeout: 500ms → 1500ms
"@
} else { "_None_" })

### Medium Priority

$(if ($gateway.Std -gt 100) {
@"
- **High variability** (σ=$($gateway.Std)ms)
  - Monitor network quality
  - Consider adaptive timeout
"@
} else { "_None_" })

### Suggested Actions

1. Adjust routing threshold: 500ms → 1000ms
2. Enable fallback to local LLM for critical queries
3. Implement request retry with exponential backoff

---

*Generated by Latency Spike Analysis Tool*
"@

    $report | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "Report exported: $OutputFile" -ForegroundColor Green
}

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""