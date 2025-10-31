# ChatOps Router: natural language control for OBS & YouTube bot
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass `
#     -File scripts/chatops_router.ps1 `
#     -Say "start the stream"

[CmdletBinding()]
param(
    # 자연어 명령 (선택). 아래 우선순위로 해석됨:
    # 1) $env:CHATOPS_SAY_B64 (UTF-8 Base64)
    # 2) -SayB64 (UTF-8 Base64)
    # 3) $env:CHATOPS_SAY (plain text)
    # 4) -Say (plain text)
    [Parameter(Mandatory = $false)]
    [string]$Say,
    [Parameter(Mandatory = $false)]
    [string]$SayB64
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

$utterance = $null

# Prefer environment-provided Base64 first (robust in VS Code tasks)
try {
    if ($env:CHATOPS_SAY_B64 -and -not [string]::IsNullOrWhiteSpace($env:CHATOPS_SAY_B64)) {
        $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:CHATOPS_SAY_B64))
        if ($decoded) { $utterance = $decoded.Trim() }
    }
}
catch {}

# Next, CLI-provided Base64
if (-not $utterance -and $SayB64) {
    try {
        $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($SayB64))
        if ($decoded) { $utterance = $decoded.Trim() }
    }
    catch {}
}

# Then plain text via environment
if (-not $utterance -and $env:CHATOPS_SAY) {
    $utterance = $env:CHATOPS_SAY.Trim()
}

# Finally, plain text parameter
if (-not $utterance -and $PSBoundParameters.ContainsKey('Say') -and $Say) {
    $utterance = $Say.Trim()
}

if (-not $utterance) {
    Write-Host "No utterance provided. Set CHATOPS_SAY or CHATOPS_SAY_B64 env, or pass -Say/-SayB64." -ForegroundColor Yellow
    exit 2
}
$workspace = Split-Path -Parent $PSScriptRoot

# --- Real-time logging helpers ---
function Emit-ChatOpsEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Type,
        [Parameter(Mandatory = $true)][hashtable]$Payload
    )
    try {
        & "$PSScriptRoot\emit_event.ps1" -EventType $Type -Payload $Payload -PersonaId "chatops" | Out-Null
    }
    catch {}
}

function Run-And-Report {
    param([ScriptBlock]$Do)
    $code = 0
    try { $code = & $Do } catch { $code = 2 }
    Emit-ChatOpsEvent -Type "chatops_action_result" -Payload @{
        utterance = $utterance
        action    = $action
        code      = $code
        timestamp = (Get-Date).ToUniversalTime().ToString('o')
    }
    return $code
}

# Emit incoming command event
Emit-ChatOpsEvent -Type "chatops_command" -Payload @{
    utterance = $utterance
    user      = $env:USERNAME
    cwd       = (Get-Location).Path
    shell     = $PSVersionTable.PSVersion.ToString()
    timestamp = (Get-Date).ToUniversalTime().ToString('o')
}

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

function Open-LumenGate {
    try {
        # Run quick health probe for Lumen Gateway
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'scripts/lumen_quick_probe.ps1')
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            Warn "Lumen probe failed. Check network or LUMEN_GATEWAY_URL."
        }
        return 0
    }
    catch {
        Warn "Lumen gate open failed: $_"
        return 2
    }
}

