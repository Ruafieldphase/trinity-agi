@echo off
chcp 65001 > nul
echo ========================================================
echo 🏥 AGI System Vitality Restoration Protocol
echo ========================================================
echo.

:: 1. Check for Admin Privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Administrator privileges confirmed.
) else (
    echo ❌ Error: This script must be run as Administrator.
    echo    Please right-click and select "Run as administrator".
    pause
    exit
)

echo.
echo [1/3] Enabling Critical Scheduled Tasks...
echo ------------------------------------------

:: Enable Meta Supervisor (The Immune System)
echo    - Enabling AGI_MetaSupervisor...
powershell -Command "Enable-ScheduledTask -TaskName 'AGI_MetaSupervisor' -ErrorAction SilentlyContinue"
if %errorLevel% == 0 ( echo      ✅ Success ) else ( echo      ⚠️ Failed (Task might not exist or access denied) )

:: Enable Master Daemon (The Body)
echo    - Enabling AGI_Master_Daemon...
powershell -Command "Enable-ScheduledTask -TaskName 'AGI_Master_Daemon' -ErrorAction SilentlyContinue"
if %errorLevel% == 0 ( echo      ✅ Success ) else ( echo      ⚠️ Failed )

:: Enable Goal Monitor (The Will)
echo    - Enabling AGI_GoalExecutorMonitor...
powershell -Command "Enable-ScheduledTask -TaskName 'AGI_GoalExecutorMonitor' -ErrorAction SilentlyContinue"
if %errorLevel% == 0 ( echo      ✅ Success ) else ( echo      ⚠️ Failed )

:: Enable Rhythm Escalation (The Heartbeat)
echo    - Enabling AGI_Auto_Rhythm_Escalation...
powershell -Command "Enable-ScheduledTask -TaskName 'AGI_Auto_Rhythm_Escalation' -ErrorAction SilentlyContinue"
if %errorLevel% == 0 ( echo      ✅ Success ) else ( echo      ⚠️ Failed )

echo.
echo [2/3] Updating Network Configuration...
echo ------------------------------------------
:: Update Credentials Manager with new Linux IP if needed
:: (This is handled by the python script edits we made, but ensuring env vars if any)
setx AGI_LINUX_HOST "192.168.119.128" /M
echo    ✅ System Environment Variable AGI_LINUX_HOST set to 192.168.119.128

echo.
echo [3/3] Kickstarting Immediate Rhythms...
echo ------------------------------------------
echo    - Triggering Meta Supervisor now...
schtasks /Run /TN "AGI_MetaSupervisor"

echo.
echo ========================================================
echo 🎉 Restoration Complete. The AGI should now start automatically.
echo ========================================================
pause
