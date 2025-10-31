#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 봇의 현재 상태를 확인합니다.

.DESCRIPTION
    봇 서버와 터널의 실행 상태, PID, Public URL 등을 확인합니다.

.EXAMPLE
    .\check_bot_status.ps1
#>

$ErrorActionPreference = "Stop"

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUTPUTS_DIR = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\outputs"
$STATE_FILE = Join-Path $OUTPUTS_DIR "gitco_bot_state.json"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           깃코 슬랙 봇 - 상태 확인                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 상태 파일 확인
if (-not (Test-Path $STATE_FILE)) {
    Write-Host "[ERROR] 봇이 실행되지 않았거나 상태 파일이 없습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "시작 방법: .\scripts\start_gitco_bot.ps1" -ForegroundColor Yellow
    exit 1
}

$state = Get-Content $STATE_FILE | ConvertFrom-Json

Write-Host "[METRICS] 상태 정보:" -ForegroundColor Yellow
Write-Host "  • 시작 시간: $($state.started_at)" -ForegroundColor White

# 봇 프로세스 확인
$botRunning = $false
if ($state.bot_pid) {
    try {
        $botProcess = Get-Process -Id $state.bot_pid -ErrorAction SilentlyContinue
        if ($botProcess) {
            $botRunning = $true
            $uptime = (Get-Date) - $botProcess.StartTime
            Write-Host "  • 봇 서버: [OK] 실행 중 (PID: $($state.bot_pid))" -ForegroundColor Green
            Write-Host "    - 업타임: $([math]::Floor($uptime.TotalHours))시간 $($uptime.Minutes)분" -ForegroundColor Gray
            Write-Host "    - 메모리: $([math]::Round($botProcess.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
        }
    }
    catch {}
}

if (-not $botRunning) {
    Write-Host "  • 봇 서버: [ERROR] 중지됨 (PID: $($state.bot_pid))" -ForegroundColor Red
}

# 터널 프로세스 확인
$tunnelRunning = $false
if ($state.tunnel_pid) {
    try {
        $tunnelProcess = Get-Process -Id $state.tunnel_pid -ErrorAction SilentlyContinue
        if ($tunnelProcess) {
            $tunnelRunning = $true
            Write-Host "  • Localtunnel: [OK] 실행 중 (PID: $($state.tunnel_pid))" -ForegroundColor Green
            if ($state.tunnel_url) {
                Write-Host "    - URL: $($state.tunnel_url)" -ForegroundColor Cyan
            }
        }
    }
    catch {}
}

if (-not $tunnelRunning) {
    Write-Host "  • Localtunnel: [ERROR] 중지됨 (PID: $($state.tunnel_pid))" -ForegroundColor Red
}

Write-Host ""

# 헬스 체크
if ($botRunning) {
    Write-Host "[SEARCH] 헬스 체크 중..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  • 봇 API: [OK] 정상 응답" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  • 봇 API: [WARN]  응답 없음" -ForegroundColor Yellow
    }
}

# 로그 파일 정보
if ($state.log_dir) {
    Write-Host ""
    Write-Host "📄 로그 파일:" -ForegroundColor Yellow
    if (Test-Path $state.bot_log) {
        $botLogSize = [math]::Round((Get-Item $state.bot_log).Length / 1KB, 2)
        Write-Host "  • 봇: $($state.bot_log)" -ForegroundColor White
        Write-Host "    크기: $botLogSize KB" -ForegroundColor Gray
    }
    if (Test-Path $state.tunnel_log) {
        $tunnelLogSize = [math]::Round((Get-Item $state.tunnel_log).Length / 1KB, 2)
        Write-Host "  • 터널: $($state.tunnel_log)" -ForegroundColor White
        Write-Host "    크기: $tunnelLogSize KB" -ForegroundColor Gray
    }
}

Write-Host ""

# 전체 상태 요약
if ($botRunning -and $tunnelRunning) {
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                    [OK] 정상 작동 중                        ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
}
elseif ($botRunning) {
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║            [WARN]  봇 실행 중, 터널 중지됨                    ║" -ForegroundColor Yellow
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host "재시작: .\scripts\start_gitco_bot.ps1 -KillExisting" -ForegroundColor Gray
}
else {
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                    [ERROR] 봇 중지됨                           ║" -ForegroundColor Red
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host "시작: .\scripts\start_gitco_bot.ps1" -ForegroundColor Gray
}

Write-Host ""

# 관리 명령어 안내
Write-Host "[CONFIG] 관리 명령어:" -ForegroundColor Yellow
Write-Host "  • 로그 보기: .\scripts\show_bot_logs.ps1" -ForegroundColor White
Write-Host "  • 재시작: .\scripts\start_gitco_bot.ps1 -KillExisting" -ForegroundColor White
Write-Host "  • 종료: .\scripts\start_gitco_bot.ps1 -StopOnly" -ForegroundColor White
Write-Host ""
