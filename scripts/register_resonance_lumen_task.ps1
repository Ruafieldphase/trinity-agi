# Resonance Loop + 루멘 자동화 등록 스크립트
# 일일 자동 분석을 예약합니다

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "03:30",
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$TaskName = "AGI_ResonanceLumenIntegration"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Status 체크
if ($Status -or (-not $Register -and -not $Unregister)) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    Write-Host "`n📋 Resonance Loop + 루멘 자동화 상태`n" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
    
    if ($task) {
        Write-Host "✅ 작업 등록됨" -ForegroundColor Green
        Write-Host "   이름: $TaskName" -ForegroundColor Gray
        Write-Host "   상태: $($task.State)" -ForegroundColor Gray
        
        $trigger = $task.Triggers | Select-Object -First 1
        if ($trigger) {
            Write-Host "   트리거: 매일 $($trigger.StartBoundary.ToString('HH:mm'))" -ForegroundColor Gray
        }
        
        $lastRun = (Get-ScheduledTaskInfo -TaskName $TaskName).LastRunTime
        if ($lastRun -gt (Get-Date).AddYears(-10)) {
            Write-Host "   마지막 실행: $lastRun" -ForegroundColor Gray
        }
        else {
            Write-Host "   마지막 실행: 없음" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ 작업 등록 안 됨" -ForegroundColor Red
        Write-Host "`n   등록 명령: .\register_resonance_lumen_task.ps1 -Register`n" -ForegroundColor Yellow
    }
    
    Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
    exit 0
}

# Unregister
if ($Unregister) {
    Write-Host "`n🗑️ Resonance Loop + 루멘 자동화 제거`n" -ForegroundColor Yellow
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 작업 제거 완료`n" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ 등록된 작업이 없습니다`n" -ForegroundColor Yellow
    }
    
    exit 0
}

# Register
if ($Register) {
    Write-Host "`n📅 Resonance Loop + 루멘 자동화 등록`n" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
    
    # 기존 작업 제거
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "🗑️ 기존 작업 제거 중..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 스크립트 경로
    $scriptPath = Join-Path $WorkspaceRoot "scripts\run_resonance_lumen_integration.ps1"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ 스크립트를 찾을 수 없습니다: $scriptPath`n" -ForegroundColor Red
        exit 1
    }
    
    # Action 정의
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    
    # Trigger 정의 (매일 지정 시간)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    
    # Principal 정의 (최고 권한으로 실행)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Highest
    
    # Settings 정의
    $settings = New-ScheduledTaskSettingsSet `
$settings.Hidden = $true
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable
    
    # 작업 등록
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "AGI Resonance Loop + 루멘 통합 자동 분석" | Out-Null
    
    Write-Host "✅ 자동화 등록 완료!`n" -ForegroundColor Green
    Write-Host "작업 이름: $TaskName" -ForegroundColor Gray
    Write-Host "실행 시간: 매일 $Time" -ForegroundColor Gray
    Write-Host "스크립트: $scriptPath`n" -ForegroundColor Gray
    
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
    Write-Host "💡 다음 명령으로 상태 확인:`n" -ForegroundColor Yellow
    Write-Host "   .\register_resonance_lumen_task.ps1`n" -ForegroundColor Cyan
}
