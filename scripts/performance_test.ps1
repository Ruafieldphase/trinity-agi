# AI 시스템 성능 테스트 및 벤치마크
# 목적: 최적화 전후 성능 비교, 베이스라인 설정

param(
    [string]$TestMode = "full",  # quick, full, continuous
    [int]$Duration = 300         # 테스트 지속시간 (초)
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



# 색상 정의
$colors = @{
    Success = [System.ConsoleColor]::Green
    Warning = [System.ConsoleColor]::Yellow
    Error = [System.ConsoleColor]::Red
    Info = [System.ConsoleColor]::Cyan
}

function Write-Log {
    param([string]$Message, [string]$Level = "Info")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $colors[$Level]
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Get-SystemMetrics {
    $metrics = @{
        Timestamp = Get-Date
        CPUUsage = 0
        MemoryUsage = 0
        DiskUsage = 0
        ActiveProcesses = 0
    }

    # CPU 사용률
    try {
        $cpuCounter = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue
        $metrics.CPUUsage = [math]::Round($cpuCounter.CounterSamples[0].CookedValue, 2)
    }
    catch {
        $metrics.CPUUsage = 0
    }

    # 메모리 사용률
    try {
        $osInfo = Get-WmiObject Win32_OperatingSystem
        $totalMem = $osInfo.TotalVisibleMemorySize
        $freeMem = $osInfo.FreePhysicalMemory
        $metrics.MemoryUsage = [math]::Round(((($totalMem - $freeMem) / $totalMem) * 100), 2)
    }
    catch {
        $metrics.MemoryUsage = 0
    }

    # 디스크 사용률 (C: 드라이브)
    try {
        $disk = Get-Volume -DriveLetter C -ErrorAction SilentlyContinue
        if ($disk) {
            $metrics.DiskUsage = [math]::Round((($disk.SizeUsed / $disk.Size) * 100), 2)
        }
    }
    catch {
        $metrics.DiskUsage = 0
    }

    # 활성 프로세스 수
    $metrics.ActiveProcesses = (Get-Process | Measure-Object).Count

    return $metrics
}

function Test-LMStudioPerformance {
    Write-Log "LM Studio 성능 테스트 시작..." "Info"

    $results = @()
    $testCount = 0
    $successCount = 0
    $failCount = 0
    $avgResponseTime = 0

    # 간단한 테스트 요청
    $testPrompts = @(
        "안녕하세요. 간단히 인사해주세요.",
        "2+2=?",
        "오늘 날씨는 어떤가요?",
        "한국의 수도는?",
        "간단한 퀴즈를 하나 주세요."
    )

    foreach ($prompt in $testPrompts) {
        $testCount++
        $startTime = Get-Date

        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/chat/completions" `
                                         -Method POST `
                                         -ContentType "application/json" `
                                         -Body (@{
                                             model = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
                                             messages = @(@{
                                                 role = "user"
                                                 content = $prompt
                                             })
                                             temperature = 0.3
                                             max_tokens = 100
                                         } | ConvertTo-Json) `
                                         -TimeoutSec 30 `
                                         -ErrorAction Stop

            $duration = ((Get-Date) - $startTime).TotalMilliseconds
            $successCount++
            $avgResponseTime += $duration

            Write-Log "✓ 테스트 $testCount 완료: ${duration}ms" "Success"

            $result = @{
                TestNumber = $testCount
                Status = "Success"
                ResponseTime = [math]::Round($duration, 2)
                Prompt = $prompt
            }
        }
        catch {
            $duration = ((Get-Date) - $startTime).TotalMilliseconds
            $failCount++

            Write-Log "✗ 테스트 $testCount 실패: $_" "Error"

            $result = @{
                TestNumber = $testCount
                Status = "Failed"
                ResponseTime = [math]::Round($duration, 2)
                Prompt = $prompt
                Error = $_
            }
        }

        $results += $result
        Start-Sleep -Seconds 1
    }

    # 평균 계산
    if ($successCount -gt 0) {
        $avgResponseTime = [math]::Round($avgResponseTime / $successCount, 2)
    }

    # 결과 요약
    Write-Log "LM Studio 성능 테스트 결과:" "Info"
    Write-Log "  - 총 테스트: $testCount" "Info"
    Write-Log "  - 성공: $successCount" "Success"
    Write-Log "  - 실패: $failCount" $(if ($failCount -gt 0) { "Error" } else { "Success" })
    Write-Log "  - 평균 응답시간: ${avgResponseTime}ms" "Info"
    Write-Log "  - 성공률: $([math]::Round(($successCount/$testCount)*100, 2))%" "Info"

    return @{
        TotalTests = $testCount
        SuccessCount = $successCount
        FailCount = $failCount
        AvgResponseTime = $avgResponseTime
        Details = $results
    }
}

function Test-APIPerformance {
    Write-Log "Agent API 성능 테스트 시작..." "Info"

    $testCount = 5
    $results = @()
    $avgResponseTime = 0
    $successCount = 0

    for ($i = 0; $i -lt $testCount; $i++) {
        $startTime = Get-Date

        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" `
                                         -TimeoutSec 10 `
                                         -ErrorAction Stop

            $duration = ((Get-Date) - $startTime).TotalMilliseconds
            $successCount++
            $avgResponseTime += $duration

            Write-Log "✓ API 테스트 $($i+1) 완료: ${duration}ms" "Success"
        }
        catch {
            $duration = ((Get-Date) - $startTime).TotalMilliseconds
            Write-Log "✗ API 테스트 $($i+1) 실패: $_" "Error"
        }

        Start-Sleep -Seconds 1
    }

    if ($successCount -gt 0) {
        $avgResponseTime = [math]::Round($avgResponseTime / $successCount, 2)
    }

    Write-Log "Agent API 성능 테스트 결과:" "Info"
    Write-Log "  - 성공: $successCount / $testCount" "Info"
    Write-Log "  - 평균 응답시간: ${avgResponseTime}ms" "Info"

    return @{
        AvgResponseTime = $avgResponseTime
        SuccessCount = $successCount
        TotalTests = $testCount
    }
}

function Test-SystemMetrics {
    Write-Log "시스템 메트릭 수집 중..." "Info"

    $startTime = Get-Date
    $metrics = @()
    $interval = 5  # 5초 간격

    while (((Get-Date) - $startTime).TotalSeconds -lt $Duration) {
        $metric = Get-SystemMetrics
        $metrics += $metric

        Write-Log "CPU: $($metric.CPUUsage)% | 메모리: $($metric.MemoryUsage)% | 디스크: $($metric.DiskUsage)% | 프로세스: $($metric.ActiveProcesses)" "Info"

        Start-Sleep -Seconds $interval
    }

    # 통계 계산
    $avgCPU = [math]::Round(($metrics.CPUUsage | Measure-Object -Average).Average, 2)
    $maxCPU = ($metrics.CPUUsage | Measure-Object -Maximum).Maximum
    $avgMem = [math]::Round(($metrics.MemoryUsage | Measure-Object -Average).Average, 2)
    $maxMem = ($metrics.MemoryUsage | Measure-Object -Maximum).Maximum

    Write-Log "시스템 메트릭 통계:" "Info"
    Write-Log "  - CPU 평균: ${avgCPU}% / 최대: $maxCPU%" "Info"
    Write-Log "  - 메모리 평균: ${avgMem}% / 최대: $maxMem%" "Info"
    Write-Log "  - 수집 기간: $Duration초" "Info"

    return @{
        AvgCPU = $avgCPU
        MaxCPU = $maxCPU
        AvgMemory = $avgMem
        MaxMemory = $maxMem
        DataPoints = $metrics.Count
    }
}

# 메인 실행
Write-Log "================== 성능 테스트 시작 ==================" "Info"
Write-Log "모드: $TestMode, 지속시간: ${Duration}초" "Info"

$testResults = @{}
$testStartTime = Get-Date

switch ($TestMode.ToLower()) {
    "quick" {
        # LM Studio 빠른 테스트
        $testResults["LMStudio"] = Test-LMStudioPerformance

        # API 테스트
        $testResults["API"] = Test-APIPerformance
    }

    "full" {
        # 모든 테스트 수행
        $testResults["LMStudio"] = Test-LMStudioPerformance
        $testResults["API"] = Test-APIPerformance
        $testResults["SystemMetrics"] = Test-SystemMetrics
    }

    "continuous" {
        # 지속적 모니터링
        $testResults["SystemMetrics"] = Test-SystemMetrics
    }

    default {
        Write-Log "알 수 없는 테스트 모드: $TestMode" "Error"
        exit 1
    }
}

# 결과 저장
$totalTime = ((Get-Date) - $testStartTime).TotalSeconds
$reportPath = "$WorkspaceRoot\outputs\performance_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

$report = @{
    Timestamp = Get-Date
    Mode = $TestMode
    Duration = $totalTime
    Results = $testResults
} | ConvertTo-Json -Depth 10

$report | Out-File -FilePath $reportPath -Encoding UTF8

Write-Log "==================  테스트 완료  ==================" "Info"
Write-Log "결과 저장: $reportPath" "Success"
Write-Log "총 소요시간: $([math]::Round($totalTime, 2))초" "Info"
Write-Log "=====================================================" "Info"