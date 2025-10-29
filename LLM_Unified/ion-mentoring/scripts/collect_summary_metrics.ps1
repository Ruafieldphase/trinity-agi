# 요약 경로 메트릭 수집 스크립트
# 목적: summary_light 사용률, cache hit rate, running summary 통계 수집

param(
    [int]$Hours = 24,
    [string]$LogsDir,
    [switch]$JsonOutput
)

$ErrorActionPreference = 'Continue'

if (-not $LogsDir) {
    $LogsDir = Join-Path $PSScriptRoot '..\logs'
}

if (-not (Test-Path $LogsDir)) {
    Write-Host "[summary_metrics] Logs directory not found: $LogsDir" -ForegroundColor Red
    exit 1
}

$cutoffTime = (Get-Date).AddHours(-$Hours)

Write-Host "[summary_metrics] Collecting summary metrics for last $Hours hours..." -ForegroundColor Cyan

# 메트릭 초기화
$metrics = @{
    period_hours             = $Hours
    cutoff_time              = $cutoffTime.ToString('yyyy-MM-dd HH:mm:ss')
    summary_light_calls      = 0
    total_calls              = 0
    cache_hits               = 0
    cache_misses             = 0
    running_summary_updates  = 0
    running_summary_failures = 0
    avg_summary_length       = 0
    avg_bullets              = 0
    latencies_ms             = @()
}

# API 로그에서 메트릭 추출 (실제 구현 시 API 로그 형식에 맞게 조정)
# 현재는 샘플 구현 - 실제로는 구조화된 로그나 메트릭 저장소에서 가져와야 함

$apiLogs = Get-ChildItem $LogsDir -Filter "api_*.log" -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -ge $cutoffTime }

$summaryLengths = @()
$bulletCounts = @()

foreach ($logFile in $apiLogs) {
    try {
        $content = Get-Content $logFile.FullName -ErrorAction SilentlyContinue
        
        # 요약 관련 로그 라인 파싱
        $content | ForEach-Object {
            $line = $_
            
            # prompt_mode=summary_light 감지
            if ($line -match 'prompt_mode.*summary_light') {
                $metrics.summary_light_calls++
            }
            
            # 전체 API 호출
            if ($line -match 'process\(|/api/v2/') {
                $metrics.total_calls++
            }
            
            # Cache hit/miss
            if ($line -match 'Cache hit') {
                $metrics.cache_hits++
            }
            if ($line -match 'Cache miss') {
                $metrics.cache_misses++
            }
            
            # Running summary 업데이트
            if ($line -match 'running_summary_len.*:.*(\d+)') {
                $metrics.running_summary_updates++
                $summaryLengths += [int]$Matches[1]
            }
            
            # Running summary bullets
            if ($line -match 'running_summary_bullets.*:.*(\d+)') {
                $bulletCounts += [int]$Matches[1]
            }
            
            # Running summary 실패
            if ($line -match 'running_summary_update.*failed') {
                $metrics.running_summary_failures++
            }
            
            # 지연 시간 (예: latency_ms: 123)
            if ($line -match 'latency_ms.*:.*(\d+(?:\.\d+)?)') {
                $metrics.latencies_ms += [double]$Matches[1]
            }
        }
    }
    catch {
        Write-Warning "Failed to parse $($logFile.Name): $($_.Exception.Message)"
    }
}

# 통계 계산
$metrics.avg_summary_length = if ($summaryLengths.Count -gt 0) {
    [math]::Round(($summaryLengths | Measure-Object -Average).Average, 1)
}
else { 0 }

$metrics.avg_bullets = if ($bulletCounts.Count -gt 0) {
    [math]::Round(($bulletCounts | Measure-Object -Average).Average, 1)
}
else { 0 }

$totalCacheOps = $metrics.cache_hits + $metrics.cache_misses
$cacheHitRate = if ($totalCacheOps -gt 0) {
    [math]::Round(($metrics.cache_hits / $totalCacheOps) * 100, 2)
}
else { 0 }

$summaryLightUsageRate = if ($metrics.total_calls -gt 0) {
    [math]::Round(($metrics.summary_light_calls / $metrics.total_calls) * 100, 2)
}
else { 0 }

# 지연 통계
$latencyStats = @{
    p50 = 0
    p95 = 0
    avg = 0
}

if ($metrics.latencies_ms.Count -gt 0) {
    $sorted = $metrics.latencies_ms | Sort-Object
    $latencyStats.p50 = [math]::Round($sorted[[int]($sorted.Count * 0.5)], 2)
    $latencyStats.p95 = [math]::Round($sorted[[int]($sorted.Count * 0.95)], 2)
    $latencyStats.avg = [math]::Round(($metrics.latencies_ms | Measure-Object -Average).Average, 2)
}

# 결과 구조화
$result = @{
    period_hours    = $metrics.period_hours
    cutoff_time     = $metrics.cutoff_time
    summary_light   = @{
        calls              = $metrics.summary_light_calls
        usage_rate_percent = $summaryLightUsageRate
    }
    cache           = @{
        hits             = $metrics.cache_hits
        misses           = $metrics.cache_misses
        hit_rate_percent = $cacheHitRate
    }
    running_summary = @{
        updates     = $metrics.running_summary_updates
        failures    = $metrics.running_summary_failures
        avg_length  = $metrics.avg_summary_length
        avg_bullets = $metrics.avg_bullets
    }
    latency         = $latencyStats
    total_api_calls = $metrics.total_calls
}

# JSON 출력
if ($JsonOutput) {
    $result | ConvertTo-Json -Depth 5
    exit 0
}

# 사람이 읽기 쉬운 형식
Write-Host "`nSUMMARY METRICS (Last $Hours hours)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray

Write-Host "`nSummary Light Mode:" -ForegroundColor Yellow
Write-Host "  Calls: $($result.summary_light.calls)" -ForegroundColor White
Write-Host "  Usage Rate: $($result.summary_light.usage_rate_percent)%" -ForegroundColor White

Write-Host "`nCache Performance:" -ForegroundColor Yellow
Write-Host "  Hits: $($result.cache.hits)" -ForegroundColor White
Write-Host "  Misses: $($result.cache.misses)" -ForegroundColor White
Write-Host "  Hit Rate: $($result.cache.hit_rate_percent)%" -ForegroundColor $(if ($cacheHitRate -ge 30) { 'Green' } elseif ($cacheHitRate -ge 10) { 'Yellow' } else { 'Red' })

Write-Host "`nRunning Summary:" -ForegroundColor Yellow
Write-Host "  Updates: $($result.running_summary.updates)" -ForegroundColor White
Write-Host "  Failures: $($result.running_summary.failures)" -ForegroundColor $(if ($result.running_summary.failures -eq 0) { 'Green' } else { 'Red' })
Write-Host "  Avg Length: $($result.running_summary.avg_length) chars" -ForegroundColor White
Write-Host "  Avg Bullets: $($result.running_summary.avg_bullets)" -ForegroundColor White

Write-Host "`nLatency Statistics:" -ForegroundColor Yellow
Write-Host "  P50: $($result.latency.p50)ms" -ForegroundColor White
Write-Host "  P95: $($result.latency.p95)ms" -ForegroundColor White
Write-Host "  Avg: $($result.latency.avg)ms" -ForegroundColor White

Write-Host "`nTotal API Calls: $($result.total_api_calls)" -ForegroundColor Gray
Write-Host "======================================`n" -ForegroundColor Gray

exit 0
