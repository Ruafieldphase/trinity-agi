# Simple Rhythm Sync from Linux Brain to Windows Body
# Uses SCP to pull latest state files


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$HOST = "bino@192.168.119.128"
$REMOTE_DIR = "/home/bino/agi/outputs"
$LOCAL_DIR = "$WorkspaceRoot\outputs"

# Create local dir if not exists
if (!(Test-Path $LOCAL_DIR)) {
    New-Item -ItemType Directory -Path $LOCAL_DIR -Force | Out-Null
}

Write-Host "🔄 Syncing Rhythm from Linux Brain..." -ForegroundColor Cyan

# Sync thought stream
$thoughtFile = "$REMOTE_DIR/thought_stream_latest.json"
scp ${HOST}:$thoughtFile $LOCAL_DIR\ 2>$null

# Sync feeling
$feelingFile = "$REMOTE_DIR/feeling_latest.json"  
scp ${HOST}:$feelingFile $LOCAL_DIR\ 2>$null

Write-Host "✅ Sync complete" -ForegroundColor Green