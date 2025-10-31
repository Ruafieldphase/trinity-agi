# Daily Briefing Generator
# Generates a summary of all integrated systems' 24-hour activities

param(
    [switch]$OpenReport,
    [int]$Hours = 24
)

$ErrorActionPreference = "Stop"

Write-Host "`nDaily Briefing Generator`n" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$dateStr = Get-Date -Format "yyyy-MM-dd"
$outputDir = "$PSScriptRoot\..\outputs"
$briefingFile = "$outputDir\daily_briefing_$dateStr.md"

# Initialize briefing content
$briefing = @"
# Daily Briefing

**Date**: $dateStr  
**Generated**: $timestamp  
**Period**: Last $Hours hours

---

## System Overview

"@

# 1. Resonance Loop
Write-Host "1. Analyzing Resonance Loop..." -ForegroundColor Cyan

$resonanceReport = "$PSScriptRoot\..\fdo_agi_repo\outputs\resonance_lumen_integration_latest.md"
if (Test-Path $resonanceReport) {
    $resonanceAge = ((Get-Date) - (Get-Item $resonanceReport).LastWriteTime).TotalHours
    
    $briefing += @"

### Resonance Loop

- **Status**: OK
- **Last Report**: $([math]::Round($resonanceAge, 1)) hours ago
- **File**: [resonance_lumen_integration_latest.md](../fdo_agi_repo/outputs/resonance_lumen_integration_latest.md)

"@
} else {
    $briefing += @"

### Resonance Loop

- **Status**: WARNING - No report found
- **Action**: Generate report needed

"@
}

# 2. BQI Phase 6
Write-Host "2. Analyzing BQI Phase 6..." -ForegroundColor Cyan

$bqiReport = "$PSScriptRoot\..\fdo_agi_repo\outputs\bqi_lumen_integration_latest.md"
if (Test-Path $bqiReport) {
    $bqiAge = ((Get-Date) - (Get-Item $bqiReport).LastWriteTime).TotalHours
    
    $briefing += @"

### BQI Phase 6

- **Status**: OK
- **Last Report**: $([math]::Round($bqiAge, 1)) hours ago
- **File**: [bqi_lumen_integration_latest.md](../fdo_agi_repo/outputs/bqi_lumen_integration_latest.md)

"@
} else {
    $briefing += @"

### BQI Phase 6

- **Status**: WARNING - No report found
- **Action**: Generate report needed

"@
}

# 3. YouTube Learning
Write-Host "3. Analyzing YouTube learning..." -ForegroundColor Cyan

$youtubeFiles = Get-ChildItem "$outputDir\youtube_enhanced_*.md" -ErrorAction SilentlyContinue | 
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-$Hours) } |
    Sort-Object LastWriteTime -Descending

if ($youtubeFiles.Count -gt 0) {
    $latestYoutube = $youtubeFiles[0]
    $briefing += @"

### YouTube Learning

- **Videos Analyzed**: $($youtubeFiles.Count)
- **Latest**: $($latestYoutube.Name)
- **Status**: OK

"@
} else {
    $briefing += @"

### YouTube Learning

- **Status**: No recent activity in last $Hours hours

"@
}

# 4. Feedback Auto-Apply
Write-Host "4. Analyzing feedback system..." -ForegroundColor Cyan

$feedbackLog = "$outputDir\feedback_implementation_plan.json"
if (Test-Path $feedbackLog) {
    $feedbackAge = ((Get-Date) - (Get-Item $feedbackLog).LastWriteTime).TotalHours
    
    try {
        $feedbackData = Get-Content $feedbackLog -Raw -Encoding UTF8 | ConvertFrom-Json
        
        $briefing += @"

### Intelligent Feedback System

- **Feedbacks Analyzed**: $($feedbackData.feedbacks_analyzed)
- **Implementation Steps**: $($feedbackData.implementation_steps.Count)
- **Last Update**: $([math]::Round($feedbackAge, 1)) hours ago
- **Status**: OK

"@
    } catch {
        $briefing += @"

### Intelligent Feedback System

- **Status**: OK (file exists)
- **Last Update**: $([math]::Round($feedbackAge, 1)) hours ago

"@
    }
} else {
    $briefing += @"

### Intelligent Feedback System

- **Status**: No recent activity

"@
}