function Open-LumenDashboard {
    param([int]$Hours = 24)
    try {
        # Generate monitoring dashboard and open HTML
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'scripts/generate_monitoring_report.ps1') `
            -Hours $Hours
        if ($LASTEXITCODE -ne 0) {
            Warn "Monitoring report generation failed."
            return 2
        }
        $html = (Join-Path $workspace 'outputs/monitoring_dashboard_latest.html')
        if (Test-Path $html) {
            Start-Process $html | Out-Null
            Ok "Opened dashboard: $html"
        }
        else {
            Warn "Dashboard HTML not found at: $html"
        }
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Lumen dashboard generation failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
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
        Info "`n=== [TARGET] Unified Operations Dashboard ==="
        
        # 1. AGI Orchestrator Status
        Write-Host "`n[AGI Orchestrator]" -ForegroundColor Cyan
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'fdo_agi_repo/scripts/ops_dashboard.ps1')
        
        # 2. Lumen Gateway Status
        Write-Host "`n[Lumen Gateway]" -ForegroundColor Cyan
        try {
            $lumenProbeLog = Join-Path $workspace 'outputs/lumen_probe_log.jsonl'
            if (Test-Path $lumenProbeLog) {
                # Read all lines and find the last valid JSON
                $lines = Get-Content $lumenProbeLog -Encoding UTF8
                $lastProbe = $null
                for ($i = $lines.Count - 1; $i -ge 0; $i--) {
                    try {
                        $lastProbe = $lines[$i] | ConvertFrom-Json
                        break
                    }
                    catch {
                        # Skip invalid JSON lines
                        continue
                    }
                }
                
                if ($lastProbe) {
                    if ($lastProbe.ok) {
                        Write-Host "  [OK] ONLINE ($($lastProbe.ms)ms)" -ForegroundColor Green
                        Write-Host "  Last probe: $($lastProbe.ts)" -ForegroundColor Gray
                    }
                    else {
                        Write-Host "  [ERROR] OFFLINE (status=$($lastProbe.status))" -ForegroundColor Red
                        if ($lastProbe.error) {
                            Write-Host "  Error: $($lastProbe.error)" -ForegroundColor Yellow
                        }
                    }
                }
                else {
                    Write-Host "  [WARN]  No valid probe data found" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "  [WARN]  No probe data (run 'Lumen: Quick Health Probe')" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "  [WARN]  Failed to read probe log: $_" -ForegroundColor Yellow
        }
        
        # 3. Monitoring Report Summary
        Write-Host "`n[24h System Health]" -ForegroundColor Cyan
        $reportPath = Join-Path $workspace 'outputs/monitoring_report_latest.md'
        if (Test-Path $reportPath) {
            $report = Get-Content $reportPath -Encoding UTF8
            # Extract overall health line
            $healthLine = $report | Where-Object { $_ -match "Overall.*Health" } | Select-Object -First 1
            if ($healthLine) {
                Write-Host "  $healthLine" -ForegroundColor White
            }
            # Extract availability
            $availLine = $report | Where-Object { $_ -match "Availability" } | Select-Object -First 1
            if ($availLine) {
                Write-Host "  $availLine" -ForegroundColor White
            }
        }
        else {
            Write-Host "  [WARN]  No 24h report (run 'Monitoring: Generate Report (24h)')" -ForegroundColor Yellow
        }
        
        Info "`n[INFO] View detailed HTML dashboard: monitoring_dashboard_latest.html"
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show ops dashboard: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Save-DailyConversations {
    <#
    .SYNOPSIS
    4-Persona 일일 대화 수집 (Gitko, Sena, Lubit)
    #>
    try {
        Info "[Session] Harvesting daily conversations from 3 personas..."
        $harvester = Join-Path $workspace 'scripts/harvest_daily_conversations.ps1'
        
        if (-not (Test-Path $harvester)) {
            Warn "Harvester script not found: $harvester"
            return 2
        }
        
        & powershell -NoProfile -ExecutionPolicy Bypass -File $harvester
        
        if ($LASTEXITCODE -eq 0) {
            Ok "[OK] Daily conversations harvested and saved to Resonance Ledger"
            Info "   - Gitko (VS Code Copilot)"
            Info "   - Sena (Claude CLI)"
            Info "   - Lubit (GPT Codex)"
        }
        else {
            Warn "Harvest completed with warnings (exit code: $LASTEXITCODE)"
        }
        
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to harvest conversations: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function End-DailySession {
    <#
    .SYNOPSIS
    오늘 세션 종료 - 대화 저장 + 상태 요약
    #>
    try {
        Info "================================================"
        Info "  오늘 작업 종료 프로세스 시작"
        Info "================================================"
        Write-Host ""
        
        # 1. 대화 수집
        Info "[1/3] 4-Persona 대화 수집 중..."
        Save-DailyConversations
        Write-Host ""
        
        # 2. 통합 상태 확인
        Info "[2/3] 통합 시스템 상태 확인 중..."
        Show-OpsDashboard
        Write-Host ""
        
        # 3. 종료 메시지
        Info "[3/3] 세션 종료 완료"
        Write-Host ""
        Ok "================================================"
        Ok "  오늘 하루 고생하셨습니다!"
        Ok "================================================"
        Write-Host ""
        Info "[METRICS] 저장된 내용:"
        Info "   - Resonance Ledger: 오늘의 대화 및 작업 기록"
        Info "   - Session Harvests: outputs/session_harvests/*.json"
        Write-Host ""
        Info "💤 다음 세션에서 모든 컨텍스트가 복원됩니다"
        Info "   명령: '저장된 대화내용을 바탕으로 작업 이어가죠'"
        Write-Host ""
        
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to end session: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Resume-SavedContext {
    <#
    .SYNOPSIS
    저장된 대화 내용을 바탕으로 작업 재개
    #>
    try {
        Info "================================================"
        Info "  저장된 컨텍스트 복원 시작"
        Info "================================================"
        Write-Host ""
        
        # 1. 최근 Harvest 파일 찾기
        Info "[1/4] 최근 대화 기록 검색 중..."
        $harvestDir = Join-Path $workspace 'outputs/session_harvests'
        if (-not (Test-Path $harvestDir)) {
            Warn "Session harvest 디렉토리를 찾을 수 없습니다: $harvestDir"
            return 2
        }
        
        $latestHarvest = Get-ChildItem -Path $harvestDir -Filter "harvest_*.json" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
        
        if (-not $latestHarvest) {
            Warn "저장된 대화 기록이 없습니다. '오늘 여기까지'를 먼저 실행하세요."
            return 2
        }
        
        Ok "   ✓ 최근 기록 발견: $($latestHarvest.Name)"
        Ok "   ✓ 날짜: $($latestHarvest.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
        Write-Host ""
        
        # 2. 대화 내용 로드
        Info "[2/4] 대화 내용 분석 중..."
        try {
            $harvestData = Get-Content $latestHarvest.FullName -Encoding UTF8 | ConvertFrom-Json
            
            Write-Host ""
            Write-Host "  [LOG] 복원된 Persona 대화:" -ForegroundColor Cyan
            foreach ($persona in $harvestData) {
                if ($persona.conversations -gt 0) {
                    Write-Host "     ✓ $($persona.persona): $($persona.conversations)개 대화" -ForegroundColor Green
                }
                else {
                    Write-Host "     - $($persona.persona): 대화 없음" -ForegroundColor Gray
                }
            }
        }
        catch {
            Warn "대화 파일 파싱 실패: $_"
            return 2
        }
        Write-Host ""
        
        # 3. Resonance Ledger 최근 이벤트 확인
        Info "[3/4] Resonance Ledger 최근 활동 확인 중..."
        $ledgerPath = "D:\nas_backup\fdo_agi_repo\memory\resonance_ledger.jsonl"
        if (Test-Path $ledgerPath) {
            $recentEvents = Get-Content $ledgerPath -Tail 5 -Encoding UTF8 |
            ForEach-Object {
                try {
                    $_ | ConvertFrom-Json
                }
                catch {
                    $null
                }
            } |
            Where-Object { $_ -ne $null }
            
            Write-Host ""
            Write-Host "  🧠 최근 AGI 활동:" -ForegroundColor Cyan
            foreach ($event in $recentEvents) {
                if ($event.event) {
                    $ts = if ($event.ts) { 
                        ([DateTime]$event.ts).ToString("MM-dd HH:mm") 
                    }
                    else { "N/A" }
                    Write-Host "     [$ts] $($event.event)" -ForegroundColor White
                }
            }
        }
        else {
            Warn "   Resonance Ledger를 찾을 수 없습니다"
        }
        Write-Host ""
        
        # 4. 현재 시스템 상태
        Info "[4/4] 현재 시스템 상태 확인 중..."
        Show-OpsDashboard
        Write-Host ""
        
        # 완료 메시지
        Ok "================================================"
        Ok "  컨텍스트 복원 완료!"
        Ok "================================================"
        Write-Host ""
        Info "[TARGET] 복원된 정보:"
        Info "   - 최근 4-Persona 대화 로드"
        Info "   - AGI 최근 활동 5개 확인"
        Info "   - 현재 시스템 상태 확인"
        Write-Host ""
        Info "✨ 이제 이전 작업을 이어서 진행할 수 있습니다!"
        Write-Host ""
        
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to resume context: $_"
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

# =====================================================================
# Session Memory Functions
# =====================================================================

function Start-SessionMemory {
    try {
        Info "[Session] Starting new session..."
        Write-Host "Enter session title: " -NoNewline -ForegroundColor Cyan
        $title = Read-Host
        if ([string]::IsNullOrWhiteSpace($title)) {
            Warn "Session title required."
            return 2
        }
        
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            start $title
        
        if ($LASTEXITCODE -eq 0) {
            Ok "Session started: $title"
        }
        return $LASTEXITCODE
    }
    catch {
        Err "Failed to start session: $_"
        return 2
    }
}

function Add-SessionTask {
    try {
        Info "[Session] Adding task to current session..."
        Write-Host "Enter task title: " -NoNewline -ForegroundColor Cyan
        $title = Read-Host
        if ([string]::IsNullOrWhiteSpace($title)) {
            Warn "Task title required."
            return 2
        }
        
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            task $title
        
        if ($LASTEXITCODE -eq 0) {
            Ok "Task added: $title"
        }
        return $LASTEXITCODE
    }
    catch {
        Err "Failed to add task: $_"
        return 2
    }
}

function End-SessionMemory {
    try {
        Info "[Session] Ending current session..."
        Write-Host "Enter resonance score (0.0-1.0, or press Enter to skip): " -NoNewline -ForegroundColor Cyan
        $score = Read-Host
        
        if ([string]::IsNullOrWhiteSpace($score)) {
            & powershell -NoProfile -ExecutionPolicy Bypass `
                -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
                end
        }
        else {
            & powershell -NoProfile -ExecutionPolicy Bypass `
                -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
                end $score
        }
        
        if ($LASTEXITCODE -eq 0) {
            Ok "Session ended."
        }
        return $LASTEXITCODE
    }
    catch {
        Err "Failed to end session: $_"
        return 2
    }
}

function Show-RecentSessions {
    try {
        Info "[Session] Recent sessions (last 10)"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            recent 10
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show recent sessions: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Search-SessionMemory {
    param([string]$Query = "")
    try {
        if ([string]::IsNullOrWhiteSpace($Query)) {
            Write-Host "Enter search query: " -NoNewline -ForegroundColor Cyan
            $Query = Read-Host
        }
        
        if ([string]::IsNullOrWhiteSpace($Query)) {
            Warn "Search query required."
            return 2
        }
        
        Info "[Session] Searching for: $Query"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            search $Query
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Search failed: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-ActiveSessions {
    try {
        Info "[Session] Active sessions"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            active
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show active sessions: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-SessionStats {
    try {
        Info "[Session] Statistics by persona"
        & powershell -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
            stats
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show session stats: $_"
        $global:LASTEXITCODE = 0
        return 0
    }
}

function Show-SessionDetails {
    param([string]$SessionId = "")
    try {
        if ([string]::IsNullOrWhiteSpace($SessionId)) {
            Write-Host "Enter session ID (or press Enter to show most recent): " -NoNewline -ForegroundColor Cyan
            $SessionId = Read-Host
        }
        
        if ([string]::IsNullOrWhiteSpace($SessionId)) {
            Info "[Session] Showing most recent session details"
            # Get most recent session ID
            $recentOutput = & powershell -NoProfile -ExecutionPolicy Bypass `
                -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
                recent 1
            # Extract ID from output (first 8 chars of UUID in table)
            # This is a simple heuristic; for production, consider JSON output
            Write-Host $recentOutput
        }
        else {
            Info "[Session] Details for: $SessionId"
            & powershell -NoProfile -ExecutionPolicy Bypass `
                -File (Join-Path $workspace 'session_memory/session_tools.ps1') `
                details $SessionId
        }
        $global:LASTEXITCODE = 0
        return 0
    }
    catch {
        Warn "Failed to show session details: $_"
        $global:LASTEXITCODE = 0
        return 0
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

# Emit resolved intent event
Emit-ChatOpsEvent -Type "chatops_resolved" -Payload @{
    utterance = $utterance
    action    = $action
    timestamp = (Get-Date).ToUniversalTime().ToString('o')
}

switch -Regex ($action) {
    '^agi_health$' {
        Info '[Action] AGI health check'
        exit (Run-And-Report { Show-AgiHealth })
    }
    '^agi_dashboard$' {
        Info '[Action] AGI dashboard'
        exit (Run-And-Report { Show-AgiDashboard })
    }
    '^agi_summary$' {
        Info '[Action] AGI ledger summary (24h)'
        exit (Run-And-Report { Show-AgiSummary -Hours 24 })
    }
    '^bqi_phase6$' {
        Info '[Action] BQI Phase 6 (Persona Learning)'
        exit (Run-And-Report { Run-BQIPhase6 })
    }
    '^canary_status$' {
        Info '[Action] Canary deployment status'
        exit (Run-And-Report { Show-CanaryStatus })
    }
    '^canary_deploy:(\d+)$' {
        $pct = [int]$matches[1]
        Info "[Action] Canary deploy -> $pct%"
        exit (Run-And-Report { Deploy-Canary -Percentage $pct })
    }
    '^canary_rollback$' {
        Info '[Action] Canary rollback to 0%'
        exit (Run-And-Report { Rollback-Canary })
    }
    '^ops_dashboard$' {
        Info '[Action] Unified ops dashboard (AGI + Canary + System)'
        exit (Run-And-Report { Show-OpsDashboard })
    }
    '^preflight_interactive$' {
        Info '[Action] YouTube bot preflight (interactive)'
        exit (Run-And-Report { Run-Preflight -Interactive })
    }
    '^preflight$' {
        Info '[Action] YouTube bot preflight'
        exit (Run-And-Report { Run-Preflight })
    }
    '^start_stream$' {
        Info '[Action] Start broadcast'
        exit (Run-And-Report { Start-Stream })
    }
    '^stop_stream$' {
        Info '[Action] Stop broadcast'
        exit (Run-And-Report { Stop-Stream })
    }
    '^quick_status$' {
        Info '[Action] Quick status dashboard'
        exit (Run-And-Report { Show-QuickStatus })
    }
    '^obs_status$' {
        Info '[Action] OBS stream status'
        exit (Run-And-Report { Show-ObsStatus })
    }
    '^lumen_dashboard$' {
        Info '[Action] Lumen 24h dashboard (HTML)'
        exit (Run-And-Report { Open-LumenDashboard -Hours 24 })
    }
    '^lumen_open$' {
        Info '[Action] Lumen gateway probe (open gate)'
        exit (Run-And-Report { Open-LumenGate })
    }
    '^bot_start$' {
        Info '[Action] Start YouTube auto-reply bot'
        exit (Run-And-Report { Run-Bot })
    }
    '^bot_stop$' {
        Info '[Action] Stop YouTube auto-reply bot'
        exit (Run-And-Report { Stop-Bot })
    }
    '^save_conversations$' {
        Info '[Action] Save daily conversations (Gitko, Sena, Lubit)'
        exit (Run-And-Report { Save-DailyConversations })
    }
    '^end_session$' {
        Info '[Action] End daily session (save + summary)'
        exit (Run-And-Report { End-DailySession })
    }
    '^resume_context$' {
        Info '[Action] Resume from saved context'
        exit (Run-And-Report { Resume-SavedContext })
    }
    '^bot_dryrun$' {
        Info '[Action] YouTube bot dry run'
        exit (Run-And-Report { Run-Bot -DryRun })
    }
    '^onboarding$' {
        Info '[Action] Show onboarding guide'
        exit (Run-And-Report { Show-Onboarding })
    }
    '^install_secret$' {
        Info '[Action] Install client secret'
        exit (Run-And-Report { Install-ClientSecret })
    }
    '^conversation_summary$' {
        Info '[Action] Conversation summary'
        exit (Run-And-Report { Show-ConversationSummary })
    }
    '^install_obs_deps$' {
        Info '[Action] Install OBS Python dependencies'
        exit (Run-And-Report { Install-ObsDeps })
    }
    '^switch_scene:(.+)$' {
        $scene = $matches[1]
        Info "[Action] Switch OBS scene -> $scene"
        exit (Run-And-Report { Switch-Scene -Scene $scene })
    }
    '^session_start$' {
        Info '[Action] Start new session'
        exit (Run-And-Report { Start-SessionMemory })
    }
    '^session_add_task$' {
        Info '[Action] Add task to current session'
        exit (Run-And-Report { Add-SessionTask })
    }
    '^session_end$' {
        Info '[Action] End current session'
        exit (Run-And-Report { End-SessionMemory })
    }
    '^session_recent$' {
        Info '[Action] Show recent sessions'
        exit (Run-And-Report { Show-RecentSessions })
    }
    '^session_search:(.*)$' {
        $query = $matches[1]
        if ([string]::IsNullOrWhiteSpace($query)) {
            Info '[Action] Search sessions (interactive)'
            exit (Run-And-Report { Search-SessionMemory })
        }
        else {
            Info "[Action] Search sessions: $query"
            exit (Run-And-Report { Search-SessionMemory -Query $query })
        }
    }
    '^session_active$' {
        Info '[Action] Show active sessions'
        exit (Run-And-Report { Show-ActiveSessions })
    }
    '^session_stats$' {
        Info '[Action] Show session statistics'
        exit (Run-And-Report { Show-SessionStats })
    }
    '^session_details$' {
        Info '[Action] Show session details'
        exit (Run-And-Report { Show-SessionDetails })
    }
    default {
        Warn "I did not understand. Try commands like:"
        Write-Host "  - 'AGI 상태 보여줘' or '통합 대시보드'" -ForegroundColor White
        Write-Host "  - '카나리 10%로 올려' or '카나리 롤백'" -ForegroundColor White
        Write-Host "  - 'start the stream', 'switch to AI Dev'" -ForegroundColor White
        Write-Host "  - 'start the bot', 'show onboarding'" -ForegroundColor White
        Emit-ChatOpsEvent -Type "chatops_action_result" -Payload @{
            utterance = $utterance
            action    = $action
            code      = 2
            timestamp = (Get-Date).ToUniversalTime().ToString('o')
        }
        exit 2
    }
}
