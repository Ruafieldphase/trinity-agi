# Real-time Process Creation Monitor
# 새로 생성되는 PowerShell/Python 프로세스를 즉시 감지

$ErrorActionPreference = "Continue"
$logPath = "C:\workspace\agi\outputs\process_creation_monitor.log"

Write-Host "=== Process Creation Monitor ===" -ForegroundColor Cyan
Write-Host "Detecting new PowerShell/Python processes..." -ForegroundColor Yellow
Write-Host "Log: $logPath`n" -ForegroundColor Gray

# 현재 실행 중인 프로세스 ID 저장
$knownProcesses = @{}
Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -match '^(powershell|pwsh|python|py|cmd)$'
} | ForEach-Object {
    $knownProcesses[$_.Id] = $true
}

Write-Host "Initial processes: $($knownProcesses.Count)" -ForegroundColor Gray
Write-Host "Starting monitoring...`n" -ForegroundColor Green

$checkCount = 0
while ($true) {
    Start-Sleep -Milliseconds 200  # 더 빠른 감지 (200ms)
    $checkCount++
    
    # 현재 프로세스 확인
    $currentProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -match '^(powershell|pwsh|python|py|cmd)$'
    }
    
    foreach ($proc in $currentProcesses) {
        if (-not $knownProcesses.ContainsKey($proc.Id)) {
            # 새 프로세스 발견!
            try {
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
                $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction Stop).CommandLine
                $parent = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction Stop).ParentProcessId
                $parentName = (Get-Process -Id $parent -ErrorAction SilentlyContinue).ProcessName
                
                $msg = @"
[$timestamp] NEW PROCESS CREATED!
  PID: $($proc.Id)
  Process: $($proc.ProcessName)
  Parent PID: $parent ($parentName)
  Window Handle: $($proc.MainWindowHandle)
  Command Line: $cmdLine
  
"@
                Write-Host $msg -ForegroundColor Red
                Add-Content -Path $logPath -Value $msg
                
                # 즉시 kill 시도
                if ($proc.MainWindowHandle -ne 0) {
                    try {
                        $proc.Kill()
                        Write-Host "  → Killed windowed process $($proc.Id)" -ForegroundColor Yellow
                        Add-Content -Path $logPath -Value "  → Killed at $(Get-Date -Format 'HH:mm:ss.fff')`n"
                    }
                    catch {
                        Write-Host "  → Could not kill: $_" -ForegroundColor Gray
                    }
                }
            }
            catch {
                Write-Host "[$timestamp] New process $($proc.Id) ($($proc.ProcessName)) - Error getting details: $_" -ForegroundColor Yellow
            }
            
            $knownProcesses[$proc.Id] = $true
        }
    }
    
    # 10초마다 상태 표시
    if ($checkCount % 50 -eq 0) {
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }
    
    # 1분마다 정리
    if ($checkCount % 300 -eq 0) {
        $currentIds = $currentProcesses | ForEach-Object { $_.Id }
        $keysToRemove = $knownProcesses.Keys | Where-Object { $_ -notin $currentIds }
        foreach ($key in $keysToRemove) {
            $knownProcesses.Remove($key)
        }
        Write-Host "`n[Cleanup] Known processes: $($knownProcesses.Count)" -ForegroundColor DarkGray
    }
}
