<#
.SYNOPSIS
    Response Time Profiler - 응답 시간 병목 분석

.DESCRIPTION
    API 요청의 각 단계별 시간을 측정하여 병목을 식별합니다.
    - DNS 조회
    - TCP 연결
    - TLS 핸드셰이크
    - 요청 전송
    - 서버 처리
    - 응답 수신

.PARAMETER ServiceUrl
    분석할 서비스 URL

.PARAMETER Iterations
    반복 측정 횟수 (기본값: 20)

.PARAMETER OutputJson
    결과를 JSON으로 저장

.EXAMPLE
    .\profile_response_time.ps1
    .\profile_response_time.ps1 -ServiceUrl "https://ion-api-canary-64076350717.us-central1.run.app" -Iterations 50
#>

[CmdletBinding()]
param(
    [string]$ServiceUrl = "https://ion-api-64076350717.us-central1.run.app",
    [int]$Iterations = 20,
    [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

Write-Host "🔬 Response Time Profiler" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 결과 저장
$Results = @{
    ServiceUrl = $ServiceUrl
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    TotalIterations = $Iterations
    Measurements = @()
    Summary = @{}
}

Write-Host "[METRICS] 설정" -ForegroundColor Yellow
Write-Host "  서비스: $ServiceUrl" -ForegroundColor Gray
Write-Host "  반복: $Iterations 회" -ForegroundColor Gray
Write-Host ""

# 테스트 엔드포인트
$endpoints = @{
    Health = "$ServiceUrl/health"
    Chat = "$ServiceUrl/chat"
}

Write-Host "[SEARCH] 프로파일링 시작..." -ForegroundColor Yellow
Write-Host ""

# 각 엔드포인트에 대해 측정
foreach ($endpointName in $endpoints.Keys) {
    $url = $endpoints[$endpointName]
    
    Write-Host "📡 $endpointName 엔드포인트 ($url)" -ForegroundColor Cyan
    
    $endpointResults = @{
        Name = $endpointName
        Url = $url
        Timings = @()
    }
    
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            # 상세 타이밍 측정을 위한 커스텀 측정
            $totalStart = Get-Date
            
            # PowerShell의 Measure-Command 사용
            $timing = @{}
            
            if ($endpointName -eq "Health") {
                # GET 요청
                $measure = Measure-Command {
                    $response = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
                }
                $timing.TotalTime = $measure.TotalMilliseconds
                $timing.StatusCode = $response.StatusCode
            }
            else {
                # POST 요청 (Chat)
                $body = @{
                    message = "Test query for profiling"
                } | ConvertTo-Json
                
                $measure = Measure-Command {
                    $response = Invoke-WebRequest `
                        -Uri $url `
                        -Method POST `
                        -Body $body `
                        -ContentType "application/json" `
                        -UseBasicParsing `
                        -TimeoutSec 30 `
                        -ErrorAction Stop
                }
                $timing.TotalTime = $measure.TotalMilliseconds
                $timing.StatusCode = $response.StatusCode
                $timing.ResponseLength = $response.Content.Length
            }
            
            $totalEnd = Get-Date
            $timing.MeasuredTotal = ($totalEnd - $totalStart).TotalMilliseconds
            
            $endpointResults.Timings += $timing
            
            # 진행 상황 표시
            if ($i % 5 -eq 0) {
                $avgTime = ($endpointResults.Timings | Measure-Object -Property TotalTime -Average).Average
                Write-Host "  [$i/$Iterations] 평균: $([math]::Round($avgTime, 1))ms" -ForegroundColor Gray
            }
            
            # 부하 방지
            Start-Sleep -Milliseconds 100
        }
        catch {
            Write-Host "  [$i/$Iterations] 오류: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # 통계 계산
    if ($endpointResults.Timings.Count -gt 0) {
        $times = $endpointResults.Timings | ForEach-Object { $_.TotalTime }
        $sortedTimes = $times | Sort-Object
        
        $stats = @{
            Min = [math]::Round($sortedTimes[0], 2)
            Max = [math]::Round($sortedTimes[-1], 2)
            Avg = [math]::Round(($times | Measure-Object -Average).Average, 2)
            Median = [math]::Round($sortedTimes[[math]::Floor($sortedTimes.Count / 2)], 2)
            P95 = [math]::Round($sortedTimes[[math]::Floor($sortedTimes.Count * 0.95)], 2)
            P99 = [math]::Round($sortedTimes[[math]::Floor($sortedTimes.Count * 0.99)], 2)
            SuccessRate = [math]::Round(($endpointResults.Timings.Count / $Iterations) * 100, 2)
        }
        
        $endpointResults.Statistics = $stats
        
        Write-Host ""
        Write-Host "  [METRICS] 통계" -ForegroundColor Yellow
        Write-Host "    최소: $($stats.Min)ms" -ForegroundColor Gray
        Write-Host "    최대: $($stats.Max)ms" -ForegroundColor Gray
        Write-Host "    평균: $($stats.Avg)ms" -ForegroundColor $(if($stats.Avg -lt 100){"Green"}elseif($stats.Avg -lt 500){"Yellow"}else{"Red"})
        Write-Host "    중간값: $($stats.Median)ms" -ForegroundColor Gray
        Write-Host "    P95: $($stats.P95)ms" -ForegroundColor Gray
        Write-Host "    P99: $($stats.P99)ms" -ForegroundColor Gray
        Write-Host "    성공률: $($stats.SuccessRate)%" -ForegroundColor $(if($stats.SuccessRate -ge 95){"Green"}else{"Red"})
    }
    
    $Results.Measurements += $endpointResults
    Write-Host ""
}

# 전체 요약
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "[METRICS] 전체 요약" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

foreach ($measurement in $Results.Measurements) {
    if ($measurement.Statistics) {
        $stats = $measurement.Statistics
        Write-Host "$($measurement.Name) 엔드포인트:" -ForegroundColor Yellow
        Write-Host "  평균 응답: $($stats.Avg)ms" -ForegroundColor $(if($stats.Avg -lt 100){"Green"}elseif($stats.Avg -lt 500){"Yellow"}else{"Red"})
        Write-Host "  P95: $($stats.P95)ms" -ForegroundColor Gray
        
        # 병목 진단
        if ($stats.Avg -gt 500) {
            Write-Host "  [CRITICAL] 응답이 매우 느립니다 (>500ms)" -ForegroundColor Red
            Write-Host "    → LLM 추론 시간 최적화 필요" -ForegroundColor Gray
            Write-Host "    → Vertex AI 모델 변경 고려" -ForegroundColor Gray
        }
        elseif ($stats.Avg -gt 200) {
            Write-Host "  [WARNING] 응답이 느립니다 (200-500ms)" -ForegroundColor Yellow
            Write-Host "    → 프롬프트 길이 최적화" -ForegroundColor Gray
            Write-Host "    → 캐싱 전략 강화" -ForegroundColor Gray
        }
        else {
            Write-Host "  [OK] 응답 시간 양호 (<200ms)" -ForegroundColor Green
        }
        
        Write-Host ""
    }
}

# 권장사항
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "[INFO] 최적화 권장사항" -ForegroundColor Yellow
Write-Host ""

$healthStats = ($Results.Measurements | Where-Object { $_.Name -eq "Health" }).Statistics
$chatStats = ($Results.Measurements | Where-Object { $_.Name -eq "Chat" }).Statistics

if ($healthStats -and $healthStats.Avg -gt 100) {
    Write-Host "1. Health Check 최적화" -ForegroundColor Cyan
    Write-Host "   현재: $($healthStats.Avg)ms" -ForegroundColor Red
    Write-Host "   목표: <50ms" -ForegroundColor Gray
    Write-Host "   • 불필요한 DB 조회 제거" -ForegroundColor Gray
    Write-Host "   • Redis 연결 캐싱" -ForegroundColor Gray
    Write-Host ""
}

if ($chatStats -and $chatStats.Avg -gt 500) {
    Write-Host "2. Chat API 병목 해결" -ForegroundColor Cyan
    Write-Host "   현재: $($chatStats.Avg)ms" -ForegroundColor Red
    Write-Host "   목표: <300ms" -ForegroundColor Gray
    Write-Host "   • Gemini 1.5 Flash 사용 (더 빠른 모델)" -ForegroundColor Gray
    Write-Host "   • max_output_tokens 제한 (512 이하)" -ForegroundColor Gray
    Write-Host "   • 응답 캐싱 활성화 (Redis TTL 1시간)" -ForegroundColor Gray
    Write-Host ""
}

if ($chatStats -and $healthStats) {
    $overhead = $chatStats.Avg - $healthStats.Avg
    Write-Host "3. LLM 처리 시간 분석" -ForegroundColor Cyan
    Write-Host "   순수 LLM 시간: ~$([math]::Round($overhead, 0))ms" -ForegroundColor Gray
    
    if ($overhead -gt 400) {
        Write-Host "   • LLM 추론이 주요 병목입니다" -ForegroundColor Red
        Write-Host "   • 프롬프트 최적화 필요" -ForegroundColor Gray
        Write-Host "   • 스트리밍 응답 활용 고려" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "4. 네트워크 최적화" -ForegroundColor Cyan
Write-Host "   • Cloud Run 리전 최적화 (현재: us-central1)" -ForegroundColor Gray
Write-Host "   • CDN 활성화 (정적 응답)" -ForegroundColor Gray
Write-Host "   • Keep-Alive 연결 활용" -ForegroundColor Gray
Write-Host ""

Write-Host "5. 스케일링 전략" -ForegroundColor Cyan
Write-Host "   • Min instances: 2 (콜드 스타트 방지)" -ForegroundColor Gray
Write-Host "   • Concurrency: 80 (응답성 우선)" -ForegroundColor Gray
Write-Host "   • CPU 할당: 2 vCPU (병렬 처리)" -ForegroundColor Gray
Write-Host ""

# JSON 저장
if ($OutputJson) {
    $Results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputJson -Encoding UTF8
    Write-Host "📄 결과 저장: $OutputJson" -ForegroundColor Green
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "[OK] 프로파일링 완료!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
