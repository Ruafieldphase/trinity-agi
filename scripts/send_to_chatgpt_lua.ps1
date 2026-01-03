# send_to_chatgpt_lua.ps1
# Lua Trinity Bridge: Prepare ChatGPT handoff with comprehensive context
# Clean rewrite - streamlined from 1332 lines to ~550 lines
#
# QUICK USAGE:
#   -GenerateSample         Generate test data (smoke test)
#   -ListSections           Show script sections index
#   -EnqueueDirect          Send to task queue (8091)
#   -AddFileRef <path>      Include specific file in context
#   -MaxContext <chars>     Limit context length (default: 8000)
#
# SECTIONS INDEX (use #region markers for folding):
#   Configuration, Utility, Context Collection, Core Logic, Main Execution

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$Query = "",
    
    [Parameter(Mandatory = $false)]
    [string]$OutMd,
    
    [Parameter(Mandatory = $false)]
    [string]$OutJson,
    
    [switch]$NoClipboard,
    [switch]$SkipRhythm,
    [switch]$SkipGoals,
    [switch]$SkipSystem,
    [switch]$SkipRcl,
    [switch]$MinimalContext,
    [switch]$VerboseLog,
    [int]$MaxContext,
    [switch]$AllowLargeClipboard,
    
    # New: Bridge processor modes
    [switch]$ProcessOnce,
    [switch]$Monitor,
    [switch]$GenerateSample,
    [int]$MonitorIntervalSec = 10,

    # Navigation helpers
    [switch]$ListSections
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================================================
# Configuration
# ============================================================================

#region Configuration
$script:WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$script:OutputDir = Join-Path $WorkspaceRoot "outputs"
$script:TempDir = Join-Path $OutputDir "temp"
$script:RequestDir = Join-Path $OutputDir "lua_requests"
$script:ProcessedDir = Join-Path $RequestDir "processed"
$script:ResponseDir = Join-Path $OutputDir "trinity_responses"
$script:HmacKey = $env:LUA_BRIDGE_HMAC_KEY

# Ensure bridge directories exist
@($script:OutputDir, $script:TempDir, $script:RequestDir, $script:ProcessedDir, $script:ResponseDir) | ForEach-Object {
    if (-not (Test-Path -LiteralPath $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

$script:Config = @{
    MaxContextLength       = 8000
    MinContextLength       = 500
    RhythmLookbackHours    = 24
    GoalLookbackDays       = 7
    SystemHealthTimeoutSec = 10
    HmacKeyEnvVar          = "LUA_BRIDGE_HMAC_KEY"
    ClipboardSafeLimit     = 3500
}

# File paths
$script:Paths = @{
    SessionContinuity = Join-Path $OutputDir "session_continuity_latest.md"
    RhythmStatus      = Join-Path $OutputDir "RHYTHM_SYSTEM_STATUS_REPORT.md"
    GoalTracker       = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\goal_tracker.json"
    QuickStatus       = Join-Path $OutputDir "quick_status_latest.json"
    ManageRclStack    = Join-Path $WorkspaceRoot "scripts\manage_rcl_stack.ps1"
    HandoffMd         = if ($OutMd) { $OutMd } else { Join-Path $OutputDir "lua_handoff_latest.md" }
    HandoffJson       = if ($OutJson) { $OutJson } else { Join-Path $OutputDir "lua_handoff_latest.json" }
}

$script:HasCustomContextLimit = $false
$script:MinimalContextRequested = [bool]$MinimalContext
$script:EffectiveMaxContext = $script:Config.MaxContextLength

if ($PSBoundParameters.ContainsKey('MaxContext') -and $MaxContext -gt 0) {
    $script:EffectiveMaxContext = [Math]::Max($MaxContext, $script:Config.MinContextLength)
    $script:HasCustomContextLimit = $true
}
elseif ($script:MinimalContextRequested) {
    $reducedDefault = [Math]::Floor($script:Config.MaxContextLength * 0.6)
    $script:EffectiveMaxContext = [Math]::Max($script:Config.MinContextLength, [int]$reducedDefault)
}
#endregion Configuration

# ============================================================================
# Utility Functions
# ============================================================================
#region Utility

function Ensure-EnvPlaceholders {
    try {
        $envFile = Join-Path $script:WorkspaceRoot ".env"
        if (-not (Test-Path -LiteralPath $envFile)) {
            "# Auto-generated placeholders`n# Add your secrets below`nLUA_BRIDGE_HMAC_KEY=" | Out-File -FilePath $envFile -Encoding UTF8 -Force
        }
        else {
            $content = Get-Content -Path $envFile -ErrorAction SilentlyContinue
            if ($content -notmatch "^LUA_BRIDGE_HMAC_KEY=") {
                Add-Content -Path $envFile -Value "LUA_BRIDGE_HMAC_KEY="
            }
        }
    }
    catch {
        Write-Log "Failed to ensure .env placeholders: $($_.Exception.Message)" "WARN"
    }
}

function Get-ScriptSections {
    param([string]$Path = $MyInvocation.MyCommand.Path)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { return @() }
        $lines = Get-Content -Path $Path -ErrorAction Stop
        $sections = @()
        foreach ($line in $lines) {
            if ($line -match '^#region\s+(.+)$') {
                $name = $Matches[1].Trim()
                $sections += $name
            }
        }
        return $sections
    }
    catch {
        return @()
    }
}

function Show-Index {
    $sections = Get-ScriptSections
    if (-not $sections -or $sections.Count -eq 0) {
        Write-Host "No sections discovered." -ForegroundColor Yellow
        return
    }
    Write-Host "Sections in send_to_chatgpt_lua.ps1:" -ForegroundColor Cyan
    $i = 1
    foreach ($s in $sections) {
        Write-Host ("  [{0}] {1}" -f $i, $s) -ForegroundColor Gray
        $i++
    }
    Write-Host "Tip: Use -GenerateSample, -ProcessOnce, or -Monitor for targeted runs." -ForegroundColor DarkGray
}

#endregion Utility

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    if ($VerboseLog -or $Level -eq "ERROR" -or $Level -eq "WARN") {
        $timestamp = Get-Date -Format "HH:mm:ss"
        $color = switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "Cyan" }
        }
        Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
    }
}

