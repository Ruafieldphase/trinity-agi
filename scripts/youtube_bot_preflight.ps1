# YouTube Bot Preflight Check
# Verifies deps, credentials folder, client secret and token presence. Optionally launches OAuth.
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/youtube_bot_preflight.ps1 [-Interactive]

param(
    [switch]$Interactive
)

$ErrorActionPreference = "Continue"

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Ok($m) { Write-Host $m -ForegroundColor Green }
function Write-Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$credDir = Join-Path $workspace "credentials"
$clientSecret = Join-Path $credDir "client_secret.json"
$tokenFile = Join-Path $credDir "youtube_token.json"

Write-Info "[Preflight] Workspace: $workspace"

# 1) Ensure credentials folder
if (-not (Test-Path $credDir)) {
    New-Item -ItemType Directory -Path $credDir | Out-Null
    Write-Ok "Created credentials directory: $credDir"
}
else {
    Write-Ok "Credentials directory exists: $credDir"
}

# 2) Check Python and deps
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { Write-Err "Python 'py' launcher not found in PATH"; exit 2 }

# Check imports quickly
$imports = @(
    'googleapiclient.discovery',
    'google.oauth2.credentials',
    'google_auth_oauthlib.flow',
    'backoff',
    'dotenv'
)
$missing = @()
foreach ($m in $imports) {
    & py -3 -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$m') else 3)" | Out-Null
    if ($LASTEXITCODE -ne 0) { $missing += $m }
}
if ($missing.Count -gt 0) {
    Write-Warn "Missing packages: $($missing -join ', ')"
    Write-Info "Run: YouTube Bot: Install Deps"
}
else {
    Write-Ok "Python deps OK"
}

# 3) Check client secret
if (-not (Test-Path $clientSecret)) {
    Write-Warn "Missing client secret: $clientSecret"
    Write-Info "Place OAuth client secret JSON here or set GOOGLE_OAUTH_CLIENT_SECRET_FILE"
    $needSecret = $true
}
else {
    Write-Ok "Found client secret: $clientSecret"
}

# 4) Check token
if (-not (Test-Path $tokenFile)) {
    Write-Warn "Missing OAuth token: $tokenFile"
    if (-not $needSecret) {
        if ($Interactive) {
            Write-Info "Launching OAuth setup... (browser will open)"
            & py -3 "$workspace/scripts/youtube_oauth_setup.py"
            exit $LASTEXITCODE
        }
        else {
            Write-Info "Run task: YouTube Bot: OAuth Setup (interactive)"
        }
    }
}
else {
    Write-Ok "Found OAuth token: $tokenFile"
}

Write-Ok "Preflight complete"
exit 0
