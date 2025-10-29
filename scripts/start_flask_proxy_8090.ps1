# Flask ?„ë¡???œë²„ ?œì‘ ?¤í¬ë¦½íŠ¸ (?¬íŠ¸ 8090)
param(
    [int]$Port = 8090,
    [string]$LumenUrl = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Flask ?„ë¡???œë²„ ?œì‘ (?¬íŠ¸ $Port)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$pythonPath = "C:\workspace\agi\LLM_Unified\.venv\Scripts\python.exe"
$proxyScript = "C:\workspace\agi\scripts\local_llm_proxy.py"

if (-not (Test-Path $pythonPath)) {
    Write-Host "??Python ?¤í–‰ ?Œì¼??ì°¾ì„ ???†ìŠµ?ˆë‹¤: $pythonPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $proxyScript)) {
    Write-Host "???„ë¡???¤í¬ë¦½íŠ¸ë¥?ì°¾ì„ ???†ìŠµ?ˆë‹¤: $proxyScript" -ForegroundColor Red
    exit 1
}

# ?¬íŠ¸ê°€ ?´ë? ?¬ìš© ì¤‘ì¸ì§€ ?•ì¸
$portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[WARN] ?¬íŠ¸ $Port ?´ë? ?¬ìš© ì¤‘ì…?ˆë‹¤ (PID: $($portInUse.OwningProcess))" -ForegroundColor Yellow
    $answer = Read-Host "ì¢…ë£Œ?˜ê³  ?¤ì‹œ ?œì‘?˜ì‹œê² ìŠµ?ˆê¹Œ? (y/n)"
    if ($answer -eq 'y') {
        Stop-Process -Id $portInUse.OwningProcess -Force
        Start-Sleep -Seconds 2
    }
    else {
        Write-Host "??ì·¨ì†Œ?˜ì—ˆ?µë‹ˆ?? -ForegroundColor Red
        exit 1
    }
}

Write-Host "?¬íŠ¸: $Port" -ForegroundColor Yellow
Write-Host "?¬ì›Œ?? $LumenUrl" -ForegroundColor Yellow
Write-Host ""

# ?˜ê²½ë³€???¤ì •
$env:LUMEN_GATEWAY_URL = $LumenUrl
$env:PROXY_PORT = $Port

Write-Host "?„ë¡???œë²„ ?œì‘ ì¤?.." -ForegroundColor Green
Write-Host "ì¢…ë£Œ?˜ë ¤ë©?Ctrl+Cë¥??„ë¥´?¸ìš”" -ForegroundColor Yellow
Write-Host "?¬ìŠ¤ì²´í¬: http://localhost:${Port}/health" -ForegroundColor Cyan
Write-Host "ì±„íŒ… ?”ë“œ?¬ì¸?? http://localhost:${Port}/v1/chat/completions" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonPath $proxyScript
}
catch {
    Write-Host "???„ë¡???œë²„ ?¤í–‰ ì¤??¤ë¥˜ ë°œìƒ: $_" -ForegroundColor Red
    exit 1
}
