# ChatOps Router: natural language control for OBS & YouTube bot
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass `
#     -File scripts/chatops_router.ps1 `
#     -Say "start the stream"

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Say
)

# Do not abort the whole router when a sub-command fails.
$ErrorActionPreference = 'Continue'

# Ensure UTF-8 console so Korean prompts render correctly in legacy hosts.
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $global:OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

function Info([string]$Message) { Write-Host $Message -ForegroundColor Cyan }
function Ok([string]$Message) { Write-Host $Message -ForegroundColor Green }
function Warn([string]$Message) { Write-Host $Message -ForegroundColor Yellow }
function Err([string]$Message) { Write-Host $Message -ForegroundColor Red }

$utterance = $Say.Trim()
$workspace = Split-Path -Parent $PSScriptRoot

# Discover the concrete Python executable that 'py -3' resolves to, for consistency across calls
$script:pythonExe = $null
try {
    $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $resolved) { $script:pythonExe = $resolved.Trim() }
}
catch {}

function Invoke-ObsHelper {
    param(
        [string]$Command,
        [string]$Value
    )
    try {
        $scriptPath = (Join-Path $workspace 'scripts/obs_ws_control.py')
        if ($script:pythonExe -and $script:pythonExe.EndsWith('.exe')) {
            $args = @($scriptPath, $Command)
            if ($Value) { $args += $Value }
            & $script:pythonExe @args 2>$null
        }
        else {
            $args = @('-3', $scriptPath, $Command)
            if ($Value) { $args += $Value }
            & py @args 2>$null
        }
        return $LASTEXITCODE
    }
    catch {
        Warn "OBS control failed: $_"
        return 2
    }
}

function Start-Stream {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'scripts/start_ai_dev_stream.ps1') `
            -OpenYouTubeStudio `
            -AutoStartStreaming
        return 0
    }
    catch {
        Err "Failed to start the broadcast: $_"
        return 2
    }
}

function Stop-Stream {
    $code = Invoke-ObsHelper -Command 'stop'
    if ($code -ne 0) {
        Warn 'OBS may not be connected or the stream is already stopped.'
    }
    return 0
}

function Switch-Scene {
    param([string]$Scene)
    if (-not $Scene) {
        Warn 'Provide a scene name, e.g. "switch to AI Dev".'
        return 2
    }
    $code = Invoke-ObsHelper -Command 'switch' -Value $Scene
    if ($code -ne 0) {
        Warn 'OBS WebSocket is unavailable or the scene was not found.'
        return 2
    }
    return 0
}

function Show-ObsStatus {
    $code = Invoke-ObsHelper -Command 'status'
    if ($code -ne 0) {
        Warn 'Check that OBS is running and the WebSocket server is connected.'
    }
    $global:LASTEXITCODE = 0
    return 0
}

function Run-Preflight {
    param([switch]$Interactive)
    $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', (Join-Path $workspace 'scripts/youtube_bot_preflight.ps1'))
    if ($Interactive) { $args += '-Interactive' }
    & powershell @args
    return $LASTEXITCODE
}

function Show-QuickStatus {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'scripts/quick_stream_status.ps1')
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Quick status failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Run-Bot {
    param([switch]$DryRun)
    $botScript = Join-Path $workspace 'scripts/youtube_live_bot.py'
    if ($DryRun) {
        & py -3 $botScript --dry-run
    }
    else {
        & py -3 $botScript
    }
    return $LASTEXITCODE
}

