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

$wmp = New-Object -ComObject WMPlayer.OCX
$wmp.settings.volume = 100
$wmp.settings.autoStart = $true

# Create a new playlist
$playlist = $wmp.newPlaylist("RestSession", "")

foreach ($file in $playlistFiles) {
    if (Test-Path $file) {
        $media = $wmp.newMedia($file)
        $playlist.appendItem($media)
        Write-Host "Added: $file"
    }
    else {
        Write-Warning "File not found: $file"
    }
}

$wmp.currentPlaylist = $playlist
$wmp.controls.play()

Write-Host "🎵 Starting 1-Hour Music Session..."
Write-Host "Volume: 100%"

# Keep script alive while playing
while ($wmp.playState -ne 1) {
    # 1 = Stopped
    Start-Sleep -Seconds 5
    # Optional: Check if user wants to stop (could implement file flag check)
}

Write-Host "Session Complete."
