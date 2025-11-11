<#
.SYNOPSIS
Register all missing tasks with optimized schedule (avoiding dawn hours)

.DESCRIPTION
Registers 5 missing tasks with user-friendly schedule:
- 10:00 Trinity Cycle (Morning)
- 22:00 Auto Backup (Evening, before sleep)
- 14:00 & 20:00 Cache Validation (Afternoon & Evening)
- 16:00 YouTube Learner (Afternoon, optional)

.NOTES
Requires Administrator privileges
#>

param(
    [switch]$SkipYouTube,
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Check admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ Administrator privileges required" -ForegroundColor Red
    Write-Host "   Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Register Missing Tasks - Optimized Schedule              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

$registered = 0
$failed = 0

# 1. Trinity Cycle - 10:00 AM (Morning learning)
Write-Host "[1/5] Trinity Cycle (10:00 AM)..." -ForegroundColor Yellow
try {
    $script = Join-Path $WorkspaceRoot "scripts\register_trinity_cycle_task.ps1"
    if ($DryRun) {
        Write-Host "  [DryRun] Would register at 10:00" -ForegroundColor Cyan
    }
    else {
        & $script -Register -Time "10:00"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Trinity Cycle registered (Daily 10:00 AM)" -ForegroundColor Green
            $registered++
        }
        else {
            Write-Host "  ⚠️  May already be registered" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
    $failed++
}

# 2. Auto Backup - 22:00 (Evening, before sleep)
Write-Host "`n[2/5] Auto Backup (22:00 Evening)..." -ForegroundColor Yellow
try {
    $script = Join-Path $WorkspaceRoot "scripts\register_auto_backup.ps1"
    if ($DryRun) {
        Write-Host "  [DryRun] Would register at 22:00" -ForegroundColor Cyan
    }
    else {
        & $script -Register -Time "22:00"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Auto Backup registered (Daily 22:00 Evening)" -ForegroundColor Green
            $registered++
        }
        else {
            Write-Host "  ⚠️  May already be registered" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
    $failed++
}

# 3. Cache Validation - 14:00 & 20:00 (Afternoon & Evening)
Write-Host "`n[3/5] Cache Validation (14:00 & 20:00)..." -ForegroundColor Yellow
try {
    $script = Join-Path $WorkspaceRoot "scripts\register_cache_validation_tasks.ps1"
    if ($DryRun) {
        Write-Host "  [DryRun] Would register at 14:00 & 20:00" -ForegroundColor Cyan
    }
    else {
        & $script -Register
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Cache Validation registered (14:00 & 20:00)" -ForegroundColor Green
            $registered++
        }
        else {
            Write-Host "  ⚠️  May already be registered" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
    $failed++
}

# 4. YouTube Learner - 16:00 (Afternoon, optional)
if (-not $SkipYouTube) {
    Write-Host "`n[4/5] YouTube Learner (16:00 Afternoon, optional)..." -ForegroundColor Yellow
    try {
        $script = Join-Path $WorkspaceRoot "scripts\register_youtube_learner_task.ps1"
        if (Test-Path $script) {
            if ($DryRun) {
                Write-Host "  [DryRun] Would register at 16:00" -ForegroundColor Cyan
            }
            else {
                & $script -Register -Time "16:00" -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -MaxFrames 3
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ YouTube Learner registered (Daily 16:00)" -ForegroundColor Green
                    $registered++
                }
                else {
                    Write-Host "  ⚠️  May already be registered" -ForegroundColor Yellow
                }
            }
        }
        else {
            Write-Host "  ℹ️  Script not found, skipping" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "  ⚠️  Skipped: $_" -ForegroundColor Yellow
    }
}
else {
    Write-Host "`n[4/5] YouTube Learner (SKIPPED)" -ForegroundColor DarkGray
}

# 5. Ion Inbox Watcher - At Logon (optional)
Write-Host "`n[5/5] Ion Inbox Watcher (At Logon, optional)..." -ForegroundColor Yellow
try {
    $script = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring\scripts\register_inbox_watcher.ps1"
    if (Test-Path $script) {
        if ($DryRun) {
            Write-Host "  [DryRun] Would register at logon" -ForegroundColor Cyan
        }
        else {
            & $script -Register -Agents "all"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Inbox Watcher registered (At Logon)" -ForegroundColor Green
                $registered++
            }
            else {
                Write-Host "  ⚠️  May already be registered" -ForegroundColor Yellow
            }
        }
    }
    else {
        Write-Host "  ℹ️  Script not found, skipping" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "  ⚠️  Skipped: $_" -ForegroundColor Yellow
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Registration Summary                                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📊 Results:" -ForegroundColor Cyan
Write-Host "  ✅ Successfully registered: $registered tasks" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "  ❌ Failed: $failed tasks" -ForegroundColor Red
}

Write-Host "`n📅 New Schedule:" -ForegroundColor Cyan
Write-Host "  10:00 - Trinity Cycle (Morning learning)" -ForegroundColor White
Write-Host "  14:00 - Cache Validation 1st (Afternoon)" -ForegroundColor White
Write-Host "  16:00 - YouTube Learner (Afternoon, optional)" -ForegroundColor White
Write-Host "  20:00 - Cache Validation 2nd (Evening)" -ForegroundColor White
Write-Host "  22:00 - Auto Backup (Evening, before sleep)" -ForegroundColor White

Write-Host "`n💡 Verify registration:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask | Where-Object { `$_.TaskName -match 'Trinity|Backup|Cache|YouTube|Inbox' } | Format-Table TaskName, State, @{L='NextRun';E={`$_.NextRunTime}}" -ForegroundColor Gray

Write-Host "`n✅ Registration complete! All tasks will run at user-friendly times." -ForegroundColor Green
