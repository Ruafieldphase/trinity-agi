# 빠른 ?결 진단 ?크립트
param(
    [switch]$StartProxy,
    [switch]$StopProxy
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

$proxyPort = 8080
$pythonPath = "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe"
$testScript = "$WorkspaceRoot\test_core_connection.py"
$proxyScript = "$WorkspaceRoot\scripts\start_local_llm_proxy.ps1"

function Get-ProxyStatus {
    $connection = Get-NetTCPConnection -LocalPort $proxyPort -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "??로컬 ?록???행 ?(PID: $($connection.OwningProcess))" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "??로컬 ?록??중??? -ForegroundColor Yellow
        return $false
    }
}

if ($StopProxy) {
    Write-Host "?록??중? ?.." -ForegroundColor Yellow
    $connection = Get-NetTCPConnection -LocalPort $proxyPort -ErrorAction SilentlyContinue
    if ($connection) {
        Stop-Process -Id $connection.OwningProcess -Force
        Write-Host "???록??중??? -ForegroundColor Green
    }
    exit 0
}

if ($StartProxy) {
    Write-Host "?록???작 ?.." -ForegroundColor Yellow
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
Write-Host "Core ?이브리???스??빠른 진단" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# ?록???태 ?인
$proxyRunning = Get-ProxyStatus

if (-not $proxyRunning) {
    Write-Host "?록?? ?동?로 ?작?니??.." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $proxyScript -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "진단 ?행 ?.." -ForegroundColor Yellow
Write-Host ""

# ?경변???정 ?진단 ?행
$env:CORE_GATEWAY_URL = "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat"

& $pythonPath $testScript

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "진단 ?료" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan