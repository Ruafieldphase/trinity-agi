param(
    [int]$TimeoutSec = 10,
    [switch]$Fast,
    [switch]$JsonOnly,
    [double]$MaxDuration = 8
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

# Workspace root (SSOT)

# Resolve python
$agiRepo = Join-Path $WorkspaceRoot 'fdo_agi_repo'
$venvPy = Join-Path $agiRepo '.venv\Scripts\python.exe'
$py = if (Test-Path $venvPy) { $venvPy } else { 'python' }

# Build args
$scriptPath = Join-Path $agiRepo 'scripts\check_health.py'
if (-not (Test-Path $scriptPath)) {
    Write-Host "check_health.py not found: $scriptPath" -ForegroundColor Red
    exit 2
}

$argsList = @()
$argsList += @("`"$scriptPath`"")
if ($JsonOnly.IsPresent) { $argsList += '--json-only' }
if ($Fast.IsPresent) { $argsList += '--fast' }
if ($MaxDuration -lt 1) { $MaxDuration = 1 }
$argsList += @('--max-duration', [string]::Format('{0:0.##}', $MaxDuration))
# Use same timeout for hard-timeout to guarantee return regardless of internal hangs
$argsList += @('--hard-timeout', [string]$TimeoutSec)

# Use Start-Process with redirection to temp files for robust capture
$tmpBase = "quick_health_$(Get-Date -Format 'yyyyMMdd_HHmmss_ffff')"
$tmpOut = Join-Path ([System.IO.Path]::GetTempPath()) ("$tmpBase.out")
$tmpErr = Join-Path ([System.IO.Path]::GetTempPath()) ("$tmpBase.err")

$proc = Start-Process -FilePath $py -ArgumentList ($argsList -join ' ') -PassThru -NoNewWindow -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr

$timedOut = $false
try {
    Wait-Process -Id $proc.Id -Timeout $TimeoutSec -ErrorAction SilentlyContinue
    if (-not $proc.HasExited) {
        $timedOut = $true
        try { Stop-Process -Id $proc.Id -Force } catch {}
    }
}
catch {
    $timedOut = $true
    try { Stop-Process -Id $proc.Id -Force } catch {}
}

if ($timedOut) {
    $payload = @{ healthy = $false; checks = @{ timeout = $true }; reason = "Process exceeded ${TimeoutSec}s"; mode = 'wrapper'; timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() } | ConvertTo-Json -Depth 6
    Write-Output $payload
    exit 2
}

$exitCode = $proc.ExitCode
if (Test-Path $tmpOut) { Get-Content -LiteralPath $tmpOut | Write-Output }
if (Test-Path $tmpErr) { Get-Content -LiteralPath $tmpErr | Write-Output }

Remove-Item -LiteralPath $tmpOut -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $tmpErr -ErrorAction SilentlyContinue

exit $exitCode