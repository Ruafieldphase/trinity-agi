# AGI 시스템 통합 중지 스크립트
# ==================================

param(
    [switch]$DashboardOnly,  # 대시보드만 중지
    [switch]$BackendOnly     # 백엔드만 중지
)

Write-Host "🛑 리듬 기반 AGI 시스템 중지" -ForegroundColor Red
Write-Host "=" * 60

# 1. 백엔드 프로세스 중지
if (-not $DashboardOnly) {
    Write-Host "`n🔧 백엔드 프로세스 중지 중..." -ForegroundColor Yellow
    
    $bgProcesses = Get-WmiObject Win32_Process | Where-Object { 
        $_.CommandLine -like '*scripts/linux/*' 
    }
    
    if ($bgProcesses) {
        $count = $bgProcesses.Count
        Write-Host "  🔍 발견: $count 개 프로세스" -ForegroundColor Gray
        
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        
        # 확인
        $remaining = Get-WmiObject Win32_Process | Where-Object { 
            $_.CommandLine -like '*scripts/linux/*' 
        }
        
        if (-not $remaining) {
            Write-Host "  ✅ 백엔드 프로세스 중지 완료" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  일부 프로세스가 남아있을 수 있습니다" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ℹ️  실행 중인 백엔드 프로세스 없음" -ForegroundColor Cyan
    }
}

# 2. 대시보드 중지
if (-not $BackendOnly) {
    Write-Host "`n🎨 대시보드 중지 중..." -ForegroundColor Yellow
    
    $dashboardProcesses = Get-Process node -ErrorAction SilentlyContinue
    
    if ($dashboardProcesses) {
        $count = $dashboardProcesses.Count
        Write-Host "  🔍 발견: $count 개 Node 프로세스" -ForegroundColor Gray
        
        Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        
        Write-Host "  ✅ 대시보드 중지 완료" -ForegroundColor Green
        Write-Host "     (PowerShell 창은 수동으로 닫아주세요)" -ForegroundColor Gray
    } else {
        Write-Host "  ℹ️  실행 중인 대시보드 없음" -ForegroundColor Cyan
    }
}

# 3. Master Daemon 확인
Write-Host "`n📋 Master Daemon 확인..." -ForegroundColor Yellow

$masterDaemon = Get-WmiObject Win32_Process | Where-Object { 
    $_.CommandLine -like '*master_daemon.ps1*' 
}

if ($masterDaemon) {
    Write-Host "  ⚠️  Master Daemon이 실행 중입니다" -ForegroundColor Yellow
    Write-Host "     중지하려면: Stop-Process -Id $($masterDaemon.ProcessId) -Force" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  Master Daemon 미실행" -ForegroundColor Cyan
}

# 4. 최종 상태
Write-Host "`n" + "=" * 60
Write-Host "📊 중지 완료 - 현재 상태:" -ForegroundColor Cyan

Start-Sleep -Seconds 1

$remaining = @()

$bgCount = (Get-WmiObject Win32_Process | Where-Object { 
    $_.CommandLine -like '*scripts/linux/*' 
}).Count

$dashCount = (Get-Process node -ErrorAction SilentlyContinue).Count

Write-Host "  백그라운드 프로세스: $bgCount 개"
Write-Host "  대시보드 프로세스: $dashCount 개"

if ($bgCount -eq 0 -and $dashCount -eq 0) {
    Write-Host "`n✅ 모든 프로세스가 정상적으로 중지되었습니다" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  일부 프로세스가 아직 실행 중입니다" -ForegroundColor Yellow
}

Write-Host "`n🚀 시스템 재시작: .\scripts\start_agi_system.ps1" -ForegroundColor Cyan
Write-Host "`n" + "=" * 60