# Purpose: Minimal stub to satisfy docs references.
# Notes:
# - No git/network calls. Only produces a small placeholder output file.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "outputs"
$outFile = Join-Path $outDir "gittco_patterns_latest.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$result = [ordered]@{
  ok = $false
  version = "gittco_patterns_stub_v1"
  timestamp = (Get-Date).ToUniversalTime().ToString("o")
  reason = "stub_only"
  note = "Docs placeholder. Implement real analysis if/when a concrete data source is defined."
}

$json = $result | ConvertTo-Json -Depth 6
$tmp = "$outFile.tmp"
$json | Set-Content -Encoding utf8 -Path $tmp
Move-Item -Force $tmp $outFile

Write-Host "ok: false (stub)"
Write-Host "out: $outFile"
