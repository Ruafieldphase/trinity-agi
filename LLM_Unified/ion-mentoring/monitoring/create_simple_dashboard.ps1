# Requires: gcloud CLI authenticated for the target project.
# Usage:
#   .\create_simple_dashboard.ps1 -ProjectId "naeda-genesis"

param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectId,

    [string] $DashboardConfig = "simple_dashboard.json"
)

$configPath = Join-Path $PSScriptRoot $DashboardConfig

if (-not (Test-Path $configPath)) {
    throw "Dashboard config not found: $configPath"
}

$gcloudCmd = $null
$cmd = Get-Command gcloud -ErrorAction SilentlyContinue
if ($cmd) {
    $gcloudCmd = $cmd.Source
}
if (-not $gcloudCmd) {
    $cmd = Get-Command gcloud.cmd -ErrorAction SilentlyContinue
    if ($cmd) {
        $gcloudCmd = $cmd.Source
    }
}
if (-not $gcloudCmd) {
    throw "gcloud CLI not found. Please install Google Cloud CLI and ensure it is in PATH."
}

Write-Output "Using gcloud executable: $gcloudCmd"

$arguments = @(
    "monitoring",
    "dashboards",
    "create",
    "--project=$ProjectId",
    "--config-from-file=$configPath"
)

Write-Output "Executing: $gcloudCmd $($arguments -join ' ')"

& $gcloudCmd @arguments
if ($LASTEXITCODE -ne 0) {
    throw "gcloud command failed with exit code $LASTEXITCODE"
}

Write-Output "Dashboard creation command finished successfully."
