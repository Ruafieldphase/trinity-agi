@echo off
REM Hey Sena v3 Multi-turn Launcher
REM Start the voice assistant with multi-turn conversation capability

cd /d D:\nas_backup\fdo_agi_repo

echo.
echo ============================================================
echo   Starting Hey Sena v3 (Multi-turn Conversations)
echo ============================================================
echo.

REM Set UTF-8 encoding
chcp 65001 > nul

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Run Hey Sena v3
python hey_sena_v3_multiturn.py

pause
