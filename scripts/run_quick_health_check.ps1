param(
    [int]$TimeoutSeconds = 20,
    [int]$WindowSeconds = 300,
    [switch]$JsonOnly
)

$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

$repo = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $repo 'fdo_agi_repo\scripts\check_health.py'
$venvPy = Join-Path $repo 'fdo_agi_repo\.venv\Scripts\python.exe'
$python = if (Test-Path $venvPy) { $venvPy } else { 'python' }

$env:PYTHONIOENCODING = 'utf-8'
# Build args with hard timeout to guarantee return
$argsList = @("`"$scriptPath`"", '--fast', '--window-seconds', $WindowSeconds, '--max-duration', [string]([math]::Min($TimeoutSeconds, 15)), '--hard-timeout', [string]$TimeoutSeconds)
if ($JsonOnly) { $argsList += '--json-only' }

$job = Start-Job -ScriptBlock {
    param($python, $argsList)
    & $python @argsList 2>&1 | Out-String
} -ArgumentList @($python, $argsList)

$completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
if (-not $completed) {
    Stop-Job -Job $job -Force | Out-Null
    Write-Host 'HEALTH: FAIL (TIMEOUT)' -ForegroundColor Red
    $payload = @{ healthy = $false; reason = 'Timed out'; timeoutSeconds = $TimeoutSeconds; mode = 'fast-wrapper' } | ConvertTo-Json -Depth 5
    $payload
    exit 2
}

$out = Receive-Job -Job $job
Remove-Job -Job $job -Force | Out-Null
$out = $out.Trim()
if ($out) { Write-Output $out }

exit 0
