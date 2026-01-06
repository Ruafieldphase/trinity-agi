#Requires -Version 5.1
<#
.SYNOPSIS
    Morning resonance digest - 최근 Resonance 이벤트의 요약 (ledger lookback).
.DESCRIPTION
    - Resonance ledger 최근 (기본 12시간) 항목 추출
    - 정책별 이벤트 분류
    - 핵심 지표: 총 이벤트, 정책별 분포, 평균 신뢰도/품질
.EXAMPLE
    .\morning_resonance_digest.ps1
    .\morning_resonance_digest.ps1 -Hours 24
    .\morning_resonance_digest.ps1 -Hours 24 -OpenMarkdown
#>

param(
    [int]$Hours = 12,
    [switch]$OpenMarkdown,
    [string]$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) = ""
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "|   Morning Resonance Digest                  |" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

# Ledger 경로 (여러 가능한 위치 시도)
$ledgerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
if (-not (Test-Path $ledgerPath)) {
    # 다른 경로들 시도
    $altPaths = @(
        (Join-Path (Join-Path $WorkspaceRoot "fdo_agi_repo") "memory\resonance_ledger.jsonl"),
        (Join-Path (Split-Path -Parent $WorkspaceRoot) "fdo_agi_repo\memory\resonance_ledger.jsonl"),
        "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
    )
    foreach ($alt in $altPaths) {
        if (Test-Path $alt) {
            $ledgerPath = $alt
            break
        }
    }
}

if (-not (Test-Path $ledgerPath)) {
    Write-Host "WARNING: Resonance ledger not found: $ledgerPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Reading resonance ledger from: $ledgerPath" -ForegroundColor Gray

# 시간 윈도우 계산
$cutoffTime = [DateTime]::Now.AddHours(-$Hours)
$events = @()

try {
    $lineNum = 0
    Get-Content -Path $ledgerPath -ErrorAction Stop | ForEach-Object {
        $lineNum++
        if (-not $_) { return }
        try {
            $line = $_ | ConvertFrom-Json -ErrorAction Stop
            if ($line.Timestamp) {
                $eventTime = [DateTime]::Parse($line.Timestamp)
                if ($eventTime -gt $cutoffTime) {
                    $events += $line
                }
            }
        }
        catch {
            # Skip malformed lines silently
        }
    }
    Write-Host "  Loaded $($events.Count) events in last $Hours hours." -ForegroundColor Green
}
catch {
    Write-Host "ERROR reading ledger: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if ($events.Count -eq 0) {
    Write-Host "  No resonance events found in this window." -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# 요약 통계
Write-Host "`nSummary Statistics:" -ForegroundColor Cyan
Write-Host "  Total Events: $($events.Count)"

# 정책별 분포
$policyGroups = $events | Group-Object -Property 'Policy' -AsHashTable -AsString
Write-Host "  By Policy:"
foreach ($policy in ($policyGroups.Keys | Sort-Object)) {
    $count = $policyGroups[$policy].Count
    Write-Host "    - $policy : $count" -ForegroundColor Gray
}

# 신뢰도/품질 평균 (있으면)
$confAll = @()
$qualAll = @()
foreach ($evt in $events) {
    if ($evt.Confidence -and $evt.Confidence -isnot [string]) {
        $confAll += [float]$evt.Confidence
    }
    if ($evt.Quality -and $evt.Quality -isnot [string]) {
        $qualAll += [float]$evt.Quality
    }
}

if ($confAll.Count -gt 0) {
    $avgConf = ($confAll | Measure-Object -Average).Average
    Write-Host "  Avg Confidence: $([Math]::Round($avgConf, 3))"
}
if ($qualAll.Count -gt 0) {
    $avgQual = ($qualAll | Measure-Object -Average).Average
    Write-Host "  Avg Quality: $([Math]::Round($avgQual, 3))"
}

# 마크다운 저장 (선택)
$outputDir = Join-Path $WorkspaceRoot "outputs"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$mdPath = Join-Path $outputDir "morning_resonance_digest_latest.md"

try {
    $sb = New-Object System.Text.StringBuilder
    $null = $sb.AppendLine("# Morning Resonance Digest")
    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("- **Timestamp**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $null = $sb.AppendLine("- **Window**: Last $Hours hours")
    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("## Summary")
    $null = $sb.AppendLine("- **Total Events**: $($events.Count)")
    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("## By Policy")
    foreach ($policy in ($policyGroups.Keys | Sort-Object)) {
        $count = $policyGroups[$policy].Count
        $null = $sb.AppendLine("- **$policy**: $count events")
    }
    $null = $sb.AppendLine("")
    if ($confAll.Count -gt 0) {
        $avgConf = ($confAll | Measure-Object -Average).Average
        $null = $sb.AppendLine("- **Avg Confidence**: $([Math]::Round($avgConf, 3))")
    }
    if ($qualAll.Count -gt 0) {
        $avgQual = ($qualAll | Measure-Object -Average).Average
        $null = $sb.AppendLine("- **Avg Quality**: $([Math]::Round($avgQual, 3))")
    }
    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("## Recent Events (Last 10)")
    $recentCount = 0
    foreach ($evt in ($events | Sort-Object -Property Timestamp -Descending | Select-Object -First 10)) {
        $recentCount++
        $ts = if ($evt.Timestamp) { $evt.Timestamp } else { "?" }
        $pol = if ($evt.Policy) { $evt.Policy } else { "?" }
        $msg = if ($evt.Message) { $evt.Message } else { "" }
        $null = $sb.AppendLine("$recentCount. **[$ts] $pol** - $msg")
    }
    
    [IO.File]::WriteAllText($mdPath, $sb.ToString(), [Text.UTF8Encoding]::new($false))
    Write-Host "`nDigest saved: $mdPath" -ForegroundColor Green
    
    if ($OpenMarkdown) {
        try {
            code $mdPath
            Write-Host "  Opened in editor." -ForegroundColor Gray
        }
        catch {
            Write-Host "  Could not open editor (continuing)." -ForegroundColor Gray
        }
    }
}
catch {
    Write-Host "`nWARNING: Could not save digest: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
exit 0