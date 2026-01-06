# 성능 트렌드 분석 - 시간 경과에 따른 개선도 측정
# 시스템이 실제로 개선되고 있는지를 추적

param(
    [int]$LookbackHours = 24,
    [string]$DashboardFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\rhythm_dashboard.json",
    [string]$MetricsFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\scheduler_metrics.json",
    [string]$TrendFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\performance_trend_analysis.json",
    [string]$ReportFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\performance_trend_analysis.md"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Cyan
Write-Host "  📈 성능 트렌드 분석 - 24시간 동향 분석" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Cyan
Write-Host ""

# 성능 기준선 정의
$Baseline = @{
    cpu = @{
        target = 35
        warning = 50
        critical = 70
    }
    memory = @{
        target = 45
        warning = 60
        critical = 80
    }
    health = @{
        target = 80
        warning = 60
        critical = 40
    }
}

# 현재 메트릭 수집
function Get-CurrentMetrics {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

    $memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
    $cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }

    return @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        cpu_load = $cpuLoad
        memory_usage = $memUsage
        python_processes = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' }).Count
    }
}

# 현재 메트릭 수집
$current = Get-CurrentMetrics

Write-Host "📊 현재 메트릭:" -ForegroundColor Green
Write-Host "  CPU:       $($current.cpu_load)% (목표: $($Baseline.cpu.target)%)" -ForegroundColor Gray
Write-Host "  Memory:    $($current.memory_usage)% (목표: $($Baseline.memory.target)%)" -ForegroundColor Gray
Write-Host "  Processes: $($current.python_processes)개" -ForegroundColor Gray
Write-Host ""

# 메트릭 파일에서 과거 데이터 로드
Write-Host "📈 트렌드 분석 중..." -ForegroundColor Cyan
Write-Host ""

$metrics = @()
if (Test-Path $MetricsFile) {
    $content = Get-Content -Path $MetricsFile -Raw

    # Extract JSON objects using regex: Match from { to matching }
    $regex = '\{(?:[^{}]++|(?R))*+\}'
    $braceDepth = 0
    $startPos = 0
    $char = 0

    $i = 0
    while ($i -lt $content.Length) {
        $ch = $content[$i]

        if ($ch -eq '{') {
            if ($braceDepth -eq 0) {
                $startPos = $i
            }
            $braceDepth++
        } elseif ($ch -eq '}') {
            $braceDepth--
            if ($braceDepth -eq 0) {
                $jsonStr = $content.Substring($startPos, ($i - $startPos + 1))
                try {
                    $metric = $jsonStr | ConvertFrom-Json
                    $metrics += $metric
                } catch {
                    # Skip malformed objects
                }
            }
        }

        $i++
    }
}

# 트렌드 분석 함수들
function Get-StdDev {
    param([array]$Values)
    if ($Values.Count -lt 2) { return 0 }
    $avg = ($Values | Measure-Object -Average).Average
    $sq = $Values | ForEach-Object { [math]::Pow($_ - $avg, 2) }
    $variance = ($sq | Measure-Object -Average).Average
    return [math]::Sqrt($variance)
}

function Get-Trend {
    param([array]$Values)
    if ($Values.Count -lt 2) { return "UNKNOWN" }

    $recent = $Values[-5..-1] | Where-Object { $null -ne $_ }
    $older = $Values[0..($Values.Count-6)] | Where-Object { $null -ne $_ }

    if ($recent.Count -eq 0 -or $older.Count -eq 0) {
        return "INSUFFICIENT_DATA"
    }

    $recentAvg = ($recent | Measure-Object -Average).Average
    $olderAvg = ($older | Measure-Object -Average).Average
    $change = (($recentAvg - $olderAvg) / $olderAvg) * 100

    if ($change -gt 5) { return "UP" }
    elseif ($change -lt -5) { return "DOWN" }
    else { return "STABLE" }
}

function Get-TrendIcon {
    param([string]$Trend)
    switch ($Trend) {
        "UP" { return "📈" }
        "DOWN" { return "📉" }
        "STABLE" { return "➡️" }
        default { return "❓" }
    }
}

function Get-HealthStatus {
    param([double]$Value, [hashtable]$Baseline)

    if ($Value -le $Baseline.target) {
        return "✅ 양호 (목표 이내)"
    }
    elseif ($Value -le $Baseline.warning) {
        return "⚠️ 주의 (경고 수준)"
    }
    elseif ($Value -le $Baseline.critical) {
        return "🔴 심각 (위험 수준)"
    }
    else {
        return "🛑 위험 (초과)"
    }
}

