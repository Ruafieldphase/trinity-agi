param(
    [switch]$ForceLowQuality,
    [string]$ScriptPath = "D:\\nas_backup\\test_phase5_integration.py"
)

# Resolve venv python
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonPath = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Error "Python not found: $pythonPath"
    exit 1
}

# Preserve current env
$oldRag = $env:RAG_DISABLE
$oldCorr = $env:CORRECTIONS_ENABLED

try {
    if ($ForceLowQuality) {
        $env:RAG_DISABLE = '1'
        $env:CORRECTIONS_ENABLED = 'true'
    }

    & $pythonPath $ScriptPath
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Error "Integration test failed with exit code $exitCode"
        exit $exitCode
    }
}
finally {
    if ($null -eq $oldRag) { Remove-Item Env:\RAG_DISABLE -ErrorAction SilentlyContinue } else { $env:RAG_DISABLE = $oldRag }
    if ($null -eq $oldCorr) { Remove-Item Env:\CORRECTIONS_ENABLED -ErrorAction SilentlyContinue } else { $env:CORRECTIONS_ENABLED = $oldCorr }
}

Write-Output "Phase5 integration test completed successfully."