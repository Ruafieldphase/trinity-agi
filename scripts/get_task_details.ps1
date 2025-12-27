# 특정 작업의 상세 정보 확인

$taskNames = @(
    "AGI Auto Rhythm Escalation",
    "AGI_AutoStart",
    "AGI_MetaSupervisor"
)

Write-Host "`n🔍 AGI 작업 상세 정보" -ForegroundColor Cyan
Write-Host "=" * 80

foreach ($taskName in $taskNames) {
    Write-Host "`n📋 작업: $taskName" -ForegroundColor Yellow
    Write-Host "-" * 80

    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction Stop

        # 기본 정보
        Write-Host "  상태: $($task.State)" -ForegroundColor White
        Write-Host "  마지막 실행: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "  다음 실행: $($info.NextRunTime)" -ForegroundColor Gray
        Write-Host "  마지막 결과: $($info.LastTaskResult)" -ForegroundColor Gray

        # 트리거 정보
        Write-Host "`n  트리거:" -ForegroundColor Cyan
        foreach ($trigger in $task.Triggers) {
            Write-Host "    - $($trigger.CimClass.CimClassName)" -ForegroundColor Gray
            if ($trigger.Repetition) {
                Write-Host "      반복 간격: $($trigger.Repetition.Interval)" -ForegroundColor Gray
            }
        }

        # 실행할 명령
        Write-Host "`n  실행 동작:" -ForegroundColor Cyan
        foreach ($action in $task.Actions) {
            Write-Host "    실행: $($action.Execute)" -ForegroundColor White
            Write-Host "    인수: $($action.Arguments)" -ForegroundColor Gray
            Write-Host "    작업 디렉토리: $($action.WorkingDirectory)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ❌ 작업을 찾을 수 없습니다: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + "=" * 80
Write-Host ""
