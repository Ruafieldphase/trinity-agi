<#
.SYNOPSIS
    Phase 4 Feedback Loop 대시보드 생성 스크립트

.DESCRIPTION
    Lumen v1.7 Phase 4: Cache Feedback Loop 모니터링을 위한 
    Google Cloud Monitoring 대시보드를 생성합니다.
    
    포함 위젯:
    1. Cache Hit Rate Scorecard (24h average)
    2. TTL Distribution (Histogram)
    3. Memory Usage Trend (Time series)
    4. Optimization History (Table)
    5. Unified Gate v1.7 Scorecard (Phase 1-4 통합)

.PARAMETER ProjectId
    GCP 프로젝트 ID

.PARAMETER ServiceName
    Cloud Run 서비스 이름 (기본값: lumen-gateway)

.PARAMETER DashboardName
    대시보드 이름 (기본값: Lumen v1.7 - Feedback Loop)

.EXAMPLE
    .\setup_feedback_dashboard.ps1 -ProjectId naeda-genesis
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory = $false)]
    [string]$ServiceName = "lumen-gateway",
    
    [Parameter(Mandatory = $false)]
    [string]$DashboardName = "Lumen v1.7 - Feedback Loop"
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Lumen v1.7 Phase 4: Feedback Loop Dashboard Setup          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# Dashboard JSON Configuration
# ============================================================================

$dashboardJson = @"
{
  "displayName": "$DashboardName",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "xPos": 0,
        "yPos": 0,
        "width": 3,
        "height": 3,
        "widget": {
          "title": "Cache Hit Rate (24h Avg)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_hit_rate\"",
                "aggregation": {
                  "alignmentPeriod": "86400s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_LINE"
            }
          }
        }
      },
      {
        "xPos": 3,
        "yPos": 0,
        "width": 3,
        "height": 3,
        "widget": {
          "title": "Memory Usage (%)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_memory_usage_pct\"",
                "aggregation": {
                  "alignmentPeriod": "3600s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_LINE"
            }
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 0,
        "width": 3,
        "height": 3,
        "widget": {
          "title": "Avg TTL (seconds)",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_avg_ttl_seconds\"",
                "aggregation": {
                  "alignmentPeriod": "3600s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_LINE"
            }
          }
        }
      },
      {
        "xPos": 9,
        "yPos": 0,
        "width": 3,
        "height": 3,
        "widget": {
          "title": "Unified Gate v1.7 Health",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/unified_health_score\"",
                "aggregation": {
                  "alignmentPeriod": "3600s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "sparkChartView": {
              "sparkChartType": "SPARK_LINE"
            }
          }
        }
      },
      {
        "xPos": 0,
        "yPos": 3,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cache Hit Rate Trend (Last 7 Days)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_hit_rate\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Hit Rate (%)",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 3,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Memory & Eviction Trend",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_memory_usage_pct\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_eviction_count\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y2"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Memory %",
              "scale": "LINEAR"
            },
            "y2Axis": {
              "label": "Evictions/hr",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            }
          }
        }
      },
      {
        "xPos": 0,
        "yPos": 7,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "TTL Distribution (Current)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/cache_ttl_bucket\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["metric.label.ttl_range"]
                    }
                  }
                },
                "plotType": "STACKED_BAR",
                "targetAxis": "Y1"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Count",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 7,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Optimization Actions (Last 24h)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/optimization_action\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["metric.label.action_type"]
                    }
                  }
                },
                "plotType": "STACKED_AREA",
                "targetAxis": "Y1"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Actions",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            }
          }
        }
      },
      {
        "xPos": 0,
        "yPos": 11,
        "width": 12,
        "height": 3,
        "widget": {
          "title": "Phase Integration Health (v1.7 Unified Gate)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/phase1_maturity_score\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/phase2_slo_compliance\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/phase3_cost_rhythm_score\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND metric.type=\"logging.googleapis.com/user/phase4_cache_health\"",
                    "aggregation": {
                      "alignmentPeriod": "3600s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                },
                "plotType": "LINE",
                "targetAxis": "Y1"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Score (0-100)",
              "scale": "LINEAR"
            },
            "chartOptions": {
              "mode": "COLOR"
            }
          }
        }
      },
      {
        "xPos": 0,
        "yPos": 14,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Feedback Loop Logs (Recent Events)",
          "logsPanel": {
            "resourceNames": [
              "projects/$ProjectId"
            ],
            "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$ServiceName\" AND (jsonPayload.component=\"feedback_loop\" OR textPayload=~\"feedback\" OR textPayload=~\"optimization\")"
          }
        }
      }
    ]
  }
}
"@

