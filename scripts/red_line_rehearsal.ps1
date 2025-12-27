# Purpose: Minimal red-line rehearsal stub (non-destructive).
# - Creates a rehearsal report without enforcing/altering the system.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$policyFile = Join-Path $root "policy\\red_line_monitor.yaml"
$outDir = Join-Path $root "outputs\\safety"
$outFile = Join-Path $outDir "red_line_rehearsal_latest.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$result = [ordered]@{
  ok = $true
  version = "red_line_rehearsal_stub_v1"
  timestamp = (Get-Date).ToUniversalTime().ToString("o")
  policy = @{
    path = $policyFile
    exists = (Test-Path $policyFile)
  }
  rehearsed = @(
    "no_self_replication"
    "no_hidden_network"
    "no_unconsented_pii_learning"
  )
  note = "Stub rehearsal: records that a rehearsal ran. No enforcement actions."
}

$json = $result | ConvertTo-Json -Depth 8
$tmp = "$outFile.tmp"
$json | Set-Content -Encoding utf8 -Path $tmp
Move-Item -Force $tmp $outFile

Write-Host "ok: true"
Write-Host "out: $outFile"

