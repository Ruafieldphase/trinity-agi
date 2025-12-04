param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = "YouTubeLearnerDaily",
    [string]$Time = "04:10",
    [switch]$OnStartup,
    [switch]$OnLogon,
    [string]$WorkspaceRoot = "C:\workspace\agi",
    [string]$Url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    [int]$MaxFrames = 1,
    [double]$FrameInterval = 30.0,
    [switch]$EnableOcr
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

$Runner = Join-Path $WorkspaceRoot 'scripts/run_youtube_learner.ps1'
if (-not (Test-Path $Runner)) {
    Write-Err "Runner script not found: $Runner"
    exit 1
}

if ($Register -and $Unregister) {
    Write-Err "Use either -Register or -Unregister, not both."
    exit 1
}

if (-not $Register -and -not $Unregister) {
    Write-Warn "No action specified. Use -Register or -Unregister."
    exit 2
}

$ocrFlag = if ($EnableOcr) { " -EnableOcr" } else { "" }
# 중복 방지: 오늘 이미 실행된 경우 스킵하도록 러너에 플래그 전달
$psArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -Url `"$Url`" -MaxFrames $MaxFrames -FrameInterval $FrameInterval -SkipIfToday$ocrFlag"

if ($Register) {
    Write-Info "Registering YouTube Learner task '$TaskName' at $Time daily"

    try {
        $today = Get-Date
        $runAt = Get-Date ("{0} {1}" -f $today.ToString('yyyy-MM-dd'), $Time)
        if ($runAt -lt $today) { $runAt = $runAt.AddDays(1) }
    }
    catch {
        Write-Err "Invalid -Time format. Use HH:mm (e.g., 04:10)."
        exit 1
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $psArgs -WorkingDirectory $WorkspaceRoot
    # 기본 매일 트리거
    $triggers = @()
    $triggers += ,(New-ScheduledTaskTrigger -Once -At $runAt -RepetitionInterval (New-TimeSpan -Days 1) -RepetitionDuration (New-TimeSpan -Days 3650))
    # 선택: 부팅 시, 로그인 시 보조 트리거 추가
    if ($OnStartup) {
        $triggers += ,(New-ScheduledTaskTrigger -AtStartup)
    }
    if ($OnLogon) {
        $triggers += ,(New-ScheduledTaskTrigger -AtLogOn)
    }
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$false -DontStopIfGoingOnBatteries:$false -StartWhenAvailable -WakeToRun
$settings.Hidden = $true
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    try {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Existing task '$TaskName' removed."
        }
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal | Out-Null
        Write-Info "Task '$TaskName' registered for daily run at $Time."
        Write-Info "Trigger manually with: Start-ScheduledTask -TaskName '$TaskName'"
    }
    catch {
        Write-Err "Failed to register task: $($_.Exception.Message)"
        exit 1
    }
}
elseif ($Unregister) {
    Write-Info "Unregistering YouTube Learner task '$TaskName'"
    try {
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Info "Task '$TaskName' removed."
        }
        else {
            Write-Warn "Task '$TaskName' not found. Nothing to do."
        }
    }
    catch {
        Write-Err "Failed to unregister task: $($_.Exception.Message)"
        exit 1
    }
}
