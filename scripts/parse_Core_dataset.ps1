param(
    [string]$InputJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\Core\origin\conversations.json",
    [string]$OutJsonl = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\Core\core_conversations_flat.jsonl",
    [switch]$ExportCsv,
    [string]$OutCsv,
    [switch]$SkipExisting
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Get-Python {
    $candidates = @(
        (Join-Path (Join-Path $WorkspaceRoot "LLM_Unified\.venv\Scripts") 'python.exe'),
        (Join-Path (Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts") 'python.exe'),
        'python'
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }
    return $null
}

$inputPath = [System.IO.Path]::GetFullPath($InputJson)
$outJsonPath = [System.IO.Path]::GetFullPath($OutJsonl)
$outCsvPath = $null

if ($ExportCsv) {
    if ([string]::IsNullOrWhiteSpace($OutCsv)) {
        $outCsvPath = [System.IO.Path]::ChangeExtension($outJsonPath, '.csv')
    }
    else {
        $outCsvPath = [System.IO.Path]::GetFullPath($OutCsv)
    }
}

if ($SkipExisting -and (Test-Path -LiteralPath $outJsonPath)) {
    Write-Warn "Output already present. Use -SkipExisting:$false to regenerate."
    return
}

if (!(Test-Path -LiteralPath $inputPath)) {
    throw "Input not found: $inputPath"
}

$py = Get-Python
if (-not $py) {
    throw 'Python interpreter not found. Activate repo venv or install Python.'
}

Write-Info "Core dataset parser"
Write-Info " Input : $inputPath"
Write-Info " Output: $outJsonPath"

$args = @(
    "`"$($PSScriptRoot)\Core_parse.py`"",
    '--input', "`"$inputPath`"",
    '--out-jsonl', "`"$outJsonPath`""
)

if ($outCsvPath) {
    Write-Info " CSV   : $outCsvPath"
    $args += @('--out-csv', "`"$outCsvPath`"")
}

& $py $args

if ($LASTEXITCODE -ne 0) {
    throw "Core parser failed with exit code $LASTEXITCODE"
}

if (Test-Path -LiteralPath $outJsonPath) {
    $lineCount = (Get-Content -LiteralPath $outJsonPath | Measure-Object -Line).Lines
    Write-Ok "JSONL ready (${lineCount} rows)"
}

if ($outCsvPath -and (Test-Path -LiteralPath $outCsvPath)) {
    Write-Ok "CSV ready: $outCsvPath"
}

Write-Ok 'Done.'