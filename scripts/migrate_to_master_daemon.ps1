<#
.SYNOPSIS
AGI 시스템을 Master Daemon으로 마이그레이션

.DESCRIPTION
- 기존의 모든 Scheduled Tasks 제거
- Startup 폴더 정리
- Master Daemon 설치
- 깔끔한 통합 시스템으로 전환
#>

param(
    [switch]$DryRun,
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║  AGI Master Daemon Migration                              ║
║  기존 시스템 → 통합 제어 시스템                           ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# 1. 기존 Scheduled Tasks 목록 확인
Write-Host "`n[1/5] Scanning existing Scheduled Tasks..." -ForegroundColor Yellow

$tasksToRemove = @(
    "AGI_Adaptive_Master_Scheduler",
    "AGI_Auto_Backup",
    "AGI_AutoContext",
    "AGI_AutonomousGoalExecutor",
    "AGI_AutonomousGoalGenerator",
    "AGI_AutopoieticTrinityCycle",
    "AGI_AutoTaskGenerator",
    "AGI_Evening_Milestone_Check",
    "AGI_FeedbackLoop",
    "AGI_Master_Orchestrator",
    "AGI_MetaLayerObserver",
    "AGI_MidDay_Milestone_Check",
    "AGI_Morning_Kickoff",
    "AGI_QuietHours_AlertCheck",
    "AGI_Sleep",
    "AGI_WakeUp",
    "AgiWatchdog",
    "AutoDreamPipeline",
    "AutopoieticLoopDailyReport",
    "BQI_Online_Learner_Daily",
    "BqiLearnerDaily",
    "TaskQueueServer"
)

$existingTasks = Get-ScheduledTask | Where-Object { $tasksToRemove -contains $_.TaskName }

Write-Host "  Found $($existingTasks.Count) AGI-related tasks" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "  [DRY-RUN] Would remove:" -ForegroundColor Yellow
    $existingTasks | ForEach-Object { Write-Host "    - $($_.TaskName)" -ForegroundColor Gray }
}
else {
    if (!$Force) {
        $confirm = Read-Host "  Remove these $($existingTasks.Count) tasks? (y/N)"
        if ($confirm -ne 'y') {
            Write-Host "  Aborted." -ForegroundColor Red
            return
        }
    }
    
    foreach ($task in $existingTasks) {
        try {
            Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false -EA Stop
            Write-Host "  ✓ Removed: $($task.TaskName)" -ForegroundColor Green
        }
        catch {
            Write-Host "  ✗ Failed to remove: $($task.TaskName)" -ForegroundColor Red
        }
    }
}

# 2. Startup 폴더 정리
Write-Host "`n[2/5] Cleaning Startup folder..." -ForegroundColor Yellow

$startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$startupFiles = @(
    "AGI_AIOpsManager.lnk",
    "AGI_AutoResume.lnk",
    "AGI_Auto_Resume.lnk",
    "AutonomousWorkWorker.cmd",
    "Start-SenaSuite.cmd"
)

foreach ($file in $startupFiles) {
    $fullPath = Join-Path $startupPath $file
    if (Test-Path $fullPath) {
        if ($DryRun) {
            Write-Host "  [DRY-RUN] Would remove: $file" -ForegroundColor Yellow
        }
        else {
            Remove-Item $fullPath -Force
            Write-Host "  ✓ Removed: $file" -ForegroundColor Green
        }
    }
}

# 3. 실행 중인 프로세스 중지
Write-Host "`n[3/5] Stopping running AGI processes..." -ForegroundColor Yellow

$processesToStop = Get-Process -Name powershell, pwsh, python, py -EA SilentlyContinue | 
Where-Object { 
    $_.CommandLine -like '*observe_desktop_telemetry*' -or
    $_.CommandLine -like '*adaptive_master_scheduler*' -or
    $_.CommandLine -like '*task_queue_server*' -or
    $_.CommandLine -like '*rpa_worker*' -or
    $_.CommandLine -like '*task_watchdog*'
}

if ($processesToStop) {
    Write-Host "  Found $($processesToStop.Count) running processes" -ForegroundColor Cyan
    
    if ($DryRun) {
        Write-Host "  [DRY-RUN] Would stop:" -ForegroundColor Yellow
        $processesToStop | ForEach-Object { Write-Host "    - $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray }
    }
    else {
        foreach ($proc in $processesToStop) {
            try {
                $proc.Kill()
                Write-Host "  ✓ Stopped: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Green
            }
            catch {
                Write-Host "  ✗ Failed to stop: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
            }
        }
    }
}
else {
    Write-Host "  No running processes found" -ForegroundColor Gray
}

# 4. Master Daemon 설치
Write-Host "`n[4/5] Installing Master Daemon..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "  [DRY-RUN] Would install AGI_Master_Daemon" -ForegroundColor Yellow
}
else {
    & "$WorkspaceRoot\scripts\master_daemon.ps1" -Install
}

# 5. 검증
Write-Host "`n[5/5] Verification..." -ForegroundColor Yellow

$remainingTasks = Get-ScheduledTask | Where-Object { $tasksToRemove -contains $_.TaskName }
if ($remainingTasks.Count -eq 0) {
    Write-Host "  ✓ All old tasks removed" -ForegroundColor Green
}
else {
    Write-Host "  ✗ Some tasks still remain: $($remainingTasks.Count)" -ForegroundColor Red
}

$masterDaemon = Get-ScheduledTask -TaskName "AGI_Master_Daemon" -EA SilentlyContinue
if ($masterDaemon) {
    Write-Host "  ✓ Master Daemon installed" -ForegroundColor Green
}
else {
    Write-Host "  ✗ Master Daemon not found" -ForegroundColor Red
}

# 완료
Write-Host @"

╔════════════════════════════════════════════════════════════╗
║  Migration Complete!                                       ║
╚════════════════════════════════════════════════════════════╝

다음 명령으로 제어할 수 있습니다:

    .\agi.ps1 start      # 시스템 시작
    .\agi.ps1 stop       # 시스템 중지
    .\agi.ps1 restart    # 재시작
    .\agi.ps1 status     # 상태 확인
    .\agi.ps1 logs       # 로그 보기

다음 로그온 시 자동으로 Master Daemon이 시작됩니다.

"@ -ForegroundColor Cyan