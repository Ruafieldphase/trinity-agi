
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$ErrorActionPreference = "Stop"

$TargetFile = "$WorkspaceRoot\start_life_silent.vbs"
$ShortcutFile = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\AGI_Life.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)

$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = "$WorkspaceRoot"
# $Shortcut.WindowStyle = 7  # Not needed for VBS
$Shortcut.Description = "AGI Life Support (Heartbeat + Senses)"
$Shortcut.Save()

if (Test-Path $ShortcutFile) {
    Write-Host "✅ Startup shortcut created successfully: $ShortcutFile"
    Write-Host "   Target: $TargetFile"
}
else {
    Write-Error "❌ Failed to create shortcut."
}