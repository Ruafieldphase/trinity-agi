# AGI 시스템 완전히 숨겨서 실행 (개선된 버전)
# CreateNoWindow = true 사용

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🔇 AGI 시스템을 백그라운드로 시작합니다..." -ForegroundColor Cyan

# Python 경로
$pythonw = "C:\Python313\pythonw.exe"
if (-not (Test-Path $pythonw)) {
    $pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
}

Write-Host "   Python: $pythonw" -ForegroundColor Gray

# 작업 디렉토리
$agiRoot = "$WorkspaceRoot"

# Process Start Info를 사용하여 완전히 숨김
function Start-HiddenProcess {
    param(
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory
    )
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    return $process.Id
}

# 1. Rhythm Guardian
Write-Host "   🫀 Rhythm Guardian 시작..." -ForegroundColor Yellow
$pid1 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\rhythm_guardian.py`"" -WorkingDirectory $agiRoot
Start-Sleep -Milliseconds 2000

# 2. Heartbeat
Write-Host "   💓 Heartbeat 시작..." -ForegroundColor Yellow
$pid2 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\start_heartbeat.py`"" -WorkingDirectory $agiRoot
Start-Sleep -Milliseconds 2000

# 3. Rhythm Think
Write-Host "   🧠 Rhythm Think 시작..." -ForegroundColor Yellow
$pid3 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\rhythm_think.py`"" -WorkingDirectory $agiRoot
Start-Sleep -Milliseconds 2000

# 4. Aura Controller
Write-Host "   ✨ Aura Controller 시작..." -ForegroundColor Yellow
$pid4 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\aura_controller.py`"" -WorkingDirectory $agiRoot
Start-Sleep -Milliseconds 2000

# 5. Background Self Bridge
Write-Host "   🌉 Background Self Bridge 시작..." -ForegroundColor Yellow
$pid5 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\background_self_bridge.py`"" -WorkingDirectory $agiRoot
Start-Sleep -Milliseconds 2000

# 6. Autonomous Goal Executor
Write-Host "   🎯 Autonomous Goal Executor 시작..." -ForegroundColor Yellow
$pid6 = Start-HiddenProcess -FilePath $pythonw -Arguments "`"$agiRoot\scripts\autonomous_goal_executor.py`"" -WorkingDirectory $agiRoot

Start-Sleep -Seconds 3

# 실행 확인
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
Write-Host ""
Write-Host "✅ AGI 시스템 시작 완료!" -ForegroundColor Green
Write-Host "   실행 중인 Python 프로세스: $pythonProcesses 개" -ForegroundColor Cyan
Write-Host "   PIDs: $pid1, $pid2, $pid3, $pid4, $pid5, $pid6" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 상태 확인:" -ForegroundColor White
Write-Host "   - Thought Stream: agi\outputs\thought_stream_latest.json" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 중지하려면: .\scripts\stop_agi_silent.ps1" -ForegroundColor Yellow