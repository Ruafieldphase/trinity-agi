# Invoke Shion (Clean Start)
# Stops existing instances and launches Shion silently.

$ErrorActionPreference = "SilentlyContinue"
$PythonW = "pythonw.exe"
$Script = "c:\workspace\agi\scripts\shion.py"

Write-Host "🌊 Invoking Shion (The Silent Heart)..." -ForegroundColor Cyan

# 1. Stop existing Shion/Guardian
Get-Process -Name "pythonw" | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force
Get-Process -Name "python" | Where-Object { $_.CommandLine -like "*shion.py*" } | Stop-Process -Force

Start-Sleep -Seconds 1

# 2. Start Silent Heart
Start-Process `
    -FilePath $PythonW `
    -ArgumentList "`"$Script`" --silent-mode" `
    -WindowStyle Hidden `
    -WorkingDirectory "c:\workspace\agi"

Write-Host "✅ Shion invoked in the void." -ForegroundColor Green
exit 0
