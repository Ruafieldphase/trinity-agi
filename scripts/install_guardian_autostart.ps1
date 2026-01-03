# Install Guardian Autostart (Startup Folder Method)
# 시작프로그램 폴더에 바로가기 생성


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$ProjectRoot = "$WorkspaceRoot"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "RhythmGuardian.lnk"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Guardian Autostart Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# VBS 스크립트로 바로가기 생성
$vbsScript = @"
Set WshShell = CreateObject("WScript.Shell")
Set Shortcut = WshShell.CreateShortcut("$ShortcutPath")
Shortcut.TargetPath = "pythonw"
Shortcut.Arguments = "$ProjectRoot\scripts\rhythm_guardian.py --interval 30"
Shortcut.WorkingDirectory = "$ProjectRoot"
Shortcut.Description = "Rhythm Guardian - AGI Single Heartbeat"
Shortcut.Save()
"@

$vbsPath = "$env:TEMP\create_shortcut.vbs"
$vbsScript | Out-File -FilePath $vbsPath -Encoding ASCII

cscript //nologo $vbsPath

if (Test-Path $ShortcutPath) {
    Write-Host ""
    Write-Host "[OK] Guardian autostart installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Location: $ShortcutPath" -ForegroundColor White
    Write-Host ""
    Write-Host "  Guardian will start automatically at Windows logon." -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Failed to create shortcut" -ForegroundColor Red
}

Remove-Item $vbsPath -Force -ErrorAction SilentlyContinue

Write-Host "========================================" -ForegroundColor Cyan