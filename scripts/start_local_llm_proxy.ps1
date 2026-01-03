# ARI Engine (Local LLM) 시작 스크립트 (UTF-8 BOM)
param(
    [int]$Port = 8080,
    [string]$CoreUrl = "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ARI Engine (Local LLM) 시작" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$pythonPath = Join-Path $WorkspaceRoot ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\pythonw.exe"
}
if (-not (Test-Path $pythonPath)) {
    $pythonPath = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
}
$proxyScript = Join-Path $WorkspaceRoot "scripts\local_llm_proxy.py"

if (-not (Test-Path $pythonPath)) {
    Write-Host "실행용 Python을 찾을 수 없습니다: $pythonPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $proxyScript)) {
    Write-Host "프록시 스크립트를 찾을 수 없습니다: $proxyScript" -ForegroundColor Red
    exit 1
}

Write-Host "포트: $Port" -ForegroundColor Yellow
Write-Host "게이트웨이: $CoreUrl" -ForegroundColor Yellow

# 환경변수 설정
$env:CORE_GATEWAY_URL = $CoreUrl
$env:PROXY_PORT = $Port

Write-Host "ARI Engine (Local LLM)을 백그라운드에서 실행합니다..." -ForegroundColor Green

try {
    Start-Process -FilePath $pythonPath -ArgumentList @($proxyScript) -WorkingDirectory $WorkspaceRoot -WindowStyle Hidden
    Write-Host "성공적으로 시작되었습니다. (창은 보이지 않습니다)" -ForegroundColor Cyan
}
catch {
    Write-Host "실행 중 오류 발생: $_" -ForegroundColor Red
    exit 1
}
