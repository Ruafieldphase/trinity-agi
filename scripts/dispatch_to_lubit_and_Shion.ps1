<#
.SYNOPSIS
  Distribute a work item to Lubit (review packet) and Shion (Gemini code assist) in parallel, optionally across multiple files.

.DESCRIPTION
  - Generates a review packet once (Lubit)
  - Launches one or more Gemini code-assist jobs (Shion), one per target file (or a single job without file)
  - Produces a collaboration summary markdown listing all artifacts and statuses

.PARAMETER Issue
  A concise issue/task description to guide both Lubit and Shion.

.PARAMETER Files
  Optional array of file paths to target for Shion (Gemini) suggestions. If omitted, runs a single generic suggestion.

.PARAMETER Model
  Gemini model ID to use. Default: gemini-2.0-flash-exp

.PARAMETER OutDir
  Output directory for artifacts. Default: <repoRoot>/outputs

.PARAMETER Parallelism
  Reserved for future throttling. Currently starts all jobs and waits.

.PARAMETER Open
  If set, opens the output folder and summary markdown in Explorer at the end.

.NOTES
  - Requires existing scripts/tools:
    scripts/prepare_lubit_review_packet.ps1
    tools/gemini_code_assist_poc.py
  - Prefers repo venv Python if available at LLM_Unified/.venv/Scripts/python.exe
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string]$Issue,
    [string[]]$Files,
    [string]$Model = "gemini-2.0-flash-exp",
    [string]$OutDir,
    [int]$Parallelism = 4,
    [switch]$Open
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-DirectoryIfMissing {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

# Resolve repository root and defaults
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutDir) { $OutDir = Join-Path $repoRoot 'outputs' }
New-DirectoryIfMissing -Path $OutDir

# Prefer repo venv Python if available
$venvPython = Join-Path $repoRoot 'LLM_Unified/.venv/Scripts/python.exe'
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python' }

# Tools & scripts
$preparePacket = Join-Path $PSScriptRoot 'prepare_lubit_review_packet.ps1'
$geminiPOC = Join-Path (Join-Path $repoRoot 'tools') 'gemini_code_assist_poc.py'

if (-not (Test-Path -LiteralPath $preparePacket)) {
    throw "Missing script: $preparePacket"
}
if (-not (Test-Path -LiteralPath $geminiPOC)) {
    throw "Missing tool: $geminiPOC"
}

# Timestamp for grouping outputs
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss\Z')

Write-Host "[1/3] Lubit: Preparing review packet..." -ForegroundColor Cyan
& $preparePacket

# Discover latest review packet artifacts under OutDir
$latestPacketFolder = Get-ChildItem -LiteralPath $OutDir -Directory -Filter 'review_packet_*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestPacketZip = Get-ChildItem -LiteralPath $OutDir -File -Filter 'review_packet_*.zip' | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $latestPacketFolder) { Write-Warning 'No review packet folder found after preparation.' }
if (-not $latestPacketZip) { Write-Warning 'No review packet ZIP found after preparation.' }

Write-Host "[2/3] Shion: Launching Gemini code assist jobs..." -ForegroundColor Cyan

# Build job list
# Coerce to array even if null/singleton
$Files = @($Files)
# Filter out empty/null entries
$Files = @($Files | Where-Object { $_ -ne $null -and $_ -ne '' })
# Normalize comma-separated list from VS Code task input
if ($Files.Count -eq 1 -and $Files[0] -match ',') {
    $Files = @($Files[0].Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
}
$targets = @()
if ($Files.Count -gt 0) {
    $targets = $Files
}
else {
    $targets = @($null)  # one generic job without file
}

$jobs = @()
$idx = 0
foreach ($t in $targets) {
    $idx++
    $filename = if ($t) { "gemini_assist_${ts}_$idx.md" } else { "gemini_assist_${ts}.md" }
    $outPath = Join-Path $OutDir $filename

    $job = Start-Job -ScriptBlock {
        param($py, $poc, $issueText, $fileParam, $outMd, $modelId)
        try {
            if ($fileParam) {
                & $py $poc --issue $issueText --file $fileParam --out $outMd --model $modelId
            }
            else {
                & $py $poc --issue $issueText --out $outMd --model $modelId
            }
            $code = if ($LASTEXITCODE -is [int]) { $LASTEXITCODE } else { 0 }
            [pscustomobject]@{ ExitCode = $code; OutPath = $outMd; File = $fileParam }
        }
        catch {
            [pscustomobject]@{ ExitCode = 1; OutPath = $outMd; File = $fileParam; Error = $_.Exception.Message }
        }
    } -ArgumentList $pythonExe, $geminiPOC, $Issue, $t, $outPath, $Model

    $jobs += $job
}

if ($jobs.Count -gt 0) {
    Wait-Job -Job $jobs | Out-Null
}

$results = @()
foreach ($j in $jobs) {
    $recv = Receive-Job -Job $j -ErrorAction SilentlyContinue
    if ($recv) { $results += $recv }
    Remove-Job -Job $j -Force -ErrorAction SilentlyContinue
}
# Keep only structured results from the job (drop plain stdout lines)
$results = @($results | Where-Object { $_ -is [object] -and $_.PSObject.Properties['ExitCode'] -and $_.PSObject.Properties['OutPath'] })

# Summarize results
$failed = @($results | Where-Object { $_.ExitCode -ne 0 })
$summaryPath = Join-Path $OutDir ("collaboration_summary_${ts}.md")
$packetFolderPath = if ($latestPacketFolder) { $latestPacketFolder.FullName } else { '(not found)' }
$packetZipPath = if ($latestPacketZip) { $latestPacketZip.FullName } else { '(not found)' }

$lines = @()
$lines += "# Collaboration Summary (${ts})"
$lines += ''
$lines += "- Issue: $Issue"
$lines += "- Model: $Model"
$lines += "- Output Folder: $OutDir"
$lines += ''
$lines += "## Lubit (Review Packet)"
$lines += "- Folder: $packetFolderPath"
$lines += "- ZIP: $packetZipPath"
$lines += ''
$lines += "## Shion (Gemini Code Assist)"
if ($results.Count -eq 0) {
    $lines += "- No jobs executed."
}
else {
    foreach ($r in $results) {
        $tag = if ($r.File) { "file='" + $r.File + "'" } else { 'generic' }
        $status = if ($r.ExitCode -eq 0) { 'OK' } else { 'FAIL' }
        $outp = if ($r.PSObject.Properties['OutPath']) { $r.OutPath } else { '(n/a)' }
        $lines += "- [$status] $tag -> $outp"
        if ($r.PSObject.Properties['Error']) { $lines += "  - Error: $($r.Error)" }
    }
}
$lines += ''
$lines += '## Next steps'
$lines += '- Lubit: Review the packet ZIP and validate completeness.'
$lines += '- Shion: Review Gemini suggestions and shortlist actionable refactors.'
$lines += '- Owner: Convert approved items into tracked tasks and schedule.'

$lines -join [Environment]::NewLine | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host "[3/3] Done. Summary: $summaryPath" -ForegroundColor Green
Write-Host "Artifacts folder: $OutDir" -ForegroundColor Green

if ($Open.IsPresent) {
    try { Start-Process explorer.exe $OutDir | Out-Null } catch {}
    try { Start-Process $summaryPath | Out-Null } catch {}
}

# Exit code indicates if any Shion job failed
if ($failed.Count -gt 0) { exit 2 } else { exit 0 }