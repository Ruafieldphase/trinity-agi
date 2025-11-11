<#
.SYNOPSIS
    Goal Executor Monitor 상태 확인 (빠른 체크)

.DESCRIPTION
    현재 Goal Executor Monitor Task가 정상 작동 중인지 빠르게 확인합니다.
    
.EXAMPLE
    .\CHECK_GOAL_MONITOR.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "   🔍 Goal Executor Monitor 상태 확인" -ForegroundColor White
Write-Host "================================================================`n" -ForegroundColor Cyan

$TaskName = "AGI_GoalExecutorMonitor"

# Task 존재 여부 확인
try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
    
    Write-Host "✅ Task 상태: 등록됨" -ForegroundColor Green
    Write-Host "   이름:        $($task.TaskName)" -ForegroundColor Cyan
    Write-Host "   상태:        $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
    Write-Host "   마지막 실행: $($info.LastRunTime)" -ForegroundColor Cyan
    Write-Host "   다음 실행:   $($info.NextRunTime)" -ForegroundColor Cyan
    
    # 마지막 실행 결과 확인
    $lastResult = $info.LastTaskResult
    if ($lastResult -eq 0) {
        Write-Host "   실행 결과:   ✅ 성공 (0)" -ForegroundColor Green
    }
    else {
        Write-Host "   실행 결과:   ⚠️  에러 ($lastResult)" -ForegroundColor Yellow
    }
    
    # Goal Tracker 상태 확인
$trackerPath = Join-Path $PSScriptRoot "fdo_agi_repo\memory\goal_tracker.json"
    if (Test-Path $trackerPath) {
        $tracker = Get-Content $trackerPath -Raw | ConvertFrom-Json
        $lastUpdateRaw = if ($tracker.PSObject.Properties.Name -contains 'last_update') { $tracker.last_update } else { $tracker.last_updated }
        $lastUpdate = if ($lastUpdateRaw) { [datetime]$lastUpdateRaw } else { $null }
        $timeSince = (Get-Date) - $lastUpdate
        
        Write-Host "`n📊 Goal Tracker 상태:" -ForegroundColor White
        Write-Host "   마지막 업데이트: $lastUpdate" -ForegroundColor Cyan
        Write-Host "   경과 시간:       $([int]$timeSince.TotalMinutes)분" -ForegroundColor $(if ($timeSince.TotalMinutes -lt 15) { 'Green' } elseif ($timeSince.TotalMinutes -lt 30) { 'Yellow' } else { 'Red' })
        
        if ($timeSince.TotalMinutes -lt 15) {
            Write-Host "   ✅ 정상 작동 중" -ForegroundColor Green
        }
        elseif ($timeSince.TotalMinutes -lt 30) {
            Write-Host "   ⚠️  약간 느림 (곧 자동 복구 예정)" -ForegroundColor Yellow
        }
        else {
            Write-Host "   ❌ 정체됨 (자동 복구 필요)" -ForegroundColor Red
        }
        
        # Active goals
        $activeGoals = @($tracker.active_goals)
        Write-Host "   활성 목표:       $($activeGoals.Count)개" -ForegroundColor Cyan
    }
    else {
        Write-Host "`n⚠️  Goal Tracker 파일 없음" -ForegroundColor Yellow
        Write-Host "   Goal Executor가 아직 실행되지 않았을 수 있습니다." -ForegroundColor Gray
    }
    
    # 로그 파일 확인
$logPath = Join-Path $PSScriptRoot "outputs\goal_executor_monitor.log"
    if (Test-Path $logPath) {
        $logLines = Get-Content $logPath -Tail 5
        if ($logLines) {
            Write-Host "`n📝 최근 로그 (마지막 5줄):" -ForegroundColor White
            $logLines | ForEach-Object {
                if ($_ -match "ERROR|FAILED") {
                    Write-Host "   $_" -ForegroundColor Red
                }
                elseif ($_ -match "WARNING|WARN") {
                    Write-Host "   $_" -ForegroundColor Yellow
                }
                else {
                    Write-Host "   $_" -ForegroundColor Gray
                }
            }
        }
    }
    
    Write-Host "`n💡 명령어:" -ForegroundColor White
    Write-Host "   즉시 실행:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
    Write-Host "   로그 보기:  Get-Content outputs\goal_executor_monitor.log -Tail 20" -ForegroundColor Cyan
    Write-Host "   제거:       .\REGISTER_GOAL_MONITOR.ps1 -Unregister" -ForegroundColor Cyan
    
}
catch {
    Write-Host "❌ Task가 등록되어 있지 않습니다." -ForegroundColor Red
    Write-Host "`n💡 등록 방법:" -ForegroundColor Yellow
    Write-Host "   .\REGISTER_GOAL_MONITOR.ps1" -ForegroundColor Cyan
    Write-Host "`n   또는 관리자 권한 PowerShell에서:" -ForegroundColor Yellow
    Write-Host "   .\scripts\register_goal_executor_monitor_task.ps1 -Register" -ForegroundColor Cyan
}

Write-Host "`n================================================================`n" -ForegroundColor Cyan
