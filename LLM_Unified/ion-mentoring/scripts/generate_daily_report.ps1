# 일일 모니터링 요약 리포트 생성 스크립트
# 목적: 지난 24시간의 모니터링 결과를 분석하고 요약 리포트 생성

param(
    [int]$Hours = 24,
    [string]$OutputPath
)

$ErrorActionPreference = 'Continue'

$logsDir = Join-Path $PSScriptRoot '..\logs'
if (-not (Test-Path $logsDir)) {
    Write-Host "[report] Logs directory not found: $logsDir" -ForegroundColor Red
    exit 1
}

$cutoffTime = (Get-Date).AddHours(-$Hours)
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
if (-not $OutputPath) {
    $OutputPath = Join-Path $logsDir "daily_report_$timestamp.txt"
}

Write-Host "[report] Generating report for last $Hours hours..." -ForegroundColor Cyan
Write-Host "[report] Cutoff time: $($cutoffTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray

# 리포트 헤더
$report = @"
================================================================================
ION Mentoring API - Monitoring Report
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Period: Last $Hours hours (since $($cutoffTime.ToString('yyyy-MM-dd HH:mm:ss')))
================================================================================

"@

# 1. 헬스 체크 결과 분석
$statusFiles = Get-ChildItem $logsDir -Filter "status_iter_*.json" -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -ge $cutoffTime } |
Sort-Object LastWriteTime

$healthyCount = 0
$unhealthyCount = 0
$errorRates = @()
$p95Latencies = @()
$anomalies = 0

foreach ($file in $statusFiles) {
    try {
        $json = Get-Content $file.FullName | ConvertFrom-Json
        if ($json.healthy) { $healthyCount++ } else { $unhealthyCount++ }
        if ($null -ne $json.error_rate_percent) { $errorRates += $json.error_rate_percent }
        if ($null -ne $json.p95_ms) { $p95Latencies += $json.p95_ms }
        if ($json.telemetry_anomaly) { $anomalies++ }
    }
    catch {
        Write-Warning "Failed to parse $($file.Name): $($_.Exception.Message)"
    }
}

$totalChecks = $healthyCount + $unhealthyCount
$healthPercent = if ($totalChecks -gt 0) { [math]::Round(($healthyCount / $totalChecks) * 100, 2) } else { 0 }

$report += @"
HEALTH CHECK SUMMARY
--------------------
Total Checks: $totalChecks
  ✓ Healthy: $healthyCount ($healthPercent%)
  ✗ Unhealthy: $unhealthyCount
  ⚠ Telemetry Anomalies: $anomalies

"@

if ($errorRates.Count -gt 0) {
    $avgErrorRate = [math]::Round(($errorRates | Measure-Object -Average).Average, 3)
    $maxErrorRate = [math]::Round(($errorRates | Measure-Object -Maximum).Maximum, 3)
    $report += @"
ERROR RATE STATISTICS
---------------------
  Average: $avgErrorRate%
  Maximum: $maxErrorRate%
  Threshold: 0.5%
  Status: $(if ($avgErrorRate -le 0.5) { '✓ PASS' } else { '✗ FAIL' })

"@
}

if ($p95Latencies.Count -gt 0) {
    $avgP95 = [math]::Round(($p95Latencies | Measure-Object -Average).Average, 2)
    $maxP95 = [math]::Round(($p95Latencies | Measure-Object -Maximum).Maximum, 2)
    $report += @"
P95 LATENCY STATISTICS
----------------------
  Average: ${avgP95}ms
  Maximum: ${maxP95}ms
  Threshold: 200ms
  Status: $(if ($avgP95 -le 200) { '✓ PASS' } else { '✗ FAIL' })

"@
}

# 2. 자동 복구 이력
$remFiles = Get-ChildItem $logsDir -Filter "auto_remediation_*.json" -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -ge $cutoffTime } |
Sort-Object LastWriteTime

$report += @"
AUTO-REMEDIATION HISTORY
------------------------
Total Remediation Attempts: $($remFiles.Count)

"@

if ($remFiles.Count -eq 0) {
    $report += "  (No remediation needed - excellent!)`n`n"
}
else {
    foreach ($file in $remFiles) {
        try {
            $json = Get-Content $file.FullName | ConvertFrom-Json
            $time = $file.LastWriteTime.ToString('HH:mm:ss')
            $report += "  [$time] Stage: $($json.stage), Healthy: $($json.healthy), DryRun: $($json.dry_run)`n"
        }
        catch {
            $report += "  [ERROR] Failed to parse $($file.Name)`n"
        }
    }
    $report += "`n"
}

# 3. 로그 파일 통계
$loopLogs = Get-ChildItem $logsDir -Filter "monitor_loop_*.log" -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -ge $cutoffTime }

