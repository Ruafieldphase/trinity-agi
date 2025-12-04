# Schedule or remove nightly RAG vector store reindex
# Usage examples:
#   Register daily 03:10:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/schedule_reindex.ps1 -Register -Time "03:10"
#   Unregister:            powershell -NoProfile -ExecutionPolicy Bypass -File scripts/schedule_reindex.ps1 -Unregister
#   Custom task name:      ... -TaskName "Gitco_RAG_Reindex_Nightly"

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "03:10",
    [string]$TaskName = "Gitco_RAG_Reindex_Nightly"
)

function Get-RepoRoot {
    $here = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $here ".."))
}

$repo = Get-RepoRoot
$scriptPath = Join-Path $repo "scripts\reindex_vector_store.ps1"

if ($Unregister) {
    Write-Host "[Schedule] Unregistering task: $TaskName"
    schtasks.exe /Delete /TN $TaskName /F | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[Schedule] Unregistered successfully." -ForegroundColor Green
        exit 0
    }
    else {
        Write-Error "[Schedule] Failed to unregister."
        exit 1
    }
}

if (-not $Register) {
    Write-Error "Specify -Register to create or -Unregister to remove the scheduled task."
    exit 2
}

if (-not (Test-Path $scriptPath)) {
    Write-Error "Reindex script not found: $scriptPath"
    exit 1
}

# Build command: run powershell with our reindex script
$action = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

Write-Host "[Schedule] Registering task: $TaskName at $Time daily"
# Create or update the scheduled task
schtasks.exe /Create /TN $TaskName /TR $action /SC DAILY /ST $Time /RL LIMITED /F | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[Schedule] Registered successfully." -ForegroundColor Green
    exit 0
}
else {
    Write-Error "[Schedule] Failed to register."
    exit 1
}
