# Quick System Check Alias
# Usage: Just run "check" or "system-check" from anywhere

$scriptPath = "$WorkspaceRoot\scripts\system_health_check.ps1"

function Invoke-SystemHealthCheck {
    param(
        [switch]$Detailed,
        [string]$OutputJson
    )
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

    
    $params = @{}
    if ($Detailed) { $params['Detailed'] = $true }
    if ($OutputJson) { $params['OutputJson'] = $OutputJson }
    
    & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath @params
}

# Create convenient aliases
Set-Alias -Name check -Value Invoke-SystemHealthCheck
Set-Alias -Name system-check -Value Invoke-SystemHealthCheck
Set-Alias -Name health -Value Invoke-SystemHealthCheck

Write-Host "System health check aliases loaded!" -ForegroundColor Green
Write-Host "  - " -NoNewline
Write-Host "check" -ForegroundColor Cyan -NoNewline
Write-Host "         : Quick system check"
Write-Host "  - " -NoNewline
Write-Host "check -Detailed" -ForegroundColor Cyan -NoNewline
Write-Host " : Full performance benchmarks"
Write-Host "  - " -NoNewline
Write-Host "health" -ForegroundColor Cyan -NoNewline
Write-Host "        : Same as check"