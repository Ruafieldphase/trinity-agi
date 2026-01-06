param(
  [switch]$Silent
)

$ErrorActionPreference = "SilentlyContinue"

Set-Location -Path (Split-Path $PSScriptRoot -Parent)
Set-Location -Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)

$path = Join-Path (Get-Location) "signals\\body_allow_browser.json"
Remove-Item -Force -ErrorAction SilentlyContinue $path

if (-not $Silent) {
  Write-Host "[OK] browser roam disabled (removed signals/body_allow_browser.json)" -ForegroundColor Yellow
}

