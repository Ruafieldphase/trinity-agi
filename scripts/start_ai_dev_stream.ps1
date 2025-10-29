# AI ê°œë°œ+ë°©ì†¡ ?µí•© ?Œí¬?Œë¡œ???°ì²˜ (VS Code + OBS + ëª¨ë‹ˆ?°ë§)
# ?¬ìš© ?ˆì‹œ:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_ai_dev_stream.ps1 -OBSProfile "Default" -Scene "VS Code Stream" -OpenYouTubeStudio
#   (ì²´í¬ ?„ìš©) powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_ai_dev_stream.ps1 -CheckOnly

param(
    [switch]$CheckOnly,                 # ?¤ì œ ?¤í–‰ ?†ì´ ?ê?ë§??˜í–‰
    [switch]$AutoStartStreaming,        # OBS ?¤í–‰ ???ë™ ë°©ì†¡ ?œì‘ (OBS???¤íŠ¸ë¦????„ìš”)
    [switch]$OpenVSCode,                # VS Code ?ë™ ?¤í–‰ (ê¸°ë³¸: true)
    [switch]$RunQuickStatus,            # ?€?œë³´???íƒœ ?¤ëƒ…???¤í–‰ (ê¸°ë³¸: true)
    [switch]$OpenYouTubeStudio,         # YouTube Studio ?˜ì´ì§€ ?´ê¸°
    [string]$WorkspacePath = "C:\workspace\agi",  # VS Code ?‘ì—… ?´ë”
    [string]$OBSProfile = "Default",   # OBS ?„ë¡œ???´ë¦„
    [string]$Scene = "VS Code Stream"  # OBS ???´ë¦„
)

$ErrorActionPreference = "Stop"

Write-Host "=== AI Dev + Streaming Orchestrator ===" -ForegroundColor Cyan
Write-Host ("Time: {0}" -f (Get-Date).ToString("s")) -ForegroundColor DarkGray

# ?¤ìœ„ì¹?ê¸°ë³¸ê°??¤ì • (ëª…ì‹œ?˜ì? ?Šìœ¼ë©?trueë¡?ê°„ì£¼)
if (-not $PSBoundParameters.ContainsKey('OpenVSCode')) { $OpenVSCode = $true }
if (-not $PSBoundParameters.ContainsKey('RunQuickStatus')) { $RunQuickStatus = $true }

# 1) VS Code ?¤í–‰
if ($OpenVSCode) {
    try {
        $vsProc = Get-Process -Name "Code" -ErrorAction SilentlyContinue
        if (-not $vsProc) {
            Write-Host "[Start] VS Code: $WorkspacePath" -ForegroundColor Cyan
            Start-Process -FilePath "code" -ArgumentList @("-n", $WorkspacePath)
        } else {
            Write-Host "[OK] VS Code already running" -ForegroundColor Green
        }
    } catch {
    Write-Host "[Warn] VS Code launch check issue: $_" -ForegroundColor Yellow
    }
}

# 2) ëª¨ë‹ˆ?°ë§ ?¤ëƒ…???¤í–‰ (? íƒ)
if ($RunQuickStatus) {
    try {
        $quickStatus = Join-Path $WorkspacePath "scripts/quick_status.ps1"
        if (Test-Path $quickStatus) {
            Write-Host "[Start] Generate system/channel snapshot" -ForegroundColor Cyan
            $outJson = Join-Path $WorkspacePath "outputs/quick_status_latest.json"
            powershell -NoProfile -ExecutionPolicy Bypass -File $quickStatus -OutJson $outJson | Out-Null
            Write-Host "[OK] Snapshot written ??$outJson" -ForegroundColor Green
        } else {
            Write-Host "[Warn] quick_status.ps1 not found: $quickStatus" -ForegroundColor Yellow
        }
    } catch {
    Write-Host "[Warn] Snapshot generation error: $_" -ForegroundColor Yellow
    }
}

# ì²´í¬ ?„ìš© ëª¨ë“œë©??¬ê¸°??ì¢…ë£Œ
if ($CheckOnly) {
    Write-Host "[OK] Check-only completed. Skipping OBS launch." -ForegroundColor Green
    exit 0
}

# 3) OBS ?œì‘ (?„ìš” ???ë™ ë°©ì†¡ ?œì‘)
try {
    $obsScript = Join-Path $WorkspacePath "scripts/obs_quick_setup.ps1"
    if (-not (Test-Path $obsScript)) {
        throw "obs_quick_setup.ps1 not found: $obsScript"
    }
    $obsArgsList = @()
    if ($AutoStartStreaming) { $obsArgsList += "-AutoStartStreaming" }
    $obsArgsList += @("-OBSProfile", $OBSProfile, "-Scene", $Scene)

    Write-Host ("[Start] OBS (Profile='{0}', Scene='{1}', AutoStart={2})" -f $OBSProfile, $Scene, $AutoStartStreaming) -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File $obsScript @obsArgsList
    Write-Host "[OK] OBS invoked" -ForegroundColor Green
} catch {
    Write-Host "[Error] OBS start failed: $_" -ForegroundColor Red
}

# 4) YouTube Studio ?´ê¸° (? íƒ)
if ($OpenYouTubeStudio) {
    try {
    Write-Host "[Start] Open YouTube Studio" -ForegroundColor Cyan
        Start-Process "https://studio.youtube.com"
    Write-Host "[OK] Browser opened" -ForegroundColor Green
    } catch {
    Write-Host "[Warn] Failed to open browser: $_" -ForegroundColor Yellow
    }
}

Write-Host "=== Ready: Start streaming in OBS and continue AI coding in VS Code ===" -ForegroundColor Cyan