function Get-SafeFileContent {
    param(
        [string]$Path,
        [int]$MaxLines = 0
    )
    
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Log "File not found: $Path" "WARN"
        return $null
    }
    
    try {
        $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
        
        if ($MaxLines -gt 0) {
            $lines = $content -split "`n"
            if ($lines.Count -gt $MaxLines) {
                $content = ($lines | Select-Object -First $MaxLines) -join "`n"
                $content += "`n... (truncated, showing first $MaxLines lines)"
            }
        }
        
        return $content
    }
    catch {
        Write-Log "Failed to read file $Path : $_" "ERROR"
        return $null
    }
}

function Get-SafeJsonContent {
    param([string]$Path)
    
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    
    try {
        $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
        return $content | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Write-Log "Failed to parse JSON from $Path : $_" "ERROR"
        return $null
    }
}

function Truncate-String {
    param(
        [string]$Text,
        [int]$MaxLength
    )
    
    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ""
    }
    
    if ($Text.Length -le $MaxLength) {
        return $Text
    }
    
    $half = [Math]::Floor($MaxLength / 2) - 50
    $start = $Text.Substring(0, $half)
    $end = $Text.Substring($Text.Length - $half)
    
    return "$start`n`n... (중간 생략: $($Text.Length - $MaxLength) chars) ...`n`n$end"
}

function Apply-ContextLimit {
    param(
        [string]$Content,
        [int]$MaxLength
    )
    
    $originalLength = if ($null -eq $Content) { 0 } else { $Content.Length }
    $result = @{
        Text           = $Content
        Truncated      = $false
        OriginalLength = $originalLength
    }
    
    if ([string]::IsNullOrWhiteSpace($Content) -or $MaxLength -le 0) {
        return $result
    }
    
    if ($originalLength -le $MaxLength) {
        return $result
    }
    
    $notice = "`n---`n⚠️ Context trimmed for Copilot limits (kept $MaxLength of $originalLength chars).`n"
    $available = $MaxLength - $notice.Length
    if ($available -lt 0) { $available = 0 }
    $trimmed = if ($available -gt 0) { $Content.Substring(0, $available).TrimEnd() } else { "" }
    $final = $trimmed + $notice
    
    if ($final.Length -gt $MaxLength) {
        $final = $final.Substring(0, $MaxLength)
    }
    
    $result.Text = $final
    $result.Truncated = $true
    return $result
}

