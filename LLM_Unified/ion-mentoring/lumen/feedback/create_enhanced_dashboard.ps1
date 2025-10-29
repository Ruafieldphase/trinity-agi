#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Create comprehensive monitoring dashboard with multiple views

.DESCRIPTION
  Creates an enhanced version of the feedback loop dashboard with:
  - Real-time metric charts (line charts)
  - Distribution histograms
  - Alert status indicators
  - SLO tracking

.PARAMETER ProjectId
  GCP project ID (default: naeda-genesis)

.PARAMETER DashboardName
  Dashboard display name (default: "Lumen v1.7 - Feedback Loop (Enhanced)")

.PARAMETER OutputFile
  Optional path to save dashboard JSON

.EXAMPLE
  ./create_enhanced_dashboard.ps1
  ./create_enhanced_dashboard.ps1 -ProjectId naeda-genesis -OutputFile dashboard.json
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [string]$DashboardName = "Lumen v1.7 - Feedback Loop (Enhanced)",
    [string]$OutputFile = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Creating Enhanced Monitoring Dashboard ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Dashboard: $DashboardName" -ForegroundColor Gray
Write-Host ""

# Dashboard JSON template
$dashboardJson = @"
{
  "displayName": "$DashboardName",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cache Hit Rate (Real-time)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Hit Rate",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            },
            "thresholds": []
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cache Memory Usage %",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_memory_usage_percent\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Memory %",
              "scale": "LINEAR"
            },
            "thresholds": []
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Unified Health Score",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/unified_health_score\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "Health Score",
              "scale": "LINEAR"
            },
            "thresholds": []
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cache Avg TTL (seconds)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_avg_ttl_seconds\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "yAxis": {
              "label": "TTL (s)",
              "scale": "LINEAR"
            },
            "thresholds": []
          }
        }
      },
      {
        "yPos": 8,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Cache Hit Rate Distribution (p50, p90, p99)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1",
                "legendTemplate": "Mean"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MAX",
                      "crossSeriesReducer": "REDUCE_MAX"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1",
                "legendTemplate": "Max"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MIN",
                      "crossSeriesReducer": "REDUCE_MIN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1",
                "legendTemplate": "Min"
              }
            ],
            "yAxis": {
              "label": "Hit Rate",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 12,
        "width": 4,
        "height": 3,
        "widget": {
          "title": "Active Alerts",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" resource.type=\"uptime_url\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_FRACTION_TRUE"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_LINE"
            },
            "thresholds": []
          }
        }
      },
      {
        "xPos": 4,
        "yPos": 12,
        "width": 4,
        "height": 3,
        "widget": {
          "title": "Logs Ingestion Rate",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                "aggregation": {
                  "alignmentPeriod": "300s",
                  "perSeriesAligner": "ALIGN_RATE"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_BAR"
            }
          }
        }
      },
      {
        "xPos": 8,
        "yPos": 12,
        "width": 4,
        "height": 3,
        "widget": {
          "title": "SLO: Cache Hit Rate > 50%",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"logging.googleapis.com/user/cache_hit_rate\" resource.type=\"global\"",
                "aggregation": {
                  "alignmentPeriod": "3600s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "gaugeView": {
              "lowerBound": 0,
              "upperBound": 1
            },
            "thresholds": []
          }
        }
      }
    ]
  }
}
"@

# Save to file if requested
if ($OutputFile) {
    Set-Content -Path $OutputFile -Value $dashboardJson
    Write-Host "??Dashboard JSON saved to: $OutputFile" -ForegroundColor Green
    Write-Host ""
}

# Create dashboard via gcloud
Write-Host "?? Creating dashboard in GCP..." -ForegroundColor Yellow

$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value $dashboardJson

try {
    $createCmd = "gcloud monitoring dashboards create --config-from-file=`"$tempFile`" --project=$ProjectId --format=json"
    $result = Invoke-Expression $createCmd 2>&1 | Out-String
  
    if ($LASTEXITCODE -eq 0) {
        $dashboard = $result | ConvertFrom-Json
        $dashboardId = $dashboard.name -replace "projects/\d+/dashboards/", ""
    
        Write-Host "??Dashboard created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Dashboard ID: $dashboardId" -ForegroundColor Cyan
        Write-Host "Dashboard URL:" -ForegroundColor Yellow
        $url = "https://console.cloud.google.com/monitoring/dashboards/custom/${dashboardId}?project=${ProjectId}"
        Write-Host $url -ForegroundColor Green
        Write-Host ""
    
        Write-Host "?�� Opening in browser..." -ForegroundColor Magenta
        Start-Process $url
    }
    else {
        Write-Host "??Failed to create dashboard" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
}
finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}
