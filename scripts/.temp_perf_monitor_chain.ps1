
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
﻿# Performance Monitor Chain
Write-Host '🔄 Running performance benchmark...' -ForegroundColor Cyan
& "$WorkspaceRoot\scripts\save_performance_benchmark.ps1" -Warmup -Iterations 3 -MaxTokens 64 -Append

if ($LASTEXITCODE -eq 0) {
    Write-Host '📊 Updating unified dashboard...' -ForegroundColor Cyan
    & "$WorkspaceRoot\scripts\generate_unified_dashboard.ps1"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host '🎨 Generating visual dashboard...' -ForegroundColor Cyan
        & "$WorkspaceRoot\scripts\generate_visual_dashboard.ps1"
    }
}

Write-Host '✓ Performance monitor cycle completed' -ForegroundColor Green