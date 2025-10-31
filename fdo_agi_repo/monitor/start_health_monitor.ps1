# AGI Health Monitor 시작 스크립트 (PowerShell)

param(
    [int]$Interval = 60,           # 체크 간격 (초)
    [int]$Duration = $null,        # 실행 시간 (초, 없으면 무한)
    [switch]$NoRecoveryNotify      # 복구 알림 비활성화
)

$ErrorActionPreference = "Stop"

Write-Host "🏥 AGI Health Monitor 시작..." -ForegroundColor Cyan

# 현재 디렉토리 확인
$MonitorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $MonitorDir

Write-Host "📁 Monitor Directory: $MonitorDir" -ForegroundColor Gray
Write-Host "📁 Repo Root: $RepoRoot" -ForegroundColor Gray

# Slack 웹훅 URL 확인
if (-not $env:SLACK_WEBHOOK_URL) {
    Write-Host ""
    Write-Host "[WARN]  경고: SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다." -ForegroundColor Yellow
    Write-Host "   Slack 알림이 비활성화됩니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   설정 방법:" -ForegroundColor Gray
    Write-Host '   $env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"' -ForegroundColor Gray
    Write-Host ""

    $continue = Read-Host "계속하시겠습니까? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Host "종료합니다." -ForegroundColor Red
        exit 1
    }
}

# Python 가상환경 활성화 (있으면)
$VenvPath = Join-Path $RepoRoot ".venv"
if (Test-Path $VenvPath) {
    Write-Host "🐍 가상환경 활성화: $VenvPath" -ForegroundColor Yellow
    & "$VenvPath\Scripts\Activate.ps1"
} else {
    Write-Host "[WARN]  가상환경 없음. 시스템 Python 사용" -ForegroundColor Yellow
}

# 헬스 모니터 실행
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "🏥 AGI Health Monitor" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "⏱️  체크 간격: $Interval 초" -ForegroundColor Cyan
if ($Duration) {
    Write-Host "[WAIT] 실행 시간: $Duration 초 ($([math]::Round($Duration/60, 1)) 분)" -ForegroundColor Cyan
} else {
    Write-Host "[WAIT] 실행 시간: 무한 (Ctrl+C로 종료)" -ForegroundColor Cyan
}
Write-Host "🔔 복구 알림: $(if ($NoRecoveryNotify) {'비활성'} else {'활성'})" -ForegroundColor Cyan
Write-Host ""

# health_monitor.py 실행
Set-Location $MonitorDir

$args = @("health_monitor.py", "--interval", $Interval)
if ($Duration) {
    $args += @("--duration", $Duration)
}
if ($NoRecoveryNotify) {
    $args += @("--no-recovery-notify")
}

python @args
