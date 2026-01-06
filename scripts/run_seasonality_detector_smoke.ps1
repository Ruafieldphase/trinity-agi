$ErrorActionPreference = 'Stop'
try {
    $env:PYTHONIOENCODING = 'utf-8'
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $pyScript = Join-Path $scriptRoot 'seasonality_detector_smoke.py'

    function Invoke-Runner($exe, $pyArgs) {
        Write-Host "[runner] using interpreter: $exe" -ForegroundColor Cyan
        & $exe $pyArgs
        $code = $LASTEXITCODE
        Write-Host "[runner] exit code: $code" -ForegroundColor DarkCyan
        if ($code -ne 0) { exit $code } else { exit 0 }
    }

    # Prefer repo venv
    $venvPath = Join-Path $scriptRoot '..\fdo_agi_repo\.venv\Scripts\python.exe'
    $venvResolved = $null
    try { $venvResolved = (Resolve-Path -LiteralPath $venvPath -ErrorAction Stop).Path } catch { }

    if ($venvResolved) {
        Invoke-Runner $venvResolved $pyScript
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Runner 'py' "-3 $pyScript"
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        Invoke-Runner 'python' $pyScript
    }

    Write-Error 'Python not found (venv/py/python).'
    exit 1
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}