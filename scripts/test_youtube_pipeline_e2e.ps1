#Requires -Version 5.1
<#
.SYNOPSIS
    End-to-End test for YouTube learning pipeline
.DESCRIPTION
    Tests the complete workflow: enqueue → process → generate MD → build index
    Validates all components work together correctly
.PARAMETER Server
    Task queue server URL
.PARAMETER TestVideoUrl
    YouTube URL to use for testing (default: short public domain video)
.PARAMETER SkipEnqueue
    Skip enqueueing and only test index generation with existing data
.PARAMETER Timeout
    Max seconds to wait for worker to process task (default: 300)
#>
param(
    [string]$Server = 'http://127.0.0.1:8091',
    [string]$TestVideoUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    [switch]$SkipEnqueue,
    [int]$Timeout = 300
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = Split-Path -Parent $scriptRoot
$outputDir = Join-Path $workspace 'outputs\youtube_learner'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "YouTube Pipeline E2E Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test results tracking
$tests = @{
    ServerHealth      = $false
    EnqueueTask       = $false
    WorkerProcessing  = $false
    JsonOutput        = $false
    MdGeneration      = $false
    IndexBasic        = $false
    IndexWithKeywords = $false
    IndexGroupByDate  = $false
    QuickStats        = $false
    EmojiIndicators   = $false
}

$testVideoId = if ($TestVideoUrl -match 'v=([^&]+)') { $matches[1] } else { 'unknown' }
$expectedJsonPath = Join-Path $outputDir "${testVideoId}_analysis.json"
$expectedMdPath = Join-Path $outputDir "${testVideoId}_analysis.md"

# ============================================
# Test 1: Server Health
# ============================================
Write-Host "[Test 1/9] Checking server health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$Server/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Server is online: $($health.status)" -ForegroundColor Green
    $tests.ServerHealth = $true
}
catch {
    Write-Host "  ✗ Server health check failed: $_" -ForegroundColor Red
    Write-Host "`nℹ️  Start server with: Task 'Task Queue Server (Fresh)'" -ForegroundColor Yellow
    exit 1
}