function Stop-Bot {
    & powershell -NoProfile -ExecutionPolicy Bypass `
        -File (Join-Path $workspace 'scripts/stop_youtube_bot.ps1')
    return 0
}

function Show-AgiHealth {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'fdo_agi_repo/scripts/check_health.ps1')
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "AGI health check failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-AgiDashboard {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'fdo_agi_repo/scripts/ops_dashboard.ps1')
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "AGI dashboard failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-AgiSummary {
    param([int]$Hours = 24)
    try {
        $venvPython = Join-Path $workspace 'fdo_agi_repo/.venv/Scripts/python.exe'
        if (Test-Path $venvPython) {
            & $venvPython (Join-Path $workspace 'fdo_agi_repo/scripts/summarize_ledger.py') --last-hours $Hours
        }
        else {
            & python (Join-Path $workspace 'fdo_agi_repo/scripts/summarize_ledger.py') --last-hours $Hours
        }
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "AGI summary failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Run-BQIPhase6 {
    Info "[BQI] Running Phase 6 (Persona Learning)..."
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'fdo_agi_repo/scripts/run_bqi_learner.ps1') `
            -Phase 6 -VerboseLog
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "BQI Phase 6 failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-CanaryStatus {
    try {
        Info "[Canary Status Check]"
        $legacy = "https://ion-api-64076350717.us-central1.run.app/api/v2/canary/metrics"
        $canary = "https://ion-api-canary-64076350717.us-central1.run.app/api/v2/canary/metrics"
        
        Write-Host "`nLegacy Service:" -ForegroundColor Cyan
        $legacyResp = Invoke-RestMethod -Uri $legacy -Method Get -ErrorAction SilentlyContinue
        if ($legacyResp) {
            $legacyResp | ConvertTo-Json -Depth 3
        }
        else {
            Warn "Legacy metrics unavailable"
        }
        
        Write-Host "`nCanary Service:" -ForegroundColor Cyan
        $canaryResp = Invoke-RestMethod -Uri $canary -Method Get -ErrorAction SilentlyContinue
        if ($canaryResp) {
            $canaryResp | ConvertTo-Json -Depth 3
        }
        else {
            Warn "Canary metrics unavailable"
        }
        
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Canary status check failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Deploy-Canary {
    param([int]$Percentage = 5)
    try {
        Info "[Canary Deploy] Setting traffic to $Percentage%"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'LLM_Unified/ion-mentoring/scripts/deploy_phase4_canary.ps1') `
            -ProjectId naeda-genesis `
            -CanaryPercentage $Percentage
        return $LASTEXITCODE
    }
    catch {
        Err "Canary deploy failed: $_"
        return 2
    }
}

function Rollback-Canary {
    try {
        Warn "[Canary Rollback] Rolling back to 0%"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'LLM_Unified/ion-mentoring/scripts/rollback_phase4_canary.ps1') `
            -ProjectId naeda-genesis `
            -AutoApprove
        return $LASTEXITCODE
    }
    catch {
        Err "Canary rollback failed: $_"
        return 2
    }
}

function Show-OpsDashboard {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'fdo_agi_repo/scripts/ops_dashboard.ps1')
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Ops dashboard failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-Onboarding {
    try {
        Info "`n[YouTube bot onboarding]"
        Write-Host '1) Install deps: VS Code command palette -> "YouTube Bot: Install Deps"' -ForegroundColor White
        Write-Host '2) Place client secret: "YouTube: Install Client Secret (copy file)"' -ForegroundColor White
        Write-Host '3) Run OAuth: "YouTube Bot: Preflight + OAuth (interactive)"' -ForegroundColor White
        Write-Host '4) Operate: use natural language like "start the bot" or VS Code tasks' -ForegroundColor White
        Ok 'Need a shortcut? Run "YouTube: Quick Onboarding (guided)".'
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show onboarding: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-ConversationSummary {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'scripts/chatops_conversation_summary.ps1')
        return $LASTEXITCODE
    }
    catch {
        Warn "Conversation summary failed: $_"
        return 2
    }
}

