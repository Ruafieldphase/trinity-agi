#requires -Version 5.1
<#
.SYNOPSIS
Post-reboot verification + auto-fix wrapper.

.DESCRIPTION
Invokes `check_system_after_restart.ps1 -AutoFix` then creates a condensed
Markdown + JSON report for quick scanning. Designed for an AtLogon scheduled
task to validate recovery and surface next actions early.

Artifacts:
  outputs/post_reboot_verify_latest.md
  outputs/post_reboot_verify_latest.json

Exit code mirrors underlying script (non-zero if errors encountered).
#>
param(
    [switch]$OpenMd,
    [string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) = "${PSScriptRoot}/.."
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Continue'
function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }

$root = Resolve-Path $WorkspaceRoot | Select-Object -ExpandProperty Path
$outputs = Join-Path $root 'outputs'
if (!(Test-Path -LiteralPath $outputs)) { New-Item -ItemType Directory -Path $outputs -Force | Out-Null }

$checkScript = Join-Path $root 'scripts/check_system_after_restart.ps1'
if (!(Test-Path -LiteralPath $checkScript)) { Write-Host "Missing check script: $checkScript" -ForegroundColor Red; exit 1 }

Info "Running system restart verification (auto-fix enabled)"
& $checkScript -WorkspaceRoot $root -AutoFix -Verbose 2>&1 | Tee-Object -Variable fullOutput | Out-Null
$exitCode = $LASTEXITCODE
Info "Underlying exit code: $exitCode"

# Basic parsing (health percentage extraction)
$healthLine = ($fullOutput | Where-Object { $_ -match '통과:' }) | Select-Object -First 1
$statusLine = ($fullOutput | Where-Object { $_ -match '시스템 상태:' }) | Select-Object -First 1

$jsonObj = [ordered]@{
    timestamp    = (Get-Date).ToString('s')
    exit_code    = $exitCode
    status_line  = $statusLine
    summary_line = $healthLine
    degraded     = ($exitCode -ne 0)
}
($jsonObj | ConvertTo-Json -Depth 4) | Out-File -LiteralPath (Join-Path $outputs 'post_reboot_verify_latest.json') -Encoding UTF8

$md = @()
$md += '# Post-Reboot Verification'
$md += "- Timestamp: $($jsonObj.timestamp)"
$md += "- Exit Code: $exitCode"
if ($statusLine) { $md += "- Status: $statusLine" }
if ($healthLine) { $md += "- Summary: $healthLine" }
$md += ''
$md += '## Raw Tail'
$tail = $fullOutput | Select-Object -Last 40
$md += '```'
$md += $tail
$md += '```'
$mdText = $md -join "`r`n"
$mdPath = Join-Path $outputs 'post_reboot_verify_latest.md'
$mdText | Out-File -LiteralPath $mdPath -Encoding UTF8
Info "Report written: $mdPath"
if ($OpenMd) { try { Start-Process code $mdPath } catch {} }
exit $exitCode