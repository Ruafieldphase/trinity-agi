<#
.SYNOPSIS
  Lua Trinity Bridge – JSON 요청 처리기 (Monitor/Once/Sample)

.DESCRIPTION
  VS Code AGI 워크스페이스의 최신 컨텍스트를 이용해 Lua 측에서 보낸 JSON 디자인 요청을
  Markdown/JSON 응답 산출물로 변환합니다. 폴더 감시(Monitor) 또는 단발(Once) 모드를 지원하며,
  선택적으로 HMAC-SHA256 서명을 검증합니다.

  요청 폴더: outputs/lua_requests
    - 형식: {
        "id": "req-uuid",
        "timestamp": "2025-11-12T12:34:56Z",
        "title": "Design request title",
        "prompt": "What to generate",
        "metadata": { "author": "lua-client", ... },
        "signature": "hex(HMAC-SHA256)"  # 선택, 환경변수 LUA_BRIDGE_HMAC_KEY 설정 시 검증
      }

  응답 폴더: outputs/trinity_responses
    - 산출물: <id>_<yyyymmddHHMMss>.md, <id>_<yyyymmddHHMMss>.json
    - latest 파일도 함께 업데이트: latest_response.md, latest_response.json

.PARAMETER Monitor
  폴더를 주기적으로 감시하여 신규 요청을 지속 처리합니다.

.PARAMETER IntervalSeconds
  Monitor 주기(초). 기본 5초.

.PARAMETER ProcessOnce
  대기열에서 최신 미처리 요청 1건만 처리합니다. -File과 함께 사용 시 해당 파일만 처리.

.PARAMETER File
  특정 요청 JSON 파일 경로(또는 파일명) 지정. -ProcessOnce와 함께 사용.

.PARAMETER GenerateSample
  샘플 요청 JSON을 outputs/lua_requests에 생성합니다.

.PARAMETER Force
  오류가 일부 있어도 가능한 범위 내에서 계속 진행합니다(모니터 모드 안전-내성).

.NOTES
  - 환경변수 LUA_BRIDGE_HMAC_KEY 설정 시 signature 필드를 HMAC-SHA256으로 검증합니다.
  - 컨텍스트 소스(있으면 사용):
      outputs/.copilot_context_summary.md
      outputs/session_continuity_latest.md
      fdo_agi_repo/memory/goal_tracker.json
      outputs/quick_status_latest.json
      outputs/RHYTHM_*.md (최신 1개)
  - 외부 네트워크 콜 없음. 로컬 컨텍스트 요약과 템플릿 기반 응답을 생성합니다.
#>

