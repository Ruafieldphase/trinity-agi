#!/usr/bin/env pwsh
<#
.SYNOPSIS
    GCP Alert Policies 자동 생성 스크립트

.DESCRIPTION
    Task 1.2: Alert Policies 설정
    - Critical Alerts (5xx errors, high latency, instance count)
    - Warning Alerts (4xx errors, CPU/Memory usage)

.PARAMETER ProjectId
    GCP Project ID (기본: naeda-genesis)

.PARAMETER Services
    Cloud Run 서비스 이름 배열 (기본: ion-api, lumen-gateway)

.PARAMETER Email
    알림 수신 이메일 (기본: devops@ion-mentoring.com)

.PARAMETER ListOnly
    현재 Alert Policies만 조회

.PARAMETER DeleteAll
    모든 ION Alert Policies 삭제

.EXAMPLE
    .\create_alert_policies.ps1
    .\create_alert_policies.ps1 -ListOnly
    .\create_alert_policies.ps1 -DeleteAll
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [string[]]$Services = @("ion-api", "lumen-gateway"),
    [string]$Email = "devops@ion-mentoring.com",
    [switch]$ListOnly,
    [switch]$DeleteAll
)

$ErrorActionPreference = "Stop"

# 색상 출력 함수
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = ""
    )
    Write-Host "$Prefix$Message" -ForegroundColor $Color
}

# Notification Channel 생성/조회
function Get-OrCreateNotificationChannel {
    param(
        [string]$ProjectId,
        [string]$Email
    )
    
    Write-ColorOutput "📧 Notification Channel 확인 중... (email: $Email)" "Yellow"
    
    # 기존 채널 검색
    $channels = gcloud alpha monitoring channels list `
        --project=$ProjectId `
        --filter="type=email" `
        --format=json | ConvertFrom-Json
    
    foreach ($channel in $channels) {
        if ($channel.labels.email_address -eq $Email) {
            $channelId = $channel.name
            Write-ColorOutput "✅ 기존 Email Channel 발견: $channelId" "Green" "   "
            return $channelId
        }
    }
    
    # 새 채널 생성
    Write-ColorOutput "📧 새 Email Channel 생성 중: $Email" "Yellow" "   "
    
    $channel = gcloud alpha monitoring channels create `
        --project=$ProjectId `
        --display-name="ION Team Email" `
        --type=email `
        --channel-labels="email_address=$Email" `
        --format=json | ConvertFrom-Json
    
    $channelId = $channel.name
    Write-ColorOutput "✅ Email Channel 생성 완료: $channelId" "Green" "   "
    
    return $channelId
}

# Alert Policies 목록 조회
function Get-AlertPolicies {
    param([string]$ProjectId)
    
    Write-ColorOutput "`n📋 Alert Policies 조회 중..." "Yellow"
    
    $policies = gcloud alpha monitoring policies list `
        --project=$ProjectId `
        --format=json | ConvertFrom-Json
    
    Write-ColorOutput "✅ 총 $($policies.Count)개 Alert Policies 발견`n" "Green"
    
    foreach ($policy in $policies) {
        $displayName = if ($policy.displayName) { $policy.displayName } else { "Unknown" }
        Write-ColorOutput "   - $displayName" "White"
    }
    
    return $policies
}

# ION Alert Policies 삭제
function Remove-IonAlertPolicies {
    param([string]$ProjectId)
    
    Write-ColorOutput "`n🗑️ ION 관련 Alert Policies 삭제 중..." "Yellow"
    
    $policies = Get-AlertPolicies -ProjectId $ProjectId
    $ionPolicies = $policies | Where-Object { $_.displayName -like "*ION*" }
    
    if ($ionPolicies.Count -eq 0) {
        Write-ColorOutput "✅ 삭제할 ION Alert Policy 없음" "Green"
        return
    }
    
    foreach ($policy in $ionPolicies) {
        $displayName = $policy.displayName
        try {
            gcloud alpha monitoring policies delete $policy.name `
                --project=$ProjectId `
                --quiet
            Write-ColorOutput "   ✅ 삭제: $displayName" "Green"
        }
        catch {
            Write-ColorOutput "   ❌ 삭제 실패: $displayName" "Red"
        }
    }
}

# Critical Alert: 5xx Error Rate > 5%
function New-Critical5xxErrorAlert {
    param(
        [string]$ProjectId,
        [string]$ChannelId,
        [string]$ServiceName
    )
    
    Write-ColorOutput "`n🚨 Critical Alert 생성: $ServiceName 5xx Error Rate > 5%" "Red"
    
    $displayName = "ION Critical - $ServiceName 5xx Error > 5%"
    $filter = "resource.type=`"cloud_run_revision`" AND resource.labels.service_name=`"$ServiceName`" AND metric.type=`"run.googleapis.com/request_count`" AND metric.labels.response_code_class=`"5xx`""
    
    try {
        gcloud alpha monitoring policies create `
            --project=$ProjectId `
            --notification-channels=$ChannelId `
            --display-name="$displayName" `
            --condition-display-name="5xx Error Rate > 5%" `
            --condition-threshold-value=0.05 `
            --condition-threshold-duration=300s `
            --condition-threshold-filter="$filter" `
            --combiner=OR `
            --format=json | Out-Null
        
        Write-ColorOutput "   ✅ 생성 완료" "Green"
    }
    catch {
        Write-ColorOutput "   ❌ 생성 실패: $_" "Red"
    }
}

