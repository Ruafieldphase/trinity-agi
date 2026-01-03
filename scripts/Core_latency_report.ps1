param(
    [string]$InputJsonl = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\core_probe_history.jsonl",
    [string]$OutMd = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\core_latency_latest.md",
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\core_latency_summary.json",
    [switch]$Open
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Resolve-Python {
    param([string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ))
    $candidates = @(
        Join-Path $WorkspaceRoot 'LLM_Unified/.venv/Scripts/python.exe'),
    (Join-Path $WorkspaceRoot 'fdo_agi_repo/.venv/Scripts/python.exe')
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return 'python'
}

$root = Split-Path -Parent $PSScriptRoot
$py = Resolve-Python -WorkspaceRoot $root
$script = Join-Path $root 'scripts/summarize_core_latency.py'

if (-not (Test-Path -LiteralPath $script)) {
    Write-Host "Missing script: $script" -ForegroundColor Red
    exit 1
}

try {
    & $py $script --input $InputJsonl --out-md $OutMd --out-json $OutJson
}
catch {
    Write-Host "Failed to generate Core latency report: $_" -ForegroundColor Red
    exit 1
}

if ($Open) {
    if (Test-Path -LiteralPath $OutMd) {
        Write-Host "Opening: $OutMd" -ForegroundColor Green
        code $OutMd
    }
    else {
        Write-Host "Output not found: $OutMd" -ForegroundColor Yellow
    }
}