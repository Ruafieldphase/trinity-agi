# 긴급 전체 서비스 중지 스크립트
# =====================================
# 모든 AGI 관련 프로세스를 중지합니다

Write-Host "`n🚨 긴급 전체 서비스 중지" -ForegroundColor Red
Write-Host "=" * 80

# 1. PowerShell 프로세스 중지
Write-Host "`n[1/3] PowerShell 프로세스 중지..." -ForegroundColor Yellow
$psProcesses = Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }
if ($psProcesses) {
    Write-Host "  발견: $($psProcesses.Count)개 프로세스" -ForegroundColor Cyan
    foreach ($proc in $psProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✅ PID $($proc.Id) 중지" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ PID $($proc.Id) 중지 실패" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ℹ️  실행 중인 PowerShell 프로세스 없음" -ForegroundColor Gray
}

# 2. Python 프로세스 중지 (AGI 관련만)
Write-Host "`n[2/3] Python 프로세스 확인 및 중지..." -ForegroundColor Yellow

# AGI 관련 Python 프로세스 패턴
$agiPatterns = @(
    "*consciousness_api.py*",
    "*unconscious_stream.py*",
    "*background_self_api.py*",
    "*unified_aggregator.py*",
    "*fsd_server.py*",
    "*lua_flow_collector.py*",
    "*lymphatic_system.py*",
    "*slack_interface.py*",
    "*core_conscious.py*",
    "*core_mcp_server.py*",
    "*rhythm_think.py*",
    "*monitoring_daemon.py*",
    "*meta_supervisor.py*",
    "*task_queue_server.py*",
    "*rpa_worker.py*",
    "*self_healing_watchdog.py*",
    "*orchestrator_agent.py*",
    "*background_self_bridge.py*"
)

$pythonProcesses = Get-WmiObject Win32_Process | Where-Object {
    $_.Name -like "python*.exe" -or $_.Name -like "pythonw.exe"
}

$stoppedCount = 0
foreach ($proc in $pythonProcesses) {
    $cmdLine = $proc.CommandLine
    if (-not $cmdLine) { continue }

    $shouldStop = $false
    foreach ($pattern in $agiPatterns) {
        if ($cmdLine -like $pattern) {
            $shouldStop = $true
            break
        }
    }

    if ($shouldStop) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            Write-Host "  ✅ Python PID $($proc.ProcessId) 중지: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))..." -ForegroundColor Green
            $stoppedCount++
        } catch {
            Write-Host "  ❌ Python PID $($proc.ProcessId) 중지 실패" -ForegroundColor Red
        }
    }
}

if ($stoppedCount -eq 0) {
    Write-Host "  ℹ️  AGI 관련 Python 프로세스 없음" -ForegroundColor Gray
} else {
    Write-Host "  총 $stoppedCount 개 Python 프로세스 중지" -ForegroundColor Cyan
}

# 3. VBScript/WScript 프로세스 중지
Write-Host "`n[3/3] VBScript 프로세스 확인 및 중지..." -ForegroundColor Yellow
$wscriptProcesses = Get-Process wscript -ErrorAction SilentlyContinue
if ($wscriptProcesses) {
    Write-Host "  발견: $($wscriptProcesses.Count)개 wscript 프로세스" -ForegroundColor Cyan
    foreach ($proc in $wscriptProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "  ✅ wscript PID $($proc.Id) 중지" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ wscript PID $($proc.Id) 중지 실패" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ℹ️  실행 중인 wscript 프로세스 없음" -ForegroundColor Gray
}

# 4. 최종 확인
Write-Host "`n" + "=" * 80
Write-Host "🔍 최종 프로세스 확인..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$remainingPS = Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }
$remainingPython = (Get-Process python* -ErrorAction SilentlyContinue).Count
$remainingWScript = (Get-Process wscript -ErrorAction SilentlyContinue).Count

Write-Host "`n남은 프로세스:" -ForegroundColor Yellow
Write-Host "  PowerShell: $($remainingPS.Count)" -ForegroundColor White
Write-Host "  Python: $remainingPython" -ForegroundColor White
Write-Host "  WScript: $remainingWScript" -ForegroundColor White

if ($remainingPS.Count -eq 0 -and $remainingWScript -eq 0) {
    Write-Host "`n✅ 모든 AGI 서비스가 중지되었습니다!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  일부 프로세스가 아직 실행 중입니다." -ForegroundColor Yellow
    if ($remainingPS.Count -gt 0) {
        Write-Host "`n남은 PowerShell 프로세스:" -ForegroundColor Yellow
        $remainingPS | Select-Object Id, StartTime | Format-Table
    }
}

Write-Host "`n" + "=" * 80
Write-Host ""