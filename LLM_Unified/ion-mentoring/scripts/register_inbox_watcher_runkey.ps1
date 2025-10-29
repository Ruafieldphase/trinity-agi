param(
    [string]$TaskName = 'IonInboxWatcher',
    [string]$Agents = 'all',
    [string]$WorkspaceFolder = 'D:\nas_backup'
)

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path -Path $WorkspaceFolder -ChildPath 'LLM_Unified\ion-mentoring\scripts\run_inbox_watcher.ps1'
if (-not (Test-Path $scriptPath)) {
    throw "Watcher script not found: $scriptPath"
}

# Compose the command to run at user logon (hidden window)
$cmd = "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Agents $Agents"

$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
New-Item -Path $runKey -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty -Path $runKey -Name $TaskName -Value $cmd -Type String

Write-Host "Registered user logon startup for '$TaskName' via HKCU Run key."
Write-Host "Value: $cmd"