@echo off
setlocal
cd /d C:\workspace\agi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\open_status_dashboard_v2.ps1"
endlocal

