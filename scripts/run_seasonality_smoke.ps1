$ErrorActionPreference = 'Stop'
try {
    $env:PYTHONIOENCODING = 'utf-8'
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $pyScript = Join-Path $scriptRoot 'seasonality_smoke_test.py'

    # Prefer repo venv
    $venvPath = Join-Path $scriptRoot '..\fdo_agi_repo\.venv\Scripts\python.exe'
    $venvResolved = $null
    try { $venvResolved = (Resolve-Path -LiteralPath $venvPath -ErrorAction Stop).Path } catch { }

    if ($venvResolved) {
        & $venvResolved $pyScript
        exit $LASTEXITCODE
    }

    # Fallback to py launcher
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 $pyScript
        exit $LASTEXITCODE
    }

    # Fallback to python in PATH
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python $pyScript
        exit $LASTEXITCODE
    }

    Write-Error 'Python not found (venv/py/python).'
    exit 1
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