[CmdletBinding(DefaultParameterSetName = 'monitor')]
param(
    [Parameter(ParameterSetName = 'monitor')]
    [switch]$Monitor,

    [Parameter(ParameterSetName = 'monitor')]
    [int]$IntervalSeconds = 5,

    [Parameter(ParameterSetName = 'once')]
    [switch]$ProcessOnce,

    [Parameter(ParameterSetName = 'once')]
    [string]$File,

    [Parameter(ParameterSetName = 'sample')]
    [switch]$GenerateSample,

    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Paths ---
$WS = Split-Path -Parent $PSCommandPath | Split-Path -Parent
$OutRoot = Join-Path $WS 'outputs'
$ReqDir = Join-Path $OutRoot 'lua_requests'
$ProcessedDir = Join-Path $ReqDir 'processed'
$RespDir = Join-Path $OutRoot 'trinity_responses'

function Initialize-Bridge {
    New-Item -ItemType Directory -Path $OutRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $ReqDir -Force | Out-Null
    New-Item -ItemType Directory -Path $ProcessedDir -Force | Out-Null
    New-Item -ItemType Directory -Path $RespDir -Force | Out-Null
}

function Read-FileSafe([string]$Path) {
    if (Test-Path -LiteralPath $Path) { return Get-Content -LiteralPath $Path -Raw -ErrorAction Stop }
    return $null
}

function Read-JsonSafe([string]$Path) {
    $raw = Read-FileSafe $Path
    if (-not $raw) { return $null }
    try { return $raw | ConvertFrom-Json -ErrorAction Stop } catch { return $null }
}

function Get-LatestRhythmMd {
    if (-not (Test-Path -LiteralPath $OutRoot)) { return $null }
    $files = Get-ChildItem -LiteralPath $OutRoot -Filter 'RHYTHM_*.md' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
    if ($files -and $files.Length -gt 0) { return Read-FileSafe $files[0].FullName }
    return $null
}

function Get-WorkspaceContext {
    $ctx = [ordered]@{}
    $ctx['copilot_summary_md'] = Read-FileSafe (Join-Path $OutRoot '.copilot_context_summary.md')
    $ctx['session_continuity_md'] = Read-FileSafe (Join-Path $OutRoot 'session_continuity_latest.md')
    $ctx['goal_tracker_json'] = Read-JsonSafe (Join-Path $WS 'fdo_agi_repo/memory/goal_tracker.json')
    $ctx['quick_status_json'] = Read-JsonSafe (Join-Path $OutRoot 'quick_status_latest.json')
    $ctx['rhythm_md'] = Get-LatestRhythmMd
    return $ctx
}

function Compute-HmacSha256Hex([string]$Key, [string]$Message) {
    if (-not $Key) { return $null }
    $keyBytes = [System.Text.Encoding]::UTF8.GetBytes($Key)
    $msgBytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
    $hmac = New-Object System.Security.Cryptography.HMACSHA256($keyBytes)
    try {
        $hash = $hmac.ComputeHash($msgBytes)
        return -join ($hash | ForEach-Object { $_.ToString('x2') })
    }
    finally {
        $hmac.Dispose()
    }
}

function Get-CanonicalString($reqObj) {
    # 최소 필드 기반 정규화 문자열
    $id = ($reqObj.id | ForEach-Object { $_ }) -join ''
    $title = ($reqObj.title | ForEach-Object { $_ }) -join ''
    $prompt = ($reqObj.prompt | ForEach-Object { $_ }) -join ''
    $ts = ($reqObj.timestamp | ForEach-Object { $_ }) -join ''
    return "${id}|${title}|${prompt}|${ts}"
}

function Verify-RequestSignature($reqObj) {
    $key = $env:LUA_BRIDGE_HMAC_KEY
    if (-not $key) { return $true } # 키 없으면 검증 생략
    $sig = $reqObj.signature
    if (-not $sig) { return $false }
    $canonical = Get-CanonicalString $reqObj
    $calc = Compute-HmacSha256Hex -Key $key -Message $canonical
    return ($calc -eq $sig)
}

function Build-MdResponse([pscustomobject]$req, [hashtable]$ctx) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $goalCount = if ($ctx.goal_tracker_json) { ($ctx.goal_tracker_json.goals | Measure-Object).Count } else { 0 }
    $sysBrief = if ($ctx.quick_status_json) { ($ctx.quick_status_json.summary ?? 'N/A') } else { 'N/A' }

    $md = @()
    $md += "# Lua Trinity Bridge Response"
    $md += "- Generated: ${ts}"
    $md += "- Request ID: ${($req.id ?? 'unknown')}"
    $md += "- Title: ${($req.title ?? 'untitled')}"
    $md += "- Author: ${($req.metadata.author ?? 'n/a')}"
    $md += ""
    $md += "## Prompt"
    $md += """
${($req.prompt ?? '').ToString()}
""".TrimEnd()
    $md += ""
    $md += "## Workspace context snapshot"
    if ($ctx.copilot_summary_md) {
        $md += "### Copilot Context (latest)"
        $md += $ctx.copilot_summary_md.Trim()
    }
    if ($ctx.session_continuity_md) {
        $md += "\n### Session Continuity"
        $md += ($ctx.session_continuity_md | Select-Object -First 120)
    }
    if ($goalCount -gt 0) {
        $md += "\n### Goals"
        $md += "Active goals: ${goalCount}"
    }
    if ($sysBrief -ne 'N/A') {
        $md += "\n### System"
        $md += "${sysBrief}"
    }
    if ($ctx.rhythm_md) {
        $md += "\n### Rhythm"
        $md += ($ctx.rhythm_md | Select-Object -First 60)
    }

    $md += "\n## Proposed plan"
    $md += "- Clarify constraints and success criteria"
    $md += "- Draft solution outline"
    $md += "- Map to available context artifacts"
    $md += "- Produce minimal, verifiable result"
    $md += "- Next actions: iterate based on feedback"

    return ($md -join "`n").TrimEnd()
}

