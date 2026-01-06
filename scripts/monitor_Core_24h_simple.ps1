# Core 24h Production - 간단한 모니터링
# 로그 파일만 체크 (JSON 파싱 오류 없음)

param(
    [int]$Tail = 5
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$logFile = "$WorkspaceRoot\fdo_agi_repo\outputs\core_production_24h_stable.jsonl"

Write-Host "`n═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Core 24h Production - 간단 모니터링" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════`n" -ForegroundColor Cyan

if (Test-Path $logFile) {
    $lines = @(Get-Content $logFile)
    $count = $lines.Count
    
    Write-Host "📊 현재 상태:" -ForegroundColor Yellow
    Write-Host "   총 사이클: $count / 288" -ForegroundColor White
    
    if ($count -gt 0) {
        $progress = ($count / 288) * 100
        Write-Host "   진행률: $([math]::Round($progress, 1))%" -ForegroundColor Green
        
        # 파일 수정 시간
        $lastModified = (Get-Item $logFile).LastWriteTime
        $elapsed = (Get-Date) - $lastModified
        Write-Host "   마지막 업데이트: $($lastModified.ToString('HH:mm:ss')) ($([math]::Round($elapsed.TotalSeconds, 0))초 전)" -ForegroundColor Gray
        
        Write-Host "`n📝 최근 $Tail 사이클:" -ForegroundColor Cyan
        $lines | Select-Object -Last $Tail | ForEach-Object {
            Write-Host "   $_" -ForegroundColor White
        }
    }
    
    Write-Host "`n파일 경로: $logFile" -ForegroundColor Gray
    Write-Host "파일 크기: $([math]::Round((Get-Item $logFile).Length / 1KB, 1)) KB`n" -ForegroundColor Gray
    
}
else {
    Write-Host "❌ 로그 파일 없음" -ForegroundColor Red
    Write-Host "   경로: $logFile`n" -ForegroundColor Gray
}