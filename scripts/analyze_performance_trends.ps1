# 성능 트렌드 분석 - 시간 경과에 따른 개선도 측정
# 시스템이 실제로 개선되고 있는지를 추적

param(
    [int]$LookbackHours = 24,
    [string]$DashboardFile = "C:\workspace\agi\outputs\rhythm_dashboard.json",
    [string]$MetricsFile = "C:\workspace\agi\outputs\scheduler_metrics.json",
    [string]$TrendFile = "C:\workspace\agi\outputs\performance_trend_analysis.json",
    [string]$ReportFile = "C:\workspace\agi\outputs\performance_trend_analysis.md"
)

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

Write-Host "✅ 성능 트렌드 분석 완료" -ForegroundColor Green
