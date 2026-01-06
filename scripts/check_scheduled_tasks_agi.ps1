# AGI 관련 스케줄 작업 확인 스크립트

Write-Host "`n📅 AGI 관련 스케줄 작업 확인" -ForegroundColor Cyan
Write-Host "=" * 60

# 모든 스케줄 작업 가져오기
$allTasks = Get-ScheduledTask -ErrorAction SilentlyContinue

# AGI 관련 작업 필터링
$agiTasks = $allTasks | Where-Object {
    $_.TaskName -like '*agi*' -or
    $_.TaskName -like '*AGI*' -or
    $_.TaskName -like '*trinity*' -or
    $_.TaskName -like '*Trinity*' -or
    $_.TaskName -like '*BQI*' -or
    $_.TaskName -like '*Binoche_Observer*' -or
    $_.TaskName -like '*Cache*' -or
    $_.TaskPath -like '*agi*'
}

if ($agiTasks.Count -eq 0) {
    Write-Host "`n✅ AGI 관련 스케줄 작업이 없습니다." -ForegroundColor Green
} else {
    Write-Host "`n📋 발견된 AGI 관련 작업 ($($agiTasks.Count)개):" -ForegroundColor Yellow
    Write-Host ""

    $agiTasks | Select-Object TaskName, State, TaskPath | Format-Table -AutoSize

    Write-Host "`n📝 상세 정보:" -ForegroundColor Cyan
    foreach ($task in $agiTasks) {
        Write-Host "`n  작업명: $($task.TaskName)" -ForegroundColor White
        Write-Host "  상태: $($task.State)" -ForegroundColor Gray
        Write-Host "  경로: $($task.TaskPath)" -ForegroundColor Gray

        $info = Get-ScheduledTaskInfo -TaskName $task.TaskName -ErrorAction SilentlyContinue
        if ($info) {
            Write-Host "  마지막 실행: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "  다음 실행: $($info.NextRunTime)" -ForegroundColor Gray
        }
    }
}

Write-Host "`n" + "=" * 60
Write-Host ""