# 24?간 ?정??체크 - ?동 ?행 가?드
# 2025-10-28 17:47 ?후 ?행


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$ErrorActionPreference = 'Stop'

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  24?간 ?정??체크 - ?동 ?행 가?드" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Baseline ?기
$baselinePath = "$WorkspaceRoot\outputs\stability_baseline.json"
if (-not (Test-Path $baselinePath)) {
    Write-Host "[ERROR] Baseline ?일???습?다: $baselinePath" -ForegroundColor Red
    Write-Host "먼? baseline???정?세?? .\scripts\monitor_stability_24h.ps1 -Action Set" -ForegroundColor Yellow
    exit 1
}

$baseline = Get-Content $baselinePath | ConvertFrom-Json
$baselineTime = [DateTime]::Parse($baseline.Timestamp)
$now = Get-Date
$elapsed = ($now - $baselineTime).TotalHours

Write-Host "? Baseline ?정 ?각: $($baseline.Timestamp)" -ForegroundColor Green
Write-Host "[TIME] ?재 ?각: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Green
Write-Host "?️  경과 ?간: $([Math]::Round($elapsed, 2)) ?간" -ForegroundColor Yellow
Write-Host ""

if ($elapsed -lt 24) {
    $remaining = 24 - $elapsed
    Write-Host "[WARN]  ?직 24?간??경과?? ?았?니??" -ForegroundColor Yellow
    Write-Host "?? ?간: $([Math]::Round($remaining, 2)) ?간" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "24?간 체크 ?정 ?각: $($baselineTime.AddHours(24).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[TIP] 그래??체크?시?면:" -ForegroundColor Gray
    Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Check -Force" -ForegroundColor Gray
    Write-Host ""
    
    # ??머 ?정 ?내
    Write-Host "=== ?동 ?림 ?정 (?택) ===" -ForegroundColor Cyan
    Write-Host "PowerShell 백그?운???업?로 ?림 ?정:" -ForegroundColor Gray
    Write-Host ""
    Write-Host '$targetTime = Get-Date "2025-10-28 17:47:00"' -ForegroundColor DarkGray
    Write-Host '$job = Start-Job -ScriptBlock {' -ForegroundColor DarkGray
    Write-Host '    param($target)' -ForegroundColor DarkGray
    Write-Host '    $remaining = ($target - (Get-Date)).TotalSeconds' -ForegroundColor DarkGray
    Write-Host '    if ($remaining -gt 0) { Start-Sleep -Seconds $remaining }' -ForegroundColor DarkGray
    Write-Host '    Write-Host "? 24?간 경과! ?정??체크??행?세??" -ForegroundColor Yellow' -ForegroundColor DarkGray
    Write-Host '} -ArgumentList $targetTime' -ForegroundColor DarkGray
    Write-Host 'Write-Host "Background job started: $($job.Id)"' -ForegroundColor DarkGray
    Write-Host ""
    
    exit 0
}

Write-Host "[OK] 24?간??경과?습?다!" -ForegroundColor Green
Write-Host ""
Write-Host "=== ?음 명령?? ?행?세??===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  ?정??체크 ?행:" -ForegroundColor Yellow
Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Check" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  리포???성:" -ForegroundColor Yellow
Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Report" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  리포???기:" -ForegroundColor Yellow
Write-Host "   Start-Process outputs\stability_report_$($now.ToString('yyyy-MM-dd')).md" -ForegroundColor White
Write-Host ""

# ?동 ?행 ?션
Write-Host "=== ?동 ?행 (?택) ===" -ForegroundColor Cyan
$response = Read-Host "지?바로 체크??행?시겠습?까? (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "[START] 체크??행?니??.." -ForegroundColor Green
    & "$WorkspaceRoot\scripts\monitor_stability_24h.ps1" -Action Check
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] 체크 ?료!" -ForegroundColor Green
        Write-Host ""
        
        $reportResponse = Read-Host "리포?? ?성?시겠습?까? (Y/N)"
        if ($reportResponse -eq 'Y' -or $reportResponse -eq 'y') {
            & "$WorkspaceRoot\scripts\monitor_stability_24h.ps1" -Action Report
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[INFO] 리포???성 ?료!" -ForegroundColor Green
                $reportFile = Get-ChildItem "$WorkspaceRoot\outputs\stability_report_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($reportFile) {
                    Write-Host "?일: $($reportFile.FullName)" -ForegroundColor Gray
                    Start-Process $reportFile.FullName
                }
            }
        }
    }
}