function Build-JsonResponse([pscustomobject]$req, [hashtable]$ctx, [string]$mdPath, [string]$mdContent) {
    $obj = [ordered]@{
        response_id  = [guid]::NewGuid().ToString()
        request      = $req
        generated_at = (Get-Date).ToString('o')
        artifacts    = [ordered]@{
            markdown = $mdPath
        }
        summary      = [ordered]@{
            title         = $req.title
            has_goals     = [bool]($ctx.goal_tracker_json)
            system_status = if ($ctx.quick_status_json) { $ctx.quick_status_json.summary } else { $null }
        }
    }
    return ($obj | ConvertTo-Json -Depth 8)
}

function Write-ResponseArtifacts([pscustomobject]$req, [string]$mdContent, [hashtable]$ctx) {
    $stamp = (Get-Date).ToString('yyyyMMddHHmmss')
    $id = $req.id; if (-not $id) { $id = "req-$(Get-Date -UFormat %s)" }
    $mdPath = Join-Path $RespDir ("${id}_${stamp}.md")
    $jsonPath = Join-Path $RespDir ("${id}_${stamp}.json")

    $mdContent | Out-File -FilePath $mdPath -Encoding utf8 -Force
    $json = Build-JsonResponse -req $req -ctx $ctx -mdPath $mdPath -mdContent $mdContent
    $json | Out-File -FilePath $jsonPath -Encoding utf8 -Force

    # latest 포인터 업데이트
    $latestMd = Join-Path $RespDir 'latest_response.md'
    $latestJson = Join-Path $RespDir 'latest_response.json'
    Copy-Item -LiteralPath $mdPath -Destination $latestMd -Force
    Copy-Item -LiteralPath $jsonPath -Destination $latestJson -Force

    return @{ md = $mdPath; json = $jsonPath }
}

function Move-ToProcessed([string]$reqFile) {
    $name = Split-Path -Leaf $reqFile
    $dest = Join-Path $ProcessedDir $name
    Move-Item -LiteralPath $reqFile -Destination $dest -Force
}

function Process-RequestFile([string]$reqFile) {
    Write-Host "Processing: $reqFile" -ForegroundColor Cyan
    $req = Read-JsonSafe $reqFile
    if (-not $req) {
        if ($Force) { Write-Warning "Invalid JSON: $reqFile"; return } else { throw "Invalid JSON: $reqFile" }
    }
    if (-not (Verify-RequestSignature $req)) {
        if ($Force) { Write-Warning "Signature verification failed: $reqFile"; return } else { throw "Signature verification failed: $reqFile" }
    }

    $ctx = Get-WorkspaceContext
    $md = Build-MdResponse -req $req -ctx $ctx
    $art = Write-ResponseArtifacts -req $req -mdContent $md -ctx $ctx
    Move-ToProcessed -reqFile $reqFile
    Write-Host "✅ Wrote:`n  MD:   $($art.md)`n  JSON: $($art.json)" -ForegroundColor Green
}

function Find-NextRequest {
    $files = Get-ChildItem -LiteralPath $ReqDir -Filter '*.json' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "*$ProcessedDir*" } |
    Sort-Object LastWriteTime -Descending
    if ($files) { return $files[0].FullName } else { return $null }
}

