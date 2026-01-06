# Install YouTube OAuth client secret into credentials folder or set as user env var
# Usage examples:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_youtube_client_secret.ps1 -SourceFile "C:\path\client_secret.json"
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_youtube_client_secret.ps1 -SourceFile "C:\path\client_secret.json" -AsEnv

param(
  [Parameter(Mandatory=$true)][string]$SourceFile,
  [switch]$AsEnv,
  [string]$EnvName = 'GOOGLE_OAUTH_CLIENT_SECRET_FILE'
)

$ErrorActionPreference = 'Stop'

function Info($m){ Write-Host $m -ForegroundColor Cyan }
function Ok($m){ Write-Host $m -ForegroundColor Green }
function Warn($m){ Write-Host $m -ForegroundColor Yellow }
function Err($m){ Write-Host $m -ForegroundColor Red }

try {
  $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
  $credDir = Join-Path $ws 'credentials'
  if (-not (Test-Path $credDir)) { New-Item -ItemType Directory -Path $credDir | Out-Null }

  $src = [System.IO.Path]::GetFullPath($SourceFile)
  if (-not (Test-Path $src)) { Err "Source file not found: $src"; exit 2 }

  # Quick JSON sanity check (non-fatal if parsing fails)
  $isValidGoogleJson = $false
  try {
    $json = Get-Content -Raw -LiteralPath $src | ConvertFrom-Json
    if ($json -and ($json.installed -or $json.web)) { $isValidGoogleJson = $true }
  } catch { Warn "Couldn't parse JSON or unknown schema. Proceeding anyway." }

  if ($AsEnv) {
    [System.Environment]::SetEnvironmentVariable($EnvName, $src, 'User')
    Ok "Set user environment variable $EnvName to: $src"
    Info 'Open a new terminal for the env var to take effect.'
    exit 0
  }

  $dst = Join-Path $credDir 'client_secret.json'
  if (Test-Path $dst) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $bak = Join-Path $credDir ("client_secret.json.bak.$ts")
    Copy-Item -LiteralPath $dst -Destination $bak -Force
    Info "Backed up existing client_secret.json -> $bak"
  }

  Copy-Item -LiteralPath $src -Destination $dst -Force
  Ok "Installed client secret to: $dst"
  if (-not $isValidGoogleJson) {
    Warn 'The file was copied, but it did not look like a standard Google OAuth client secret (no installed/web root).'
  }
  exit 0
}
catch {
  Err $_
  exit 1
}