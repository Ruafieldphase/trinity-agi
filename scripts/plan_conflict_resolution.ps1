#requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$ConflictsCsv,
    [string]$SourceRoot = 'D:\nas_backup',
    [string]$TargetRoot = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )",
    [string]$OutPlanMd = ''
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'

function New-Line { param([string]$s = '') ; return $s }

if (-not (Test-Path -LiteralPath $ConflictsCsv)) {
    Write-Host "❌ Conflicts CSV not found: $ConflictsCsv" -ForegroundColor Red
    exit 1
}

if (-not $OutPlanMd -or [string]::IsNullOrWhiteSpace($OutPlanMd)) {
    $outDir = Join-Path $SourceRoot 'outputs'
    if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $OutPlanMd = Join-Path $outDir ("conflict_resolution_PLAN_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".md")
}

$rows = Import-Csv -LiteralPath $ConflictsCsv

$preferSource = @()
$preferTarget = @()
$manual = @()

foreach ($r in $rows) {
    try {
        $srcTime = [datetime]::Parse($r.SourceTime)
        $dstTime = [datetime]::Parse($r.TargetTime)
    }
    catch {
        $srcTime = Get-Date 0
        $dstTime = Get-Date 0
    }

    if ($srcTime -gt $dstTime) {
        $preferSource += $r
    }
    elseif ($dstTime -gt $srcTime) {
        $preferTarget += $r
    }
    else {
        $manual += $r
    }
}

$lines = @()
$lines += "# Conflict Resolution Plan"
$lines += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += "- Source: $SourceRoot"
$lines += "- Target: $TargetRoot"
$lines += New-Line
$lines += "## Summary"
$lines += "- Prefer Source (newer at source): $($preferSource.Count)"
$lines += "- Prefer Target (newer at target): $($preferTarget.Count)"
$lines += "- Manual Review (tie/unknown): $($manual.Count)"
$lines += New-Line

function Add-Section {
    param(
        [string]$title,
        [array]$items
    )
    $script:lines += ("## {0}" -f $title)
    if (-not $items -or $items.Count -eq 0) { $script:lines += "(none)"; $script:lines += New-Line; return }
    foreach ($r in $items) {
        $rel = $r.RelativePath
        $src = Join-Path (Join-Path $SourceRoot $r.Folder) $rel
        $dst = Join-Path (Join-Path $TargetRoot $r.Folder) $rel
        $script:lines += ("- {0}/{1}" -f $r.Folder, $rel)
        $script:lines += ("  - Source: size={0} time={1}" -f $r.SourceSize, $r.SourceTime)
        $script:lines += ("  - Target: size={0} time={1}" -f $r.TargetSize, $r.TargetTime)
        if ($title -like 'Prefer Source*') {
            $script:lines += "  - Action: copy source -> target"
            $script:lines += ('    - Command (optional): Copy-Item -LiteralPath "{0}" -Destination "{1}" -Force' -f $src, $dst)
        }
        elseif ($title -like 'Prefer Target*') {
            $script:lines += "  - Action: keep target (no changes)"
        }
        else {
            $script:lines += "  - Action: manual diff/merge recommended"
            $script:lines += ('    - Suggestion: code --diff "{0}" "{1}"' -f $src, $dst)
        }
    }
    $script:lines += New-Line
}

Add-Section -title "Prefer Source (newer at source)" -items $preferSource
Add-Section -title "Prefer Target (newer at target)" -items $preferTarget
Add-Section -title "Manual Review (tie/unknown)" -items $manual

$lines | Out-File -FilePath $OutPlanMd -Encoding UTF8
Write-Host "📝 Plan written: $OutPlanMd" -ForegroundColor Green
exit 0