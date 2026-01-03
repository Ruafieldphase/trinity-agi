# AGI 시스템 자동 시작 비활성화 스크립트
# ===============================================
# 모든 자동 시작 항목을 안전하게 비활성화합니다.

param(
    [switch]$DryRun,  # 실제로 변경하지 않고 미리보기만
    [switch]$Force    # 확인 없이 즉시 실행
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



Write-Host "`n🛑 AGI 시스템 자동 시작 비활성화" -ForegroundColor Red
Write-Host "=" * 80

if (-not $Force -and -not $DryRun) {
    Write-Host "`n⚠️  경고: 다음 자동 시작 항목들이 비활성화됩니다:" -ForegroundColor Yellow
    Write-Host "  1. 레지스트리 시작 항목: AGI_Master_Orchestrator" -ForegroundColor White
    Write-Host "  2. Task Scheduler: AGI_AutoStart" -ForegroundColor White
    Write-Host "  3. Task Scheduler: AGI Auto Rhythm Escalation" -ForegroundColor White
    Write-Host "  4. Task Scheduler: AGI_MetaSupervisor" -ForegroundColor White
    Write-Host ""
    $confirm = Read-Host "계속하시겠습니까? (Y/N)"
    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        Write-Host "`n취소되었습니다." -ForegroundColor Gray
        exit 0
    }
}

$changes = @()

# 1. 레지스트리 시작 항목 제거
Write-Host "`n[1/4] 레지스트리 시작 항목 확인..." -ForegroundColor Cyan
try {
    $regValue = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "AGI_Master_Orchestrator" -ErrorAction SilentlyContinue

    if ($regValue) {
        Write-Host "  발견: AGI_Master_Orchestrator" -ForegroundColor Yellow
        Write-Host "  값: $($regValue.AGI_Master_Orchestrator)" -ForegroundColor Gray

        if ($DryRun) {
            Write-Host "  [DRY RUN] 제거 예정" -ForegroundColor Cyan
            $changes += "레지스트리 항목 제거: AGI_Master_Orchestrator"
        } else {
            Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "AGI_Master_Orchestrator" -ErrorAction Stop
            Write-Host "  ✅ 제거 완료" -ForegroundColor Green
            $changes += "✅ 레지스트리 항목 제거: AGI_Master_Orchestrator"
        }
    } else {
        Write-Host "  ℹ️  레지스트리 항목이 없습니다 (이미 제거됨)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ 오류: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Task Scheduler 작업 비활성화
$tasksToDisable = @(
    "AGI_AutoStart",
    "AGI Auto Rhythm Escalation",
    "AGI_MetaSupervisor"
)

Write-Host "`n[2/4] Task Scheduler 작업 비활성화..." -ForegroundColor Cyan

foreach ($taskName in $tasksToDisable) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

        if ($task) {
            Write-Host "  발견: $taskName (현재 상태: $($task.State))" -ForegroundColor Yellow

            if ($task.State -eq "Disabled") {
                Write-Host "    ℹ️  이미 비활성화되어 있습니다" -ForegroundColor Gray
            } else {
                if ($DryRun) {
                    Write-Host "    [DRY RUN] 비활성화 예정" -ForegroundColor Cyan
                    $changes += "Task 비활성화: $taskName"
                } else {
                    Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
                    Write-Host "    ✅ 비활성화 완료" -ForegroundColor Green
                    $changes += "✅ Task 비활성화: $taskName"
                }
            }
        } else {
            Write-Host "  ℹ️  작업이 없습니다: $taskName" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ❌ 오류: $taskName - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. 백업 생성
Write-Host "`n[3/4] 백업 생성..." -ForegroundColor Cyan
$backupDir = "$WorkspaceRoot\outputs\sena\backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\autostart_backup_$timestamp.json"

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$backup = @{
    timestamp = $timestamp
    registry = @{
        path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
        name = "AGI_Master_Orchestrator"
        value = if ($regValue) { $regValue.AGI_Master_Orchestrator } else { $null }
        existed = ($null -ne $regValue)
    }
    tasks = @()
}

foreach ($taskName in $tasksToDisable) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
        $backup.tasks += @{
            name = $taskName
            state = $task.State
            lastRunTime = $taskInfo.LastRunTime
            lastResult = $taskInfo.LastTaskResult
        }
    }
}

if (-not $DryRun) {
    $backup | ConvertTo-Json -Depth 10 | Out-File -FilePath $backupFile -Encoding UTF8
    Write-Host "  ✅ 백업 완료: $backupFile" -ForegroundColor Green
    $changes += "✅ 백업 생성: $backupFile"
} else {
    Write-Host "  [DRY RUN] 백업 파일: $backupFile" -ForegroundColor Cyan
}

# 4. 요약
Write-Host "`n[4/4] 요약" -ForegroundColor Cyan
Write-Host "=" * 80

if ($DryRun) {
    Write-Host "`n🔍 DRY RUN 모드 - 실제로 변경되지 않았습니다" -ForegroundColor Cyan
    Write-Host "`n예상되는 변경 사항:" -ForegroundColor Yellow
} else {
    Write-Host "`n완료된 변경 사항:" -ForegroundColor Green
}

if ($changes.Count -eq 0) {
    Write-Host "  ℹ️  변경 사항 없음 (이미 모두 비활성화되어 있음)" -ForegroundColor Gray
} else {
    foreach ($change in $changes) {
        Write-Host "  • $change" -ForegroundColor White
    }
}

Write-Host "`n" + "=" * 80

if (-not $DryRun) {
    Write-Host "`n✅ 모든 AGI 자동 시작 항목이 비활성화되었습니다!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 시스템을 시작하려면:" -ForegroundColor Cyan
    Write-Host "   .\agi\scripts\master_orchestrator.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "🔄 복원하려면:" -ForegroundColor Cyan
    Write-Host "   .\agi\scripts\restore_autostart.ps1 $backupFile" -ForegroundColor White
} else {
    Write-Host "`n💡 실제로 실행하려면:" -ForegroundColor Cyan
    Write-Host "   .\agi\scripts\disable_all_autostart.ps1" -ForegroundColor White
    Write-Host "   또는" -ForegroundColor Gray
    Write-Host "   .\agi\scripts\disable_all_autostart.ps1 -Force" -ForegroundColor White
}

Write-Host ""