#Requires -Version 5.1
<#
.SYNOPSIS
    Adaptive Music Session Player (Windowless)
    
.DESCRIPTION
    Scans c:\workspace\agi\music for .wav files matching current system state keywords.
    Plays them sequentially using System.Media.SoundPlayer (No GUI).
    
.PARAMETER Keywords
    Comma-separated keywords to filter music (default: "Resonance,Flow,Dawn,Lumen,Light")
#>

param(
    [string]$Keywords = "Resonance,Flow,Dawn,Lumen,Light,Water"
)

$musicDir = "c:\workspace\agi\music"
$keywordList = $Keywords -split ","

Write-Host "🎵 Starting Adaptive Music Session..." -ForegroundColor Cyan
Write-Host "   Target Keywords: $Keywords" -ForegroundColor Gray

if (-not (Test-Path $musicDir)) {
    Write-Warning "Music directory not found: $musicDir"
    exit
}

# Get all wav files
$files = Get-ChildItem -Path $musicDir -Filter "*.wav" -Recurse

# Filter by keywords
$playlist = @()
foreach ($file in $files) {
    foreach ($k in $keywordList) {
        if ($file.Name -match $k.Trim()) {
            $playlist += $file
            break
        }
    }
}

if ($playlist.Count -eq 0) {
    Write-Warning "No matching music found. Playing random tracks."
    $playlist = $files | Get-Random -Count 5
} else {
    # Shuffle
    $playlist = $playlist | Sort-Object {Get-Random}
}

Write-Host "`n📋 Playlist ($($playlist.Count) tracks):" -ForegroundColor Green
$playlist | ForEach-Object { Write-Host "   - $($_.Name)" }

Write-Host "`n▶️ Playing..." -ForegroundColor Cyan

foreach ($track in $playlist) {
    Write-Host "   Now Playing: $($track.Name)" -ForegroundColor Yellow
    try {
        $player = New-Object System.Media.SoundPlayer $track.FullName
        $player.PlaySync()
    }
    catch {
        Write-Warning "   Failed to play: $_"
    }
    Start-Sleep -Seconds 1
}

Write-Host "`n✅ Session Complete." -ForegroundColor Green
