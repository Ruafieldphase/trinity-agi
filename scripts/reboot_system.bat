@echo off
echo 🔄 Initiating AGI System Reboot...

echo 🥀 Folding (Killing) Active Processes...
taskkill /F /FI "WINDOWTITLE eq AGI-Heartbeat" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AGI-Brain" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AGI-Sena" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AGI-Master" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AGI-Immune" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AGI-Aura" >nul 2>&1

echo ⏳ Waiting for cleanup...
timeout /t 3 /nobreak >nul

echo 🌱 Unfolding (Restarting) System...
cd /d "%~dp0.."
call start_life.bat

echo ✅ Reboot Sequence Complete.
