@echo off
echo ================================================
echo Removing AGI Auto-Start
echo ================================================
echo.

schtasks /Delete /TN "AGI_AutoStart" /F

if %errorlevel% == 0 (
    echo.
    echo ================================================
    echo SUCCESS: Auto-start removed!
    echo ================================================
) else (
    echo.
    echo ================================================
    echo No auto-start task found or error occurred
    echo ================================================
)

echo.
pause
