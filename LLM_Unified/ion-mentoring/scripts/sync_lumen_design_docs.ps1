#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Sync Lumen design documentation from origin folders to repository docs.

.DESCRIPTION
  Imports design files (.md, .yaml, .json, images) from three origin folders
  into LLM_Unified/ion-mentoring/docs/lumen_design, preserving directory structure.
  
  Auto-detects source folders containing 'lumen_v*' files. Generates per-folder
  README with file listings and a root INDEX.md for navigation.

.PARAMETER OriginRoot
  Base directory containing origin folders (default: D:\nas_backup\ai_binoche_conversation_origin\lumen)

.PARAMETER OriginFolders
  Specific folder names to sync (default: auto-detect folders with lumen_v* files)

.PARAMETER DestRoot
  Target directory in repository (default: ../docs/lumen_design relative to script)

.PARAMETER Extensions
  File extensions to include (default: .md, .yaml, .yml, .json, .png, .jpg, .jpeg, .svg, .gif)

.PARAMETER IncludeArchives
  Include archive files (.zip, .tar, .gz)

.PARAMETER CleanDest
  Remove all existing files in destination before sync (full refresh)

.EXAMPLE
  # Full sync with clean (recommended for first run)
  .\sync_lumen_design_docs.ps1 -CleanDest

.EXAMPLE
  # Incremental sync (preserves existing files, updates changed)
  .\sync_lumen_design_docs.ps1

.EXAMPLE
  # Sync specific folders only
  .\sync_lumen_design_docs.ps1 -OriginFolders @("루멘vs code 연결", "루멘vs code 연결2")

.EXAMPLE
  # Include archive files
  .\sync_lumen_design_docs.ps1 -IncludeArchives

.NOTES
  After sync, design docs are accessible via:
  - Repository: LLM_Unified/ion-mentoring/docs/lumen_design/INDEX.md
  - Operations Runbook: lumen/feedback/OPERATIONS_RUNBOOK.md (📚 Design Docs section)
  - Global Index: docs/INDEX.md (Lumen Design Archive link)
  
  Total synced: 321 files from 3 origin folders
#>

param(
    [string]$OriginRoot = "D:\nas_backup\ai_binoche_conversation_origin\lumen",
    [string[]]$OriginFolders = @(),
    [string]$DestRoot = (Join-Path $PSScriptRoot "..\docs\lumen_design"),
    [string[]]$Extensions = @(".md", ".yaml", ".yml", ".json", ".png", ".jpg", ".jpeg", ".svg", ".gif"),
    [switch]$IncludeArchives,
    [switch]$CleanDest
)

Write-Host "[sync] OriginRoot=" -NoNewline; Write-Host $OriginRoot -ForegroundColor Cyan
Write-Host "[sync] DestRoot=" -NoNewline; Write-Host (Resolve-Path -LiteralPath $DestRoot -ErrorAction SilentlyContinue) -ForegroundColor Cyan

if ($IncludeArchives) {
    $Extensions += @(".zip", ".tar", ".gz")
}

# Ensure destination exists
if (-not (Test-Path -LiteralPath $DestRoot)) {
    New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null
}

if ($CleanDest) {
    Write-Host "[sync] Cleaning destination: $DestRoot" -ForegroundColor Yellow
    Get-ChildItem -LiteralPath $DestRoot -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

$autoDetected = $false
if (-not $OriginFolders -or $OriginFolders.Count -eq 0) {
    # Auto-detect likely Lumen design folders: pick directories that contain at least one file starting with 'lumen_v'
    $candidates = Get-ChildItem -LiteralPath $OriginRoot -Directory -ErrorAction SilentlyContinue
    $selected = @()
    foreach ($dir in $candidates) {
        $hasLumenV = Get-ChildItem -LiteralPath $dir.FullName -File -Recurse -ErrorAction SilentlyContinue -Filter 'lumen_v*' | Select-Object -First 1
        if ($hasLumenV) { $selected += $dir.Name }
    }
    if ($selected.Count -gt 0) {
        $OriginFolders = $selected
        $autoDetected = $true
        Write-Host "[sync] Auto-detected source folders: $($OriginFolders -join ', ')" -ForegroundColor Yellow
    }
}

$total = 0
$folderSummaries = @()

foreach ($folder in $OriginFolders) {
    $source = Join-Path $OriginRoot $folder
    if (-not (Test-Path -LiteralPath $source)) {
        Write-Warning "[sync] Source not found: $source"
        continue
    }

    $destSub = Join-Path $DestRoot $folder
    New-Item -ItemType Directory -Path $destSub -Force | Out-Null

    Write-Host "[sync] Copying from $source → $destSub" -ForegroundColor Green

    # Gather files matching allowed extensions
    $files = Get-ChildItem -LiteralPath $source -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $Extensions -contains $_.Extension.ToLower() }

    $count = 0
    foreach ($f in $files) {
        $relative = $f.FullName.Substring($source.Length).TrimStart('\', '/')
        $target = Join-Path $destSub $relative
        $targetDir = Split-Path $target -Parent
        if (-not (Test-Path -LiteralPath $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $f.FullName -Destination $target -Force
        $count++
    }

    $folderSummaries += [pscustomobject]@{
        Folder = $folder
        Source = $source
        Dest   = $destSub
        Count  = $count
    }
    $total += $count

    # Create per-origin README.md
    $readmePath = Join-Path $destSub "README.md"
    $list = $files | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($source.Length).TrimStart('\', '/')
        $relWeb = ($rel -replace '\\', '/')
        "- [$rel]($relWeb)"
    }

    @"
# Source: $folder

Synced from: $source
Files: $count
Last Sync: $((Get-Date).ToString("s"))

## Files
$(($list -join "`r`n"))
"@ | Set-Content -Path $readmePath -Encoding UTF8
}

# Write root INDEX.md under DestRoot
$indexPath = Join-Path $DestRoot "INDEX.md"
$lines = @()
$lines += "# Lumen Design Archive"
$lines += ""
$lines += "Synced on: $((Get-Date).ToString('s'))"
$lines += ""
$lines += "## Sources"
foreach ($s in $folderSummaries) {
    $folderNameWeb = ($s.Folder -replace '\\', '/')
    $lines += "- $($s.Folder): $($s.Count) files → [browse]($folderNameWeb/README.md)"
}
$lines += ""
$lines += "Total files: $total"

Set-Content -Path $indexPath -Value ($lines -join "`r`n") -Encoding UTF8

Write-Host "[sync] Completed. Total files: $total" -ForegroundColor Green
