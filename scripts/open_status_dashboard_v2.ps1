<#
Open Status Dashboard v2

비노체용 원클릭:
- 로컬 서버(3031)를 보증하고
- 브라우저에서 v2 대시보드를 연다.
#>

param([int]$Port = 3031)

$ErrorActionPreference = 'Continue'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

$static = Join-Path $WorkspaceRoot 'outputs\bridge\status_dashboard_v2_static.html'
if (Test-Path $static) {
    Start-Process $static | Out-Null
    exit 0
}

# fallback: old v2 (server 필요)
$ensure = Join-Path $WorkspaceRoot 'scripts\ensure_rubit_dashboard_server.ps1'
if (Test-Path $ensure) { & $ensure -Port $Port -Silent | Out-Null }
$url = "http://127.0.0.1:$Port/outputs/bridge/status_dashboard_v2.html"
Start-Process $url | Out-Null
