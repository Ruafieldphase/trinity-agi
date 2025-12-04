# Îπ†Î•∏ ?∞Í≤∞ ÏßÑÎã® ?§ÌÅ¨Î¶ΩÌä∏
param(
    [switch]$StartProxy,
    [switch]$StopProxy
)

$ErrorActionPreference = "Stop"

$proxyPort = 8080
$pythonPath = "C:\workspace\agi\LLM_Unified\.venv\Scripts\python.exe"
$testScript = "C:\workspace\agi\test_lumen_connection.py"
$proxyScript = "C:\workspace\agi\scripts\start_local_llm_proxy.ps1"

function Get-ProxyStatus {
    $connection = Get-NetTCPConnection -LocalPort $proxyPort -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "??Î°úÏª¨ ?ÑÎ°ù???§Ìñâ Ï§?(PID: $($connection.OwningProcess))" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "??Î°úÏª¨ ?ÑÎ°ù??Ï§ëÏ??? -ForegroundColor Yellow
        return $false
    }
}

if ($StopProxy) {
    Write-Host "?ÑÎ°ù??Ï§ëÏ? Ï§?.." -ForegroundColor Yellow
    $connection = Get-NetTCPConnection -LocalPort $proxyPort -ErrorAction SilentlyContinue
    if ($connection) {
        Stop-Process -Id $connection.OwningProcess -Force
        Write-Host "???ÑÎ°ù??Ï§ëÏ??? -ForegroundColor Green
    }
    exit 0
}

if ($StartProxy) {
    Write-Host "?ÑÎ°ù???úÏûë Ï§?.." -ForegroundColor Yellow
    $proxyRunning = Get-ProxyStatus
    if (-not $proxyRunning) {
        Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $proxyScript -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Get-ProxyStatus | Out-Null
    }
    exit 0
}

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Î£®Î©ò ?òÏù¥Î∏åÎ¶¨???úÏä§??Îπ†Î•∏ ÏßÑÎã®" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# ?ÑÎ°ù???ÅÌÉú ?ïÏù∏
$proxyRunning = Get-ProxyStatus

if (-not $proxyRunning) {
    Write-Host "?ÑÎ°ù?úÎ? ?êÎèô?ºÎ°ú ?úÏûë?©Îãà??.." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $proxyScript -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "ÏßÑÎã® ?§Ìñâ Ï§?.." -ForegroundColor Yellow
Write-Host ""

# ?òÍ≤ΩÎ≥Ä???§Ï†ï Î∞?ÏßÑÎã® ?§Ìñâ
$env:LUMEN_GATEWAY_URL = "https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat"

& $pythonPath $testScript

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "ÏßÑÎã® ?ÑÎ£å" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
