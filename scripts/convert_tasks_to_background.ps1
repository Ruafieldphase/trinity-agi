<#
.SYNOPSIS
    모든 AGI 작업을 백그라운드(숨김)로 전환

.DESCRIPTION
    - 필요없는 작업: 제거
    - 필요한 작업: WindowStyle Hidden 추가
    - 백그라운드 실행으로 전환
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI 작업 → 백그라운드 전환                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 제거할 작업 (중복/불필요)
$tasksToRemove = @(
    "AGI_Event_Detector",           # 중복
    "AGI_Performance_Monitor",      # 중복
    "AGI_Master_Scheduler",         # 중복 (Adaptive가 대체)
    "AGI_Integrated_Rhythm_Orchestrator",  # 중복
    "WorkerMonitor"                 # 중복 (ensure_rpa_worker로 대체)
)

# 백그라운드로 전환할 작업 (필요함)
$tasksToConvert = @(
    "AgiWatchdog",
    "AGI_Adaptive_Master_Scheduler",
    "MonitoringCollector",
    "BinocheEnsembleMonitor",
    "BinocheOnlineLearner",
    "MonitoringDailyMaintenance",
    "MonitoringSnapshotRotationDaily"
)

# 그대로 유지 (이미 Hidden)
$tasksAlreadyHidden = @(
    "AGI_AutoContext",
    "AGI_Master_Orchestrator",
    "AGI_Morning_Kickoff",
    "AGI_Sleep",
    "AGI_WakeUp"
)

Write-Host "📋 작업 분류:" -ForegroundColor Yellow
Write-Host "  제거: $($tasksToRemove.Count)개" -ForegroundColor Red
Write-Host "  전환: $($tasksToConvert.Count)개" -ForegroundColor Green
Write-Host "  유지: $($tasksAlreadyHidden.Count)개 (이미 숨김)" -ForegroundColor Cyan
Write-Host ""

# 1. 불필요한 작업 제거
Write-Host "🗑️  [1/3] 불필요한 작업 제거 중..." -ForegroundColor Yellow
foreach ($taskName in $tasksToRemove) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            if ($DryRun) {
                Write-Host "   [DRY-RUN] 제거: $taskName" -ForegroundColor Gray
            }
            else {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-Host "   ✅ 제거: $taskName" -ForegroundColor Green
            }
        }
        else {
            Write-Host "   ⊘ 없음: $taskName" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ⚠️  실패: $taskName - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 2. 백그라운드로 전환
Write-Host "`n🔄 [2/3] 백그라운드로 전환 중..." -ForegroundColor Yellow

foreach ($taskName in $tasksToConvert) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if (-not $task) {
            Write-Host "   ⊘ 없음: $taskName" -ForegroundColor Gray
            continue
        }

        $action = $task.Actions | Select-Object -First 1
        $currentArgs = $action.Arguments

        # 이미 Hidden이 있는지 확인
        if ($currentArgs -like "*-WindowStyle Hidden*") {
            Write-Host "   ✓ 이미 숨김: $taskName" -ForegroundColor Cyan
            continue
        }

        if ($DryRun) {
            Write-Host "   [DRY-RUN] 전환: $taskName" -ForegroundColor Gray
            Write-Host "     현재: $($currentArgs.Substring(0, [Math]::Min(60, $currentArgs.Length)))..." -ForegroundColor DarkGray
            continue
        }

        # PowerShell 작업인 경우 -WindowStyle Hidden 추가
        if ($action.Execute -like "*powershell.exe") {
            $newArgs = $currentArgs -replace '^(-NoProfile)', '-WindowStyle Hidden $1'
            
            # 새 액션 생성
            $newAction = New-ScheduledTaskAction `
                -Execute $action.Execute `
                -Argument $newArgs `
                -WorkingDirectory $action.WorkingDirectory

            # 작업 업데이트
            Set-ScheduledTask -TaskName $taskName -Action $newAction | Out-Null
            Write-Host "   ✅ 전환: $taskName" -ForegroundColor Green
        }
        # Python 작업인 경우 pythonw.exe로 전환
        elseif ($action.Execute -like "*python.exe") {
            $newExecute = $action.Execute -replace 'python\.exe$', 'pythonw.exe'
            
            $newAction = New-ScheduledTaskAction `
                -Execute $newExecute `
                -Argument $action.Arguments `
                -WorkingDirectory $action.WorkingDirectory

            Set-ScheduledTask -TaskName $taskName -Action $newAction | Out-Null
            Write-Host "   ✅ 전환 (pythonw): $taskName" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  지원 안됨: $taskName ($($action.Execute))" -ForegroundColor Yellow
        }

    }
    catch {
        Write-Host "   ⚠️  실패: $taskName - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. 확인
Write-Host "`n✅ [3/3] 결과 확인..." -ForegroundColor Yellow

$allTasks = Get-ScheduledTask | Where-Object { 
    $_.TaskName -like "*AGI*" -or 
    $_.TaskName -like "*Monitoring*" -or 
    $_.TaskName -like "*Binoche_Observer*" 
}

$hiddenCount = 0
$visibleCount = 0

foreach ($task in $allTasks) {
    $action = $task.Actions | Select-Object -First 1
    if ($action.Arguments -like "*-WindowStyle Hidden*" -or $action.Execute -like "*pythonw.exe") {
        $hiddenCount++
    }
    else {
        $visibleCount++
        if (-not $DryRun) {
            Write-Host "   ⚠️  아직 보임: $($task.TaskName)" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  완료!                                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 결과:" -ForegroundColor Cyan
Write-Host "  ✅ 백그라운드: $hiddenCount 개" -ForegroundColor Green
Write-Host "  ⚠️  보임: $visibleCount 개" -ForegroundColor $(if ($visibleCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($DryRun) {
    Write-Host "💡 실제 적용하려면:" -ForegroundColor Cyan
    Write-Host "  .\scripts\convert_tasks_to_background.ps1" -ForegroundColor White
    Write-Host ""
}

if ($visibleCount -gt 0 -and -not $DryRun) {
    Write-Host "💡 남은 작업은 수동 확인 필요" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "✅ 이제 5분마다 팝업 없이 조용히 실행됩니다!" -ForegroundColor Green
Write-Host ""