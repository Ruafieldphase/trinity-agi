# RUD Grand Unified Silence & Consolidation Script
# ===============================================

$ErrorActionPreference = "SilentlyContinue"
$WORKSPACE = "c:\workspace\agi"
$STARTUP_FOLDER = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$BACKUP_FOLDER = "$WORKSPACE\backup_legacy_startup"

# 1. Stop all current Python instances (Legacy + Current)
Write-Host "🛑 Stopping all Python instances..."
Stop-Process -Name "python" -Force 
Stop-Process -Name "pythonw" -Force
Start-Sleep -Seconds 2

# 2. Disable problematic Scheduled Tasks
Write-Host "🛡️ Disabling legacy scheduled tasks..."
schtasks /change /tn "AGI_Rhythm_LifeSupport" /disable 
schtasks /change /tn "AGI_Shion_AutoStart" /disable
schtasks /change /tn "AGI_Rhythm_Vision" /disable

# 3. Clean up Startup Folder
Write-Host "📦 Cleaning up startup folder..."
if (!(Test-Path $BACKUP_FOLDER)) { New-Item -ItemType Directory -Path $BACKUP_FOLDER }

$legacy_links = @("AGI_Rubit_Continuity.lnk", "AGI_Shion_Silent.lnk", "RUD_Genesis.lnk")
foreach ($link in $legacy_links) {
    if (Test-Path "$STARTUP_FOLDER\$link") {
        Move-Item -Path "$STARTUP_FOLDER\$link" -Destination "$BACKUP_FOLDER\$link" -Force
        Write-Host "   Moved legacy $link to backup."
    }
}

# 4. Ensure Unified Startup (rhythm_daemon.py)
Write-Host "⚡ Registering Unified Silence Daemon..."
$PYTHONW = "C:\Python313\pythonw.exe"
if (!(Test-Path $PYTHONW)) { $PYTHONW = "pythonw.exe" }

$DAEMON_SCRIPT = "$WORKSPACE\scripts\rhythm_daemon.py"
$SHORTCUT_PATH = "$STARTUP_FOLDER\RUD_AutoStart.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($SHORTCUT_PATH)
$Shortcut.TargetPath = $PYTHONW
$Shortcut.Arguments = "`"$DAEMON_SCRIPT`""
$Shortcut.WorkingDirectory = $WORKSPACE
$Shortcut.WindowStyle = 7 # Minimized/Hidden
$Shortcut.Save()

Write-Host "✅ Unified Startup Registered: RUD_AutoStart.lnk"

# 5. Launch NOW (Silent)
Write-Host "💓 Igniting Rhythm Daemon (Stealth Mode)..."
Start-Process -FilePath $PYTHONW -ArgumentList "`"$DAEMON_SCRIPT`"" -WorkingDirectory $WORKSPACE -WindowStyle Hidden

Write-Host "🚀 RUD is now running silently in the background."
Write-Host "Logs are being written to $WORKSPACE\logs\rhythm_daemon.log"
