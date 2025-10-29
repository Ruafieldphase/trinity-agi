# Rate Limit Probe Script
# 목적: API의 Rate Limiting 동작 검증 및 초당 처리량 한계 테스트
# Phase 4 Canary 배포 모니터링에 필수
#
# 사용 예:
#   .\rate_limit_probe.ps1 -RequestsPerSide 10 -DelayMsBetweenRequests 500
#   .\rate_limit_probe.ps1 -RequestsPerSide 50 -DelayMsBetweenRequests 100 -BaseUrl 'https://...'

param(
    [Parameter(Mandatory = $false)]
    [int]$RequestsPerSide = 10,

    [Parameter(Mandatory = $false)]
    [int]$DelayMsBetweenRequests = 500,

    [Parameter(Mandatory = $false)]
    [ValidateSet('GET', 'POST')]
    [string]$Method = 'GET',

    [Parameter(Mandatory = $false)]
    [string]$BaseUrl = 'https://ion-api-canary-x4qvsargwa-uc.a.run.app',

    [Parameter(Mandatory = $false)]
    [string]$LegacyUrl = 'https://ion-api-x4qvsargwa-uc.a.run.app',

    [Parameter(Mandatory = $false)]
    [string]$CanaryEndpointPath = '/api/v2/health',

    [Parameter(Mandatory = $false)]
    [string]$LegacyEndpointPath = '/health',

    [Parameter(Mandatory = $false)]
    [string]$CanaryBodyJson,

    [Parameter(Mandatory = $false)]
    [string]$LegacyBodyJson,

    [Parameter(Mandatory = $false)]
    [string]$OutJson
)

$ErrorActionPreference = 'Continue'

# Ensure TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Write-Host "[rate_limit_probe] Starting at $timestamp" -ForegroundColor Cyan
Write-Host "[rate_limit_probe] RequestsPerSide: $RequestsPerSide, Delay: ${DelayMsBetweenRequests}ms, Method: $Method" -ForegroundColor Gray

# 결과 추적
$results = @{
    canary = @{ success = 0; failed = 0; times = @(); errors = @() }
    legacy = @{ success = 0; failed = 0; times = @(); errors = @() }
}

# 기본 바디 정의 (미제공 시)
if (-not $CanaryBodyJson -and $Method -eq 'POST') {
    $CanaryBodyJson = @{ 
        user_id = ("probe-" + (Get-Date -Format 'yyyyMMddHHmmss'))
        query   = "Explain AI concepts in a concise style"
        options = @{ style = 'concise'; depth = 'overview' }
    } | ConvertTo-Json -Depth 5
}
if (-not $LegacyBodyJson -and $Method -eq 'POST') {
    $LegacyBodyJson = @{ message = "Explain AI concepts in a concise style" } | ConvertTo-Json -Depth 3
}

Write-Host "`n[rate_limit_probe] Testing Canary: $BaseUrl$CanaryEndpointPath" -ForegroundColor Cyan
$canaryBase = $BaseUrl.TrimEnd('/')
$canaryEndpoint = "$canaryBase$CanaryEndpointPath"