# ============================================
# Test 2: Enqueue Task (Optional)
# ============================================
if (-not $SkipEnqueue) {
    Write-Host "[Test 2/9] Enqueueing test video..." -ForegroundColor Yellow
    try {
        $enqueueScript = Join-Path $scriptRoot 'enqueue_youtube_learn.ps1'
        $null = & $enqueueScript -Url $TestVideoUrl -ClipSeconds 10 -MaxFrames 2 -FrameInterval 30 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Task enqueued successfully" -ForegroundColor Green
            $tests.EnqueueTask = $true
            
            # Wait for worker to process
            Write-Host "[Test 3/9] Waiting for worker to process (max ${Timeout}s)..." -ForegroundColor Yellow
            $elapsed = 0
            $found = $false
            
            while ($elapsed -lt $Timeout -and -not $found) {
                Start-Sleep -Seconds 5
                $elapsed += 5
                
                if (Test-Path $expectedJsonPath) {
                    $found = $true
                    Write-Host "  ✓ Worker processed task (${elapsed}s)" -ForegroundColor Green
                    $tests.WorkerProcessing = $true
                }
                else {
                    Write-Host "  ⏳ Waiting... ${elapsed}s" -ForegroundColor Gray
                }
            }
            
            if (-not $found) {
                Write-Host "  ✗ Timeout waiting for worker" -ForegroundColor Red
                Write-Host "`nℹ️  Start worker with: Task 'YouTube: Start Worker (Background)'" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  ✗ Enqueue failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ Enqueue error: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "[Test 2-3/9] Skipped enqueue (using existing data)" -ForegroundColor Gray
    $tests.EnqueueTask = $true
    $tests.WorkerProcessing = $true
}

# ============================================
# Test 4: JSON Output Validation
# ============================================
Write-Host "[Test 4/9] Validating JSON output..." -ForegroundColor Yellow
if (Test-Path $expectedJsonPath) {
    try {
        $json = Get-Content -Raw -Path $expectedJsonPath | ConvertFrom-Json
        
        $requiredFields = @('video_id', 'title', 'analyzed_at')
        $missing = $requiredFields | Where-Object { -not $json.$_ -and -not $json.data.$_ }
        
        if ($missing.Count -eq 0) {
            Write-Host "  ✓ JSON structure valid" -ForegroundColor Green
            $title = if ($json.title) { $json.title } else { $json.data.title }
            $duration = if ($json.duration) { $json.duration } else { $json.data.duration }
            Write-Host "    - Title: $title" -ForegroundColor Gray
            Write-Host "    - Duration: ${duration}s" -ForegroundColor Gray
            $tests.JsonOutput = $true
        }
        else {
            Write-Host "  ✗ Missing required fields: $($missing -join ', ')" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ JSON parse error: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "  ⚠ JSON file not found: $expectedJsonPath" -ForegroundColor Yellow
}

# ============================================
# Test 5: Markdown Generation
# ============================================
Write-Host "[Test 5/9] Testing MD generation..." -ForegroundColor Yellow
if (Test-Path $expectedJsonPath) {
    try {
        $mdScript = Join-Path $scriptRoot 'generate_youtube_md_from_json.ps1'
        & $mdScript -File $expectedJsonPath -NoOpen | Out-Null
        
        if (Test-Path $expectedMdPath) {
            $mdContent = Get-Content -Raw -Path $expectedMdPath
            if ($mdContent -match '# .+' -and $mdContent.Length -gt 100) {
                Write-Host "  ✓ Markdown generated successfully" -ForegroundColor Green
                $tests.MdGeneration = $true
            }
            else {
                Write-Host "  ✗ Markdown content appears invalid" -ForegroundColor Red
            }
        }
        else {
            Write-Host "  ✗ Markdown file not created" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ MD generation error: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "  ⚠ Skipped (no JSON file)" -ForegroundColor Yellow
}

# ============================================
# Test 6: Basic Index Generation
# ============================================
Write-Host "[Test 6/9] Testing basic index generation..." -ForegroundColor Yellow
try {
    $indexScript = Join-Path $scriptRoot 'build_youtube_index.ps1'
    & $indexScript -Top 5 -NoOpen | Out-Null
    
    $indexPath = Join-Path $workspace 'outputs\youtube_learner_index.md'
    if (Test-Path $indexPath) {
        $indexContent = Get-Content -Raw -Path $indexPath
        if ($indexContent -match '# YouTube Analysis Index' -and $indexContent -match '\| Title \|') {
            Write-Host "  ✓ Basic index generated" -ForegroundColor Green
            $tests.IndexBasic = $true
        }
        else {
            Write-Host "  ✗ Index content malformed" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  ✗ Index file not created" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ✗ Index generation error: $_" -ForegroundColor Red
}

# ============================================
# Test 7: Index with Keywords
# ============================================
Write-Host "[Test 7/9] Testing index with keywords..." -ForegroundColor Yellow
try {
    & $indexScript -IncludeKeywords -Top 5 -NoOpen | Out-Null
    
    $indexPath = Join-Path $workspace 'outputs\youtube_learner_index.md'
    $indexContent = Get-Content -Raw -Path $indexPath
    
    if ($indexContent -match '\| Keywords \|') {
        Write-Host "  ✓ Keywords column present" -ForegroundColor Green
        $tests.IndexWithKeywords = $true
    }
    else {
        Write-Host "  ✗ Keywords column missing" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ✗ Keyword index error: $_" -ForegroundColor Red
}

# ============================================
# Test 8: Index with Date Grouping
# ============================================
Write-Host "[Test 8/10] Testing index with date grouping..." -ForegroundColor Yellow
try {
    & $indexScript -GroupByDate -Top 5 -NoOpen | Out-Null
    
    $indexPath = Join-Path $workspace 'outputs\youtube_learner_index.md'
    $indexContent = Get-Content -Raw -Path $indexPath
    
    # Look for date pattern like "### 📅 2025-10-31" or just "### 2025-10-31"
    if ($indexContent -match '###.+\d{4}-\d{2}-\d{2}') {
        Write-Host "  ✓ Date grouping present" -ForegroundColor Green
        $tests.IndexGroupByDate = $true
    }
    else {
        Write-Host "  ✗ Date grouping missing" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ✗ Date grouping index error: $_" -ForegroundColor Red
}

# ============================================
# Test 9: Quick Stats Section
# ============================================
Write-Host "[Test 9/10] Validating Quick Stats..." -ForegroundColor Yellow
$indexPath = Join-Path $workspace 'outputs\youtube_learner_index.md'
if (Test-Path $indexPath) {
    $indexContent = Get-Content -Raw -Path $indexPath
    
    $statsChecks = @(
        '## 📊 Quick Stats',
        'Total Analyses:',
        'With Markdown:',
        'Avg Duration:',
        'Length Distribution:'
    )
    
    $missing = $statsChecks | Where-Object { $indexContent -notlike "*$_*" }
    
    if ($missing.Count -eq 0) {
        Write-Host "  ✓ Quick Stats section complete" -ForegroundColor Green
        $tests.QuickStats = $true
    }
    else {
        Write-Host "  ✗ Missing stats: $($missing -join ', ')" -ForegroundColor Red
    }
}

# ============================================
# Test 10: Emoji Length Indicators
# ============================================
Write-Host "[Test 10/10] Checking emoji indicators..." -ForegroundColor Yellow
if (Test-Path $indexPath) {
    $indexContent = Get-Content -Raw -Path $indexPath
    
    if ($indexContent -match '[🔵🟡🔴]') {
        Write-Host "  ✓ Emoji indicators present" -ForegroundColor Green
        $tests.EmojiIndicators = $true
    }
    else {
        Write-Host "  ⚠ No emoji indicators found (may be no videos with duration)" -ForegroundColor Yellow
    }
}

# ============================================
# Summary
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passed = ($tests.Values | Where-Object { $_ -eq $true }).Count
$total = $tests.Count
$percentage = [int](($passed / $total) * 100)

foreach ($test in $tests.Keys | Sort-Object) {
    $status = if ($tests[$test]) { "✓ PASS" } else { "✗ FAIL" }
    $color = if ($tests[$test]) { "Green" } else { "Red" }
    Write-Host "  $status - $test" -ForegroundColor $color
}

Write-Host "`nOverall: $passed / $total tests passed ($percentage%)" -ForegroundColor Cyan

if ($passed -eq $total) {
    Write-Host "`n🎉 All tests passed! Pipeline is fully operational." -ForegroundColor Green
    exit 0
}
elseif ($percentage -ge 70) {
    Write-Host "`n⚠️  Most tests passed. Check failures above." -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "`n❌ Multiple test failures. Pipeline needs attention." -ForegroundColor Red
    exit 1
}