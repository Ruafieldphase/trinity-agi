@echo off
echo.
echo 👁️ Awakening Senses (OCR + OBS)...
echo.

:: 1. Start OBS Learner (The Eye)
tasklist /V | findstr "AGI-OBS" >nul
if %errorlevel% neq 0 (
    echo    Starting OBS Learner...
    start "" pythonw -u services\obs_learner.py
) else (
    echo    OBS Learner already active.
)

:: 2. Start OCR Service (The Reading)
:: Using Direct Pythonw to avoid PowerShell window
tasklist /V | findstr "AGI-OCR" >nul
if %errorlevel% neq 0 (
    echo    Starting OCR Service...
    set "PYTHONPATH=%WORKSPACE_ROOT%\fdo_agi_repo;%PYTHONPATH%"
    start "" pythonw -u fdo_agi_repo\scripts\smoke_e2e_ocr.py
)

echo ✅ Senses restored.
exit /b
