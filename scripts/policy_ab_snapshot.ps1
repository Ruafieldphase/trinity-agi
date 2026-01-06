Param(
    [int]$Lines = 50000,
    [switch]$OpenMd
)

$ErrorActionPreference = 'Stop'

Write-Host "Generating policy A/B snapshot..." -ForegroundColor Cyan

$outDir = Join-Path (Resolve-Path ".").Path "outputs"
if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

# 1) Run ledger policy analyzer
python scripts/analyze_policy_from_ledger.py --lines $Lines --out "$outDir/policy_ab_summary_latest.json"

# 2) Run synthetic A/B micro-benchmark
python scripts/policy_ab_microbench.py --lines $Lines --out "$outDir/policy_ab_synthetic_latest.json"

# 3) Build Markdown summary
$summaryPath = Join-Path $outDir "policy_ab_snapshot_latest.md"

$ledgerJson = Get-Content "$outDir/policy_ab_summary_latest.json" -Raw | ConvertFrom-Json
$syntheticJson = Get-Content "$outDir/policy_ab_synthetic_latest.json" -Raw | ConvertFrom-Json

$md = @()
$md += "# Policy A/B Snapshot"
$md += ""
$md += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += "Lines analyzed (ledger): $($ledgerJson.analyzed_lines)"
$md += ""
$md += "## Ledger-Based Counts"
foreach ($k in $ledgerJson.policies.PSObject.Properties.Name) {
    $p = $ledgerJson.policies.$k
    $md += ("- {0}: count={1} allow={2} warn={3} block={4} avg={5}ms p95={6}ms" -f `
        $k, $p.count, $p.allow, $p.warn, $p.block, [math]::Round($p.avg_latency_ms), [math]::Round($p.p95_latency_ms))
}
$md += ""
$md += "## Synthetic Re-Evaluation"
foreach ($k in $syntheticJson.policies.PSObject.Properties.Name) {
    $p = $syntheticJson.policies.$k
    $md += ("- {0}: n={1} allow={2} warn={3} avg={4}ms p95={5}ms" -f `
        $k, $p.samples, $p.allow, $p.warn, [math]::Round($p.avg_latency_ms), [math]::Round($p.p95_latency_ms))
}

Set-Content -Path $summaryPath -Value ($md -join "`r`n") -Encoding UTF8

Write-Host "Snapshot written: $summaryPath" -ForegroundColor Green

if ($OpenMd) { Start-Process $summaryPath }