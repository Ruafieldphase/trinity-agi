<#
.SYNOPSIS
  Stop Local LLM Proxy using proxy_info.json
#>

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $root
$infoPath = Join-Path $repoRoot 'fdo_agi_repo\outputs\proxy_info.json'

if (-not (Test-Path $infoPath)) { Write-Host "[WARN]  proxy_info.json not found: $infoPath" -ForegroundColor Yellow; exit 0 }

try {
    $info = Get-Content $infoPath | ConvertFrom-Json
}
catch {
    Write-Host ("[WARN]  Failed to read {0}: {1}" -f $infoPath, $_) -ForegroundColor Yellow
    exit 1
}

$proxyPid = [int]$info.pid
if ($proxyPid -le 0) { Write-Host "[WARN]  Invalid PID in $infoPath" -ForegroundColor Yellow; exit 1 }

try {
    Get-Process -Id $proxyPid -ErrorAction Stop | Out-Null
    Stop-Process -Id $proxyPid -Force
    Write-Host "[OK] Stopped proxy PID=$proxyPid (Port=$($info.port))" -ForegroundColor Green
}
catch {
    Write-Host "ℹ️  Process PID=$proxyPid not running." -ForegroundColor Gray
}
