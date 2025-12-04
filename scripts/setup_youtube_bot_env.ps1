# Setup dependencies for YouTube Live Auto-Reply Bot
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_youtube_bot_env.ps1

param(
    [switch]$UpgradePip,
    [switch]$UseRepoVenv
)

$ErrorActionPreference = "Stop"

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Ok($m) { Write-Host $m -ForegroundColor Green }
function Write-Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

# Detect python
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyLauncher) {
    Write-Err "Python launcher 'py' not found in PATH. Install Python 3 for Windows."
    exit 2
}

# Prefer workspace .venv if present and UseRepoVenv not explicitly false
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$repoVenvPython = Join-Path $workspace ".venv/Scripts/python.exe"
$pythonExe = $null
if ((Test-Path $repoVenvPython) -and (-not $PSBoundParameters.ContainsKey('UseRepoVenv') -or $UseRepoVenv)) {
    $pythonExe = $repoVenvPython
    Write-Info "Using repo venv: $repoVenvPython"
}
else {
    $pythonExe = "py -3"
    Write-Info "Using system Python via 'py -3'"
}

# Helper to run pip
function PipInstall([string]$pkg) {
    if ($pythonExe -eq "py -3") {
        & py -3 -m pip install $pkg
    }
    else {
        & $pythonExe -m pip install $pkg
    }
}

try {
    if ($UpgradePip) {
        Write-Info "Upgrading pip"
        if ($pythonExe -eq "py -3") { py -3 -m pip install --upgrade pip } else { & $pythonExe -m pip install --upgrade pip }
    }

    Write-Info "Installing base packages for YouTube + AI"
    PipInstall "google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    PipInstall "python-dotenv backoff"
    # AI backends (optional): OpenAI and Gemini
    PipInstall "openai"
    PipInstall "google-generativeai"

    Write-Ok "Dependencies installed"
    exit 0
}
catch {
    Write-Err "Dependency install failed: $_"
    exit 2
}
