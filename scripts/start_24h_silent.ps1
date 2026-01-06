<#
.SYNOPSIS
    24h Production을 완전히 백그라운드에서 실행 (터미널 방해 없음)

.DESCRIPTION
    3가지 방법 제공:
    1. Windows Task Scheduler (권장) - 완전 독립 실행
    2. Hidden PowerShell Window - 보이지 않는 창에서 실행
    3. Windows Service (고급) - 시스템 서비스로 등록

.PARAMETER Method
    실행 방법 선택
    - 'scheduler' (기본): Task Scheduler 등록
    - 'hidden': 숨김 창으로 실행
    - 'service': Windows Service로 등록

.PARAMETER Register
    Task Scheduler에 등록만 하고 실행은 안함

.EXAMPLE
    .\start_24h_silent.ps1
    # Task Scheduler에 등록하고 즉시 시작

.EXAMPLE
    .\start_24h_silent.ps1 -Method hidden
    # 숨김 창으로 실행

.EXAMPLE
    .\start_24h_silent.ps1 -Register
    # 등록만 하고 실행 안함
#>

[CmdletBinding()]
param(
    [ValidateSet('scheduler', 'hidden', 'service')]
    [string]$Method = 'scheduler',
    
    [switch]$Register
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host $Message -ForegroundColor $Color
}

function Register-TaskScheduler {
    param([bool]$StartNow = $true)
    
    Write-Info "`n=== Windows Task Scheduler 등록 ===" "Cyan"
    
    $taskName = "AGI_24h_Production"
    $scriptPath = Join-Path $WorkspaceRoot "scripts\resume_24h_productions.ps1"
    
    # 기존 Task 제거
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Info "기존 Task 제거 중..." "Yellow"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Task 생성
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
        "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Silent"
    
    # 트리거: 지금 즉시 + 로그온 시
    $triggers = @(
        New-ScheduledTaskTrigger -Once -At (Get-Date)
        New-ScheduledTaskTrigger -AtLogon
    )
    
    # 설정: 백그라운드 실행, 배터리 무시
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -Hidden
    
    # 현재 사용자로 실행
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
    
    # Task 등록
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Description "AGI 24h Production 자동 실행 (백그라운드)" | Out-Null
    
    Write-Info "✅ Task Scheduler 등록 완료" "Green"
    Write-Info "   Task 이름: $taskName" "Gray"
    Write-Info "   실행 계정: $env:USERNAME" "Gray"
    Write-Info "   스타일: 숨김 (Hidden)" "Gray"
    
    if ($StartNow) {
        Write-Info "`n🚀 Task 시작 중..." "Cyan"
        Start-ScheduledTask -TaskName $taskName
        Start-Sleep -Seconds 2
        
        $task = Get-ScheduledTask -TaskName $taskName
        Write-Info "   상태: $($task.State)" "White"
    }
    
    Write-Info "`n💡 관리 명령:" "Yellow"
    Write-Info "   상태 확인: Get-ScheduledTask -TaskName '$taskName'" "Gray"
    Write-Info "   시작:     Start-ScheduledTask -TaskName '$taskName'" "Gray"
    Write-Info "   중지:     Stop-ScheduledTask -TaskName '$taskName'" "Gray"
    Write-Info "   제거:     Unregister-ScheduledTask -TaskName '$taskName'" "Gray"
}

function Start-HiddenWindow {
    Write-Info "`n=== 숨김 창으로 실행 ===" "Cyan"
    
    $scriptPath = Join-Path $WorkspaceRoot "scripts\resume_24h_productions.ps1"
    
    # 숨김 창에서 PowerShell 실행
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Silent"
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    
    $process = [System.Diagnostics.Process]::Start($psi)
    
    Write-Info "✅ 백그라운드 프로세스 시작" "Green"
    Write-Info "   PID: $($process.Id)" "Gray"
    Write-Info "   숨김: 예 (보이지 않음)" "Gray"
    
    Write-Info "`n💡 관리 명령:" "Yellow"
    Write-Info "   확인: Get-Process -Id $($process.Id)" "Gray"
    Write-Info "   중지: Stop-Process -Id $($process.Id)" "Gray"
    
    return $process
}

function Register-WindowsService {
    Write-Info "`n=== Windows Service 등록 (고급) ===" "Cyan"
    Write-Info "⚠️  이 기능은 NSSM(Non-Sucking Service Manager) 필요" "Yellow"
    Write-Info "    설치: winget install nssm" "Gray"
    Write-Info ""
    
    # NSSM 설치 확인
    $nssm = Get-Command nssm -ErrorAction SilentlyContinue
    if (-not $nssm) {
        Write-Info "❌ NSSM이 설치되지 않았습니다." "Red"
        Write-Info "   설치 후 다시 시도하세요: winget install nssm" "Yellow"
        return
    }
    
    $serviceName = "AGI_Production_24h"
    $scriptPath = Join-Path $WorkspaceRoot "scripts\resume_24h_productions.ps1"
    
    # 서비스 등록
    & nssm install $serviceName powershell.exe `
        "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Silent"
    
    & nssm set $serviceName AppStdout (Join-Path $WorkspaceRoot "outputs\service_stdout.log")
    & nssm set $serviceName AppStderr (Join-Path $WorkspaceRoot "outputs\service_stderr.log")
    & nssm set $serviceName Start SERVICE_AUTO_START
    
    Write-Info "✅ Windows Service 등록 완료" "Green"
    Write-Info "   서비스명: $serviceName" "Gray"
    Write-Info "   시작: 자동" "Gray"
    
    Write-Info "`n💡 관리 명령:" "Yellow"
    Write-Host "   시작: Start-Service -Name '$serviceName'" -ForegroundColor Gray
    Write-Host "   중지: Stop-Service -Name '$serviceName'" -ForegroundColor Gray
    Write-Host "   제거: nssm remove '$serviceName' confirm" -ForegroundColor Gray
}

# ============================================
# Main Execution
# ============================================

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI 24h Production - 백그라운드 실행 설정    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

switch ($Method) {
    'scheduler' {
        Register-TaskScheduler -StartNow (-not $Register)
    }
    'hidden' {
        if ($Register) {
            Write-Info "⚠️  Hidden 방식은 등록 개념이 없습니다. 즉시 실행합니다." "Yellow"
        }
        Start-HiddenWindow
    }
    'service' {
        Register-WindowsService
    }
}

Write-Info "`n✅ 백그라운드 설정 완료" "Green"
Write-Info "   이제 터미널을 닫아도 Production이 계속 실행됩니다." "White"
Write-Info ""