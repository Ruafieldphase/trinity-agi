#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Feedback Loop Alert Policies 생성

.DESCRIPTION
    Unified health score와 cache hit rate 메트릭에 대한 alert policies를 생성합니다.
    
    Alerts:
    - Unified Health Score < 30 (CRITICAL)
    - Cache Hit Rate < 50% (WARNING)
    
.PARAMETER ProjectId
    GCP Project ID (기본: naeda-genesis)
    
.PARAMETER NotificationChannel
    알림 채널 ID (기본: projects/naeda-genesis/notificationChannels/13529545347198450079)
    
.PARAMETER DryRun
    실제 생성 없이 JSON만 출력
    
.EXAMPLE
    .\create_feedback_alert_policies.ps1
    .\create_feedback_alert_policies.ps1 -DryRun
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [string]$NotificationChannel = "projects/naeda-genesis/notificationChannels/13529545347198450079",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Feedback Loop Alert Policies Creator" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "ProjectId: $ProjectId" -ForegroundColor Yellow
Write-Host "NotificationChannel: $NotificationChannel" -ForegroundColor Yellow
Write-Host ""

# 1. Unified Health Score Alert (CRITICAL) - LOG-BASED
$healthAlertJson = @"
{
  "displayName": "Feedback Loop - Critical Health Score",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Unified Health Score < 30",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND jsonPayload.unified_health_score<30",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_COUNT"
          }
        ]
      }
    }
  ],
  "notificationChannels": ["$NotificationChannel"],
  "documentation": {
    "content": "## Critical: Unified Health Score Low\n\n**Threshold**: < 30\n**Duration**: 5 minutes\n\n### 원인\n- ROI가 매우 낮음 (< -50%)\n- SLO 미달\n- 캐시 성능 저하\n\n### 대응\n1. Feedback loop report 확인: \`outputs/feedback_loop_report.md\`\n2. Dashboard 확인: https://console.cloud.google.com/monitoring/dashboards/custom/260e1b13-9eef-4f20-9c00-50cc1f1ce686\n3. 캐시 성능 분석: \`cache_hit_rate\`, \`cache_memory_usage\`\n4. 비용 효율성 검토: ROI > -50% 목표\n",
    "mimeType": "text/markdown"
  },
  "enabled": true,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
"@

# 2. Cache Hit Rate Alert (WARNING) - LOG-BASED
$cacheAlertJson = @"
{
  "displayName": "Feedback Loop - Low Cache Hit Rate",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Cache Hit Rate < 50%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND jsonPayload.cache_hit_rate<0.5",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "600s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_COUNT"
          }
        ]
      }
    }
  ],
  "notificationChannels": ["$NotificationChannel"],
  "documentation": {
    "content": "## Warning: Low Cache Hit Rate\n\n**Threshold**: < 50%\n**Duration**: 10 minutes\n\n### 원인\n- 캐시 TTL이 너무 짧음\n- 캐시 메모리 부족으로 eviction 발생\n- 요청 패턴이 변경됨\n\n### 대응\n1. TTL 자동 조정 확인: \`AdaptiveTTLPolicy\` 로그\n2. 캐시 메모리 사용량 확인: \`cache_memory_usage\`\n3. 수동 TTL 증가: Redis TTL 설정 변경\n4. 캐시 크기 증가 고려\n",
    "mimeType": "text/markdown"
  },
  "enabled": true,
  "alertStrategy": {
    "autoClose": "3600s"
  }
}
"@

if ($DryRun) {
    Write-Host "===== Unified Health Score Alert Policy =====" -ForegroundColor Magenta
    $healthAlertJson
    Write-Host "`n===== Cache Hit Rate Alert Policy =====" -ForegroundColor Magenta
    $cacheAlertJson
    Write-Host "`n[DRY RUN] 실제 생성은 -DryRun 없이 실행하세요." -ForegroundColor Yellow
    exit 0
}

# Create Health Score Alert
Write-Host "Creating Unified Health Score Alert Policy..." -ForegroundColor Cyan
$healthAlertFile = "$env:TEMP\health_alert.json"
$healthAlertJson | Out-File -FilePath $healthAlertFile -Encoding UTF8

try {
    $token = gcloud auth print-access-token
    $healthResponse = Invoke-RestMethod -Method Post `
        -Uri "https://monitoring.googleapis.com/v3/projects/$ProjectId/alertPolicies" `
        -Headers @{Authorization = "Bearer $token"; "Content-Type" = "application/json" } `
        -Body $healthAlertJson
    
    Write-Host "✅ Created: $($healthResponse.displayName)" -ForegroundColor Green
    Write-Host "   Policy ID: $($healthResponse.name)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Failed to create Health Score alert: $_" -ForegroundColor Red
}

# Create Cache Hit Rate Alert
Write-Host "`nCreating Cache Hit Rate Alert Policy..." -ForegroundColor Cyan
$cacheAlertFile = "$env:TEMP\cache_alert.json"
$cacheAlertJson | Out-File -FilePath $cacheAlertFile -Encoding UTF8

try {
    $token = gcloud auth print-access-token
    $cacheResponse = Invoke-RestMethod -Method Post `
        -Uri "https://monitoring.googleapis.com/v3/projects/$ProjectId/alertPolicies" `
        -Headers @{Authorization = "Bearer $token"; "Content-Type" = "application/json" } `
        -Body $cacheAlertJson
    
    Write-Host "✅ Created: $($cacheResponse.displayName)" -ForegroundColor Green
    Write-Host "   Policy ID: $($cacheResponse.name)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Failed to create Cache Hit Rate alert: $_" -ForegroundColor Red
}

Write-Host "`n✅ Alert policies creation complete!" -ForegroundColor Green
Write-Host "`nVerify at: https://console.cloud.google.com/monitoring/alerting/policies?project=$ProjectId" -ForegroundColor Yellow
