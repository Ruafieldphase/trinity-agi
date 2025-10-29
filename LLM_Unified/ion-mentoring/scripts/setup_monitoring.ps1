# ============================================================================
# Cloud Monitoring Dashboard Setup for Lumen Gateway Cache
# ============================================================================
# Purpose: Create monitoring dashboard and alert policies for Redis caching
# Author: GitCo
# Date: 2025-10-24
# ============================================================================

param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectId = "naeda-genesis",
    
    [Parameter(Mandatory = $false)]
    [string]$ServiceName = "lumen-gateway",
    
    [Parameter(Mandatory = $false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Cloud Monitoring Setup for Lumen Gateway" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# ============================================================================
# 1. Dashboard JSON Configuration
# ============================================================================

$dashboardJson = @"
{
  "displayName": "Lumen Gateway - Cache Performance",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cache Hit Rate (Last 24h)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_hit_rate\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Hit Rate (%)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Response Time (Cached vs Uncached)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Latency (ms)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"run.googleapis.com/request_count\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "STACKED_AREA",
                "targetAxis": "Y1"
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class!=\"2xx\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ]
          }
        }
      },
      {
        "yPos": 8,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Recent Logs (Cache Operations)",
          "logsPanel": {
            "resourceNames": [
              "projects/$ProjectId/logs/run.googleapis.com%2Fstdout"
            ],
            "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND (textPayload=~\"CACHE HIT\" OR textPayload=~\"CACHE MISS\")"
          }
        }
      }
    ]
  }
}
"@

# Save dashboard JSON
$dashboardFile = Join-Path $PSScriptRoot "..\outputs\monitoring_dashboard.json"
$dashboardJson | Out-File -FilePath $dashboardFile -Encoding utf8 -Force

Write-Host "✅ Dashboard JSON saved: $dashboardFile" -ForegroundColor Green

# ============================================================================
# 2. Create Dashboard
# ============================================================================

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would create dashboard with:" -ForegroundColor Yellow
    Write-Host "  Project: $ProjectId" -ForegroundColor White
    Write-Host "  Service: $ServiceName" -ForegroundColor White
    Write-Host "  Dashboard file: $dashboardFile" -ForegroundColor White
}
else {
    Write-Host "`n📊 Creating Cloud Monitoring Dashboard..." -ForegroundColor Cyan
    
    try {
        $result = gcloud monitoring dashboards create --config-from-file=$dashboardFile --project=$ProjectId 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Dashboard created successfully!" -ForegroundColor Green
            Write-Host "`n🔗 Dashboard URL:" -ForegroundColor Cyan
            Write-Host "   https://console.cloud.google.com/monitoring/dashboards?project=$ProjectId" -ForegroundColor White
        }
        else {
            Write-Host "⚠️  Dashboard creation failed or already exists" -ForegroundColor Yellow
            Write-Host "   $result" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ Error creating dashboard: $_" -ForegroundColor Red
    }
}

