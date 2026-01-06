# Flask ?록???버 ?작 ?크립트 (?트 8090)
param(
    [int]$Port = 8090,
    [string]$CoreUrl = "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Flask ?록???버 ?작 (?트 $Port)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$pythonPath = "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
$proxyScript = "$WorkspaceRoot\scripts\local_llm_proxy.py"

if (-not (Test-Path $pythonPath)) {
    Write-Host "??Python ?행 ?일??찾을 ???습?다: $pythonPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $proxyScript)) {
    Write-Host "???록???크립트?찾을 ???습?다: $proxyScript" -ForegroundColor Red
    exit 1
}

# ?트가 ?? ?용 중인지 ?인
$portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[WARN] ?트 $Port ?? ?용 중입?다 (PID: $($portInUse.OwningProcess))" -ForegroundColor Yellow
    $answer = Read-Host "종료?고 ?시 ?작?시겠습?까? (y/n)"
    if ($answer -eq 'y') {
        Stop-Process -Id $portInUse.OwningProcess -Force
        Start-Sleep -Seconds 2
    }
    else {
        Write-Host "??취소?었?니?? -ForegroundColor Red
        exit 1
    }
}

Write-Host "?트: $Port" -ForegroundColor Yellow
Write-Host "?워?? $CoreUrl" -ForegroundColor Yellow
Write-Host ""

# ?경변???정
$env:CORE_GATEWAY_URL = $CoreUrl
$env:PROXY_PORT = $Port

Write-Host "?록???버 ?작 ?.." -ForegroundColor Green
Write-Host "종료?려?Ctrl+C??르?요" -ForegroundColor Yellow
Write-Host "?스체크: http://localhost:${Port}/health" -ForegroundColor Cyan
Write-Host "채팅 ?드?인?? http://localhost:${Port}/v1/chat/completions" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonPath $proxyScript
}
catch {
    Write-Host "???록???버 ?행 ??류 발생: $_" -ForegroundColor Red
    exit 1
}