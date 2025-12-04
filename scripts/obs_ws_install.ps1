# Install obsws-python for OBS WebSocket control
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/obs_ws_install.ps1

param(
    [switch]$UpgradePip
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

try {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        Write-Err "Python launcher 'py' not found. Install Python 3 for Windows and ensure 'py' is in PATH."
        exit 2
    }

    if ($UpgradePip) {
        Write-Info "Upgrading pip (py -3 -m pip install --upgrade pip)"
        py -3 -m pip install --upgrade pip
    }

    Write-Info "Checking obsws-python availability"
    & py -3 -c "import sys; import importlib; sys.exit(0 if importlib.util.find_spec('obsws_python') else 3)"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "obsws-python already installed"
        exit 0
    }

    Write-Info "Installing obsws-python"
    py -3 -m pip install obsws-python

    # Re-check
    & py -3 -c "import obsws_python; print('obsws-python OK')" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "obsws-python import failed after install" }
    Write-Ok "obsws-python installed successfully"
    exit 0
}
catch {
    Write-Err "Install failed: $_"
    exit 2
}
