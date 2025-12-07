# AGI 시스템 통합 시작 스크립트
# ==================================

param(
    [switch]$DashboardOnly,  # 대시보드만 시작
    [switch]$BackendOnly,    # 백엔드만 시작
    [switch]$Status          # 상태만 확인
)

Write-Host "🌊 리듬 기반 AGI 시스템 시작" -ForegroundColor Cyan
Write-Host "=" * 60

# 상태 확인만 하는 경우
if ($Status) {
    & "$PSScriptRoot\check_system_status.ps1"
    exit
}

# 작업 디렉토리 확인
$agiRoot = Split-Path -Parent $PSScriptRoot
Set-Location $agiRoot

Write-Host "`n📍 작업 디렉토리: $agiRoot" -ForegroundColor Gray

# 1. 백엔드 프로세스 시작
if (-not $DashboardOnly) {
    Write-Host "`n🔧 백엔드 프로세스 시작 중..." -ForegroundColor Yellow
    
    # 기존 프로세스 정리
    $existingProcesses = Get-WmiObject Win32_Process | Where-Object { 
        $_.CommandLine -like '*scripts/linux/*' 
    }
    
    if ($existingProcesses) {
        Write-Host "  ⚠️  기존 프로세스 발견, 종료 중..." -ForegroundColor Yellow
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Orchestrator Agent 시작
    Write-Host "  ▶️  Orchestrator Agent 시작..." -ForegroundColor Cyan
    Start-Process -FilePath "C:\Python313\python.exe" `
                  -ArgumentList "scripts/linux/orchestrator_agent.py" `
                  -WorkingDirectory $agiRoot `
                  -NoNewWindow
    
    Start-Sleep -Milliseconds 500
    
    # Background Self Bridge 시작
    Write-Host "  ▶️  Background Self Bridge 시작..." -ForegroundColor Cyan
    Start-Process -FilePath "C:\Python313\python.exe" `
                  -ArgumentList "scripts/linux/background_self_bridge.py" `
                  -WorkingDirectory $agiRoot `
                  -NoNewWindow
    
    Start-Sleep -Seconds 1
    
    # 확인
    $bgProcesses = Get-WmiObject Win32_Process | Where-Object { 
        $_.CommandLine -like '*scripts/linux/*' 
    }
    
    if ($bgProcesses) {
        Write-Host "  ✅ 백엔드 프로세스 시작 완료 ($($bgProcesses.Count)개)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 백엔드 프로세스 시작 실패" -ForegroundColor Red
    }
}

# 2. 대시보드 시작
if (-not $BackendOnly) {
    Write-Host "`n🎨 대시보드 시작 중..." -ForegroundColor Yellow
    
    # 기존 대시보드 프로세스 확인
    $existingDashboard = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -eq 'node'
    }
    
    if ($existingDashboard) {
        Write-Host "  ℹ️  대시보드가 이미 실행 중입니다" -ForegroundColor Cyan
        Write-Host "     URL: http://localhost:3001" -ForegroundColor Gray
    } else {
        Write-Host "  ▶️  대시보드 시작 중... (약 10초 소요)" -ForegroundColor Cyan
        
        $dashboardPath = Join-Path $agiRoot "dashboard"
        
        # 새 PowerShell 창에서 대시보드 시작
        $command = "cd '$dashboardPath'; npm run dev"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
        
        Write-Host "  ✅ 대시보드 시작 명령 실행됨" -ForegroundColor Green
        Write-Host "     대기 중... (브라우저 창 확인)" -ForegroundColor Gray
        
        # 대시보드가 준비될 때까지 대기
        Start-Sleep -Seconds 3
    }
}

# 3. 최종 상태 확인
Write-Host "`n" + "=" * 60
Write-Host "📊 시스템 시작 완료 - 최종 상태:" -ForegroundColor Cyan

Start-Sleep -Seconds 2

& "$PSScriptRoot\check_system_status.ps1"

Write-Host "`n💡 다음 단계:" -ForegroundColor Yellow
Write-Host "  1. 브라우저에서 http://localhost:3001 열기" -ForegroundColor Gray
Write-Host "  2. 바이브 채팅창에서 한국어로 질문하기" -ForegroundColor Gray
Write-Host "  3. AI 응답 확인하기" -ForegroundColor Gray

Write-Host "`n🛑 시스템 중지: .\scripts\stop_agi_system.ps1" -ForegroundColor Yellow
Write-Host "`n" + "=" * 60
