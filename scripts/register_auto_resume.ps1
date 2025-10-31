# ============================================================
# Windows 부팅 시 자동 실행 등록 스크립트
# ============================================================
# 목적: PC 재부팅 시 자동으로 AGI Phase 2.5 재개
# 사용: 한 번만 실행하면 영구 등록
# ============================================================

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$TaskName = "AGI_Phase25_AutoResume"
$WorkspaceRoot = "C:\workspace\agi"
$ScriptPath = Join-Path $WorkspaceRoot "scripts\auto_resume_on_startup.ps1"

# ============================================================
# 1. 현재 상태 확인
# ============================================================
function Get-TaskStatus {
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($Task) {
        Write-Host "✅ 자동 재개 시스템 등록됨" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 작업 정보:" -ForegroundColor Cyan
        Write-Host "   이름: $($Task.TaskName)" -ForegroundColor Gray
        Write-Host "   상태: $($Task.State)" -ForegroundColor Gray
        Write-Host "   트리거: 로그온 시" -ForegroundColor Gray
        Write-Host "   스크립트: $ScriptPath" -ForegroundColor Gray
        Write-Host ""
        return $true
    }
    else {
        Write-Host "❌ 자동 재개 시스템 미등록" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

if ($Status) {
    Get-TaskStatus
    exit 0
}

# ============================================================
# 2. 등록 해제
# ============================================================
if ($Unregister) {
    Write-Host "🗑️  자동 재개 시스템 등록 해제 중..." -ForegroundColor Yellow
    
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 등록 해제 완료" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  등록된 작업이 없습니다." -ForegroundColor Yellow
    }
    exit 0
}

# ============================================================
# 3. 새로 등록
# ============================================================
if ($Register) {
    Write-Host "📝 자동 재개 시스템 등록 중..." -ForegroundColor Yellow
    Write-Host ""
    
    # 기존 작업 확인
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "⚠️  기존 작업이 존재합니다. 먼저 제거합니다..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Action: PowerShell 스크립트 실행
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -Silent"
    
    # Trigger: 사용자 로그온 시
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Settings: 백그라운드 실행
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    
    # Principal: 현재 사용자 권한
    $Principal = New-ScheduledTaskPrincipal `
        -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
        -LogonType Interactive `
        -RunLevel Limited
    
    # Task 등록
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "AGI Phase 2.5 자동 재개: 로그온 시 자동으로 작업 계속" | Out-Null
    
    Write-Host "✅ 등록 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  🎉 완전 자동화 시스템 활성화됨!                         ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 이제부터:" -ForegroundColor Yellow
    Write-Host "   ✅ VS Code 재시작 → 자동 재개" -ForegroundColor Green
    Write-Host "   ✅ PC 재부팅 → 자동 재개" -ForegroundColor Green
    Write-Host "   ✅ 로그아웃/로그인 → 자동 재개" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 수동 확인:" -ForegroundColor Gray
    Write-Host "   - taskschd.msc (작업 스케줄러) 에서 확인 가능" -ForegroundColor Gray
    Write-Host "   - 또는 이 스크립트를 -Status 옵션으로 실행" -ForegroundColor Gray
    Write-Host ""
    
    exit 0
}

# ============================================================
# 기본: 상태 확인
# ============================================================
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI Phase 2.5 자동 재개 시스템 관리                      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$IsRegistered = Get-TaskStatus

Write-Host "사용법:" -ForegroundColor Yellow
Write-Host "   등록:      .\register_auto_resume.ps1 -Register" -ForegroundColor Gray
Write-Host "   해제:      .\register_auto_resume.ps1 -Unregister" -ForegroundColor Gray
Write-Host "   상태확인:  .\register_auto_resume.ps1 -Status" -ForegroundColor Gray
Write-Host ""

if (-not $IsRegistered) {
    Write-Host "💡 추천: -Register 옵션으로 자동 재개를 활성화하세요!" -ForegroundColor Yellow
}
