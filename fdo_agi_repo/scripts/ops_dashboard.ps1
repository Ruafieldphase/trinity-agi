param(
    [switch]$Json,
    [double]$Hours = 1.0
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

# ops_dashboard.py 실행
$DashboardScript = Join-Path $RepoRoot "scripts\ops_dashboard.py"

$PythonArgs = @()
if ($Json) {
    $PythonArgs += "--json"
}
$PythonArgs += "--hours"
$PythonArgs += $Hours.ToString()

Write-Host "🚀 Running Ops Dashboard..." -ForegroundColor Cyan
& $Python $DashboardScript @PythonArgs

exit $LASTEXITCODE
