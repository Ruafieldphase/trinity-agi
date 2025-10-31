# harvest_daily_conversations.ps1
# 4-Persona 일일 대화 수집 및 Resonance Ledger 기록
#
# Usage:
#   .\harvest_daily_conversations.ps1
#   .\harvest_daily_conversations.ps1 -Date "2025-10-30"
#   .\harvest_daily_conversations.ps1 -DryRun

param(
    [string]$Date = (Get-Date).ToString("yyyy-MM-dd"),
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# UTF-8 인코딩 설정 (폰트 깨짐 방지)
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
}
catch {}

# 설정
$GitkoPath = "C:\Users\kuirv\AppData\Roaming\Code\User\workspaceStorage"
$SenaPath = "C:\Users\kuirv\.claude\projects"
$LubitPath = "C:\Users\kuirv\.codex\sessions"
$LedgerPath = "D:\nas_backup\fdo_agi_repo\memory\resonance_ledger.jsonl"
$OutputDir = "C:\workspace\agi\outputs\session_harvests"

# 출력 디렉토리 생성
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  4-Persona Daily Conversation Harvester" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Date: $Date" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "Mode: DRY-RUN (no writes)" -ForegroundColor Yellow
}
Write-Host ""

# 타임스탬프
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
$targetDate = [DateTime]::Parse($Date)
$conversations = @()

# Emit harvest start event
& "$PSScriptRoot\emit_event.ps1" -EventType "session_harvest_started" -Payload @{
    date      = $Date
    timestamp = $timestamp
} -PersonaId "harvest_script"

# =============================================================================
# 1. Gitko (VS Code Copilot) - 당신과 나의 대화
# =============================================================================
Write-Host "[1/3] Harvesting Gitko (VS Code Copilot) conversations..." -ForegroundColor Cyan

try {
    # workspaceStorage에서 대화 파일 찾기 (파일 수정시간 + 내용 timestamp 모두 확인)
    $allGitkoFiles = Get-ChildItem -Path $GitkoPath -Recurse -File -Filter "*.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 50  # 후보 50개 선택

    $gitkoConvCount = 0
    $gitkoKeyPoints = @()
    $gitkoFiles = @()

    foreach ($file in $allGitkoFiles) {
        try {
            $content = Get-Content $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if (-not $content -or $content.Length -lt 100) { continue }

            $matchDate = $false
            
            # 1. 파일 수정 시간 확인
            if ($file.LastWriteTime.Date -eq $targetDate.Date) {
                $matchDate = $true
            }
            
            # 2. JSON 내용의 timestamp 필드 확인
            if (-not $matchDate -and $content -match '"timestamp"\s*:\s*"([^"]+)"') {
                try {
                    $contentTs = [DateTime]::Parse($Matches[1])
                    if ($contentTs.Date -eq $targetDate.Date) {
                        $matchDate = $true
                    }
                }
                catch { }
            }
            
            # 3. createdAt 필드 확인 (일부 파일)
            if (-not $matchDate -and $content -match '"createdAt"\s*:\s*"([^"]+)"') {
                try {
                    $contentTs = [DateTime]::Parse($Matches[1])
                    if ($contentTs.Date -eq $targetDate.Date) {
                        $matchDate = $true
                    }
                }
                catch { }
            }

            if ($matchDate) {
                $gitkoConvCount++
                $gitkoFiles += $file
                
                # 간단한 키워드 추출 (JSON 파싱 시도)
                if ($content -match '"request".*?"prompt".*?"(.*?)"') {
                    $prompt = $Matches[1].Substring(0, [Math]::Min(80, $Matches[1].Length))
                    $gitkoKeyPoints += $prompt
                }
            }
        }
        catch {
            # 파일 파싱 실패 시 조용히 무시
        }
        
        # 20개 찾으면 중단
        if ($gitkoConvCount -ge 20) { break }
    }

    $conversations += @{
        persona       = "Gitko"
        role          = "VS Code Copilot (GitHub 기반)"
        location      = $GitkoPath
        files_found   = $gitkoFiles.Count
        conversations = $gitkoConvCount
        key_points    = $gitkoKeyPoints | Select-Object -First 5
        timestamp     = $timestamp
    }

    Write-Host "  ✓ Found $gitkoConvCount conversations" -ForegroundColor Green
}
catch {
    Write-Host "  ⚠ Error accessing Gitko: $_" -ForegroundColor Yellow
}

