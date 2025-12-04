# Fix all register_*_task.ps1 scripts to use Hidden mode by default
# This ensures future task registrations will automatically use Hidden=$true and -WindowStyle Hidden

param(
    [switch]$DryRun,
    [switch]$Verbose
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Find all register_*_task.ps1 files
$registerScripts = @(
    Get-ChildItem -Path "$PSScriptRoot" -Filter "register_*_task.ps1" -File
    Get-ChildItem -Path "$PSScriptRoot\..\fdo_agi_repo\scripts" -Filter "register_*_task.ps1" -File -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$PSScriptRoot\..\LLM_Unified\ion-mentoring\scripts" -Filter "register_*_task.ps1" -File -ErrorAction SilentlyContinue
)

Write-Info "Found $($registerScripts.Count) register scripts"

$updated = 0
$skipped = 0
$failed = 0

foreach ($script in $registerScripts) {
    Write-Host ""
    Write-Info "Processing: $($script.Name)"
    
    try {
        $content = Get-Content -Path $script.FullName -Raw -Encoding UTF8
        $originalContent = $content
        $changed = $false
        
        # Check if already has -Hidden in Register-ScheduledTask or Set-ScheduledTask
        if ($content -match 'Register-ScheduledTask.*-Settings.*\$settings' -or 
            $content -match '\$settings\s*=\s*New-ScheduledTaskSettingsSet') {
            
            # Check if Hidden is already set in settings
            if ($content -notmatch '\$settings\.Hidden\s*=\s*\$true' -and
                $content -notmatch 'Hidden\s*=\s*\$true' -and
                $content -notmatch '-Hidden') {
                
                Write-Warn "  - Settings object found but Hidden not set"
                
                # Try to add Hidden=$true after New-ScheduledTaskSettingsSet
                if ($content -match '(\$settings\s*=\s*New-ScheduledTaskSettingsSet[^\n]+)') {
                    $settingsLine = $Matches[1]
                    $newLine = "$settingsLine`n`$settings.Hidden = `$true"
                    $content = $content -replace [regex]::Escape($settingsLine), $newLine
                    $changed = $true
                    Write-Info "  - Added: `$settings.Hidden = `$true"
                }
            }
            else {
                Write-Info "  - Settings.Hidden already configured"
            }
        }
        
        # Check if -WindowStyle Hidden is in Arguments
        if ($content -match 'ArgumentList.*powershell' -or $content -match '-Arguments.*powershell') {
            if ($content -notmatch '-WindowStyle\s+Hidden') {
                Write-Warn "  - PowerShell arguments found but missing -WindowStyle Hidden"
                
                # Try to add -WindowStyle Hidden after -ExecutionPolicy
                if ($content -match '(-ExecutionPolicy\s+\w+)(\s+)(-File|\")') {
                    $content = $content -replace '(-ExecutionPolicy\s+\w+)(\s+)(-File|\")', '$1$2-WindowStyle Hidden$2$3'
                    $changed = $true
                    Write-Info "  - Added: -WindowStyle Hidden to arguments"
                }
            }
            else {
                Write-Info "  - WindowStyle Hidden already present"
            }
        }
        
        # Save changes
        if ($changed) {
            if ($DryRun) {
                Write-Warn "  - [DRY RUN] Would update file"
                $updated++
            }
            else {
                Set-Content -Path $script.FullName -Value $content -Encoding UTF8 -NoNewline
                Write-Success "  - Updated successfully"
                $updated++
            }
        }
        else {
            Write-Info "  - No changes needed (already configured or no matching patterns)"
            $skipped++
        }
        
    }
    catch {
        Write-Err "  - Failed: $($_.Exception.Message)"
        if ($Verbose) {
            Write-Err "  - Stack: $($_.ScriptStackTrace)"
        }
        $failed++
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Info "Summary:"
Write-Success "  Updated: $updated"
Write-Warn "  Skipped: $skipped"
Write-Err "  Failed: $failed"

if ($DryRun) {
    Write-Host ""
    Write-Warn "This was a DRY RUN. No files were actually modified."
    Write-Info "Run without -DryRun to apply changes."
}
