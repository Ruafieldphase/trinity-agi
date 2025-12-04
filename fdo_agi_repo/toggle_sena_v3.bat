@echo off
REM Toggle Hey Sena v3 (Start if not running, Stop if running)

cd /d D:\nas_backup\fdo_agi_repo

REM Check if Hey Sena is running
tasklist /FI "WINDOWTITLE eq Hey Sena v3*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Hey Sena v3 is running. Stopping...
    taskkill /FI "WINDOWTITLE eq Hey Sena v3*" /F
    echo Hey Sena v3 stopped.
) else (
    echo Hey Sena v3 is not running. Starting...
    start "Hey Sena v3" cmd /k start_sena_v3.bat
    echo Hey Sena v3 started!
)

timeout /t 2