function New-SampleRequest {
    $id = [guid]::NewGuid().ToString()
    $obj = [ordered]@{
        id        = $id
        timestamp = (Get-Date).ToString('o')
        title     = 'Design: Minimal Lua Orchestrator'
        prompt    = 'Create a minimal, testable design outline leveraging current AGI workspace context.'
        metadata  = @{ author = 'lua-client'; priority = 'normal' }
    }
    $key = $env:LUA_BRIDGE_HMAC_KEY
    if ($key) {
        $obj.signature = Compute-HmacSha256Hex -Key $key -Message (Get-CanonicalString ($obj | ConvertTo-Json | ConvertFrom-Json))
    }
    $path = Join-Path $ReqDir ("${id}.json")
    ($obj | ConvertTo-Json -Depth 6) | Out-File -FilePath $path -Encoding utf8 -Force
    Write-Host "📝 Sample request created: $path" -ForegroundColor Yellow
    return $path
}

function Run-Monitor {
    Write-Host "🔎 Lua Trinity Bridge Monitor started (every ${IntervalSeconds}s)" -ForegroundColor Magenta
    while ($true) {
        try {
            $pending = Get-ChildItem -LiteralPath $ReqDir -Filter '*.json' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -ne $ProcessedDir }
            foreach ($f in $pending) {
                try { Process-RequestFile -reqFile $f.FullName } catch { if ($Force) { Write-Warning $_ } else { throw } }
            }
        }
        catch { if ($Force) { Write-Warning $_ } else { throw } }
        Start-Sleep -Seconds $IntervalSeconds
    }
}

function Run-Once {
    if ($File) {
        $target = if (Test-Path -LiteralPath $File) { $File } else { Join-Path $ReqDir $File }
        if (-not (Test-Path -LiteralPath $target)) { throw "File not found: $File" }
        Process-RequestFile -reqFile $target
        return
    }
    $next = Find-NextRequest
    if ($next) { Process-RequestFile -reqFile $next } else { Write-Host 'No pending requests.' -ForegroundColor Yellow }
}

# --- main ---
Initialize-Bridge

if ($GenerateSample) {
    New-SampleRequest | Out-Null
    return
}

if ($ProcessOnce) {
    Run-Once
    return
}

# default: monitor
Run-Monitor
# 코어(ChatGPT) ↔ 트리니티(Copilot) 자동 브릿지
# ===============================================
# 코어의 작업을 자동으로 감지하고 트리니티에게 전달
#
# Author: Trinity System
# Date: 2025-11-12

