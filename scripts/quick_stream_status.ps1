# Quick Stream Status (safe)
# Summarize OBS WebSocket ping/status and YouTube bot preflight without failing the task
# Always exits with code 0

$ErrorActionPreference = "Continue"

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m) { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Err($m) { Write-Host $m -ForegroundColor Red }

try {
    $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
    $py = Get-Command py -ErrorAction SilentlyContinue
    $obsPing = @{ code = $null; note = $null }
    $obsStat = @{ code = $null; note = $null }
    $ytPre = @{ code = $null; note = $null }

    Info "[OBS] WebSocket ping..."
    if ($py) {
        & py -3 (Join-Path $ws 'scripts/obs_ws_control.py') ping
        $obsPing.code = $LASTEXITCODE
        if ($obsPing.code -ne 0) { $obsPing.note = 'OBS가 꺼져 있거나 WebSocket(4455)이 닫혀 있습니다.'; Warn $obsPing.note } else { Ok 'OBS WS ping OK' }
    }
    else {
        $obsPing.code = 2
        $obsPing.note = "Python 'py' 런처가 필요합니다."
        Warn $obsPing.note
    }

    Info "[OBS] Stream status..."
    if ($py) {
        & py -3 (Join-Path $ws 'scripts/obs_ws_control.py') status
        $obsStat.code = $LASTEXITCODE
        if ($obsStat.code -ne 0) { $obsStat.note = 'OBS 연결이 필요합니다.'; Warn $obsStat.note } else { Ok 'OBS status OK' }
    }
    else {
        $obsStat.code = 2; $obsStat.note = "Python 'py' 런처가 필요합니다."; Warn $obsStat.note
    }

    Info "[YouTube] Bot preflight..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ws 'scripts/youtube_bot_preflight.ps1')
    $ytPre.code = $LASTEXITCODE
    if ($ytPre.code -ne 0) { $ytPre.note = '의존성/자격 증명 준비가 필요할 수 있습니다.'; Warn $ytPre.note } else { Ok 'YouTube bot preflight OK' }

    Write-Host "\nSummary:" -ForegroundColor Cyan
    $summary = [PSCustomObject]@{
        obs_ping_code          = $obsPing.code
        obs_status_code        = $obsStat.code
        youtube_preflight_code = $ytPre.code
    }
    $summary | ConvertTo-Json -Depth 3 | Write-Host

    if ($obsPing.code -ne 0) {
        Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkYellow
        Write-Host "📌 OBS WebSocket 설정 가이드" -ForegroundColor Yellow
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkYellow
        Write-Host "1. OBS Studio를 실행하세요" -ForegroundColor White
        Write-Host "2. 상단 메뉴에서 [Tools] → [WebSocket Server Settings] 선택" -ForegroundColor White
        Write-Host "3. [Enable WebSocket server] 체크박스를 활성화" -ForegroundColor White
        Write-Host "4. Server Port: 4455 (기본값 유지)" -ForegroundColor White
        Write-Host "5. [Show Connect Info] 버튼을 클릭해 연결 정보 확인" -ForegroundColor White
        Write-Host "6. 설정 완료 후 [Apply] → [OK]" -ForegroundColor White
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkYellow
    }
    if ($ytPre.code -ne 0) {
        Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkYellow
        Write-Host "📌 YouTube Bot 온보딩 가이드" -ForegroundColor Yellow
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkYellow
        Write-Host "VS Code에서 다음 태스크를 순서대로 실행하세요:" -ForegroundColor White
        Write-Host "  1. 'YouTube Bot: Install Deps' - 필요한 Python 패키지 설치" -ForegroundColor Cyan
        Write-Host "  2. 'YouTube: Install Client Secret (copy file)' - client_secret.json 등록" -ForegroundColor Cyan
        Write-Host "  3. 'YouTube Bot: Preflight + OAuth (interactive)' - OAuth 인증" -ForegroundColor Cyan
        Write-Host "`n또는 자연어로:" -ForegroundColor White
        Write-Host "  '온보딩 도와줘' 또는 '시크릿 등록해줘'" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkYellow
    }

    $global:LASTEXITCODE = 0
    exit 0
}
catch {
    Warn "요약 중 예외가 발생했지만 작업은 계속됩니다: $_"
    $global:LASTEXITCODE = 0
    exit 0
}