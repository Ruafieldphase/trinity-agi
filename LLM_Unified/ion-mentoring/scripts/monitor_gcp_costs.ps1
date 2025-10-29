<#
.SYNOPSIS
    GCP Cost Monitor - 비용 모니터링 및 예산 알림

.DESCRIPTION
    GCP 프로젝트의 비용을 모니터링하고 예산 초과 시 알림을 제공합니다.
    - Cloud Run 서비스별 비용
    - 일일/월간 비용 추이
    - 예산 대비 사용률
    - 비용 절감 권장사항

.PARAMETER ProjectId
    GCP 프로젝트 ID

.PARAMETER Days
    조회 기간 (일) (기본값: 7)

.PARAMETER MonthlyBudget
    월 예산 (USD) (기본값: 200)

.PARAMETER OutputJson
    결과를 JSON으로 저장

.EXAMPLE
    .\monitor_gcp_costs.ps1 -ProjectId "naeda-genesis"
    .\monitor_gcp_costs.ps1 -ProjectId "naeda-genesis" -Days 30 -MonthlyBudget 300
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [int]$Days = 7,
    [double]$MonthlyBudget = 200.0,
    [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

Write-Host "💰 GCP Cost Monitor" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 설정" -ForegroundColor Yellow
Write-Host "  프로젝트: $ProjectId" -ForegroundColor Gray
Write-Host "  조회 기간: 최근 $Days 일" -ForegroundColor Gray
Write-Host "  월 예산: `$$MonthlyBudget USD" -ForegroundColor Gray
Write-Host ""

# 결과 저장
$Results = @{
    ProjectId = $ProjectId
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Period = "$Days days"
    MonthlyBudget = $MonthlyBudget
    Services = @{}
    Summary = @{}
}

# 1. Cloud Run 서비스 비용 추정
Write-Host "🔍 1단계: Cloud Run 서비스 분석..." -ForegroundColor Yellow
Write-Host ""

try {
    # Main 서비스 정보
    $mainService = gcloud run services describe ion-api `
        --region=us-central1 `
        --project=$ProjectId `
        --format=json 2>&1 | ConvertFrom-Json
    
    $mainMinInstances = [int]$mainService.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
    $mainMaxInstances = [int]$mainService.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
    $mainCpu = $mainService.spec.template.spec.containers[0].resources.limits.cpu
    $mainMemory = $mainService.spec.template.spec.containers[0].resources.limits.memory
    
    # Canary 서비스 정보
    $canaryService = gcloud run services describe ion-api-canary `
        --region=us-central1 `
        --project=$ProjectId `
        --format=json 2>&1 | ConvertFrom-Json
    
    $canaryMinInstances = [int]$canaryService.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
    $canaryMaxInstances = [int]$canaryService.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
    $canaryCpu = $canaryService.spec.template.spec.containers[0].resources.limits.cpu
    $canaryMemory = $canaryService.spec.template.spec.containers[0].resources.limits.memory
    
    Write-Host "📦 ion-api (Main)" -ForegroundColor Cyan
    Write-Host "  Min/Max: $mainMinInstances/$mainMaxInstances" -ForegroundColor Gray
    Write-Host "  CPU: $mainCpu, Memory: $mainMemory" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "📦 ion-api-canary" -ForegroundColor Cyan
    Write-Host "  Min/Max: $canaryMinInstances/$canaryMaxInstances" -ForegroundColor Gray
    Write-Host "  CPU: $canaryCpu, Memory: $canaryMemory" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "⚠️  서비스 정보 조회 실패: $_" -ForegroundColor Yellow
}

# 2. 비용 추정 (Cloud Run 가격 기준)
Write-Host "💵 2단계: 비용 추정..." -ForegroundColor Yellow
Write-Host ""

# Cloud Run 가격 (us-central1, 2024 기준)
$pricing = @{
    CpuPerSecond = 0.00002400  # $0.000024 per vCPU-second
    MemoryPerGbSecond = 0.0000025  # $0.0000025 per GB-second
    RequestPer1M = 0.40  # $0.40 per million requests
}

# 월간 예상 비용 계산
function Calculate-MonthlyCost {
    param(
        [int]$MinInstances,
        [int]$AvgInstances,
        [double]$CpuCores,
        [double]$MemoryGb,
        [int]$AvgRequestsPerDay
    )
    
    $secondsPerMonth = 30 * 24 * 3600
    
    # 최소 인스턴스 비용 (항상 실행)
    $minInstanceCost = $MinInstances * (
        ($CpuCores * $pricing.CpuPerSecond * $secondsPerMonth) +
        ($MemoryGb * $pricing.MemoryPerGbSecond * $secondsPerMonth)
    )
    
    # 추가 스케일링 비용 (평균 실행 시간 50% 가정)
    $scalingCost = ($AvgInstances - $MinInstances) * 0.5 * (
        ($CpuCores * $pricing.CpuPerSecond * $secondsPerMonth) +
        ($MemoryGb * $pricing.MemoryPerGbSecond * $secondsPerMonth)
    )
    
    # 요청 비용
    $requestCost = ($AvgRequestsPerDay * 30 / 1000000) * $pricing.RequestPer1M
    
    return @{
        MinInstanceCost = [math]::Round($minInstanceCost, 2)
        ScalingCost = [math]::Round($scalingCost, 2)
        RequestCost = [math]::Round($requestCost, 2)
        Total = [math]::Round($minInstanceCost + $scalingCost + $requestCost, 2)
    }
}

# Main 서비스 비용 추정
$mainCpuNum = if ($mainCpu -match "(\d+)") { [int]$matches[1] } else { 2 }
$mainMemGb = if ($mainMemory -match "(\d+)") { [int]$matches[1] / 1024.0 } else { 1.0 }

$mainCost = Calculate-MonthlyCost `
    -MinInstances $mainMinInstances `
    -AvgInstances ([math]::Min($mainMinInstances + 2, $mainMaxInstances)) `
    -CpuCores $mainCpuNum `
    -MemoryGb $mainMemGb `
    -AvgRequestsPerDay 10000

$Results.Services.Main = @{
    Name = "ion-api"
    Config = @{
        MinInstances = $mainMinInstances
        MaxInstances = $mainMaxInstances
        Cpu = $mainCpu
        Memory = $mainMemory
    }
    EstimatedMonthlyCost = $mainCost
}

Write-Host "💰 ion-api (Main) 월간 예상 비용" -ForegroundColor Cyan
Write-Host "  최소 인스턴스 비용: `$$($mainCost.MinInstanceCost)" -ForegroundColor Gray
Write-Host "  스케일링 비용: `$$($mainCost.ScalingCost)" -ForegroundColor Gray
Write-Host "  요청 비용: `$$($mainCost.RequestCost)" -ForegroundColor Gray
Write-Host "  총 예상 비용: `$$($mainCost.Total)" -ForegroundColor $(if($mainCost.Total -lt 100){"Green"}else{"Yellow"})
Write-Host ""

# Canary 서비스 비용 추정
$canaryCpuNum = if ($canaryCpu -match "(\d+)") { [int]$matches[1] } else { 1 }
$canaryMemGb = if ($canaryMemory -match "(\d+)") { [int]$matches[1] / 1024.0 } else { 0.5 }

$canaryCost = Calculate-MonthlyCost `
    -MinInstances $canaryMinInstances `
    -AvgInstances ([math]::Min($canaryMinInstances + 1, $canaryMaxInstances)) `
    -CpuCores $canaryCpuNum `
    -MemoryGb $canaryMemGb `
    -AvgRequestsPerDay 1000

$Results.Services.Canary = @{
    Name = "ion-api-canary"
    Config = @{
        MinInstances = $canaryMinInstances
        MaxInstances = $canaryMaxInstances
        Cpu = $canaryCpu
        Memory = $canaryMemory
    }
    EstimatedMonthlyCost = $canaryCost
}

Write-Host "💰 ion-api-canary 월간 예상 비용" -ForegroundColor Cyan
Write-Host "  최소 인스턴스 비용: `$$($canaryCost.MinInstanceCost)" -ForegroundColor Gray
Write-Host "  스케일링 비용: `$$($canaryCost.ScalingCost)" -ForegroundColor Gray
Write-Host "  요청 비용: `$$($canaryCost.RequestCost)" -ForegroundColor Gray
Write-Host "  총 예상 비용: `$$($canaryCost.Total)" -ForegroundColor Green
Write-Host ""

# 3. 전체 요약
$totalEstimatedCost = $mainCost.Total + $canaryCost.Total
$budgetUsagePercent = [math]::Round(($totalEstimatedCost / $MonthlyBudget) * 100, 1)

$Results.Summary = @{
    TotalEstimatedMonthlyCost = [math]::Round($totalEstimatedCost, 2)
    MonthlyBudget = $MonthlyBudget
    BudgetUsagePercent = $budgetUsagePercent
    RemainingBudget = [math]::Round($MonthlyBudget - $totalEstimatedCost, 2)
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 전체 요약" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "💵 월간 예상 비용" -ForegroundColor Yellow
Write-Host "  Cloud Run 총합: `$$totalEstimatedCost" -ForegroundColor $(if($totalEstimatedCost -lt $MonthlyBudget){"Green"}else{"Red"})
Write-Host "  예산 대비: $budgetUsagePercent%" -ForegroundColor $(if($budgetUsagePercent -lt 80){"Green"}elseif($budgetUsagePercent -lt 100){"Yellow"}else{"Red"})
Write-Host "  남은 예산: `$$($Results.Summary.RemainingBudget)" -ForegroundColor Gray
Write-Host ""

# 4. 권장사항
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "💡 비용 최적화 권장사항" -ForegroundColor Yellow
Write-Host ""

if ($budgetUsagePercent -gt 100) {
    Write-Host "⚠️  예산 초과 위험!" -ForegroundColor Red
    Write-Host "  현재 추정치가 예산을 $([math]::Round($budgetUsagePercent - 100, 1))% 초과합니다." -ForegroundColor Red
    Write-Host ""
}

Write-Host "1. 즉시 실행 가능한 절감 방안" -ForegroundColor Cyan

if ($mainMinInstances -gt 1) {
    $savingsMain = ($mainCost.MinInstanceCost / $mainMinInstances) * ($mainMinInstances - 1)
    Write-Host "  - Main 최소 인스턴스를 $mainMinInstances -> 1로 조정" -ForegroundColor Gray
    Write-Host "    예상 절감: ~`$$([math]::Round($savingsMain, 2))/월" -ForegroundColor Green
}

if ($canaryMinInstances -gt 0) {
    Write-Host "  - Canary 최소 인스턴스를 $canaryMinInstances -> 0으로 조정" -ForegroundColor Gray
    Write-Host "    예상 절감: ~`$$([math]::Round($canaryCost.MinInstanceCost, 2))/월" -ForegroundColor Green
}

Write-Host ""
Write-Host "2. 리소스 최적화" -ForegroundColor Cyan
Write-Host "  - CPU: 2 vCPU -> 1 vCPU (성능 테스트 후)" -ForegroundColor Gray
Write-Host "    예상 절감: 약 50pct CPU 비용" -ForegroundColor Green
Write-Host "  - Memory: 1Gi -> 512Mi (메모리 사용량 모니터링 후)" -ForegroundColor Gray
Write-Host "    예상 절감: 약 50pct Memory 비용" -ForegroundColor Green
Write-Host ""

Write-Host "3. 트래픽 최적화" -ForegroundColor Cyan
Write-Host "  - 응답 캐싱 활성화 (히트율 80pct 목표)" -ForegroundColor Gray
Write-Host "    예상 절감: 요청 수 80pct 감소" -ForegroundColor Green
Write-Host "  - 불필요한 health check 빈도 감소" -ForegroundColor Gray
Write-Host "  - 배치 처리 활용 (가능한 경우)" -ForegroundColor Gray
Write-Host ""

Write-Host "4. 모니터링 및 알림" -ForegroundColor Cyan
Write-Host "  - Cloud Monitoring 대시보드 설정" -ForegroundColor Gray
Write-Host "  - 예산 알림 설정 (80pct, 100pct, 120pct)" -ForegroundColor Gray
Write-Host "  - 주간 비용 리뷰 자동화" -ForegroundColor Gray
Write-Host ""

# 5. 예산 알림 설정 가이드
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🔔 예산 알림 설정 방법" -ForegroundColor Yellow
Write-Host ""
Write-Host "Cloud Console에서 예산 및 알림 설정:" -ForegroundColor Gray
Write-Host "  1. https://console.cloud.google.com/billing/budgets?project=$ProjectId" -ForegroundColor Cyan
Write-Host "  2. '예산 만들기' 클릭" -ForegroundColor Gray
Write-Host "  3. 예산 금액: `$$MonthlyBudget USD" -ForegroundColor Gray
Write-Host "  4. 알림 임계값: 80pct, 100pct, 120pct" -ForegroundColor Gray
Write-Host "  5. 이메일 수신자 추가" -ForegroundColor Gray
Write-Host ""

# JSON 저장
if ($OutputJson) {
    $Results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputJson -Encoding UTF8
    Write-Host "📄 결과 저장: $OutputJson" -ForegroundColor Green
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ 비용 모니터링 완료!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
