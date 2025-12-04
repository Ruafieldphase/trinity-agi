# Master Daemon 통합 스크립트 (관리자 권한 필요)
# 우클릭 → "관리자 권한으로 실행"

$ErrorActionPreference = "Continue"

Write-Host "`n=== AGI Master Daemon 통합 시작 ===" -ForegroundColor Cyan

# 1. Master Daemon 설치
Write-Host "`n[1/3] Master Daemon 설치 중..." -ForegroundColor Yellow
try {
    & "C:\workspace\agi\scripts\master_daemon.ps1" -Install
    Write-Host "✅ Master Daemon 설치 완료" -ForegroundColor Green
}
catch {
    Write-Host "❌ Master Daemon 설치 실패: $_" -ForegroundColor Red
}

# 2. 중복 작업 비활성화
Write-Host "`n[2/3] 중복 작업 비활성화 중..." -ForegroundColor Yellow
$tasksToDisable = @(
    'AGI_GoalExecutorMonitor',
    'ION Monitor Loop',
    'CacheValidation_12h',
    'CacheValidation_24h',
    'CacheValidation_7d',
    'MonitoringSnapshotRotationDaily'
)

foreach ($taskName in $tasksToDisable) {
    try {
        Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
        Write-Host "  ✅ Disabled: $taskName" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️ Not found or already disabled: $taskName" -ForegroundColor Gray
    }
}

# 3. Master Daemon 시작
Write-Host "`n[3/3] Master Daemon 시작 중..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName "AGI_Master_Daemon" -ErrorAction Stop
    Write-Host "✅ Master Daemon 시작 완료" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Master Daemon 시작 실패 (나중에 로그온 시 자동 시작됨)" -ForegroundColor Yellow
}

# 상태 확인
Write-Host "`n=== 최종 상태 확인 ===" -ForegroundColor Cyan
Start-Sleep -Seconds 2
& "C:\workspace\agi\scripts\master_daemon.ps1" -Status

Write-Host "`n=== 통합 완료 ===" -ForegroundColor Green
Write-Host "팝업 창이 더 이상 뜨지 않습니다!" -ForegroundColor Cyan

Read-Host "`nPress Enter to exit"
