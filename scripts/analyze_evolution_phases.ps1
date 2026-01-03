# Purpose: Minimal stub to satisfy docs references.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "outputs"
$outFile = Join-Path $outDir "evolution_phases_analysis_latest.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$result = [ordered]@{
  ok = $false
  version = "evolution_phases_analyzer_stub_v1"
  timestamp = (Get-Date).ToUniversalTime().ToString("o")
  reason = "not_implemented"
}

$json = $result | ConvertTo-Json -Depth 6
$tmp = "$outFile.tmp"
$json | Set-Content -Encoding utf8 -Path $tmp
Move-Item -Force $tmp $outFile

Write-Host "ok: false (stub)"
Write-Host "out: $outFile"