function Build-ClipboardSummary {
    param(
        [hashtable]$SessionCtx,
        [hashtable]$RhythmCtx,
        [hashtable]$GoalCtx,
        [hashtable]$SystemCtx,
        [hashtable]$RclCtx,
        [hashtable]$ReportMeta,
        [string]$FullPath,
        [string[]]$RecommendedActions
    )
    
    $lines = @(
        "# Lua Bridge Quick Summary",
        "",
        "- Session: $($SessionCtx.Summary)",
        "- Rhythm: $($RhythmCtx.Summary)",
        "- Goals: $($GoalCtx.Summary)",
        "- System: $($SystemCtx.Summary)",
        "- RCL: $($RclCtx.Summary)"
    )
    
    if ($ReportMeta) {
        $lines += "- Generated: $($ReportMeta.generated_at)"
    }
    
    $lines += ""
    $lines += "Recommended next actions:"
    if ($RecommendedActions -and $RecommendedActions.Count -gt 0) {
        $i = 1
        foreach ($act in $RecommendedActions[0..([Math]::Min($RecommendedActions.Count,3)-1)]) {
            $lines += "$i. $act"
            $i++
        }
    }
    else {
        $lines += "1. 리듬 상태 재확인 (System: Core Processes task)"
        $lines += "2. 목표 진행 점검 (Goal Tracker)"
        $lines += "3. RCL 스택 상태 확인 (scripts/manage_rcl_stack.ps1 -Action Status)"
    }
    $lines += ""
    $lengthInfo = if ($ReportMeta) { "Full report length ≈ $($ReportMeta.context_length) chars." } else { "" }
    $lines += "Full Markdown: $FullPath"
    if ($lengthInfo) {
        $lines += $lengthInfo
    }
    $lines += "Use -AllowLargeClipboard to copy the complete payload."
    
    return ($lines -join "`n")
}

# ============================================================================
# Context Collectors
# ============================================================================

function Get-SessionContext {
    Write-Log "Collecting session continuity context..."
    
    $sessionPath = $script:Paths.SessionContinuity
    $content = Get-SafeFileContent -Path $sessionPath -MaxLines 100
    
    if (-not $content) {
        return @{
            Available  = $false
            Summary    = "세션 연속성 리포트 없음"
            LastUpdate = "N/A"
        }
    }
    
    # Extract key metrics
    $rhythmMatch = $content | Select-String -Pattern "현재 리듬.*?(\d+\.\d+)%" -AllMatches
    $rhythmScore = if ($rhythmMatch) { $rhythmMatch.Matches[0].Groups[1].Value } else { "N/A" }
    
    $goalsMatch = $content | Select-String -Pattern "활성 목표.*?(\d+)개" -AllMatches
    $activeGoals = if ($goalsMatch) { $goalsMatch.Matches[0].Groups[1].Value } else { "N/A" }
    
    return @{
        Available  = $true
        Summary    = "리듬: $rhythmScore%, 활성 목표: $activeGoals개"
        Content    = Truncate-String -Text $content -MaxLength 2000
        LastUpdate = (Get-Item -LiteralPath $sessionPath).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }
}

function Get-RhythmContext {
    if ($SkipRhythm) {
        Write-Log "Skipping rhythm context (--SkipRhythm)" "WARN"
        return @{ Available = $false; Summary = "스킵됨" }
    }
    
    Write-Log "Collecting rhythm status..."
    
    $rhythmPath = $script:Paths.RhythmStatus
    $content = Get-SafeFileContent -Path $rhythmPath -MaxLines 50
    
    if (-not $content) {
        return @{
            Available = $false
            Summary   = "리듬 상태 리포트 없음"
        }
    }
    
    # Extract phase and score
    $phaseMatch = $content | Select-String -Pattern "현재 페이즈:\s*(\S+)" -AllMatches
    $phase = if ($phaseMatch) { $phaseMatch.Matches[0].Groups[1].Value } else { "UNKNOWN" }
    
    $scoreMatch = $content | Select-String -Pattern "시스템 건강도:\s*(\d+\.\d+)%" -AllMatches
    $score = if ($scoreMatch) { $scoreMatch.Matches[0].Groups[1].Value } else { "N/A" }
    
    return @{
        Available = $true
        Phase     = $phase
        Score     = $score
        Summary   = "페이즈: $phase, 건강도: $score%"
        Content   = Truncate-String -Text $content -MaxLength 1500
    }
}

function Get-GoalContext {
    if ($SkipGoals) {
        Write-Log "Skipping goal context (--SkipGoals)" "WARN"
        return @{ Available = $false; Summary = "스킵됨" }
    }
    
    Write-Log "Collecting autonomous goals..."
    
    $goalPath = $script:Paths.GoalTracker
    $data = Get-SafeJsonContent -Path $goalPath
    
    if (-not $data -or -not $data.goals) {
        return @{
            Available = $false
            Summary   = "목표 트래커 없음"
        }
    }
    
    $goals = $data.goals
    $active = @($goals | Where-Object { $_.status -eq "in_progress" })
    $completed = @($goals | Where-Object { $_.status -eq "completed" })
    $failed = @($goals | Where-Object { $_.status -eq "failed" })
    
    $summary = "활성: $($active.Count), 완료: $($completed.Count), 실패: $($failed.Count)"
    
    # Recent goals (last 3) - handle missing created_at gracefully
    $recent = $goals | 
    Where-Object { $_.created_at } |
    Sort-Object -Property { 
        try { [datetime]$_.created_at } 
        catch { [datetime]::MinValue }
    } -Descending -ErrorAction SilentlyContinue | 
    Select-Object -First 3
    
    # If no goals with created_at, just take first 3
    if (-not $recent) {
        $recent = $goals | Select-Object -First 3
    }
    
    return @{
        Available   = $true
        Total       = $goals.Count
        Active      = $active.Count
        Completed   = $completed.Count
        Failed      = $failed.Count
        Summary     = $summary
        RecentGoals = $recent
    }
}

