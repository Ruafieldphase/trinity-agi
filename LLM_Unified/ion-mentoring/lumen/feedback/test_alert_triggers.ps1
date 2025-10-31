#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Test alert policies by temporarily emitting metrics that violate thresholds

.DESCRIPTION
  Emits test metrics to trigger alerts for validation:
  - Low cache hit rate (< 0.50)
  - High memory usage (> 90%)
  - Low health score (< 60)

.PARAMETER ProjectId
  GCP project ID (default: naeda-genesis)

.PARAMETER TestScenario
  Which alert to test: 'hit-rate', 'memory', 'health', or 'all' (default: all)

.EXAMPLE
  ./test_alert_triggers.ps1
  ./test_alert_triggers.ps1 -TestScenario memory
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [ValidateSet("hit-rate", "memory", "health", "all")]
    [string]$TestScenario = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Alert Policy Test Trigger ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Test Scenario: $TestScenario" -ForegroundColor Gray
Write-Host ""

$pythonExe = "D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe"
$emitterScript = "D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/emit_feedback_metrics_once.py"

# Prepare test data
$testData = @{
    "hit-rate" = @{
        cache_hit_rate             = 0.3
        cache_memory_usage_percent = 65
        cache_avg_ttl_seconds      = 1200
        unified_health_score       = 85
    }
    "memory"   = @{
        cache_hit_rate             = 0.7
        cache_memory_usage_percent = 95
        cache_avg_ttl_seconds      = 1200
        unified_health_score       = 85
    }
    "health"   = @{
        cache_hit_rate             = 0.7
        cache_memory_usage_percent = 65
        cache_avg_ttl_seconds      = 1200
        unified_health_score       = 50
    }
}

function Emit-TestMetrics {
    param([hashtable]$metrics, [string]$description)
  
    Write-Host "[HOT] Emitting test metrics: $description" -ForegroundColor Yellow
    Write-Host "   Cache Hit Rate: $($metrics.cache_hit_rate)" -ForegroundColor Gray
    Write-Host "   Memory Usage: $($metrics.cache_memory_usage_percent)%" -ForegroundColor Gray
    Write-Host "   Health Score: $($metrics.unified_health_score)" -ForegroundColor Gray
  
    # Create temp Python script to emit custom values
    $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
  
    $scriptContent = @"
import logging
from google.cloud import logging as cloud_logging
import os

os.environ['GCP_PROJECT_ID'] = '$ProjectId'
os.environ['SERVICE_NAME'] = 'lumen-gateway'

client = cloud_logging.Client(project='$ProjectId')
logger = client.logger('feedback-loop-test')

payload = {
    'component': 'feedback_loop',
    'cache_hit_rate': $($metrics.cache_hit_rate),
    'cache_memory_usage_percent': $($metrics.cache_memory_usage_percent),
    'cache_avg_ttl_seconds': $($metrics.cache_avg_ttl_seconds),
    'unified_health_score': $($metrics.unified_health_score),
    'test_trigger': True
}

logger.log_struct(payload, severity='INFO')
print(f"[OK] Emitted test metrics to Cloud Logging")
"@
  
    Set-Content -Path $tempScript -Value $scriptContent
  
    try {
        & $pythonExe $tempScript
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Metrics emitted successfully" -ForegroundColor Green
        }
        else {
            Write-Host "   [ERROR] Failed to emit metrics" -ForegroundColor Red
        }
    }
    finally {
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
  
    Write-Host ""
}

# Execute tests
if ($TestScenario -eq "all") {
    Write-Host "[TEST] Testing all alert scenarios..." -ForegroundColor Magenta
    Write-Host ""
  
    Emit-TestMetrics $testData["hit-rate"] "Low Cache Hit Rate (0.3 < 0.5)"
    Start-Sleep -Seconds 2
  
    Emit-TestMetrics $testData["memory"] "High Memory Usage (95% > 90%)"
    Start-Sleep -Seconds 2
  
    Emit-TestMetrics $testData["health"] "Low Health Score (50 < 60)"
}
else {
    $description = switch ($TestScenario) {
        "hit-rate" { "Low Cache Hit Rate" }
        "memory" { "High Memory Usage" }
        "health" { "Low Health Score" }
    }
    Emit-TestMetrics $testData[$TestScenario] $description
}

Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Wait 2-5 minutes for metrics to populate" -ForegroundColor Gray
Write-Host "2. Wait 5+ minutes for alert policy evaluation" -ForegroundColor Gray
Write-Host "3. Check for alert notifications:" -ForegroundColor Gray
Write-Host "   - Email (if configured)" -ForegroundColor Gray
Write-Host "   - Slack (if configured)" -ForegroundColor Gray
Write-Host "   - GCP Console: https://console.cloud.google.com/monitoring/alerting?project=$ProjectId" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. View recent logs:" -ForegroundColor Gray
Write-Host "   gcloud logging read 'jsonPayload.test_trigger=true' --project=$ProjectId --limit=10 --freshness=10m" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Tip: Emit normal metrics again to clear alerts:" -ForegroundColor Magenta
Write-Host "   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/run_emit_feedback_metrics_once.ps1" -ForegroundColor Gray
