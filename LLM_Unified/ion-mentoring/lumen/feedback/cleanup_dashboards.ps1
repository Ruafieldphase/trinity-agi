param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [Parameter(Mandatory = $true)] [string[]]$DashboardIds,
    [switch]$DryRun
)

Write-Host "`n[Lumen v1.7] Dashboard Cleanup Utility" -ForegroundColor Cyan

foreach ($dashboardId in $DashboardIds) {
    Write-Host "`n[•] Processing dashboard: $dashboardId" -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "   - DryRun: Would delete this dashboard" -ForegroundColor DarkGray
        continue
    }
    
    try {
        $fullName = "projects/$ProjectId/dashboards/$dashboardId"
        gcloud monitoring dashboards delete $fullName --project=$ProjectId --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   - Deleted successfully" -ForegroundColor Green
        }
        else {
            Write-Host "   - Failed to delete (exit code: $LASTEXITCODE)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "   - Error: $_" -ForegroundColor Red
    }
}

Write-Host ("`n" + 'Dashboard cleanup complete for project: ' + $ProjectId) -ForegroundColor Green
