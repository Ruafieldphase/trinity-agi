# Real-time Popup Window Monitor
# 팝업 창이 뜨면 즉시 감지하고 로그에 기록합니다

$ErrorActionPreference = "Continue"
$logPath = "C:\workspace\agi\outputs\popup_monitor.log"

Write-Host "=== Popup Window Monitor ===" -ForegroundColor Cyan
Write-Host "Monitoring for visible PowerShell/Python windows..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

$lastSeen = @{}

while ($true) {
    Start-Sleep -Milliseconds 500
    
    # 창이 있는 프로세스 찾기
    $visibleProcs = Get-Process -ErrorAction SilentlyContinue | 
    Where-Object {
        ($_.ProcessName -eq 'powershell' -or 
        $_.ProcessName -eq 'pwsh' -or 
        $_.ProcessName -eq 'python' -or 
        $_.ProcessName -eq 'py') -and 
        $_.MainWindowHandle -ne 0
    }
    
    foreach ($proc in $visibleProcs) {
        $key = "$($proc.Id)-$($proc.ProcessName)"
        
        if (-not $lastSeen.ContainsKey($key)) {
            # 새로 발견된 창!
            try {
                $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction Stop).CommandLine
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                
                $msg = @"
[$timestamp] POPUP DETECTED!
  PID: $($proc.Id)
  Process: $($proc.ProcessName)
  Window Title: $($proc.MainWindowTitle)
  Command Line: $cmdLine
  
"@
                Write-Host $msg -ForegroundColor Red
                Add-Content -Path $logPath -Value $msg
                
                # 창 숨기기 시도
                try {
                    $proc.Kill()
                    Write-Host "  → Killed process $($proc.Id)" -ForegroundColor Yellow
                }
                catch {
                    Write-Host "  → Could not kill: $_" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  → Error getting details: $_" -ForegroundColor Gray
            }
            
            $lastSeen[$key] = $true
        }
    }
    
    # 10초마다 캐시 정리 (종료된 프로세스 제거)
    if ((Get-Date).Second % 10 -eq 0) {
        $currentKeys = $visibleProcs | ForEach-Object { "$($_.Id)-$($_.ProcessName)" }
        $keysToRemove = $lastSeen.Keys | Where-Object { $_ -notin $currentKeys }
        foreach ($key in $keysToRemove) {
            $lastSeen.Remove($key)
        }
    }
}
