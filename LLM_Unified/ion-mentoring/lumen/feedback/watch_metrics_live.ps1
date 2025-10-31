#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Watch dashboard for real-time updates

.DESCRIPTION
  Polls Cloud Logging and displays real-time metric updates in terminal

.PARAMETER ProjectId
  GCP project ID (default: naeda-genesis)

.PARAMETER RefreshSeconds
  Refresh interval (default: 5)

.EXAMPLE
  ./watch_metrics_live.ps1
  ./watch_metrics_live.ps1 -RefreshSeconds 10
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [int]$RefreshSeconds = 5
)

$ErrorActionPreference = "Stop"

Write-Host "=== Live Metrics Monitor ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Refresh: Every ${RefreshSeconds}s (Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

$iteration = 0
$lastTimestamp = ""

while ($true) {
    $iteration++
  
    # Query latest log entry
    $logFilter = "jsonPayload.component=`"feedback_loop`""
    $logCmd = "gcloud logging read `"$logFilter`" --project=$ProjectId --limit=1 --format=json --freshness=10m 2>&1"
    $logJson = cmd /c $logCmd
  
    if ($LASTEXITCODE -eq 0) {
        $logEntries = $logJson | ConvertFrom-Json
    
        if ($logEntries.Count -gt 0) {
            $latest = $logEntries[0]
            $timestamp = $latest.timestamp
            $payload = $latest.jsonPayload
      
            # Only display if new data
            if ($timestamp -ne $lastTimestamp) {
                $lastTimestamp = $timestamp
        
                Clear-Host
                Write-Host "=== Live Metrics Monitor ===" -ForegroundColor Cyan
                Write-Host "Last Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
                Write-Host "Iteration: #$iteration" -ForegroundColor Gray
                Write-Host ""
        
                # Parse timestamp
                $logTime = [DateTime]::Parse($timestamp).ToLocalTime()
                Write-Host "[METRICS] Latest Metrics" -ForegroundColor Yellow
                Write-Host "Timestamp: $logTime" -ForegroundColor Cyan
                Write-Host ""
        
                # Cache Hit Rate
                $hitRate = $payload.cache_hit_rate
                $hitRatePercent = [Math]::Round($hitRate * 100, 1)
                $hitRateColor = if ($hitRate -ge 0.7) { "Green" } elseif ($hitRate -ge 0.5) { "Yellow" } else { "Red" }
                $hitRateStatus = if ($hitRate -ge 0.7) { "[OK]" } elseif ($hitRate -ge 0.5) { "[WARN]" } else { "[CRIT]" }
                Write-Host "  $hitRateStatus Cache Hit Rate: ${hitRatePercent}%" -ForegroundColor $hitRateColor
        
                # Memory Usage
                $memUsage = $payload.cache_memory_usage_percent
                $memColor = if ($memUsage -le 75) { "Green" } elseif ($memUsage -le 90) { "Yellow" } else { "Red" }
                $memStatus = if ($memUsage -le 75) { "[OK]" } elseif ($memUsage -le 90) { "[WARN]" } else { "[CRIT]" }
                Write-Host "  $memStatus Memory Usage: ${memUsage}%" -ForegroundColor $memColor
        
                # Avg TTL
                $avgTTL = $payload.cache_avg_ttl_seconds
                $ttlMin = [Math]::Round($avgTTL / 60, 1)
                $ttlColor = if ($avgTTL -ge 600) { "Green" } elseif ($avgTTL -ge 300) { "Yellow" } else { "Red" }
                $ttlStatus = if ($avgTTL -ge 600) { "[OK]" } elseif ($avgTTL -ge 300) { "[WARN]" } else { "[CRIT]" }
                Write-Host "  $ttlStatus Avg TTL: ${avgTTL}s (${ttlMin} min)" -ForegroundColor $ttlColor
        
                # Health Score
                $health = $payload.unified_health_score
                $healthColor = if ($health -ge 80) { "Green" } elseif ($health -ge 60) { "Yellow" } else { "Red" }
                $healthStatus = if ($health -ge 80) { "[OK]" } elseif ($health -ge 60) { "[WARN]" } else { "[CRIT]" }
                Write-Host "  $healthStatus Health Score: ${health}/100" -ForegroundColor $healthColor
        
                Write-Host ""
                Write-Host "[STATS] Status Summary" -ForegroundColor Cyan
        
                $allGreen = ($hitRate -ge 0.7) -and ($memUsage -le 75) -and ($avgTTL -ge 600) -and ($health -ge 80)
                $anyRed = ($hitRate -lt 0.5) -or ($memUsage -gt 90) -or ($avgTTL -lt 300) -or ($health -lt 60)
        
                if ($allGreen) {
                    Write-Host "  [OK] All systems nominal" -ForegroundColor Green
                }
                elseif ($anyRed) {
                    Write-Host "  [CRITICAL] Issues detected" -ForegroundColor Red
                }
                else {
                    Write-Host "  [WARNING] Some metrics need attention" -ForegroundColor Yellow
                }
        
                Write-Host ""
                Write-Host "Press Ctrl+C to stop monitoring..." -ForegroundColor Gray
            }
        }
        else {
            Write-Host "[WAIT] Waiting for new metrics..." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "[ERROR] Failed to query logs" -ForegroundColor Red
    }
  
    Start-Sleep -Seconds $RefreshSeconds
}
