param(
    [Parameter(Mandatory = $true)] [string]$ProjectId,
    [Parameter(Mandatory = $true)] [string]$DashboardId
)

Write-Host "`n[Lumen v1.7] Dashboard Quick Link Generator" -ForegroundColor Cyan

$url = "https://console.cloud.google.com/monitoring/dashboards/custom/${DashboardId}?project=${ProjectId}"

Write-Host "`nDashboard URL:" -ForegroundColor Yellow
Write-Host $url -ForegroundColor Green

Write-Host "`nOpening in default browser..." -ForegroundColor Yellow
Start-Process $url

Write-Host "`nTip: Bookmark this URL for quick access to live metrics" -ForegroundColor Cyan
