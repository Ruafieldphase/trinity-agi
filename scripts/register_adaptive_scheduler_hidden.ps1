# Register Adaptive Scheduler with Hidden Window
# Run this script with Administrator privileges

param(
    [switch]$Unregister
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

$TaskName = "AGI_Adaptive_Master_Scheduler"
$ScriptPath = "$WorkspaceRoot\scripts\adaptive_master_scheduler.ps1"

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n⚠️  관리자 권한이 필요합니다!" -ForegroundColor Red
    Write-Host "   PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요.`n" -ForegroundColor Yellow
    exit 1
}

if ($Unregister) {
    Write-Host "`nUnregistering $TaskName..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ Unregistered!" -ForegroundColor Green
    exit 0
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Adaptive Scheduler 등록 (Hidden 모드)                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Unregister if exists
Write-Host "[1/4] 기존 작업 제거..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "      ✅ 완료" -ForegroundColor Green

# Create action (Hidden window)
Write-Host "[2/4] 작업 생성 (Hidden 모드)..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
Write-Host "      ✅ 완료" -ForegroundColor Green

# Create trigger (every 5 minutes)
Write-Host "[3/4] 트리거 생성 (5분 간격)..." -ForegroundColor Yellow
$trigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5)
Write-Host "      ✅ 완료" -ForegroundColor Green

# Create settings (Hidden, run even if on battery)
Write-Host "[4/4] 설정 및 등록..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -Hidden

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User $env:USERNAME `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "      ✅ 완료" -ForegroundColor Green

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✅ 등록 완료!                                     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📋 작업 정보:" -ForegroundColor Cyan
Write-Host "  • 이름: $TaskName" -ForegroundColor White
Write-Host "  • 실행 간격: 5분" -ForegroundColor White
Write-Host "  • 창 모드: Hidden (보이지 않음)" -ForegroundColor White
Write-Host "  • 다음 실행: $(Get-Date (Get-ScheduledTaskInfo $TaskName).NextRunTime -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

Write-Host "`n💡 확인 명령어:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Format-List" -ForegroundColor Gray
Write-Host "`n🎊 이제 창이 뜨지 않습니다!`n" -ForegroundColor Green