param(
    [switch]$NoAlert,
    [switch]$NoDefaultExcludes,
    [string[]]$ExcludePrefix
)

$ErrorActionPreference = 'Stop'

# Repo root 찾기
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# Python 실행 파일 결정
if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
}
else {
    Write-Error "Python not found (checked venv and system)"
    exit 1
}

# alert_system.py 실행
$AlertScript = Join-Path $RepoRoot "scripts\alert_system.py"

$PythonArgs = @()
if ($NoAlert) {
    $PythonArgs += "--no-alert"
}
if ($NoDefaultExcludes) {
    $PythonArgs += "--no-default-excludes"
}
if ($ExcludePrefix) {
    foreach ($prefix in $ExcludePrefix) {
        if ([string]::IsNullOrWhiteSpace($prefix)) { continue }
        $PythonArgs += "--exclude-prefix"
        $PythonArgs += $prefix
    }
}

Write-Host "🚨 Running Health Check & Alert System..." -ForegroundColor Yellow
& $Python $AlertScript @PythonArgs

exit $LASTEXITCODE