function Install-ObsDeps {
    try {
        Info "[Setup] Installing Python deps for OBS control (obsws-python)..."
        # Use the default Python launcher; -3 prefers Python 3 on Windows
        & py -3 -m pip install --upgrade pip
        & py -3 -m pip install --upgrade obsws-python
        if ($LASTEXITCODE -ne 0) {
            Warn "pip install returned a non-zero exit code. You may need to run in elevated PowerShell."
        }
        # Verify installation via inline Python
        & py -3 -c "import sys, importlib; m=importlib.import_module('obsws_python'); print('OK obsws-python', getattr(m,'__version__','')); sys.exit(0)"
        if ($LASTEXITCODE -eq 0) {
            Ok "obsws-python installed. You can now use OBS actions like 'obs 상태' or '씬 AI Dev 바꿔줘'."
            $global:LASTEXITCODE = 0
            return 0
        }
        else {
            Warn "Installation check failed. Try restarting VS Code or your shell, then retry."
            $global:LASTEXITCODE = 0
            return 0
        }
    }
    catch {
        Warn "OBS deps installation failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Install-ClientSecret {
    try {
        Info "Enter the path to client_secret.json (press Enter to use defaults)."
        $path = Read-Host 'Client secret path'
        $installer = Join-Path $workspace 'scripts/install_youtube_client_secret.ps1'
        if ([string]::IsNullOrWhiteSpace($path)) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $installer -UseEnvVar
        }
        else {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $installer -ClientSecretPath $path
        }
        if ($LASTEXITCODE -eq 0) {
            Ok "Client secret installed. Next step: run OAuth with the preflight command."
        }
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Client secret install failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Resolve-Intent {
    param([string]$Text)
    try {
        $intent = & py -3 (Join-Path $workspace 'scripts/chatops_intent.py') --say "$Text"
        if ($LASTEXITCODE -ne 0 -or -not $intent) { return 'unknown' }
        return ($intent | Select-Object -First 1).Trim()
    }
    catch {
        return 'unknown'
    }
}

$action = Resolve-Intent -Text $utterance

switch -Regex ($action) {
    '^agi_health$' {
        Info '[Action] AGI health check'
        exit (Show-AgiHealth)
    }
    '^agi_dashboard$' {
        Info '[Action] AGI dashboard'
        exit (Show-AgiDashboard)
    }
    '^agi_summary$' {
        Info '[Action] AGI ledger summary (24h)'
        exit (Show-AgiSummary -Hours 24)
    }
    '^bqi_phase6$' {
        Info '[Action] BQI Phase 6 (Persona Learning)'
        exit (Run-BQIPhase6)
    }
    '^canary_status$' {
        Info '[Action] Canary deployment status'
        exit (Show-CanaryStatus)
    }
    '^canary_deploy:(\d+)$' {
        $pct = [int]$matches[1]
        Info "[Action] Canary deploy -> $pct%"
        exit (Deploy-Canary -Percentage $pct)
    }
    '^canary_rollback$' {
        Info '[Action] Canary rollback to 0%'
        exit (Rollback-Canary)
    }
    '^ops_dashboard$' {
        Info '[Action] Unified ops dashboard (AGI + Canary + System)'
        exit (Show-OpsDashboard)
    }
    '^preflight_interactive$' {
        Info '[Action] YouTube bot preflight (interactive)'
        exit (Run-Preflight -Interactive)
    }
    '^preflight$' {
        Info '[Action] YouTube bot preflight'
        exit (Run-Preflight)
    }
    '^start_stream$' {
        Info '[Action] Start broadcast'
        exit (Start-Stream)
    }
    '^stop_stream$' {
        Info '[Action] Stop broadcast'
        exit (Stop-Stream)
    }
    '^quick_status$' {
        Info '[Action] Quick status dashboard'
        exit (Show-QuickStatus)
    }
    '^obs_status$' {
        Info '[Action] OBS stream status'
        exit (Show-ObsStatus)
    }
    '^bot_start$' {
        Info '[Action] Start YouTube auto-reply bot'
        exit (Run-Bot)
    }
    '^bot_stop$' {
        Info '[Action] Stop YouTube auto-reply bot'
        exit (Stop-Bot)
    }
    '^bot_dryrun$' {
        Info '[Action] YouTube bot dry run'
        exit (Run-Bot -DryRun)
    }
    '^onboarding$' {
        Info '[Action] Show onboarding guide'
        exit (Show-Onboarding)
    }
    '^install_secret$' {
        Info '[Action] Install client secret'
        exit (Install-ClientSecret)
    }
    '^conversation_summary$' {
        Info '[Action] Conversation summary'
        exit (Show-ConversationSummary)
    }
    '^install_obs_deps$' {
        Info '[Action] Install OBS Python dependencies'
        exit (Install-ObsDeps)
    }
    '^switch_scene:(.+)$' {
        $scene = $matches[1]
        Info "[Action] Switch OBS scene -> $scene"
        exit (Switch-Scene -Scene $scene)
    }
    default {
        Warn "I did not understand. Try commands like:"
        Write-Host "  - 'AGI 상태 보여줘' or '통합 대시보드'" -ForegroundColor White
        Write-Host "  - '카나리 10%로 올려' or '카나리 롤백'" -ForegroundColor White
        Write-Host "  - 'start the stream', 'switch to AI Dev'" -ForegroundColor White
        Write-Host "  - 'start the bot', 'show onboarding'" -ForegroundColor White
        exit 2
    }
}