for ($i = 1; $i -le $RequestsPerSide; $i++) {
    $t0 = Get-Date
    try {
        if ($Method -eq 'GET') {
            $response = Invoke-RestMethod -Uri $canaryEndpoint -Method Get -TimeoutSec 30 -ErrorAction Stop
        }
        else {
            $response = Invoke-RestMethod -Uri $canaryEndpoint -Method Post -Body $CanaryBodyJson `
                -ContentType 'application/json' -TimeoutSec 30 -ErrorAction Stop
        }

        $t1 = Get-Date
        $elapsed = [int]($t1 - $t0).TotalMilliseconds

        $results.canary.success++
        $results.canary.times += $elapsed
        Write-Host "  [$i/$RequestsPerSide] OK - ${elapsed}ms" -ForegroundColor Green
    }
    catch {
        $results.canary.failed++
        $results.canary.errors += $_.Exception.Message
        Write-Host "  [$i/$RequestsPerSide] FAIL - $($_.Exception.Message)" -ForegroundColor Red
    }

    if ($i -lt $RequestsPerSide) {
        Start-Sleep -Milliseconds $DelayMsBetweenRequests
    }
}

# Legacy 테스트 (if provided)
if ($LegacyUrl -and $LegacyUrl.Trim().Length -gt 0) {
    Write-Host "`n[rate_limit_probe] Testing Legacy: $LegacyUrl$LegacyEndpointPath" -ForegroundColor Cyan
    $legacyBase = $LegacyUrl.TrimEnd('/')
    $legacyEndpoint = "$legacyBase$LegacyEndpointPath"

    for ($i = 1; $i -le $RequestsPerSide; $i++) {
        $t0 = Get-Date
        try {
            if ($Method -eq 'GET') {
                $response = Invoke-RestMethod -Uri $legacyEndpoint -Method Get -TimeoutSec 30 -ErrorAction Stop
            }
            else {
                $response = Invoke-RestMethod -Uri $legacyEndpoint -Method Post -Body $LegacyBodyJson `
                    -ContentType 'application/json' -TimeoutSec 30 -ErrorAction Stop
            }

            $t1 = Get-Date
            $elapsed = [int]($t1 - $t0).TotalMilliseconds

            $results.legacy.success++
            $results.legacy.times += $elapsed
            Write-Host "  [$i/$RequestsPerSide] OK - ${elapsed}ms" -ForegroundColor Green
        }
        catch {
            $results.legacy.failed++
            $results.legacy.errors += $_.Exception.Message
            Write-Host "  [$i/$RequestsPerSide] FAIL - $($_.Exception.Message)" -ForegroundColor Red
        }

        if ($i -lt $RequestsPerSide) {
            Start-Sleep -Milliseconds $DelayMsBetweenRequests
        }
    }
}

# 결과 요약
Write-Host "`n[rate_limit_probe] Results Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Gray

# Canary 통계
$canaryTotal = $results.canary.success + $results.canary.failed
if ($canaryTotal -gt 0) {
    $canarySuccessRate = [math]::Round(($results.canary.success / $canaryTotal) * 100, 2)
    Write-Host "Canary:" -ForegroundColor Yellow
    Write-Host "  Success: $($results.canary.success)/$canaryTotal ($canarySuccessRate%)" -ForegroundColor Green
    Write-Host "  Failed: $($results.canary.failed)" -ForegroundColor $(if ($results.canary.failed -eq 0) { 'Green' } else { 'Red' })

    if ($results.canary.times.Count -gt 0) {
        $avgTime = [math]::Round(($results.canary.times | Measure-Object -Average).Average, 0)
        $minTime = ($results.canary.times | Measure-Object -Minimum).Minimum
        $maxTime = ($results.canary.times | Measure-Object -Maximum).Maximum
        Write-Host "  Avg Response: ${avgTime}ms (Min: ${minTime}ms, Max: ${maxTime}ms)" -ForegroundColor White
    }
}

# Legacy 통계
if ($results.legacy.success -gt 0 -or $results.legacy.failed -gt 0) {
    $legacyTotal = $results.legacy.success + $results.legacy.failed
    $legacySuccessRate = [math]::Round(($results.legacy.success / $legacyTotal) * 100, 2)
    Write-Host "Legacy:" -ForegroundColor Yellow
    Write-Host "  Success: $($results.legacy.success)/$legacyTotal ($legacySuccessRate%)" -ForegroundColor Green
    Write-Host "  Failed: $($results.legacy.failed)" -ForegroundColor $(if ($results.legacy.failed -eq 0) { 'Green' } else { 'Red' })

    if ($results.legacy.times.Count -gt 0) {
        $avgTime = [math]::Round(($results.legacy.times | Measure-Object -Average).Average, 0)
        $minTime = ($results.legacy.times | Measure-Object -Minimum).Minimum
        $maxTime = ($results.legacy.times | Measure-Object -Maximum).Maximum
        Write-Host "  Avg Response: ${avgTime}ms (Min: ${minTime}ms, Max: ${maxTime}ms)" -ForegroundColor White
    }
}

Write-Host "`n[rate_limit_probe] Completed" -ForegroundColor Green

# 결과를 JSON으로 출력 (start_monitor_loop.ps1 호환성)
$output = @{
    timestamp = Get-Date -Format 'o'
    canary    = @{
        requests        = $RequestsPerSide
        success         = $results.canary.success
        failed          = $results.canary.failed
        success_rate    = if ($canaryTotal -gt 0) { $canarySuccessRate } else { 100 }
        avg_response_ms = if ($results.canary.times.Count -gt 0) { [math]::Round(($results.canary.times | Measure-Object -Average).Average, 0) } else { 0 }
    }
    legacy    = @{
        requests        = $RequestsPerSide
        success         = $results.legacy.success
        failed          = $results.legacy.failed
        success_rate    = if ($results.legacy.success -gt 0 -or $results.legacy.failed -gt 0) { [math]::Round(($results.legacy.success / ($results.legacy.success + $results.legacy.failed)) * 100, 2) } else { 100 }
        avg_response_ms = if ($results.legacy.times.Count -gt 0) { [math]::Round(($results.legacy.times | Measure-Object -Average).Average, 0) } else { 0 }
    }
} | ConvertTo-Json -Depth 3

Write-Host "`n$output"

# Save to file if -OutJson specified
if ($OutJson) {
    try {
        # Save without BOM for better Python compatibility
        [System.IO.File]::WriteAllText($OutJson, $output, [System.Text.UTF8Encoding]::new($false))
        Write-Host "[rate_limit_probe] Saved results to: $OutJson" -ForegroundColor Green
    }
    catch {
        Write-Warning "[rate_limit_probe] Failed to save JSON: $_"
    }
}
