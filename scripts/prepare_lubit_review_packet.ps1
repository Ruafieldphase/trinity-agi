#!/usr/bin/env pwsh
<#!
.SYNOPSIS
  Prepare a compressed review packet for Lubit (reviewer).
.DESCRIPTION
  Collects key Week 3 deliverables and assembles a versioned ZIP under outputs/.
  Also generates a short README_REVIEW.txt with a one-page summary.
.PARAMETER OutDir
  Optional. Output base directory. Default: C:\workspace\agi\outputs
#>
param(
    [string]$OutDir = "C:\workspace\agi\outputs"
)

$ErrorActionPreference = "Stop"

function New-Timestamp {
    return (Get-Date).ToString('yyyyMMdd_HHmmss')
}

function Ensure-Dir($path) {
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

$root = "C:\workspace\agi"
$ts = New-Timestamp
$sessionDir = Join-Path $OutDir "review_packet_$ts"
Ensure-Dir $OutDir
Ensure-Dir $sessionDir

# Candidate files (best-effort; skip missing)
$files = @(
    "Phase1_Week3_최종?�수?�계_2025-10-22.md",
    "Phase1_Week3_?�료보고??2025-10-22.md",
    "Phase1_Week3_TODO_?�료.md",
    "깃코_Phase1_Week3_최종?�료?�약_2025-10-22.md",
    "?�약_모델_벤치마크_결과_2025-10-22.md",
    "?�?�요???�도개선_?�안_2025-10-22.md"
)

$collected = @()
foreach ($f in $files) {
    $full = Join-Path $root $f
    if (Test-Path -LiteralPath $full) {
        Copy-Item -LiteralPath $full -Destination (Join-Path $sessionDir $f) -Force
        $collected += $f
    }
}

# Compose README summary
$readmePath = Join-Path $sessionDir "README_REVIEW.txt"
$summary = @()
$summary += "Phase 1 Week 3 - Review Packet"
$summary += "Generated: $((Get-Date).ToString('u'))"
$summary += "Collector: prepare_lubit_review_packet.ps1"
$summary += ""
$summary += "Included Files:" 
if ($collected.Count -eq 0) {
    $summary += "  (none found)"
}
else {
    foreach ($c in $collected) { $summary += "  - $c" }
}
$summary += ""
$summary += "Highlights:"
$summary += "  - 7/7 tasks complete; performance targets achieved"
$summary += "  - Summary_light mode; running summary; L1 cache; monitoring integrated"
$summary += "  - Benchmark: current pipeline >> Gemini for latency/stability/cost"
$summary += ""
$summary += "How to verify quickly:"
$summary += "  1) Open Phase1_Week3_최종?�수?�계_2025-10-22.md for operations handover"
$summary += "  2) Run tests listed in the doc (integration + unit)"
$summary += "  3) Generate daily report: scripts/generate_daily_report.ps1"
$summary += ""
$summary -join "`r`n" | Out-File -FilePath $readmePath -Encoding UTF8 -Force

# Zip
$zipPath = Join-Path $OutDir ("review_packet_" + $ts + ".zip")
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -Path (Join-Path $sessionDir '*') -DestinationPath $zipPath

Write-Host "Review packet prepared." -ForegroundColor Green
Write-Host "Folder: $sessionDir" -ForegroundColor Cyan
Write-Host "ZIP:    $zipPath" -ForegroundColor Cyan
