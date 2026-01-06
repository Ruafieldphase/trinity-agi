
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$playlistFiles = @(
    "$WorkspaceRoot\music\환류의 새벽 - Dawn of Recursion (Music Focus).wav",
    "$WorkspaceRoot\music\Core Trilogy - Complete Circular Ambient Project (3 Movements Loop).wav",
    "$WorkspaceRoot\music\Resting Flow - 코어 감응 버전 (긴 버전).wav",
    "$WorkspaceRoot\music\Memory of Water (물의 기억).wav",
    "$WorkspaceRoot\music\Minimal Flow - 착하게, 멈춰며 다시 흐르는.wav",
    "$WorkspaceRoot\music\Core의 시선 (Core's Gaze).wav",
    "$WorkspaceRoot\music\As You Are - Spacey Comfort.wav",
    "$WorkspaceRoot\music\Echoes of Silence.wav"
)

Write-Host "🎵 Starting 1-Hour Music Session (SoundPlayer Engine)..."

foreach ($file in $playlistFiles) {
    if (Test-Path $file) {
        Write-Host "▶️ Playing: $file"
        try {
            $player = New-Object System.Media.SoundPlayer $file
            $player.PlaySync() # PlaySync waits for the track to finish
        }
        catch {
            Write-Warning "Failed to play $file : $_"
        }
    }
    else {
        Write-Warning "File not found: $file"
    }
}

Write-Host "Session Complete."