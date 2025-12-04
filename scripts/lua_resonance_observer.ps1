# lua_resonance_observer.ps1
# 루아 (정인/正人) - Resonance 감응 관찰자
# 역할: "무슨 일이 일어나고 있는가?" - 있는 그대로 관찰

[CmdletBinding()]
param(
    [int]$Hours = 24,
    [string]$OutJson = "",
    [string]$OutMd = "",
    [switch]$OpenMd
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

# 기본 출력 경로 설정
if (-not $OutJson) {
    $OutJson = Join-Path $RepoRoot "outputs\lua_observation_latest.json"
}
if (-not $OutMd) {
    $OutMd = Join-Path $RepoRoot "outputs\lua_observation_latest.md"
}
$LedgerPath = Join-Path $RepoRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"

Write-Host "🔍 루아 (정인) - Resonance 감응 관찰" -ForegroundColor Cyan
Write-Host "   정(正): 무슨 일이 일어나고 있는가?" -ForegroundColor DarkCyan
Write-Host ""

# 1. Ledger 존재 확인
if (-not (Test-Path $LedgerPath)) {
    Write-Host "❌ Ledger not found: $LedgerPath" -ForegroundColor Red
    exit 1
}

Write-Host "📂 Loading: $LedgerPath" -ForegroundColor Gray

# 2. JSONL 파싱
$Cutoff = (Get-Date).AddHours(-$Hours).ToUniversalTime()
$CutoffTs = [int]([DateTimeOffset]$Cutoff).ToUnixTimeSeconds()

$Events = @()
$LineCount = 0
Get-Content $LedgerPath -Encoding UTF8 | ForEach-Object {
    $LineCount++
    $line = $_.Trim()
    if ($line) {
        try {
            $evt = $_ | ConvertFrom-Json
            if ($evt.ts -ge $CutoffTs) {
                $Events += $evt
            }
        }
        catch {
            # 파싱 실패는 조용히 무시 (정인은 판단하지 않음)
        }
    }
}

Write-Host "   Total lines: $LineCount" -ForegroundColor Gray
Write-Host "   Events in window: $($Events.Count)" -ForegroundColor Green
Write-Host ""

# 3. 정(正) - 있는 그대로 관찰 (판단 없이)
Write-Host "🔎 정(正) 관찰 결과:" -ForegroundColor Yellow

# 이벤트 타입 빈도
$TypeCount = @{}
$Events | ForEach-Object {
    $type = if ($_.event) { $_.event } elseif ($_.type) { $_.type } else { "unknown" }
    if (-not $TypeCount.ContainsKey($type)) {
        $TypeCount[$type] = 0
    }
    $TypeCount[$type]++
}

Write-Host "   Event types observed:" -ForegroundColor Gray
$TypeCount.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
    Write-Host "      $($_.Key): $($_.Value)" -ForegroundColor White
}
Write-Host ""

# Task 분포
$TaskCount = @{}
$Events | Where-Object { $_.task_id } | ForEach-Object {
    $tid = $_.task_id
    if (-not $TaskCount.ContainsKey($tid)) {
        $TaskCount[$tid] = 0
    }
    $TaskCount[$tid]++
}

Write-Host "   Unique tasks: $($TaskCount.Count)" -ForegroundColor Gray
if ($TaskCount.Count -gt 0) {
    $TopTasks = $TaskCount.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 5
    Write-Host "   Top 5 active tasks:" -ForegroundColor Gray
    $TopTasks | ForEach-Object {
        Write-Host "      $($_.Key): $($_.Value) events" -ForegroundColor White
    }
}
Write-Host ""

# 품질 분포 (있으면)
$WithQuality = $Events | Where-Object { $null -ne $_.quality }
if ($WithQuality.Count -gt 0) {
    $AvgQuality = ($WithQuality | Measure-Object -Property quality -Average).Average
    $MinQuality = ($WithQuality | Measure-Object -Property quality -Minimum).Minimum
    $MaxQuality = ($WithQuality | Measure-Object -Property quality -Maximum).Maximum
    
    Write-Host "   Quality metrics observed:" -ForegroundColor Gray
    Write-Host "      Count: $($WithQuality.Count)" -ForegroundColor White
    Write-Host "      Average: $([math]::Round($AvgQuality, 3))" -ForegroundColor White
    Write-Host "      Range: $([math]::Round($MinQuality, 3)) - $([math]::Round($MaxQuality, 3))" -ForegroundColor White
}
Write-Host ""

# Latency 분포 (있으면)
$WithLatency = $Events | Where-Object { $null -ne $_.latency }
if ($WithLatency.Count -gt 0) {
    $AvgLatency = ($WithLatency | Measure-Object -Property latency -Average).Average
    $MinLatency = ($WithLatency | Measure-Object -Property latency -Minimum).Minimum
    $MaxLatency = ($WithLatency | Measure-Object -Property latency -Maximum).Maximum
    
    Write-Host "   Latency observed:" -ForegroundColor Gray
    Write-Host "      Count: $($WithLatency.Count)" -ForegroundColor White
    Write-Host "      Average: $([math]::Round($AvgLatency, 2))s" -ForegroundColor White
    Write-Host "      Range: $([math]::Round($MinLatency, 2))s - $([math]::Round($MaxLatency, 2))s" -ForegroundColor White
}
Write-Host ""

