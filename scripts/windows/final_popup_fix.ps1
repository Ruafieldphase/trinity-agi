# 최종 팝업 제거 스크립트 (관리자 권한 필요)
# 우클릭 → "관리자 권한으로 실행"

$ErrorActionPreference = "Continue"

Write-Host "`n=== 최종 팝업 제거 작업 ===" -ForegroundColor Cyan

# Master Daemon과 중복되는 작업들 비활성화
$tasksToDisable = @(
    'AGI_MetaSupervisor',
    'IonInboxWatcher'
)

Write-Host "`n[1/2] 중복 작업 비활성화..." -ForegroundColor Yellow
foreach ($taskName in $tasksToDisable) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        if ($task.State -ne 'Disabled') {
            Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
            Write-Host "  ✅ Disabled: $taskName" -ForegroundColor Green
        }
        else {
            Write-Host "  ✓ Already disabled: $taskName" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ❌ Error: $taskName - $_" -ForegroundColor Red
    }
}

Write-Host "`n[2/2] 최종 상태 확인..." -ForegroundColor Yellow
$allTasks = @('AGI Auto Rhythm Escalation', 'AGI_MetaSupervisor', 'IonInboxWatcher', 'Purple', 'AGI_GoalExecutorMonitor', 'ION Monitor Loop')
$results = Get-ScheduledTask | Where-Object { $_.TaskName -in $allTasks } | Select-Object TaskName, State, @{Name = 'Hidden'; Expression = { $_.Settings.Hidden } }

Write-Host "`n=== 작업 상태 ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$readyCount = ($results | Where-Object { $_.State -eq 'Ready' }).Count
$disabledCount = ($results | Where-Object { $_.State -eq 'Disabled' }).Count
$hiddenCount = ($results | Where-Object { $_.Settings.Hidden -eq $true }).Count

Write-Host "`n=== 요약 ===" -ForegroundColor Cyan
Write-Host "  총 작업: $($results.Count)" -ForegroundColor White
Write-Host "  비활성화됨: $disabledCount" -ForegroundColor Green
Write-Host "  활성 상태: $readyCount" -ForegroundColor $(if ($readyCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "  숨김 모드: $hiddenCount / $($results.Count)" -ForegroundColor Green

if ($readyCount -eq 0 -or ($results | Where-Object { $_.State -eq 'Ready' -and $_.Settings.Hidden -eq $false }).Count -eq 0) {
    Write-Host "`n✅ 완료! 팝업 창이 더 이상 뜨지 않습니다!" -ForegroundColor Green
}
else {
    Write-Host "`n⚠️ 일부 작업이 여전히 활성화되어 있을 수 있습니다." -ForegroundColor Yellow
}

Write-Host "`n=== Master Daemon 상태 ===" -ForegroundColor Cyan
& "C:\workspace\agi\scripts\master_daemon.ps1" -Status

Read-Host "`nPress Enter to exit"