# ============================================================================
# Create Dashboard
# ============================================================================

Write-Host "[1/3] Dashboard JSON 준비 중..." -ForegroundColor Yellow
$tempFile = [System.IO.Path]::GetTempFileName()
$dashboardJson | Out-File -FilePath $tempFile -Encoding UTF8
Write-Host "      ✓ JSON 파일 생성: $tempFile" -ForegroundColor Green

Write-Host "`n[2/3] GCP에 대시보드 배포 중..." -ForegroundColor Yellow
$outputFile = [System.IO.Path]::GetTempFileName()
$cmdLine = "gcloud monitoring dashboards create --config-from-file=`"$tempFile`" --project=$ProjectId"
cmd /c "$cmdLine > `"$outputFile`" 2>&1"
$output = Get-Content -Path $outputFile -Raw
Remove-Item $outputFile -ErrorAction SilentlyContinue

# Extract dashboard ID from output (supports both format: "Created [uuid]" or "name: projects/.../dashboards/uuid")
if ($output -match "Created \[([a-f0-9\-]+)\]") {
    $dashboardId = $matches[1]
}
elseif ($output -match "name: projects/\d+/dashboards/([a-f0-9\-]+)") {
    $dashboardId = $matches[1]
}
else {
    $dashboardId = $null
}

if ($dashboardId) {
    Write-Host "      ✓ 대시보드 생성 완료" -ForegroundColor Green
    Write-Host "      Dashboard ID: $dashboardId" -ForegroundColor Cyan
}
else {
    Write-Host "      ✗ 대시보드 생성 실패 또는 ID 추출 불가" -ForegroundColor Red
    Write-Host "      GCP 출력: $output" -ForegroundColor Red
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    exit 1
}

# ============================================================================
# Cleanup & Output
# ============================================================================

Write-Host "`n[3/3] 정리 중..." -ForegroundColor Yellow
Remove-Item $tempFile -ErrorAction SilentlyContinue
Write-Host "      ✓ 임시 파일 삭제 완료" -ForegroundColor Green

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  [OK] Phase 4 Feedback Loop 대시보드 생성 완료!                ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "[METRICS] 대시보드 접근:" -ForegroundColor Cyan
Write-Host "   URL: https://console.cloud.google.com/monitoring/dashboards/custom/$dashboardId`?project=$ProjectId`n" -ForegroundColor White

Write-Host "📌 포함된 위젯 (10개):" -ForegroundColor Cyan
Write-Host "   1. Cache Hit Rate Scorecard (24h average)" -ForegroundColor White
Write-Host "   2. Memory Usage Scorecard" -ForegroundColor White
Write-Host "   3. Avg TTL Scorecard" -ForegroundColor White
Write-Host "   4. Unified Gate v1.7 Health Scorecard" -ForegroundColor White
Write-Host "   5. Cache Hit Rate Trend (7 days)" -ForegroundColor White
Write-Host "   6. Memory & Eviction Trend" -ForegroundColor White
Write-Host "   7. TTL Distribution (Stacked Bar)" -ForegroundColor White
Write-Host "   8. Optimization Actions (24h)" -ForegroundColor White
Write-Host "   9. Phase Integration Health (v1.7 Unified)" -ForegroundColor White
Write-Host "  10. Feedback Loop Logs (Recent Events)`n" -ForegroundColor White

Write-Host "[INFO] 다음 단계:" -ForegroundColor Cyan
Write-Host "   1. feedback_loop_redis.py에서 Custom Metrics 로깅 구현" -ForegroundColor White
Write-Host "   2. Cloud Logging으로 메트릭 전송 (structured logging)" -ForegroundColor White
Write-Host "   3. 대시보드에서 실시간 데이터 확인" -ForegroundColor White
Write-Host "   4. SLO 임계값 튜닝 (hit rate: 60%+, memory: <90%)`n" -ForegroundColor White

Write-Host "🎵 Lumen v1.7 = Phase 1 + Phase 2 + Phase 3 + Phase 4 (Complete!)" -ForegroundColor Magenta
Write-Host ""
