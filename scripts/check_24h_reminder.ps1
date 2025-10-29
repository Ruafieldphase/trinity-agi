# 24?œê°„ ?ˆì •??ì²´í¬ - ?˜ë™ ?¤í–‰ ê°€?´ë“œ
# 2025-10-28 17:47 ?´í›„ ?¤í–‰

$ErrorActionPreference = 'Stop'

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  24?œê°„ ?ˆì •??ì²´í¬ - ?˜ë™ ?¤í–‰ ê°€?´ë“œ" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Baseline ?½ê¸°
$baselinePath = "C:\workspace\agi\outputs\stability_baseline.json"
if (-not (Test-Path $baselinePath)) {
    Write-Host "[ERROR] Baseline ?Œì¼???†ìŠµ?ˆë‹¤: $baselinePath" -ForegroundColor Red
    Write-Host "ë¨¼ì? baseline???¤ì •?˜ì„¸?? .\scripts\monitor_stability_24h.ps1 -Action Set" -ForegroundColor Yellow
    exit 1
}

$baseline = Get-Content $baselinePath | ConvertFrom-Json
$baselineTime = [DateTime]::Parse($baseline.Timestamp)
$now = Get-Date
$elapsed = ($now - $baselineTime).TotalHours

Write-Host "?“… Baseline ?¤ì • ?œê°: $($baseline.Timestamp)" -ForegroundColor Green
Write-Host "[TIME] ?„ì¬ ?œê°: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Green
Write-Host "?±ï¸  ê²½ê³¼ ?œê°„: $([Math]::Round($elapsed, 2)) ?œê°„" -ForegroundColor Yellow
Write-Host ""

if ($elapsed -lt 24) {
    $remaining = 24 - $elapsed
    Write-Host "[WARN]  ?„ì§ 24?œê°„??ê²½ê³¼?˜ì? ?Šì•˜?µë‹ˆ??" -ForegroundColor Yellow
    Write-Host "?¨ì? ?œê°„: $([Math]::Round($remaining, 2)) ?œê°„" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "24?œê°„ ì²´í¬ ?ˆì • ?œê°: $($baselineTime.AddHours(24).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[TIP] ê·¸ë˜??ì²´í¬?˜ì‹œ?¤ë©´:" -ForegroundColor Gray
    Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Check -Force" -ForegroundColor Gray
    Write-Host ""
    
    # ?€?´ë¨¸ ?¤ì • ?ˆë‚´
    Write-Host "=== ?ë™ ?Œë¦¼ ?¤ì • (? íƒ) ===" -ForegroundColor Cyan
    Write-Host "PowerShell ë°±ê·¸?¼ìš´???‘ì—…?¼ë¡œ ?Œë¦¼ ?¤ì •:" -ForegroundColor Gray
    Write-Host ""
    Write-Host '$targetTime = Get-Date "2025-10-28 17:47:00"' -ForegroundColor DarkGray
    Write-Host '$job = Start-Job -ScriptBlock {' -ForegroundColor DarkGray
    Write-Host '    param($target)' -ForegroundColor DarkGray
    Write-Host '    $remaining = ($target - (Get-Date)).TotalSeconds' -ForegroundColor DarkGray
    Write-Host '    if ($remaining -gt 0) { Start-Sleep -Seconds $remaining }' -ForegroundColor DarkGray
    Write-Host '    Write-Host "?”” 24?œê°„ ê²½ê³¼! ?ˆì •??ì²´í¬ë¥??¤í–‰?˜ì„¸??" -ForegroundColor Yellow' -ForegroundColor DarkGray
    Write-Host '} -ArgumentList $targetTime' -ForegroundColor DarkGray
    Write-Host 'Write-Host "Background job started: $($job.Id)"' -ForegroundColor DarkGray
    Write-Host ""
    
    exit 0
}

Write-Host "[OK] 24?œê°„??ê²½ê³¼?ˆìŠµ?ˆë‹¤!" -ForegroundColor Green
Write-Host ""
Write-Host "=== ?¤ìŒ ëª…ë ¹?´ë? ?¤í–‰?˜ì„¸??===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1ï¸âƒ£  ?ˆì •??ì²´í¬ ?¤í–‰:" -ForegroundColor Yellow
Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Check" -ForegroundColor White
Write-Host ""
Write-Host "2ï¸âƒ£  ë¦¬í¬???ì„±:" -ForegroundColor Yellow
Write-Host "   .\scripts\monitor_stability_24h.ps1 -Action Report" -ForegroundColor White
Write-Host ""
Write-Host "3ï¸âƒ£  ë¦¬í¬???´ê¸°:" -ForegroundColor Yellow
Write-Host "   Start-Process outputs\stability_report_$($now.ToString('yyyy-MM-dd')).md" -ForegroundColor White
Write-Host ""

# ?ë™ ?¤í–‰ ?µì…˜
Write-Host "=== ?ë™ ?¤í–‰ (? íƒ) ===" -ForegroundColor Cyan
$response = Read-Host "ì§€ê¸?ë°”ë¡œ ì²´í¬ë¥??¤í–‰?˜ì‹œê² ìŠµ?ˆê¹Œ? (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "[START] ì²´í¬ë¥??¤í–‰?©ë‹ˆ??.." -ForegroundColor Green
    & "C:\workspace\agi\scripts\monitor_stability_24h.ps1" -Action Check
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] ì²´í¬ ?„ë£Œ!" -ForegroundColor Green
        Write-Host ""
        
        $reportResponse = Read-Host "ë¦¬í¬?¸ë? ?ì„±?˜ì‹œê² ìŠµ?ˆê¹Œ? (Y/N)"
        if ($reportResponse -eq 'Y' -or $reportResponse -eq 'y') {
            & "C:\workspace\agi\scripts\monitor_stability_24h.ps1" -Action Report
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[INFO] ë¦¬í¬???ì„± ?„ë£Œ!" -ForegroundColor Green
                $reportFile = Get-ChildItem "C:\workspace\agi\outputs\stability_report_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($reportFile) {
                    Write-Host "?Œì¼: $($reportFile.FullName)" -ForegroundColor Gray
                    Start-Process $reportFile.FullName
                }
            }
        }
    }
}
