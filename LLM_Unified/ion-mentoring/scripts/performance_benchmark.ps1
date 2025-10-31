#Requires -Version 5.1
<#
.SYNOPSIS
    두 서비스의 성능을 자동으로 벤치마크하고 비교

.DESCRIPTION
    Main과 Canary 서비스의 응답시간, 에러율, 가용성을 측정하고 비교합니다.
    - 여러 번 요청하여 평균, 최소, 최대, 중간값 계산
    - 결과를 JSON 파일로 저장
    - 시계열 데이터 수집 (선택적)

.PARAMETER Iterations
    각 서비스당 테스트 반복 횟수 (기본값: 10)

.PARAMETER OutputFile
    결과를 저장할 JSON 파일 경로

.PARAMETER IncludeTimeSeries
    시계열 데이터 수집 여부

.EXAMPLE
    .\performance_benchmark.ps1
    기본 설정으로 벤치마크 실행

.EXAMPLE
    .\performance_benchmark.ps1 -Iterations 50 -OutputFile "outputs/benchmark_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    50회 반복, 결과 파일 지정
#>

param(
    [int]$Iterations = 10,
    [string]$OutputFile = "outputs\performance_benchmark_$(Get-Date -Format 'yyyyMMdd_HHmmss').json",
    [switch]$IncludeTimeSeries
)

$ErrorActionPreference = "Continue"

# 색상 출력 함수
function Write-ColorHost {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-ColorHost "==========================================" "Cyan"
    Write-ColorHost "  $Title" "Yellow"
    Write-ColorHost "==========================================" "Cyan"
    Write-Host ""
}

# 통계 계산 함수
function Calculate-Stats {
    param([array]$Values)
    
    $sorted = $Values | Sort-Object
    $count = $sorted.Count
    
    return @{
        min    = $sorted[0]
        max    = $sorted[-1]
        avg    = ($sorted | Measure-Object -Average).Average
        median = if ($count % 2 -eq 0) {
            ($sorted[[math]::Floor($count / 2) - 1] + $sorted[[math]::Floor($count / 2)]) / 2
        }
        else {
            $sorted[[math]::Floor($count / 2)]
        }
        p95    = $sorted[[math]::Floor($count * 0.95)]
        p99    = $sorted[[math]::Floor($count * 0.99)]
    }
}

# 서비스 벤치마크 함수
function Benchmark-Service {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$Iterations
    )
    
    Write-ColorHost "▶ 벤치마킹: $ServiceName" "Green"
    Write-ColorHost "  URL: $Url" "Gray"
    Write-ColorHost "  반복: $Iterations 회" "Gray"
    
    $responseTimes = @()
    $successCount = 0
    $errorCount = 0
    $timeSeries = @()
    
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $startTime = Get-Date
            $response = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 10 -ErrorAction Stop
            $endTime = Get-Date
            
            $responseTime = ($endTime - $startTime).TotalMilliseconds
            $responseTimes += $responseTime
            $successCount++
            
            if ($IncludeTimeSeries) {
                $timeSeries += @{
                    iteration        = $i
                    timestamp        = $startTime.ToString("yyyy-MM-ddTHH:mm:ss.fff")
                    response_time_ms = [math]::Round($responseTime, 2)
                    status           = "success"
                }
            }
            
            Write-Host "  [$i/$Iterations] $([math]::Round($responseTime, 2))ms" -NoNewline
            Write-ColorHost " ✓" "Green"
            
        }
        catch {
            $errorCount++
            if ($IncludeTimeSeries) {
                $timeSeries += @{
                    iteration        = $i
                    timestamp        = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fff")
                    response_time_ms = $null
                    status           = "error"
                    error            = $_.Exception.Message
                }
            }
            Write-Host "  [$i/$Iterations]" -NoNewline
            Write-ColorHost " ✗ ($($_.Exception.Message))" "Red"
        }
        
        Start-Sleep -Milliseconds 100
    }
    
    $stats = if ($responseTimes.Count -gt 0) {
        Calculate-Stats -Values $responseTimes
    }
    else {
        @{ min = 0; max = 0; avg = 0; median = 0; p95 = 0; p99 = 0 }
    }
    
    return @{
        service_name     = $ServiceName
        url              = $Url
        iterations       = $Iterations
        success_count    = $successCount
        error_count      = $errorCount
        success_rate     = [math]::Round(($successCount / $Iterations) * 100, 2)
        response_time_ms = $stats
        time_series      = if ($IncludeTimeSeries) { $timeSeries } else { $null }
    }
}

