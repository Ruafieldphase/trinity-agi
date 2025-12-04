# Rapid Reindex Test Suite
# 재색인 후 5개 간단한 task를 빠르게 실행하여 즉시 효과 측정

param(
    [int]$TaskCount = 5,
    [string]$WorkspaceRoot = "C:\workspace\agi"
)

$ErrorActionPreference = 'Continue'  # Allow warnings but continue
$repoDir = "$WorkspaceRoot\fdo_agi_repo"
Set-Location $repoDir

Write-Host "`n=== Rapid Reindex Test Suite ===" -ForegroundColor Cyan
Write-Host "Running $TaskCount quick tasks to measure immediate improvement...`n"

$testTasks = @(
    "2+2는?",
    "Python에서 list comprehension 예제 하나만",
    "AGI의 정의를 한 문장으로",
    "Fibonacci 수열의 5번째 숫자는?",
    "Hello World를 3가지 언어로"
)

$startTime = Get-Date
$results = @()

for ($i = 0; $i -lt [math]::Min($TaskCount, $testTasks.Count); $i++) {
    $goal = $testTasks[$i]
    $taskNum = $i + 1
    
    Write-Host "[$taskNum/$TaskCount] Running: $goal" -ForegroundColor Yellow
    
    $taskStart = Get-Date
    
    try {
        if (Test-Path "$repoDir\.venv\Scripts\python.exe") {
            $pythonExe = "$repoDir\.venv\Scripts\python.exe"
        }
        else {
            $pythonExe = "python"
        }
        
        $result = & $pythonExe -m scripts.run_task --title "reindex_test_$taskNum" --goal $goal 2>&1
        $success = $LASTEXITCODE -eq 0
    }
    catch {
        $success = $false
    }
    
    $taskEnd = Get-Date
    $duration = ($taskEnd - $taskStart).TotalSeconds
    $results += [PSCustomObject]@{
        TaskNum  = $taskNum
        Goal     = $goal
        Success  = $success
        Duration = [math]::Round($duration, 2)
    }
    
    if ($success) {
        Write-Host "  ✅ Completed in $([math]::Round($duration, 1))s" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed" -ForegroundColor Red
    }
    Write-Host ""
}

$totalTime = ((Get-Date) - $startTime).TotalSeconds

Write-Host "`n=== Test Results ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$successCount = ($results | Where-Object { $_.Success }).Count
$successRate = [math]::Round(($successCount / $TaskCount) * 100, 1)
$avgDuration = [math]::Round(($results | Measure-Object -Property Duration -Average).Average, 2)

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Success rate: $successRate% ($successCount/$TaskCount)"
Write-Host "  Avg duration: $avgDuration seconds"
Write-Host "  Total time: $([math]::Round($totalTime, 1))s`n"

Write-Host "Now checking ReplanRate for these tasks..." -ForegroundColor Cyan
& "$WorkspaceRoot\scripts\quick_replan_check.ps1" -LastTasks $TaskCount

exit 0
