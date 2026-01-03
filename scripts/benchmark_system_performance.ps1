# benchmark_system_performance.ps1
# 시스템 성능 벤치마크 - VS Code CLI와 비교

<#
.SYNOPSIS
    현재 시스템과 VS Code CLI의 성능을 벤치마크합니다.

.DESCRIPTION
    - 단순 코드 생성
    - 파일 수정
    - 복잡한 리팩토링
    각 시나리오에서 레이턴시를 측정하고 비교합니다.

.PARAMETER Scenarios
    테스트할 시나리오 (기본: all)

.PARAMETER Iterations
    각 시나리오 반복 횟수 (기본: 5)

.PARAMETER OutJson
    결과를 저장할 JSON 파일 경로

.EXAMPLE
    .\benchmark_system_performance.ps1
    .\benchmark_system_performance.ps1 -Scenarios "simple,modify" -Iterations 10
#>

param(
    [string]$Scenarios = "all",
    [int]$Iterations = 5,
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\benchmark_results_latest.json",
    [switch]$OpenMd
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$ws = Split-Path -Parent $PSScriptRoot

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🏁 시스템 성능 벤치마크                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 시나리오 정의
$scenarioDefs = @{
    simple   = @{
        name   = "단순 코드 생성"
        prompt = "Python으로 Hello World를 출력하는 함수를 작성해주세요."
        type   = "generation"
    }
    modify   = @{
        name    = "파일 수정"
        prompt  = "이 함수에 try-except 에러 핸들링을 추가해주세요."
        type    = "modification"
        context = "def hello():\n    print('Hello World')"
    }
    refactor = @{
        name    = "복잡한 리팩토링"
        prompt  = "이 모듈을 3개의 작은 모듈로 분리하고 각 모듈의 책임을 명확히 해주세요."
        type    = "refactoring"
        context = "# 100줄 정도의 복잡한 코드"
    }
}

# 시나리오 선택
$selectedScenarios = @()
if ($Scenarios -eq "all") {
    $selectedScenarios = $scenarioDefs.Keys
}
else {
    $selectedScenarios = $Scenarios -split ","
}

Write-Host "📋 선택된 시나리오: $($selectedScenarios -join ', ')" -ForegroundColor Yellow
Write-Host "🔄 반복 횟수: $Iterations" -ForegroundColor Yellow
Write-Host ""

# 결과 저장
$results = @{
    timestamp = (Get-Date).ToString("o")
    scenarios = @{}
    summary   = @{}
}

# 각 시나리오 실행
foreach ($scenarioKey in $selectedScenarios) {
    if (-not $scenarioDefs.ContainsKey($scenarioKey)) {
        Write-Host "⚠️  Unknown scenario: $scenarioKey" -ForegroundColor Yellow
        continue
    }

    $scenario = $scenarioDefs[$scenarioKey]
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "🎯 시나리오: $($scenario.name)" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    $scenarioResults = @{
        name       = $scenario.name
        type       = $scenario.type
        iterations = @()
        stats      = @{}
    }

    # 반복 실행
    for ($i = 1; $i -le $Iterations; $i++) {
        Write-Host "`n  🔄 Iteration $i/$Iterations" -ForegroundColor Gray

        # 현재 시스템 테스트
        $startTime = Get-Date
        try {
            $body = @{
                task_type = 'benchmark_test'
                priority  = 'high'
                params    = @{
                    prompt    = $scenario.prompt
                    context   = $scenario.context
                    fast_mode = $false
                }
            } | ConvertTo-Json -Depth 10

            $taskResponse = Invoke-RestMethod -Uri 'http://localhost:8091/api/enqueue' `
                -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 5

            $taskId = $taskResponse.task_id
            
            # 완료 대기
            $maxWait = 30
            $waited = 0
            $completed = $false
            while ($waited -lt $maxWait) {
                Start-Sleep -Milliseconds 500
                $waited += 0.5
                
                $resultResponse = Invoke-RestMethod -Uri "http://localhost:8091/api/results?limit=10" -TimeoutSec 3
                $result = $resultResponse | Where-Object { $_.task_id -eq $taskId }
                
                if ($result) {
                    $completed = $true
                    break
                }
            }

            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds

            if ($completed) {
                Write-Host "    ✅ 완료: $($duration.ToString('F2'))초" -ForegroundColor Green
                
                $scenarioResults.iterations += @{
                    iteration        = $i
                    success          = $true
                    duration_seconds = [math]::Round($duration, 3)
                    ttfb             = $null  # 현재 측정 불가 (스트리밍 없음)
                    timestamp        = (Get-Date).ToString("o")
                }
            }
            else {
                Write-Host "    ⏱️  타임아웃: $maxWait초 초과" -ForegroundColor Yellow
                
                $scenarioResults.iterations += @{
                    iteration        = $i
                    success          = $false
                    duration_seconds = $maxWait
                    error            = "timeout"
                    timestamp        = (Get-Date).ToString("o")
                }
            }

        }
        catch {
            Write-Host "    ❌ 에러: $($_.Exception.Message)" -ForegroundColor Red
            
            $scenarioResults.iterations += @{
                iteration        = $i
                success          = $false
                duration_seconds = $null
                error            = $_.Exception.Message
                timestamp        = (Get-Date).ToString("o")
            }
        }

        # 서버 부하 방지
        Start-Sleep -Milliseconds 1000
    }

    # 통계 계산
    $successfulRuns = $scenarioResults.iterations | Where-Object { $_.success -eq $true }
    if ($successfulRuns.Count -gt 0) {
        $durations = $successfulRuns | ForEach-Object { $_.duration_seconds }
        $scenarioResults.stats = @{
            success_count   = $successfulRuns.Count
            failure_count   = $Iterations - $successfulRuns.Count
            avg_duration    = [math]::Round(($durations | Measure-Object -Average).Average, 3)
            min_duration    = [math]::Round(($durations | Measure-Object -Minimum).Minimum, 3)
            max_duration    = [math]::Round(($durations | Measure-Object -Maximum).Maximum, 3)
            median_duration = [math]::Round(($durations | Sort-Object)[[math]::Floor($durations.Count / 2)], 3)
        }

        Write-Host "`n  📊 통계:" -ForegroundColor Cyan
        Write-Host "     평균: $($scenarioResults.stats.avg_duration)초" -ForegroundColor White
        Write-Host "     최소: $($scenarioResults.stats.min_duration)초" -ForegroundColor White
        Write-Host "     최대: $($scenarioResults.stats.max_duration)초" -ForegroundColor White
        Write-Host "     중앙값: $($scenarioResults.stats.median_duration)초" -ForegroundColor White
        Write-Host "     성공률: $($successfulRuns.Count)/$Iterations" -ForegroundColor White
    }
    else {
        Write-Host "`n  ❌ 성공한 실행 없음" -ForegroundColor Red
        $scenarioResults.stats = @{
            success_count = 0
            failure_count = $Iterations
        }
    }

    $results.scenarios[$scenarioKey] = $scenarioResults
}

# 전체 요약
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 전체 요약" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$allDurations = @()
$totalSuccess = 0
$totalFailure = 0

foreach ($scenarioKey in $results.scenarios.Keys) {
    $scenario = $results.scenarios[$scenarioKey]
    Write-Host "`n$($scenario.name):" -ForegroundColor Cyan
    
    if ($scenario.stats.success_count -gt 0) {
        Write-Host "  평균: $($scenario.stats.avg_duration)초" -ForegroundColor White
        Write-Host "  성공률: $($scenario.stats.success_count)/$($scenario.stats.success_count + $scenario.stats.failure_count)" -ForegroundColor White
        
        $allDurations += $scenario.iterations | Where-Object { $_.success } | ForEach-Object { $_.duration_seconds }
        $totalSuccess += $scenario.stats.success_count
    }
    else {
        Write-Host "  성공한 실행 없음" -ForegroundColor Red
    }
    
    $totalFailure += $scenario.stats.failure_count
}

if ($allDurations.Count -gt 0) {
    $results.summary = @{
        total_runs      = $totalSuccess + $totalFailure
        successful_runs = $totalSuccess
        failed_runs     = $totalFailure
        overall_avg     = [math]::Round(($allDurations | Measure-Object -Average).Average, 3)
        overall_min     = [math]::Round(($allDurations | Measure-Object -Minimum).Minimum, 3)
        overall_max     = [math]::Round(($allDurations | Measure-Object -Maximum).Maximum, 3)
    }

    Write-Host "`n전체 평균: $($results.summary.overall_avg)초" -ForegroundColor Green
    Write-Host "전체 성공률: $totalSuccess/$($totalSuccess + $totalFailure)" -ForegroundColor Green
}

# JSON 저장
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutJson -Encoding UTF8
Write-Host "`n✅ 결과 저장: $OutJson" -ForegroundColor Green

# 마크다운 리포트 생성
$mdPath = $OutJson -replace '\.json$', '.md'
$mdContent = @"
# 성능 벤치마크 결과

**실행 시간**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**반복 횟수**: $Iterations

---

## 📊 전체 요약

"@

if ($results.summary.Keys.Count -gt 0) {
    $mdContent += @"
- **전체 실행**: $($results.summary.total_runs)회
- **성공**: $($results.summary.successful_runs)회
- **실패**: $($results.summary.failed_runs)회
- **전체 평균**: $($results.summary.overall_avg)초
- **최소**: $($results.summary.overall_min)초
- **최대**: $($results.summary.overall_max)초

---

"@
}

foreach ($scenarioKey in $results.scenarios.Keys) {
    $scenario = $results.scenarios[$scenarioKey]
    $mdContent += @"
## 🎯 $($scenario.name)

**타입**: $($scenario.type)

"@

    if ($scenario.stats.success_count -gt 0) {
        $mdContent += @"
### 통계

- **평균**: $($scenario.stats.avg_duration)초
- **최소**: $($scenario.stats.min_duration)초
- **최대**: $($scenario.stats.max_duration)초
- **중앙값**: $($scenario.stats.median_duration)초
- **성공률**: $($scenario.stats.success_count)/$($scenario.stats.success_count + $scenario.stats.failure_count)

### 개별 실행

| Iteration | 성공 | 소요 시간 |
|-----------|------|-----------|
"@
        foreach ($iter in $scenario.iterations) {
            $status = if ($iter.success) { "✅" } else { "❌" }
            $duration = if ($iter.duration_seconds) { "$($iter.duration_seconds)초" } else { "N/A" }
            $mdContent += "`n| $($iter.iteration) | $status | $duration |"
        }
    }
    else {
        $mdContent += @"
### ❌ 성공한 실행 없음

"@
    }

    $mdContent += "`n`n---`n`n"
}

$mdContent += @"
## 📌 VS Code CLI와 비교

**참고**: VS Code Claude CLI/GPT Codex는 일반적으로:
- 단순 작업: 0.5-2초
- 중간 복잡도: 2-5초
- 복잡한 작업: 5-10초

**현재 시스템 목표**:
- Phase 1 (Quick Wins): 4초 이하
- Phase 2 (구조 개선): 2.8초 이하
- Phase 3 (아키텍처 재설계): VS Code CLI와 동등 (1-2초)

---

**다음 액션**: `docs\PERFORMANCE_ANALYSIS_vs_VSCODE_CLI.md` 참고
"@

$mdContent | Out-File -FilePath $mdPath -Encoding UTF8
Write-Host "✅ 마크다운 리포트: $mdPath" -ForegroundColor Green

if ($OpenMd) {
    Start-Process code $mdPath
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎊 벤치마크 완료!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan