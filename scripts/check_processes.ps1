# Check AGI processes
Write-Host "=== Python Processes ===" -ForegroundColor Cyan
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize

Write-Host "`n=== PowerShell Processes ===" -ForegroundColor Cyan
Get-Process -Name "powershell*" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize

Write-Host "`n=== Scheduled Tasks (AGI) ===" -ForegroundColor Cyan
schtasks /query /fo LIST | Select-String -Pattern "AGI|rhythm|brain|heartbeat" -Context 0,3
