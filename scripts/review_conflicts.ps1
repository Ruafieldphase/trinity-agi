#requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$ConflictsCsv,
    [string]$SourceRoot = 'D:\nas_backup',
    [string]$TargetRoot = 'C:\workspace\agi',
    [ValidateSet('PreferSource', 'PreferTarget', 'Manual', 'All')]
    [string]$Mode = 'All',
    [int]$Count = 10,
    [string[]]$Folders = @()
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ConflictsCsv)) {
    Write-Host "❌ Conflicts CSV not found: $ConflictsCsv" -ForegroundColor Red
    exit 1
}

$rows = Import-Csv -LiteralPath $ConflictsCsv
if ($Folders -and $Folders.Count -gt 0) {
    $rows = $rows | Where-Object { $Folders -contains $_.Folder }
}

# Annotate with comparison
$ann = foreach ($r in $rows) {
    try { $srcTime = [datetime]::Parse($r.SourceTime); $dstTime = [datetime]::Parse($r.TargetTime) } catch { $srcTime = $null; $dstTime = $null }
    $rel = $r.RelativePath
    $src = Join-Path (Join-Path $SourceRoot $r.Folder) $rel
    $dst = Join-Path (Join-Path $TargetRoot $r.Folder) $rel
    $cmp = if (($srcTime -ne $null) -and ($dstTime -ne $null)) {
        if ($srcTime -gt $dstTime) { 'PreferSource' } elseif ($dstTime -gt $srcTime) { 'PreferTarget' } else { 'Manual' }
    }
    else { 'Manual' }
    [pscustomobject]@{ Folder = $r.Folder; RelativePath = $rel; Source = $src; Target = $dst; Decision = $cmp; SourceTime = $r.SourceTime; TargetTime = $r.TargetTime }
}

if ($Mode -ne 'All') { $ann = $ann | Where-Object { $_.Decision -eq $Mode } }

$pick = $ann | Select-Object -First $Count
if (-not $pick -or $pick.Count -eq 0) { Write-Host "No items to review for mode '$Mode'." -ForegroundColor Yellow; exit 0 }

Write-Host ("Opening {0} diffs in VS Code (mode={1})..." -f $pick.Count, $Mode) -ForegroundColor Cyan
foreach ($p in $pick) {
    if ((Test-Path -LiteralPath $p.Source) -and (Test-Path -LiteralPath $p.Target)) {
        Start-Process code -ArgumentList @('--diff', $p.Source, $p.Target)
    }
    elseif (Test-Path -LiteralPath $p.Target) {
        Start-Process code -ArgumentList @($p.Target)
    }
    elseif (Test-Path -LiteralPath $p.Source) {
        Start-Process code -ArgumentList @($p.Source)
    }
    else {
        Write-Host ("Skip (missing both): {0}/{1}" -f $p.Folder, $p.RelativePath) -ForegroundColor Yellow
    }
}

Write-Host "✅ Review launch complete." -ForegroundColor Green
exit 0
