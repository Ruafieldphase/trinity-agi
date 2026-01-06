#Requires -Version 5.1
param(
    [int]$WindowSeconds = 300,
    [double]$MinEntropy = 2.5,
    [double]$MinCompressionRatio = 1.05,
    [switch]$OpenReport
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$venvPython = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$py = if (Test-Path $venvPython) { $venvPython } else { "python" }
$script = "$WorkspaceRoot\fdo_agi_repo\monitoring\stall_guard.py"

$paths = @()
$candidates = @(
    "$WorkspaceRoot\outputs\results_log.jsonl",
    "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl",
    "$WorkspaceRoot\fdo_agi_repo\outputs\online_learning_log.jsonl"
)
foreach ($p in $candidates) { if (Test-Path $p) { $paths += $p } }

if (-not (Test-Path $script)) { throw "stall_guard.py not found: $script" }
if ($paths.Count -eq 0) { Write-Warning "No candidate files to monitor found. Proceeding with URL-only checks." }

$args = @($script, "--window-seconds", "$WindowSeconds", "--min-entropy", "$MinEntropy", `
        "--min-compression-ratio", "$MinCompressionRatio", `
        "--out-json", "$WorkspaceRoot\outputs\stall_guard_report.json")

if ($paths.Count -gt 0) { $args += @("--paths") + $paths }
$args += @("--urls", "http://127.0.0.1:8091/api/health")

& $py @args
$code = $LASTEXITCODE
Write-Host "StallGuard exit code: $code" -ForegroundColor Cyan
if ($OpenReport) { code "$WorkspaceRoot\outputs\stall_guard_report.json" }
exit $code