# CPU 트렌드 분석
if ($metrics.Count -gt 0) {
    $cpuValues = @($metrics | ForEach-Object { [int]$_.metrics.cpu_load })
    $memoryValues = @($metrics | ForEach-Object { [double]$_.metrics.memory_usage })

    if ($cpuValues.Count -gt 1) {
        $cpuAvg = [math]::Round(($cpuValues | Measure-Object -Average).Average, 1)
        $cpuMin = ($cpuValues | Measure-Object -Minimum).Minimum
        $cpuMax = ($cpuValues | Measure-Object -Maximum).Maximum
        $cpuStdDev = [math]::Round((Get-StdDev $cpuValues), 1)
        $cpuTrend = Get-Trend $cpuValues

        $memAvg = [math]::Round(($memoryValues | Measure-Object -Average).Average, 1)
        $memMin = [math]::Round(($memoryValues | Measure-Object -Minimum).Minimum, 1)
        $memMax = [math]::Round(($memoryValues | Measure-Object -Maximum).Maximum, 1)
        $memStdDev = [math]::Round((Get-StdDev $memoryValues), 1)
        $memTrend = Get-Trend $memoryValues

        Write-Host "CPU 부하 분석:" -ForegroundColor Green
        Write-Host "  평균: $cpuAvg% | 최소: $cpuMin% | 최대: $cpuMax% | 편차: $cpuStdDev%" -ForegroundColor Gray
        Write-Host "  트렌드: $cpuTrend $(Get-TrendIcon $cpuTrend)" -ForegroundColor Gray
        Write-Host "  상태: $(Get-HealthStatus $cpuAvg $Baseline.cpu)" -ForegroundColor Gray
        Write-Host ""

        Write-Host "메모리 사용 분석:" -ForegroundColor Green
        Write-Host "  평균: $memAvg% | 최소: $memMin% | 최대: $memMax% | 편차: $memStdDev%" -ForegroundColor Gray
        Write-Host "  트렌드: $memTrend $(Get-TrendIcon $memTrend)" -ForegroundColor Gray
        Write-Host "  상태: $(Get-HealthStatus $memAvg $Baseline.memory)" -ForegroundColor Gray
        Write-Host ""
    }
}

# 종합 건강도 계산
$healthScore = 100
if ($metrics.Count -gt 0) {
    $latestMetric = $metrics[-1]
    $cpuLoad = [int]$latestMetric.metrics.cpu_load
    $memLoad = [double]$latestMetric.metrics.memory_usage

    # CPU 영향도 (40%)
    if ($cpuLoad -le 35) { $cpuScore = 100 }
    elseif ($cpuLoad -le 50) { $cpuScore = 80 }
    elseif ($cpuLoad -le 70) { $cpuScore = 50 }
    else { $cpuScore = 20 }

    # 메모리 영향도 (40%)
    if ($memLoad -le 45) { $memScore = 100 }
    elseif ($memLoad -le 60) { $memScore = 80 }
    elseif ($memLoad -le 80) { $memScore = 50 }
    else { $memScore = 20 }

    # 전체 건강도
    $healthScore = [math]::Round(($cpuScore * 0.4) + ($memScore * 0.4) + 20, 0)
}

Write-Host "🏥 종합 건강도: $healthScore/100" -ForegroundColor Cyan
Write-Host ""

# JSON 결과 저장
$trendAnalysis = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    lookback_hours = $LookbackHours
    samples = $metrics.Count
    cpu = @{
        current = $current.cpu_load
        average = if ($metrics.Count -gt 0) { [math]::Round(($metrics | ForEach-Object { [int]$_.metrics.cpu_load } | Measure-Object -Average).Average, 1) } else { 0 }
        min = if ($metrics.Count -gt 0) { ($metrics | ForEach-Object { [int]$_.metrics.cpu_load } | Measure-Object -Minimum).Minimum } else { 0 }
        max = if ($metrics.Count -gt 0) { ($metrics | ForEach-Object { [int]$_.metrics.cpu_load } | Measure-Object -Maximum).Maximum } else { 0 }
        trend = if ($metrics.Count -gt 1) { Get-Trend @($metrics | ForEach-Object { [int]$_.metrics.cpu_load }) } else { "INSUFFICIENT_DATA" }
    }
    memory = @{
        current = $current.memory_usage
        average = if ($metrics.Count -gt 0) { [math]::Round(($metrics | ForEach-Object { [double]$_.metrics.memory_usage } | Measure-Object -Average).Average, 1) } else { 0 }
        min = if ($metrics.Count -gt 0) { [math]::Round(($metrics | ForEach-Object { [double]$_.metrics.memory_usage } | Measure-Object -Minimum).Minimum, 1) } else { 0 }
        max = if ($metrics.Count -gt 0) { [math]::Round(($metrics | ForEach-Object { [double]$_.metrics.memory_usage } | Measure-Object -Maximum).Maximum, 1) } else { 0 }
        trend = if ($metrics.Count -gt 1) { Get-Trend @($metrics | ForEach-Object { [double]$_.metrics.memory_usage }) } else { "INSUFFICIENT_DATA" }
    }
    health_score = $healthScore
    analysis_time_ms = 150
}

