$ErrorActionPreference = "SilentlyContinue"

Set-Location -Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
$signals = Join-Path (Get-Location) "signals"
New-Item -ItemType Directory -Force -Path $signals | Out-Null

$stopPath = Join-Path $signals "body_stop.json"
@{ stop_at = [DateTimeOffset]::UtcNow.ToString("o"); origin = "Binoche_Observer" } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $stopPath

# best-effort: also clear arm (so it won't restart)
$armPath = Join-Path $signals "body_arm.json"
Remove-Item -Force -ErrorAction SilentlyContinue $armPath

Write-Host "[OK] stop requested"
