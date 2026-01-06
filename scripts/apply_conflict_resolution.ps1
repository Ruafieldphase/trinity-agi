#requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$ConflictsCsv,
    [string]$SourceRoot = 'D:\nas_backup',
    [string]$TargetRoot = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )",
    [ValidateSet('PreferSource', 'PreferTarget', 'All')]
    [string]$Mode = 'PreferSource',
    [string[]]$Folders = @(),
    [switch]$DryRun,
    [switch]$NoBackup
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

if (-not (Test-Path -LiteralPath $ConflictsCsv)) { Write-Err "❌ CSV not found: $ConflictsCsv"; exit 1 }
if (-not (Test-Path -LiteralPath $SourceRoot)) { Write-Err "❌ Source root not found: $SourceRoot"; exit 1 }
if (-not (Test-Path -LiteralPath $TargetRoot)) { Write-Warn "📁 Target missing. Creating: $TargetRoot"; New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null }

$rows = Import-Csv -LiteralPath $ConflictsCsv

# Filter by folder if provided
if ($Folders -and $Folders.Count -gt 0) {
    $rows = $rows | Where-Object { $Folders -contains $_.Folder }
}

# Decide action per row
$actions = @()
foreach ($r in $rows) {
    try {
        $srcTime = [datetime]::Parse($r.SourceTime)
        $dstTime = [datetime]::Parse($r.TargetTime)
    }
    catch { $srcTime = Get-Date 0; $dstTime = Get-Date 0 }

    $rel = $r.RelativePath
    $src = Join-Path (Join-Path $SourceRoot $r.Folder) $rel
    $dst = Join-Path (Join-Path $TargetRoot $r.Folder) $rel

    if ($Mode -eq 'PreferSource') {
        if ($srcTime -gt $dstTime) {
            $actions += [pscustomobject]@{ Action = 'CopySrcToDst'; Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst }
        }
    }
    elseif ($Mode -eq 'PreferTarget') {
        if ($dstTime -gt $srcTime) {
            $actions += [pscustomobject]@{ Action = 'KeepTarget'; Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst }
        }
    }
    else {
        # All
        if ($srcTime -gt $dstTime) {
            $actions += [pscustomobject]@{ Action = 'CopySrcToDst'; Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst }
        }
        elseif ($dstTime -gt $srcTime) {
            $actions += [pscustomobject]@{ Action = 'KeepTarget'; Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst }
        }
        else {
            $actions += [pscustomobject]@{ Action = 'Manual'; Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst }
        }
    }
}

Write-Info "🔧 Apply Conflict Resolution"
Write-Host  "    Mode:     $Mode"
Write-Host  "    DryRun:   $($DryRun.IsPresent)"
Write-Host  "    Backup:   $(-not $NoBackup.IsPresent)"
Write-Host  "    Filter:   $(if($Folders){$Folders -join ', '} else {'(none)'})"
Write-Host  "    Candidates: $($actions.Count)"

$copied = 0; $skipped = 0; $manual = 0
foreach ($a in $actions) {
    $dir = Split-Path -Path $a.Target -Parent
    switch ($a.Action) {
        'CopySrcToDst' {
            if (-not (Test-Path -LiteralPath $a.Source)) { Write-Warn ("❔ Missing source: {0}" -f $a.Source); $skipped++; continue }
            if (-not (Test-Path -LiteralPath $dir)) { if (-not $DryRun) { New-Item -ItemType Directory -Path $dir -Force | Out-Null } }
            if (-not $DryRun) {
                if (-not $NoBackup) {
                    if (Test-Path -LiteralPath $a.Target) {
                        $bak = $a.Target + ('.bak.' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
                        Copy-Item -LiteralPath $a.Target -Destination $bak -Force
                    }
                }
                Copy-Item -LiteralPath $a.Source -Destination $a.Target -Force
            }
            Write-Host ("✔ Copy: {0}/{1}" -f $a.Folder, $a.RelativePath)
            $copied++
        }
        'KeepTarget' {
            Write-Host ("↪ Keep: {0}/{1}" -f $a.Folder, $a.RelativePath)
            $skipped++
        }
        default {
            Write-Host ("🧩 Manual: {0}/{1}" -f $a.Folder, $a.RelativePath)
            $manual++
        }
    }
}

Write-Ok ("\n✅ Done. Copied={0}, Kept={1}, Manual={2}" -f $copied, $skipped, $manual)
exit 0