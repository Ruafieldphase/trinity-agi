# Purpose: Minimal stub to satisfy docs references.
# Notes:
# - This script does not call network or external models.
# - It only checks for expected local files and writes a small status JSON.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$constitution = Join-Path $root "policy\\core_constitution.json"
$outDir = Join-Path $root "outputs"
$outFile = Join-Path $outDir "inject_core_philosophy_latest.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$result = [ordered]@{
  ok = $true
  version = "inject_core_philosophy_stub_v1"
  timestamp = (Get-Date).ToUniversalTime().ToString("o")
  inputs = @{
    core_constitution_json = @{
      path = $constitution
      exists = (Test-Path $constitution)
    }
  }
  note = "Stub: no injection performed. This file exists to restore doc-path connectivity."
}

$json = $result | ConvertTo-Json -Depth 8
$tmp = "$outFile.tmp"
$json | Set-Content -Encoding utf8 -Path $tmp
Move-Item -Force $tmp $outFile

Write-Host "ok: true"
Write-Host "out: $outFile"
