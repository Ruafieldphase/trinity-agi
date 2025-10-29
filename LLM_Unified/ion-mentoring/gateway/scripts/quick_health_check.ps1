<#
.SYNOPSIS
    Cloud Run 간단 헬스체크
    
.DESCRIPTION
    ION API와 Canary 서비스의 헬스를 빠르게 확인합니다.
    
.PARAMETER Services
    확인할 서비스 목록 (ion-api, ion-api-canary, 또는 both)
    
.EXAMPLE
    .\quick_health_check.ps1
    두 서비스 모두 확인
    
.EXAMPLE
    .\quick_health_check.ps1 -Services ion-api
    메인 서비스만 확인
#>

[CmdletBinding()]
param(
    [ValidateSet("ion-api", "ion-api-canary", "both")]
    [string]$Services = "both"
)

$ErrorActionPreference = "Stop"

# 서비스 URL 정의
$ServiceUrls = @{
    "ion-api"        = "https://ion-api-64076350717.us-central1.run.app"
    "ion-api-canary" = "https://ion-api-canary-64076350717.us-central1.run.app"
}

function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [string]$Url
    )
    
    Write-Host "`n$('-' * 70)" -ForegroundColor Cyan
    Write-Host "Checking: $ServiceName" -ForegroundColor Cyan
    Write-Host "URL: $Url" -ForegroundColor Gray
    Write-Host "$('-' * 70)" -ForegroundColor Cyan
    
    try {
        $healthUrl = "$Url/health"
        $startTime = Get-Date
        
        $response = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        $duration = ((Get-Date) - $startTime).TotalMilliseconds
        
        # 성공
        Write-Host "✅ Status: " -NoNewline -ForegroundColor Green
        Write-Host $response.status -ForegroundColor White
        
        Write-Host "📦 Version: " -NoNewline -ForegroundColor Green
        Write-Host $response.version -ForegroundColor White
        
        Write-Host "🔧 Pipeline Ready: " -NoNewline -ForegroundColor Green
        Write-Host $response.pipeline_ready -ForegroundColor White
        
        Write-Host "⏱️  Response Time: " -NoNewline -ForegroundColor Green
        Write-Host "$([math]::Round($duration, 2)) ms" -ForegroundColor White
        
        return $true
    }
    catch {
        Write-Host "❌ FAILED" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        
        # HTTP 상태 코드 확인
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "HTTP Status: $statusCode" -ForegroundColor Yellow
        }
        
        return $false
    }
}

function Get-CloudRunServiceInfo {
    param(
        [string]$ServiceName
    )
    
    try {
        Write-Host "`n🔍 Cloud Run Service Info:" -ForegroundColor Cyan
        
        $serviceInfo = gcloud run services describe $ServiceName `
            --region=us-central1 `
            --project=naeda-genesis `
            --format="value(status.latestReadyRevisionName,status.traffic[0].percent)" `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $parts = $serviceInfo -split "`n"
            Write-Host "  Revision: $($parts[0])" -ForegroundColor White
            Write-Host "  Traffic: $($parts[1])%" -ForegroundColor White
        }
        else {
            Write-Host "  Unable to fetch service info" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  Error fetching service info: $_" -ForegroundColor Yellow
    }
}

# 메인 로직
Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "  ION API Health Check" -ForegroundColor White
Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "="*70 + "`n" -ForegroundColor Cyan

$results = @{}

if ($Services -eq "both") {
    foreach ($service in $ServiceUrls.Keys) {
        $results[$service] = Test-ServiceHealth -ServiceName $service -Url $ServiceUrls[$service]
        Get-CloudRunServiceInfo -ServiceName $service
    }
}
else {
    $results[$Services] = Test-ServiceHealth -ServiceName $Services -Url $ServiceUrls[$Services]
    Get-CloudRunServiceInfo -ServiceName $Services
}

# 요약
Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor White
Write-Host "="*70 -ForegroundColor Cyan

$totalChecks = $results.Count
$successfulChecks = ($results.Values | Where-Object { $_ -eq $true }).Count

Write-Host "`nTotal Checks: $totalChecks" -ForegroundColor White
Write-Host "Successful: $successfulChecks" -ForegroundColor Green
Write-Host "Failed: $($totalChecks - $successfulChecks)" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round($successfulChecks / $totalChecks * 100, 2))%" -ForegroundColor White

if ($successfulChecks -eq $totalChecks) {
    Write-Host "`n✅ All services are healthy!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n⚠️  Some services have issues" -ForegroundColor Yellow
    exit 1
}
