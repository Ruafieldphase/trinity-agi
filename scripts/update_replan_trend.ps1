param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor Cyan }
}

function Write-Err($msg) {
    Write-Host $msg -ForegroundColor Red
}

try {
    $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
    $py = Join-Path $ws 'LLM_Unified/.venv/Scripts/python.exe'
    $script = Join-Path $ws 'scripts/check_replan_trend.py'

    if (-not (Test-Path -LiteralPath $script)) {
        Write-Err "check_replan_trend.py not found: $script"
        exit 1
    }

    if (Test-Path -LiteralPath $py) {
        Write-Info "Using venv Python: $py"
        & $py $script
    }
    else {
        Write-Info "Using system Python"
        python $script
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}