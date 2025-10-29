param(
    [string]$TaskName = 'IonInboxWatcher'
)

$ErrorActionPreference = 'Stop'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
if (Get-ItemProperty -Path $runKey -Name $TaskName -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path $runKey -Name $TaskName -ErrorAction Stop
    Write-Host "Removed user logon startup for '$TaskName' from HKCU Run key."
}
else {
    Write-Host "No Run key entry found for '$TaskName'."
}