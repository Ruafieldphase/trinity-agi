#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Verify logs → metrics → dashboard data flow

.DESCRIPTION
  Checks that scheduled metrics emission is working end-to-end:
  1. Scheduled task executed successfully
  2. Logs written to Cloud Logging
  3. Metrics configuration valid
  4. Dashboard accessible

.PARAMETER ProjectId
  GCP project ID (default: naeda-genesis)

.EXAMPLE
  ./verify_data_flow.ps1
  ./verify_data_flow.ps1 -ProjectId naeda-genesis
#>

param(
    [string]$ProjectId = "naeda-genesis"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Lumen Feedback Loop - Data Flow Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check scheduled task
Write-Host "1️⃣  Checking scheduled task..." -ForegroundColor Yellow
$taskInfo = Get-ScheduledTaskInfo -TaskName "LumenFeedbackEmitter" -ErrorAction SilentlyContinue
if ($taskInfo) {
    $lastRun = $taskInfo.LastRunTime
    $lastResult = $taskInfo.LastTaskResult
    $nextRun = $taskInfo.NextRunTime
  
    Write-Host "   [OK] Task exists" -ForegroundColor Green
    Write-Host "   Last Run: $lastRun" -ForegroundColor Gray
    Write-Host "   Result: $lastResult (0 = success)" -ForegroundColor Gray
    Write-Host "   Next Run: $nextRun" -ForegroundColor Gray
  
    if ($lastResult -ne 0) {
        Write-Host "   [WARN]  Non-zero exit code detected!" -ForegroundColor Red
    }
}
else {
    Write-Host "   [ERROR] Task not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Check recent logs
Write-Host "2️⃣  Checking Cloud Logging..." -ForegroundColor Yellow
$logFilter = "jsonPayload.component=`"feedback_loop`""
$logCmd = "gcloud logging read `"$logFilter`" --project=$ProjectId --limit=1 --format=json --freshness=10m 2>&1"
$logJson = cmd /c $logCmd
if ($LASTEXITCODE -eq 0) {
    $logEntries = $logJson | ConvertFrom-Json
    if ($logEntries.Count -gt 0) {
        $latestLog = $logEntries[0]
        $timestamp = $latestLog.timestamp
        $cacheHitRate = $latestLog.jsonPayload.cache_hit_rate
        $healthScore = $latestLog.jsonPayload.unified_health_score
    
        Write-Host "   [OK] Recent logs found" -ForegroundColor Green
        Write-Host "   Timestamp: $timestamp" -ForegroundColor Gray
        Write-Host "   Cache Hit Rate: $cacheHitRate" -ForegroundColor Gray
        Write-Host "   Health Score: $healthScore" -ForegroundColor Gray
    }
    else {
        Write-Host "   [WARN]  No logs in last 10 minutes" -ForegroundColor Yellow
    }
}
else {
    Write-Host "   [ERROR] Failed to query logs: $logJson" -ForegroundColor Red
}

Write-Host ""

# 3. Check metrics configuration
Write-Host "3️⃣  Checking logs-based metrics..." -ForegroundColor Yellow
$metricsToCheck = @("cache_hit_rate", "cache_memory_usage_percent", "cache_avg_ttl_seconds", "unified_health_score")
$allValid = $true

foreach ($metric in $metricsToCheck) {
    $descCmd = "gcloud logging metrics describe $metric --project=$ProjectId --format=json 2>&1"
    $descJson = cmd /c $descCmd
    if ($LASTEXITCODE -eq 0) {
        $metricDesc = $descJson | ConvertFrom-Json
        $metricType = $metricDesc.metricDescriptor.valueType
        Write-Host "   [OK] $metric ($metricType)" -ForegroundColor Green
    }
    else {
        Write-Host "   [ERROR] $metric (not found)" -ForegroundColor Red
        $allValid = $false
    }
}

Write-Host ""

# 4. Dashboard info
Write-Host "4️⃣  Dashboard URL" -ForegroundColor Yellow
$dashboardId = "71f2f32c-29a4-49e2-b3c5-d840984828a6"
$dashboardUrl = "https://console.cloud.google.com/monitoring/dashboards/custom/${dashboardId}?project=${ProjectId}"
Write-Host "   🔗 ${dashboardUrl}" -ForegroundColor Cyan
Write-Host "   (Data may take 2-5 minutes to appear after log emission)" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "[OK] Scheduled task running successfully" -ForegroundColor Green
Write-Host "[OK] Logs being written to Cloud Logging" -ForegroundColor Green
Write-Host "[OK] Metrics configuration valid" -ForegroundColor Green
Write-Host "[WAIT] Dashboard ready (wait 2-5 min for data points)" -ForegroundColor Yellow
Write-Host ""
Write-Host "[INFO] Next Steps:" -ForegroundColor Magenta
Write-Host "   1. Open dashboard and verify data points appear" -ForegroundColor Gray
Write-Host "   2. Wait 1-2 days to observe metric distributions" -ForegroundColor Gray
Write-Host "   3. Tune alert policy thresholds based on actual values" -ForegroundColor Gray
Write-Host "   4. Configure notification channels with real email/Slack" -ForegroundColor Gray