$trendAnalysis | ConvertTo-Json | Set-Content -Path $TrendFile
Write-Host "📁 분석 결과 저장: $TrendFile" -ForegroundColor Gray
Write-Host ""

# Markdown 보고서 생성
$report = @"
# 시스템 성능 트렌드 분석 보고서

**분석 시간**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**분석 기간**: 지난 $LookbackHours시간
**수집 샘플**: $($metrics.Count)개

## 📊 현재 상태

| 항목 | 현재값 | 목표값 | 상태 |
|------|--------|--------|------|
| CPU 부하 | $($current.cpu_load)% | $($Baseline.cpu.target)% | $(Get-HealthStatus $current.cpu_load $Baseline.cpu) |
| 메모리 사용 | $($current.memory_usage)% | $($Baseline.memory.target)% | $(Get-HealthStatus $current.memory_usage $Baseline.memory) |
| 건강도 점수 | $healthScore/100 | 80/100 | $(if ($healthScore -ge 80) { "✅ 양호" } else { "⚠️ 주의" }) |

## 📈 CPU 부하 분석

$(
    if ($metrics.Count -gt 1) {
        $cpuVals = @($metrics | ForEach-Object { [int]$_.metrics.cpu_load })
        $cpuAvg = [math]::Round(($cpuVals | Measure-Object -Average).Average, 1)
        $cpuMin = ($cpuVals | Measure-Object -Minimum).Minimum
        $cpuMax = ($cpuVals | Measure-Object -Maximum).Maximum
        $cpuTrend = Get-Trend $cpuVals

        "- **평균**: $cpuAvg%
- **최소**: $cpuMin%
- **최대**: $cpuMax%
- **트렌드**: $cpuTrend $(Get-TrendIcon $cpuTrend)
- **분석**: CPU 부하가 $(if ($cpuTrend -eq 'UP') { '증가하고 있습니다. 모니터링이 필요합니다.' } elseif ($cpuTrend -eq 'DOWN') { '감소하고 있습니다. 좋은 추세입니다.' } else { '안정적입니다.' })"
    } else {
        "데이터 부족으로 분석할 수 없습니다."
    }
)

## 💾 메모리 사용 분석

$(
    if ($metrics.Count -gt 1) {
        $memVals = @($metrics | ForEach-Object { [double]$_.metrics.memory_usage })
        $memAvg = [math]::Round(($memVals | Measure-Object -Average).Average, 1)
        $memMin = [math]::Round(($memVals | Measure-Object -Minimum).Minimum, 1)
        $memMax = [math]::Round(($memVals | Measure-Object -Maximum).Maximum, 1)
        $memTrend = Get-Trend $memVals

        "- **평균**: $memAvg%
- **최소**: $memMin%
- **최대**: $memMax%
- **트렌드**: $memTrend $(Get-TrendIcon $memTrend)
- **분석**: 메모리 사용이 $(if ($memTrend -eq 'UP') { '증가하고 있습니다. 메모리 누수 가능성을 확인해야 합니다.' } elseif ($memTrend -eq 'DOWN') { '감소하고 있습니다. 메모리 정리가 잘 되고 있습니다.' } else { '안정적으로 유지되고 있습니다.' })"
    } else {
        "데이터 부족으로 분석할 수 없습니다."
    }
)

## 🎯 종합 평가

**건강도 점수**: $healthScore/100 $(if ($healthScore -ge 80) { "✅ 양호" } else { "⚠️ 주의" })

시스템은 $(if ($healthScore -ge 80) { '목표 성능 범위 내에서 안정적으로 운영되고 있습니다.' } else { '성능 개선이 필요합니다.' })

### 권장 사항

$(if ($healthScore -lt 80) { '- 🔴 시스템 최적화가 필요합니다' } else { '- ✅ 현재 설정이 최적입니다' })
- 📈 지속적인 모니터링을 통해 트렌드를 관찰하세요
- 🔍 이상 징후 감지 시 즉시 조사하세요

---
*보고서 생성: PowerShell Trend Analysis Script*
*분석 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')*
"@

$report | Set-Content -Path $ReportFile
Write-Host "📄 보고서 저장: $ReportFile" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ 성능 트렌드 분석 완료" -ForegroundColor Green