function Get-SystemContext {
    if ($SkipSystem) {
        Write-Log "Skipping system context (--SkipSystem)" "WARN"
        return @{ Available = $false; Summary = "스킵됨" }
    }
    
    Write-Log "Collecting system health..."
    
    $statusPath = $script:Paths.QuickStatus
    $data = Get-SafeJsonContent -Path $statusPath
    
    if (-not $data) {
        return @{
            Available = $false
            Summary   = "시스템 상태 없음"
        }
    }
    
    $agi = $data.agi_status
    $Core = $data.core_status
    
    return @{
        Available = $true
        AGI       = @{
            Workers  = if ($agi.rpa_workers) { $agi.rpa_workers } else { 0 }
            Watchdog = if ($agi.watchdog_running) { "실행 중" } else { "중지됨" }
        }
        Core     = @{
            Status = if ($Core.api_status) { $Core.api_status } else { "UNKNOWN" }
        }
        Summary   = "Workers: $($agi.rpa_workers), Watchdog: $(if($agi.watchdog_running){'OK'}else{'DOWN'})"
        Timestamp = $data.timestamp
    }
}

function Get-RclContext {
    if ($SkipRcl) {
        Write-Log "Skipping RCL context (--SkipRcl)" "WARN"
        return @{ Available = $false; Summary = "스킵됨" }
    }

    $manageScript = $script:Paths.ManageRclStack
    if (-not (Test-Path -LiteralPath $manageScript)) {
        Write-Log "manage_rcl_stack.ps1 not found at $manageScript" "WARN"
        return @{
            Available = $false
            Summary   = "manage_rcl_stack.ps1 없음"
        }
    }

    try {
        Write-Log "Collecting RCL stack status..."
        $raw = & $manageScript -Action Status -OutputJson
        if (-not $raw) {
            throw "Empty output"
        }
        $status = $raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Write-Log "Failed to collect RCL status: $_" "WARN"
        return @{
            Available = $false
            Summary   = "RCL 상태 조회 실패"
            Error     = $_.ToString()
        }
    }

    $jobs = @()
    foreach ($job in $status.jobs) {
        $jobs += @{
            Name    = $job.name
            Running = [bool]$job.running
            State   = $job.state
        }
    }

    $jobSummary = if ($jobs.Count -gt 0) {
        ($jobs | ForEach-Object { "$($_.Name):" + ($(if ($_.Running) { "ON" } else { "OFF" })) }) -join ", "
    }
    else {
        "등록된 Job 없음"
    }

    return @{
        Available   = $true
        Summary     = "Runner:$($status.runner_port) / Bridge:$($status.bridge_port) | $jobSummary"
        RunnerPort  = $status.runner_port
        BridgePort  = $status.bridge_port
        TickHz      = $status.tick_hz
        IntervalSec = $status.feedback_interval
        Jobs        = $jobs
        Raw         = $status
    }
}

# ============================================================================
# Report Builder
# ============================================================================

