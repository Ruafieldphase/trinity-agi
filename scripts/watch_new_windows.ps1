#Requires -Version 5.1
<#
.SYNOPSIS
    새로 열리는 PowerShell 창 감시 및 로그
#>

param(
    [int]$DurationMinutes = 10
)

$logFile = "$PSScriptRoot\..\outputs\new_windows_log.txt"
$endTime = (Get-Date).AddMinutes($DurationMinutes)

Write-Host "🔍 Watching for new PowerShell windows..." -ForegroundColor Cyan
Write-Host "Duration: $DurationMinutes minutes" -ForegroundColor Yellow
Write-Host "Log: $logFile`n" -ForegroundColor Gray

# 현재 프로세스 목록 저장
$baseline = Get-Process -Name 'powershell', 'pwsh' -ErrorAction SilentlyContinue | Select-Object Id

while ((Get-Date) -lt $endTime) {
    Start-Sleep -Seconds 2
    
    # 새 프로세스 감지
    $current = Get-Process -Name 'powershell', 'pwsh' -ErrorAction SilentlyContinue
    $new = $current | Where-Object { $_.Id -notin $baseline.Id }
    
    foreach ($proc in $new) {
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
        
        $entry = @"
[$timestamp] New PowerShell Window Detected!
  PID: $($proc.Id)
  Name: $($proc.ProcessName)
  Title: $($proc.MainWindowTitle)
  Command: $cmdLine
  Visible: $($proc.MainWindowHandle -ne 0)
----------------------------------------
"@
        
        Write-Host $entry -ForegroundColor Yellow
        Add-Content -Path $logFile -Value $entry
        
        # 베이스라인 업데이트
        $baseline = $current | Select-Object Id
    }
}

Write-Host "`n✅ Monitoring complete. Check log: $logFile" -ForegroundColor Green
