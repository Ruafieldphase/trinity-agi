<#
.SYNOPSIS
    Redis Cache Performance Analyzer

.DESCRIPTION
    ION API의 Redis 캐시 성능을 분석합니다.
    - 캐시 히트율
    - TTL 분포
    - 캐시 키 패턴
    - 메모리 사용량

.PARAMETER ServiceUrl
    서비스 URL (기본값: Main 서비스)

.PARAMETER Samples
    샘플링 횟수 (기본값: 100)

.PARAMETER OutputJson
    결과를 JSON 파일로 저장 (선택)

.EXAMPLE
    .\analyze_cache_performance.ps1
    .\analyze_cache_performance.ps1 -ServiceUrl "https://ion-api-canary-64076350717.us-central1.run.app" -Samples 200
    .\analyze_cache_performance.ps1 -OutputJson "cache_analysis.json"
#>

[CmdletBinding()]
param(
    [string]$ServiceUrl = "https://ion-api-64076350717.us-central1.run.app",
    [int]$Samples = 100,
    [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

Write-Host "🔍 Redis Cache Performance Analyzer" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 결과 저장
$Results = @{
    ServiceUrl            = $ServiceUrl
    Timestamp             = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    TotalSamples          = $Samples
    CacheHits             = 0
    CacheMisses           = 0
    ResponseTimes         = @()
    CachedResponseTimes   = @()
    UncachedResponseTimes = @()
    UniqueQueries         = @()
}

# 테스트 쿼리 세트
$TestQueries = @(
    "Explain AI concepts briefly",
    "What is machine learning?",
    "How does neural network work?",
    "Difference between AI and ML",
    "What is deep learning?",
    "Explain natural language processing",
    "What is computer vision?",
    "How does reinforcement learning work?",
    "What is transfer learning?",
    "Explain transformer architecture"
)

Write-Host "📊 테스트 설정" -ForegroundColor Yellow
Write-Host "  - 서비스: $ServiceUrl" -ForegroundColor Gray
Write-Host "  - 샘플: $Samples개" -ForegroundColor Gray
Write-Host "  - 쿼리 종류: $($TestQueries.Count)개" -ForegroundColor Gray
Write-Host ""

# 1차: 캐시 워밍업 (각 쿼리 1회)
Write-Host "🔥 1단계: 캐시 워밍업..." -ForegroundColor Yellow

foreach ($query in $TestQueries) {
    try {
        $body = @{
            user_id = "cache-test-user"
            query   = $query
            options = @{
                style = "concise"
                depth = "overview"
            }
        } | ConvertTo-Json -Compress

        $response = Invoke-RestMethod `
            -Uri "$ServiceUrl/api/v2/recommend/personalized" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 30 `
            -ErrorAction SilentlyContinue

        Write-Host "  [OK] $query" -ForegroundColor Gray
    }
    catch {
        Write-Host "  [X] $query : $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "⏱️  2초 대기 (캐시 안정화)..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# 2차: 실제 성능 측정
Write-Host ""
Write-Host "📈 2단계: 성능 측정 ($Samples 샘플)..." -ForegroundColor Yellow
Write-Host ""

$ProgressCount = 0

for ($i = 0; $i -lt $Samples; $i++) {
    # 쿼리 선택 (반복 패턴으로 캐시 히트 유도)
    $queryIndex = $i % $TestQueries.Count
    $query = $TestQueries[$queryIndex]

    try {
        $body = @{
            user_id = "cache-test-user"
            query   = $query
            options = @{
                style = "concise"
                depth = "overview"
            }
        } | ConvertTo-Json -Compress

        $startTime = Get-Date

        $response = Invoke-RestMethod `
            -Uri "$ServiceUrl/api/v2/recommend/personalized" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 30 `
            -ErrorAction Stop

        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalMilliseconds

        # 응답 시간 저장
        $Results.ResponseTimes += $duration

        # 캐시 히트 여부 판단 (응답 시간 기반)
        # 일반적으로 캐시된 응답은 100ms 이하
        if ($duration -lt 100) {
            $Results.CacheHits++
            $Results.CachedResponseTimes += $duration
            $indicator = "V"
            $color = "Green"
        }
        else {
            $Results.CacheMisses++
            $Results.UncachedResponseTimes += $duration
            $indicator = "O"
            $color = "Yellow"
        }

        # 진행 상황 표시 (10개마다)
        $ProgressCount++
        if ($ProgressCount % 10 -eq 0) {
            $hitRate = [math]::Round(($Results.CacheHits / $ProgressCount) * 100, 1)
            Write-Host "  [$ProgressCount/$Samples] 캐시 히트율: $hitRate% | 평균: $([math]::Round($duration, 1))ms" -ForegroundColor $color
        }
    }
    catch {
        Write-Host "  [X] 요청 실패: $($_.Exception.Message)" -ForegroundColor Red
        $Results.CacheMisses++
    }

    # 부하 방지 (50ms 대기)
    Start-Sleep -Milliseconds 50
}

# 통계 계산
$TotalRequests = $Results.CacheHits + $Results.CacheMisses
$HitRate = if ($TotalRequests -gt 0) { 
    [math]::Round(($Results.CacheHits / $TotalRequests) * 100, 2)
}
else { 0 }

$AvgResponseTime = if ($Results.ResponseTimes.Count -gt 0) {
    [math]::Round(($Results.ResponseTimes | Measure-Object -Average).Average, 2)
}
else { 0 }

$AvgCachedTime = if ($Results.CachedResponseTimes.Count -gt 0) {
    [math]::Round(($Results.CachedResponseTimes | Measure-Object -Average).Average, 2)
}
else { 0 }

$AvgUncachedTime = if ($Results.UncachedResponseTimes.Count -gt 0) {
    [math]::Round(($Results.UncachedResponseTimes | Measure-Object -Average).Average, 2)
}
else { 0 }

# 결과 저장
$Results.HitRate = $HitRate
$Results.AvgResponseTime = $AvgResponseTime
$Results.AvgCachedResponseTime = $AvgCachedTime
$Results.AvgUncachedResponseTime = $AvgUncachedTime

# 결과 출력
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 분석 결과" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎯 캐시 효율성" -ForegroundColor Yellow
Write-Host "  - 총 요청: $TotalRequests" -ForegroundColor Gray
Write-Host "  - 캐시 히트: $($Results.CacheHits) ($(if($HitRate -ge 80){"Green"}elseif($HitRate -ge 50){"Yellow"}else{"Red"}))" -ForegroundColor $(if ($HitRate -ge 80) { "Green" }elseif ($HitRate -ge 50) { "Yellow" }else { "Red" })
Write-Host "  - 캐시 미스: $($Results.CacheMisses)" -ForegroundColor Gray
Write-Host "  - 히트율: $HitRate%" -ForegroundColor $(if ($HitRate -ge 80) { "Green" }elseif ($HitRate -ge 50) { "Yellow" }else { "Red" })
Write-Host ""

Write-Host "⚡ 성능 지표" -ForegroundColor Yellow
Write-Host "  - 전체 평균: ${AvgResponseTime}ms" -ForegroundColor Gray
Write-Host "  - 캐시 히트 시: ${AvgCachedTime}ms" -ForegroundColor Green
Write-Host "  - 캐시 미스 시: ${AvgUncachedTime}ms" -ForegroundColor Yellow

if ($AvgCachedTime -gt 0 -and $AvgUncachedTime -gt 0) {
    $speedup = [math]::Round($AvgUncachedTime / $AvgCachedTime, 2)
    Write-Host "  - 속도 향상: ${speedup}x" -ForegroundColor Cyan
}

Write-Host ""

# 권장사항
Write-Host "[!] 권장사항" -ForegroundColor Yellow

if ($HitRate -lt 50) {
    Write-Host "  [WARN] 캐시 히트율이 낮습니다 (<50%)" -ForegroundColor Red
    Write-Host "     - TTL 설정을 늘려보세요 (현재: 1시간 -> 추천: 2시간)" -ForegroundColor Gray
    Write-Host "     - 캐시 워밍업 전략을 검토하세요" -ForegroundColor Gray
}
elseif ($HitRate -lt 80) {
    Write-Host "  [WARN] 캐시 히트율 개선 가능 (50-80%)" -ForegroundColor Yellow
    Write-Host "     - 자주 사용되는 쿼리를 사전 캐싱하세요" -ForegroundColor Gray
}
else {
    Write-Host "  ✅ 캐시 히트율이 우수합니다 (≥80%)" -ForegroundColor Green
}

if ($AvgCachedTime -gt 100) {
    Write-Host "  [WARN] 캐시된 응답도 느립니다 (>100ms)" -ForegroundColor Yellow
    Write-Host "     - Redis 연결 지연을 확인하세요" -ForegroundColor Gray
    Write-Host "     - 네트워크 레이턴시를 점검하세요" -ForegroundColor Gray
}

if ($AvgUncachedTime -gt 500) {
    Write-Host "  [WARN] 캐시 미스 시 응답이 느립니다 (>500ms)" -ForegroundColor Yellow
    Write-Host "     - LLM 프롬프트 최적화를 고려하세요" -ForegroundColor Gray
    Write-Host "     - 모델 응답 시간을 프로파일링하세요" -ForegroundColor Gray
}

Write-Host ""

# JSON 출력
if ($OutputJson) {
    $Results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputJson -Encoding UTF8
    Write-Host "📄 결과 저장: $OutputJson" -ForegroundColor Green
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