function Build-HandoffReport {
    param(
        [hashtable]$SessionCtx,
        [hashtable]$RhythmCtx,
        [hashtable]$GoalCtx,
        [hashtable]$SystemCtx,
        [hashtable]$RclCtx,
        [string]$UserQuery
    )
    
    Write-Log "Building handoff report..."
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Markdown report
    $md = @"
# 🌌 Lua Trinity Bridge - ChatGPT Handoff
**생성 시각**: $timestamp
**사용자 쿼리**: $(if($UserQuery){"``$UserQuery``"}else{"(없음)"})

---

## 📍 현재 세션 상태

$($SessionCtx.Summary)

**마지막 업데이트**: $($SessionCtx.LastUpdate)

$(if($SessionCtx.Content){"### 📄 세션 연속성 리포트 (요약)`n``````markdown`n$($SessionCtx.Content)`n```````n"}else{""})

---

## 🌊 리듬 상태

$($RhythmCtx.Summary)

$(if($RhythmCtx.Content){"### 📊 리듬 시스템 리포트 (요약)`n``````markdown`n$($RhythmCtx.Content)`n```````n"}else{""})

---

## 🎯 자율 목표 상태

$($GoalCtx.Summary)

$(if($GoalCtx.RecentGoals){
    "### 📋 최근 목표 (최근 3개)`n"
    $GoalCtx.RecentGoals | ForEach-Object {
        "- **$($_.title)** [$($_.status)]`n  - 생성: $($_.created_at)`n"
    }
}else{""})

---

## ⚙️ 시스템 상태

$($SystemCtx.Summary)

**타임스탬프**: $($SystemCtx.Timestamp)

---

## 🧠 RCL 루프 상태

$($RclCtx.Summary)

$(if($RclCtx.Jobs){
    "### 프로세스 상태`n" + (($RclCtx.Jobs | ForEach-Object {
        "- **$($_.Name)** : $(if($_.Running){'ON'}else{'OFF'})$(if($_.State){" (`$($_.State)`)"})"
    }) -join "`n")
}else{"(데이터 없음)"})

---

## 💡 추천 다음 행동

$(if($SessionCtx.Content -match "추천.*행동"){
    $SessionCtx.Content | Select-String -Pattern "추천.*행동[\s\S]{0,300}" | ForEach-Object { $_.Matches[0].Value }
}else{
    "1. 리듬 상태 확인 및 조정`n2. 활성 목표 진행 상황 점검`n3. 시스템 건강도 모니터링"
})

---

## 🔗 관련 파일

- 세션 연속성: `outputs/session_continuity_latest.md`
- 리듬 상태: `outputs/RHYTHM_SYSTEM_STATUS_REPORT.md`
- 목표 트래커: ``fdo_agi_repo/memory/goal_tracker.json``
- 시스템 상태: `outputs/quick_status_latest.json`

---

*이 리포트는 Lua Trinity Bridge가 자동 생성했습니다.*
*ChatGPT에 붙여넣기하여 즉시 컨텍스트를 복원할 수 있습니다.*
"@

    # JSON report
    $json = @{
        metadata            = @{
            generated_at = $timestamp
            generator    = "Lua Trinity Bridge v2.0"
            user_query   = $UserQuery
        }
        session             = $SessionCtx
        rhythm              = $RhythmCtx
        goals               = $GoalCtx
        system              = $SystemCtx
        rcl                 = $RclCtx
        recommended_actions = @(
            "리듬 상태 확인 및 조정",
            "활성 목표 진행 상황 점검",
            "시스템 건강도 모니터링",
            "RCL 루프 상태 점검"
        )
        file_references     = @(
            $script:Paths.SessionContinuity,
            $script:Paths.RhythmStatus,
            $script:Paths.GoalTracker,
            $script:Paths.QuickStatus,
            $script:Paths.ManageRclStack
        )
    }
    
    $limitInfo = Apply-ContextLimit -Content $md -MaxLength $script:EffectiveMaxContext
    $md = $limitInfo.Text
    $json.metadata.context_limit = $script:EffectiveMaxContext
    $json.metadata.context_length = $limitInfo.OriginalLength
    $json.metadata.context_truncated = $limitInfo.Truncated
    $json.metadata.trimmed_length = if ($null -eq $md) { 0 } else { $md.Length }
    if ($limitInfo.Truncated) {
        $json.metadata.truncation_notice = "Markdown trimmed to prevent Copilot invalid_request_body errors."
    }
    
    return @{
        Markdown = $md
        Json     = $json
    }
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    Write-Log "=== Lua Trinity Bridge - ChatGPT Handoff ===" "SUCCESS"
    Write-Log "Workspace: $script:WorkspaceRoot"
    if ($script:HasCustomContextLimit) {
        Write-Log "Custom context limit: $script:EffectiveMaxContext chars" "WARN"
    }
    elseif ($script:MinimalContextRequested) {
        Write-Log "Minimal context mode active (limit $script:EffectiveMaxContext chars)" "WARN"
    }
    
    # Ensure output directories
    if (-not (Test-Path -LiteralPath $script:OutputDir)) {
        New-Item -ItemType Directory -Path $script:OutputDir -Force | Out-Null
    }
    
    if (-not (Test-Path -LiteralPath $script:TempDir)) {
        New-Item -ItemType Directory -Path $script:TempDir -Force | Out-Null
    }
    
    # Collect context
    $sessionCtx = Get-SessionContext
    $rhythmCtx = if (-not $SkipRhythm) { Get-RhythmContext } else { @{ Summary = "스킵됨"; Content = "" } }
    $goalCtx = if (-not $SkipGoals) { Get-GoalContext } else { @{ Summary = "스킵됨"; RecentGoals = @() } }
    $systemCtx = Get-SystemContext
    $rclCtx = Get-RclContext
    
    # Build report
    $report = Build-HandoffReport -SessionCtx $sessionCtx -RhythmCtx $rhythmCtx `
        -GoalCtx $goalCtx -SystemCtx $systemCtx -RclCtx $rclCtx -UserQuery $Query
    if ($report.Json.metadata.context_truncated) {
        $originalLength = $report.Json.metadata.context_length
        $limitLength = $report.Json.metadata.context_limit
        Write-Log "Context trimmed ($originalLength → $limitLength chars) to avoid invalid_request_body." "WARN"
    }
    
    # Save Markdown
    $mdPath = $script:Paths.HandoffMd
    try {
        $report.Markdown | Out-File -FilePath $mdPath -Encoding UTF8 -Force
        Write-Log "Markdown saved: $mdPath" "SUCCESS"
    }
    catch {
        Write-Log "Failed to save Markdown: $_" "ERROR"
    }
    
    # Save JSON
    $jsonPath = $script:Paths.HandoffJson
    try {
        $report.Json | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8 -Force
        Write-Log "JSON saved: $jsonPath" "SUCCESS"
    }
    catch {
        Write-Log "Failed to save JSON: $_" "ERROR"
    }
    
    $clipboardPayload = $report.Markdown
    $clipboardMode = "full"
    if (-not $AllowLargeClipboard -and $report.Markdown.Length -gt $script:Config.ClipboardSafeLimit) {
        $clipboardPayload = Build-ClipboardSummary -SessionCtx $sessionCtx -RhythmCtx $rhythmCtx `
            -GoalCtx $goalCtx -SystemCtx $systemCtx -RclCtx $rclCtx -ReportMeta $report.Json.metadata `
            -FullPath $mdPath -RecommendedActions $report.Json.recommended_actions
        $clipboardMode = "summary"
        Write-Log "Clipboard payload trimmed to safe summary ($($report.Markdown.Length)→$($clipboardPayload.Length) chars)." "WARN"
    }
    
    # Copy to clipboard
    if (-not $NoClipboard) {
        try {
            $clipboardPayload | Set-Clipboard
            $modeMsg = if ($clipboardMode -eq "summary") { "summary" } else { "full report" }
            Write-Log "Copied $modeMsg to clipboard (Ctrl+V to paste)" "SUCCESS"
        }
        catch {
            Write-Log "Failed to copy to clipboard: $_" "WARN"
        }
    }
    
    # Summary
    Write-Host "`n=== 📋 Handoff Summary ===" -ForegroundColor Cyan
    Write-Host "세션: $($sessionCtx.Summary)" -ForegroundColor White
    Write-Host "리듬: $($rhythmCtx.Summary)" -ForegroundColor White
    Write-Host "목표: $($goalCtx.Summary)" -ForegroundColor White
    Write-Host "시스템: $($systemCtx.Summary)" -ForegroundColor White
    Write-Host "RCL: $($rclCtx.Summary)" -ForegroundColor White
    Write-Host "`n출력 파일:" -ForegroundColor Cyan
    Write-Host "  - Markdown: $mdPath" -ForegroundColor Gray
    Write-Host "  - JSON: $jsonPath" -ForegroundColor Gray
    
    if (-not $NoClipboard) {
        if ($clipboardMode -eq "summary") {
            Write-Host "`n⚠️ 길이 제한 때문에 요약본만 클립보드에 복사했습니다. 전체 리포트: $mdPath" -ForegroundColor Yellow
        }
        else {
            Write-Host "`n✅ 클립보드에 복사됨. ChatGPT에 Ctrl+V로 붙여넣기하세요!" -ForegroundColor Green
        }
    }
    
    Write-Log "=== Handoff Complete ===" "SUCCESS"
}

