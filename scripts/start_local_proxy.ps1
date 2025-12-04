<#
.SYNOPSIS
  Start Local LLM Proxy on an available port and record status

.DESCRIPTION
  - Finds a free port in the range [8090..8100] unless -Port specified
  - Starts scripts/local_llm_proxy.py with PROXY_PORT and LUMEN_GATEWAY_URL
  - Writes proxy info to fdo_agi_repo/outputs/proxy_info.json

.PARAMETER Port
  Preferred port. If busy, will search next ports in range.

.PARAMETER GatewayUrl
  Lumen Gateway URL to forward to.

.PARAMETER Background
  Start in background (default: true)
#>
param(
    [int]$Port = 18090,
    [string]$GatewayUrl = $env:LUMEN_GATEWAY_URL,
    [switch]$NoBackground
)

$ErrorActionPreference = 'Stop'

# Paths
$root = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $root
$proxyPy = Join-Path $root 'local_llm_proxy.py'
$outDir = Join-Path $repoRoot 'fdo_agi_repo\outputs'
$infoPath = Join-Path $outDir 'proxy_info.json'

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

if (-not (Test-Path $proxyPy)) {
    Write-Host "[ERROR] local_llm_proxy.py not found: $proxyPy" -ForegroundColor Red
    exit 1
}

if (-not $GatewayUrl) { $GatewayUrl = 'https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat' }

function Test-PortFree([int]$p) {
    $net = netstat -ano | Select-String ":$p"
    return -not $net
}

# Find free port in range [Port .. Port+50]
$chosen = $null
for ($p = $Port; $p -le ($Port + 50); $p++) {
    if (Test-PortFree $p) { $chosen = $p; break }
}
if (-not $chosen) {
    Write-Host "[ERROR] No free port found in range $Port-$($Port+50)" -ForegroundColor Red
    exit 1
}

# Choose Python
$pyCandidates = @(
    'C:\workspace\agi\LLM_Unified\.venv\Scripts\python.exe',
    'C:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe',
    'C:\workspace\agi\.venv\Scripts\python.exe',
    'python'
)
$python = $null
foreach ($c in $pyCandidates) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        # verify flask availability
        & $c -c "import flask" 2>$null; if ($LASTEXITCODE -eq 0) { $python = $c; break }
    }
}
if (-not $python) { Write-Host '[ERROR] No python with Flask found' -ForegroundColor Red; exit 1 }

$env:PROXY_PORT = $chosen
$env:LUMEN_GATEWAY_URL = $GatewayUrl

Write-Host "[START] Starting Local LLM Proxy on port $chosen" -ForegroundColor Cyan
Write-Host "?бя╕П  Forwarding to: $GatewayUrl" -ForegroundColor Cyan

if ($NoBackground) {
    & $python $proxyPy
    exit $LASTEXITCODE
}
else {
    $proc = Start-Process -FilePath $python -ArgumentList @("`"$proxyPy`"") -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 1
    # Write info JSON
    $info = @{ port = $chosen; pid = $proc.Id; started_at = (Get-Date).ToString('s') }
    $info | ConvertTo-Json | Set-Content -Path $infoPath -Encoding UTF8
    Write-Host "[OK] Proxy started. PID=$($proc.Id), info: $infoPath" -ForegroundColor Green
}