# 4. JSON 출력 (정인은 가공하지 않고 관찰만)
$Observation = [ordered]@{
    observer         = "lua"
    persona          = "정인(正人)"
    role             = "관찰"
    philosophy       = "무슨 일이 일어나고 있는가?"
    timestamp        = (Get-Date).ToUniversalTime().ToString("o")
    window_hours     = $Hours
    ledger_path      = $LedgerPath
    total_lines      = $LineCount
    events_in_window = $Events.Count
    event_types      = $TypeCount
    unique_tasks     = $TaskCount.Count
    top_tasks        = @{}
    quality_metrics  = $null
    latency_metrics  = $null
}

# Top tasks
if ($TaskCount.Count -gt 0) {
    $TopTasks = $TaskCount.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 10
    $Observation.top_tasks = @{}
    $TopTasks | ForEach-Object {
        $Observation.top_tasks[$_.Key] = $_.Value
    }
}

# Quality
if ($WithQuality.Count -gt 0) {
    $Observation.quality_metrics = @{
        count   = $WithQuality.Count
        average = [math]::Round($AvgQuality, 3)
        min     = [math]::Round($MinQuality, 3)
        max     = [math]::Round($MaxQuality, 3)
    }
}

# Latency
if ($WithLatency.Count -gt 0) {
    $Observation.latency_metrics = @{
        count   = $WithLatency.Count
        average = [math]::Round($AvgLatency, 2)
        min     = [math]::Round($MinLatency, 2)
        max     = [math]::Round($MaxLatency, 2)
    }
}

# JSON 저장
$OutDir = Split-Path -Parent $OutJson
if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$Observation | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutJson -Encoding UTF8
Write-Host "💾 JSON saved: $OutJson" -ForegroundColor Green

# 5. Markdown 보고서
$MdContent = @"
# 루아 (정인/正人) - Resonance 감응 관찰 보고서

**정(正): 무슨 일이 일어나고 있는가?**

- **생성 시각**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **관찰 기간**: 최근 $Hours 시간
- **Ledger**: ``$LedgerPath``

---

## 📊 관찰 요약

- **총 라인 수**: $LineCount
- **윈도우 내 이벤트**: $($Events.Count)
- **고유 Task 수**: $($TaskCount.Count)

---

## 🔍 이벤트 타입 분포

| 타입 | 발생 횟수 |
|------|-----------|
"@

$TypeCount.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
    $MdContent += "| $($_.Key) | $($_.Value) |`n"
}

$MdContent += @"

---

## 📋 활동적인 Task (Top 10)

| Task ID | 이벤트 수 |
|---------|-----------|
"@

if ($TaskCount.Count -gt 0) {
    $TopTasks = $TaskCount.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 10
    $TopTasks | ForEach-Object {
        $MdContent += "| ``$($_.Key)`` | $($_.Value) |`n"
    }
}
else {
    $MdContent += "| (없음) | - |`n"
}

$MdContent += @"

---

## 📈 품질 메트릭 (관찰됨)

"@

if ($WithQuality.Count -gt 0) {
    $MdContent += @"
- **개수**: $($WithQuality.Count)
- **평균**: $([math]::Round($AvgQuality, 3))
- **범위**: $([math]::Round($MinQuality, 3)) ~ $([math]::Round($MaxQuality, 3))
"@
}
else {
    $MdContent += "- (품질 메트릭 없음)`n"
}

$MdContent += @"

---

## ⏱️ Latency 관찰

"@

if ($WithLatency.Count -gt 0) {
    $MdContent += @"
- **개수**: $($WithLatency.Count)
- **평균**: $([math]::Round($AvgLatency, 2))s
- **범위**: $([math]::Round($MinLatency, 2))s ~ $([math]::Round($MaxLatency, 2))s
"@
}
else {
    $MdContent += "- (Latency 데이터 없음)`n"
}

$MdContent += @"

---

## 🧘 정인(正人)의 관찰 철학

> **"무슨 일이 일어나고 있는가?"**
> 
> 정(正)은 판단하지 않고, 비판하지 않으며, 있는 그대로 관찰합니다.
> 
> - ✅ 직접 관찰
> - ✅ 사실 기록
> - ❌ 평가 배제
> - ❌ 해석 배제
> 
> **다음 단계**: 엘로 (반인/反人)가 비판적으로 검증합니다.

---

*Generated by Lua (正人) Observer at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")*
"@

$MdContent | Out-File -FilePath $OutMd -Encoding UTF8
Write-Host "📄 Markdown saved: $OutMd" -ForegroundColor Green

if ($OpenMd) {
    Write-Host "📂 Opening report..." -ForegroundColor Cyan
    Start-Process "code" -ArgumentList $OutMd
}

Write-Host ""
Write-Host "✅ 루아 (정인) 관찰 완료" -ForegroundColor Green
Write-Host "   다음: 엘로 (반인)가 검증할 차례입니다." -ForegroundColor DarkGray

exit 0