# ============================================================================
# Bridge Processor Functions
# ============================================================================

function Get-HmacSignature {
    param(
        [string]$Data,
        [string]$Key
    )
    
    try {
        $hmac = New-Object System.Security.Cryptography.HMACSHA256
        $hmac.Key = [System.Text.Encoding]::UTF8.GetBytes($Key)
        $hashBytes = $hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Data))
        return [Convert]::ToBase64String($hashBytes)
    }
    catch {
        Write-Log "HMAC signature failed: $_" "ERROR"
        return $null
    }
}

function Test-RequestSignature {
    param([hashtable]$Request)
    
    $hmacKey = [Environment]::GetEnvironmentVariable($script:Config.HmacKeyEnvVar, "User")
    
    if (-not $hmacKey) {
        Write-Log "HMAC key not set in env var: $($script:Config.HmacKeyEnvVar). Skipping signature check." "WARN"
        return $true  # Allow unsigned requests if no key configured
    }
    
    if (-not $Request.signature) {
        Write-Log "Request missing signature field" "WARN"
        return $false
    }
    
    # Canonical data: timestamp|request_id|query
    $canonical = "$($Request.timestamp)|$($Request.request_id)|$($Request.query)"
    $expectedSig = Get-HmacSignature -Data $canonical -Key $hmacKey
    
    if ($Request.signature -eq $expectedSig) {
        Write-Log "Signature verified" "SUCCESS"
        return $true
    }
    else {
        Write-Log "Signature mismatch" "ERROR"
        return $false
    }
}

