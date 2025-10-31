param(
    [switch] $Install,
    [switch] $Uninstall,
    [switch] $Show
)

$ErrorActionPreference = 'Stop'
trap [System.Exception] {
    Write-Err "[ERROR] $_"
    exit 1
}

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Ok($m) { Write-Host $m -ForegroundColor Green }
function Write-Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

$profilePath = $PROFILE
$profileDir = Split-Path -Parent $profilePath
$markerBegin = '# >>> UTF8 PROFILE START (auto-installed)'
$markerEnd = '# <<< UTF8 PROFILE END'
$utf8Block = @'
# >>> UTF8 PROFILE START (auto-installed)
# Ensure UTF-8 for this PowerShell session
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { chcp 65001 | Out-Null } catch {}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:LANG = 'en_US.UTF-8'
# <<< UTF8 PROFILE END
'@

if ($Show) {
    Write-Info "PowerShell profile: $profilePath"
    if (Test-Path $profilePath) { Get-Content $profilePath -Raw | Write-Host } else { Write-Warn 'Profile not found.' }
    exit 0
}

if ($Uninstall) {
    if (Test-Path $profilePath) {
        $text = Get-Content $profilePath -Raw
        $pattern = [regex]::Escape($markerBegin) + '.*?' + [regex]::Escape($markerEnd)
        $newText = [regex]::Replace($text, $pattern, '', 'Singleline')
        Set-Content -Path $profilePath -Value $newText -Encoding UTF8
        Write-Ok 'UTF-8 block removed from profile.'
    }
    else {
        Write-Warn 'Profile not found; nothing to remove.'
    }
    exit 0
}

if ($Install) {
    if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir | Out-Null }
    $existing = ''
    if (Test-Path $profilePath) { $existing = Get-Content $profilePath -Raw } else { New-Item -ItemType File -Path $profilePath | Out-Null }

    # Cleanup legacy wrong block that used literal $markerBegin/$markerEnd
    if ($existing) {
        $legacyPattern = '(?ms)^\$markerBegin.*?^\$markerEnd\s*'
        $existing = [regex]::Replace($existing, $legacyPattern, '')
    }

    if ($existing -and $existing -match [regex]::Escape($markerBegin)) {
        Write-Info 'UTF-8 block already installed. Updating it.'
        $pattern = [regex]::Escape($markerBegin) + '.*?' + [regex]::Escape($markerEnd)
        $updated = [regex]::Replace($existing, $pattern, $utf8Block, 'Singleline')
        Set-Content -Path $profilePath -Value $updated -Encoding UTF8
    }
    else {
        Add-Content -Path $profilePath -Value "`n$utf8Block`n" -Encoding UTF8
    }
    Write-Ok "UTF-8 block ensured in profile: $profilePath"

    # Apply to current session too
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
    try { chcp 65001 | Out-Null } catch {}
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'
    $env:LANG = 'en_US.UTF-8'
    Write-Ok 'Applied UTF-8 to current session.'
    exit 0
}

Write-Info "Usage: ./setup_utf8_profile.ps1 -Install | -Uninstall | -Show"
exit 0