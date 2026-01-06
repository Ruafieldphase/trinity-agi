param(
    [switch]$Open
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "[YouTubeIndex] Generating index..." -ForegroundColor Cyan

& py -3 -X utf8 scripts/summarize_youtube_learner.py
if ($LASTEXITCODE -ne 0) {
    throw "Index generation failed (exit $LASTEXITCODE)"
}

$indexPath = Join-Path (Get-Location) 'outputs/youtube_learner/INDEX.md'
if (Test-Path $indexPath) {
    Write-Host "[YouTubeIndex] Wrote: $indexPath" -ForegroundColor Green
    if ($Open) {
        try { & code $indexPath } catch { Start-Process $indexPath }
    }
} else {
    Write-Warning "[YouTubeIndex] INDEX.md not found."
}
