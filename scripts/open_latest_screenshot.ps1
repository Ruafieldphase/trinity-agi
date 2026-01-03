param(
    [string]$Folder = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs",
    [string]$Pattern = "screenshot_*.png"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
try {
    $path = Resolve-Path -LiteralPath $Folder -ErrorAction Stop
    $files = Get-ChildItem -LiteralPath $path -Filter $Pattern -File | Sort-Object -Property LastWriteTime -Descending
    if (-not $files -or $files.Count -eq 0) {
        Write-Host "No screenshot files found in: $path" -ForegroundColor Yellow
        exit 0
    }
    $latest = $files[0]
    Write-Host ("Opening: {0}" -f $latest.FullName) -ForegroundColor Green
    Start-Process -FilePath $latest.FullName | Out-Null
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}