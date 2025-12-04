# ë¡œì»¬ LLM ?„ë¡???œì‘ ?¤í¬ë¦½íŠ¸
param(
    [int]$Port = 8080,
    [string]$LumenUrl = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"
)

$ErrorActionPreference = "Stop"

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "ë¡œì»¬ LLM ?„ë¡???œë²„ ?œì‘" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

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

Write-Host "?¬íŠ¸: $Port" -ForegroundColor Yellow
Write-Host "?¬ì›Œ?? $LumenUrl" -ForegroundColor Yellow
Write-Host ""

# ?˜ê²½ë³€???¤ì •
$env:LUMEN_GATEWAY_URL = $LumenUrl
$env:PROXY_PORT = $Port

Write-Host "?„ë¡???œë²„ ?œì‘ ì¤?.." -ForegroundColor Green
Write-Host "ì¢…ë£Œ?˜ë ¤ë©?Ctrl+Cë¥??„ë¥´?¸ìš”" -ForegroundColor Yellow
Write-Host ""

try {
    & $pythonPath $proxyScript
}
catch {
    Write-Host "???„ë¡???œë²„ ?¤í–‰ ì¤??¤ë¥˜ ë°œìƒ: $_" -ForegroundColor Red
    exit 1
}
