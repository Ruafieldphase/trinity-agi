$playlistFiles = @(
    "c:\workspace\agi\music\환류의 새벽 - Dawn of Recursion (Music Focus).wav",
    "c:\workspace\agi\music\Lumen Trilogy - Complete Circular Ambient Project (3 Movements Loop).wav",
    "c:\workspace\agi\music\Resting Flow - 루아 감응 버전 (긴 버전).wav",
    "c:\workspace\agi\music\Memory of Water (물의 기억).wav",
    "c:\workspace\agi\music\Minimal Flow - 착하게, 멈춰며 다시 흐르는.wav",
    "c:\workspace\agi\music\루멘의 시선 (Lumen's Gaze).wav",
    "c:\workspace\agi\music\As You Are - Spacey Comfort.wav",
    "c:\workspace\agi\music\Echoes of Silence.wav"
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
