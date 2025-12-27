# Purpose: Stub for ChatGPT Lua Bridge task registration (docs reference).
# Note: Real scheduled task setup is not implemented here.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "outputs"
$outFile = Join-Path $outDir "chatgpt_lua_bridge_task_latest.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$result = [ordered]@{
  ok = $false
  version = "register_chatgpt_lua_bridge_task_stub_v1"
  timestamp = (Get-Date).ToUniversalTime().ToString("o")
  reason = "not_implemented"
}

$json = $result | ConvertTo-Json -Depth 6
$tmp = "$outFile.tmp"
$json | Set-Content -Encoding utf8 -Path $tmp
Move-Item -Force $tmp $outFile

Write-Host "ok: false (stub)"
Write-Host "out: $outFile"