$totalLogSize = ($loopLogs | Measure-Object -Property Length -Sum).Sum
$report += @"
LOG FILES STATISTICS
--------------------
  Monitor Loops: $($loopLogs.Count)
  Total Log Size: $([math]::Round($totalLogSize/1MB, 2)) MB
  Oldest Log: $(if ($loopLogs) { ($loopLogs | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') } else { 'N/A' })
  Newest Log: $(if ($loopLogs) { ($loopLogs | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') } else { 'N/A' })

"@

# 4. 전체 평가
$overallStatus = "EXCELLENT"
if ($unhealthyCount -gt 0) { $overallStatus = "ATTENTION NEEDED" }
if ($unhealthyCount -gt ($totalChecks * 0.1)) { $overallStatus = "CRITICAL" }

$report += @"
OVERALL ASSESSMENT
------------------
Status: $overallStatus
Uptime: $healthPercent%

"@

# 5. 요약 경로 메트릭 (새로 추가)
$summaryMetricsScript = Join-Path $PSScriptRoot "collect_summary_metrics.ps1"
if (Test-Path $summaryMetricsScript) {
    try {
        $summaryMetricsJson = & $summaryMetricsScript -Hours $Hours -LogsDir $logsDir -JsonOutput | ConvertFrom-Json
        
        $report += @"
SUMMARIZATION METRICS
---------------------
Summary Light Mode:
  Calls: $($summaryMetricsJson.summary_light.calls)
  Usage Rate: $($summaryMetricsJson.summary_light.usage_rate_percent)%

Cache Performance:
  Hits: $($summaryMetricsJson.cache.hits)
  Misses: $($summaryMetricsJson.cache.misses)
  Hit Rate: $($summaryMetricsJson.cache.hit_rate_percent)%
  Status: $(if ($summaryMetricsJson.cache.hit_rate_percent -ge 30) { '✓ PASS (≥30%)' } elseif ($summaryMetricsJson.cache.hit_rate_percent -ge 10) { '⚠ MARGINAL (≥10%)' } else { '✗ LOW (<10%)' })

Running Summary:
  Updates: $($summaryMetricsJson.running_summary.updates)
  Failures: $($summaryMetricsJson.running_summary.failures)
  Avg Length: $($summaryMetricsJson.running_summary.avg_length) chars
  Avg Bullets: $($summaryMetricsJson.running_summary.avg_bullets)
  Status: $(if ($summaryMetricsJson.running_summary.failures -eq 0) { '✓ PASS (No failures)' } else { '⚠ REVIEW (Failures detected)' })

Latency (Summary Requests):
  P50: $($summaryMetricsJson.latency.p50)ms
  P95: $($summaryMetricsJson.latency.p95)ms
  Avg: $($summaryMetricsJson.latency.avg)ms

"@
    }
    catch {
        $report += @"
SUMMARIZATION METRICS
---------------------
(Failed to collect: $($_.Exception.Message))

"@
    }
}
else {
    $report += @"
SUMMARIZATION METRICS
---------------------
(Metrics collection script not found)

"@
}

$report += "`n"

if ($overallStatus -eq "EXCELLENT") {
    $report += "System is operating within all thresholds. No action required.`n"
}
elseif ($overallStatus -eq "ATTENTION NEEDED") {
    $report += "Minor issues detected. Review unhealthy checks and consider adjustments.`n"
}
else {
    $report += "CRITICAL: Significant issues detected. Immediate investigation required.`n"
}

$report += @"

RECOMMENDATIONS
---------------
"@

if ($avgErrorRate -gt 0.5) {
    $report += "  ⚠ Error rate above threshold - investigate root cause`n"
}
if ($avgP95 -gt 200) {
    $report += "  ⚠ P95 latency above threshold - consider performance optimization`n"
}
if ($anomalies -gt 0) {
    $report += "  ⚠ Telemetry anomalies detected - verify monitoring setup`n"
}
if ($totalLogSize -gt 100MB) {
    $report += "  ℹ Log size exceeds 100MB - consider running cleanup_old_logs.ps1`n"
}

# 요약 메트릭 관련 권장사항
if ($summaryMetricsJson) {
    if ($summaryMetricsJson.cache.hit_rate_percent -lt 10) {
        $report += "  ⚠ Summary cache hit rate below 10% - review caching strategy`n"
    }
    if ($summaryMetricsJson.running_summary.failures -gt 0) {
        $report += "  ⚠ Running summary failures detected - check error logs`n"
    }
    if ($summaryMetricsJson.summary_light.usage_rate_percent -gt 0 -and $summaryMetricsJson.latency.p95 -gt 500) {
        $report += "  ⚠ Summary P95 latency above 500ms - consider optimization`n"
    }
    if ($summaryMetricsJson.summary_light.calls -gt 0 -and $summaryMetricsJson.summary_light.usage_rate_percent -lt 5) {
        $report += "  ℹ Low summary_light usage (<5%) - verify feature adoption`n"
    }
}

if ($overallStatus -eq "EXCELLENT") {
    $report += "  ✓ All metrics within acceptable ranges - continue monitoring`n"
}

$report += @"

================================================================================
End of Report
================================================================================
"@

# 리포트 저장
$report | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Host "[report] Report saved: $OutputPath" -ForegroundColor Green

# 콘솔에도 출력
Write-Host "`n$report" -ForegroundColor White

# 간단한 요약을 반환
Write-Host "`nQuick Summary:" -ForegroundColor Cyan
Write-Host "  Health: $healthyCount/$totalChecks checks passed ($healthPercent%)" -ForegroundColor $(if ($healthPercent -ge 95) { 'Green' } elseif ($healthPercent -ge 80) { 'Yellow' } else { 'Red' })
Write-Host "  Status: $overallStatus" -ForegroundColor $(if ($overallStatus -eq 'EXCELLENT') { 'Green' } elseif ($overallStatus -eq 'ATTENTION NEEDED') { 'Yellow' } else { 'Red' })

exit 0
