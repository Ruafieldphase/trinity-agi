@echo off
echo Stopping AGI Backend Services...

FOR /F "tokens=5" %%a IN ('netstat -aon ^| findstr ":8100"') DO taskkill /F /PID %%a >nul 2>&1
FOR /F "tokens=5" %%a IN ('netstat -aon ^| findstr ":8101"') DO taskkill /F /PID %%a >nul 2>&1
FOR /F "tokens=5" %%a IN ('netstat -aon ^| findstr ":8102"') DO taskkill /F /PID %%a >nul 2>&1
FOR /F "tokens=5" %%a IN ('netstat -aon ^| findstr ":8104"') DO taskkill /F /PID %%a >nul 2>&1

taskkill /F /IM python.exe /FI "CommandLine LIKE *lymphatic_system.py*" >nul 2>&1
taskkill /F /IM python.exe /FI "CommandLine LIKE *slack_interface.py*" >nul 2>&1
taskkill /F /IM python.exe /FI "CommandLine LIKE *core_conscious.py*" >nul 2>&1

echo.
echo All AGI backend services stopped.
pause
