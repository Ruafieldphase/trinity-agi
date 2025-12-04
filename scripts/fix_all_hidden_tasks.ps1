#requires -Version 5.1
<#
.SYNOPSIS
    Fix all task registration scripts to properly hide windows
.DESCRIPTION
    Replaces incorrect $settings.Hidden = $true pattern with proper -Hidden parameter
    and adds -WindowStyle Hidden to all powershell.exe invocations
#>
param(
    [switch]$DryRun,
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$scriptsToFix = @(
    'scripts\register_llm_monitor_task.ps1',
    'scripts\register_gateway_optimization_task.ps1',
    'scripts\register_daily_maintenance_task.ps1',
    'scripts\register_break_maintenance_task.ps1',
    'scripts\register_autopoietic_report_task.ps1',
    'scripts\register_autonomous_executor_task.ps1',
    'scripts\register_youtube_learner_task.ps1',
    'scripts\register_task_watchdog_scheduled_task.ps1',
    'scripts\register_snapshot_rotation_task.ps1',
    'scripts\register_trinity_cycle_task.ps1',
    'scripts\register_resonance_lumen_task.ps1',
    'scripts\register_worker_monitor_task.ps1',
    'fdo_agi_repo\scripts\register_online_learner_task.ps1',
    'fdo_agi_repo\scripts\register_online_learner_scheduled_task.ps1',
    'fdo_agi_repo\scripts\register_forced_evidence_scheduled_task.ps1',
    'fdo_agi_repo\scripts\register_health_check_task.ps1',
    'fdo_agi_repo\scripts\register_bqi_phase6_scheduled_task.ps1',
    'fdo_agi_repo\scripts\register_ensemble_monitor_task.ps1'
)

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Fix Hidden Task Registration (Mass Update)      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No files will be modified`n" -ForegroundColor Yellow
}

$fixedCount = 0
$errorCount = 0

foreach ($scriptRelPath in $scriptsToFix) {
    $scriptPath = Join-Path $workspaceRoot $scriptRelPath
    
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        Write-Host "⚠️  NOT FOUND: $scriptRelPath" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "📄 Processing: $scriptRelPath" -ForegroundColor Cyan
    
    try {
        $content = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
        $originalContent = $content
        $modified = $false
        
        # Fix 1: Replace $settings.Hidden = $true with -Hidden parameter
        if ($content -match '\$settings\.Hidden\s*=\s*\$true') {
            Write-Host "   🔧 Fixing: `$settings.Hidden = `$true pattern" -ForegroundColor Yellow
            
            # Find the New-ScheduledTaskSettingsSet block and add -Hidden
            $content = $content -replace '(\$settings\s*=\s*New-ScheduledTaskSettingsSet\s*``[^)]+)(\))', '$1 ``$2        -Hidden$3'
            
            # Remove the old $settings.Hidden = $true line
            $content = $content -replace '^\s*\$settings\.Hidden\s*=\s*\$true\s*$', ''
            
            $modified = $true
        }
        
        # Fix 2: Add -WindowStyle Hidden to powershell.exe arguments (if not already present)
        if ($content -match 'New-ScheduledTaskAction.*powershell\.exe' -and $content -notmatch '-WindowStyle\s+Hidden') {
            Write-Host "   🔧 Adding: -WindowStyle Hidden to powershell.exe" -ForegroundColor Yellow
            
            # Pattern 1: -Argument "..."
            $content = $content -replace '(-Argument\s+["\x60])-NoProfile\s+-ExecutionPolicy\s+Bypass\s+-File', '$1-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File'
            
            # Pattern 2: -Argument '...'
            $content = $content -replace "(-Argument\s+['\x60])-NoProfile\s+-ExecutionPolicy\s+Bypass\s+-File", '$1-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File'
            
            $modified = $true
        }
        
        if ($modified) {
            if ($DryRun) {
                Write-Host "   ✓ Would be fixed (DRY RUN)" -ForegroundColor Green
            }
            else {
                # Backup original
                $backupPath = "$scriptPath.bak"
                Copy-Item -LiteralPath $scriptPath -Destination $backupPath -Force
                
                # Write fixed content
                Set-Content -LiteralPath $scriptPath -Value $content -Encoding UTF8 -NoNewline
                
                Write-Host "   ✅ FIXED (backup: $([System.IO.Path]::GetFileName($backupPath)))" -ForegroundColor Green
                $fixedCount++
            }
        }
        else {
            Write-Host "   ℹ️  Already correct" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
    
    if ($Verbose) {
        Write-Host ""
    }
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "   Total scripts checked: $($scriptsToFix.Count)" -ForegroundColor Gray
Write-Host "   Fixed: $fixedCount" -ForegroundColor Green
Write-Host "   Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { 'Red' } else { 'Gray' })

if ($DryRun) {
    Write-Host "`n💡 Run without -DryRun to apply changes" -ForegroundColor Yellow
}
else {
    Write-Host "`n✨ All tasks will now run with hidden windows!" -ForegroundColor Green
    Write-Host "`n📌 Next step: Re-register all tasks to apply changes" -ForegroundColor Cyan
    Write-Host "   Run: .\scripts\reregister_all_tasks.ps1" -ForegroundColor Gray
}

exit $(if ($errorCount -gt 0) { 1 } else { 0 })