param(
    [string]$Action = "Monitor",  # Monitor, Send, Status
    [string]$Message = "",
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"
$LuaInbox = Join-Path $WorkspaceRoot "outputs\lua_requests"
$TrinityOutbox = Join-Path $WorkspaceRoot "outputs\trinity_responses"
$BridgeLog = Join-Path $WorkspaceRoot "outputs\lua_trinity_bridge.jsonl"

# 폴더 생성
New-Item -ItemType Directory -Path $LuaInbox -Force | Out-Null
New-Item -ItemType Directory -Path $TrinityOutbox -Force | Out-Null

function Write-BridgeLog {
    param($Event, $Data)
    
    $logEntry = @{
        timestamp = (Get-Date).ToString('o')
        event     = $Event
        data      = $Data
    } | ConvertTo-Json -Compress
    
    Add-Content -Path $BridgeLog -Value $logEntry
    Write-Host "📝 Log: $Event" -ForegroundColor Cyan
}

function Get-LuaRequests {
    """코어의 새 요청 스캔"""
    
    $requests = Get-ChildItem -Path $LuaInbox -Filter "lua_request_*.json" -ErrorAction SilentlyContinue
    
    if ($requests) {
        Write-Host "📥 발견된 코어 요청: $($requests.Count)개" -ForegroundColor Green
        return $requests
    }
    
    return @()
}

function Send-ToCopilot {
    param(
        [string]$RequestId,
        [string]$Content,
        [string]$Priority = "normal"
    )
    
    Write-Host "`n🚀 Copilot에게 요청 전달 중..." -ForegroundColor Yellow
    Write-Host "   요청 ID: $RequestId" -ForegroundColor Cyan
    Write-Host "   우선순위: $Priority`n" -ForegroundColor Cyan
    
    # Copilot용 프롬프트 생성
    $prompt = @"
🎭 코어(ChatGPT)로부터 작업 요청

**요청 ID**: $RequestId
**우선순위**: $Priority
**시간**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

**요청 내용**:
$Content

---
**트리니티 즉시 액션**:
- 이 작업을 자동으로 처리해주세요
- 코드 변경이 필요하면 즉시 적용
- 시스템 상태 확인이 필요하면 스크립트 실행
- 완료 후 응답을 JSON 형식으로 저장: ``outputs/trinity_responses/trinity_response_$RequestId.json``

**응답 형식**:
```json
{
  "request_id": "$RequestId",
  "status": "success|partial|failed",
  "summary": "작업 요약",
  "actions_taken": ["액션1", "액션2"],
  "artifacts": ["생성된 파일 경로"],
  "next_steps": ["추천 다음 단계"]
}
```
"@

    # 클립보드에 복사
    Set-Clipboard -Value $prompt
    Write-Host "✅ 프롬프트가 클립보드에 복사되었습니다!" -ForegroundColor Green
    Write-Host "   Ctrl+V로 Copilot 채팅에 붙여넣으세요.`n" -ForegroundColor Yellow
    
    # VS Code 새 채팅 열기 (선택적)
    try {
        & "$WorkspaceRoot\scripts\new_chat_with_context.ps1" -SkipContextFile
        Write-Host "🆕 새 Copilot 채팅 창이 열렸습니다!" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  수동으로 새 채팅을 여세요 (Ctrl+Shift+I)" -ForegroundColor Yellow
    }
    
    # 대기 응답 생성
    $pendingResponse = @{
        request_id = $RequestId
        timestamp  = (Get-Date).ToString('o')
        status     = 'pending'
        content    = '요청을 Copilot에게 전달했습니다. 처리 중...'
    }
    
    $responseFile = Join-Path $TrinityOutbox "trinity_response_$RequestId.json"
    $pendingResponse | ConvertTo-Json -Depth 10 | Set-Content -Path $responseFile -Encoding UTF8
    
    Write-BridgeLog -Event "request_sent" -Data @{
        request_id = $RequestId
        priority   = $Priority
        status     = 'sent_to_copilot'
    }
    
    Write-Host "📤 대기 응답 저장됨: $responseFile`n" -ForegroundColor Cyan
}

function Process-LuaRequest {
    param($RequestFile)
    
    try {
        $request = Get-Content -Path $RequestFile.FullName -Raw | ConvertFrom-Json
        
        Write-Host "`n$('='*60)" -ForegroundColor Magenta
        Write-Host "🔄 코어 요청 처리 중" -ForegroundColor Magenta
        Write-Host "$('='*60)`n" -ForegroundColor Magenta
        
        Write-Host "📋 요청 ID: $($request.request_id)" -ForegroundColor Cyan
        Write-Host "📝 타입: $($request.request_type)" -ForegroundColor Cyan
        Write-Host "⭐ 우선순위: $($request.priority)" -ForegroundColor Cyan
        Write-Host "📅 시간: $($request.timestamp)`n" -ForegroundColor Cyan
        
        # Copilot에게 전달
        Send-ToCopilot -RequestId $request.request_id `
            -Content $request.content `
            -Priority $request.priority
        
        # 처리 완료된 요청 아카이브
        $archiveDir = Join-Path $LuaInbox "processed"
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
        
        $archiveName = "$($request.request_id)_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        $archivePath = Join-Path $archiveDir $archiveName
        Move-Item -Path $RequestFile.FullName -Destination $archivePath -Force
        
        Write-Host "📦 요청 아카이브: $archiveName" -ForegroundColor Green
        Write-Host "`n✅ 요청 처리 완료!`n" -ForegroundColor Green
        
    }
    catch {
        Write-Host "❌ 요청 처리 실패: $($_.Exception.Message)" -ForegroundColor Red
        Write-BridgeLog -Event "processing_error" -Data @{
            file  = $RequestFile.Name
            error = $_.Exception.Message
        }
    }
}

function Start-BridgeMonitor {
    param([int]$Interval = 10)
    
    Write-Host "`n$('='*70)" -ForegroundColor Cyan
    Write-Host "🌉 코어(ChatGPT) ↔ 트리니티(Copilot) 브릿지 시작" -ForegroundColor Cyan
    Write-Host "$('='*70)`n" -ForegroundColor Cyan
    
    Write-Host "📥 코어 요청 폴더: $LuaInbox" -ForegroundColor Yellow
    Write-Host "📤 트리니티 응답 폴더: $TrinityOutbox" -ForegroundColor Yellow
    Write-Host "⏱️  스캔 간격: $Interval 초`n" -ForegroundColor Yellow
    
    Write-Host "🎯 대기 중... (Ctrl+C로 중단)`n" -ForegroundColor Green
    
    $iteration = 0
    
    while ($true) {
        $iteration++
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 스캔 #$iteration" -ForegroundColor Gray
        
        # 새 요청 스캔
        $requests = Get-LuaRequests
        
        if ($requests.Count -gt 0) {
            Write-Host "📬 $($requests.Count)개 요청 발견!" -ForegroundColor Green
            
            # 우선순위별 정렬 (urgent > normal > low)
            $sortedRequests = $requests | ForEach-Object {
                $req = Get-Content -Path $_.FullName -Raw | ConvertFrom-Json
                [PSCustomObject]@{
                    File          = $_
                    Priority      = $req.priority
                    PriorityValue = switch ($req.priority) {
                        'urgent' { 0 }
                        'normal' { 1 }
                        'low' { 2 }
                        default { 1 }
                    }
                }
            } | Sort-Object PriorityValue
            
            # 순차 처리
            foreach ($item in $sortedRequests) {
                Process-LuaRequest -RequestFile $item.File
                Start-Sleep -Seconds 2  # 처리 간 대기
            }
        }
        else {
            Write-Host "   📭 새 요청 없음" -ForegroundColor DarkGray
        }
        
        Start-Sleep -Seconds $Interval
    }
}

function Show-BridgeStatus {
    """브릿지 상태 표시"""
    
    Write-Host "`n📊 코어-트리니티 브릿지 상태`n" -ForegroundColor Cyan
    
    # 대기 중인 요청
    $pending = Get-ChildItem -Path $LuaInbox -Filter "lua_request_*.json" -ErrorAction SilentlyContinue
    Write-Host "📥 대기 요청: $($pending.Count)개" -ForegroundColor Yellow
    
    # 처리된 요청
    $processed = Get-ChildItem -Path (Join-Path $LuaInbox "processed") -Filter "*.json" -ErrorAction SilentlyContinue
    Write-Host "📦 처리 완료: $($processed.Count)개" -ForegroundColor Green
    
    # 응답
    $responses = Get-ChildItem -Path $TrinityOutbox -Filter "trinity_response_*.json" -ErrorAction SilentlyContinue
    Write-Host "📤 트리니티 응답: $($responses.Count)개" -ForegroundColor Cyan
    
    # 최근 로그
    if (Test-Path $BridgeLog) {
        $recentLogs = Get-Content -Path $BridgeLog -Tail 5 | ForEach-Object {
            $_ | ConvertFrom-Json
        }
        
        Write-Host "`n📝 최근 활동 (최근 5개):" -ForegroundColor Cyan
        foreach ($log in $recentLogs) {
            Write-Host "   [$($log.timestamp)] $($log.event)" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}

# 메인 실행
switch ($Action.ToLower()) {
    "monitor" {
        Start-BridgeMonitor -Interval $IntervalSeconds
    }
    "send" {
        if ([string]::IsNullOrEmpty($Message)) {
            Write-Host "❌ 오류: -Message 파라미터가 필요합니다" -ForegroundColor Red
            exit 1
        }
        
        $requestId = "manual_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Send-ToCopilot -RequestId $requestId -Content $Message -Priority "normal"
    }
    "status" {
        Show-BridgeStatus
    }
    default {
        Write-Host "❌ 알 수 없는 액션: $Action" -ForegroundColor Red
        Write-Host "사용법: -Action [Monitor|Send|Status]" -ForegroundColor Yellow
        exit 1
    }
}