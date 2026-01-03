# AI 개발+방송 ?합 ?크?로???처 (VS Code + OBS + 모니?링)
# ?용 ?시:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_ai_dev_stream.ps1 -OBSProfile "Default" -Scene "VS Code Stream" -OpenYouTubeStudio
#   (체크 ?용) powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_ai_dev_stream.ps1 -CheckOnly

param(
    [switch]$CheckOnly,                 # ?제 ?행 ?이 ????행
    [switch]$AutoStartStreaming,        # OBS ?행 ???동 방송 ?작 (OBS???트????요)
    [switch]$OpenVSCode,                # VS Code ?동 ?행 (기본: true)
    [switch]$RunQuickStatus,            # ??보???태 ?냅???행 (기본: true)
    [switch]$OpenYouTubeStudio,         # YouTube Studio ?이지 ?기
    [string]$WorkspacePath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )",  # VS Code ?업 ?더
    [string]$OBSProfile = "Default",   # OBS ?로???름
    [string]$Scene = "VS Code Stream"  # OBS ???름
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

Write-Host "=== AI Dev + Streaming Orchestrator ===" -ForegroundColor Cyan
Write-Host ("Time: {0}" -f (Get-Date).ToString("s")) -ForegroundColor DarkGray

# ?위?기본??정 (명시?? ?으?true?간주)
if (-not $PSBoundParameters.ContainsKey('OpenVSCode')) { $OpenVSCode = $true }
if (-not $PSBoundParameters.ContainsKey('RunQuickStatus')) { $RunQuickStatus = $true }

# 1) VS Code ?행
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

# 2) 모니?링 ?냅???행 (?택)
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

# 체크 ?용 모드??기??종료
if ($CheckOnly) {
    Write-Host "[OK] Check-only completed. Skipping OBS launch." -ForegroundColor Green
    exit 0
}

# 3) OBS ?작 (?요 ???동 방송 ?작)
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

# 4) YouTube Studio ?기 (?택)
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