. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

# check_autonomous_goal_loop_status.ps1
# Check status of adaptive rhythm autonomous goal execution loop

$ErrorActionPreference = "Stop"

Write-Host "🔍 적응형 리듬 자율 목표 루프 상태 확인..." -ForegroundColor Cyan

# Find daemon processes
$processes = Get-Process -Name "python", "pwsh", "powershell" -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like '*autonomous_goal_loop_daemon.ps1*' }

if ($processes) {
    Write-Host "✅ 적응형 리듬 루프 실행 중" -ForegroundColor Green
    Write-Host ""
    foreach ($proc in $processes) {
        Write-Host "   Process ID: $($proc.Id)" -ForegroundColor Cyan
        Write-Host "   CPU Time:   $($proc.CPU)" -ForegroundColor Cyan
        Write-Host "   Memory:     $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Cyan
        Write-Host "   Start Time: $($proc.StartTime)" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Check rhythm state
    $rhythmPath = Join-Path $WorkspaceRoot "outputs\rhythm_state.json"
    if (Test-Path $rhythmPath) {
        $rhythmState = Get-Content $rhythmPath -Raw | ConvertFrom-Json
        Write-Host "🎵 현재 리듬 상태:" -ForegroundColor Yellow
        Write-Host "   마지막 실행: $($rhythmState.last_execution)" -ForegroundColor Gray
        Write-Host "   연속 성공: $($rhythmState.consecutive_successes)" -ForegroundColor Green
        Write-Host "   연속 실패: $($rhythmState.consecutive_failures)" -ForegroundColor Red
        Write-Host "   최근 간격: $($rhythmState.last_interval) 분" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Calculate next rhythm
    $workspaceRoot = Split-Path $PSScriptRoot -Parent
    $pythonExe = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }
    
    $rhythmCalc = Join-Path $workspaceRoot "scripts\adaptive_rhythm_calculator.py"
    if (Test-Path $rhythmCalc) {
        Write-Host "🎯 다음 실행 예측:" -ForegroundColor Yellow
        $rhythmJson = & $pythonExe $rhythmCalc 2>&1 | Out-String
        try {
            $rhythm = $rhythmJson | ConvertFrom-Json
            Write-Host "   간격: $($rhythm.next_interval_minutes) 분" -ForegroundColor Cyan
            Write-Host "   예정: $($rhythm.next_execution_time)" -ForegroundColor Cyan
            Write-Host ""
        }
        catch {
            Write-Host "   (리듬 계산 실패)" -ForegroundColor Red
        }
    }
    
    # Check tracker file
    $trackerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\goal_tracker.json"
    if (Test-Path $trackerPath) {
        $tracker = Get-Content $trackerPath -Raw | ConvertFrom-Json
        $completed = ($tracker.goals | Where-Object { $_.status -eq "completed" }).Count
        $total = $tracker.goals.Count
        Write-Host "📊 목표 추적:" -ForegroundColor Yellow
        Write-Host "   완료: $completed/$total" -ForegroundColor Green
        Write-Host "   최근 업데이트: $($tracker.last_updated)" -ForegroundColor Gray
    }
}
else {
    Write-Host "❌ 적응형 리듬 루프가 실행 중이지 않습니다" -ForegroundColor Red
    Write-Host ""
    Write-Host "시작하려면: .\scripts\start_autonomous_goal_loop.ps1" -ForegroundColor Yellow
}