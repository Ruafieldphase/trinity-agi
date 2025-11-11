#Requires -RunAsAdministrator
<#
.SYNOPSIS
    관리자 권한으로 기존 AGI 작업 정리
.DESCRIPTION
    Master Daemon으로 마이그레이션하기 전에 기존 작업들을 정리합니다.
    관리자 권한이 필요합니다.
#>

param(
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "`n🧹 AGI Task Cleanup (Admin Mode)`n" -ForegroundColor Cyan

# 제거할 작업 목록 (Master Daemon이 대체할 작업들)
$tasksToRemove = @(
    'AgiWatchdog',
    'AGI_Adaptive_Master_Scheduler',
    'AGI_Auto_Backup',
    'AGI_AutopoieticTrinityCycle',
    'AGI_Master_Orchestrator',
    'AGI_MetaLayerObserver',
    'AutoDreamPipeline',
    'TaskQueueServer'
)

Write-Host "제거 대상 작업:" -ForegroundColor Yellow
$tasksToRemove | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

if ($DryRun) {
    Write-Host "`n[DRY-RUN] 실제로는 제거하지 않습니다.`n" -ForegroundColor Yellow
    return
}

if (-not $Force) {
    $confirm = Read-Host "`n정말로 제거하시겠습니까? (yes/no)"
    if ($confirm -ne 'yes') {
        Write-Host "취소되었습니다." -ForegroundColor Yellow
        return
    }
}

Write-Host "`n제거 중..." -ForegroundColor Cyan
$removed = 0
$failed = 0

foreach ($taskName in $tasksToRemove) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "  ✓ Removed: $taskName" -ForegroundColor Green
            $removed++
        }
        else {
            Write-Host "  - Not found: $taskName" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ✗ Failed: $taskName - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n결과:" -ForegroundColor Cyan
Write-Host "  제거됨: $removed" -ForegroundColor Green
Write-Host "  실패: $failed" -ForegroundColor $(if ($failed -gt 0) { 'Red' } else { 'Gray' })

if ($failed -eq 0 -and $removed -gt 0) {
    Write-Host "`n✅ 모든 작업이 성공적으로 제거되었습니다!" -ForegroundColor Green
    Write-Host "`n다음 단계:" -ForegroundColor Cyan
    Write-Host "  1. .\agi.ps1 install    # Master Daemon 설치" -ForegroundColor Gray
    Write-Host "  2. .\agi.ps1 start      # 시스템 시작`n" -ForegroundColor Gray
}
