[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$DryRun,
    [string[]]$Targets
)

# Purpose:
#   Toggle ReadOnly attribute on critical code directories to guard against accidental writes.
#   Default targets focus on orchestrator (low-risk). You can extend Targets to include more.
#
# Usage examples (PowerShell):
#   # Enable guardrails (set ReadOnly on files)
#   .\protect_code_dirs.ps1 -Enable
#   # Disable guardrails (remove ReadOnly from files)
#   .\protect_code_dirs.ps1 -Disable
#   # Dry-run (log only)
#   .\protect_code_dirs.ps1 -Enable -DryRun
#   # Custom targets
#   .\protect_code_dirs.ps1 -Enable -Targets "C:\workspace\agi\fdo_agi_repo\orchestrator","C:\workspace\agi\LLM_Unified\ion-mentoring"

$ErrorActionPreference = 'Stop'

if (-not $Enable -and -not $Disable) {
    Write-Host "Specify one: -Enable or -Disable" -ForegroundColor Yellow
    exit 1
}

$base = "C:\workspace\agi"
if (-not $Targets -or $Targets.Count -eq 0) {
    $Targets = @(
        Join-Path $base 'fdo_agi_repo\orchestrator'
        # Add carefully if needed:
        # Join-Path $base 'LLM_Unified\ion-mentoring'
    )
}

function Set-ROForFiles {
    param(
        [string]$Path,
        [bool]$EnableRO
    )
    if (-not (Test-Path $Path)) { return }
    $files = Get-ChildItem -Path $Path -File -Recurse -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        try {
            if ($EnableRO) {
                if ($DryRun) {
                    Write-Host "[DRYRUN] +R $($f.FullName)" -ForegroundColor Cyan
                }
                else {
                    (Get-Item $f.FullName).Attributes = ((Get-Item $f.FullName).Attributes -bor [System.IO.FileAttributes]::ReadOnly)
                }
            }
            else {
                if ($DryRun) {
                    Write-Host "[DRYRUN] -R $($f.FullName)" -ForegroundColor Cyan
                }
                else {
                    (Get-Item $f.FullName).Attributes = ((Get-Item $f.FullName).Attributes -band -bnot [System.IO.FileAttributes]::ReadOnly)
                }
            }
        }
        catch {
            Write-Warning "Failed to toggle: $($f.FullName) => $($_.Exception.Message)"
        }
    }
}

foreach ($t in $Targets) {
    if (-not (Test-Path $t)) {
        Write-Warning "Target not found: $t"
        continue
    }
    Write-Host "Processing: $t" -ForegroundColor Green
    if ($Enable) {
        Set-ROForFiles -Path $t -EnableRO:$true
    }
    if ($Disable) {
        Set-ROForFiles -Path $t -EnableRO:$false
    }
}

Write-Host "Done." -ForegroundColor Green
