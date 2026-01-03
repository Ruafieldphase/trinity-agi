param(
    [int]$Hours = 24,
    [switch]$Open
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$pyRepo = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'
$pyRepoAlt = Join-Path $workspace 'fdo_agi_repo/.venv/Scripts/python.exe'

$python = $null
if (Test-Path -LiteralPath $pyRepo) {
    $python = $pyRepo
}
elseif (Test-Path -LiteralPath $pyRepoAlt) {
    $python = $pyRepoAlt
}
else {
    $python = 'python'
}

$scriptPath = Join-Path $workspace 'scripts/generate_context_snapshot.py'

& $python $scriptPath --hours $Hours | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Open) {
    $md = Join-Path $workspace 'outputs/context_snapshot.md'
    $json = Join-Path $workspace 'outputs/context_snapshot.json'
    if (Test-Path -LiteralPath $md) {
        code $md
    }
    elseif (Test-Path -LiteralPath $json) {
        code $json
    }
    else {
        Write-Host 'No context snapshot outputs found to open.' -ForegroundColor Yellow
    }
}