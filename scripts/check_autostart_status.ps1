# AGI 자동 시작 상태 확인 스크립트

Write-Host "`n📊 AGI 자동 시작 상태" -ForegroundColor Cyan
Write-Host "=" * 80

# 1. 레지스트리 확인
Write-Host "`n[레지스트리 시작 항목]" -ForegroundColor Yellow
$regValue = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "AGI_Master_Orchestrator" -ErrorAction SilentlyContinue

if ($regValue) {
    Write-Host "  ⚠️  AGI_Master_Orchestrator: 활성화됨" -ForegroundColor Yellow
    Write-Host "     값: $($regValue.AGI_Master_Orchestrator)" -ForegroundColor Gray
} else {
    Write-Host "  ✅ AGI_Master_Orchestrator: 비활성화됨" -ForegroundColor Green
}

# 2. Task Scheduler 확인
Write-Host "`n[Task Scheduler 작업]" -ForegroundColor Yellow

$tasksToCheck = @(
    "AGI_AutoStart",
    "AGI Auto Rhythm Escalation",
    "AGI_MetaSupervisor",
    "AGI_GoalExecutorMonitor",
    "AGI_Master_Daemon"
)

$activeCount = 0
$disabledCount = 0
$notFoundCount = 0

foreach ($taskName in $tasksToCheck) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

    if ($task) {
        if ($task.State -eq "Ready") {
            Write-Host "  ⚠️  $taskName : 활성화됨" -ForegroundColor Yellow
            $info = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
            if ($info.NextRunTime) {
                Write-Host "     다음 실행: $($info.NextRunTime)" -ForegroundColor Gray
            }
            $activeCount++
        } elseif ($task.State -eq "Disabled") {
            Write-Host "  ✅ $taskName : 비활성화됨" -ForegroundColor Green
            $disabledCount++
        } else {
            Write-Host "  ℹ️  $taskName : $($task.State)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ℹ️  $taskName : 존재하지 않음" -ForegroundColor Gray
        $notFoundCount++
    }
}

# 3. 요약
Write-Host "`n[요약]" -ForegroundColor Cyan
Write-Host "  활성화된 작업: $activeCount 개" -ForegroundColor $(if ($activeCount -gt 0) { "Yellow" } else { "Green" })
Write-Host "  비활성화된 작업: $disabledCount 개" -ForegroundColor Green
Write-Host "  존재하지 않는 작업: $notFoundCount 개" -ForegroundColor Gray

# 4. 권장 사항
Write-Host "`n[권장 사항]" -ForegroundColor Cyan

$hasRegistry = $null -ne $regValue
$hasActiveTask = $activeCount -gt 0

if ($hasRegistry -and $hasActiveTask) {
    Write-Host "  ⚠️  레지스트리와 Task Scheduler가 모두 활성화되어 있습니다!" -ForegroundColor Red
    Write-Host "     중복 실행 가능성이 있습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  비활성화하려면:" -ForegroundColor Cyan
    Write-Host "     .\agi\scripts\disable_all_autostart.ps1" -ForegroundColor White
} elseif ($hasRegistry -or $hasActiveTask) {
    Write-Host "  ℹ️  일부 자동 시작 항목이 활성화되어 있습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  모두 비활성화하려면:" -ForegroundColor Cyan
    Write-Host "     .\agi\scripts\disable_all_autostart.ps1" -ForegroundColor White
} else {
    Write-Host "  ✅ 모든 자동 시작 항목이 비활성화되어 있습니다." -ForegroundColor Green
    Write-Host ""
    Write-Host "  수동으로 시작하려면:" -ForegroundColor Cyan
    Write-Host "     .\agi\scripts\master_orchestrator.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "  복원하려면:" -ForegroundColor Cyan
    Write-Host "     .\agi\scripts\restore_autostart.ps1" -ForegroundColor White
}

Write-Host "`n" + "=" * 80
Write-Host ""
