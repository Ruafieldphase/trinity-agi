# 관리자 권한으로 Task 비활성화

Write-Host "🛑 관리자 권한으로 Task 비활성화" -ForegroundColor Red

$tasksToDisable = @(
    "AGI_AutoStart",
    "AGI_MetaSupervisor"
)

foreach ($taskName in $tasksToDisable) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task -and $task.State -ne "Disabled") {
            Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
            Write-Host "✅ $taskName 비활성화 완료" -ForegroundColor Green
        } else {
            Write-Host "ℹ️  $taskName 이미 비활성화됨" -ForegroundColor Gray
        }
    } catch {
        Write-Host "❌ $taskName 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
}