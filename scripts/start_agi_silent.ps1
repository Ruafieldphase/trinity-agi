# AGI 시스템 조용히 백그라운드 실행
# 윈도우 팝업 없이 실행됩니다

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🔇 AGI 시스템을 백그라운드로 시작합니다..." -ForegroundColor Cyan

# Python 경로 찾기
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    $pythonw = "C:\Python313\pythonw.exe"
}

Write-Host "   Python: $pythonw" -ForegroundColor Gray

# 작업 디렉토리
$agiRoot = "C:\workspace\agi"
Set-Location $agiRoot

# 1. Rhythm Guardian 시작 (단일 심장)
Write-Host "   🫀 Rhythm Guardian 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\rhythm_guardian.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 2

# 2. Heartbeat Loop 시작
Write-Host "   💓 Heartbeat Loop 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\start_heartbeat.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 2

# 3. Rhythm Think (Brain) 시작
Write-Host "   🧠 Rhythm Think 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\rhythm_think.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 2

# 4. Aura Controller 시작
Write-Host "   ✨ Aura Controller 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\aura_controller.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 2

# 5. Background Self Bridge 시작
Write-Host "   🌉 Background Self Bridge 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\background_self_bridge.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 2

# 6. Autonomous Goal Executor 시작
Write-Host "   🎯 Autonomous Goal Executor 시작..." -ForegroundColor Yellow
Start-Process -FilePath $pythonw -ArgumentList "scripts\autonomous_goal_executor.py" -WindowStyle Hidden -WorkingDirectory $agiRoot

Start-Sleep -Seconds 3

# 실행 확인
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
Write-Host ""
Write-Host "✅ AGI 시스템 시작 완료!" -ForegroundColor Green
Write-Host "   실행 중인 Python 프로세스: $pythonProcesses 개" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 상태 확인:" -ForegroundColor White
Write-Host "   - Thought Stream: agi\outputs\thought_stream_latest.json" -ForegroundColor Gray
Write-Host "   - Guardian Log: agi\logs\rhythm_guardian.log" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 중지하려면: .\scripts\stop_agi_silent.ps1" -ForegroundColor Yellow
