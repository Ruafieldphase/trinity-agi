$ErrorActionPreference = 'Stop'
try {
    $env:PYTHONIOENCODING = 'utf-8'
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $pyScript = Join-Path $scriptRoot 'scheduler_dry_run.py'

    # Defaults (03:00, 7 days)
    $argsList = @('--hour', '3', '--minute', '0', '--days', '7')

    # Prefer repo venv
    $venvPath = Join-Path $scriptRoot '..\fdo_agi_repo\.venv\Scripts\python.exe'
    $venvResolved = $null
    try { $venvResolved = (Resolve-Path -LiteralPath $venvPath -ErrorAction Stop).Path } catch { }

    if ($venvResolved) {
        & $venvResolved $pyScript @argsList
        exit $LASTEXITCODE
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 $pyScript @argsList
        exit $LASTEXITCODE
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        python $pyScript @argsList
        exit $LASTEXITCODE
    }

    Write-Error 'Python not found (venv/py/python).'
    exit 1
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}