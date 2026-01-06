param(
    [int]$DelayMinutes = 5,
    [string]$Workspace = "${PSScriptRoot}\.."
)

$ErrorActionPreference = 'Stop'

$sleepSeconds = [int]([double]$DelayMinutes * 60)
Start-Sleep -Seconds $sleepSeconds

& (Join-Path $PSScriptRoot 'launch_vscode_after_logon.ps1') -Workspace $Workspace