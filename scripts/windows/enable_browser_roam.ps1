param(
  # 기본: 7일
  [int]$Days = 7,
  # 고정 상한 대신 "리듬 기반"이 기본.
  # 강제로 제한하고 싶으면 아래 옵션을 사용(0이면 리듬 기반).
  [int]$MaxTasksPerHour = 0,
  [int]$MinCooldownSec = 0,
  # 기본: 제한 없음(0,0) = 24시간 (로컬 시간)
  [int]$StartHourLocal = 0,
  [int]$EndHourLocal = 0,
  [switch]$Silent
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path $PSScriptRoot -Parent)
Set-Location -Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)

$signals = Join-Path (Get-Location) "signals"
New-Item -ItemType Directory -Force -Path $signals | Out-Null

$now = [DateTimeOffset]::UtcNow
$expires = $null
if ($Days -gt 0) {
  $expires = $now.AddDays($Days).ToUnixTimeSeconds()
}

$payload = @{
  allow = $true
  enabled_at = $now.ToString("o")
  origin = "binoche"
  note = "browser roam allowed (read-only, allowlist)"
  max_tasks_per_hour = [int]$MaxTasksPerHour
  min_cooldown_sec = [int]$MinCooldownSec
  allowed_hours_local = @([int]$StartHourLocal, [int]$EndHourLocal)
}
if ($expires -ne $null) { $payload.expires_at = [double]$expires }

$path = Join-Path $signals "body_allow_browser.json"
$json = $payload | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($path, $json, (New-Object System.Text.UTF8Encoding($false)))

if (-not $Silent) {
  Write-Host "[OK] browser roam enabled" -ForegroundColor Green
  Write-Host ("- file: {0}" -f $path)
  if ($expires -ne $null) { Write-Host ("- expires_at(utc epoch): {0}" -f $expires) }
}