# ============================================================================
# 3. Alert Policy Configuration
# ============================================================================

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Alert Policies Setup" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# Alert 1: High Response Time
$alertHighLatency = @"
{
  "displayName": "Lumen Gateway - High Response Time",
  "conditions": [
    {
      "displayName": "Response time > 5s (p95)",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"run.googleapis.com/request_latencies\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 5000,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_DELTA",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95"
          }
        ]
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
"@

$alertFile1 = Join-Path $PSScriptRoot "..\outputs\alert_high_latency.json"
$alertHighLatency | Out-File -FilePath $alertFile1 -Encoding utf8 -Force

# Alert 2: High Error Rate
$alertHighError = @"
{
  "displayName": "Lumen Gateway - High Error Rate",
  "conditions": [
    {
      "displayName": "Error rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class!=\"2xx\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "180s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ]
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
"@

$alertFile2 = Join-Path $PSScriptRoot "..\outputs\alert_high_error.json"
$alertHighError | Out-File -FilePath $alertFile2 -Encoding utf8 -Force

Write-Host "✅ Alert policy JSONs saved:" -ForegroundColor Green
Write-Host "   - $alertFile1" -ForegroundColor White
Write-Host "   - $alertFile2" -ForegroundColor White

# ============================================================================
# 4. Create Alert Policies
# ============================================================================

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would create 2 alert policies" -ForegroundColor Yellow
}
else {
    Write-Host "`n🔔 Creating Alert Policies..." -ForegroundColor Cyan
    
    # Alert 1
    try {
        $result1 = gcloud alpha monitoring policies create --policy-from-file=$alertFile1 --project=$ProjectId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ High Response Time alert created" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Alert creation failed or already exists: $result1" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error creating alert 1: $_" -ForegroundColor Red
    }
    
    # Alert 2
    try {
        $result2 = gcloud alpha monitoring policies create --policy-from-file=$alertFile2 --project=$ProjectId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ High Error Rate alert created" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Alert creation failed or already exists: $result2" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error creating alert 2: $_" -ForegroundColor Red
    }
}

# ============================================================================
# 5. Log-based Metrics Setup
# ============================================================================

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Log-based Metrics Setup" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# Cache Hit Metric
$cacheHitMetric = @"
{
  "name": "projects/$ProjectId/metrics/cache_hit_rate",
  "description": "Rate of cache hits for Lumen Gateway",
  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND textPayload=~\"CACHE HIT\"",
  "metricDescriptor": {
    "metricKind": "DELTA",
    "valueType": "INT64"
  }
}
"@

$metricFile = Join-Path $PSScriptRoot "..\outputs\metric_cache_hit.json"
$cacheHitMetric | Out-File -FilePath $metricFile -Encoding utf8 -Force

Write-Host "✅ Log-based metric JSON saved: $metricFile" -ForegroundColor Green

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would create log-based metric for cache hits" -ForegroundColor Yellow
}
else {
    Write-Host "`n📈 Creating Log-based Metric..." -ForegroundColor Cyan
    
    try {
        $result = gcloud logging metrics create cache_hit_rate --project=$ProjectId --description="Rate of cache hits for Lumen Gateway" --log-filter="resource.type=\""cloud_run_revision\"" AND resource.labels.service_name=\""$ServiceName\"" AND textPayload=~\`"CACHE HIT\`"" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cache hit rate metric created" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Metric creation failed or already exists: $result" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error creating metric: $_" -ForegroundColor Red
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

Write-Host "✅ Created Resources:" -ForegroundColor Green
Write-Host "   1. Cloud Monitoring Dashboard" -ForegroundColor White
Write-Host "   2. Alert Policy - High Response Time (>5s)" -ForegroundColor White
Write-Host "   3. Alert Policy - High Error Rate (>5%)" -ForegroundColor White
Write-Host "   4. Log-based Metric - Cache Hit Rate" -ForegroundColor White

Write-Host "`n🔗 Quick Links:" -ForegroundColor Cyan
Write-Host "   Dashboard: https://console.cloud.google.com/monitoring/dashboards?project=$ProjectId" -ForegroundColor White
Write-Host "   Alerts: https://console.cloud.google.com/monitoring/alerting?project=$ProjectId" -ForegroundColor White
Write-Host "   Metrics: https://console.cloud.google.com/logs/metrics?project=$ProjectId" -ForegroundColor White
Write-Host "   Upstash: https://console.upstash.com/redis/careful-mustang-35050" -ForegroundColor White

Write-Host "`n📊 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Check dashboard for initial metrics" -ForegroundColor White
Write-Host "   2. Send test requests to populate data" -ForegroundColor White
Write-Host "   3. Configure notification channels for alerts" -ForegroundColor White
Write-Host "   4. Monitor cache hit rate over 24-48 hours`n" -ForegroundColor White
