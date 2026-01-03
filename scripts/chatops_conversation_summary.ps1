# ChatOps Helper: Conversation Log Summary
# Finds the latest JSONL conversation log and runs the summarizer

param(
    [string]$Input,
    [int]$MaxTimeline = 60,
    [string]$OutDir = "outputs"
)

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m) { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Err($m) { Write-Host $m -ForegroundColor Red }

try {
    # Ensure UTF-8 output in legacy PowerShell
    if ($PSVersionTable.PSVersion.Major -le 5) {
        try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
    }

    $ws = "$PSScriptRoot" | Split-Path -Parent
    $summarizer = Join-Path $ws 'scripts/summarize_conversation_log.py'
    if (-not (Test-Path $summarizer)) {
        Err "Summarizer not found: $summarizer"
        exit 2
    }

    # Discover latest JSONL if not specified
    $inPath = $Input
    if ([string]::IsNullOrWhiteSpace($inPath)) {
        $root = Join-Path $ws 'ai_binoche_conversation_origin'
        if (-not (Test-Path $root)) {
            Err "Log root not found: $root"
            exit 2
        }
        $latest = Get-ChildItem -Path $root -Recurse -Filter *.jsonl -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $latest) {
            Err "No JSONL logs found under: $root"
            exit 2
        }
        $inPath = $latest.FullName
    }

    # Prepare outputs
    $dateTag = (Get-Date).ToString('yyyy-MM-dd')
    $outDirAbs = Join-Path $ws $OutDir
    if (-not (Test-Path $outDirAbs)) { New-Item -ItemType Directory -Path $outDirAbs | Out-Null }
    $outMd = Join-Path $outDirAbs "conversation_summary_$dateTag.md"
    $outJson = Join-Path $outDirAbs "conversation_timeline_$dateTag.json"

    # Force UTF-8 for Python prints
    $env:PYTHONIOENCODING = 'utf-8'

    # Pick Python launcher: prefer py -3, fallback to python
    $pyCmd = $null
    if (Get-Command py -ErrorAction SilentlyContinue) { $pyCmd = 'py' } else { $pyCmd = 'python' }
    $args = @()
    if ($pyCmd -eq 'py') { $args += '-3' }
    $args += $summarizer
    $args += @('--input', $inPath, '--out-md', $outMd, '--out-json', $outJson, '--max-timeline', $MaxTimeline)

    Info "Running summarizer..."
    Info "Input: $inPath"
    & $pyCmd @args
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Err "Summarizer exited with code $code"
        exit $code
    }

    Ok "Summary generated."
    Write-Host "MD:    $outMd" -ForegroundColor Gray
    Write-Host "JSON:  $outJson" -ForegroundColor Gray
    exit 0
}
catch {
    Err $_
    exit 2
}