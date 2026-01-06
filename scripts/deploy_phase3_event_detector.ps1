# Phase 3 배포 - 이벤트 감지기 (Event Detector) 활성화
# 시스템 지능형 모니터링 및 이상 탐지 시작

param(
    [switch]$AutoStart = $true
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🎵 PHASE 3 배포 - 이벤트 감지기 (Event Detector) 활성화" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

$TaskName = "AGI_Event_Detector"
$ScriptPath = "$WorkspaceRoot\scripts\event_detector.ps1"

# 스크립트 존재 확인
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ 오류: 스크립트를 찾을 수 없습니다: $ScriptPath" -ForegroundColor Red
    exit 1
}

# 기존 작업 확인
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "기존 작업을 찾았습니다. 다시 등록합니다..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    Start-Sleep -Seconds 1
}

# 작업 액션 생성
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File '$ScriptPath'"

# 작업 트리거 생성 (1분마다 실행)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration (New-TimeSpan -Days 999)

# 작업 설정 생성
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries

# 작업 등록
try {
    Register-ScheduledTask -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "AGI Phase 3 - 실시간 이벤트 감지기. 시스템 이상 탐지 및 자동 대응" `
        -Force | Out-Null

    Write-Host "✅ 작업이 성공적으로 등록되었습니다!" -ForegroundColor Green
} catch {
    Write-Host "❌ 작업 등록 실패: $_" -ForegroundColor Red
    exit 1
}

# 등록된 작업 정보
$task = Get-ScheduledTask -TaskName $TaskName

# 등록 상세 정보 표시
Write-Host "`n📋 배포 상세:" -ForegroundColor Cyan
Write-Host "  작업명:       $TaskName" -ForegroundColor Gray
Write-Host "  스크립트:     $ScriptPath" -ForegroundColor Gray
Write-Host "  실행 간격:    1분 (연속)" -ForegroundColor Gray
Write-Host "  상태:         $($task.State)" -ForegroundColor Green
Write-Host ""

# 즉시 시작 (요청된 경우)
if ($AutoStart) {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ 이벤트 감지기가 즉시 시작되었습니다!" -ForegroundColor Green
        Start-Sleep -Seconds 2

        $task = Get-ScheduledTask -TaskName $TaskName
        Write-Host "  마지막 실행:  $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "  다음 실행:    $($task.NextRunTime)" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️  경고: 작업을 즉시 시작할 수 없습니다: $_" -ForegroundColor Yellow
    }
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🎵 PHASE 3 배포 완료 - 지능형 시스템 이제 활성화됨" -ForegroundColor Green
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

# 최종 확인
Write-Host "✅ 모든 Phase가 이제 배포되었습니다:" -ForegroundColor Green
Write-Host "   🔴 Phase 1: 마스터 스케줄러 (AGI_Master_Scheduler)" -ForegroundColor Red
Write-Host "   🔵 Phase 2: 적응형 스케줄러 (AGI_Adaptive_Master_Scheduler)" -ForegroundColor Cyan
Write-Host "   🟡 Phase 3: 이벤트 감지기 (AGI_Event_Detector) ✅ NEW" -ForegroundColor Yellow
Write-Host "   🟢 오케스트레이터: 통합 리듬 시스템 (AGI_Integrated_Rhythm_Orchestrator)" -ForegroundColor Green
Write-Host ""

# 시스템 건강도 확인
Write-Host "🏥 현재 시스템 상태:" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1

$memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
$cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }
$pythonProcs = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' } | Measure-Object).Count

Write-Host "  CPU:              $cpuLoad% (목표: <35%)" -ForegroundColor Gray
Write-Host "  메모리:           $memUsage% (목표: <45%)" -ForegroundColor Gray
Write-Host "  파이썬 프로세스:  $pythonProcs개 (목표: <40)" -ForegroundColor Gray
Write-Host ""