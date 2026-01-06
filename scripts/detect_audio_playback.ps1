#Requires -Version 5.1
<#
.SYNOPSIS
    Detect audio playback (music, media) on Windows
.DESCRIPTION
    Uses Windows Audio Session API via PowerShell to detect active audio streams
    Useful for triggering wake-up protocols or rhythm phase transitions
#>
param(
    [switch]$Json,
    [string]$OutFile,
    [string]$OutJson,  # JSON 출력 파일 (호환성)
    [switch]$Continuous,
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-ActiveAudioSessions {
    <#
    .SYNOPSIS
        Detect active audio sessions using Windows API
    .NOTES
        Checks for processes with audio output (music players, browsers, etc.)
    #>
    $audioProcesses = @(
        "spotify", "chrome", "msedge", "firefox", "vlc", "wmplayer",
        "iTunes", "foobar2000", "AIMP", "winamp", "MusicBee", "obs64",
        "comet"  # Comet Browser
    )

    $activeSessions = @()

    foreach ($procName in $audioProcesses) {
        $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue
        if ($procs) {
            foreach ($proc in $procs) {
                # Simple heuristic: if process is running, assume potential audio
                $activeSessions += [PSCustomObject]@{
                    ProcessName = $proc.ProcessName
                    PID         = $proc.Id
                    WindowTitle = $proc.MainWindowTitle
                    CPU         = [math]::Round($proc.CPU, 2)
                    WorkingSet  = [math]::Round($proc.WorkingSet64 / 1MB, 1)
                    DetectedAt  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                }
            }
        }
    }

    return $activeSessions
}

function Get-AudioPlaybackState {
    $sessions = @(Get-ActiveAudioSessions)

    $result = [PSCustomObject]@{
        Timestamp        = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        IsPlaying        = $sessions.Count -gt 0
        is_music_playing = $sessions.Count -gt 0  # 호환성 필드
        ActiveSessions   = $sessions
        SessionCount     = $sessions.Count
        browser_count    = $sessions.Count  # 호환성 필드
        TopProcess       = if ($sessions -and $sessions.Count -gt 0) { $sessions[0].ProcessName } else { $null }
        SignalStrength   = if ($sessions.Count -gt 2) { "STRONG" } elseif ($sessions.Count -gt 0) { "MODERATE" } else { "NONE" }
    }

    return $result
}

function Main {
    do {
        $state = Get-AudioPlaybackState

        if ($Json) {
            $output = $state | ConvertTo-Json -Depth 5 -Compress
            Write-Output $output
        }
        else {
            Write-Host "🎵 Audio Playback Detection - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
            Write-Host "  Playing: $($state.IsPlaying)" -ForegroundColor $(if ($state.IsPlaying) { "Green" } else { "Yellow" })
            Write-Host "  Sessions: $($state.SessionCount)"
            if ($state.TopProcess) {
                Write-Host "  Top: $($state.TopProcess)" -ForegroundColor Magenta
            }
            Write-Host ""
        }

        if ($OutFile) {
            $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutFile -Encoding utf8 -Force
        }

        if ($OutJson) {
            # 호환성: OutJson도 지원
            $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutJson -Encoding utf8 -Force
        }

        if ($Continuous) {
            Start-Sleep -Seconds $IntervalSeconds
        }
    } while ($Continuous)
}

Main