# Stop Autonomous Goal Loop
# Sets stop flag to gracefully terminate the running daemon

param(
    [switch]$Remove,
    [switch]$Status,
    [switch]$Force
)

$StopFlag = "C:\workspace\agi\outputs\stop_autonomous_goal_loop.flag"
$StatusFile = "C:\workspace\agi\outputs\autonomous_goal_loop_status.json"

if ($Status) {
    # Show current status
    Write-Host "🔍 자율 목표 루프 상태 확인" -ForegroundColor Cyan
    
    $flagExists = Test-Path -LiteralPath $StopFlag
    if ($flagExists) {
        Write-Host "⏹️  정지 플래그: 존재함 (루프가 곧 종료됩니다)" -ForegroundColor Yellow
    }
    else {
        Write-Host "✅ 정지 플래그: 없음 (루프 실행 중)" -ForegroundColor Green
    }
    
    if (Test-Path -LiteralPath $StatusFile) {
        Write-Host "`n📊 마지막 상태:" -ForegroundColor Cyan
        try {
            $status = Get-Content -LiteralPath $StatusFile -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "  시각: $($status.timestamp)" -ForegroundColor Gray
            Write-Host "  페이즈: $($status.phase)" -ForegroundColor Gray
            Write-Host "  간격: $($status.interval_min) 분" -ForegroundColor Gray
            Write-Host "  실패 횟수: $($status.failure_count)" -ForegroundColor Gray
            Write-Host "  마지막 결과: $($status.last_result)" -ForegroundColor Gray
            Write-Host "  다음 실행: $($status.next_run_local)" -ForegroundColor Gray
        }
        catch {
            Write-Host "  (상태 파일 읽기 실패)" -ForegroundColor Yellow
        }
    }
    
    # Check if process is running
    $processes = Get-Process -Name 'pwsh', 'powershell' -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like '*autonomous_goal_loop_daemon.ps1*' }
    
    if ($processes) {
        Write-Host "`n🔄 실행 중인 프로세스:" -ForegroundColor Green
        $processes | Format-Table Id, ProcessName, CPU, @{Label = 'Memory(MB)'; Expression = { [math]::Round($_.WorkingSet / 1MB, 1) } }
    }
    else {
        Write-Host "`n⚠️  실행 중인 데몬 프로세스 없음" -ForegroundColor Yellow
    }
    
    exit 0
}

if ($Remove) {
    # Remove stop flag
    if (Test-Path -LiteralPath $StopFlag) {
        Remove-Item -LiteralPath $StopFlag -Force
        Write-Host "✅ 정지 플래그 제거됨. 새 루프를 시작할 수 있습니다." -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️  정지 플래그가 이미 없습니다." -ForegroundColor Cyan
    }
    exit 0
}

if ($Force) {
    # Force kill processes (old behavior)
    Write-Host "🛑 강제 종료 모드..." -ForegroundColor Yellow
    
    $processes = Get-Process -Name "python", "pwsh", "powershell" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like '*autonomous_goal_loop*' }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "   프로세스 종료 ID: $($proc.Id)" -ForegroundColor Cyan
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "✅ 강제 종료 완료" -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️  실행 중인 루프 없음" -ForegroundColor Yellow
    }
    
    # Also remove flag
    if (Test-Path -LiteralPath $StopFlag) {
        Remove-Item -LiteralPath $StopFlag -Force
    }
    exit 0
}

# Set stop flag (default, graceful shutdown)
try {
    "stop" | Out-File -FilePath $StopFlag -Encoding UTF8 -Force
    Write-Host "⏹️  정지 플래그 설정 완료" -ForegroundColor Yellow
    Write-Host "   루프가 다음 사이클에 우아하게 종료됩니다." -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 팁:" -ForegroundColor Cyan
    Write-Host "   - 플래그 제거: .\stop_autonomous_goal_loop.ps1 -Remove" -ForegroundColor Gray
    Write-Host "   - 상태 확인: .\stop_autonomous_goal_loop.ps1 -Status" -ForegroundColor Gray
    Write-Host "   - 강제 종료: .\stop_autonomous_goal_loop.ps1 -Force" -ForegroundColor Gray
}
catch {
    Write-Host "❌ 정지 플래그 설정 실패: $_" -ForegroundColor Red
    exit 1
}