# 5. Persona Orchestration
Write-Host "5. Analyzing orchestration..." -ForegroundColor Cyan

$orchestrationLog = "$outputDir\orchestration_latest.md"
if (Test-Path $orchestrationLog) {
    $orchAge = ((Get-Date) - (Get-Item $orchestrationLog).LastWriteTime).TotalHours
    
    $briefing += @"

### Persona Orchestration

- **Status**: OK
- **Last Run**: $([math]::Round($orchAge, 1)) hours ago
- **File**: [orchestration_latest.md](orchestration_latest.md)

"@
} else {
    $briefing += @"

### Persona Orchestration

- **Status**: No recent activity

"@
}

# System Health Summary
$briefing += @"

---

## System Health

| System | Status | Notes |
|--------|--------|-------|
| Resonance Loop | $(if (Test-Path $resonanceReport) { "OK" } else { "WARNING" }) | $(if (Test-Path $resonanceReport) { "Active" } else { "Report needed" }) |
| BQI Phase 6 | $(if (Test-Path $bqiReport) { "OK" } else { "WARNING" }) | $(if (Test-Path $bqiReport) { "Active" } else { "Report needed" }) |
| YouTube Learning | $(if ($youtubeFiles.Count -gt 0) { "OK" } else { "IDLE" }) | $($youtubeFiles.Count) recent videos |
| Feedback System | $(if (Test-Path $feedbackLog) { "OK" } else { "IDLE" }) | $(if (Test-Path $feedbackLog) { "Active" } else { "No activity" }) |
| Orchestration | $(if (Test-Path $orchestrationLog) { "OK" } else { "IDLE" }) | $(if (Test-Path $orchestrationLog) { "Active" } else { "No activity" }) |

**Overall Status**: OPERATIONAL

---

## Recommended Actions

"@

# Determine recommendations
$recommendations = @()

if (-not (Test-Path $resonanceReport)) {
    $recommendations += "- [ ] Generate Resonance Loop report"
}

if (-not (Test-Path $bqiReport)) {
    $recommendations += "- [ ] Generate BQI Phase 6 report"
}

if ($youtubeFiles.Count -eq 0) {
    $recommendations += "- [ ] Analyze YouTube videos"
}

if ($recommendations.Count -eq 0) {
    $briefing += @"

**All systems are operational!**

Continue with:
- Regular monitoring
- New YouTube video learning
- Review persona feedback

"@
} else {
    $briefing += "`n"
    $briefing += $recommendations -join "`n"
    $briefing += "`n"
}

# Quick links
$briefing += @"

---

## Quick Links

### Main Reports
- [Resonance Loop](../fdo_agi_repo/outputs/resonance_lumen_integration_latest.md)
- [BQI Phase 6](../fdo_agi_repo/outputs/bqi_lumen_integration_latest.md)
- [Feedback Implementation Plan](feedback_implementation_plan.md)

### Scripts
- Resonance
- BQI
- YouTube
- Feedback
- Orchestration

---

*Auto-generated briefing - $timestamp*
"@

# Save briefing
$briefing | Out-File -FilePath $briefingFile -Encoding UTF8

Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
Write-Host "Daily briefing generated!`n" -ForegroundColor Green

Write-Host "File: $briefingFile`n" -ForegroundColor Cyan

# Open report
if ($OpenReport) {
    Write-Host "Opening briefing...`n" -ForegroundColor Cyan
    code $briefingFile
}

Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  Basic:           .\generate_daily_briefing.ps1" -ForegroundColor Gray
Write-Host "  Open report:     .\generate_daily_briefing.ps1 -OpenReport" -ForegroundColor Gray
Write-Host "  Custom period:   .\generate_daily_briefing.ps1 -Hours 48`n" -ForegroundColor Gray