# 시작
Write-Header "Performance Benchmark"

Write-ColorHost "설정:" "White"
Write-ColorHost "  • 반복 횟수: $Iterations" "Gray"
Write-ColorHost "  • 결과 파일: $OutputFile" "Gray"
Write-ColorHost "  • 시계열 데이터: $(if($IncludeTimeSeries){'포함'}else{'제외'})" "Gray"
Write-Host ""

# Outputs 디렉토리 생성
$outputDir = Split-Path $OutputFile -Parent
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

# Main 서비스 벤치마크
$mainResults = Benchmark-Service `
    -ServiceName "ion-api (Main)" `
    -Url "https://ion-api-64076350717.us-central1.run.app/health" `
    -Iterations $Iterations

Write-Host ""

# Canary 서비스 벤치마크
$canaryResults = Benchmark-Service `
    -ServiceName "ion-api-canary" `
    -Url "https://ion-api-canary-64076350717.us-central1.run.app/health" `
    -Iterations $Iterations

# 비교 분석
Write-Header "비교 분석"

$avgDiff = (($canaryResults.response_time_ms.avg - $mainResults.response_time_ms.avg) / $mainResults.response_time_ms.avg) * 100
$medianDiff = (($canaryResults.response_time_ms.median - $mainResults.response_time_ms.median) / $mainResults.response_time_ms.median) * 100

Write-ColorHost "평균 응답시간:" "White"
Write-ColorHost "  Main:   $([math]::Round($mainResults.response_time_ms.avg, 2))ms" "Gray"
Write-ColorHost "  Canary: $([math]::Round($canaryResults.response_time_ms.avg, 2))ms" $(if ($avgDiff -lt 0) { "Green" }else { "Yellow" })
Write-ColorHost "  차이:   $([math]::Round($avgDiff, 2))%" $(if ($avgDiff -lt 0) { "Green" }else { "Yellow" })

Write-Host ""
Write-ColorHost "중간값 응답시간:" "White"
Write-ColorHost "  Main:   $([math]::Round($mainResults.response_time_ms.median, 2))ms" "Gray"
Write-ColorHost "  Canary: $([math]::Round($canaryResults.response_time_ms.median, 2))ms" $(if ($medianDiff -lt 0) { "Green" }else { "Yellow" })
Write-ColorHost "  차이:   $([math]::Round($medianDiff, 2))%" $(if ($medianDiff -lt 0) { "Green" }else { "Yellow" })

Write-Host ""
Write-ColorHost "성공률:" "White"
Write-ColorHost "  Main:   $($mainResults.success_rate)%" $(if ($mainResults.success_rate -ge 95) { "Green" }else { "Red" })
Write-ColorHost "  Canary: $($canaryResults.success_rate)%" $(if ($canaryResults.success_rate -ge 95) { "Green" }else { "Red" })

# 결과 저장
$results = @{
    benchmark_time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    config         = @{
        iterations          = $Iterations
        include_time_series = $IncludeTimeSeries
    }
    main           = $mainResults
    canary         = $canaryResults
    comparison     = @{
        avg_response_time_diff_percent    = [math]::Round($avgDiff, 2)
        median_response_time_diff_percent = [math]::Round($medianDiff, 2)
        winner                            = if ($avgDiff -lt 0) { "Canary" } else { "Main" }
        recommendation                    = if ($avgDiff -lt -10 -and $canaryResults.success_rate -ge 95) {
            "Canary가 Main보다 10% 이상 빠르고 안정적입니다. 승격을 고려하세요."
        }
        elseif ($avgDiff -lt 0 -and $canaryResults.success_rate -ge 95) {
            "Canary가 Main보다 빠르지만 차이가 작습니다. 현재 상태 유지 권장."
        }
        else {
            "Main이 Canary보다 성능이 좋거나 동등합니다. 현재 상태 유지."
        }
    }
}

$results | ConvertTo-Json -Depth 10 | Set-Content $OutputFile

Write-Header "완료"
Write-ColorHost "[OK] 벤치마크 완료!" "Green"
Write-ColorHost "  결과 파일: $OutputFile" "Gray"
Write-Host ""
Write-ColorHost "[INFO] 권장 사항:" "Cyan"
Write-ColorHost "  $($results.comparison.recommendation)" "Yellow"
Write-Host ""
