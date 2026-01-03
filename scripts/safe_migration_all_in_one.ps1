#requires -Version 5.1
param(
    [string]$Source = 'D:\nas_backup',
    [string]$Target = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )",
    [string[]]$Folders = @('scripts', 'outputs', 'session_memory', 'docs', 'configs', 'knowledge_base'),
    [switch]$DryRun,
    [switch]$NoOpen
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Ok($m) { Write-Host $m -ForegroundColor Green }
function Write-Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

if (-not (Test-Path -LiteralPath $Source)) { Write-Err "❌ Source not found: $Source"; exit 1 }
if (-not (Test-Path -LiteralPath $Target)) { Write-Warn "📁 Target missing. Creating: $Target"; New-Item -ItemType Directory -Path $Target -Force | Out-Null }

Write-Info "🔎 Step 1/3: Safe migration ($(if($DryRun){'DRY-RUN'}else{'COPY-missing'}))"
$smScript = Join-Path $Source 'scripts\safe_migration.ps1'
$smArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $smScript, '-Source', $Source, '-Target', $Target)
# Only pass -Folders if explicitly provided to this wrapper; else let the inner script use its defaults
if ($PSBoundParameters.ContainsKey('Folders')) { $smArgs += @('-Folders') + $Folders }
if ($DryRun) { $smArgs += '-DryRun' }
& powershell @smArgs

$outDir = Join-Path $Source 'outputs'
$list1 = Get-ChildItem -LiteralPath $outDir -Filter 'migration_conflicts_*.csv' -ErrorAction SilentlyContinue
$list2 = Get-ChildItem -LiteralPath $env:TEMP -Filter 'migration_conflicts_*.csv' -ErrorAction SilentlyContinue
$candidates = @(); if ($list1) { $candidates += $list1 }; if ($list2) { $candidates += $list2 }
$latestCsv = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latestCsv) { Write-Err "❌ No conflicts CSV found after safe_migration run (checked outputs and TEMP)."; exit 1 }

Write-Info "📝 Step 2/3: Generate conflict plan"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Source 'scripts\plan_conflict_resolution.ps1') -ConflictsCsv $latestCsv.FullName -SourceRoot $Source -TargetRoot $Target | Out-Null

$latestPlan = Get-ChildItem -LiteralPath $outDir -Filter 'conflict_resolution_PLAN_*.md' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latestPlan) { Write-Err "❌ Plan generation failed."; exit 1 }

Write-Info "📊 Step 3/3: Summary"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Source 'scripts\summarize_conflicts.ps1') -ConflictsCsv $latestCsv.FullName | Out-String | Write-Host
$latestSummary = Get-ChildItem -LiteralPath (Join-Path $Source 'outputs') -Filter 'conflicts_summary_*.md' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ("- Conflicts CSV: {0}" -f $latestCsv.FullName)
Write-Host ("- Plan:         {0}" -f $latestPlan.FullName)
if ($latestSummary) { Write-Host ("- Summary:      {0}" -f $latestSummary.FullName) }

if (-not $NoOpen) {
    $toOpen = @()
    if ($latestPlan) { $toOpen += $latestPlan.FullName }
    if ($latestSummary) { $toOpen += $latestSummary.FullName }
    if ($toOpen.Count -gt 0) { Start-Process code -ArgumentList $toOpen }
}

Write-Ok "✅ All-in-one completed."
exit 0