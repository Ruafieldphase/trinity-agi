<#
check_no_file_uri_in_md.ps1
- Scans *.md files under the workspace for "file:///" links.
- Exits 1 if any are found (prints file + line number).
- Exits 0 if clean.

Usage:
  powershell -ExecutionPolicy Bypass -File scripts\check_no_file_uri_in_md.ps1
  powershell -ExecutionPolicy Bypass -File scripts\check_no_file_uri_in_md.ps1 -Root "$WorkspaceRoot"
#>

param(
  [string]$Root = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

# Directories to skip (tune as needed)
$ExcludeDirs = @(
  ".git", ".venv", "venv", "node_modules", "dist", "build", ".next", ".cache", "__pycache__", ".mypy_cache", "backups", "outputs"
)
$ExcludeDirsLower = $ExcludeDirs | ForEach-Object { $_.ToLowerInvariant() }

function Should-SkipPath([string]$fullPath) {
  $segments = ($fullPath -split '[\\/]+') | ForEach-Object { $_.ToLowerInvariant() }
  foreach ($d in $ExcludeDirsLower) {
    if ($segments -contains $d) { return $true }
  }
  return $false
}

if (-not (Test-Path $Root)) {
  Write-Host "Root path not found: $Root" -ForegroundColor Red
  exit 2
}

$RootPath = (Resolve-Path $Root).Path
Write-Host "Scanning *.md for 'file:///' under: $RootPath" -ForegroundColor Cyan

$mdFiles = Get-ChildItem -Path $RootPath -Recurse -File -Filter "*.md" -ErrorAction SilentlyContinue |
Where-Object { -not (Should-SkipPath $_.FullName) }

$hits = @()

foreach ($f in $mdFiles) {
  $matches = Select-String -Path $f.FullName -Pattern "file:///" -SimpleMatch -AllMatches -ErrorAction SilentlyContinue
  if ($matches) {
    foreach ($m in $matches) {
      $hits += [PSCustomObject]@{
        File = $m.Path
        Line = $m.LineNumber
        Text = $m.Line.Trim()
      }
    }
  }
}

if ($hits.Count -gt 0) {
  Write-Host ""
  Write-Host "[FAIL] Found forbidden 'file:///' links in Markdown:" -ForegroundColor Red
  $hits | Sort-Object File, Line | Format-Table -AutoSize
  Write-Host ""
  Write-Host "Fix: replace file:///... with workspace-relative paths (e.g., docs/..., scripts/..., LLM_Unified/...)." -ForegroundColor Yellow
  exit 1
}

Write-Host "[OK] No 'file:///' links found in Markdown." -ForegroundColor Green
exit 0