# =============================================================================
# 2. Sena (Claude CLI)
# =============================================================================
Write-Host "[2/3] Harvesting Sena (Claude CLI) conversations..." -ForegroundColor Cyan

try {
    if (Test-Path $SenaPath) {
        $allSenaFiles = Get-ChildItem -Path $SenaPath -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 50

        $senaConvCount = 0
        $senaKeyPoints = @()
        $senaFiles = @()

        foreach ($file in $allSenaFiles) {
            try {
                $content = Get-Content $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
                if (-not $content -or $content.Length -lt 100) { continue }

                $matchDate = $false
                
                # 1. 파일 수정 시간 확인
                if ($file.LastWriteTime.Date -eq $targetDate.Date) {
                    $matchDate = $true
                }
                
                # 2. JSON 내용의 timestamp 확인
                if (-not $matchDate -and $content -match '"timestamp"\s*:\s*"([^"]+)"') {
                    try {
                        $contentTs = [DateTime]::Parse($Matches[1])
                        if ($contentTs.Date -eq $targetDate.Date) {
                            $matchDate = $true
                        }
                    }
                    catch { }
                }

                if ($matchDate) {
                    $senaConvCount++
                    $senaFiles += $file
                    
                    # Claude CLI는 보통 텍스트나 JSON 형식
                    if ($content -match 'User:|Human:|Request:') {
                        $excerpt = $content.Substring(0, [Math]::Min(100, $content.Length))
                        $senaKeyPoints += $excerpt
                    }
                }
            }
            catch {
                # 조용히 무시
            }
            
            if ($senaConvCount -ge 20) { break }
        }

        $conversations += @{
            persona       = "Sena"
            role          = "Claude CLI (터미널 기반)"
            location      = $SenaPath
            files_found   = $senaFiles.Count
            conversations = $senaConvCount
            key_points    = $senaKeyPoints | Select-Object -First 5
            timestamp     = $timestamp
        }

        Write-Host "  ✓ Found $senaConvCount conversations" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ Sena path not found: $SenaPath" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠ Error accessing Sena: $_" -ForegroundColor Yellow
}

# =============================================================================
# 3. Lubit (GPT Codex)
# =============================================================================
Write-Host "[3/3] Harvesting Lubit (GPT Codex) conversations..." -ForegroundColor Cyan

try {
    if (Test-Path $LubitPath) {
        $allLubitFiles = Get-ChildItem -Path $LubitPath -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 50

        $lubitConvCount = 0
        $lubitKeyPoints = @()
        $lubitFiles = @()

        foreach ($file in $allLubitFiles) {
            try {
                $content = Get-Content $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
                if (-not $content -or $content.Length -lt 100) { continue }

                $matchDate = $false
                
                # 1. 파일 수정 시간 확인
                if ($file.LastWriteTime.Date -eq $targetDate.Date) {
                    $matchDate = $true
                }
                
                # 2. JSON 내용의 timestamp 확인
                if (-not $matchDate -and $content -match '"timestamp"\s*:\s*"([^"]+)"') {
                    try {
                        $contentTs = [DateTime]::Parse($Matches[1])
                        if ($contentTs.Date -eq $targetDate.Date) {
                            $matchDate = $true
                        }
                    }
                    catch { }
                }
                
                # 3. created_at 필드 확인
                if (-not $matchDate -and $content -match '"created_at"\s*:\s*"([^"]+)"') {
                    try {
                        $contentTs = [DateTime]::Parse($Matches[1])
                        if ($contentTs.Date -eq $targetDate.Date) {
                            $matchDate = $true
                        }
                    }
                    catch { }
                }

                if ($matchDate) {
                    $lubitConvCount++
                    $lubitFiles += $file
                    
                    # Codex 세션 형식에 따라 파싱
                    if ($content -match '"prompt"|"input"|"query"') {
                        $excerpt = $content.Substring(0, [Math]::Min(100, $content.Length))
                        $lubitKeyPoints += $excerpt
                    }
                }
            }
            catch {
                # 조용히 무시
            }
            
            if ($lubitConvCount -ge 20) { break }
        }

        $conversations += @{
            persona       = "Lubit"
            role          = "GPT Codex (코딩 전문)"
            location      = $LubitPath
            files_found   = $lubitFiles.Count
            conversations = $lubitConvCount
            key_points    = $lubitKeyPoints | Select-Object -First 5
            timestamp     = $timestamp
        }

        Write-Host "  ✓ Found $lubitConvCount conversations" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ Lubit path not found: $LubitPath" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠ Error accessing Lubit: $_" -ForegroundColor Yellow
}

# =============================================================================
# 결과 요약
# =============================================================================
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Harvest Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$totalConversations = ($conversations | ForEach-Object { $_.conversations } | Measure-Object -Sum).Sum

foreach ($conv in $conversations) {
    Write-Host ""
    Write-Host "[$($conv.persona)] $($conv.role)" -ForegroundColor Yellow
    Write-Host "  Location: $($conv.location)"
    Write-Host "  Files found: $($conv.files_found)"
    Write-Host "  Conversations: $($conv.conversations)"
    if ($conv.key_points.Count -gt 0) {
        Write-Host "  Sample topics:" -ForegroundColor Cyan
        $conv.key_points | ForEach-Object { Write-Host "    - $_" -ForegroundColor Gray }
    }
}

Write-Host ""
Write-Host "Total conversations found: $totalConversations" -ForegroundColor Green

# =============================================================================
# Resonance Ledger에 기록
# =============================================================================
if (-not $DryRun) {
    Write-Host ""
    Write-Host "Writing to Resonance Ledger..." -ForegroundColor Cyan

    $ledgerEvent = @{
        event               = "daily_conversation_harvest"
        date                = $Date
        personas            = @($conversations | ForEach-Object {
                @{
                    name          = $_.persona
                    role          = $_.role
                    conversations = $_.conversations
                    files         = $_.files_found
                }
            })
        total_conversations = $totalConversations
        harvest_timestamp   = $timestamp
        ts                  = $timestamp
    }

    $ledgerEvent | ConvertTo-Json -Compress | Out-File -Append -Encoding utf8 -FilePath $LedgerPath

    Write-Host "  ✓ Recorded to: $LedgerPath" -ForegroundColor Green
}

# =============================================================================
# JSON 출력 (선택적)
# =============================================================================
$outputFile = Join-Path $OutputDir "harvest_$($Date.Replace('-','')).json"
$conversations | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 -FilePath $outputFile

Write-Host ""
Write-Host "  ✓ Detailed output: $outputFile" -ForegroundColor Green

# =============================================================================
# 완료
# =============================================================================
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Harvest Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "  (Dry-run mode - no ledger write)" -ForegroundColor Yellow
}

# Emit harvest completion event
# Emit harvest completion event
# Derive per-persona counts from summary array
$gitkoEntry = $conversations | Where-Object { $_.persona -eq 'Gitko' } | Select-Object -First 1
$senaEntry = $conversations | Where-Object { $_.persona -eq 'Sena' }  | Select-Object -First 1
$lubitEntry = $conversations | Where-Object { $_.persona -eq 'Lubit' } | Select-Object -First 1

$gitkoCount = if ($gitkoEntry) { [int]$gitkoEntry.conversations } else { 0 }
$senaCount = if ($senaEntry) { [int]$senaEntry.conversations }  else { 0 }
$lubitCount = if ($lubitEntry) { [int]$lubitEntry.conversations } else { 0 }

& "$PSScriptRoot\emit_event.ps1" -EventType "session_harvest_completed" -Payload @{
    date        = $Date
    timestamp   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    gitko_count = $gitkoCount
    sena_count  = $senaCount
    lubit_count = $lubitCount
    total       = ($gitkoCount + $senaCount + $lubitCount)
    dry_run     = [bool]$DryRun
} -PersonaId "harvest_script"

exit 0
