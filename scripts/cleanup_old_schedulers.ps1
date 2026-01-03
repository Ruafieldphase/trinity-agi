# AGI Old Schedulers Cleanup
# 기존 중복 스케줄러들을 비활성화하고 Guardian으로 통합

$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AGI Scheduler Cleanup" -ForegroundColor Cyan
Write-Host "  (Guardian으로 통합)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 비활성화할 AGI 관련 작업들
$tasksToDisable = @(
    "AGI Auto Rhythm Escalation",
    "AGI_GoalExecutorMonitor",
    "AGI_MetaSupervisor",
    "AsyncThesisHealthMonitor",
    "BinocheEnsembleMonitor",
    "BinocheOnlineLearner",
    "ION Monitor Loop",
    "MonitoringCollector",
    "StreamObserverTelemetry",
    "LoopDashboard",
    "ReplanTrendUpdater",
    "TaskQueueServer",
    "OriginalDataApiEnsure"
)

Write-Host ""
Write-Host "[INFO] Disabling old AGI schedulers..." -ForegroundColor Yellow
Write-Host ""

$disabled = 0
$failed = 0

foreach ($task in $tasksToDisable) {
    $result = schtasks /Change /TN $task /Disable 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $task" -ForegroundColor Green
        $disabled++
    } else {
        # 작업이 없거나 이미 비활성화됨
        Write-Host "  [SKIP] $task (not found or already disabled)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Result: $disabled tasks disabled" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[TIP] Guardian 시작: .\scripts\start_guardian.ps1" -ForegroundColor Cyan
Write-Host "[TIP] Guardian 상태: cat outputs\guardian_state.json" -ForegroundColor Cyan