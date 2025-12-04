<#
.SYNOPSIS
    PowerShell 스크립트에서 이모지를 ASCII로 수동 변환 가이드

.DESCRIPTION
    PowerShell 5.1에서 이모지 파싱 문제로 인해 자동 변환이 불가능합니다.
    대신 Visual Studio Code의 Find & Replace를 사용하여 수동 변환하세요.
    
.NOTES
    자동화 불가 사유: PowerShell이 스크립트 파일 내 이모지를 로드할 때 파서 에러 발생
#>

Write-Host "`n========================================" -ForegroundColor Red
Write-Host "  [ERROR] PowerShell Emoji Parsing Issue" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Red

Write-Host "PowerShell 5.1 cannot parse emoji literals in script files." -ForegroundColor Yellow
Write-Host "This causes parser errors even when trying to automate replacement.`n" -ForegroundColor Yellow

Write-Host "[SOLUTION] Use VS Code Find & Replace (Regex Mode):`n" -ForegroundColor Cyan

$mappings = @"
Find (Regex)              Replace With
--------------------      ------------
\u2705                    [OK]
\u274C                    [ERROR]
\u26A0\uFE0F              [WARN]
\u{1F4CA}                 [INFO]
\u{1F680}                 [START]
\u{1F4A1}                 [TIP]
\u{1F50D}                 [SEARCH]
\u23F0                    [TIME]
\u{1F3AF}                 [TARGET]
\u{1F4C8}                 [UP]
\u{1F4C9}                 [DOWN]
\u{1F504}                 [RELOAD]
\u2728                    [NEW]
\u{1F389}                 [DONE]
\u{1F6D1}                 [STOP]
\u26A1                    [FAST]
\u{1F4DD}                 [NOTE]
\u{1F916}                 [BOT]
\u{1F310}                 [WEB]
\u{1F511}                 [KEY]
\u{1F4E1}                 [SIGNAL]
\u23F9\uFE0F              [END]
\u{1F3AC}                 [SCENE]
\u{1F399}\uFE0F           [MIC]
"@

Write-Host $mappings -ForegroundColor White

Write-Host "`n[STEPS]" -ForegroundColor Cyan
Write-Host "1. Open VS Code" -ForegroundColor White
Write-Host "2. Press Ctrl+Shift+H (Find & Replace in Files)" -ForegroundColor White
Write-Host "3. Enable Regex mode (.* button)" -ForegroundColor White
Write-Host "4. Enter find pattern (e.g., \u2705)" -ForegroundColor White
Write-Host "5. Enter replacement (e.g., [OK])" -ForegroundColor White
Write-Host "6. Set 'files to include': scripts/*.ps1" -ForegroundColor White
Write-Host "7. Click 'Replace All'`n" -ForegroundColor White

Write-Host "[ALTERNATIVE] Manual edit of affected files:" -ForegroundColor Cyan

# 영향받는 파일 목록 (grep 결과 기반)
$affectedFiles = @(
    "generate_monitoring_report.ps1",
    "register_24h_stability_check.ps1",
    "stop_local_proxy.ps1",
    "test_proxy_recovery.ps1",
    "unified_dashboard.ps1",
    "update_todo_week3.ps1",
    "verify_production_deployment.ps1"
)

foreach ($file in $affectedFiles) {
    Write-Host "  - scripts\$file" -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
