# Reindex Vector Store for Hybrid RAG
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/reindex_vector_store.ps1 [-RootDir <path>]

param(
    [string]$RootDir = (Split-Path -Parent $PSCommandPath)
)

Write-Host "[Reindex] RootDir: $RootDir"

# Prefer repo python if available, else fallback to system python
$ws = Split-Path -Parent $RootDir
$pythonCandidates = @(
    (Join-Path $ws "LLM_Unified\.venv\Scripts\python.exe"),
    (Join-Path $ws "fdo_agi_repo\.venv\Scripts\python.exe"),
    (Join-Path $ws ".venv\Scripts\python.exe"),
    "python"
)

$pythonExe = $null
foreach ($p in $pythonCandidates) {
    if (Test-Path $p -ErrorAction SilentlyContinue) {
        & $p --version 2>$null
        if ($LASTEXITCODE -eq 0) { $pythonExe = $p; break }
    }
}

if (-not $pythonExe) {
    Write-Error "Python interpreter not found. Ensure Python is installed or venv exists."
    exit 1
}

# Change to repo root (assume this script lives under scripts/)
$repoRoot = (Resolve-Path (Join-Path $RootDir ".."))
Push-Location $repoRoot

Write-Host "[Reindex] Using Python: $pythonExe"

# Run indexer; it reads config for vector_store path if implemented
# Try module invocation first; fallback to script path
$cmds = @(
    "-m fdo_agi_repo.tools.rag.index_docs",
    "fdo_agi_repo\\tools\\rag\\index_docs.py"
)

$success = $false
foreach ($c in $cmds) {
    Write-Host "[Reindex] Running: $pythonExe $c" -ForegroundColor Cyan
    & $pythonExe $c
    if ($LASTEXITCODE -eq 0) { $success = $true; break }
}

Pop-Location

if ($success) {
    Write-Host "[Reindex] Completed successfully." -ForegroundColor Green
    exit 0
}
else {
    Write-Error "[Reindex] Failed. See output above."
    exit 1
}
