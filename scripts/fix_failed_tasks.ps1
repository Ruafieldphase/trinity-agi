<#
.SYNOPSIS
    실패한 작업들을 백그라운드로 수정 (관리자 권한 필요)
#>

$ErrorActionPreference = 'Stop'

Write-Host "`n🔧 실패한 작업 수동 수정..." -ForegroundColor Yellow
Write-Host ""

# WorkingDirectory가 빈 작업들
$tasksToFix = @(
    @{Name = "AgiWatchdog"; WorkDir = "C:\workspace\agi" },
    @{Name = "AGI_Adaptive_Master_Scheduler"; WorkDir = "C:\workspace\agi" },
    @{Name = "MonitoringSnapshotRotationDaily"; WorkDir = "C:\workspace\agi" }
)

foreach ($taskInfo in $tasksToFix) {
    try {
        $task = Get-ScheduledTask -TaskName $taskInfo.Name -ErrorAction SilentlyContinue
        if (-not $task) {
            Write-Host "  ⊘ 없음: $($taskInfo.Name)" -ForegroundColor Gray
            continue
        }

        $action = $task.Actions | Select-Object -First 1
        
        # -WindowStyle Hidden 추가
        $newArgs = "-WindowStyle Hidden " + $action.Arguments
        
        $newAction = New-ScheduledTaskAction `
            -Execute $action.Execute `
            -Argument $newArgs `
            -WorkingDirectory $taskInfo.WorkDir
        
        Set-ScheduledTask -TaskName $taskInfo.Name -Action $newAction | Out-Null
        Write-Host "  ✅ 수정: $($taskInfo.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️  실패: $($taskInfo.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# BinocheOnlineLearner pythonw로 전환
try {
    $task = Get-ScheduledTask -TaskName "BinocheOnlineLearner" -ErrorAction SilentlyContinue
    if ($task) {
        $action = $task.Actions | Select-Object -First 1
        $newExecute = $action.Execute -replace 'python\.exe$', 'pythonw.exe'
        
        $newAction = New-ScheduledTaskAction `
            -Execute $newExecute `
            -Argument $action.Arguments `
            -WorkingDirectory $action.WorkingDirectory
        
        Set-ScheduledTask -TaskName "BinocheOnlineLearner" -Action $newAction | Out-Null
        Write-Host "  ✅ 수정 (pythonw): BinocheOnlineLearner" -ForegroundColor Green
    }
}
catch {
    Write-Host "  ⚠️  실패: BinocheOnlineLearner - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ 완료!" -ForegroundColor Green
Write-Host ""
