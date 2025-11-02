# Self-Healing Level 1 배포 및 등록
# 자동 복구 시스템을 Windows Scheduled Task로 등록

param(
    [switch]$AutoStart = $true
)

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🏥 Self-Healing Level 1 배포" -ForegroundColor Yellow
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

$TaskName = "AGI_Self_Healing_Level1"
$ScriptPath = "C:\workspace\agi\scripts\self_healing_level1.ps1"

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

# 작업 트리거 생성 (즉시 시작, 시스템 부팅 시)
$trigger = New-ScheduledTaskTrigger -AtStartup

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
        -Description "AGI Self-Healing Level 1 - 시스템 이상에 자동으로 대응하고 복구" `
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
Write-Host "  트리거:       시스템 부팅 시 + 즉시" -ForegroundColor Gray
Write-Host "  상태:         $($task.State)" -ForegroundColor Green
Write-Host ""

# 즉시 시작 (요청된 경우)
if ($AutoStart) {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ 자가 치유 시스템이 즉시 시작되었습니다!" -ForegroundColor Green
        Start-Sleep -Seconds 2

        $task = Get-ScheduledTask -TaskName $TaskName
        Write-Host "  마지막 실행:  $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "  상태:         정상 운영 중" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  경고: 작업을 즉시 시작할 수 없습니다: $_" -ForegroundColor Yellow
    }
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host "  🏥 Self-Healing Level 1 배포 완료" -ForegroundColor Green
Write-Host ("=" * 90) -ForegroundColor Magenta
Write-Host ""

Write-Host "🎵 완전한 지능형 자동화 시스템이 이제 준비되었습니다:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   감지 (Detection):     Phase 3 - Event Detector" -ForegroundColor Yellow
Write-Host "   대응 (Response):      Self-Healing Level 1" -ForegroundColor Green
Write-Host "   조율 (Orchestration): Integrated Rhythm System" -ForegroundColor Magenta
Write-Host ""
Write-Host "   🔄 순환: 감지 → 진단 → 치유 → 복구 → 모니터링 (반복)" -ForegroundColor Cyan
Write-Host ""