# Critical Alert: P99 Latency > 2000ms
function New-CriticalLatencyAlert {
    param(
        [string]$ProjectId,
        [string]$ChannelId,
        [string]$ServiceName
    )
    
    Write-ColorOutput "`n🚨 Critical Alert 생성: $ServiceName P99 Latency > 2000ms" "Red"
    
    $displayName = "ION Critical - $ServiceName P99 Latency > 2s"
    $filter = "resource.type=`"cloud_run_revision`" AND resource.labels.service_name=`"$ServiceName`" AND metric.type=`"run.googleapis.com/request_latencies`""
    
    try {
        gcloud alpha monitoring policies create `
            --project=$ProjectId `
            --notification-channels=$ChannelId `
            --display-name="$displayName" `
            --condition-display-name="P99 Latency > 2000ms" `
            --condition-threshold-value=2000 `
            --condition-threshold-duration=300s `
            --condition-threshold-filter="$filter" `
            --combiner=OR `
            --format=json | Out-Null
        
        Write-ColorOutput "   ✅ 생성 완료" "Green"
    }
    catch {
        Write-ColorOutput "   ❌ 생성 실패: $_" "Red"
    }
}

# Warning Alert: 4xx Error Rate > 10%
function New-Warning4xxErrorAlert {
    param(
        [string]$ProjectId,
        [string]$ChannelId,
        [string]$ServiceName
    )
    
    Write-ColorOutput "`n⚠️ Warning Alert 생성: $ServiceName 4xx Error Rate > 10%" "Yellow"
    
    $displayName = "ION Warning - $ServiceName 4xx Error > 10%"
    $filter = "resource.type=`"cloud_run_revision`" AND resource.labels.service_name=`"$ServiceName`" AND metric.type=`"run.googleapis.com/request_count`" AND metric.labels.response_code_class=`"4xx`""
    
    try {
        gcloud alpha monitoring policies create `
            --project=$ProjectId `
            --notification-channels=$ChannelId `
            --display-name="$displayName" `
            --condition-display-name="4xx Error Rate > 10%" `
            --condition-threshold-value=0.10 `
            --condition-threshold-duration=600s `
            --condition-threshold-filter="$filter" `
            --combiner=OR `
            --format=json | Out-Null
        
        Write-ColorOutput "   ✅ 생성 완료" "Green"
    }
    catch {
        Write-ColorOutput "   ❌ 생성 실패: $_" "Red"
    }
}

# Warning Alert: P95 Latency > 1500ms
function New-WarningP95LatencyAlert {
    param(
        [string]$ProjectId,
        [string]$ChannelId,
        [string]$ServiceName
    )
    
    Write-ColorOutput "`n⚠️ Warning Alert 생성: $ServiceName P95 Latency > 1500ms" "Yellow"
    
    $displayName = "ION Warning - $ServiceName P95 Latency > 1.5s"
    $filter = "resource.type=`"cloud_run_revision`" AND resource.labels.service_name=`"$ServiceName`" AND metric.type=`"run.googleapis.com/request_latencies`""
    
    try {
        gcloud alpha monitoring policies create `
            --project=$ProjectId `
            --notification-channels=$ChannelId `
            --display-name="$displayName" `
            --condition-display-name="P95 Latency > 1500ms" `
            --condition-threshold-value=1500 `
            --condition-threshold-duration=600s `
            --condition-threshold-filter="$filter" `
            --combiner=OR `
            --format=json | Out-Null
        
        Write-ColorOutput "   ✅ 생성 완료" "Green"
    }
    catch {
        Write-ColorOutput "   ❌ 생성 실패: $_" "Red"
    }
}

# 메인 실행
function Main {
    Write-ColorOutput "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "🚀 GCP Alert Policies 관리" "Green"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "📦 Project: $ProjectId" "White"
    Write-ColorOutput "📦 Services: $($Services -join ', ')" "White"
    
    # List-only 모드
    if ($ListOnly) {
        Get-AlertPolicies -ProjectId $ProjectId
        return
    }
    
    # Delete-all 모드
    if ($DeleteAll) {
        Remove-IonAlertPolicies -ProjectId $ProjectId
        return
    }
    
    # Notification Channel 생성/조회
    $channelId = Get-OrCreateNotificationChannel -ProjectId $ProjectId -Email $Email
    
    Write-ColorOutput "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "📧 Notification Channel: $channelId" "White"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    
    # 각 서비스별 Alert 생성
    foreach ($service in $Services) {
        Write-ColorOutput "`n─────────────────────────────────────────────────────" "Cyan"
        Write-ColorOutput "📦 Service: $service" "White"
        Write-ColorOutput "─────────────────────────────────────────────────────" "Cyan"
        
        # Critical Alerts
        New-Critical5xxErrorAlert -ProjectId $ProjectId -ChannelId $channelId -ServiceName $service
        New-CriticalLatencyAlert -ProjectId $ProjectId -ChannelId $channelId -ServiceName $service
        
        # Warning Alerts
        New-Warning4xxErrorAlert -ProjectId $ProjectId -ChannelId $channelId -ServiceName $service
        New-WarningP95LatencyAlert -ProjectId $ProjectId -ChannelId $channelId -ServiceName $service
    }
    
    Write-ColorOutput "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorOutput "✅ Alert Policies 생성 완료" "Green"
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    
    # 최종 확인
    Get-AlertPolicies -ProjectId $ProjectId
    
    Write-ColorOutput "`n📊 확인:" "Yellow"
    $url = "https://console.cloud.google.com/monitoring/alerting/policies?project=$ProjectId"
    Write-ColorOutput "   $url" "White"
}

# 실행
Main