function Process-LuaRequest {
    param([string]$RequestFilePath)
    
    Write-Log "Processing request: $RequestFilePath" "INFO"
    
    try {
        $requestJson = Get-Content -LiteralPath $RequestFilePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $request = @{
            request_id = $requestJson.request_id
            timestamp  = $requestJson.timestamp
            query      = $requestJson.query
            signature  = $requestJson.signature
        }
        
        # Verify signature
        if (-not (Test-RequestSignature -Request $request)) {
            Write-Log "Request signature verification failed. Skipping." "ERROR"
            return
        }
        
        # Generate response
        Write-Log "Generating response for query: $($request.query)" "INFO"
        
        # Detect request type
        $isDesignRequest = $request.query -match "(design|architect|create|build|implement)"
        
        if ($isDesignRequest) {
            Write-Log "Detected as design request" "INFO"
            Process-DesignRequest -Request $request -ResponseDir $script:ResponseDir
        }
        else {
            Write-Log "Processing as handoff request" "INFO"
            
            # Run main handoff generation
            $global:Query = $request.query
            $sessionCtx = Get-SessionContext
            $rhythmCtx = if (-not $SkipRhythm) { Get-RhythmContext } else { @{ Summary = "Skipped"; Details = "" } }
            $goalCtx = if (-not $SkipGoals) { Get-GoalContext } else { @{ Summary = "Skipped"; Details = "" } }
            $systemCtx = if (-not $SkipSystem) { Get-SystemContext } else { @{ Summary = "Skipped"; Details = "" } }
            $rclCtx = if (-not $SkipRcl) { Get-RclContext } else { @{ Summary = "Skipped"; Details = "" } }
            
            $report = Build-HandoffReport -SessionContext $sessionCtx -RhythmContext $rhythmCtx `
                -GoalContext $goalCtx -SystemContext $systemCtx -RclContext $rclCtx
            if ($report.Json.metadata.context_truncated) {
                $origLen = $report.Json.metadata.context_length
                $limitLen = $report.Json.metadata.context_limit
                Write-Log "Context trimmed ($origLen → $limitLen chars) for request $($request.request_id)" "WARN"
            }
            
            # Save response
            $responseId = $request.request_id
            $responseMdPath = Join-Path $script:ResponseDir "$responseId.md"
            $responseJsonPath = Join-Path $script:ResponseDir "$responseId.json"
            
            $report.Markdown | Out-File -FilePath $responseMdPath -Encoding UTF8 -Force
            $report.Json | ConvertTo-Json -Depth 10 | Out-File -FilePath $responseJsonPath -Encoding UTF8 -Force
            
            Write-Log "Response saved: $responseMdPath" "SUCCESS"
            Write-Log "Response JSON: $responseJsonPath" "SUCCESS"
        }
        
        # Move request to processed
        $processedPath = Join-Path $script:ProcessedDir (Split-Path -Leaf $RequestFilePath)
        Move-Item -LiteralPath $RequestFilePath -Destination $processedPath -Force
        Write-Log "Request moved to processed: $processedPath" "SUCCESS"
    }
    catch {
        Write-Log "Failed to process request: $_" "ERROR"
    }
}

function Process-DesignRequest {
    param(
        [hashtable]$Request,
        [string]$ResponseDir
    )
    
    Write-Log "Processing design request: $($Request.request_id)" "INFO"
    
    $designQuery = $Request.query
    $requestId = $Request.request_id
    
    # Extract design type from query
    $designType = "system"  # Default
    if ($designQuery -match "(workflow|pipeline|automation)") {
        $designType = "workflow"
    }
    elseif ($designQuery -match "(architecture|component|module)") {
        $designType = "architecture"
    }
    elseif ($designQuery -match "(integration|bridge|connection)") {
        $designType = "integration"
    }
    
    Write-Log "Detected design type: $designType" "INFO"
    
    # Generate design artifacts
    $designMd = @"
# Design Response: $requestId

**Query**: $designQuery
**Type**: $designType
**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Design Overview

This design addresses the following requirements:
- **Goal**: $designQuery
- **Type**: $designType
- **Scope**: System-level design

## Architecture

### Components
1. **Core Module**: Main processing logic
2. **Interface Layer**: Input/output handling
3. **Integration Points**: External system connections

### Data Flow
```
Input → Validation → Processing → Output → Storage
```

## Implementation Plan

1. **Phase 1**: Core component setup
2. **Phase 2**: Interface layer implementation
3. **Phase 3**: Integration testing
4. **Phase 4**: Production deployment

## Next Steps

- [ ] Review design with stakeholders
- [ ] Create implementation tickets
- [ ] Set up development environment
- [ ] Begin Phase 1 implementation

---
Generated by Lua Trinity Bridge
Request ID: $requestId
"@

    $designJson = @{
        request_id   = $requestId
        design_type  = $designType
        query        = $designQuery
        timestamp    = (Get-Date).ToUniversalTime().ToString("o")
        components   = @(
            @{ name = "Core Module"; description = "Main processing logic" }
            @{ name = "Interface Layer"; description = "Input/output handling" }
            @{ name = "Integration Points"; description = "External system connections" }
        )
        phases       = @(
            @{ phase = 1; name = "Core component setup"; status = "pending" }
            @{ phase = 2; name = "Interface layer implementation"; status = "pending" }
            @{ phase = 3; name = "Integration testing"; status = "pending" }
            @{ phase = 4; name = "Production deployment"; status = "pending" }
        )
        next_actions = @(
            "Review design with stakeholders"
            "Create implementation tickets"
            "Set up development environment"
            "Begin Phase 1 implementation"
        )
    }
    
    # Save artifacts
    $mdPath = Join-Path $ResponseDir "$requestId.md"
    $jsonPath = Join-Path $ResponseDir "$requestId.json"
    
    $designMd | Out-File -FilePath $mdPath -Encoding UTF8 -Force
    $designJson | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8 -Force
    
    Write-Log "Design artifacts saved: $mdPath, $jsonPath" "SUCCESS"
    
    return @{
        MdPath   = $mdPath
        JsonPath = $jsonPath
    }
}

function Start-RequestMonitor {
    param([int]$IntervalSec = 10)
    
    Write-Log "Starting request monitor (interval: ${IntervalSec}s)" "INFO"
    Write-Log "Watching directory: $script:RequestDir" "INFO"
    Write-Log "Press Ctrl+C to stop" "WARN"
    
    while ($true) {
        try {
            $requests = Get-ChildItem -Path $script:RequestDir -Filter "*.json" -File -ErrorAction SilentlyContinue
            
            foreach ($req in $requests) {
                Process-LuaRequest -RequestFilePath $req.FullName
            }
            
            Start-Sleep -Seconds $IntervalSec
        }
        catch {
            Write-Log "Monitor error: $_" "ERROR"
            Start-Sleep -Seconds $IntervalSec
        }
    }
}

function New-SampleRequest {
    $requestId = "sample_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    
    $sampleRequest = @{
        request_id = $requestId
        timestamp  = $timestamp
        query      = "현재 시스템 상태를 확인하고 다음 작업을 추천해주세요"
        signature  = ""
    }
    
    # Generate signature if HMAC key is set
    $hmacKey = [Environment]::GetEnvironmentVariable($script:Config.HmacKeyEnvVar, "User")
    if ($hmacKey) {
        $canonical = "$timestamp|$requestId|$($sampleRequest.query)"
        $sampleRequest.signature = Get-HmacSignature -Data $canonical -Key $hmacKey
    }
    else {
        Write-Log "HMAC key not set. Sample request will be unsigned." "WARN"
    }
    
    $samplePath = Join-Path $script:RequestDir "$requestId.json"
    $sampleRequest | ConvertTo-Json -Depth 5 | Out-File -FilePath $samplePath -Encoding UTF8 -Force
    
    Write-Log "Sample request generated: $samplePath" "SUCCESS"
    Write-Host "`nSample Request:" -ForegroundColor Cyan
    $sampleRequest | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Gray
}

# ============================================================================
# Main Entry Point (Updated)
# ============================================================================

# Run
try {
    if ($GenerateSample) {
        New-SampleRequest
        exit 0
    }
    
    if ($ProcessOnce) {
        $requests = Get-ChildItem -Path $script:RequestDir -Filter "*.json" -File -ErrorAction SilentlyContinue
        if ($requests.Count -eq 0) {
            Write-Log "No requests found in $script:RequestDir" "WARN"
            exit 0
        }
        
        foreach ($req in $requests) {
            Process-LuaRequest -RequestFilePath $req.FullName
        }
        exit 0
    }
    
    if ($Monitor) {
        Start-RequestMonitor -IntervalSec $MonitorIntervalSec
        exit 0
    }
    
    # Default: interactive query mode
    Main
    exit 0
}
catch {
    Write-Log "Fatal error: $_" "ERROR"
    Write-Log $_.ScriptStackTrace "ERROR"
    exit 1
}